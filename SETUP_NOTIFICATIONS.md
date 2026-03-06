# Guide d'installation et de configuration

## Installation des tables de base de données

### Étape 1 : Créer la migration

```bash
cd djangotutorial
python3 manage.py makemigrations
```

Vous devriez voir un message comme :
```
Migrations for 'polls':
  polls/migrations/0015_notification.py
    - Create model Notification
```

### Étape 2 : Appliquer la migration

```bash
python3 manage.py migrate
```

Vous devriez voir :
```
Running migrations:
  Applying polls.0015_notification... OK
```

### Étape 3 : Vérifier l'installation

```bash
python3 manage.py shell

# Dans le shell Django :
from polls.models import Notification
print(Notification._meta.db_table)  # Doit afficher 'polls_notification'
```

---

## Configuration des notifications automatiques

### Option 1 : Avec Cron (Linux/Mac)

1. Ouvrez crontab :
```bash
crontab -e
```

2. Ajoutez les lignes suivantes :
```crontab
# Rappel quotidien chaque matin à 8h
0 8 * * * cd /home/maudyaiche/dev/site_reves/djangotutorial && /home/maudyaiche/.local/bin/python3 manage.py send_daily_reminder >> /tmp/reves_daily.log 2>&1

# Rappel questionnaire chaque jour à 10h
0 10 * * * cd /home/maudyaiche/dev/site_reves/djangotutorial && /home/maudyaiche/.local/bin/python3 manage.py send_questionnaire_reminder >> /tmp/reves_questionnaire.log 2>&1
```

3. Vérifiez les logs :
```bash
tail -f /tmp/reves_daily.log
tail -f /tmp/reves_questionnaire.log
```

### Option 2 : Avec APScheduler (recommandé)

1. Installez le package :
```bash
pip install django-apscheduler
```

2. Ajoutez à `INSTALLED_APPS` dans `settings.py` :
```python
INSTALLED_APPS = [
    # ...
    'django_apscheduler',
]
```

3. Créez un fichier `polls/apps.py` ou modifiez-le :
```python
from django.apps import AppConfig
from apscheduler.schedulers.background import BackgroundScheduler
import logging

logger = logging.getLogger(__name__)

class PollsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'polls'
    
    def ready(self):
        from django.core.management import call_command
        
        scheduler = BackgroundScheduler(daemon=True)
        
        # Rappels quotidiens à 8h
        scheduler.add_job(
            lambda: call_command('send_daily_reminder'),
            'cron',
            hour=8,
            minute=0,
            id='daily_reminder'
        )
        
        # Rappels questionnaire à 10h
        scheduler.add_job(
            lambda: call_command('send_questionnaire_reminder'),
            'cron',
            hour=10,
            minute=0,
            id='questionnaire_reminder'
        )
        
        scheduler.start()
        logger.info("Scheduler Started!")
```

4. Appliquez migrations APScheduler :
```bash
python3 manage.py migrate django_apscheduler
```

### Option 3 : Avec Celery et Beat (pour production)

```bash
pip install celery django-celery-beat django-celery-results
```

Voir la documentation : https://docs.celeryproject.org/

---

## Test manuel des notifications

### Dans Django Shell :

```bash
python3 manage.py shell
```

```python
from polls.models import Profil, Notification
from django.contrib.auth.models import User
from django.utils import timezone

# Récupérer un profil
profil = Profil.objects.first()

# Créer une notification de test
notification = Notification.objects.create(
    profil=profil,
    notification_type='daily_reminder',
    title='Test Rappel Quotidien',
    message='Ceci est une notification de test. Avez-vous rêvé cette nuit?'
)

print(f"Notification créée: {notification.id}")

# Voir toutes les notifications
notifications = Notification.objects.filter(profil=profil)
print(f"Total notifications: {notifications.count()}")

# Marquer comme lue
notification.mark_as_read()
print(f"Notification lue: {notification.is_read}")
```

### Via l'interface web :

1. Ouvrez votre navigateur et allez à : `http://localhost:8000/polls/`
2. Connectez-vous
3. Une cloche 🔔 devrait apparaître en haut à droite si vous avez des notifications non lues
4. Cliquez dessus pour voir les notifications

---

## Test de la modal de questionnaire

### Créer un utilisateur de test avec 7+ jours d'ancienneté :

```bash
python3 manage.py shell
```

```python
from polls.models import Profil
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# Créer un utilisateur
user = User.objects.create_user(
    username='test_user',
    email='test@example.com',
    password='testpass123'
)

# Créer un profil avec une date de création il y a 8 jours
profil = Profil.objects.create(
    user=user,
    email='test@example.com',
    created_at=timezone.now() - timedelta(days=8)
)

print(f"Profil créé: {profil.user.username}")
print(f"Age: {profil.days_until_questionnaire_access()} jours")
```

Puis :
1. Connectez-vous avec ces identifiants
2. Allez sur `/polls/enregistrer/` ou `/polls/journal/`
3. Une modale devrait s'afficher après 1 seconde

---

## Vérifier les cookies de session

### Dans le navigateur :

1. Ouvrez DevTools (F12)
2. Allez à l'onglet "Storage"
3. Sélectionnez "Cookies"
4. Cherchez `reves_sessionid` avec une expiration de 30 jours

### En base de données :

```bash
python3 manage.py dbshell
```

```sql
SELECT session_key, expire_date FROM django_session LIMIT 5;
```

---

## Commandes utiles

### Créer un superutilisateur :
```bash
python3 manage.py createsuperuser
```

### Nettoyer les sessions expirées :
```bash
python3 manage.py clearsessions
```

### Voir les migrations :
```bash
python3 manage.py showmigrations
```

---

## Checklist de configuration

- [ ] Migration créée et appliquée (`makemigrations` + `migrate`)
- [ ] Tâches cron configurées (ou APScheduler installé)
- [ ] Les fichiers CSS/JS sont chargés correctement
- [ ] La cloche de notifications apparaît en haut à droite (utilisateurs connectés)
- [ ] Les notifications s'affichent après exécution de `send_daily_reminder`
- [ ] La modal du questionnaire s'affiche après 7 jours
- [ ] Le cookie de session persiste 30 jours
- [ ] Test en supprimant les cookies → session doit être supprimée

---

## Dépannage

### "ModuleNotFoundError: No module named 'apscheduler'"
```bash
pip install django-apscheduler
```

### "Notification table does not exist"
```bash
python3 manage.py migrate
```

### Les notifications ne s'affichent pas sur le site
Ouvrez la console (F12) et cherchez les erreurs JavaScript :
```javascript
// Testez manuellement
fetch('/polls/api/notifications/')
    .then(r => r.json())
    .then(d => console.log(d))
```

---

## Configuration en production

Avant de déployer :

1. Définir `SESSION_COOKIE_SECURE = True` dans `settings.py`
2. Utiliser HTTPS
3. Mettre `DEBUG = False`
4. Utiliser un lien SMTP réel pour les emails
5. Configurer un vrai serveur de base de données (PostgreSQL)
6. Utiliser un gestionnaire de tâches comme Celery ou APScheduler

---

Besoin d'aide ? Consultez la documentation complète dans [NOTIFICATIONS_IMPLEMENTATION.md](NOTIFICATIONS_IMPLEMENTATION.md)
