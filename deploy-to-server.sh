#!/bin/bash

# Script de déploiement ConstitutionIA sur serveur Ubuntu
# Usage: ./deploy-to-server.sh IP_SERVEUR UTILISATEUR CHEMIN_CLE

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Vérification des arguments
if [ $# -ne 3 ]; then
    echo -e "${RED}❌ Usage: $0 IP_SERVEUR UTILISATEUR CHEMIN_CLE${NC}"
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

# Vérifier que le fichier .env existe
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Fichier .env non trouvé. Création à partir de env.example...${NC}"
    if [ -f "env.example" ]; then
        cp env.example .env
        echo -e "${YELLOW}⚠️  Veuillez configurer votre fichier .env avant de continuer${NC}"
        echo -e "${YELLOW}   - Ajoutez votre OPENAI_API_KEY${NC}"
        echo -e "${YELLOW}   - Modifiez les autres variables si nécessaire${NC}"
        exit 1
    else
        echo -e "${RED}❌ Fichier env.example non trouvé${NC}"
        exit 1
    fi
fi

# Créer le dossier de déploiement sur le serveur
echo -e "${BLUE}📁 Création du dossier de déploiement...${NC}"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
    sudo mkdir -p /opt/constitutionia
    sudo chown $USER:$USER /opt/constitutionia
    mkdir -p /opt/constitutionia/logs
    mkdir -p /opt/constitutionia/backups
EOF

# Copier les fichiers sur le serveur
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
    UBUNTU_FILES.md \
    .env \
    "$SERVER_USER@$SERVER_IP:/opt/constitutionia/"

# Installer Docker et Docker Compose sur le serveur
echo -e "${BLUE}🐳 Installation de Docker et Docker Compose...${NC}"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
    # Mettre à jour le système
    sudo apt update && sudo apt upgrade -y
    
    # Installer les dépendances
    sudo apt install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release \
        software-properties-common \
        git \
        unzip
    
    # Installer Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    
    # Installer Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    # Redémarrer pour appliquer les changements de groupe
    sudo systemctl enable docker
    sudo systemctl start docker
EOF

# Configurer le firewall
echo -e "${BLUE}🔥 Configuration du firewall...${NC}"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
    cd /opt/constitutionia
    
    # Activer UFW
    sudo ufw --force enable
    
    # Autoriser SSH
    sudo ufw allow ssh
    
    # Autoriser HTTP et HTTPS
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Autoriser l'API (optionnel)
    sudo ufw allow 8000/tcp
    
    # Vérifier le statut
    sudo ufw status
EOF

# Configurer le service systemd
echo -e "${BLUE}⚙️  Configuration du service systemd...${NC}"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
    cd /opt/constitutionia
    
    # Copier le service
    sudo cp constitutionia.service /etc/systemd/system/
    
    # Recharger systemd
    sudo systemctl daemon-reload
    
    # Activer le service
    sudo systemctl enable constitutionia
EOF

# Configurer les tâches cron
echo -e "${BLUE}⏰ Configuration des tâches cron...${NC}"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
    cd /opt/constitutionia
    
    # Rendre le script de sauvegarde exécutable
    chmod +x backup-ubuntu.sh
    
    # Ajouter les tâches cron
    (crontab -l 2>/dev/null; cat cron-jobs.txt) | crontab -
EOF

# Démarrer l'application
echo -e "${BLUE}🚀 Démarrage de l'application...${NC}"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
    cd /opt/constitutionia
    
    # Construire et démarrer les conteneurs
    docker-compose -f docker-compose-ubuntu.yml down
    docker-compose -f docker-compose-ubuntu.yml build --no-cache
    docker-compose -f docker-compose-ubuntu.yml up -d
    
    # Attendre que les services soient prêts
    sleep 30
    
    # Vérifier le statut
    docker-compose -f docker-compose-ubuntu.yml ps
EOF

# Vérifier que tout fonctionne
echo -e "${BLUE}🔍 Vérification du déploiement...${NC}"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
    cd /opt/constitutionia
    
    # Vérifier les conteneurs
    echo "📊 Statut des conteneurs:"
    docker-compose -f docker-compose-ubuntu.yml ps
    
    # Vérifier les logs
    echo "📝 Logs récents:"
    docker-compose -f docker-compose-ubuntu.yml logs --tail=20
    
    # Test de connectivité
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
echo -e "   - Voir les logs: ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP 'cd /opt/constitutionia && docker-compose -f docker-compose-ubuntu.yml logs -f'"
echo -e "   - Redémarrer: ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP 'cd /opt/constitutionia && docker-compose -f docker-compose-ubuntu.yml restart'"
echo -e "   - Sauvegarde: ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP 'cd /opt/constitutionia && ./backup-ubuntu.sh'" 