"""Met en file les relances e-mail du questionnaire."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from reves.models import EmailReminderTask, Notification, Profil, Questionnaire
from reves.services.email_queue import enqueue_reminder


class Command(BaseCommand):
    help = "Met en file les relances questionnaire à partir de J+3"
    MAX_REMINDERS = 3

    def handle(self, *args, **options):
        now = timezone.now()
        three_days_ago = now - timedelta(days=3)
        one_week_ago = now - timedelta(days=7)
        count = 0

        profils = Profil.objects.filter(
            user__is_active=True,
            created_at__lte=three_days_ago,
        ).select_related("user")
        for profil in profils:
            if Questionnaire.objects.filter(profil=profil, is_completed=True).exists():
                continue

            reminders = Notification.objects.filter(
                profil=profil,
                notification_type=Notification.NotificationType.QUESTIONNAIRE_EMAIL_REMINDER,
            )
            last_email = reminders.order_by("-created_at").first()
            if reminders.count() >= self.MAX_REMINDERS:
                continue
            if last_email and last_email.created_at > one_week_ago:
                continue

            enqueue_reminder(
                profil,
                EmailReminderTask.ReminderType.QUESTIONNAIRE,
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f"{count} relance(s) questionnaire mise(s) en file."))
