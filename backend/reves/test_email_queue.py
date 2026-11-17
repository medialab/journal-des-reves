from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from .models import EmailReminderLock, EmailReminderTask, Notification, Profil, Questionnaire


class EmailReminderQueueTests(TestCase):
    def make_profil(self, username):
        user = User.objects.create_user(username=username, password="test-pass")
        profil = user.profil
        profil.email = f"{username}@example.test"
        profil.save(update_fields=["email"])
        return profil

    def make_questionnaire_candidate(self, username):
        profil = self.make_profil(username)
        Profil.objects.filter(pk=profil.pk).update(
            created_at=timezone.now() - timedelta(days=4),
        )
        return profil

    def make_dream_candidate(self, username):
        profil = self.make_profil(username)
        Questionnaire.objects.create(
            profil=profil,
            is_completed=True,
            completed_at=timezone.now() - timedelta(days=8),
        )
        return profil

    def test_questionnaire_reminder_is_queued(self):
        profil = self.make_questionnaire_candidate("questionnaire")

        call_command("send_questionnaire_reminder")

        task = EmailReminderTask.objects.get(profil=profil)
        self.assertEqual(
            task.reminder_type,
            EmailReminderTask.ReminderType.QUESTIONNAIRE,
        )
        self.assertEqual(task.status, EmailReminderTask.Status.PENDING)
        self.assertEqual(len(mail.outbox), 0)

    def test_running_producer_twice_does_not_duplicate_task(self):
        profil = self.make_questionnaire_candidate("idempotent")

        call_command("send_questionnaire_reminder")
        call_command("send_questionnaire_reminder")

        self.assertEqual(
            EmailReminderTask.objects.filter(profil=profil).count(),
            1,
        )

    def test_dream_reminder_is_queued(self):
        profil = self.make_dream_candidate("dream")

        call_command("send_dream_reminder")

        task = EmailReminderTask.objects.get(profil=profil)
        self.assertEqual(task.reminder_type, EmailReminderTask.ReminderType.DREAM)
        self.assertEqual(task.status, EmailReminderTask.Status.PENDING)

    @patch("reves.management.commands.send_queued_email_reminders.send_questionnaire_reminder_email")
    def test_questionnaire_and_dream_tasks_share_hourly_limit(self, send_email):
        for index in range(25):
            profil = self.make_profil(f"limit-{index}")
            EmailReminderTask.objects.create(
                profil=profil,
                reminder_type=(
                    EmailReminderTask.ReminderType.QUESTIONNAIRE
                    if index % 2
                    else EmailReminderTask.ReminderType.DREAM
                ),
                status=EmailReminderTask.Status.SENT,
                sent_at=timezone.now() - timedelta(minutes=10),
            )
        pending_profil = self.make_profil("limit-pending")
        EmailReminderTask.objects.create(
            profil=pending_profil,
            reminder_type=EmailReminderTask.ReminderType.QUESTIONNAIRE,
        )

        call_command("send_queued_email_reminders")

        self.assertEqual(send_email.call_count, 0)
        self.assertEqual(
            EmailReminderTask.objects.get(profil=pending_profil).status,
            EmailReminderTask.Status.PENDING,
        )

    @patch("reves.management.commands.send_queued_email_reminders.send_questionnaire_reminder_email")
    def test_ninety_second_interval_is_respected(self, send_email):
        old_profil = self.make_profil("interval-old")
        EmailReminderTask.objects.create(
            profil=old_profil,
            reminder_type=EmailReminderTask.ReminderType.QUESTIONNAIRE,
            status=EmailReminderTask.Status.SENT,
            sent_at=timezone.now() - timedelta(seconds=89),
        )
        pending_profil = self.make_profil("interval-pending")
        pending = EmailReminderTask.objects.create(
            profil=pending_profil,
            reminder_type=EmailReminderTask.ReminderType.QUESTIONNAIRE,
        )

        call_command("send_queued_email_reminders")

        send_email.assert_not_called()
        pending.refresh_from_db()
        self.assertEqual(pending.status, EmailReminderTask.Status.PENDING)

    @patch("reves.management.commands.send_queued_email_reminders.send_questionnaire_reminder_email")
    def test_notification_is_created_only_after_success(self, send_email):
        profil = self.make_profil("notification")
        task = EmailReminderTask.objects.create(
            profil=profil,
            reminder_type=EmailReminderTask.ReminderType.QUESTIONNAIRE,
        )
        send_email.side_effect = OSError("SMTP indisponible")

        call_command("send_queued_email_reminders")

        self.assertFalse(
            Notification.objects.filter(
                profil=profil,
                notification_type=Notification.NotificationType.QUESTIONNAIRE_EMAIL_REMINDER,
            ).exists()
        )
        task.refresh_from_db()
        self.assertEqual(task.status, EmailReminderTask.Status.PENDING)
        self.assertEqual(task.attempts, 1)

        send_email.side_effect = None
        task.available_at = timezone.now()
        task.save(update_fields=["available_at", "updated_at"])
        call_command("send_queued_email_reminders")

        self.assertTrue(
            Notification.objects.filter(
                profil=profil,
                notification_type=Notification.NotificationType.QUESTIONNAIRE_EMAIL_REMINDER,
            ).exists()
        )

    @patch("reves.management.commands.send_queued_email_reminders.Command._send_one")
    def test_worker_uses_database_lock(self, send_one):
        call_command("send_queued_email_reminders")

        self.assertTrue(EmailReminderLock.objects.filter(pk=1).exists())
        send_one.assert_called_once()
