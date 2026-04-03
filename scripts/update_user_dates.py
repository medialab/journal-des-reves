#!/usr/bin/env python
"""
Script pour modifier la date de création (date_joined) des comptes admin et Maud
au 15 février 2026.
"""
import django
import os
import sys
from datetime import datetime

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
# Ajouter le répertoire backend au path Python
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
sys.path.insert(0, backend_dir)

django.setup()

from django.contrib.auth.models import User
from django.utils import timezone

def update_user_date_joined(username, target_date):
    """Met à jour la date de création d'un utilisateur"""
    try:
        user = User.objects.get(username=username)
        old_date = user.date_joined
        
        # Convertir la date en datetime avec timezone
        target_datetime = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
        user.date_joined = target_datetime
        user.save()
        
        print(f"✅ {username}: {old_date} → {user.date_joined}")
        return True
    except User.DoesNotExist:
        print(f"❌ L'utilisateur '{username}' n'existe pas")
        return False
    except Exception as e:
        print(f"❌ Erreur pour '{username}': {e}")
        return False

def main():
    """Modifie les dates de création des comptes admin et Maud"""
    print("📅 Modification des dates de création des comptes...")
    print("-" * 60)
    
    # Date cible: 15 février 2026
    target_date = datetime(2026, 2, 15).date()
    
    # Listes des utilisateurs à modifier
    usernames = ['admin', 'Maud']
    
    success_count = 0
    for username in usernames:
        if update_user_date_joined(username, target_date):
            success_count += 1
    
    print("-" * 60)
    print(f"✨ {success_count}/{len(usernames)} compte(s) modifié(s) avec succès!")

if __name__ == '__main__':
    main()
