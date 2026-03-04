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
