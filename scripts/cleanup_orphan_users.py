#!/usr/bin/env python
"""
Script pour nettoyer les utilisateurs orphelins (sans profil associé).
Exécution: python manage.py shell < cleanup_orphan_users.py
Ou: cd backend && python manage.py shell -c "exec(open('../scripts/cleanup_orphan_users.py').read())"
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
django.setup()

from django.contrib.auth.models import User
from reves.models import Profil


def find_orphan_users():
    """Retourne uniquement les comptes qui n'ont aucun profil associé."""
    profile_user_ids = Profil.objects.values_list('user_id', flat=True)
    return User.objects.exclude(id__in=profile_user_ids)


def main():
    print("=" * 60)
    print("NETTOYAGE DES UTILISATEURS ORPHELINS")
    print("=" * 60)

    orphan_users = list(find_orphan_users())

    if not orphan_users:
        print("\n✓ Aucun utilisateur orphelin détecté!")
    else:
        print(f"\n✗ {len(orphan_users)} utilisateur(s) orphelin(s) trouvé(s):")
        for user in orphan_users:
            print(f"  - {user.username} (email: {user.email if user.email else '[vide]'})")

        print("\n⚠ Ces utilisateurs vont être supprimés.")
        response = input("Êtes-vous sûr? (oui/non): ").lower().strip()

        if response in ['oui', 'yes', 'o', 'y']:
            deleted_count = 0
            for user in orphan_users:
                username = user.username
                user.delete()
                deleted_count += 1
                print(f"  ✓ Supprimé: {username}")

            print(f"\n✓ {deleted_count} utilisateur(s) supprimé(s) avec succès!")
        else:
            print("\n✗ Suppression annulée.")

    print("\n" + "=" * 60)
    print("VÉRIFICATION FINALE")
    print("=" * 60)

    remaining_orphans = find_orphan_users()
    if remaining_orphans.exists():
        print(f"✗ {remaining_orphans.count()} utilisateur(s) orphelin(s) encore présent(s)")
    else:
        print("✓ Aucun utilisateur orphelin en base de données!")

    total_users = User.objects.count()
    print(f"✓ Total utilisateurs: {total_users}")


if __name__ == '__main__':
    main()
