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
