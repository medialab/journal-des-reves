from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def _send_templated_email(user, profil, subject, template_name):
    """Send a participant email with both text and HTML alternatives."""
    context = {
        "username": user.username,
    }
    text_content = render_to_string(f"emails/{template_name}.txt", context)
    html_content = render_to_string(f"emails/{template_name}.html", context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[profil.email],
    )
    msg.attach_alternative(html_content, "text/html")
    sent = msg.send(fail_silently=False)
    if sent != 1:
        raise RuntimeError(f"Email non envoyé à {profil.email}")
    return True


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


def send_questionnaire_reminder_email(user, profil):
    return _send_templated_email(
        user,
        profil,
        "Il te manque une étape pour lancer tes 7 nuits 🌙",
        "questionnaire_reminder",
    )


def send_dream_reminder_email(user, profil):
    return _send_templated_email(
        user,
        profil,
        "Nuit 1 sur 7 : de quoi as-tu rêvé cette nuit ?",
        "dream_reminder",
    )
