#!/usr/bin/env python
"""
Script de test pour vérifier le flux complet du questionnaire
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/home/maudyaiche/dev/site_reves/backend')
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
from reves.models import Profil
from django.utils import timezone
from datetime import timedelta
import json

client = Client()

# 1. Créer un utilisateur de test
print("\n=== Création d'un utilisateur de test ===")
import uuid
unique_suffix = str(uuid.uuid4())[:8]
username = f'test_user_{unique_suffix}'
email = f'test_{unique_suffix}@example.com'

try:
    user = User.objects.get(username=username)
    print(f"✓ Utilisateur existant: {user.username}")
except User.DoesNotExist:
    user = User.objects.create_user(
        username=username,
        email=email,
        password='testpass123'
    )
    print(f"✓ Nouvel utilisateur créé: {user.username}")

# Créer ou mettre à jour le profil pour que l'accès au questionnaire soit disponible
try:
    profil = user.profil
except Profil.DoesNotExist:
    profil = Profil.objects.create(user=user)
    print(f"✓ Nouveau profil créé")

# Mettre la date d'enregistrement assez loin dans le passé pour que le questionnaire soit accessible
profil.created_at = timezone.now() - timedelta(days=8)
profil.save()
print(f"✓ Profil mis à jour pour accès questionnaire (création: {profil.created_at})")

# 2. Se connecter
print("\n=== Connexion ===")
login_success = client.login(username=username, password='testpass123')
if login_success:
    print("✓ Connexion réussie")
else:
    print("✗ Échec de la connexion")
    sys.exit(1)

# 3. Accéder au questionnaire
print("\n=== Accès au questionnaire ===")
url_questionnaire = reverse('reves:questionnaire')
response = client.get(url_questionnaire)
print(f"Code de réponse GET: {response.status_code}")
if response.status_code == 200:
    print("✓ Questionnaire accessible")
else:
    print(f"✗ Erreur d'accès: {response.status_code}")
    print(response.content[:500])
    sys.exit(1)

# 4. Tester la sauvegarde AJAX de la section 1
print("\n=== Test sauvegarde AJAX - Section 1 ===")
section1_data = {
    'section': '1',
    'section_duration': '15',
    'freq_reves_not': '1',  # "Oui souvent"
    'mod_img': 'on',
    'etendue_souvenir_reve': '3',
    'temps_du_reve': '2',
    'heure_coucher': '23:00',
    'heure_reveil': '07:30',
    'latence_som': '15',
    'besoin_som': '00:00',
    'reveil_nuit': 'False',
}

response = client.post(
    url_questionnaire,
    section1_data,
    HTTP_X_REQUESTED_WITH='XMLHttpRequest'
)
print(f"Code de réponse: {response.status_code}")
if response.status_code == 200:
    data = json.loads(response.content)
    print(f"Réponse JSON: {data}")
    if data.get('success'):
        print("✓ Section 1 enregistrée avec succès")
    else:
        print(f"✗ Erreur: {data.get('message')}")
else:
    print(f"✗ Erreur HTTP: {response.status_code}")
    print(response.content[:500])

# 5. Tester la sauvegarde AJAX de la section 2
print("\n=== Test sauvegarde AJAX - Section 2 ===")
section2_data = {
    'section': '2',
    'section_duration': '20',
    'perception_financiere': '3',
    'perception_risque_pauvrete': '2',
    'position_subjective_classe': '3',
    'perception_mobilite': '2',
    'discri_presence': '2',
    'sante_generale': '2',
    'det_1': '1',
    'det_2': '1',
    'det_3': '1',
    'det_4': '1',
    'det_5': '1',
}

response = client.post(
    url_questionnaire,
    section2_data,
    HTTP_X_REQUESTED_WITH='XMLHttpRequest'
)
print(f"Code de réponse: {response.status_code}")
if response.status_code == 200:
    data = json.loads(response.content)
    print(f"Réponse JSON: {data}")
    if data.get('success'):
        print("✓ Section 2 enregistrée avec succès")
    else:
        print(f"✗ Erreur: {data.get('message')}")
else:
    print(f"✗ Erreur HTTP: {response.status_code}")

# 6. Tester la soumission finale (section 3)
print("\n=== Test soumission finale - Section 3 ===")
section3_data = {
    'section': '3',
    'section_duration': '25',
    'annee_naissance': '1985',
    'genre': '1',
    'habitat': '2',
    'niv_diplome': '10',
    'revenus_tranche': '6',
    'logement': '1',
    'pret': 'True',
    'montant_loyer': '800.50',
    'travail_statut': '1',
    'profession': '201',
    'statut_couple': '1',
}

response = client.post(
    url_questionnaire,
    section3_data,
    HTTP_X_REQUESTED_WITH='XMLHttpRequest'
)
print(f"Code de réponse: {response.status_code}")
if response.status_code == 200:
    data = json.loads(response.content)
    print(f"Réponse JSON: {data}")
    if data.get('success'):
        print("✓ Section 3 enregistrée avec succès")
    else:
        print(f"✗ Erreur: {data.get('message')}")
else:
    print(f"✗ Erreur HTTP: {response.status_code}")

# 7. Vérifier que le questionnaire est finalisé
print("\n=== Vérification finale ===")
from reves.models import Questionnaire
questionnaires = Questionnaire.objects.filter(profil=profil)
if questionnaires.exists():
    q = questionnaires.first()
    print(f"✓ Questionnaire créé (ID: {q.id})")
    print(f"  - Complété: {q.is_completed}")
    print(f"  - Données section 1: freq_reves_not={q.freq_reves_not}, mod_img={q.mod_img}")
    print(f"  - Données section 2: perception_financiere={q.perception_financiere}")
    print(f"  - Données section 3: annee_naissance={q.annee_naissance}, professions={q.profession}")
    print(f"  - Logement: logement={q.logement}, pret={q.pret}, montant_loyer={q.montant_loyer}")
else:
    print("✗ Aucun questionnaire trouvé")

print("\n=== Test terminé ===\n")
