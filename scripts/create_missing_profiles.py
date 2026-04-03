#!/usr/bin/env python
"""
Script pour créer les Profils manquants pour les utilisateurs existants
Utile si des utilisateurs (comme l'admin) n'ont pas de profil associé
"""
import django
import os
import sys

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
# Ajouter le répertoire backend au path Python
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
sys.path.insert(0, backend_dir)

django.setup()

from django.contrib.auth.models import User
from reves.models import Profil

def create_missing_profiles():
    """Crée un Profil pour chaque utilisateur qui n'en a pas"""
    users_without_profil = []
    created_count = 0
    
    for user in User.objects.all():
        if not hasattr(user, 'profil'):
            try:
                # Créer le profil avec l'email de l'utilisateur
                profil = Profil.objects.create(
                    user=user,
                    email=user.email if user.email else f"{user.username}@example.com"
                )
                print(f"✅ Profil créé pour l'utilisateur '{user.username}' (email: {profil.email})")
                created_count += 1
            except Exception as e:
                print(f"❌ Erreur création profil pour '{user.username}': {e}")
                users_without_profil.append(user.username)
        else:
            print(f"✓ L'utilisateur '{user.username}' a déjà un profil")
    
    print(f"\n📊 Résumé:")
    print(f"   - Profils créés: {created_count}")
    if users_without_profil:
        print(f"   - Erreurs: {', '.join(users_without_profil)}")

if __name__ == '__main__':
    create_missing_profiles()
