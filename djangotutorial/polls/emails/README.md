# 📧 Système d'Email de Bienvenue

Ce dossier contient la logique pour gérer l'envoi d'emails aux utilisateurs lors de leur première connexion.

## Structure

```
emails/
├── __init__.py
├── services.py          # Service d'envoi d'email
├── signals.py          # (dans le dossier parent) Signaux pour détecter la première connexion
└── templates/
    ├── welcome_email.txt    # Template texte
    └── welcome_email.html   # Template HTML
```

## Fonctionnement

1. **Détection de la première connexion** : Le signal `user_logged_in` de Django est utilisé
2. **Vérification** : On vérifie si l'email de bienvenue a déjà été envoyé (champ `profil.welcome_email_sent`)
3. **Envoi** : Le service `send_welcome_email()` envoie l'email avec une version texte et HTML
4. **Suivi** : Le champ `profil.welcome_email_sent` est mis à True pour éviter les envois futurs

## Configuration

### En développement (DEBUG=True)

Les emails sont affichés dans la console Django (par défaut).

### En production (DEBUG=False)

Configurer les paramètres SMTP dans `mysite/settings.py`:

```python
EMAIL_HOST = 'smtp.gmail.com'  # ou votre serveur SMTP
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'noreply@reves-etude.fr'
```

## Test

Pour tester l'envoi d'email en développement :

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
from polls.models import Profil
from polls.emails.services import send_welcome_email

user = User.objects.first()  # Prendre un utilisateur existant
profil = user.profil

# Réinitialiser le flag pour retester
profil.welcome_email_sent = False
profil.save()

# Envoyer l'email
send_welcome_email(user, profil)
```

L'email s'affichera dans la console Django.

## Personnalisation

Vous pouvez personnaliser le contenu de l'email en modifiant les fichiers dans `templates/`:

- `welcome_email.txt` : Version texte
- `welcome_email.html` : Version HTML avec style

Les variables disponibles dans les templates :
- `first_name` : Prénom de l'utilisateur
- `username` : Nom d'utilisateur
