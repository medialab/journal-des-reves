#!/bin/bash

# Entrypoint script pour le conteneur Docker
# Exécute les tâches de démarrage avant de lancer supervisord

set -e

echo "🚀 Initialisation du conteneur Docker..."

# Attendre que la base de données soit disponible (si PostgreSQL externe)
# DATABASE_HOST=${DATABASE_HOST:-localhost}
# DATABASE_PORT=${DATABASE_PORT:-5432}
# until nc -z $DATABASE_HOST $DATABASE_PORT; do
#   echo "Attente de la base de données..."
#   sleep 1
# done
# echo "Base de données disponible!"

# Appliquer les migrations
echo "📦 Application des migrations Django..."
cd /app
python manage.py migrate --noinput || true

# Collecter les fichiers statiques
echo "📂 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput --clear || true

# Vérifier les problématiques de sécurité
echo "🔒 Vérification de la sécurité..."
python manage.py check --deploy --fail-level WARNING || true

echo ""
echo "✅ Initialisation terminée!"
echo "🌐 Démarrage de l'application..."
echo ""

# Lancer supervisord
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
