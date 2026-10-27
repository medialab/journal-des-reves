from django.db import migrations, models


def copy_legacy_sleep_answers(apps, schema_editor):
    Questionnaire = apps.get_model("reves", "Questionnaire")
    pens_mapping = {
        "pens_trav": "travail",
        "pens_fin": "finances",
        "pens_fam": "famille",
        "pens_proch": "proches",
        "pens_actu": "actualite",
        "pens_autre": "autre",
        "pens_rien": "rien",
    }
    content_mapping = {
        "cont_tv": "television",
        "cont_series_films": "series_films",
        "cont_rs": "reseaux_sociaux",
        "cont_jeux": "jeux_videos",
        "cont_livres": "livres_journaux",
        "cont_rien": "rien",
        "cont_autre": "autre",
    }
    for questionnaire in Questionnaire.objects.all().iterator():
        questionnaire.pens_avant_dormir = [
            value for field, value in pens_mapping.items()
            if getattr(questionnaire, field)
        ]
        questionnaire.contenus_avant_dormir = [
            value for field, value in content_mapping.items()
            if getattr(questionnaire, field)
        ]
        questionnaire.save(update_fields=["pens_avant_dormir", "contenus_avant_dormir"])


class Migration(migrations.Migration):
    dependencies = [
        ("reves", "0047_profil_progression"),
    ]

    operations = [
        migrations.AddField(
            model_name="questionnaire",
            name="pens_avant_dormir",
            field=models.JSONField(blank=True, default=list, help_text="Liste des réponses sélectionnées avant de s’endormir", verbose_name="Pensées avant de s’endormir"),
        ),
        migrations.AddField(
            model_name="questionnaire",
            name="contenus_avant_dormir",
            field=models.JSONField(blank=True, default=list, help_text="Liste des contenus ou activités sélectionnés avant de s’endormir", verbose_name="Contenus ou activités avant de s’endormir"),
        ),
        migrations.RunPython(copy_legacy_sleep_answers, migrations.RunPython.noop),
    ]
