"""
Script utilitaire pour gérer l'accès au questionnaire des utilisateurs
Usage:
    python manage.py shell < polls/management/commands/manage_questionnaire_access.py
"""

from polls.models import Profil
from django.utils import timezone


def grant_immediate_access(username):
    """Donne accès immédiat au questionnaire à un utilisateur"""
    try:
        profil = Profil.objects.get(user__username=username)
        profil.created_at = timezone.now() - timezone.timedelta(days=8)
        profil.save()
        print(f"✅ Accès au questionnaire accordé à {username}")
        return True
    except Profil.DoesNotExist:
        print(f"❌ Profil non trouvé pour l'utilisateur {username}")
        return False


def reset_access_delay(username):
    """Réinitialise le délai d'accès (remet à aujourd'hui)"""
    try:
        profil = Profil.objects.get(user__username=username)
        profil.created_at = timezone.now()
        profil.save()
        print(f"✅ Délai d'accès réinitialisé pour {username}")
        return True
    except Profil.DoesNotExist:
        print(f"❌ Profil non trouvé pour l'utilisateur {username}")
        return False


def show_access_status():
    """Affiche le statut d'accès au questionnaire pour tous les utilisateurs"""
    profils = Profil.objects.all()
    
    print("\n" + "="*70)
    print("STATUT D'ACCÈS AU QUESTIONNAIRE")
    print("="*70)
    
    for profil in profils:
        can_access = "✅ OUI" if profil.can_access_questionnaire() else "❌ NON"
        days_remaining = profil.days_until_questionnaire_access()
        
        print(f"\n{profil.user.username}")
        print(f"  Créé le: {profil.created_at.strftime('%d/%m/%Y %H:%M')}")
        print(f"  Peut accéder: {can_access}")
        if not profil.can_access_questionnaire():
            print(f"  Jours restants: {days_remaining}")
    
    print("\n" + "="*70)


def grant_access_to_all():
    """Donne accès immédiat à tous les utilisateurs"""
    profils = Profil.objects.all()
    count = 0
    
    for profil in profils:
        if not profil.can_access_questionnaire():
            profil.created_at = timezone.now() - timezone.timedelta(days=8)
            profil.save()
            count += 1
    
    print(f"✅ Accès accordé à {count} utilisateurs")


# Menu interactif
if __name__ == "__main__":
    print("\n🔐 GESTION DE L'ACCÈS AU QUESTIONNAIRE")
    print("="*70)
    print("\nCommandes disponibles:")
    print("  show_access_status()              - Voir le statut de tous les utilisateurs")
    print("  grant_immediate_access('username') - Donner accès immédiat à un utilisateur")
    print("  reset_access_delay('username')     - Réinitialiser le délai pour un utilisateur")
    print("  grant_access_to_all()              - Donner accès à tous les utilisateurs")
    print("\n" + "="*70)
    print("\nExemple:")
    print("  >>> grant_immediate_access('admin')")
    print("  >>> show_access_status()")
    print("\n")
