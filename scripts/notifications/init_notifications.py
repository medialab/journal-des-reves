#!/usr/bin/env python3
"""
Script d'initialisation pour le système de notifications
Exécute automatiquement les migrations et les tests
Utilisation: python3 init_notifications.py
"""

import os
import sys
import subprocess
from pathlib import Path

# Obtenir le répertoire du script
SCRIPT_DIR = Path(__file__).parent.absolute()
DJANGO_DIR = SCRIPT_DIR.parent.parent / 'backend'

def run_command(cmd, description):
    """Exécuter une commande et afficher le résultat"""
    print(f"\n📋 {description}...")
    print(f"   $ {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, cwd=DJANGO_DIR, check=True)
        print(f"✅ {description} - SUCCÈS\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - ERREUR\n")
        return False

def main():
    """Étapes d'initialisation"""
    print("=" * 60)
    print("🌙 Initialisation du Système de Notifications")
    print("=" * 60)
    
    # Vérifier que Django est installé
    try:
        import django
        print(f"✅ Django version: {django.get_version()}")
    except ImportError:
        print("❌ Django n'est pas installé. Exécutez: pip install django")
        return 1
    
    # 1. Créer les migrations
    if not run_command(
        [sys.executable, 'manage.py', 'makemigrations'],
        "Création des migrations"
    ):
        print("⚠️  La création des migrations a échoué")
    
    # 2. Appliquer les migrations
    if not run_command(
        [sys.executable, 'manage.py', 'migrate'],
        "Application des migrations"
    ):
        print("⚠️  L'application des migrations a échoué")
        return 1
    
    # 3. Tester les notifications
    print("\n📋 Test du système de notifications...")
    print("-" * 60)
    
    test_code = """
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from reves.models import Profil, Notification
from django.utils import timezone

# Compter les profils
profil_count = Profil.objects.count()
print(f"✅ {profil_count} profil(s) trouvé(s)")

# Compter les notifications
notification_count = Notification.objects.count()
print(f"✅ {notification_count} notification(s) trouvée(s)")

# Tester la création d'une notification
if profil_count > 0:
    profil = Profil.objects.first()
    test_notif = Notification.objects.create(
        profil=profil,
        notification_type='daily_reminder',
        title='Test Initialisation',
        message='Ceci est une notification de test pour valider l\\'installation'
    )
    print(f"✅ Notification test créée (ID: {test_notif.id})")
    print(f"✅ Utilisateur: {profil.user.username}")
else:
    print("⚠️  Aucun profil trouvé - créez d'abord un utilisateur")

print("\\n✅ Système de notifications prêt à l'emploi!")
"""
    
    try:
        result = subprocess.run(
            [sys.executable, '-c', test_code],
            cwd=DJANGO_DIR,
            check=True,
            capture_output=False
        )
        print("\n✅ Tests - SUCCÈS")
    except subprocess.CalledProcessError:
        print("\n❌ Tests - ERREUR")
    
    # 4. Afficher les prochaines étapes
    print("\n" + "=" * 60)
    print("📚 PROCHAINES ÉTAPES")
    print("=" * 60)
    print("""
1. Configurer les tâches planifiées :
   
   Avec Cron (Linux/Mac):
   $ crontab -e
   
   Ajouter:
    0 8 * * * cd /path/to/site_reves/backend && python3 manage.py send_daily_reminder
    0 10 * * * cd /path/to/site_reves/backend && python3 manage.py send_questionnaire_reminder
   
   Avec APScheduler:
   $ pip install django-apscheduler
   (voir SETUP_NOTIFICATIONS.md)

2. Tester le système en local :
   $ python3 manage.py runserver
   
   Puis ouvrir:
   http://localhost:8000/polls/

3. Lire la documentation complète :
   - NOTIFICATIONS_IMPLEMENTATION.md (détails complets)
   - SETUP_NOTIFICATIONS.md (guide d'installation)

4. Créer un utilisateur de test (si pas encore fait):
   $ python3 manage.py createsuperuser

5. Accéder à l'admin Django:
   http://localhost:8000/admin/
   
   Pour gérer les notifications manuellement.
""")
    
    print("=" * 60)
    print("✅ Installation terminée avec succès!")
    print("=" * 60)
    return 0

if __name__ == '__main__':
    sys.exit(main())
