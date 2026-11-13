"""Envoie les relances e-mail pour commencer le journal de rêves."""

from datetime import timedelta
from smtplib import SMTPException

from django.core.mail import BadHeaderError
from django.core.management.base import BaseCommand
from django.utils import timezone

from reves.models import Notification, Profil, Questionnaire, Reve
from reves.services.email_service import send_dream_reminder_email


class Command(BaseCommand):
    help = "Relance les participants qui n'ont encore enregistré aucune nuit"
    MAX_REMINDERS = 6

    def handle(self, *args, **options):
        now = timezone.now()
        questionnaire_cutoff = now - timedelta(days=7)
        one_week_ago = now - timedelta(days=7)
        count = 0
        errors = 0

        profils = Profil.objects.filter(user__is_active=True).select_related("user")
        for profil in profils:
            questionnaire = Questionnaire.objects.filter(
                profil=profil,
                is_completed=True,
            ).order_by("-completed_at", "-created_at").first()
            if not questionnaire or not questionnaire.completed_at:
                continue
            if questionnaire.completed_at > questionnaire_cutoff:
                continue
            if Reve.objects.filter(profil=profil).exists():
                continue

            last_email = Notification.objects.filter(
                profil=profil,
                notification_type=Notification.NotificationType.DREAM_EMAIL_REMINDER,
            ).order_by("-created_at").first()
            reminder_count = Notification.objects.filter(
                profil=profil,
                notification_type=Notification.NotificationType.DREAM_EMAIL_REMINDER,
            ).count()
            if reminder_count >= self.MAX_REMINDERS:
                continue
            if last_email and last_email.created_at > one_week_ago:
                continue

            try:
                send_dream_reminder_email(profil.user, profil)
            except (BadHeaderError, OSError, SMTPException) as exc:
                errors += 1
                self.stderr.write(self.style.ERROR(
                    f"✗ Échec pour {profil.user.username}: {exc}"
                ))
                continue

            Notification.objects.create(
                profil=profil,
                notification_type=Notification.NotificationType.DREAM_EMAIL_REMINDER,
                title="Nuit 1 sur 7 : de quoi as-tu rêvé cette nuit ?",
                message="Enregistre un rêve ou indique que tu ne t'en souviens pas.",
            )
            count += 1
            self.stdout.write(self.style.SUCCESS(
                f"✓ Relance rêve envoyée à {profil.user.username}"
            ))

        self.stdout.write(self.style.SUCCESS(
            f"{count} relances envoyées, {errors} échec(s)."
        ))
