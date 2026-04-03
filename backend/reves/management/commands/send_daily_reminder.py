"""
Commande pour envoyer des rappels quotidiens aux utilisateurs pour enregistrer un rêve.
À exécuter chaque matin (e.g., 8:00 AM via cron ou scheduler).

Usage:
    python manage.py send_daily_reminder
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from reves.models import Profil, Notification
try:
    from webpush import send_user_notification
    WEBPUSH_AVAILABLE = True
except ImportError:
    WEBPUSH_AVAILABLE = False


class Command(BaseCommand):
    help = "Envoie des rappels quotidiens aux utilisateurs pour enregistrer un rêve"

    def handle(self, *args, **options):
        """
        Envoyer des rappels à tous les utilisateurs actifs.
        Un rappel par utilisateur et par jour maximum.
        """
        self.stdout.write(self.style.SUCCESS('Début de l\'envoi des rappels quotidiens...'))
        
        # Obtenir tous les profils actifs avec des utilisateurs
        profils = Profil.objects.filter(
            user__is_active=True
        ).select_related('user')
        
        count = 0
        for profil in profils:
            # Vérifier si une notification a déjà été envoyée aujourd'hui
            today = timezone.now().date()
            existing_notification = Notification.objects.filter(
                profil=profil,
                notification_type=Notification.NotificationType.DAILY_REMINDER,
                created_at__date=today
            ).exists()
            
            if not existing_notification:
                # Créer la notification
                Notification.objects.create(
                    profil=profil,
                    notification_type=Notification.NotificationType.DAILY_REMINDER,
                    title="Avez-vous rêvé cette nuit ?",
                    message="N'oubliez pas d'enregistrer votre rêve de la nuit passée. "
                            "Plus vous documentez vos rêves, plus l'étude sera enrichie!"
                )
                count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Notification BD créée pour {profil.user.username}'))

                # Envoyer la push notification si django-webpush est disponible
                if WEBPUSH_AVAILABLE:
                    try:
                        push_payload = {
                            "head": "Journal des Rêves 🌙",
                            "body": "Avez-vous rêvé cette nuit ? N'oubliez pas d'enregistrer votre rêve !",
                            "icon": "/static/reves/icons/icon-192x192.png",
                            "url": "/enregistrer/",
                        }
                        send_user_notification(
                            user=profil.user,
                            payload=push_payload,
                            ttl=43200  # 12 heures
                        )
                        self.stdout.write(self.style.SUCCESS(f'  📳 Push envoyé à {profil.user.username}'))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'  ⚠ Push échoué pour {profil.user.username}: {e}'))
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n{count} rappels quotidiens ont été envoyés avec succès!'
            )
        )
