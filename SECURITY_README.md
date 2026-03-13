# README Sécurité (Débutant)

## 1. Ce qui est déjà en place dans le projet

La sécurité du projet repose déjà sur plusieurs bases solides. L'authentification Django est active, avec la gestion des sessions, la protection CSRF et la validation des mots de passe. Le flux « mot de passe oublié » est aussi en place : un utilisateur peut demander un lien de réinitialisation par email, cliquer sur ce lien, puis définir un nouveau mot de passe. En développement, les emails sont affichés dans la console Django pour tester facilement sans serveur SMTP réel. Cela permet de vérifier tout le parcours de récupération de compte de bout en bout.

Le projet inclut aussi des en-têtes de sécurité et des réglages importants dans les settings, comme la protection contre le clickjacking (`X_FRAME_OPTIONS`), la politique de référent (`SECURE_REFERRER_POLICY`) et la politique COOP (`SECURE_CROSS_ORIGIN_OPENER_POLICY`). Les cookies de session et CSRF sont déjà prévus pour passer en mode sécurisé en production. Les vérifications Django de type `manage.py check --deploy` ont été lancées, et les alertes restantes sont normales tant que l'on travaille en mode développement (`DEBUG=True`, pas de HTTPS local forcé).

## 2. Comment la configuration d'environnement est gérée (et protégée)

Le projet lit ses variables d'environnement de façon flexible. Par défaut, Django peut charger `djangotutorial/.env`, mais il peut aussi charger un fichier externe via `DJANGO_ENV_FILE`. Cela permet d'utiliser un fichier stocké dans `mon_env`, par exemple `mon_env/reves.dev.env`, pour séparer la configuration locale du code source. C'est pratique pour un débutant, car on garde une méthode simple et claire pour changer les réglages sans modifier le code Python.

La protection Git est déjà en place pour éviter les fuites de secrets. Le dossier `mon_env/` est ignoré par `.gitignore`, tout comme les fichiers `.env`. Donc les secrets locaux, mots de passe SMTP et clés privées ne sont pas poussés sur le dépôt par erreur. En complément, deux fichiers d'exemple existent : `.env.example` pour le développement et `.env.prod.example` pour préparer la production. Ces fichiers servent de modèles et ne contiennent pas de secrets réels.

## 3. Ce qu'il faut faire quand tu passeras en production

En production, l'objectif est d'activer les options de sécurité strictes qui restent volontairement assouplies en dev. Il faudra mettre `DJANGO_DEBUG=false`, définir des `ALLOWED_HOSTS` précis, activer la redirection HTTPS (`DJANGO_SECURE_SSL_REDIRECT=true`), activer HSTS et passer les cookies session/CSRF en mode `secure`. À ce moment-là, les avertissements de `check --deploy` disparaîtront et le projet sera aligné avec les recommandations Django de sécurité pour un déploiement réel.

Il faudra aussi configurer un vrai SMTP pour l'envoi d'emails de réinitialisation, avec des identifiants stockés uniquement dans les variables d'environnement. Enfin, garde une routine simple : lancer régulièrement les checks Django, tester le parcours de connexion/réinitialisation, et vérifier que les secrets restent hors Git. Avec cette discipline, tu auras une base sécurité propre, compréhensible et maintenable, même en étant débutant.
