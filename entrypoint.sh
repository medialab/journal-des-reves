#!/bin/bash
# Entrypoint script - Basé sur resin-api
# Lance les migrations, collecte les fichiers statiques, puis démarre Gunicorn

set -e

echo "Apply database migrations"
python manage.py migrate

echo "Collect static files"
python manage.py collectstatic --noinput --clear

# Vérifier les configurations de sécurité
echo "🔒 Vérification des configurations Django..."
python manage.py check --deploy

echo ""
echo "✅ Initialisation terminée!"
echo "🌐 Démarrage de Gunicorn sur le port 8000..."
echo ""

# Démarrer Gunicorn (exec = remplace ce processus, PID 1)
echo "Starting Gunicorn."
exec gunicorn \
    --workers 2 \
    --worker-class sync \
    --bind 0.0.0.0:8000 \
    --timeout 300 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    config.wsgi:application
