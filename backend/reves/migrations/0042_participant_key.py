# Generated manually to replace the old profil foreign key with a stable participant UUID.

import uuid

from django.db import migrations, models


def populate_participant_keys(apps, schema_editor):
    profil_model = apps.get_model('reves', 'Profil')

    for model_name in ('Reve', 'Questionnaire'):
        model = apps.get_model('reves', model_name)
        for obj in model.objects.all().iterator():
            participant_key = None
            profil_id = getattr(obj, 'profil_id', None)

            if profil_id is not None:
                participant_key = profil_model.objects.filter(pk=profil_id).values_list('key', flat=True).first()

            if participant_key is None:
                participant_key = uuid.uuid4()

            model.objects.filter(pk=obj.pk).update(participant_key=participant_key)


class Migration(migrations.Migration):

    dependencies = [
        ('reves', '0041_profil_consent_sensitive_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='reve',
            name='participant_key',
            field=models.UUIDField(blank=True, editable=False, null=True, db_index=True, verbose_name='Clé du participant'),
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='participant_key',
            field=models.UUIDField(blank=True, editable=False, null=True, db_index=True, verbose_name='Clé du participant'),
        ),
        migrations.RunPython(populate_participant_keys, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='reve',
            name='participant_key',
            field=models.UUIDField(default=uuid.uuid4, editable=False, db_index=True, verbose_name='Clé du participant'),
        ),
        migrations.AlterField(
            model_name='questionnaire',
            name='participant_key',
            field=models.UUIDField(default=uuid.uuid4, editable=False, db_index=True, verbose_name='Clé du participant'),
        ),
        migrations.RemoveField(
            model_name='reve',
            name='profil',
        ),
        migrations.RemoveField(
            model_name='questionnaire',
            name='profil',
        ),
    ]