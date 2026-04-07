#!/bin/bash

# Script de vérification avant déploiement Docker
# Usage: bash docker_pre_deployment_check.sh

echo "🔍 Vérification de la configuration de déploiement Docker..."
echo ""

CHECKS_PASSED=0
CHECKS_FAILED=0
WARNINGS=0

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((CHECKS_PASSED++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((CHECKS_FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

# ========== VÉRIFICATIONS ==========

echo "📦 Fichiers Docker:"
if [ -f "Dockerfile" ]; then
    check_pass "Dockerfile existe"
else
    check_fail "Dockerfile MANQUANT"
fi

if [ -f "docker-compose.yml" ]; then
    check_pass "docker-compose.yml existe"
else
    check_fail "docker-compose.yml MANQUANT"
fi

if [ -f "docker/nginx.conf" ]; then
    check_pass "nginx.conf existe"
else
    check_fail "nginx.conf MANQUANT"
fi

if [ -f "docker/supervisord.conf" ]; then
    check_pass "supervisord.conf existe"
else
    check_fail "supervisord.conf MANQUANT"
fi

echo ""
echo "📝 Configuration Django:"

if [ -f ".env.prod" ]; then
    check_pass ".env.prod existe"
    
    # Vérifier les variables critiques
    if grep -q "^DJANGO_DEBUG=False" .env.prod; then
        check_pass "DJANGO_DEBUG = False ✓"
    else
        check_fail "DJANGO_DEBUG n'est pas False ⚠️ CRITIQUE!"
    fi
    
    if grep -q "^DJANGO_SECRET_KEY=" .env.prod; then
        SECRET_KEY=$(grep "^DJANGO_SECRET_KEY=" .env.prod | cut -d'=' -f2)
        if [[ "$SECRET_KEY" == *"your-"* ]] || [[ "$SECRET_KEY" == *"change-this"* ]]; then
            check_fail "DJANGO_SECRET_KEY n'est pas configurée (valeur par défaut)"
        else
            check_pass "DJANGO_SECRET_KEY configurée"
        fi
    else
        check_fail "DJANGO_SECRET_KEY MANQUANTE"
    fi
    
    if grep -q "^DJANGO_ALLOWED_HOSTS=" .env.prod; then
        ALLOWED=$(grep "^DJANGO_ALLOWED_HOSTS=" .env.prod | cut -d'=' -f2)
        if [[ "$ALLOWED" == *"reves-"* ]]; then
            check_warn "DJANGO_ALLOWED_HOSTS configurée (vérifie le domaine)"
        else
            check_fail "DJANGO_ALLOWED_HOSTS semble vide ou invalide"
        fi
    else
        check_fail "DJANGO_ALLOWED_HOSTS MANQUANTE"
    fi
    
else
    check_fail ".env.prod MANQUANT - le déploiement ne fonctionnera pas!"
fi

if [ -f "backend/config/settings.py" ]; then
    if grep -q "whitenoise.middleware.WhiteNoiseMiddleware" backend/config/settings.py; then
        check_pass "WhiteNoise middleware configuré"
    else
        check_warn "WhiteNoise middleware non configuré dans settings.py"
    fi
else
    check_fail "settings.py MANQUANT"
fi

echo ""
echo "🐍 Dépendances Python:"

if [ -f "requirements.txt" ]; then
    check_pass "requirements.txt existe"
    
    if grep -q "^gunicorn" requirements.txt; then
        check_pass "gunicorn listé dans requirements.txt"
    else
        check_fail "gunicorn MANQUANT dans requirements.txt"
    fi
    
    if grep -q "^whitenoise" requirements.txt; then
        check_pass "whitenoise listé dans requirements.txt"
    else
        check_fail "whitenoise MANQUANT dans requirements.txt"
    fi
    
else
    check_fail "requirements.txt MANQUANT"
fi

echo ""
echo "🛠️ Outils système:"

if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version 2>/dev/null | grep -oP '(\d+\.)+\d+' | head -1)
    check_pass "Docker installé (version: $DOCKER_VERSION)"
else
    check_fail "Docker N'EST PAS INSTALLÉ"
fi

if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version 2>/dev/null | grep -oP '(\d+\.)+\d+' | head -1)
    check_pass "Docker Compose installé (version: $COMPOSE_VERSION)"
else
    check_fail "Docker Compose N'EST PAS INSTALLÉ"
fi

echo ""
echo "📁 Structure du projet:"

if [ -d "backend" ]; then
    check_pass "Répertoire backend/ existe"
else
    check_fail "Répertoire backend/ MANQUANT"
fi

if [ -d "backend/reves" ]; then
    check_pass "Répertoire backend/reves/ existe"
else
    check_fail "Répertoire backend/reves/ MANQUANT"
fi

if [ -f "backend/manage.py" ]; then
    check_pass "manage.py existe"
else
    check_fail "manage.py MANQUANT"
fi

echo ""
echo "📊 RÉSUMÉ"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "✓ Vérifications réussies: ${GREEN}$CHECKS_PASSED${NC}"
echo -e "✗ Vérifications échouées: ${RED}$CHECKS_FAILED${NC}"
echo -e "⚠ Avertissements: ${YELLOW}$WARNINGS${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $CHECKS_FAILED -gt 0 ]; then
    echo ""
    echo -e "${RED}❌ DÉPLOIEMENT NON RECOMMANDÉ${NC}"
    echo "Corrige les erreurs marquées en rouge ci-dessus."
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  DÉPLOIEMENT POSSIBLE AVEC PRUDENCE${NC}"
    echo "Vérifie les avertissements avant de continuer."
    exit 0
else
    echo ""
    echo -e "${GREEN}✅ PRÊT POUR LA PRODUCTION!${NC}"
    echo ""
    echo "Commandes suivantes:"
    echo "  1. docker-compose build"
    echo "  2. docker-compose up -d"
    echo "  3. docker-compose exec web python manage.py migrate"
    exit 0
fi
