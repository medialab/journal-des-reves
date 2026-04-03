from django.db import migrations, models


def backfill_completion_metadata(apps, schema_editor):
    Questionnaire = apps.get_model('reves', 'Questionnaire')

    for questionnaire in Questionnaire.objects.all().iterator():
        duration_seconds = None
        if questionnaire.created_at and questionnaire.updated_at:
            duration_seconds = max(
                0,
                int((questionnaire.updated_at - questionnaire.created_at).total_seconds()),
            )

        questionnaire.is_completed = True
        questionnaire.completed_at = questionnaire.updated_at or questionnaire.created_at
        questionnaire.completion_duration_seconds = duration_seconds
        questionnaire.save(
            update_fields=['is_completed', 'completed_at', 'completion_duration_seconds']
        )


class Migration(migrations.Migration):

    dependencies = [
        ('reves', '0027_questionnaire_det_1_questionnaire_det_2_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionnaire',
            name='completed_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Date de complétion'),
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='completion_duration_seconds',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Durée de passation (secondes)'),
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='is_completed',
            field=models.BooleanField(db_index=True, default=False, verbose_name='Questionnaire complété'),
        ),
        migrations.RunPython(backfill_completion_metadata, migrations.RunPython.noop),
    ]