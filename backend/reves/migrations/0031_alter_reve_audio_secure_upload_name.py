from django.db import migrations, models
import reves.models


class Migration(migrations.Migration):

    dependencies = [
        ('reves', '0030_add_recording_groups'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reve',
            name='audio',
            field=models.FileField(blank=True, help_text='Enregistrement audio du rêve (WAV)', null=True, upload_to=reves.models.reve_audio_upload_to),
        ),
    ]
