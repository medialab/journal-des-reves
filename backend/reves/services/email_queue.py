from django.utils import timezone

from reves.models import EmailReminderTask


def enqueue_reminder(profil, reminder_type):
    """Create or reopen the single recurring task for a profile and type."""
    task, created = EmailReminderTask.objects.get_or_create(
        profil=profil,
        reminder_type=reminder_type,
        defaults={"available_at": timezone.now()},
    )
    if not created and task.status != EmailReminderTask.Status.PENDING:
        task.status = EmailReminderTask.Status.PENDING
        task.attempts = 0
        task.available_at = timezone.now()
        task.sent_at = None
        task.last_error = ""
        task.save(
            update_fields=[
                "status",
                "attempts",
                "available_at",
                "sent_at",
                "last_error",
                "updated_at",
            ]
        )
    return task, created
