#!/usr/bin/env python
"""
Script pour modifier la date de création des Profils (created_at)
des comptes admin et Maud au 15 février 2026.
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
from reves.models import Profil
from django.utils import timezone

def update_profil_created_at(username, target_date):
    """Met à jour la date de création d'un profil"""
    try:
        user = User.objects.get(username=username)
        profil = Profil.objects.get(user=user)
        old_date = profil.created_at
        
        # Convertir la date en datetime avec timezone
        target_datetime = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
        profil.created_at = target_datetime
        profil.save()
        
        print(f"✅ {username}: {old_date} → {profil.created_at}")
        return True
    except User.DoesNotExist:
        print(f"❌ L'utilisateur '{username}' n'existe pas")
        return False
    except Profil.DoesNotExist:
        print(f"❌ Le profil de '{username}' n'existe pas")
        return False
    except Exception as e:
        print(f"❌ Erreur pour '{username}': {e}")
        return False

def main():
    """Modifie les dates de création des profils admin et Maud"""
    print("📅 Modification des dates de création des profils...")
    print("-" * 60)
    
    # Date cible: 15 février 2026
    target_date = datetime(2026, 2, 15).date()
    
    # Listes des utilisateurs à modifier
    usernames = ['admin', 'Maud']
    
    success_count = 0
    for username in usernames:
        if update_profil_created_at(username, target_date):
            success_count += 1
    
    print("-" * 60)
    print(f"✨ {success_count}/{len(usernames)} profil(s) modifié(s) avec succès!")

if __name__ == '__main__':
    main()
