# README - Site Reves (vue generale, installation, licences)

Je maintiens ici un site Django pour une etude sociologique autour des reves.
Ce README est mon point d'entree principal: j'y explique ce que fait le site,
comment je le lance, ce qui est important pour la securite des comptes, et quelles
regles de licence je dois respecter.

## 1. Ce que fait le site

Je propose une plateforme ou les personnes peuvent:

- creer un compte,
- enregistrer leur reve (texte ou audio selon les ecrans),
- consulter leur journal,
- remplir un questionnaire (avec un delai d'acces),
- recevoir des rappels via le systeme de notifications.

Le coeur de l'application est dans `djangotutorial/polls/`.

## 2. Les 3 README que je garde

Pour simplifier la doc, je garde seulement ces 3 grands README:

1. `README.md` (ce fichier): site, architecture generale, securite, licences
2. `README_AUDIO_TRANSCRIPTION.md`: enregistrement audio + transcription + Safari
3. `README_PWA_NOTIFICATIONS.md`: PWA + notifications + modal + sessions persistantes

Je garde aussi `SECURITY_README.md` a part, comme demande.

## 3. Prerequis

Je travaille avec:

- Python 3.12+
- Django (projet dans `djangotutorial/`)
- un environnement virtuel (`mon_env/`)
- SQLite pour le developpement local
- ffmpeg (recommande pour certains flux audio)

## 4. Demarrage rapide (debutant)

Depuis la racine du projet:

```bash
source mon_env/bin/activate
cd djangotutorial
python manage.py migrate
python manage.py runserver
```

Ensuite j'ouvre:

- accueil: `http://localhost:8000/polls/`
- connexion: `http://localhost:8000/accounts/login/`
- inscription: `http://localhost:8000/polls/signup/`
- journal: `http://localhost:8000/polls/journal/`

## 5. Architecture generale (simple)

Je garde une architecture Django classique:

- `djangotutorial/mysite/`: configuration (settings, urls globales)
- `djangotutorial/polls/models.py`: modeles (`Profil`, `Reve`, `Questionnaire`, `Notification`, etc.)
- `djangotutorial/polls/views.py`: vues HTML + endpoints JSON
- `djangotutorial/polls/templates/`: pages du site
- `djangotutorial/polls/static/`: CSS/JS
- `djangotutorial/polls/management/commands/`: commandes planifiees (rappels, etc.)

## 6. Comptes, consentement et securite

### 6.1 Inscription et consentements

Lors de l'inscription, je fais accepter 3 consentements obligatoires
(traitement des donnees, compte protege par mot de passe, autorisation de citation).

Ces consentements sont traces dans `Profil` avec une date d'acceptation.

### 6.2 Mot de passe et validation

Je m'appuie sur Django:

- hashage PBKDF2 (`pbkdf2_sha256`),
- validateurs de robustesse (longueur min, mot de passe trop commun, etc.),
- protection CSRF sur les formulaires.

Je ne stocke jamais de mot de passe en clair.

### 6.3 Integrite des donnees utilisateur

Je maintiens les garanties suivantes:

- unicite du `username` (modele `User` Django),
- relation `User <-> Profil` en OneToOne,
- contraintes de cle etrangere sur les objets relies.

Consequence pratique: je ne peux pas avoir deux profils pour le meme utilisateur.

### 6.4 Delai d'acces au questionnaire

Le questionnaire n'est pas accesible immediatement apres inscription.

- Le profil stocke `created_at`.
- Le code verifie qu'un delai de 7 jours est passe.
- Avant ce delai, une page d'attente explique le fonctionnement.

Cela evite un remplissage trop precoce et maintient la coherence du protocole.

### 6.5 Email de bienvenue (premiere connexion)

A la premiere connexion, j'envoie un email de bienvenue via signal Django.

- signal `user_logged_in`,
- service d'envoi dedie,
- drapeau `welcome_email_sent` pour ne pas renvoyer plusieurs fois.

En developpement, les emails peuvent sortir dans la console.

## 7. Base de donnees et migrations

Commandes utiles:

```bash
cd djangotutorial
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations
```

Je recommande de lancer `python manage.py check` apres les changements importants.

## 8. Liens vers les 2 autres README

- audio + transcription: `README_AUDIO_TRANSCRIPTION.md`
- PWA + notifications: `README_PWA_NOTIFICATIONS.md`

## 9. Licences (important)

### 9.1 Licence du projet

Le projet est distribue sous **GNU AGPL v3**.

Le texte complet est dans `LICENSE`.

En pratique, si je redistribue ou expose une version modifiee du logiciel via un service en ligne,
je dois respecter les obligations AGPL (notamment la mise a disposition du code source correspondant).

### 9.2 Dependances tierces

Le projet utilise des bibliotheques tierces (Django, outils JS, etc.)
qui ont chacune leur propre licence. Avant diffusion publique, je fais un audit
des licences de dependances pour verifier la compatibilite.

### 9.3 Securite

La documentation securite reste separee dans:

- `SECURITY_README.md` (conserve tel quel)

## 10. FAQ debutant

### Je lance le serveur mais la page ne s'affiche pas

Je verifie:

1. que mon venv est active,
2. que je suis dans `djangotutorial/`,
3. que les migrations sont appliquees,
4. que le port 8000 n'est pas deja pris.

### Je ne peux pas me connecter apres inscription

Je controle:

1. les erreurs formulaire (username/email/mot de passe),
2. que les consentements obligatoires ont ete coches,
3. que je vais bien sur `/accounts/login/`.

### Je veux verifier vite l'etat du projet

```bash
cd djangotutorial
python manage.py check
python manage.py test
```

## 11. Resume

Si je debute sur ce repo, je lis dans cet ordre:

1. `README.md` (ce fichier)
2. `README_AUDIO_TRANSCRIPTION.md`
3. `README_PWA_NOTIFICATIONS.md`
4. `SECURITY_README.md`


---

## Annexes migrees (Site, comptes, integrite)



### Source migree: `AUTHENTICATION_IMPLEMENTATION.md`

# Système d'Authentification et de Consentement - Site Rêves

## Vue d'ensemble

Le site implémente un système d'authentification sécurisé avec gestion du consentement pour l'enquête de recherche. Les utilisateurs doivent créer un compte ET accepter les trois consentements obligatoires avant d'accéder aux fonctionnalités principales.

## Flux utilisateur

1. **Page d'accueil** : Accessible à tous
2. **Page de connexion** : Proposer les options :
   - Se connecter avec compte existant
   - Ou créer un nouveau compte (lien "Créer un compte")
3. **Création de compte** : 
   - Remplir identifiants (nom d'utilisateur, email)
   - Créer un mot de passe sécurisé
   - Lire et accepter les 3 conditions de consentement
   - Confirmer la création
4. **Questionnaire** : Remplir les informations socio-démographiques (etape suivante de la création)
5. **Journal des rêves** : Accès à toutes les fonctionnalités du site

## Implémentation technique

### 1. Modèle de données (models.py)

Les champs de consentement ont été ajoutés au modèle `Profil` :

```python
# Champs de consentement pour l'enquête
consent_data_processing = BooleanField()        # Accepte le traitement des données
consent_password_account = BooleanField()       # Accepte un compte protégé
consent_quote_expressions = BooleanField()      # Autorise les citations
consent_date = DateTimeField()                  # Date d'acceptation
```

### 2. Formulaire d'inscription (forms.py)

Classe `SignUpForm` qui :
- Utilise `UserCreationForm` de Django pour la validation de sécurité
- Ajoute les champs d'email et des trois consentements
- Valide que tous les consentements sont cochés
- Hache automatiquement le mot de passe (PBKDF2)
- Crée automatiquement un profil utilisateur associé

### 3. Vue d'inscription (views.py)

Classe `SignUpView` qui :
- Affiche le formulaire d'inscription
- Traite la soumission du formulaire
- Authentifie et connecte automatiquement l'utilisateur après inscription
- Redirige vers le questionnaire (étape suivante)

### 4. Template d'inscription (signup.html)

Page qui affiche :
- La mention complète d'information et consentement
- Les champs d'identifiants (username, email, password)
- Les trois cases à cocher pour les consentements
- Validation client et serveur

## Sécurité

### Hachage des mots de passe

Django utilise **PBKDF2** (Password-Based Key Derivation Function 2) par défaut :
- Algorithme : `pbkdf2_sha256`
- Nombre d'itérations : $1200000
- Les mots de passe ne sont jamais stockés en texto
- Impossible de récupérer le mot de passe original

Format du hash stocké en base de données :
```
pbkdf2_sha256$1200000$[random_salt]$[hash]
```

### Validation des mots de passe

Django applique automatiquement les validations suivantes :
1. **UserAttributeSimilarityValidator** : Le mot de passe ne doit pas être similaire aux attributs utilisateur (username, email...)
2. **MinimumLengthValidator** : Minimum 8 caractères
3. **CommonPasswordValidator** : Ne doit pas être un mot de passe courant
4. **NumericPasswordValidator** : Ne doit pas être uniquement numérique

### Protection CSRF

- Tous les formulaires utilisent le jeton CSRF (`{% csrf_token %}`)
- Le middleware CSRF (`CsrfViewMiddleware`) est activé
- Validation automatique des tokens sur POST/PUT/DELETE

### Validation des emails

- L'email est requis et validé
- Unicité vérifiée : impossible d'avoir deux comptes avec le même email
- Format email validé

### Authentification

- Authentification basée sur username (Django par défaut)
- Session sécurisée avec cookies httponly
- LoginRequiredMixin pour protéger les pages

## Base de données

### Schéma des consentements

```
Profil
├── consent_data_processing (Boolean)
├── consent_password_account (Boolean)
├── consent_quote_expressions (Boolean)
└── consent_date (DateTime)
```

### Migration

La migration `0007_profil_consent_date_and_more.py` ajoute :
- 3 champs BooleanField (défaut: False)
- 1 champ DateTimeField (défaut: None)

## Routes

| URL | Méthode | Description |
|-----|---------|-------------|
| `/polls/signup/` | GET | Affiche le formulaire d'inscription |
| `/polls/signup/` | POST | Traite la création de compte |
| `/accounts/login/` | GET/POST | Page de connexion Django |
| `/polls/` | GET | Page d'accueil (accessible à tous) |
| `/polls/questionnaire/` | GET/POST | Questionnaire (LoginRequired) |
| `/polls/journal/` | GET | Journal des rêves (LoginRequired) |

## Installation et mise en route

1. **Migrations appliquées** ✓
   ```bash
   python manage.py migrate
   ```

2. **Vérifier la configuration** ✓
   ```bash
   python manage.py check
   ```

3. **Lancer le serveur** ✓
   ```bash
   python manage.py runserver
   ```

4. **Accéder au site**
   - Page d'inscription : `http://localhost:8000/polls/signup/`
   - Page de connexion : `http://localhost:8000/accounts/login/`
   - Accueil : `http://localhost:8000/polls/`

## Test d'inscription

Un test complet a été effectué et validé :

✓ Formulaire valide avec tous les consentements  
✓ Validation des mots de passe identiques  
✓ Validation de la force du mot de passe  
✓ Validation des consentements obligatoires  
✓ Création de l'utilisateur et du profil  
✓ Hashage sécurisé du mot de passe (PBKDF2)  
✓ Enregistrement des consentements avec date  

## Conformité RGPD/Légale

- **Mention d'information** : Affichée avant création du compte
- **Consentement explicite** : 3 cases à cocher obligatoires
- **Documentation** : Les consentements acceptés et la date sont enregistrés
- **Droit de rétraction** : Peut être implémenté via un formulaire "retirer le consentement"
- **Pas de stockage en texto** : Les mots de passe sont toujours hashés

## Prochaines étapes

1. Mettre en place un lien/formulaire pour retirer le consentement
2. Créer un page d'administration pour visualiser les consentements acceptés
3. Implémenter un audit log pour les changements de consentement
4. Ajouter une vérification de l'email (confirmation par email)
5. Implémenter une page de modification des consentements existants



### Source migree: `djangotutorial/DATA_INTEGRITY.md`

# 🔒 Garanties d'Unicité des Identifiants Utilisateurs

## ✅ Résumé : Vos données sont protégées

**Django garantit à 100% l'unicité des utilisateurs.** Il est **impossible** d'avoir deux personnes avec le même `user` grâce aux contraintes de base de données et aux validations Django.

---

## 🛡️ Contraintes d'Unicité en Place

### 1. **Modèle User de Django** (Table `auth_user`)

```sql
CREATE TABLE "auth_user" (
    "id" integer PRIMARY KEY AUTOINCREMENT,
    "username" varchar(150) NOT NULL UNIQUE,  ← ✅ UNIQUE
    "email" varchar(254) NOT NULL,
    ...
);
```

**Garanties :**
- ✅ **`username` est UNIQUE** : Contrainte au niveau base de données
- ✅ Django valide l'unicité avant l'insertion
- ✅ Impossible de créer deux users avec le même username

**Test :**
```python
# Tentative de créer un doublon
User.objects.create_user(username='admin', ...)  # ❌ ERREUR si 'admin' existe déjà
# IntegrityError: UNIQUE constraint failed: auth_user.username
```

---

### 2. **Relation User ↔ Profil** (Table `polls_profil`)

```sql
CREATE TABLE "polls_profil" (
    "id" integer PRIMARY KEY AUTOINCREMENT,
    "user_id" integer NOT NULL UNIQUE          ← ✅ UNIQUE
        REFERENCES "auth_user" ("id"),
    "email" varchar(254) NOT NULL,
    ...
);
```

**Garanties :**
- ✅ **`user_id` est UNIQUE** : Un User ne peut avoir qu'UN SEUL Profil
- ✅ **OneToOneField** dans Django : `user = models.OneToOneField(User)`
- ✅ Contrainte de clé étrangère (`REFERENCES "auth_user"`)

**Test :**
```python
# Tentative de créer un 2ème profil pour le même user
user = User.objects.get(username='admin')
Profil.objects.create(user=user, ...)  # ❌ ERREUR si profil existe déjà
# IntegrityError: UNIQUE constraint failed: polls_profil.user_id
```

---

### 3. **Relations Reve et Questionnaire**

#### Table `polls_reve`
```sql
"user_id" integer NULL REFERENCES "auth_user" ("id")
"profil_id" bigint NOT NULL REFERENCES "polls_profil" ("id")
```

#### Table `polls_questionnaire`
```sql
"user_id" integer NULL REFERENCES "auth_user" ("id")
"profil_id" bigint NOT NULL REFERENCES "polls_profil" ("id")
```

**Garanties :**
- ✅ **ForeignKey** : Chaque rêve/questionnaire est lié à UN user/profil valide
- ✅ **Clés étrangères** : Empêche les liens vers des users inexistants
- ✅ **CASCADE on_delete** : Si un user est supprimé, ses données sont supprimées

---

## 🔍 Vérification de l'Intégrité Actuelle

**Résultats de l'audit (4 mars 2026) :**

```
✅ Total users: 3
✅ Usernames uniques: 3
✅ Doublons usernames: 0

✅ Total profils: 3
✅ Users avec plusieurs profils: 0

✅ Relation 1:1 User ↔ Profil : VALIDE
```

**Détails :**
| User ID | Username | Email | Profil ID |
|---------|----------|-------|-----------|
| 1 | admin | maudyaiche@gmail.com | 1 |
| 5 | Maud | y.maud@hotmail.fr | 4 |
| 6 | testuser | test@example.com | 5 |

---

## 🚫 Scénarios Impossibles

### ❌ Créer un username en doublon
```python
User.objects.create_user(username='admin', password='xxx')
# IntegrityError: UNIQUE constraint failed
```

### ❌ Créer un 2ème profil pour le même user
```python
user = User.objects.get(username='admin')
Profil.objects.create(user=user, email='test@test.com')
# IntegrityError: UNIQUE constraint failed
```

### ❌ Avoir un Reve/Questionnaire sans user valide
```python
Reve.objects.create(user_id=999, ...)  # user_id 999 n'existe pas
# IntegrityError: FOREIGN KEY constraint failed
```

---

## 📋 Validations Supplémentaires

### Au niveau formulaire (SignUpForm)

```python
class SignUpForm(UserCreationForm):
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Vérification d'unicité de l'email dans Profil
        if Profil.objects.filter(email=email).exists():
            raise ValidationError("Cet email est déjà utilisé.")
        return email
```

### Au niveau vue (SignUpView)

```python
def post(self, request):
    form = SignUpForm(request.POST)
    if form.is_valid():
        user = form.save()  # Django valide automatiquement l'unicité
        Profil.objects.create(user=user, ...)
```

---

## 🔧 Recommandations Supplémentaires

### 1. Ajouter l'unicité de l'email dans Profil

Actuellement, l'email dans `Profil` n'a pas de contrainte `unique=True`.

**Avant (actuel) :**
```python
class Profil(models.Model):
    email = models.EmailField()  # Pas de contrainte unique
```

**Recommandé :**
```python
class Profil(models.Model):
    email = models.EmailField(
        unique=True,
        error_messages={
            'unique': "Un profil avec cet email existe déjà."
        }
    )
```

**Migration à créer :**
```bash
python manage.py makemigrations
python manage.py migrate
```

---

### 2. Script de vérification régulière

```python
# polls/management/commands/check_data_integrity.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from polls.models import Profil

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Vérifier doublons username
        usernames = User.objects.values_list('username', flat=True)
        if len(usernames) != len(set(usernames)):
            self.stdout.write(self.style.ERROR('❌ Doublons username détectés'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Usernames uniques'))
        
        # Vérifier User ↔ Profil 1:1
        users_without_profil = User.objects.filter(profil__isnull=True).count()
        if users_without_profil > 0:
            self.stdout.write(self.style.WARNING(f'⚠️ {users_without_profil} users sans profil'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Tous les users ont un profil'))
```

**Usage :**
```bash
python manage.py check_data_integrity
```

---

## 📊 Résumé des Protections

| Niveau | Protection | Status |
|--------|-----------|--------|
| Base de données | `username UNIQUE` | ✅ Actif |
| Base de données | `user_id UNIQUE` dans Profil | ✅ Actif |
| Base de données | Foreign Keys | ✅ Actif |
| Django ORM | OneToOneField | ✅ Actif |
| Django Forms | Validation username | ✅ Actif |
| Django Forms | Validation email | ✅ Actif |
| Application | Email unique Profil | ⚠️ Recommandé |

---

## 🎯 Conclusion

**Vous pouvez être 100% sûr que deux personnes ne partageront jamais le même `user`.**

Les garanties en place :
1. ✅ Contrainte `UNIQUE` au niveau SQL
2. ✅ Validation Django avant insertion
3. ✅ OneToOneField User ↔ Profil
4. ✅ Foreign Keys pour Reve et Questionnaire
5. ✅ Cascade suppression pour l'intégrité

**Vos données de recherche sont protégées contre les doublons d'identifiants.**



### Source migree: `djangotutorial/EMAIL_WELCOME_SYSTEM.md`

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



### Source migree: `djangotutorial/QUESTIONNAIRE_ACCESS_DELAY.md`

# 📋 Système de Délai d'Accès au Questionnaire

## Vue d'ensemble

Le questionnaire est maintenant soumis à une **restriction temporelle de 7 jours** :
- Les utilisateurs doivent attendre **1 semaine** après la création de leur profil
- Pendant cette période, une page d'attente élégante est affichée
- Après 7 jours, l'accès au questionnaire est automatiquement débloqué

## Architecture

### Modèle Profil - Nouvelles fonctionnalités

**Champ ajouté :**
```python
created_at = models.DateTimeField(auto_now_add=True)
```

**Méthodes ajoutées :**

1. `can_access_questionnaire()` : Retourne `True` si 7 jours se sont écoulés depuis la création
2. `days_until_questionnaire_access()` : Retourne le nombre de jours restants (0 si déjà accessible)

### Vue QuestionnaireView - Logique mise à jour

**Méthode GET :**
1. Vérifie l'authentification
2. Vérifie `profil.can_access_questionnaire()`
3. Si `False` → Affiche `questionnaire_waiting.html` avec countdown
4. Si `True` → Affiche le formulaire normal

**Méthode POST :**
1. Vérifie l'authentification
2. Vérifie `profil.can_access_questionnaire()` (sécurité)
3. Bloque la soumission si pas encore accessible
4. Enregistre avec `user` et `profil`

### Template questionnaire_waiting.html

**Design élégant avec :**
- Gradient violet moderne
- Grande icône ⏳
- Countdown visuel du nombre de jours restants
- Explication pédagogique du délai
- Bouton vers le journal
- Date précise de disponibilité

## Flux utilisateur

```
Utilisateur créé nouveau compte
         ↓
created_at = maintenant
         ↓
Accès /questionnaire/
         ↓
days_remaining = 7
         ↓
Page d'attente affichée
         ↓
... 7 jours passent ...
         ↓
can_access_questionnaire() = True
         ↓
Formulaire questionnaire accessible
```

## Fichiers modifiés

| Fichier | Changements |
|---------|-------------|
| `polls/models.py` | + `created_at`, + `can_access_questionnaire()`, + `days_until_questionnaire_access()` |
| `polls/views.py` | Logique de vérification dans `QuestionnaireView.get()` et `.post()` |
| `polls/templates/polls/questionnaire_waiting.html` | Nouveau template pour page d'attente |
| Migration `0013_profil_created_at.py` | Ajout du champ avec `timezone.now` comme défaut |

## Test rapide

```bash
cd djangotutorial
source ../mon_env/bin/activate
python manage.py shell
```

```python
from polls.models import Profil

# Vérifier un profil
profil = Profil.objects.first()
print(f"Créé le: {profil.created_at}")
print(f"Jours restants: {profil.days_until_questionnaire_access()}")
print(f"Peut accéder: {profil.can_access_questionnaire()}")

# Simuler accès après 7 jours (pour test)
from django.utils import timezone
profil.created_at = timezone.now() - timezone.timedelta(days=8)
profil.save()
print(f"Peut accéder maintenant: {profil.can_access_questionnaire()}")
```

## Pour bypass le délai (admin/test)

Si vous voulez tester le questionnaire immédiatement sans attendre 7 jours :

```python
# Dans le shell Django
from polls.models import Profil
from django.utils import timezone

profil = Profil.objects.get(user__username='votre_username')
profil.created_at = timezone.now() - timezone.timedelta(days=8)
profil.save()
```

## Sécurité

- ✅ Vérification côté serveur dans GET et POST
- ✅ Pas de manipulation possible côté client
- ✅ Message d'erreur si tentative de bypass
- ✅ Redirection automatique vers page d'attente

## UX / Design

- Interface moderne et engageante
- Explication claire du "pourquoi"
- Countdown visuel motivant
- Suggestions d'actions alternatives (journal, profil)
- Date précise de disponibilité
- Call-to-action vers le journal

## Notes importantes

1. **Profils existants** : Tous les profils créés avant cette fonctionnalité ont `created_at` défini à la date de migration
2. **Nouveaux profils** : `created_at` est automatiquement défini à la création
3. **Timezone-aware** : Utilise `timezone.now()` pour gérer les fuseaux horaires
4. **Pas de décompte minute/heure** : Le calcul est en jours complets pour simplifier l'UX

