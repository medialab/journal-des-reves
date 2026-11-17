"""Envoie progressivement la file commune des relances e-mail."""

from datetime import timedelta
from smtplib import SMTPException

from django.core.mail import BadHeaderError
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from reves.models import (
    EmailReminderLock,
    EmailReminderTask,
    Notification,
)
from reves.services.email_service import (
    send_dream_reminder_email,
    send_questionnaire_reminder_email,
)


class Command(BaseCommand):
    help = "Envoie au plus un e-mail de relance toutes les 90 secondes"
    MIN_INTERVAL = timedelta(seconds=90)
    HOURLY_LIMIT = 25
    MAX_ATTEMPTS = 5

    def handle(self, *args, **options):
        with transaction.atomic():
            lock, _ = EmailReminderLock.objects.get_or_create(pk=1)
            EmailReminderLock.objects.select_for_update().get(pk=lock.pk)
            self._send_one()

    def _send_one(self):
        now = timezone.now()
        last_sent = (
            EmailReminderTask.objects.filter(
                status=EmailReminderTask.Status.SENT,
                sent_at__isnull=False,
            )
            .order_by("-sent_at")
            .first()
        )
        if last_sent and now - last_sent.sent_at < self.MIN_INTERVAL:
            self.stdout.write("Cadence minimale non atteinte ; aucun envoi.")
            return

        hourly_count = EmailReminderTask.objects.filter(
            status=EmailReminderTask.Status.SENT,
            sent_at__gte=now - timedelta(hours=1),
        ).count()
        if hourly_count >= self.HOURLY_LIMIT:
            self.stdout.write("Plafond horaire atteint ; aucun envoi.")
            return

        task = (
            EmailReminderTask.objects.select_related("profil", "profil__user")
            .filter(
                status=EmailReminderTask.Status.PENDING,
                available_at__lte=now,
                attempts__lt=self.MAX_ATTEMPTS,
            )
            .order_by("created_at")
            .first()
        )
        if task is None:
            self.stdout.write("Aucune relance en attente.")
            return

        try:
            if task.reminder_type == EmailReminderTask.ReminderType.QUESTIONNAIRE:
                send_questionnaire_reminder_email(task.profil.user, task.profil)
                notification_type = Notification.NotificationType.QUESTIONNAIRE_EMAIL_REMINDER
                title = "Il vous manque une étape pour lancer vos 7 nuits"
                message = "Complétez le questionnaire pour commencer l'enquête."
            else:
                send_dream_reminder_email(task.profil.user, task.profil)
                notification_type = Notification.NotificationType.DREAM_EMAIL_REMINDER
                title = "Nuit 1 sur 7 : de quoi avez-vous rêvé cette nuit ?"
                message = "Enregistrez un rêve ou indiquez que vous ne vous en souvenez pas."
        except (BadHeaderError, OSError, SMTPException, RuntimeError) as exc:
            task.attempts += 1
            task.last_error = str(exc)
            task.available_at = now + timedelta(minutes=min(60, 2 ** task.attempts))
            if task.attempts >= self.MAX_ATTEMPTS:
                task.status = EmailReminderTask.Status.FAILED
            task.save(update_fields=[
                "attempts", "last_error", "available_at", "status", "updated_at",
            ])
            self.stderr.write(self.style.ERROR(f"Échec de la relance {task.pk}: {exc}"))
            return

        task.status = EmailReminderTask.Status.SENT
        task.sent_at = now
        task.save(update_fields=["status", "sent_at", "updated_at"])
        Notification.objects.create(
            profil=task.profil,
            notification_type=notification_type,
            title=title,
            message=message,
        )
        self.stdout.write(self.style.SUCCESS(
            f"Relance envoyée à {task.profil.user.username}."
        ))
