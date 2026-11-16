from django.db import migrations, models


def populate_paris_region(apps, schema_editor):
    Questionnaire = apps.get_model("reves", "Questionnaire")
    Questionnaire.objects.filter(
        habitat=5,
    ).update(region="Île-de-France")


class Migration(migrations.Migration):

    dependencies = [
        ("reves", "0055_email_reminder_types"),
    ]

    operations = [
        migrations.AddField(
            model_name="questionnaire",
            name="region",
            field=models.CharField(
                blank=True,
                choices=[
                    ("Île-de-France", "Île-de-France"),
                    ("Auvergne-Rhône-Alpes", "Auvergne-Rhône-Alpes"),
                    ("Bourgogne-Franche-Comté", "Bourgogne-Franche-Comté"),
                    ("Bretagne", "Bretagne"),
                    ("Centre-Val de Loire", "Centre-Val de Loire"),
                    ("Corse", "Corse"),
                    ("Grand Est", "Grand Est"),
                    ("Hauts-de-France", "Hauts-de-France"),
                    ("Normandie", "Normandie"),
                    ("Nouvelle-Aquitaine", "Nouvelle-Aquitaine"),
                    ("Occitanie", "Occitanie"),
                    ("Pays de la Loire", "Pays de la Loire"),
                    ("Provence-Alpes-Côte d'Azur", "Provence-Alpes-Côte d'Azur"),
                    ("Guadeloupe", "Guadeloupe"),
                    ("Guyane", "Guyane"),
                    ("La Réunion", "La Réunion"),
                    ("Martinique", "Martinique"),
                    ("Mayotte", "Mayotte"),
                ],
                max_length=64,
                null=True,
                verbose_name="Région",
            ),
        ),
        migrations.RunPython(populate_paris_region, migrations.RunPython.noop),
    ]
