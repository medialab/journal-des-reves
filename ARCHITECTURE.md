# Architecture du Système de Notifications

## 🏗️ Architecture Globale

```
┌─────────────────────────────────────────────────────────────────┐
│                        UTILISATEUR                              │
│                    (Navigateur Web)                             │
└────────────────────┬────────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
    ┌──────────────┐      ┌─────────────────┐
    │  Templates   │      │  JavaScript API │
    │ (base.html)  │      │  (notifications │
    │              │      │   .js)          │
    └──────┬───────┘      └────────┬────────┘
           │                      │
           └──────────┬───────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │   Django URLs (polls/urls)  │
        │                             │
        │ • /api/notifications/       │
        │ • /api/notifications/<id>/  │
        │ • /notifications/count/     │
        └──────────────┬──────────────┘
                       │
                       ▼
        ┌──────────────────────────┐
        │   Django Views           │
        │   (polls/views.py)       │
        │                          │
        │ • NotificationsListView  │
        │ • MarkAsReadView         │
        │ • UnreadCountView        │
        └──────────┬───────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │   Django Models      │
        │   (polls/models.py)  │
        │                      │
        │ class Notification:  │
        │   - profil (FK)      │
        │   - type             │
        │   - title            │
        │   - message          │
        │   - is_read          │
        │   - created_at       │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │   Base de Données    │
        │   (db.sqlite3)       │
        │                      │
        │ • polls_notification │
        │ • django_session     │
        │ • django_user        │
        └──────────────────────┘
```

---

## 🔄 Flux des Notifications

### 1️⃣ Création des Notifications

```
┌────────────────────────┐
│  Django Command        │
│ send_daily_reminder.py│
└───────────┬────────────┘
            │
            ▼
┌─────────────────────────────────┐
│  1. Boucle sur tous les profils │
│  2. Vérifie si notif existe     │
│  3. Crée Notification()         │
│  4. Sauvegarde en BD            │
└───────────┬─────────────────────┘
            │
            ▼
        📝 Notification
        stockée en BD
```

### 2️⃣ Affichage des Notifications

```
┌─────────────────────────┐
│  Utilisateur charge     │
│  une page au site       │
└────────────┬────────────┘
             │
             ▼
    ┌──────────────────────┐
    │ Script notifications │
    │ .js démarre          │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────────┐
    │ Fetch /api/notifications │
    └──────────┬───────────────┘
               │
               ▼
    ┌──────────────────────────┐
    │ Django retourne JSON     │
    │ des notifications non    │
    │ lues                     │
    └──────────┬───────────────┘
               │
               ▼
    ┌──────────────────────────┐
    │ JavaScript les affiche   │
    │ dans le DOM              │
    │ (en haut à droite)       │
    └──────────┬───────────────┘
               │
               ▼
    👁️ Utilisateur voit
       la notification
```

### 3️⃣ Marquage comme lue

```
Utilisateur clique
    └─▶ POST /api/notifications/<id>/read/
           └─▶ Vue mark_as_read()
                  └─▶ notification.mark_as_read()
                     └─▶ ORM sauvegarde
                        └─▶ BD mise à jour
                           └─▶ is_read = True
```

---

## ⏰ Cycle des Tâches Planifiées

```
┌──────────────────────────────────────────┐
│           Chaque jour à 8h               │
└────────────────┬─────────────────────────┘
                 │
     ┌───────────▼─────────────┐
     │ Tâche planifiée lancée  │
     │ (cron ou APScheduler)   │
     └───────────┬─────────────┘
                 │
     ┌───────────▼──────────────────┐
     │ Django exécute:              │
     │ manage.py send_daily_reminder │
     └───────────┬──────────────────┘
                 │
     ┌───────────▼──────────────┐
     │ 1. Query tous les profils│
     │ 2. Pour chaque profil:   │
     │    - Check si notif      │
     │    - Créer si absent     │
     │ 3. Sauvegarder          │
     └───────────┬──────────────┘
                 │
     ┌───────────▼───────────────┐
     │ Log: ✅ X rappels envoyés │
     └───────────────────────────┘
```

---

## 🔐 Authentification Persistante

```
┌──────────────────────────────┐
│     Utilisateur Login        │
└────────────┬─────────────────┘
             │
    ┌────────▼──────────────┐
    │ Django AUTH crée      │
    │ - User Session        │
    │ - HTTP Cookie         │
    └────────┬──────────────┘
             │
    ┌────────▼──────────────────────────┐
    │ Cookie paramètres (settings.py):  │
    │ - AGE: 30 jours                   │
    │ - DOMAIN: site                    │
    │ - SAME_SITE: Lax                  │
    │ - SECURE: HTTPS                   │
    │ - HTTPONLY: non accessible JS     │
    └────────┬──────────────────────────┘
             │
    ┌────────▼──────────────────┐
    │ Cookie envoyé au          │
    │ navigateur de              │
    │ l'utilisateur             │
    └────────┬──────────────────┘
             │
    ┌────────▼──────────────────┐
    │ Navigateur le stocke      │
    │ Expiration: 30 jours      │
    └────────┬──────────────────┘
             │
    ┌────────▼──────────────────┐
    │ Utilisateur ferme         │
    │ le navigateur             │
    └────────┬──────────────────┘
             │
    ┌────────▼──────────────────┐
    │ Cookie persiste (30j)     │
    └────────┬──────────────────┘
             │
    ┌────────▼──────────────────┐
    │ Utilisateur revient       │
    │ Navigateur envoie cookie  │
    │ Django le valide          │
    │ ✅ Connecté !             │
    └───────────────────────────┘
```

