# Dockerfile simple et léger basé sur l'approche resin-api
FROM python:3.12-slim

# Variables d'environnement Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Installer les dépendances système essentielles
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    gcc \
    libssl-dev \
    libffi-dev \
    postgresql-client \
    libpq-dev \
    # git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier requirements et installer les dépendances Python
# Téléchargemetn de torch pour cpu : pas besoin de torch pour CPu : c'était beaucoup trop gros. 
COPY requirements.txt .
RUN pip install --no-cache-dir --prefer-binary \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Pré-télécharger le modèle Whisper dans l'image (parce que ça marchait pas la transcription avant )
RUN python -c "import whisper; whisper.load_model('large-v3')"

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