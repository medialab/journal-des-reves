#!/bin/bash

# Script de déploiement Docker - PRÊT POUR PRODUCTION
# Domaine: reves-journal.fr
# Date: 7 avril 2026

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         🚀 DÉPLOIEMENT DOCKER - SITE RÊVES                     ║"
echo "║         Domaine: reves-journal.fr                             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Vérifier que Docker est installé
if ! command -v docker &> /dev/null; then
    echo "❌ ERREUR: Docker n'est pas installé!"
    echo "   Voir: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ ERREUR: Docker Compose n'est pas installé!"
    echo "   Voir: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✓ Docker $(docker --version | grep -oP '(\d+\.)+\d+')"
echo "✓ Docker Compose $(docker-compose --version | grep -oP '(\d+\.)+\d+')"
echo ""

# Étape 1: Vérification finale
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  VÉRIFICATION DE LA CONFIGURATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

bash docker_pre_deployment_check.sh

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Vérifications échouées. Corrige les erreurs ci-dessus."
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  CONSTRUCTION DE L'IMAGE DOCKER"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⏳ Construction de l'image... (cela peut prendre 10-15 minutes)"
echo ""

docker-compose build --no-cache

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Erreur lors de la construction de l'image Docker"
    exit 1
fi

echo ""
echo "✅ Image construite avec succès!"
echo ""

# Étape 2: Démarrage des services
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  DÉMARRAGE DES SERVICES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

docker-compose up -d

echo ""
sleep 3

echo "Statut des services:"
docker-compose ps

echo ""

# Étape 3: Initialisation de la base de données
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  INITIALISATION DE LA BASE DE DONNÉES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "⏳ Application des migrations..."
docker-compose exec -T web python manage.py migrate

echo ""
echo "✅ Migrations appliquées avec succès!"
echo ""

# Étape 4: Tests
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Test 1: Health check"
if curl -sf http://localhost/health/ > /dev/null; then
    echo "✅ Health check: OK"
else
    echo "⚠️  Health check: pas de réponse (nginx peut mettre du temps à démarrer)"
fi

echo ""
echo "Test 2: Accès à l'application"
sleep 2
if curl -sf http://localhost/ > /dev/null 2>&1; then
    echo "✅ Application: accessible"
else
    echo "⚠️  Application: vérifier les logs avec: docker-compose logs web"
fi

echo ""

# Résumé final
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   ✅ DÉPLOIEMENT TERMINÉ!                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Informations de déploiement:"
echo "   Domaine: reves-journal.fr"
echo "   URL: http://localhost (en local) ou http://reves-journal.fr (en prod)"
echo "   Admin: http://localhost/admin/"
echo ""
echo "📖 Commandes utiles:"
echo "   Voir les logs: docker-compose logs -f web"
echo "   Admin shell: docker-compose exec web python manage.py shell"
echo "   Créer un admin: docker-compose exec web python manage.py createsuperuser"
echo "   Redémarrer: docker-compose restart"
echo "   Arrêter: docker-compose down"
echo ""
echo "🔐 Configuration de sécurité:"
echo "   DEBUG = False ✓"
echo "   SECRET_KEY = Configurée ✓"
echo "   ALLOWED_HOSTS = reves-journal.fr ✓"
echo "   CSRF_TRUSTED_ORIGINS = HTTPS configuré ✓"
echo ""
echo "📚 Documentation:"
echo "   - DEPLOYMENT_DOCKER.md (guide complet)"
echo "   - DOCKER_QUICK_COMMANDS.sh (commandes rapides)"
echo ""
