"""
Initialise le compte admin Django depuis les variables d'env .env.prod
Script sécurisé : les mots de passe restent dans .env.prod (non commité)
"""
import os
import sys
from pathlib import Path

# Ajouter /app au sys.path pour que Django trouve les modules
app_dir = Path(__file__).parent.parent  # Remonte du dossier scripts/ à la racine /app/
sys.path.insert(0, str(app_dir))

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User

def init_superuser():
    """Crée le superuser depuis les variables d'env"""
    admin_username = os.getenv('DJANGO_ADMIN_USER', 'admin')
    admin_email = os.getenv('DJANGO_ADMIN_EMAIL', 'admin@example.com')
    admin_password = os.getenv('DJANGO_ADMIN_PASSWORD', '')
    
    # Validation
    if not admin_password:
        print("❌ ERREUR: DJANGO_ADMIN_PASSWORD non défini dans .env.prod")
        return False
    
    # Vérifier si l'user existe déjà
    if User.objects.filter(username=admin_username).exists():
        print(f"ℹ️  Superuser '{admin_username}' existe déjà. Aucune modification.")
        return True
    
    try:
        User.objects.create_superuser(
            username=admin_username,
            email=admin_email,
            password=admin_password
        )
        print(f"✅ Superuser '{admin_username}' créé avec succès!")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la création du superuser: {e}")
        return False

if __name__ == '__main__':
    print("═" * 70)
    print("🔐 Initialisation du compte administrateur Django")
    print("═" * 70)
    
    success = init_superuser()
    
    print("")
    if success:
        print("✅ Initialisation réussie!")
        print("   Accédez à: http://localhost:8000/admin/")
        sys.exit(0)
    else:
        print("❌ Initialisation échouée!")
        sys.exit(1)