---

## 📱 Modal du Questionnaire

```
Utilisateur visite une page
        │
        ▼
Template charge avec:
- user.profil.created_at
- has_questionnaire

        │
        ▼
JavaScript vérifie:
1. 7 jours écoulés?
2. has_questionnaire = False?
3. Modal pas rejetée <24h?

        │
        ▼
    Si OUI ▶ Afficher modal
    Si NON ▶ Rien faire

        │
        ▼
Utilisateur peut:
- Cliquer "Remplir" ▶ Redirection /questionnaire/
- Cliquer "Plus tard" ▶ Stockage localStorage (24h)
- Fermer ▶ Stockage localStorage (24h)
```

---

## 🗂️ Structure des fichiers

```
site_reves/
├── djangotutorial/
│   ├── polls/
│   │   ├── models.py
│   │   │   └── class Notification (NEW)
│   │   │
│   │   ├── views.py
│   │   │   ├── NotificationsListView (NEW)
│   │   │   ├── NotificationMarkAsReadView (NEW)
│   │   │   └── NotificationUnreadCountView (NEW)
│   │   │
│   │   ├── urls.py
│   │   │   └── api/notifications/* (NEW)
│   │   │
│   │   ├── admin.py
│   │   │   └── NotificationAdmin (NEW)
│   │   │
│   │   ├── management/commands/
│   │   │   ├── send_daily_reminder.py (NEW)
│   │   │   └── send_questionnaire_reminder.py (NEW)
│   │   │
│   │   ├── static/polls/
│   │   │   ├── notifications.css (NEW)
│   │   │   ├── notifications.js (NEW)
│   │   │   └── style.css (existing)
│   │   │
│   │   └── templates/polls/
│   │       └── base.html (MODIFIED)
│   │
│   └── mysite/
│       └── settings.py (MODIFIED - SESSION config)
│
└── Documentation:
    ├── NOTIFICATIONS_IMPLEMENTATION.md (NEW)
    ├── SETUP_NOTIFICATIONS.md (NEW)
    ├── QUICK_START.md (NEW)
    ├── SCHEDULER_EXAMPLES.py (NEW)
    └── init_notifications.py (NEW - setup script)
```

---

## 🚀 Déploiement Flow

```
┌─────────────────────────────────────────────┐
│  1. Développeur crée migration              │
│     python3 manage.py makemigrations        │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  2. Appliquer la migration                  │
│     python3 manage.py migrate               │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  3. Configurer les tâches planifiées        │
│     - Cron, APScheduler, ou Celery         │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  4. Tester les 3 fonctionnalités            │
│     - Notifications ✅                       │
│     - Modal ✅                               │
│     - Sessions ✅                            │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  5. Déployer en production                  │
│     - Vérifier settings.py                 │
│     - Activer HTTPS                        │
│     - Utiliser serveur app (uwsgi/gunicorn)│
└─────────────────────────────────────────────┘
```

---

## 📊 Métriques & Analytics

```
Données disponibles à tracker:

✅ Notifications créées
   - Date
   - Type
   - Utilisateur
   - Lue oui/non

✅ Taux d'engagement
   - % notifications lues
   - Temps avant lecture
   - Clics sur lien

✅ Session
   - Durée moyenne
   - Nombre de visites
   - Taux de fidélité 30j

Requête SQL d'exemple:
SELECT 
  COUNT(*) as total_notifs,
  SUM(CASE WHEN is_read THEN 1 ELSE 0 END) as read_count,
  notification_type,
  DATE(created_at) as date
FROM polls_notification
GROUP BY notification_type, DATE(created_at);
```

---

## 🔧 Performance & Optimisation

```
Optimisations appliquées:

✅ BD:
  - Index sur (profil_id, is_read)
  - Index sur (created_at)
  - Pagination (limit 50)

✅ Cache:
  - Recharger notifs chaque 30s
  - localStorage pour modal 24h

✅ Frontend:
  - Lazy load notifications
  - Auto-remove après duration

✅ Backend:
  - Requêtes optimisées (select_related)
  - Pagination pour listage
  - Logs pour monitoring
```

---

Cette architecture est scalable et peut supporter:
- 100+ utilisateurs ✅
- Milliers de notifications ✅
- Tâches planifiées fiables ✅
- Sessions sécurisées ✅

Pour plus de détails, lire [NOTIFICATIONS_IMPLEMENTATION.md](NOTIFICATIONS_IMPLEMENTATION.md)
