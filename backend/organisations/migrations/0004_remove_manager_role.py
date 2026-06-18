from django.db import migrations, models


def convert_manager_to_admin(apps, schema_editor):
    Membership = apps.get_model("organisations", "Membership")
    Membership.objects.filter(membership_type="manager").update(membership_type="admin")


class Migration(migrations.Migration):
    dependencies = [
        ("organisations", "0003_pole_dsf_code"),
    ]

    operations = [
        migrations.RunPython(convert_manager_to_admin, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="membership",
            name="membership_type",
            field=models.CharField(
                choices=[("admin", "Administrateur"), ("responder", "Répondant")],
                verbose_name="type de rôle",
            ),
        ),
    ]
