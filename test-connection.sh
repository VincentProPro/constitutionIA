#!/bin/bash

# Script de test de connexion SSH
# Usage: ./test-connection.sh IP_SERVEUR UTILISATEUR CHEMIN_CLE

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

if [ $# -ne 3 ]; then
    echo -e "${RED}❌ Usage: $0 IP_SERVEUR UTILISATEUR CHEMIN_CLE${NC}"
    echo -e "${YELLOW}Exemple: $0 192.168.1.100 ubuntu ~/.ssh/id_rsa${NC}"
    exit 1
fi

SERVER_IP=$1
SERVER_USER=$2
SSH_KEY=$3

echo -e "${BLUE}🔍 Test de connexion à $SERVER_USER@$SERVER_IP${NC}"

# Vérifier que la clé SSH existe
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}❌ Clé SSH non trouvée: $SSH_KEY${NC}"
    exit 1
fi

# Test de connexion SSH
echo -e "${BLUE}📡 Test de connexion SSH...${NC}"
if ssh -i "$SSH_KEY" -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "echo '✅ Connexion SSH réussie'" 2>/dev/null; then
    echo -e "${GREEN}✅ Connexion SSH réussie!${NC}"
else
    echo -e "${RED}❌ Échec de la connexion SSH${NC}"
    echo -e "${YELLOW}Vérifiez:${NC}"
    echo -e "   - L'IP du serveur est correcte"
    echo -e "   - Le nom d'utilisateur est correct"
    echo -e "   - La clé SSH est valide"
    echo -e "   - Le serveur est accessible"
    exit 1
fi

# Vérifier les prérequis sur le serveur
echo -e "${BLUE}🔧 Vérification des prérequis...${NC}"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
    echo "📊 Informations système:"
    echo "   - OS: $(lsb_release -d | cut -f2)"
    echo "   - Kernel: $(uname -r)"
    echo "   - Architecture: $(uname -m)"
    echo "   - Mémoire: $(free -h | grep Mem | awk '{print $2}')"
    echo "   - Disque: $(df -h / | tail -1 | awk '{print $4}') libre"
    
    echo ""
    echo "🐳 Docker:"
    if command -v docker &> /dev/null; then
        echo "   ✅ Docker installé: $(docker --version)"
    else
        echo "   ❌ Docker non installé"
    fi
    
    echo ""
    echo "📦 Docker Compose:"
    if command -v docker-compose &> /dev/null; then
        echo "   ✅ Docker Compose installé: $(docker-compose --version)"
    else
        echo "   ❌ Docker Compose non installé"
    fi
    
    echo ""
    echo "🔥 UFW:"
    if command -v ufw &> /dev/null; then
        echo "   ✅ UFW installé"
        echo "   - Statut: $(sudo ufw status | head -1)"
    else
        echo "   ❌ UFW non installé"
    fi
EOF

echo -e "${GREEN}✅ Test de connexion terminé!${NC}"
echo -e "${BLUE}🚀 Prêt pour le déploiement avec:${NC}"
echo -e "   ./deploy-to-server.sh $SERVER_IP $SERVER_USER $SSH_KEY" 