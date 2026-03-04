# 📧 Email de Bienvenue à la Première Connexion

## Vue d'ensemble

Lors de la première connexion d'un utilisateur, un email de bienvenue lui est envoyé automatiquement pour :
- Le remercier de participer à l'étude
- Lui rappeler le cadre de l'expérience
- Clarifier ses responsabilités
- Assurer sa confidentialité

## Architecture

### Flux d'envoi

```
Utilisateur se connecte
         ↓
Signal user_logged_in déclenché
         ↓
Signal handler: send_welcome_email_on_first_login()
         ↓
Vérifier si profil.welcome_email_sent == False
         ↓
Envoyer email via service send_welcome_email()
         ↓
Mettre à jour profil.welcome_email_sent = True
```

### Fichiers clés

| Fichier | Rôle |
|---------|------|
| `polls/emails/services.py` | Service d'envoi d'email utilisant Django templates |
| `polls/signals.py` | Signal Django qui déclenche l'envoi à la première connexion |
| `polls/apps.py` | Enregistrement du signal dans la méthode `ready()` |
| `polls/models.py` | Champ `welcome_email_sent` dans le modèle Profil |
| `mysite/settings.py` | Configuration des emails (console en dev, SMTP en prod) |
| `polls/emails/templates/` | Templates d'email (texte et HTML) |

## Configuration

### Développement

Ajouter à `settings.py` (déjà configuré) :

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@reves-etude.fr'
```

Les emails s'affichent dans la console Django.

### Production

Modifier `settings.py` pour utiliser SMTP réel :

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'noreply@reves-etude.fr'
```

## Test rapide

```bash
cd djangotutorial
source ../mon_env/bin/activate
python manage.py shell
```

```python
from django.contrib.auth.models import User
from polls.emails.services import send_welcome_email

user = User.objects.first()
profil = user.profil

# Réinitialiser pour retester
profil.welcome_email_sent = False
profil.save()

# Envoyer
send_welcome_email(user, profil)
```

## Contenu de l'email

L'email inclut :
- Remerciement personnalisé
- Description du cadre de l'étude
- Responsabilités de l'utilisateur
- Informations de confidentialité
- Support et contact

Voir `polls/emails/templates/welcome_email.html` pour le rendu complet.

## Notes importantes

1. **Une seule fois** : L'email n'est envoyé qu'une seule fois grâce au flag `welcome_email_sent`
2. **Automatique** : Aucune action requise du développeur - c'est transparent
3. **Personnalisable** : Modifiez les templates pour changer le contenu
4. **Multilingue** : Codebase prête pour une version anglaise (à ajouter si nécessaire)
