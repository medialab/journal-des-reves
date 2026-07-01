# Generated manually to repair legacy rows whose participant_key drifted away from Profil.key.

from django.db import migrations


def sync_participant_keys_from_user(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE reves_questionnaire
            SET participant_key = (
                SELECT reves_profil.key
                FROM reves_profil
                WHERE reves_profil.user_id = reves_questionnaire.user_id
            )
            WHERE user_id IS NOT NULL
              AND EXISTS (
                SELECT 1
                FROM reves_profil
                WHERE reves_profil.user_id = reves_questionnaire.user_id
            )
            """
        )
        cursor.execute(
            """
            UPDATE reves_reve
            SET participant_key = (
                SELECT reves_profil.key
                FROM reves_profil
                WHERE reves_profil.user_id = reves_reve.user_id
            )
            WHERE user_id IS NOT NULL
              AND EXISTS (
                SELECT 1
                FROM reves_profil
                WHERE reves_profil.user_id = reves_reve.user_id
            )
            """
        )


class Migration(migrations.Migration):

    dependencies = [
        ('reves', '0042_participant_key'),
    ]

    operations = [
        migrations.RunPython(sync_participant_keys_from_user, migrations.RunPython.noop),
    ]