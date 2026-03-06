"""
Commande pour envoyer des rappels après 7 jours d'inscription pour remplir le questionnaire.
À exécuter une fois par jour (e.g., via cron ou scheduler).

Usage:
    python manage.py send_questionnaire_reminder
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from polls.models import Profil, Notification, Questionnaire


class Command(BaseCommand):
    help = "Envoie des rappels pour remplir le questionnaire après 7 jours d'inscription"

    def handle(self, *args, **options):
        """
        Envoyer un rappel aux utilisateurs qui ont créé leur compte il y a 7 jours
        et qui n'ont pas encore rempli le questionnaire.
        """
        self.stdout.write(self.style.SUCCESS('Début de l\'envoi des rappels du questionnaire...'))
        
        # Calculer la date limite (7 jours après création)
        now = timezone.now()
        seven_days_ago = now - timedelta(days=7)
        eight_days_ago = now - timedelta(days=8)
        
        # Trouver les profils créés il y a environ 7 jours
        recent_profils = Profil.objects.filter(
            user__is_active=True,
            created_at__gte=eight_days_ago,
            created_at__lte=seven_days_ago
        ).select_related('user')
        
        count = 0
        for profil in recent_profils:
            # Vérifier si l'utilisateur a déjà rempli le questionnaire
            has_questionnaire = Questionnaire.objects.filter(
                profil=profil
            ).exists()
            
            if not has_questionnaire:
                # Vérifier si un rappel a déjà été envoyé
                existing_notification = Notification.objects.filter(
                    profil=profil,
                    notification_type=Notification.NotificationType.QUESTIONNAIRE_REMINDER
                ).exists()
                
                if not existing_notification:
                    # Créer la notification
                    notification = Notification.objects.create(
                        profil=profil,
                        notification_type=Notification.NotificationType.QUESTIONNAIRE_REMINDER,
                        title="Bienvenue ! Complétez votre profil",
                        message="Une semaine a passé depuis votre inscription ! "
                                "Aidez-nous à mieux comprendre votre profil en remplissant le questionnaire. "
                                "Cela nous prendra seulement 10-15 minutes."
                    )
                    count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Rappel questionnaire créé pour {profil.user.username}'
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n{count} rappels du questionnaire ont été envoyés avec succès!'
            )
        )
