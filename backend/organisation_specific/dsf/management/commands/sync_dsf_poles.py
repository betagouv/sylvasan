from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connections

from organisations.models import Organisation, Pole


class Command(BaseCommand):
    help = "Synchronise les pôles DSF depuis metadsf (unite ECHDSF)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche les changements sans les appliquer",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

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

        with connections["dsf_ref"].cursor() as cursor:
            cursor.execute("""
                SELECT mode, libelle, definition, position
                FROM metadsf.abmode
                WHERE unite = 'ECHDSF' AND mode != 'P'
                ORDER BY position NULLS LAST
            """)
            rows = cursor.fetchall()

        self.stdout.write(f"\n{len(rows)} pôles trouvés dans metadsf (ECHDSF)")

        if dry_run:
            self.stdout.write(self.style.WARNING("\n[dry-run] Pôles :"))
            for mode, libelle, definition, position in rows:
                self.stdout.write(f"{mode} — {libelle}")
                if definition:
                    self.stdout.write(f"{definition}")
            self.stdout.write(self.style.WARNING("\n[dry-run] Aucune modification appliquée"))
            return

        source_codes = {row[0] for row in rows}
        created_count = updated_count = deactivated_count = 0

        for mode, libelle, definition, _ in rows:
            _, created = Pole.objects.update_or_create(
                organisation=dsf,
                dsf_code=mode,
                defaults={
                    "name": libelle.title(),
                    "is_active": True,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        # Deactivate poles no longer in metadsf
        deactivated_count = (
            Pole.objects.filter(
                organisation=dsf,
                dsf_code__isnull=False,
                is_active=True,
            )
            .exclude(dsf_code__in=source_codes)
            .update(is_active=False)
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nPôles — {created_count} créés, {updated_count} mis à jour, {deactivated_count} désactivés"
            )
        )
