#!/bin/bash
# Entrypoint script - Basé sur resin-api
# Lance les migrations, collecte les fichiers statiques, puis démarre Gunicorn

set -e

echo "Application des Migrations"
python manage.py migrate

echo "Chargement des émotions"
python manage.py loaddata emotions

echo "Collect les dossiers static"
# Ne pas utiliser --clear pour éviter de recréer tous les fichiers comme  ce que fait resin
python manage.py collectstatic --noinput

# Initialiser le compte admin ( si il n'y en a pas )
echo ""
echo "🔐 Initialisation du compte administrateur..."
python scripts/init_superuser.py
if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de l'initialisation de l'admin"
    exit 1
fi

# Vérifier les configurations de sécurité
echo ""
echo "🔒 Vérification des configurations Django..."
python manage.py check --deploy

echo ""
echo "✅ Initialisation terminée!"
echo "🌐 Démarrage de Gunicorn sur le port 8000..."
echo ""

# Démarrer Gunicorn (exec = remplace ce processus, PID 1)
# DEMANDER à Benjamin pour le nombre de worker ? !!!!
echo "Starting Gunicorn."
exec gunicorn \
    --workers 3 \
    --worker-class sync \
    --bind 0.0.0.0:8000 \
    --timeout 300 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    config.wsgi:application
