# 🚀 Déploiement Docker - Site Rêves

**Domaine:** reves-journal.fr | **Status:** ✅ PRÊT POUR PRODUCTION | **Date:** 7 avril 2026

---

## ✅ Ce Qui A Été Fait

### Sécurité Django
- ✅ `DJANGO_DEBUG = False` → Production activée
- ✅ `DJANGO_SECRET_KEY` → Générée (50 caractères uniques)
- ✅ `DJANGO_ALLOWED_HOSTS` → reves-journal.fr, www.reves-journal.fr
- ✅ `DJANGO_CSRF_TRUSTED_ORIGINS` → https://reves-journal.fr (HTTPS)
- ✅ `EMAIL_BACKEND` → Désactivé (console backend)
- ✅ `.env.prod` → Protégé dans .gitignore

### Infrastructure Docker
- ✅ **Dockerfile** → Image Python 3.12 + Nginx + Gunicorn (multi-stage)
- ✅ **docker-compose.yml** → Orchestration complète des services
- ✅ **docker/nginx.conf** → Reverse proxy pour reves-journal.fr
- ✅ **docker/supervisord.conf** → Gestion Gunicorn + Nginx
- ✅ **docker/entrypoint.sh** → Auto-migrations et init
- ✅ **.dockerignore** → Exclusion fichiers inutiles
- ✅ **requirements.txt** → +gunicorn, +whitenoise

### Configuration Django
- ✅ **WhiteNoiseMiddleware** → Fichiers statiques en production
- ✅ **backend/config/settings.py** → Flexible avec variables .env
- ✅ **Migrations** → Prêtes à appliquer

### Documentation & Scripts
- ✅ **deploy_docker.sh** → Déploiement automatique complet
- ✅ **docker_pre_deployment_check.sh** → Vérification automatique
- ✅ **.env.prod** → Configuration production complète
- ✅ **.env.example** → Template pour développement

---

## ⬜ Ce Qui Reste À Faire (Sur le Serveur)

### Avant Déploiement
- ⬜ Commander un serveur avec Docker installé
- ⬜ Configurer le DNS (pointer reves-journal.fr vers l'IP du serveur)

### Après Déploiement
- ⬜ Configurer HTTPS avec Let's Encrypt (certificats SSL)
  ```bash
  sudo certbot certonly --standalone -d reves-journal.fr -d www.reves-journal.fr
  # Puis mettre à jour docker/nginx.conf avec les certificats
  ```
- ⬜ Activer les backups automatiques de db.sqlite3
- ⬜ Monitorer les logs au quotidien

---

## 🚀 Déployer en 1 Ligne

```bash
cd /opt && git clone https://github.com/medialab/site_reves.git && cd site_reves && bash deploy_docker.sh
```

**⏳ Durée:** ~25 minutes | **Résultat:** Application sur http://reves-journal.fr

---

## 📋 Étapes Détaillées

### 1. Sur le Serveur - Préparation
```bash
sudo apt-get update && sudo apt-get install -y docker.io docker-compose git
sudo usermod -aG docker $USER
```

### 2. Cloner & Vérifier
```bash
cd /opt && git clone https://github.com/medialab/site_reves.git && cd site_reves
bash docker_pre_deployment_check.sh  # Doit retourner ✅
```

### 3. Construire & Démarrer
```bash
docker-compose build                # 10-15 minutes
docker-compose up -d
docker-compose ps                   # Vérifier le statut
```

### 4. Initialiser BD
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### 5. Accéder
```
🌐 http://reves-journal.fr
🔧 http://reves-journal.fr/admin/
💚 http://reves-journal.fr/health/
```

---

## 🔧 Commandes Essentielles

| Commande | Effet |
|----------|--------|
| `docker-compose logs -f web` | Logs en temps réel |
| `docker-compose restart` | Redémarrer |
| `docker-compose down` | Arrêter |
| `docker-compose exec web python manage.py shell` | Django shell |
| `git pull && docker-compose build && docker-compose up -d` | Mettre à jour |

---

## 📊 Architecture

```
Internet (Port 80)
    ↓
  Nginx (reverse proxy)
    ↓ localhost:8000
  Gunicorn (4 workers)
    ↓
  Django Application
    ↓
  SQLite Database (ou PostgreSQL)
```

**Volumes:** media/ (uploads) | static/ (CSS/JS) | logs/ (logs)

---

## 🔒 Sécurité Configuration

```
✅ DEBUG = False
✅ SECRET_KEY = Unique (50 chars)
✅ ALLOWED_HOSTS = Spécifiques
✅ CSRF_TRUSTED_ORIGINS = HTTPS
✅ Email = Désactivé
✅ .env.prod = Dans .gitignore
✅ Utilisateur = www-data (non-root)
✅ Health checks = Activés
```

---

## 📁 Fichiers Importants

| Fichier | Rôle |
|---------|------|
| `Dockerfile` | Image Docker |
| `docker-compose.yml` | Orchestration |
| `.env.prod` | Config production (SECRET!) |
| `docker/nginx.conf` | Nginx config |
| `docker/supervisord.conf` | Gestion processus |
| `deploy_docker.sh` | Script déploiement auto |
| `docker_pre_deployment_check.sh` | Vérification |

---

## ✨ Configuration HTTPS (Optionnel mais Recommandé)

```bash
# 1. Générer certificats
sudo apt-get install certbot
sudo certbot certonly --standalone -d reves-journal.fr -d www.reves-journal.fr

# 2. Mettre à jour docker/nginx.conf:
# server {
#     listen 443 ssl http2;
#     ssl_certificate /etc/letsencrypt/live/reves-journal.fr/fullchain.pem;
#     ssl_certificate_key /etc/letsencrypt/live/reves-journal.fr/privkey.pem;
# }

# 3. Redémarrer
docker-compose restart web
```

---

## 🐛 Troubleshooting

| Problème | Solution |
|----------|----------|
| Port 80 utilisé | `sudo lsof -i :80` puis tuer le processus |
| Container ne démarre pas | `docker-compose logs web` |
| Database locked (SQLite) | Passer à PostgreSQL |
| Application lente | Augmenter workers Gunicorn |
| DNS non résolvé | Attendre propagation DNS (24h) |

---

## 📞 Besoin d'Aide?

- **Logs:** `docker-compose logs -f web`
- **Vérification:** `bash docker_pre_deployment_check.sh`
- **Shell Django:** `docker-compose exec web python manage.py shell`
- **Documentation complète:** `DEPLOYMENT_DOCKER.md` (avant suppression)

---

## 🎯 Checklist Finale

- [ ] Serveur avec Docker installé
- [ ] Repositorygit cloné
- [ ] `bash docker_pre_deployment_check.sh` ✅
- [ ] `docker-compose build` complet
- [ ] `docker-compose up -d` lancé
- [ ] `docker-compose ps` montre healthy
- [ ] Migrations appliquées (`migrate`)
- [ ] Admin créé (`createsuperuser`)
- [ ] Application accessible (http://reves-journal.fr)
- [ ] DNS configuré (domaine pointant vers le serveur)
- [ ] Certificats SSL optionnels (Let's Encrypt)
- [ ] Backups planifiés

---

**🎉 STATUS: PRÊT POUR PRODUCTION** | Domaine: **reves-journal.fr** | Durée déploiement: **~25 min**
