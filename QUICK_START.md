# 🚀 Guide de démarrage rapide - Notifications et Authentification

## Installation rapide (5 minutes)

### 1. Appliquer les migrations
```bash
cd djangotutorial
python3 manage.py makemigrations
python3 manage.py migrate
```

### 2. Tester sur site local
```bash
python3 manage.py runserver
# Ouvrez http://localhost:8000/polls/
```

### 3. Configurer chaque matin et chaque jour


**Option rapide avec cron :**
```bash
crontab -e
```

Ajouter ces lignes:
```crontab
0 8 * * * cd /home/maudyaiche/dev/site_reves/djangotutorial && python3 manage.py send_daily_reminder
0 10 * * * cd /home/maudyaiche/dev/site_reves/djangotutorial && python3 manage.py send_questionnaire_reminder
```

---

## ✨ Nouvelles fonctionnalités

### 1. 📬 Notifications
- **Chaque matin** : Rappel d'enregistrer un rêve
- **Après 7 jours** : Rappel de remplir le questionnaire
- **Interface** : Cloche 🔔 en haut à droite

### 2. 📋 Modal Pop-up
- Apparaît automatiquement 7 jours après inscription
- Sur les pages: enregistrer, profil, journal
- Peut être rejetée (réapparaît dans 24h)

### 3. 🔐 Session persistent
- Utilisateur reste connecté 30 jours
- Même après fermeture du navigateur
- Cookies sécurisés (HTTPS en production)

---

## 📖 Documentation

| Document | Contenu |
|----------|---------|
| [NOTIFICATIONS_IMPLEMENTATION.md](NOTIFICATIONS_IMPLEMENTATION.md) | Détails techniques complets |
| [SETUP_NOTIFICATIONS.md](SETUP_NOTIFICATIONS.md) | Installation détaillée |
| Ce fichier | Guide rapide |

---

## 🧪 Tester les 3 fonctionnalités

### Test 1: Notifications
```bash
# Créer une notification manuelle
python3 manage.py shell

from polls.models import Profil, Notification
profil = Profil.objects.first()
Notification.objects.create(
    profil=profil,
    notification_type='daily_reminder',
    title='Test',
    message='Ceci est un test'
)
# Actualiser la page, la cloche apparaît!
```

### Test 2: Modal après 7 jours
```bash
python3 manage.py shell

from polls.models import Profil
from django.utils import timezone
from datetime import timedelta

# Modifier la date de création
profil = Profil.objects.first()
profil.created_at = timezone.now() - timedelta(days=8)
profil.save()

# Actualiser la page, la modal apparaît!
```

### Test 3: Authentification persistante
1. Connectez-vous
2. Fermez le navigateur complètement
3. Rouvrez et allez à http://localhost:8000/polls/journal
4. ✅ Vous êtes toujours connecté!

---

## 🎯 Checklist

- [ ] Migrations appliquées (`migrate`)
- [ ] Cloche 🔔 visible en haut à droite
- [ ] Notifications apparaissent avec la commande
- [ ] Modal apparaît après 7 jours
- [ ] Session persiste après fermeture navigateur
- [ ] Tâches cron configurées

---

## 💡 Conseils

**Pour la production :**
- Utilisez APScheduler ou Celery au lieu de cron
- Mettre `SESSION_COOKIE_SECURE = True`
- Utilisez une vraie base de données (PostgreSQL)
- Armer les emails SMTP réels

**Pour le développement :**
- Laissez `DEBUG = True`
- Les emails vont dans la console
- `SESSION_COOKIE_SECURE = False`

---

## 🆘 Aide rapide

| Problème | Solution |
|----------|----------|
| "Table does not exist" | Exécutez `python3 manage.py migrate` |
| Cloche n'apparaît pas | Rechargez la page, vérifiez F12 Console |
| Modal ne s'affiche pas | Vérifiez que 7 jours sont écoulés |
| Pas connecté après fermeture | Vérifiez `SESSION_COOKIE_AGE` dans settings |

---

## 📞 Support rapide

1. **Lire la doc** : Voir [NOTIFICATIONS_IMPLEMENTATION.md](NOTIFICATIONS_IMPLEMENTATION.md)
2. **Tester manuellement** : Créer une notification via shell
3. **Vérifier les logs** : `F12 → Console` dans le navigateur
4. **Base de données** : `python3 manage.py dbshell`

---

## 🎓 Fichier modifiés/créés

✅ **Modèles:**
- `polls/models.py` - Nouveau modèle `Notification`

✅ **Vues:**
- `polls/views.py` - 3 vues API pour notifications

✅ **URLs:**
- `polls/urls.py` - 3 routes API

✅ **Admin:**
- `polls/admin.py` - Interface admin pour notifications

✅ **Commandes:**
- `polls/management/commands/send_daily_reminder.py`
- `polls/management/commands/send_questionnaire_reminder.py`

✅ **Front-end:**
- `polls/static/polls/notifications.css` - Styles
- `polls/static/polls/notifications.js` - JavaScript

✅ **Template:**
- `polls/templates/polls/base.html` - Intégration

✅ **Configuration:**
- `mysite/settings.py` - Session & Cookies

✅ **Documentation:**
- `NOTIFICATIONS_IMPLEMENTATION.md`
- `SETUP_NOTIFICATIONS.md`
- `init_notifications.py` - Script auto-installation

---

💬 Des questions ? Vérifie les MD files en haut de ce répertoire!
