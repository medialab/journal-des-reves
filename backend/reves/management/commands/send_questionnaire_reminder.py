"""Envoie les relances e-mail du questionnaire."""

from datetime import timedelta
from smtplib import SMTPException

from django.core.mail import BadHeaderError
from django.core.management.base import BaseCommand
from django.utils import timezone

from reves.models import Notification, Profil, Questionnaire
from reves.services.email_service import send_questionnaire_reminder_email


class Command(BaseCommand):
    help = "Envoie les relances e-mail du questionnaire à partir de J+3"
    MAX_REMINDERS = 3

    def handle(self, *args, **options):
        now = timezone.now()
        three_days_ago = now - timedelta(days=3)
        one_week_ago = now - timedelta(days=7)
        count = 0
        errors = 0

        profils = Profil.objects.filter(
            user__is_active=True,
            created_at__lte=three_days_ago,
        ).select_related("user")
        for profil in profils:
            if Questionnaire.objects.filter(
                profil=profil,
                is_completed=True,
            ).exists():
                continue

            last_email = Notification.objects.filter(
                profil=profil,
                notification_type=Notification.NotificationType.QUESTIONNAIRE_EMAIL_REMINDER,
            ).order_by("-created_at").first()
            reminder_count = Notification.objects.filter(
                profil=profil,
                notification_type=Notification.NotificationType.QUESTIONNAIRE_EMAIL_REMINDER,
            ).count()
            if reminder_count >= self.MAX_REMINDERS:
                continue
            if last_email and last_email.created_at > one_week_ago:
                continue

            try:
                send_questionnaire_reminder_email(profil.user, profil)
            except (BadHeaderError, OSError, SMTPException) as exc:
                errors += 1
                self.stderr.write(self.style.ERROR(
                    f"✗ Échec pour {profil.user.username}: {exc}"
                ))
                continue

            Notification.objects.create(
                profil=profil,
                notification_type=Notification.NotificationType.QUESTIONNAIRE_EMAIL_REMINDER,
                title="Il te manque une étape pour lancer tes 7 nuits",
                message="Complète le questionnaire pour commencer l'enquête.",
            )
            count += 1
            self.stdout.write(self.style.SUCCESS(
                f"✓ Relance questionnaire envoyée à {profil.user.username}"
            ))

        self.stdout.write(self.style.SUCCESS(
            f"{count} relances envoyées, {errors} échec(s)."
        ))
