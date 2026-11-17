"""Met en file les relances e-mail pour commencer le journal de rêves."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from reves.models import EmailReminderTask, Notification, Profil, Questionnaire, Reve
from reves.services.email_queue import enqueue_reminder


class Command(BaseCommand):
    help = "Met en file les relances rêve des participants éligibles"
    MAX_REMINDERS = 6

    def handle(self, *args, **options):
        now = timezone.now()
        questionnaire_cutoff = now - timedelta(days=7)
        one_week_ago = now - timedelta(days=7)
        count = 0

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

            reminders = Notification.objects.filter(
                profil=profil,
                notification_type=Notification.NotificationType.DREAM_EMAIL_REMINDER,
            )
            last_email = reminders.order_by("-created_at").first()
            if reminders.count() >= self.MAX_REMINDERS:
                continue
            if last_email and last_email.created_at > one_week_ago:
                continue

            enqueue_reminder(profil, EmailReminderTask.ReminderType.DREAM)
            count += 1

        self.stdout.write(self.style.SUCCESS(f"{count} relance(s) rêve mise(s) en file."))
