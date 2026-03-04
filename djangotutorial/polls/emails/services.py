from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def send_welcome_email(user, profil):
    """
    Envoyer un email de bienvenue à la première connexion
    
    Args:
        user: User object
        profil: Profil object
    """
    subject = "Bienvenue dans notre étude sur les rêves"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [profil.email]
    
    # Contexte pour les templates
    context = {
        'first_name': user.first_name or user.username,
        'username': user.username,
    }
    
    # Générer le contenu texte et HTML
    text_content = render_to_string(
        'emails/welcome_email.txt',
        context
    )
    html_content = render_to_string(
        'emails/welcome_email.html',
        context
    )
    
    # Créer le message avec alternative HTML
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=to_email,
    )
    msg.attach_alternative(html_content, "text/html")
    
    # Envoyer l'email
    msg.send()
    
    # Marquer que l'email a été envoyé
    profil.welcome_email_sent = True
    profil.save()
    
    return True
