#!/bin/bash

# Déploiement rapide des mises à jour (services installés directement)
# Usage: ./deploy-update-direct.sh IP_SERVEUR UTILISATEUR CHEMIN_CLE_SSH

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

if [ $# -ne 3 ]; then
    echo -e "${RED}❌ Usage: $0 IP_SERVEUR UTILISATEUR CHEMIN_CLE_SSH${NC}"
    echo -e "${YELLOW}Exemple: $0 192.168.1.100 ubuntu ~/.ssh/id_rsa${NC}"
    exit 1
fi

SERVER_IP=$1
SERVER_USER=$2
SSH_KEY=$3

echo -e "${BLUE}🚀 Mise à jour ConstitutionIA sur $SERVER_USER@$SERVER_IP${NC}"

# Test de connexion
echo -e "${BLUE}🔍 Test de connexion...${NC}"
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "echo '✅ Connexion SSH réussie'" 2>/dev/null; then
    echo -e "${RED}❌ Impossible de se connecter au serveur${NC}"
    echo -e "${YELLOW}Vérifiez :${NC}"
    echo -e "   - L'IP du serveur: $SERVER_IP"
    echo -e "   - L'utilisateur: $SERVER_USER"
    echo -e "   - Le chemin de la clé SSH: $SSH_KEY"
    echo -e "   - La clé SSH est autorisée sur le serveur"
    exit 1
fi

echo -e "${GREEN}✅ Connexion réussie !${NC}"

# Mise à jour sur le serveur
echo -e "${BLUE}🔄 Mise à jour en cours...${NC}"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
    cd /opt/constitutionia
    
    echo "📥 Récupération des dernières modifications..."
    git pull origin main
    
    echo "🔧 Installation des dépendances frontend..."
    cd frontend
    npm install
    
    echo "🔧 Installation des dépendances backend..."
    cd ../backend
    pip install -r requirements.txt
    
    echo "🔄 Redémarrage des services..."
    sudo systemctl restart constitutionia-backend
    sudo systemctl restart constitutionia-frontend
    sudo systemctl restart nginx
    
    echo "✅ Mise à jour terminée !"
    echo "🌐 Application accessible sur: http://$(hostname -I | awk '{print $1}')"
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Mise à jour réussie !${NC}"
    echo -e "${BLUE}📋 Accès :${NC}"
    echo -e "   - Frontend: http://$SERVER_IP"
    echo -e "   - API: http://$SERVER_IP:8000"
    echo -e "   - Documentation: http://$SERVER_IP:8000/docs"
    echo -e "   - Health check: http://$SERVER_IP/health"
    echo -e "${BLUE}📊 Vérification des services :${NC}"
    echo -e "   - Statut: ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP 'sudo systemctl status constitutionia-backend constitutionia-frontend nginx'"
    echo -e "   - Logs: ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP 'sudo journalctl -u constitutionia-backend -f'"
else
    echo -e "${RED}❌ Erreur lors de la mise à jour${NC}"
    exit 1
fi 