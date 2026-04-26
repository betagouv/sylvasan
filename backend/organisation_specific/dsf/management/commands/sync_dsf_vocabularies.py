from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connections

from organisations.models import Organisation
from surveys.models import VocabularyEntry, VocabularySet

VOCABULARIES = [
    {
        "code": "ESS",
        "name": "Essence d'arbre",
        "unite": "ESS",
    },
    # À rajouter d'autres par la suite
]


class Command(BaseCommand):
    help = "Synchronise les vocabulaires DSF depuis la base de référence metadsf"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche les changements sans les appliquer",
        )
        parser.add_argument(
            "--vocabulary",
            type=str,
            help="Synchronise uniquement un vocabulaire spécifique (par code)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        only_vocab = options.get("vocabulary")

        if "dsf_ref" not in settings.DATABASES:
            self.stderr.write(
                self.style.ERROR("DSF_REF_DB_HOST non configuré — la base de référence DSF est indisponible.")
            )
            return

        try:
            dsf = Organisation.objects.get(name="DSF")
        except Organisation.DoesNotExist:
            self.stderr.write(self.style.ERROR("Organisation DSF introuvable. Créez-la d'abord via l'admin."))
            return

        vocabs_to_sync = [v for v in VOCABULARIES if v["code"] == only_vocab] if only_vocab else VOCABULARIES

        if not vocabs_to_sync:
            self.stderr.write(self.style.WARNING(f"Aucun vocabulaire trouvé pour le code '{only_vocab}'"))
            return

        for vocab_def in vocabs_to_sync:
            self._sync_vocabulary(dsf, vocab_def, dry_run)

    def _sync_vocabulary(self, organisation, vocab_def, dry_run):
        code = vocab_def["code"]
        name = vocab_def["name"]
        unite = vocab_def["unite"]

        self.stdout.write(f"\nSynchronisation de '{code}' ({name})...")

        with connections["dsf_ref"].cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    m.mode,
                    COALESCE(l.libelle, m.libelle) AS libelle,
                    m.position
                FROM metadsf.abmode m
                LEFT JOIN metadsf.ablexique l
                    ON l.unite = m.unite
                    AND l.mode = m.mode
                    AND l.langue = 'FR'
                WHERE m.unite = %s
                ORDER BY m.position NULLS LAST, m.mode
                """,
                [unite],
            )
            rows = cursor.fetchall()

        if not rows:
            self.stderr.write(self.style.WARNING(f"Aucune entrée trouvée pour unite='{unite}' dans metadsf"))
            return

        self.stdout.write(f"{len(rows)} entrées trouvées dans metadsf")

        if dry_run:
            self.stdout.write(self.style.WARNING("[dry-run] Aucune modification appliquée"))
            for mode, libelle, position in rows:
                self.stdout.write(f"{mode} — {libelle} (position: {position})")
            return

        vocab, created = VocabularySet.objects.get_or_create(
            organisation=organisation,
            code=code,
            defaults={"name": name},
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"VocabularySet '{code}' créé"))
        else:
            self.stdout.write(f"VocabularySet '{code}' existant — mise à jour des entrées")

        existing_codes = set(vocab.entries.values_list("code", flat=True))
        source_codes = {row[0] for row in rows}

        created_count = 0
        updated_count = 0

        for mode, libelle, position in rows:
            _, entry_created = VocabularyEntry.objects.update_or_create(
                vocabulary_set=vocab,
                code=mode,
                defaults={
                    "label": libelle,
                    "position": position,
                    "is_active": True,
                },
            )
            if entry_created:
                created_count += 1
            else:
                updated_count += 1

        # Entrées existantes dans notre DB mais absentes dans metadsf → désactiver
        removed_codes = existing_codes - source_codes
        deactivated_count = 0

        if removed_codes:
            deactivated_count = VocabularyEntry.objects.filter(
                vocabulary_set=vocab,
                code__in=removed_codes,
                is_active=True,
            ).update(is_active=False)

            self.stdout.write(
                self.style.WARNING(
                    f"{deactivated_count} entrée(s) désactivée(s) (absentes de metadsf) : {', '.join(sorted(removed_codes))}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"  ✓ {created_count} créée(s), {updated_count} mise(s) à jour, {deactivated_count} désactivée(s)"
            )
        )
