from django.db import migrations, models
import django.core.validators


def backfill_submission_numbers(apps, schema_editor):
    Questionnaire = apps.get_model('polls', 'Questionnaire')
    Profil = apps.get_model('polls', 'Profil')

    for profil in Profil.objects.all().iterator():
        completed = Questionnaire.objects.filter(
            profil=profil,
            is_completed=True,
        ).order_by('created_at', 'id')[:5]

        for index, questionnaire in enumerate(completed, start=1):
            questionnaire.submission_number = index
            questionnaire.save(update_fields=['submission_number'])


def clear_submission_numbers(apps, schema_editor):
    Questionnaire = apps.get_model('polls', 'Questionnaire')
    Questionnaire.objects.update(submission_number=None)


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0028_questionnaire_completion_tracking'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionnaire',
            name='submission_number',
            field=models.PositiveSmallIntegerField(
                blank=True,
                db_index=True,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(5),
                ],
                verbose_name='Numéro de soumission complète',
            ),
        ),
        migrations.RunPython(backfill_submission_numbers, clear_submission_numbers),
    ]
