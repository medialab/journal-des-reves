# Site Rêves

Je construis `Site Reves`, un site PWA avec un back-end Django pour collecter des récits de reves dans le cadre de ma thèse en sociologie.

## Résume rapide

Sur ce site, je propose d'une part un journal de rêves avec saisie audio,lance la transcription audio automatiquement en arrière-plan et de remplir un questionnaire socio-démographique. 
Pour que tout se passe bien, je permets l'inscription, la connexion et la gestion de profil et je gère des notifications (rappels quotidiens).

## Architecture du site

- `backend/config/`: configuration Django (settings, urls, wsgi/asgi).
- `backend/reves/models.py`: coeur metier (`Profil`, `Reve`, `Questionnaire`, `Notification`).
- `backend/reves/views.py`: vues pages + endpoints API.
- `backend/reves/templates/`: interfaces HTML.
- `backend/reves/static/`: CSS/JS (UI, notifications, logique front).
- `backend/reves/management/commands/`: taches planifiees.
- `scripts/notifications/`: scripts utilitaires pour initialisation/scheduler.
- `docs/assets/`: assets de documentation.

## Lancer en local et faire les migrations 

```bash
source mon_env/bin/activate
cd backend
python manage.py runserver
```
```bash
source mon_env/bin/activate
cd backend
python manage.py makemigrations
python manage.py migrate
```

Acces principal: `http://localhost:8000/polls/`

## Documentation detaillee

- `README_AUDIO_TRANSCRIPTION.md`
- `README_PWA_NOTIFICATIONS.md`
- `SECURITY_README.md`

## Licence

Le projet est sous licence **GNU AGPL v3** (voir `LICENSE`).
