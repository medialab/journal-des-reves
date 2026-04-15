#!/usr/bin/env python
"""
Script de validation de la modification des émotions proposées
"""
import os
import sys
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/home/maudyaiche/dev/site_reves/backend')

django.setup()

from reves.models import ReveEmotion
from reves.services.autocomplete_service import AutocompleteService

def validate_changes():
    """Valide que les changements sont corrects"""
    
    print("=" * 70)
    print("✅ VALIDATION DE LA MODIFICATION DES ÉMOTIONS PROPOSÉES")
    print("=" * 70)
    
    # 1. Vérifier les émotions proposées
    print("\n1️⃣  Émotions proposées (boutons dans enregistrer.html):")
    emotions = ReveEmotion.objects.all().order_by('ordre')
    emotions_list = []
    for emotion in emotions:
        print(f"   {emotion.ordre}. {emotion.emoji} {emotion.libelle}")
        emotions_list.append(emotion.libelle)
    
    expected_emotions = ['Peur', 'Colère', 'Dégout', 'Tristesse', 'Surprise', 'Joie']
    if emotions_list == expected_emotions:
        print(f"   ✅ Correspond exactement à: {', '.join(expected_emotions)}")
    else:
        print(f"   ❌ ERREUR! Attendu: {expected_emotions}")
        print(f"      Reçu: {emotions_list}")
        return False
    
    # 2. Vérifier les émotions suggérées (autocomplete)
    print("\n2️⃣  Émotions suggérées (autocomplete - ne doivent pas changer):")
    suggested_emotions = AutocompleteService.get_emotions()
    print(f"   Total: {len(suggested_emotions)} émotions")
    
    # Vérifier que Dégout et Surprise sont bien dans la liste des suggestions
    if 'Dégout' in suggested_emotions and 'Surprise' in suggested_emotions:
        print(f"   ✅ Les nouvelles émotions sont dans les suggestions")
        idx_degout = suggested_emotions.index('Dégout') if 'Dégout' in suggested_emotions else -1
        idx_surprise = suggested_emotions.index('Surprise') if 'Surprise' in suggested_emotions else -1
        print(f"      - Dégout: position {idx_degout + 1}")
        print(f"      - Surprise: position {idx_surprise + 1}")
    else:
        print(f"   ⚠️  Les nouvelles émotions ne sont pas dans les suggestions")
        if 'Dégout' not in suggested_emotions:
            print(f"      - Dégout MANQUANT")
        if 'Surprise' not in suggested_emotions:
            print(f"      - Surprise MANQUANT")
    
    # 3. Vérifier que les anciennes émotions sont remplacées
    print("\n3️⃣  Vérification du remplacement:")
    if 'Appréhension' not in emotions_list:
        print(f"   ✅ Appréhension a bien été remplacée")
    else:
        print(f"   ❌ ERREUR! Appréhension devrait avoir été remplacée")
        return False
    
    if 'Bonheur' not in emotions_list:
        print(f"   ✅ Bonheur a bien été remplacé")
    else:
        print(f"   ❌ ERREUR! Bonheur devrait avoir été remplacé")
        return False
    
    # 4. Vérifier que les émotions conservées sont présentes
    print("\n4️⃣  Vérification des émotions conservées:")
    conserved = ['Peur', 'Colère', 'Tristesse', 'Joie']
    for emotion in conserved:
        if emotion in emotions_list:
            print(f"   ✅ {emotion} présente")
        else:
            print(f"   ❌ {emotion} MANQUANT!")
            return False
    
    # 5. Résumé
    print("\n" + "=" * 70)
    print("✨ TOUS LES TESTS RÉUSSIS!")
    print("=" * 70)
    print("\n📝 RÉSUMÉ DES CHANGEMENTS:")
    print("   Anciennes émotions proposées:")
    print("   • Peur, Colère, Appréhension, Tristesse, Joie, Bonheur")
    print("\n   Nouvelles émotions proposées:")
    print(f"   • {', '.join(expected_emotions)}")
    print("\n   Changements appliqués:")
    print("   ✅ Appréhension → Dégout")
    print("   ✅ Bonheur → Surprise")
    print("   ✅ Joie déplacée à la 6ème position")
    print("\n💡 Implémentation complète et prête à l'emploi!")
    
    return True


if __name__ == "__main__":
    success = validate_changes()
    sys.exit(0 if success else 1)
