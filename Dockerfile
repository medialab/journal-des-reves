# Dockerfile simple et léger basé sur l'approche resin-api
FROM python:3.12-slim

# Variables d'environnement Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Installer les dépendances système essentielles
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    gcc \
    libssl-dev \
    libffi-dev \
    postgresql-client \
    libpq-dev \
    # git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier requirements et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copier uniquement le code source (pas les données)
COPY backend/config ./config
COPY backend/reves ./reves
COPY backend/manage.py .
COPY scripts ./scripts

# Créer les répertoires pour les fichiers dynamiques (volumes à runtime)
# En gros ça va créer une architecture au sein du docker file. 
# Du coup comme il copie pas les données il doit créer un chemin pour metre les données. 
RUN mkdir -p /app/static && \
    mkdir -p /app/media && \
    mkdir -p /app/logs

# Copier le script entrypoint
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Exposer le port 8000 (Gunicorn)
EXPOSE 8000

# Lancer l'entrypoint
CMD ["./entrypoint.sh"]
