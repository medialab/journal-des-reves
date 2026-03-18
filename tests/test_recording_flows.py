#!/usr/bin/env python
"""
Script de test pour valider le système de deux groupes d'enregistrement
Teste:
1. L'affichage du bon formulaire selon le groupe
2. La sauvegarde en mode AUDIO
3. La sauvegarde en mode TEXTE
"""

import os
import sys
import django
from io import BytesIO

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, '/home/maudyaiche/dev/site_reves/djangotutorial')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from polls.models import Reve, Profil

def test_recording_groups():
    """Test les deux modes d'enregistrement"""
    
    client = Client()
    
    print("=" * 70)
    print("🧪 TESTS DU SYSTÈME DE DEUX MODES D'ENREGISTREMENT")
    print("=" * 70)
    print()
    
    # Test 1: Vérifier le contexte GET pour mode AUDIO
    print("TEST 1️⃣  - Mode AUDIO: Vérifier le contexte GET")
    print("-" * 70)
    
    try:
        user_audio = User.objects.get(username='test_audio')
        client.force_login(user_audio)
        response = client.get('/polls/enregistrer/')
        
        context = response.context
        recording_mode = context.get('recording_mode')
        
        if recording_mode == 'audio_recording':
            print("✅ PASS: Mode AUDIO détecté correctement")
            print(f"   recording_mode = '{recording_mode}'")
        else:
            print(f"❌ FAIL: Mode attendu 'audio_recording', obtenu '{recording_mode}'")
        
        # Vérifier que le template contient le recorder
        html = response.content.decode()
        if 'id="startBtn"' in html and 'Démarrer l\'enregistrement' in html:
            print("✅ PASS: Bouton 'Démarrer l'enregistrement' trouvé dans le template")
        else:
            print("❌ FAIL: Bouton audio non trouvé dans le template")
            
        if 'id="sectionTextDream"' in html:
            print("✅ PASS: Section texte présente (sera masquée par JavaScript)")
        else:
            print("❌ FAIL: Section texte non trouvée")
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
    
    print()
    
    # Test 2: Vérifier le contexte GET pour mode TEXTE
    print("TEST 2️⃣  - Mode TEXTE: Vérifier le contexte GET")
    print("-" * 70)
    
    try:
        user_text = User.objects.get(username='test_text')
        client.force_login(user_text)
        response = client.get('/polls/enregistrer/')
        
        context = response.context
        recording_mode = context.get('recording_mode')
        
        if recording_mode == 'text_only':
            print("✅ PASS: Mode TEXTE détecté correctement")
            print(f"   recording_mode = '{recording_mode}'")
        else:
            print(f"❌ FAIL: Mode attendu 'text_only', obtenu '{recording_mode}'")
        
        # Vérifier que le template contient la textarea
        html = response.content.decode()
        if 'id="dreamTextarea"' in html and 'Raconte-moi ton rêve' in html:
            print("✅ PASS: Textarea trouvée dans le template")
        else:
            print("❌ FAIL: Textarea non trouvée")
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
    
    print()
    
    # Test 3: POST en mode AUDIO
    print("TEST 3️⃣  - Mode AUDIO: Sauvegarde avec audio")
    print("-" * 70)
    
    try:
        user_audio = User.objects.get(username='test_audio')
        client.force_login(user_audio)
        
        # Créer un fichier audio fictif
        audio_content = b'RIFF\x00\x00\x00\x00WAVEfmt \x10\x00\x00\x00'  # Minimal WAV header
        audio_file = BytesIO(audio_content)
        audio_file.name = 'test.wav'
        
        data = {
            'audio': audio_file,
            'existence_souvenir': '1',
            'type_reve': 'positif',
            'etendue_reve': '1',
            'sens': '1',
        }
        
        reves_before = Reve.objects.filter(profil=user_audio.profil).count()
        response = client.post('/polls/enregistrer/', data)
        
        if response.status_code == 200:
            try:
                import json
                result = json.loads(response.content)
                
                if result.get('success'):
                    reves_after = Reve.objects.filter(profil=user_audio.profil).count()
                    
                    if reves_after > reves_before:
                        reve = Reve.objects.filter(profil=user_audio.profil).latest('created_at')
                        
                        if reve.audio:
                            print("✅ PASS: Rêve créé avec audio")
                            print(f"   ID rêve: {reve.id}")
                            print(f"   Audio présent: {bool(reve.audio)}")
                            print(f"   Transcription prête: {reve.transcription_ready}")
                        else:
                            print("❌ FAIL: Rêve créé mais sans audio")
                    else:
                        print("❌ FAIL: Rêve non créé")
                else:
                    print(f"❌ FAIL: Erreur lors de la sauvegarde: {result.get('message')}")
                    
            except json.JSONDecodeError:
                print(f"❌ FAIL: Réponse non-JSON: {response.content[:200]}")
        else:
            print(f"❌ FAIL: Status code {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test 4: POST en mode TEXTE
    print("TEST 4️⃣  - Mode TEXTE: Sauvegarde avec texte")
    print("-" * 70)
    
    try:
        user_text = User.objects.get(username='test_text')
        client.force_login(user_text)
        
        data = {
            'existence_souvenir': '1',
            'transcription': 'Je rêvais que je volais dans le ciel bleu et magnifique.',
            'type_reve': 'tres_positif',
            'etendue_reve': '2',
            'sens': '2',
        }
        
        reves_before = Reve.objects.filter(profil=user_text.profil).count()
        response = client.post('/polls/enregistrer/', data)
        
        if response.status_code == 200:
            try:
                import json
                result = json.loads(response.content)
                
                if result.get('success'):
                    reves_after = Reve.objects.filter(profil=user_text.profil).count()
                    
                    if reves_after > reves_before:
                        reve = Reve.objects.filter(profil=user_text.profil).latest('created_at')
                        
                        if reve.transcription and not reve.audio:
                            print("✅ PASS: Rêve créé avec texte (pas d'audio)")
                            print(f"   ID rêve: {reve.id}")
                            print(f"   Audio présent: {bool(reve.audio)}")
                            print(f"   Transcription: {reve.transcription[:50]}...")
                            print(f"   Transcription prête: {reve.transcription_ready}")
                            
                            if reve.transcription_ready:
                                print("✅ PASS: Transcription marquée comme prête (pas de transcription asynchrone)")
                            else:
                                print("⚠️  WARN: Transcription non marquée comme prête")
                        else:
                            print("❌ FAIL: Données incorrectes")
                            print(f"   Audio: {bool(reve.audio)}")
                            print(f"   Transcription: {bool(reve.transcription)}")
                    else:
                        print("❌ FAIL: Rêve non créé")
                else:
                    print(f"❌ FAIL: Erreur lors de la sauvegarde: {result.get('message')}")
                    
            except json.JSONDecodeError:
                print(f"❌ FAIL: Réponse non-JSON: {response.content[:200]}")
        else:
            print(f"❌ FAIL: Status code {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test 5: POST en mode TEXTE sans transcription (validation)
    print("TEST 5️⃣  - Mode TEXTE: Validation transcription requise")
    print("-" * 70)
    
    try:
        user_text = User.objects.get(username='test_text')
        client.force_login(user_text)
        
        data = {
            'existence_souvenir': '1',
            'transcription': '',  # Vide = devrait échouer
            'type_reve': 'neutre',
        }
        
        response = client.post('/polls/enregistrer/', data)
        
        if response.status_code == 200 or response.status_code == 400:
            try:
                import json
                result = json.loads(response.content)
                
                if not result.get('success') and 'transcription' in result.get('message', '').lower():
                    print("✅ PASS: Validation correcte - transcription vide rejetée")
                    print(f"   Message: {result.get('message')}")
                else:
                    print("⚠️  WARN: Validation pas effectuée ou message différent")
                    print(f"   Succès: {result.get('success')}")
                    print(f"   Message: {result.get('message')}")
                    
            except json.JSONDecodeError:
                print(f"❌ FAIL: Réponse non-JSON")
        else:
            print(f"❌ FAIL: Status code {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
    
    print()
    print("=" * 70)
    print("✅ TESTS TERMINÉS")
    print("=" * 70)

if __name__ == '__main__':
    test_recording_groups()
