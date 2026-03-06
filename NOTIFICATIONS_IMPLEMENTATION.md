# Implémentation des Notifications et Authentification Persistante

## 📋 Vue d'ensemble

Ce document décrit les trois nouvelles fonctionnalités implémentées :

1. **Notifications quotidiennes et rapels du questionnaire**
2. **Pop-up modal après 7 jours d'inscription pour remplir le questionnaire**
3. **Cookies de session pour une authentification persistante**

---

## 1️⃣ Notifications Système

### Description

Le système de notifications permet d'envoyer des rappels aux utilisateurs :
- **Rappel quotidien** : Chaque matin pour enregistrer un rêve
- **Rappel questionnaire** : Après 7 jours d'inscription pour remplir le questionnaire

### Architecture

#### Base de données (Modèle)

Nouveau modèle `Notification` dans `models.py` :

```python
class Notification(models.Model):
    class NotificationType(models.TextChoices):
        DAILY_REMINDER = 'daily_reminder'
        QUESTIONNAIRE_REMINDER = 'questionnaire_reminder'
        GENERAL = 'general'
    
    profil = ForeignKey(Profil, ...)
    notification_type = CharField(choices=NotificationType.choices)
    title = CharField()
    message = TextField()
    is_read = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    read_at = DateTimeField(null=True)
```

#### Commandes de gestion

Deux commandes Django pour générer les notifications :

1. **`send_daily_reminder`** - Envoyer les rappels quotidiens
   ```bash
   python manage.py send_daily_reminder
   ```
   À exécuter chaque matin via cron ou scheduler
   
2. **`send_questionnaire_reminder`** - Envoyer les rappels du questionnaire
   ```bash
   python manage.py send_questionnaire_reminder
   ```
   À exécuter une fois par jour

#### APIs

Trois nouvelles routes API pour gérer les notifications :

- `GET /polls/api/notifications/` - Lister les notifications
- `POST /polls/api/notifications/<id>/read/` - Marquer comme lue
- `GET /polls/api/notifications/unread-count/` - Nombre non lues

#### Front-end

- **CSS** : `polls/static/polls/notifications.css` - Styles des notifications
- **JavaScript** : `polls/static/polls/notifications.js` - Classe `NotificationManager`

**Fonctionnalités JavaScript** :
- Affichage des notifications avec animation
- Badge de notification non lue
- Auto-refresh toutes les 30 secondes
- Sons/animations visuelles

### Comment configurer les notifications

#### 1. Créer la migration et appliquer

```bash
python manage.py makemigrations
python manage.py migrate
```

#### 2. Configurer les tâches planifiées

**Option A : Avec cron (Linux/Mac)**

```bash

# Éditer la crontab
crontab -e

# Ajouter les lignes suivantes :
# Rappels quotidiens à 8h du matin
0 8 * * * cd /path/to/site_reves/djangotutorial && python manage.py send_daily_reminder

# Rappels questionnaire une fois par jour à 10h
0 10 * * * cd /path/to/site_reves/djangotutorial && python manage.py send_questionnaire_reminder
```

**Option B : Avec APScheduler**

Installer le package :
```bash
pip install django-apscheduler
```

Créer un fichier `apps.py` pour initialiser le scheduler (exemple) :

```python
from django.apps import AppConfig
from apscheduler.schedulers.background import BackgroundScheduler

class PollsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'polls'
    
    def ready(self):
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            send_daily_reminder_task,
            'cron',
            hour=8,
            minute=0
        )
        scheduler.add_job(
            send_questionnaire_reminder_task,
            'cron',
            hour=10,
            minute=0
        )
        scheduler.start()
```

#### 3. Tester les notifications

Dans Django shell :
```python
python manage.py shell

from polls.models import Profil, Notification
from django.contrib.auth.models import User

# Créer une notification de test
profil = Profil.objects.first()
notification = Notification.objects.create(
    profil=profil,
    notification_type='daily_reminder',
    title='Test notification',
    message='Ceci est une notification de test'
)
```

### Utilisation dans les vues

Les notifications s'affichent automatiquement en haut à droite de la page. Les utilisateurs peuvent :
- Voir les notifications non lues
- Voir le badge du nombre de notifications
- Cliquer sur une notification pour la marquer comme lue
- Fermer une notification

---

## 2️⃣ Pop-up Modal après 7 jours

### Description

Une fenêtre modale s'affiche automatiquement après 7 jours d'inscription sur les pages :
- Page d'enregistrement (`/polls/enregistrer/`)
- Profil (`/polls/profil/`)
- Journal (`/polls/journal/`)

### Fonctionnement

Le script JavaScript dans `base.html` vérifie :
1. Si l'utilisateur a créé son compte
2. Si 7 jours (ou plus) se sont écoulés
3. Si le questionnaire n'a pas déjà été complété
4. Si la modal n'a pas été rejetée il y a moins de 24h

### Code implémenté

Dans `base.html` :
```html
<script>
    document.addEventListener('DOMContentLoaded', function() {
        {% if user.is_authenticated %}
            const profilData = {
                created_at: '{{ user.profil.created_at|date:"Y-m-dTH:i:s" }}',
                has_questionnaire: '{{ has_questionnaire }}' === 'True'
            };
            
            if (!profilData.has_questionnaire && profilData.created_at) {
                const createdDate = new Date(profilData.created_at);
                const now = new Date();
                const daysEllapsed = Math.floor((now - createdDate) / (1000 * 60 * 60 * 24));
                
                if (daysEllapsed >= 7) {
                    const dismissedTime = localStorage.getItem('questionnaire_modal_dismissed');
                    const shouldShow = !dismissedTime || (now - new Date(parseInt(dismissedTime))) > (24 * 60 * 60 * 1000);
                    
                    if (shouldShow) {
                        setTimeout(() => {
                            notificationManager.showQuestionnaireModal(daysEllapsed);
                        }, 1000);
                    }
                }
            }
        {% endif %}
    });
</script>
```

