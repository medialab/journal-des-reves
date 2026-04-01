from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_welcome_email(user, profil):
    """Send welcome email on first login."""
    subject = "Bienvenue dans notre étude sur les rêves"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [profil.email]

    context = {
        "first_name": user.first_name or user.username,
        "username": user.username,
    }

    text_content = render_to_string("emails/welcome_email.txt", context)
    html_content = render_to_string("emails/welcome_email.html", context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=to_email,
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()

    profil.welcome_email_sent = True
    profil.save()

    return True
