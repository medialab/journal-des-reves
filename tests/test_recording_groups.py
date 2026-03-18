#!/usr/bin/env python
"""
Script de test pour créer deux utilisateurs de test et vérifier les groupes
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, '/home/maudyaiche/dev/site_reves/djangotutorial')
django.setup()

from django.contrib.auth.models import User, Group
from polls.models import Profil

def create_test_users():
    """Créer deux utilisateurs de test avec groupes différents"""
    
    # Récupérer ou créer les groupes
    group_audio, _ = Group.objects.get_or_create(name='audio_recording')
    group_text, _ = Group.objects.get_or_create(name='text_only')
    
    print("✅ Groupes créés/trouvés:")
    print(f"  - audio_recording: {group_audio.id}")
    print(f"  - text_only: {group_text.id}")
    print()
    
    # Utilisateur 1: Audio Recording (groupe par défaut)
    user1, created1 = User.objects.get_or_create(
        username='test_audio',
        defaults={
            'email': 'test_audio@example.com',
            'first_name': 'Audio',
            'last_name': 'TestUser',
            'is_active': True,
        }
    )
    if created1:
        user1.set_password('testpassword123')
        user1.save()
        print(f"✅ Utilisateur créé: {user1.username}")
    else:
        print(f"ℹ️  Utilisateur existe déjà: {user1.username}")
    
    # Assigner au groupe audio_recording
    user1.groups.add(group_audio)
    
    # Créer profil s'il n'existe pas
    profil1, created_p1 = Profil.objects.get_or_create(
        user=user1,
        defaults={'email': user1.email}
    )
    if created_p1:
        print(f"✅ Profil créé pour {user1.username}")
    
    print(f"   - Username: {user1.username}")
    print(f"   - Email: {user1.email}")
    print(f"   - Groupe: {list(user1.groups.values_list('name', flat=True))}")
    print(f"   - Mode: AUDIO_RECORDING")
    print()
    
    # Utilisateur 2: Text Only
    user2, created2 = User.objects.get_or_create(
        username='test_text',
        defaults={
            'email': 'test_text@example.com',
            'first_name': 'Text',
            'last_name': 'TestUser',
            'is_active': True,
        }
    )
    if created2:
        user2.set_password('testpassword456')
        user2.save()
        print(f"✅ Utilisateur créé: {user2.username}")
    else:
        print(f"ℹ️  Utilisateur existe déjà: {user2.username}")
    
    # Assigner au groupe text_only
    user2.groups.add(group_text)
    
    # Créer profil s'il n'existe pas
    profil2, created_p2 = Profil.objects.get_or_create(
        user=user2,
        defaults={'email': user2.email}
    )
    if created_p2:
        print(f"✅ Profil créé pour {user2.username}")
    
    print(f"   - Username: {user2.username}")
    print(f"   - Email: {user2.email}")
    print(f"   - Groupe: {list(user2.groups.values_list('name', flat=True))}")
    print(f"   - Mode: TEXT_ONLY")
    print()
    
    print("=" * 60)
    print("🧪 Comptes de test créés avec succès!")
    print("=" * 60)
    print()
    print("Pour tester:")
    print()
    print("1️⃣  Mode AUDIO (avec enregistrement):")
    print("   - Identifiant: test_audio")
    print("   - Mot de passe: testpassword123")
    print()
    print("2️⃣  Mode TEXTE (sans enregistrement):")
    print("   - Identifiant: test_text")
    print("   - Mot de passe: testpassword456")
    print()
    
    return user1, user2

if __name__ == '__main__':
    create_test_users()
