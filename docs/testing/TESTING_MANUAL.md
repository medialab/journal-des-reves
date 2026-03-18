# 🧪 Manuel de Test Visuel - Deux Modes d'Enregistrement

## Configuration Actuelle

Deux groupes d'utilisateurs ont été créés :

### 1️⃣ Mode AUDIO (groupe `audio_recording`)
- **Identifiant**: `test_audio`
- **Mot de passe**: `testpassword123`
- **Comportement**: Affiche le bouton "Démarrer l'enregistrement" pour enregistrer de l'audio
- **Transcription**: Asynchrone avec Whisper

### 2️⃣ Mode TEXTE (groupe `text_only`)
- **Identifiant**: `test_text`
- **Mot de passe**: `testpassword456`
- **Comportement**: Affiche une textarea "Raconter son rêve" pour écrire le texte
- **Transcription**: Pas de transcription asynchrone, le texte est utilisé directement

---

## 🎯 Tests à Effectuer

### Test 1: Affichage Correct selon le Mode

**Mode AUDIO:**
1. Se connecter avec `test_audio` / `testpassword123`
2. Aller à `/polls/enregistrer/`
3. ✅ **Vérifier:**
   - Le bouton "Démarrer l'enregistrement" est visible
   - La textarea "Raconter mon rêve" est **cachée**
   - Les horloges d'enregistrement sont visibles

**Mode TEXTE:**
1. Se connecter avec `test_text` / `testpassword456`
2. Aller à `/polls/enregistrer/`
3. ✅ **Vérifier:**
   - La textarea "Raconter son rêve" est visible
   - Le bouton "Démarrer l'enregistrement" est **caché**
   - Le bouton "Aucun souvenir" est présent sous la textarea

---

### Test 2: Soumission en Mode AUDIO

1. Connect comme `test_audio`
2. Accéder à `/polls/enregistrer/`
3. Enregistrer un court audio (5-10 secondes)
4. Remplir les informations du formulaire
5. Cliquer "Soumettre"
6. ✅ **Vérifier:**
   - Message "Rêve enregistré! La transcription arrivera dans quelques minutes..."
   - Redirection vers le journal
   - L'audio est visible dans le journal

---

### Test 3: Soumission en Mode TEXTE

1. Connecter comme `test_text`
2. Accéder à `/polls/enregistrer/`
3. Écrire un texte complet (ex: "J'ai rêvé que je volais au-dessus des nuages...")
4. Remplir les informations du formulaire
5. Cliquer "Soumettre"
6. ✅ **Vérifier:**
   - Message "Rêve enregistré avec succès !"
   - Redirection vers le journal
   - Le texte est visible comme transcription (pas d'audio)

---

### Test 4: Validation Mode TEXTE

1. Connecter comme `test_text`
2. Accéder à `/polls/enregistrer/`
3. Laisser la textarea vide
4. Cliquer "Soumettre"
5. ✅ **Vérifier:**
   - Message d'erreur: "Veuillez saisir une transcription."
   - Formulaire reste visible (pas de redirection)

---

### Test 5: Bouton "Aucun souvenir"

**Mode AUDIO:**
1. Connecter comme `test_audio`
2. Accéder à `/polls/enregistrer/`
3. Cliquer "Aucun souvenir..." (sans enregistrement)
4. ✅ **Vérifier:**
   - Message "Entrée enregistrée : aucun souvenir de rêve cette nuit"
   - Redirection vers le journal
   - Aucun audio n'apparaît

**Mode TEXTE:**
1. Connecter comme `test_text`
2. Accéder à `/polls/enregistrer/`
3. Cliquer "Aucun souvenir..." sous la textarea
4. ✅ **Vérifier:**
   - Message "Entrée enregistrée : aucun souvenir de rêve cette nuit"
   - Redirection vers le journal

---

## 📋 Checklist de Vérification

- [ ] Mode AUDIO affiche uniquement le recorder audio
- [ ] Mode TEXTE affiche uniquement la textarea
- [ ] Mode AUDIO sauvegarde avec transcription asynchrone
- [ ] Mode TEXTE sauvegarde sans transcription asynchrone
- [ ] Mode TEXTE valide que la transcription n'est pas vide
- [ ] Bouton "Aucun souvenir" fonctionne dans les deux modes
- [ ] Le journal affiche correctement les deux types de rêves
- [ ] Le mode par défaut (sans groupe) est AUDIO_RECORDING

---

## 🔧 Commandes Utiles

### Redémarrer le serveur Django:
```bash
cd /home/maudyaiche/dev/site_reves/djangotutorial
source ../mon_env/bin/activate
python manage.py runserver 127.0.0.1:8000
```

### Afficher les comptes de test dans l'admin:
- URL: `/admin/`
- Identifiants admin: (voir le compte créé lors de l'installation)

### Vérifier les rêves créés:
```bash
python manage.py shell
>>> from polls.models import Reve
>>> Reve.objects.all().values('id', 'profil__user__username', 'audio', 'transcription')
```

---

## Notes Importantes

1. **Mode par défaut**: Les utilisateurs sans groupe spécifique seront en mode AUDIO_RECORDING
2. **Modification du groupe**: Via l'admin Django (`/admin/auth/group/`)
3. **JavaScript**: Le basculement audio/texte est fait en JavaScript côté client, basé sur le contexte `{{ recording_mode }}`
4. **Validation côté serveur**: Adaptée selon le mode pour audio ou texte
