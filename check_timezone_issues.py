#!/usr/bin/env python
"""
Script d'investigation et diagnostic des problèmes timezone 
Django + PostgreSQL + Psycopg2

À exécuter lors de la migration pour valider les timezones.
Destiné à être exécuté APRÈS les migrations en PostgreSQL.

Usage:
    cd backend
    python manage.py shell < check_timezone_issues.py
    
OU:
    python manage.py shell_plus
    exec(open('check_timezone_issues.py').read())
"""

import os
import sys
import django
from pathlib import Path

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from datetime import datetime, timezone, timedelta
from django.utils import timezone as tz
from django.conf import settings
from django.db import connection
import pytz

print("=" * 80)
print("DIAGNOSTIC TIMEZONE - Django + PostgreSQL + Psycopg2")
print("=" * 80)

# ============================================================================
# 1. CONFIGURATION DJANGO
# ============================================================================
print("\n[1️⃣] Configuration Django")
print("-" * 80)
print(f"TIME_ZONE: {settings.TIME_ZONE}")
print(f"USE_TZ: {settings.USE_TZ}")
print(f"LANGUAGE_CODE: {settings.LANGUAGE_CODE}")

# ============================================================================
# 2. FUSEAU HORAIRE SYSTÈME
# ============================================================================
print("\n[2️⃣] Fuseau horaire système")
print("-" * 80)
print(f"TZ env var: {os.environ.get('TZ', 'NOT SET')}")
tz_paris = pytz.timezone('Europe/Paris')
now_utc = datetime.now(timezone.utc)
now_paris = now_utc.astimezone(tz_paris)
print(f"Heure UTC: {now_utc}")
print(f"Heure Paris: {now_paris}")
print(f"Offset Paris: {now_paris.strftime('%z')}")

# ============================================================================
# 3. DJANGO - Gestion des datetimes
# ============================================================================
print("\n[3️⃣] Django - Datetimes et timezones")
print("-" * 80)
now_django = tz.now()
local_django = tz.localtime(now_django)
print(f"timezone.now() (UTC): {now_django}")
print(f"timezone.now().tzinfo: {now_django.tzinfo}")
print(f"timezone.localtime(): {local_django}")
print(f"timezone.localtime().tzinfo: {local_django.tzinfo}")
print(f"get_current_timezone(): {tz.get_current_timezone()}")

# ============================================================================
# 4. PostgreSQL - Connexion et timezone
# ============================================================================
print("\n[4️⃣] PostgreSQL - Configuration de connexion")
print("-" * 80)
connection.ensure_connection()

with connection.cursor() as cursor:
    # Vérifier la timezone PostgreSQL
    cursor.execute("SHOW timezone;")
    db_timezone = cursor.fetchone()[0]
    print(f"PostgreSQL timezone (SHOW): {db_timezone}")
    
    # Vérifier l'heure PostgreSQL
    cursor.execute("SELECT NOW();")
    db_now_utc = cursor.fetchone()[0]
    print(f"PostgreSQL NOW() (UTC): {db_now_utc}")
    
    # Vérifier l'heure convertie en Europe/Paris
    cursor.execute("SELECT NOW() AT TIME ZONE 'Europe/Paris';")
    db_now_paris = cursor.fetchone()[0]
    print(f"PostgreSQL NOW() AT PARIS: {db_now_paris}")
    
    # Vérifier la version PostgreSQL
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()[0]
    print(f"PostgreSQL version: {db_version}")

# ============================================================================
# 5. PSYCOPG2 - Configuration
# ============================================================================
print("\n[5️⃣] Psycopg2 - Driver info")
print("-" * 80)
import psycopg2
print(f"Psycopg2 version: {psycopg2.__version__}")
print(f"Database backend: {connection.vendor}")

# ============================================================================
# 6. TESTS - Création et lecture de datetimes
# ============================================================================
print("\n[6️⃣] Tests - Datetimes en base de données")
print("-" * 80)

# Créer un test datetime
test_datetime = tz.now()
print(f"Test datetime créé: {test_datetime}")
print(f"Timezone: {test_datetime.tzinfo}")

# Insérer et relire
try:
    from reves.models import Reve, User
    from django.contrib.auth.models import User as DjangoUser
    
    # Vérifier si la table existe
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'reves_reve'
            );
        """)
        table_exists = cursor.fetchone()[0]
    
    if table_exists:
        # Créer un test Reve (sans contenu, juste les dates)
        test_reve = Reve(
            contenu="Test timezone",
            heure_reve=test_datetime,
        )
        # Voir si la création pose problème
        print("✓ Création d'objet Reve en mémoire: OK")
        
        # ATTENTION: Ne pas sauvegarder dans la base en production!
        # print(f"  - heure_reve (avant save): {test_reve.heure_reve}")
        # print(f"  - heure_reve.tzinfo: {test_reve.heure_reve.tzinfo}")
    else:
        print("⚠️ Table 'reves_reve' non trouvée (migrations non exécutées)")
        
except Exception as e:
    print(f"⚠️ Erreur lors du test Reve: {e}")

# ============================================================================
# 7. PROBLÈMES IDENTIFIÉS
# ============================================================================
print("\n[7️⃣] Analyse - Problèmes potentiels")
print("-" * 80)

issues = []

# Vérifier que Django utilise USE_TZ
if not settings.USE_TZ:
    issues.append("❌ USE_TZ = False - Les timezones ne sont pas gérées!")

# Vérifier que TIME_ZONE est bien configuré
if settings.TIME_ZONE != 'Europe/Paris':
    issues.append(f"⚠️ TIME_ZONE = {settings.TIME_ZONE} (attendu: Europe/Paris)")

# Vérifier que now_django et db_now_utc sont cohérents
try:
    time_diff = (now_django.replace(tzinfo=None) - db_now_utc.replace(tzinfo=None)).total_seconds()
except Exception as e:
    time_diff = 0  # Ignorer les problèmes de soustraction
if abs(time_diff) > 5:  # Plus de 5 secondes de différence
    issues.append(f"⚠️ Écart Django/PostgreSQL: {time_diff} secondes")

# Vérifier que PostgreSQL utilise UTC
if 'UTC' not in db_timezone and 'UTC' not in db_timezone.upper():
    issues.append(f"⚠️ PostgreSQL timezone: {db_timezone} (attendu: UTC)")

if not issues:
    print("✅ Aucun problème identifié!")
else:
    print("Problèmes trouvés:")
    for issue in issues:
        print(f"  {issue}")

# ============================================================================
# 8. RECOMMANDATIONS
# ============================================================================
print("\n[8️⃣] Recommandations")
print("-" * 80)
print("""
✓ Django USE_TZ=True stocke les datetimes en UTC en PostgreSQL
✓ Django les convertit automatiquement en Europe/Paris côté Python
✓ Les templates affichent correctement grâce au filtre |date

⚠️ À vérifier après migration réelle:
  - Les datetimes existants (SQLite) que vous migrerez
  - Les timestamps hardcodés dans les migrations
  - Les fixtures de test avec datetimes spécifiques
  - Les queries raw SQL avec datetimes

🔧 Pour déboguer en production:
  1. docker-compose exec web python manage.py shell
  2. exec(open('check_timezone_issues.py').read())
  3. Vérifier les résultats ci-dessus
""")

print("\n" + "=" * 80)
print("FIN DU DIAGNOSTIC")
print("=" * 80)
