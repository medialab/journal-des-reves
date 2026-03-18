# Site Reves

Je construis `Site Reves`, une application Django pour collecter des recits de reves
dans un cadre de recherche en sciences sociales.

## Resume rapide

- Je permets l'inscription, la connexion et la gestion de profil.
- Je propose un journal de reves avec saisie texte et audio.
- Je lance la transcription audio automatiquement en arriere-plan.
- Je gere des notifications (rappels quotidiens et questionnaire).
- Je fournis une experience PWA avec session persistante.

## Architecture du site

- `djangotutorial/mysite/`: configuration Django (settings, urls, wsgi/asgi).
- `djangotutorial/polls/models.py`: coeur metier (`Profil`, `Reve`, `Questionnaire`, `Notification`).
- `djangotutorial/polls/views.py`: vues pages + endpoints API.
- `djangotutorial/polls/templates/`: interfaces HTML.
- `djangotutorial/polls/static/`: CSS/JS (UI, notifications, logique front).
- `djangotutorial/polls/management/commands/`: taches planifiees.
- `scripts/notifications/`: scripts utilitaires pour initialisation/scheduler.
- `docs/assets/`: assets de documentation.

## Lancer en local

```bash
source mon_env/bin/activate
cd djangotutorial
python manage.py migrate
python manage.py runserver
```

Acces principal: `http://localhost:8000/polls/`

## Documentation detaillee

- `README_AUDIO_TRANSCRIPTION.md`
- `README_PWA_NOTIFICATIONS.md`
- `SECURITY_README.md`

## Licence

Le projet est sous licence **GNU AGPL v3** (voir `LICENSE`).
