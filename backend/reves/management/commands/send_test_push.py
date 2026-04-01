"""
Commande pour envoyer une push notification de test immédiatement.

Usage:
    python manage.py send_test_push --username <username>
    python manage.py send_test_push --all
"""

from django.core.management.base import BaseCommand, CommandError
from reves.models import Profil

try:
    from webpush import send_user_notification
    WEBPUSH_AVAILABLE = True
except ImportError:
    WEBPUSH_AVAILABLE = False


class Command(BaseCommand):
    help = "Envoie une push notification de test immédiate"

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Nom utilisateur cible')
        parser.add_argument('--all', action='store_true', help='Envoyer à tous les utilisateurs actifs')

    def handle(self, *args, **options):
        if not WEBPUSH_AVAILABLE:
            raise CommandError("django-webpush n'est pas installé correctement.")

        username = options.get('username')
        send_all = options.get('all')

        if not username and not send_all:
            raise CommandError("Utilise --username <nom> ou --all")

        if username and send_all:
            raise CommandError("Choisis soit --username, soit --all")

        profils = Profil.objects.filter(user__is_active=True).select_related('user')
        if username:
            profils = profils.filter(user__username=username)

        if not profils.exists():
            raise CommandError("Aucun profil correspondant trouvé.")

        sent = 0
        for profil in profils:
            try:
                payload = {
                    "head": "Test Push – Journal des Rêves 🌙",
                    "body": "Notification de test immédiate reçue ✅",
                    "icon": "/static/polls/icons/icon-192x192.png",
                    "url": "/polls/journal/",
                }
                send_user_notification(user=profil.user, payload=payload, ttl=60)
                sent += 1
                self.stdout.write(self.style.SUCCESS(f"✓ Push test envoyé à {profil.user.username}"))
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"⚠ Échec push pour {profil.user.username}: {exc}"))

        self.stdout.write(self.style.SUCCESS(f"\nTerminé : {sent} push(s) envoyé(s)."))
