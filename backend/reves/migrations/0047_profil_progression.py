from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reves", "0046_alter_questionnaire_habitat"),
    ]

    operations = [
        migrations.AddField(
            model_name="profil",
            name="dernier_palier_vu",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="profil",
            name="profil_code",
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        migrations.AddField(
            model_name="profil",
            name="profil_revele_le",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
