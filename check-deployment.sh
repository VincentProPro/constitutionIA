#!/bin/bash

# Script de vérification post-déploiement
# Usage: ./check-deployment.sh

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SERVER_IP="98.85.253.114"
SERVER_USER="ubuntu"
SSH_KEY="/Users/vincentps/Downloads/key/aiconstitution.pem"

echo -e "${BLUE}🔍 Vérification du déploiement ConstitutionIA${NC}"
echo -e "${BLUE}=============================================${NC}"

# Test de connexion SSH
echo -e "\n${BLUE}1. Test de connexion SSH...${NC}"
if ssh -i "$SSH_KEY" -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "echo '✅ Connexion SSH réussie'" 2>/dev/null; then
    echo -e "${GREEN}✅ Connexion SSH OK${NC}"
else
    echo -e "${RED}❌ Échec de la connexion SSH${NC}"
    exit 1
fi

# Vérification des services
echo -e "\n${BLUE}2. Vérification des services...${NC}"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
echo "=== Backend (uvicorn) ==="
if ps aux | grep uvicorn | grep -v grep > /dev/null; then
    echo "✅ Backend en cours d'exécution"
    ps aux | grep uvicorn | grep -v grep
else
    echo "❌ Backend non démarré"
fi

echo -e "\n=== Nginx ==="
if sudo systemctl is-active --quiet nginx; then
    echo "✅ Nginx actif"
    sudo systemctl status nginx --no-pager | head -5
else
    echo "❌ Nginx inactif"
fi

echo -e "\n=== Espace disque ==="
df -h | grep -E "(Filesystem|/dev/)"

echo -e "\n=== Mémoire ==="
free -h
EOF

# Test des endpoints
echo -e "\n${BLUE}3. Test des endpoints...${NC}"

# Test frontend
echo -n "Frontend (http://$SERVER_IP): "
if curl -s -o /dev/null -w "%{http_code}" http://$SERVER_IP | grep -q "200"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ Erreur${NC}"
fi

# Test backend (si accessible)
echo -n "Backend (http://$SERVER_IP:8000): "
if curl -s -o /dev/null -w "%{http_code}" http://$SERVER_IP:8000/health 2>/dev/null | grep -q "200"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${YELLOW}⚠️  Non accessible (normal si proxy Nginx)${NC}"
fi

# Vérification du build frontend
echo -e "\n${BLUE}4. Vérification du build frontend...${NC}"
FRONTEND_JS=$(curl -s http://$SERVER_IP | grep -o "main\.[a-zA-Z0-9]*\.js" | head -1)
if [ ! -z "$FRONTEND_JS" ]; then
    echo -e "${GREEN}✅ Fichier JS détecté: $FRONTEND_JS${NC}"
else
    echo -e "${RED}❌ Fichier JS non trouvé${NC}"
fi

# Vérification des logs récents
echo -e "\n${BLUE}5. Logs récents du backend...${NC}"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "tail -5 /opt/constitutionia/backend/backend.log 2>/dev/null || echo 'Aucun log disponible'"

echo -e "\n${GREEN}✅ Vérification terminée !${NC}"
echo -e "${BLUE}🌐 Application accessible sur: http://$SERVER_IP${NC}" 