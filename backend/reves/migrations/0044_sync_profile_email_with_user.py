# Generated manually to keep Profil.email aligned with the linked User.email.

from django.db import migrations


def sync_profile_emails(apps, schema_editor):
    Profil = apps.get_model('reves', 'Profil')

    for profil in Profil.objects.select_related('user').all().iterator():
        user_email = (profil.user.email or '').strip()
        profile_email = (profil.email or '').strip()

        if user_email:
            if profile_email != user_email:
                Profil.objects.filter(pk=profil.pk).update(email=user_email)
        elif profile_email:
            profil.user.email = profile_email
            profil.user.save(update_fields=['email'])


class Migration(migrations.Migration):

    dependencies = [
        ('reves', '0043_sync_participant_keys_from_user'),
    ]

    operations = [
        migrations.RunPython(sync_profile_emails, migrations.RunPython.noop),
    ]