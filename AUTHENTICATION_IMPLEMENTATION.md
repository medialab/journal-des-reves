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
