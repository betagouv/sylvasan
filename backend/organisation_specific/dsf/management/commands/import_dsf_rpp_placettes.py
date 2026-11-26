import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connections

from organisations.models import Pole
from surveys.models import Placette, PlacetteSurvey
from users.models import User

logger = logging.getLogger(__name__)

# Ordre des colonnes retournées par RPP_SQL — doit rester synchronisé avec la requête.
COLUMNS = (
    "code_placette",
    "id_localisation",
    "code_co",
    "echelon",
    "actif",
    "lat",
    "lon",
    "topo",
    "expoliz",
    "annee_plant",
    "code_essence",
    "code_essence2",
    "long_lisiere",
)

RPP_SQL = """
SELECT
    p.code_placette,
    p.id_localisation,
    p.code_co,
    p.echelon,
    p.actif,
    CASE
        WHEN l.lat  IS NOT NULL AND l.long IS NOT NULL
             THEN l.lat
        WHEN l.geom IS NOT NULL
             THEN ST_Y(ST_Transform(l.geom::geometry, 4326))
        WHEN l.code_referentiel = 'LAM93' AND l.x IS NOT NULL AND l.x <> 0
             THEN ST_Y(ST_Transform(ST_SetSRID(ST_MakePoint(l.x, l.y), 2154), 4326))
        WHEN l.code_referentiel = 'LAM' AND l.x IS NOT NULL AND l.x <> 0
             THEN ST_Y(ST_Transform(ST_SetSRID(ST_MakePoint(l.x, l.y), 27572), 4326))
        ELSE NULL
    END AS lat,
    CASE
        WHEN l.lat  IS NOT NULL AND l.long IS NOT NULL
             THEN l.long
        WHEN l.geom IS NOT NULL
             THEN ST_X(ST_Transform(l.geom::geometry, 4326))
        WHEN l.code_referentiel = 'LAM93' AND l.x IS NOT NULL AND l.x <> 0
             THEN ST_X(ST_Transform(ST_SetSRID(ST_MakePoint(l.x, l.y), 2154), 4326))
        WHEN l.code_referentiel = 'LAM' AND l.x IS NOT NULL AND l.x <> 0
             THEN ST_X(ST_Transform(ST_SetSRID(ST_MakePoint(l.x, l.y), 27572), 4326))
        ELSE NULL
    END AS lon,
    pr.topo,
    pr.expoliz,
    pr.annee_plant,
    pr.code_essence,
    pr.code_essence2,
    pr.long_lisiere
FROM dsffs.placettes p
JOIN dsffs.localisation l ON l.id_localisation = p.id_localisation
JOIN dsffs.placette_rpp pr ON pr.code_placette = p.code_placette
WHERE p.type = 'RPP'
ORDER BY p.code_placette
"""


class Command(BaseCommand):
    help = "Importe les placettes RPP depuis la base de référence DSF (dsffs.placettes, type=RPP)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche les changements sans les appliquer",
        )
        parser.add_argument(
            "--survey-id",
            type=int,
            dest="survey_id",
            help="Identifiant du PlacetteSurvey Sylvasan auquel rattacher les placettes importées",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        survey_id = options.get("survey_id")

        if "dsf_ref" not in settings.DATABASES:
            self.stderr.write(
                self.style.ERROR("DSF_REF_DB_HOST non configuré — la base de référence DSF est indisponible.")
            )
            return

        survey = None
        if survey_id is not None:
            try:
                survey = PlacetteSurvey.objects.get(pk=survey_id)
                self.stdout.write(f"Enquête : « {survey.name} » (id={survey.pk})")
            except PlacetteSurvey.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"PlacetteSurvey id={survey_id} introuvable."))
                return

        with connections["dsf_ref"].cursor() as cursor:
            cursor.execute(RPP_SQL)
            rows = cursor.fetchall()

        self.stdout.write(f"{len(rows)} placettes RPP trouvées dans metadsf")

        # Préchargement pour éviter N+1 dans la boucle
        poles_by_dsf_code = {p.dsf_code: p for p in Pole.objects.exclude(dsf_code__isnull=True).exclude(dsf_code="")}
        users_by_external_id = {
            u.external_id: u for u in User.objects.exclude(external_id__isnull=True).exclude(external_id="")
        }

        totals = {"created": 0, "updated": 0, "skipped_no_coords": 0}

        for row in rows:
            r = dict(zip(COLUMNS, row))

            if r["lat"] is None or r["lon"] is None:
                logger.warning("Coordonnées manquantes pour %s — ignorée", r["code_placette"])
                totals["skipped_no_coords"] += 1
                continue

            pole = poles_by_dsf_code.get(r["echelon"])
            created_by = users_by_external_id.get(r["code_co"]) if r["code_co"] else None

            characteristics = {
                "topo": r["topo"],
                "expoliz": r["expoliz"],
                "annee_plant": r["annee_plant"],
                "code_essence": r["code_essence"],
                "code_essence2": r["code_essence2"],
                "long_lisiere": r["long_lisiere"],
            }

            if dry_run:
                exists = Placette.objects.filter(dsf_id_localisation=r["id_localisation"]).exists()
                action = "MIS À JOUR" if exists else "CRÉE"
                self.stdout.write(
                    f"  [{action}] {r['code_placette']} — "
                    f"lat={r['lat']:.5f}, lon={r['lon']:.5f}, "
                    f"pôle={r['echelon'] or '—'}, actif={r['actif']}"
                )
                continue

            defaults = {
                "code": r["code_placette"],
                "label": r["code_placette"],
                "lat": r["lat"],
                "lon": r["lon"],
                "dsf_actif": bool(r["actif"]),
                "dsf_type": "RPP",
                "is_active": bool(r["actif"]),
                "characteristics": characteristics,
                "pole": pole,
                # created_by exclus des defaults : on ne l'écrase pas lors des ré-imports.
            }
            if survey is not None:
                defaults["survey"] = survey

            # La clé combine dsf_id_localisation + survey quand un protocole est fourni,
            # pour permettre à la même localisation DSF d'exister dans plusieurs protocoles.
            lookup = {"dsf_id_localisation": r["id_localisation"]}
            if survey is not None:
                lookup["survey"] = survey

            try:
                placette, created = Placette.objects.update_or_create(
                    **lookup,
                    defaults=defaults,
                )
            except Placette.MultipleObjectsReturned:
                logger.error(
                    "Plusieurs placettes partagent dsf_id_localisation=%s — ignorée",
                    r["id_localisation"],
                )
                continue

            if created:
                totals["created"] += 1
                if created_by is not None:
                    placette.created_by = created_by
                    placette.save(update_fields=["created_by"])
                    placette.accessors.add(created_by)
            else:
                totals["updated"] += 1

        if dry_run:
            self.stdout.write(self.style.WARNING("[dry-run] Aucune modification appliquée"))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Import terminé : {totals['created']} créée(s), "
                f"{totals['updated']} mise(s) à jour, "
                f"{totals['skipped_no_coords']} ignorée(s) (coordonnées manquantes)"
            )
        )
