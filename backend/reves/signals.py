from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from .services.email_service import send_welcome_email


@receiver(post_save, sender=User)
def create_profil_on_user_creation(sender, instance, created, **kwargs):
    """
    Créer automatiquement un profil Profil quand un utilisateur est créé
    """
    if created:
        from .models import Profil
        Profil.objects.get_or_create(
            user=instance,
            defaults={'email': instance.email}
        )


@receiver(user_logged_in)
def send_welcome_email_on_first_login(sender, request, user, **kwargs):
    """
    Envoyer un email de bienvenue à la première connexion
    EN DÉVELOPPEMENT: Marquer comme envoyé sans l'envoyer réellement
    """
    try:
        profil = user.profil
        
        # Envoyer l'email seulement si ce n'a pas déjà été fait
        if not profil.welcome_email_sent:
            # EN DÉVELOPPEMENT: Ne pas envoyer, juste marquer comme envoyé
            # send_welcome_email(user, profil)
            
            # Marquer l'email comme envoyé sans l'envoyer
            profil.welcome_email_sent = True
            profil.save()
    except ObjectDoesNotExist:
        # Si le profil n'existe pas, on ne fait rien
        pass
