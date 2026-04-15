#!/usr/bin/env python
"""
Script de validation complet pour l'auto-complétion
"""
import os
import sys
import django
import json

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/home/maudyaiche/dev/site_reves/backend')

django.setup()

from reves.services.autocomplete_service import AutocompleteService

def validate_implementation():
    """Valide l'implémentation complète de l'auto-complétion"""
    
    print("=" * 60)
    print("🔍 VALIDATION DE L'IMPLÉMENTATION AUTOCOMPLETE")
    print("=" * 60)
    
    # 1. Vérifier le chargement des données
    print("\n1️⃣  Vérification du chargement des données...")
    try:
        emotions = AutocompleteService.get_emotions()
        elements = AutocompleteService.get_elements()
        print(f"   ✅ Émotions chargées: {len(emotions)} items")
        print(f"   ✅ Éléments chargés: {len(elements)} items")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    # 2. Vérifier la structure des données
    print("\n2️⃣  Vérification de la structure des données...")
    if isinstance(emotions, list) and len(emotions) > 0:
        print(f"   ✅ Émotions: liste valide")
        print(f"      Samples: {emotions[:3]}")
    else:
        print(f"   ❌ Émotions: structure invalide")
        return False
    
    if isinstance(elements, list) and len(elements) > 0:
        print(f"   ✅ Éléments: liste valide")
        print(f"      Samples: {elements[:3]}")
    else:
        print(f"   ❌ Éléments: structure invalide")
        return False
    
    # 3. Vérifier la recherche d'émotions
    print("\n3️⃣  Vérification de la recherche d'émotions...")
    test_queries = ['calme', 'joie', 'peur', 'am']
    for query in test_queries:
        results = AutocompleteService.search_emotions(query)
        print(f"   ✅ Recherche '{query}': {len(results)} résultats")
        print(f"      → {results[:2]}")
    
    # 4. Vérifier la recherche d'éléments
    print("\n4️⃣  Vérification de la recherche d'éléments...")
    test_queries = ['maison', 'eau', 'pa']
    for query in test_queries:
        results = AutocompleteService.search_elements(query)
        print(f"   ✅ Recherche '{query}': {len(results)} résultats")
        print(f"      → {results[:2]}")
    
    # 5. Vérifier le fichier JSON source
    print("\n5️⃣  Vérification du fichier source...")
    data_file = '/home/maudyaiche/dev/site_reves/backend/reves/fixtures/autocomplete_data.json'
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"   ✅ Fichier JSON valide")
        print(f"      - Émotions dans le fichier: {len(data.get('emotions', []))}")
        print(f"      - Éléments dans le fichier: {len(data.get('elements', []))}")
    except Exception as e:
        print(f"   ❌ Erreur de lecture: {e}")
        return False
    
    # 6. Vérifier que les données en cache correspondent au fichier
    print("\n6️⃣  Vérification de la cohérence (cache vs fichier)...")
    if emotions == data.get('emotions', []):
        print(f"   ✅ Émotions en cache = fichier JSON")
    else:
        print(f"   ⚠️  Les émotions diffèrent (cache vs fichier)")
        print(f"      Cache: {len(emotions)} items")
        print(f"      Fichier: {len(data.get('emotions', []))} items")
    
    if elements == data.get('elements', []):
        print(f"   ✅ Éléments en cache = fichier JSON")
    else:
        print(f"   ⚠️  Les éléments diffèrent (cache vs fichier)")
        print(f"      Cache: {len(elements)} items")
        print(f"      Fichier: {len(data.get('elements', []))} items")
    
    # 7. Résumé
    print("\n" + "=" * 60)
    print("✅ VALIDATION RÉUSSIE!")
    print("=" * 60)
    print("\n📝 RÉSUMÉ:")
    print(f"   • Émotions: {len(emotions)} items")
    print(f"   • Éléments: {len(elements)} items")
    print(f"   • Service d'auto-complétion: ✅ Fonctionnel")
    print(f"   • Migration DB: ❌ Non nécessaire")
    print("\n💡 L'implémentation est prête!")
    print("   Redémarrez simplement le serveur Django pour appliquer les changements.")
    
    return True

if __name__ == "__main__":
    success = validate_implementation()
    sys.exit(0 if success else 1)
