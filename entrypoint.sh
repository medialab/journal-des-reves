#!/bin/bash

# Entrypoint script pour le conteneur Docker
# Exécute les migrations et collecte les fichiers statiques avant de lancer supervisord

set -e

echo "🚀 Initialisation du conteneur Docker..."

# Appliquer les migrations Django
echo "📦 Application des migrations Django..."
cd /app
python manage.py migrate --noinput

# Collecter les fichiers statiques
echo "📂 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput --clear

# Vérifier les configurations de sécurité
echo "🔒 Vérification des configurations Django..."
python manage.py check --deploy

echo ""
echo "✅ Initialisation terminée!"
echo "🌐 Démarrage de l'application avec Nginx + Gunicorn..."
echo ""

# Lancer supervisord (qui gère Nginx et Gunicorn)
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
