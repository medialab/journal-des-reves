# 🎙️ Architecture d'Enregistrement Audio (État Actuel)

## 📋 Vue d'ensemble

Le projet utilise une architecture **audio navigateur + transcription locale côté serveur Django**.

- ✅ Enregistrement audio dans le navigateur (microphone)
- ✅ Upload du fichier audio vers Django
- ✅ Transcription asynchrone en local via `openai-whisper`
- ✅ Modèle par défaut : `large-v3`
- ✅ Aucune transcription exécutée dans le navigateur

---

## 🏗️ Flux réel

1. L'utilisateur enregistre un audio dans la page `enregistrer`
2. Le navigateur envoie le fichier audio au backend Django
3. La vue crée un objet `Reve` avec `transcription_ready=False`
4. Le backend lance `start_transcription_async(reve_id)`
5. Un thread exécute la commande `transcribe_dreams`
6. Whisper transcrit en local puis sauvegarde le texte en base

---

## 📁 Fichiers clés

- `djangotutorial/polls/templates/polls/enregistrer.html`
  - Enregistrement audio + soumission du formulaire
- `djangotutorial/polls/views.py`
  - Création du rêve et lancement de la transcription asynchrone
- `djangotutorial/polls/services/transcription_service.py`
  - Thread non bloquant pour lancer la commande de transcription
- `djangotutorial/polls/management/commands/transcribe_dreams.py`
  - Transcription locale Whisper (`large-v3` par défaut)

---

## ⚙️ Configuration Whisper

Commande par défaut :

```bash
python manage.py transcribe_dreams --all
```

Forcer un modèle :

```bash
python manage.py transcribe_dreams --all --model medium
```

Configuration globale :

```bash
export WHISPER_MODEL=large-v3
```

---

## 🔐 Confidentialité

- Les audios sont stockés localement sur l'infrastructure du projet
- La transcription est exécutée localement sur le serveur Django
- Aucune API tierce distante n'est requise pour transcrire

---

## 🧹 Note de maintenance

L'ancien module de transcription navigateur (`transcription.js` / Whisper WASM) a été retiré du code actif pour éviter les incohérences de pipeline.
