# Generated manually to add stable public UUID identifiers to all reves models.

import uuid

from django.db import migrations, models


PUBLIC_KEY_MODEL_NAMES = [
    'Profil',
    'ReveImageModalite',
    'ReveEmotion',
    'ReveEmotionCustom',
    'ReveElementCustom',
    'Reve',
    'Questionnaire',
    'Notification',
]


def populate_public_keys(apps, schema_editor):
    for model_name in PUBLIC_KEY_MODEL_NAMES:
        model = apps.get_model('reves', model_name)
        for obj in model.objects.filter(key__isnull=True).iterator():
            obj.key = uuid.uuid4()
            obj.save(update_fields=['key'])


class Migration(migrations.Migration):

    dependencies = [
        ('reves', '0038_profil_consent_age_vulnerability_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profil',
            name='key',
            field=models.UUIDField(blank=True, editable=False, null=True, verbose_name='Clé publique'),
        ),
        migrations.AddField(
            model_name='reveimagemodalite',
            name='key',
            field=models.UUIDField(blank=True, editable=False, null=True, verbose_name='Clé publique'),
        ),
        migrations.AddField(
            model_name='reveemotion',
            name='key',
            field=models.UUIDField(blank=True, editable=False, null=True, verbose_name='Clé publique'),
        ),
        migrations.AddField(
            model_name='reveemotioncustom',
            name='key',
            field=models.UUIDField(blank=True, editable=False, null=True, verbose_name='Clé publique'),
        ),
        migrations.AddField(
            model_name='reveelementcustom',
            name='key',
            field=models.UUIDField(blank=True, editable=False, null=True, verbose_name='Clé publique'),
        ),
        migrations.AddField(
            model_name='reve',
            name='key',
            field=models.UUIDField(blank=True, editable=False, null=True, verbose_name='Clé publique'),
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='key',
            field=models.UUIDField(blank=True, editable=False, null=True, verbose_name='Clé publique'),
        ),
        migrations.AddField(
            model_name='notification',
            name='key',
            field=models.UUIDField(blank=True, editable=False, null=True, verbose_name='Clé publique'),
        ),
        migrations.RunPython(populate_public_keys, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='profil',
            name='key',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Clé publique'),
        ),
        migrations.AlterField(
            model_name='reveimagemodalite',
            name='key',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Clé publique'),
        ),
        migrations.AlterField(
            model_name='reveemotion',
            name='key',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Clé publique'),
        ),
        migrations.AlterField(
            model_name='reveemotioncustom',
            name='key',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Clé publique'),
        ),
        migrations.AlterField(
            model_name='reveelementcustom',
            name='key',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Clé publique'),
        ),
        migrations.AlterField(
            model_name='reve',
            name='key',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Clé publique'),
        ),
        migrations.AlterField(
            model_name='questionnaire',
            name='key',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Clé publique'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='key',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Clé publique'),
        ),
    ]