### Customisation

Pour modifier la modal, éditez la méthode `showQuestionnaireModal()` dans `polls/static/polls/notifications.js` :

```javascript
showQuestionnaireModal(daysEllapsed) {
    this.showModal(
        'Complétez votre profil !',  // Titre
        'Message personnalisé...',     // Message
        '📋',                          // Emoji
        {
            subtitle: 'Texte sous-titre',
            progressInfo: 'Barre de progression',
            primaryLabel: 'Remplir maintenant',
            // ...
        }
    );
}
```

---

## 3️⃣ Authentification Persistante avec Cookies

### Description

L'utilisateur reste authentifié même s'il ferme son navigateur. La session persiste pendant 30 jours.

### Configuration dans `settings.py`

```python
# SESSION & COOKIES CONFIGURATION

# Durée de la session : 30 jours
SESSION_COOKIE_AGE = 30 * 24 * 60 * 60

# Les cookies persistent après fermeture du navigateur
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Sécurité
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG  # HTTPS en production
SESSION_COOKIE_SAMESITE = 'Lax'

# Backend de stockage
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Durée du "Remember me" optionnel
REMEMBER_ME_DURATION = 30 * 24 * 60 * 60
```

### Comportement

1. **Au login** : Django crée un cookie de session avec une durée limité à 30 jours
2. **À chaque visite** : Le cookie est validé et la session prolongée
3. **Au logout** : Le cookie est supprimé immédiatement
4. **Expiration** : Après 30 jours d'inactivité, l'utilisateur doit se reconnecter

### Pour implémenter un bouton "Se souvenir de moi"

Modifier le formulaire de login (optionnel) :

```html
<form method="post" action="{% url 'login' %}">
    {% csrf_token %}
    <input type="text" name="username" placeholder="Nom d'utilisateur">
    <input type="password" name="password" placeholder="Mot de passe">
    <label>
        <input type="checkbox" name="remember_me">
        Se souvenir de moi
    </label>
    <button type="submit">Connexion</button>
</form>
```

Ajouter le code pour traiter le checkbox dans la vue de login :

```python
if request.method == 'POST':
    remember_me = request.POST.get('remember_me', False)
    # ... authentifier l'utilisateur ...
    if remember_me:
        request.session.set_expiry(settings.REMEMBER_ME_DURATION)
    else:
        request.session.set_expiry(0)  # Session jusqu'à fermeture
```

---

## 📝 Structure des fichiers modifiés

```
djangotutorial/
├── polls/
│   ├── models.py                          # ✅ Ajout: Notification model
│   ├── admin.py                           # ✅ Ajout: NotificationAdmin
│   ├── views.py                           # ✅ Ajout: vues notifications
│   ├── urls.py                            # ✅ Ajout: routes API notifications
│   ├── signals.py                         # (inchangé)
│   ├── management/commands/
│   │   ├── send_daily_reminder.py        # ✅ NOUVEAU
│   │   └── send_questionnaire_reminder.py # ✅ NOUVEAU
│   ├── static/polls/
│   │   ├── notifications.css             # ✅ NOUVEAU
│   │   ├── notifications.js              # ✅ NOUVEAU
│   │   └── style.css                     # (inchangé)
│   └── templates/polls/
│       ├── base.html                     # ✅ Modifié: ajout scripts
│       ├── profil.html                   # (inchangé - uses has_questionnaire)
│       ├── enregistrer.html              # (inchangé - uses has_questionnaire)
│       └── journal.html                  # (inchangé - uses has_questionnaire)
│
└── mysite/
    └── settings.py                       # ✅ Modifié: config sessions/cookies
```

---

## 🔧 Dépannage

### Les notifications ne s'affichent pas

1. Vérifier que JavaScript est activé dans le navigateur
2. Vérifier que les fichiers CSS/JS sont bien chargés (F12 → Console)
3. Vérifier les réponses API : `F12 → Network → /polls/api/notifications/`

### La modal ne s'affiche pas

1. Vérifier que `user.profil.created_at` est bien défini
2. Vérifier que `has_questionnaire` est False
3. Vérifier le localStorage : `console.log(localStorage.getItem('questionnaire_modal_dismissed'))`

### L'utilisateur ne reste pas connecté

1. Cocher que `SESSION_COOKIE_SECURE = False` en développement
2. Vérifier que les cookies sont activés dans le navigateur
3. Vérifier la base de données : `python manage.py dbshell` → `SELECT * FROM django_session`

---

## 🚀 Prochaines étapes recommandées

1. **Email notifications** : Envoyer aussi un email aux utilisateurs
   ```python
   from django.core.mail import send_mail
   send_mail(notification.title, notification.message, ...)
   ```

2. **Notifications en temps réel** : Utiliser WebSockets avec Django Channels

3. **Historique des notifications** : Page dédiée pour voir tous les historiques

4. **Préférences utilisateur** : Permettre aux utilisateurs de désactiver certains rappels

5. **Analytics** : Tracker combien de notifications sont lues/converties

---

## 📞 Support

Pour toute question ou problème, consultez :
- [Django Sessions](https://docs.djangoproject.com/en/6.0/topics/http/sessions/)
- [Django Messages Framework](https://docs.djangoproject.com/en/6.0/ref/contrib/messages/)
- [Management Commands](https://docs.djangoproject.com/en/6.0/howto/custom-management-commands/)
