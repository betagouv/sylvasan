from django.db import migrations


def backfill_vocabulary_categories(apps, schema_editor):
    """Assigne la catégorie 'forest' aux organisations existantes pour préserver leur accès aux référentiels."""
    Organisation = apps.get_model("organisations", "Organisation")
    Organisation.objects.filter(vocabulary_categories=[]).update(vocabulary_categories=["forest"])


def reverse_backfill_vocabulary_categories(apps, schema_editor):
    Organisation = apps.get_model("organisations", "Organisation")
    Organisation.objects.filter(vocabulary_categories=["forest"]).update(vocabulary_categories=[])


class Migration(migrations.Migration):

    dependencies = [
        ("organisations", "0006_organisation_vocabulary_categories"),
    ]

    operations = [
        migrations.RunPython(
            backfill_vocabulary_categories,
            reverse_code=reverse_backfill_vocabulary_categories,
        ),
    ]
