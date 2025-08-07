#!/bin/bash

# Script de déploiement simplifié ConstitutionIA
# Usage: ./deploy-simple.sh IP_SERVEUR UTILISATEUR CHEMIN_CLE_PRIVEE

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

if [ $# -ne 3 ]; then
    echo -e "${RED}❌ Usage: $0 IP_SERVEUR UTILISATEUR CHEMIN_CLE_PRIVEE${NC}"
    echo -e "${YELLOW}Exemple: $0 192.168.1.100 ubuntu ~/.ssh/id_rsa${NC}"
    exit 1
fi

SERVER_IP=$1
SERVER_USER=$2
SSH_KEY=$3

echo -e "${BLUE}🚀 Déploiement ConstitutionIA sur $SERVER_USER@$SERVER_IP${NC}"

# Vérifier que la clé SSH existe
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}❌ Clé SSH non trouvée: $SSH_KEY${NC}"
    exit 1
fi

# Vérifier que le fichier .env existe et est configuré
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Fichier .env non trouvé. Lancement de la configuration...${NC}"
    ./setup-env.sh
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Configuration échouée${NC}"
        exit 1
    fi
fi

# Test de connexion SSH
echo -e "${BLUE}🔍 Test de connexion SSH...${NC}"
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "echo '✅ Connexion SSH réussie'" 2>/dev/null; then
    echo -e "${RED}❌ Échec de la connexion SSH${NC}"
    echo -e "${YELLOW}Vérifiez:${NC}"
    echo -e "   - L'IP du serveur: $SERVER_IP"
    echo -e "   - L'utilisateur: $SERVER_USER"
    echo -e "   - La clé SSH: $SSH_KEY"
    exit 1
fi

echo -e "${GREEN}✅ Connexion SSH réussie!${NC}"

# Créer le dossier sur le serveur
echo -e "${BLUE}📁 Création du dossier de déploiement...${NC}"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
    sudo mkdir -p /opt/constitutionia
    sudo chown $USER:$USER /opt/constitutionia
    mkdir -p /opt/constitutionia/logs
    mkdir -p /opt/constitutionia/backups
EOF

# Copier les fichiers
echo -e "${BLUE}📤 Copie des fichiers sur le serveur...${NC}"
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no -r \
    backend/ \
    frontend/ \
    docker-compose-ubuntu.yml \
    nginx-ubuntu.conf \
    nginx/ \
    constitutionia.service \
    ufw-rules.txt \
    backup-ubuntu.sh \
    cron-jobs.txt \
    .env \
    "$SERVER_USER@$SERVER_IP:/opt/constitutionia/"

# Installer Docker et configurer le serveur
echo -e "${BLUE}🐳 Installation et configuration du serveur...${NC}"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
    cd /opt/constitutionia
    
    # Mettre à jour le système
    sudo apt update && sudo apt upgrade -y
    
    # Installer Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    
    # Installer Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    # Configurer le firewall
    sudo ufw --force enable
    sudo ufw allow ssh
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow 8000/tcp
    
    # Configurer le service systemd
    sudo cp constitutionia.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable constitutionia
    
    # Configurer les tâches cron
    chmod +x backup-ubuntu.sh
    (crontab -l 2>/dev/null; cat cron-jobs.txt) | crontab -
    
    # Démarrer l'application
    docker-compose -f docker-compose-ubuntu.yml down
    docker-compose -f docker-compose-ubuntu.yml build --no-cache
    docker-compose -f docker-compose-ubuntu.yml up -d
    
    # Attendre que les services soient prêts
    sleep 30
    
    # Vérifier le statut
    echo "📊 Statut des conteneurs:"
    docker-compose -f docker-compose-ubuntu.yml ps
    
    echo "🌐 Test de connectivité:"
    curl -f http://localhost/health || echo "❌ Health check échoué"
    curl -f http://localhost:8000/docs || echo "❌ API docs non accessible"
EOF

echo -e "${GREEN}✅ Déploiement terminé!${NC}"
echo -e "${BLUE}🌐 URLs d'accès:${NC}"
echo -e "   - Frontend: http://$SERVER_IP"
echo -e "   - API: http://$SERVER_IP:8000"
echo -e "   - Documentation: http://$SERVER_IP:8000/docs"
echo -e "   - Health check: http://$SERVER_IP/health"

echo -e "${YELLOW}📋 Commandes utiles:${NC}"
echo -e "   - Logs: ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP 'cd /opt/constitutionia && docker-compose -f docker-compose-ubuntu.yml logs -f'"
echo -e "   - Redémarrer: ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP 'cd /opt/constitutionia && docker-compose -f docker-compose-ubuntu.yml restart'"
echo -e "   - Sauvegarde: ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP 'cd /opt/constitutionia && ./backup-ubuntu.sh'" 