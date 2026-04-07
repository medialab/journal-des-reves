# Stage 1: Builder - Étape de construction
FROM python:3.12-slim as builder

WORKDIR /app

# Installer les dépendances système requises pour la compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements et installer les dépendances Python
COPY requirements.txt .
RUN pip install --user --no-cache-dir --prefer-binary -r requirements.txt

# Stage 2: Runtime - Étape finale pour la production
FROM python:3.12-slim

# Installer Nginx et autres dépendances runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier les dépendances Python du builder
COPY --from=builder /root/.local /root/.local

# Définir le PATH pour utiliser les paquets Python installés
ENV PATH=/root/.local/bin:$PATH PIP_NO_CACHE_DIR=1 PYTHONUNBUFFERED=1

# Copier le code Django
COPY backend/ .

# Créer les répertoires nécessaires
RUN mkdir -p /app/static && \
    mkdir -p /app/media && \
    mkdir -p /app/logs && \
    mkdir -p /var/log/app

# Collecter les fichiers statiques Django
RUN python manage.py collectstatic --noinput --clear

# Copier la configuration Nginx
COPY docker/nginx.conf /etc/nginx/sites-available/default
# Désactiver le site default nginx
RUN rm -f /etc/nginx/sites-enabled/default && \
    ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

# Copier la configuration supervisord
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copier le script entrypoint
COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Changement de permissions
RUN chown -R www-data:www-data /app && \
    chown -R www-data:www-data /var/log/app

# Exposer le port 80 (HTTP)
EXPOSE 80

# Commande pour démarrer l'entrypoint (qui lance supervisord)
CMD ["/app/entrypoint.sh"]
