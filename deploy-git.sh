#!/bin/bash

# Déploiement automatique via Git
# Usage: ./deploy-git.sh IP_SERVEUR UTILISATEUR CHEMIN_CLE_SSH

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

echo -e "${BLUE}🚀 Configuration du déploiement Git sur $SERVER_USER@$SERVER_IP${NC}"

# 1. Créer le dossier de déploiement sur le serveur
echo -e "${BLUE}📁 Configuration du serveur...${NC}"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
    # Créer le dossier de déploiement
    sudo mkdir -p /opt/constitutionia
    sudo chown $USER:$USER /opt/constitutionia
    cd /opt/constitutionia
    
    # Installer Git si pas présent
    sudo apt update
    sudo apt install -y git docker.io docker-compose
    
    # Configurer Git
    git config --global user.name "ConstitutionIA Deploy"
    git config --global user.email "deploy@constitutionia.gn"
    
    # Cloner le repository (si pas déjà fait)
    if [ ! -d ".git" ]; then
        git clone https://github.com/VincentProPro/constitutionIA.git .
    fi
    
    # Créer le script de déploiement automatique
    cat > deploy-auto.sh << 'SCRIPT'
#!/bin/bash
echo "🔄 Déploiement automatique en cours..."
cd /opt/constitutionia

# Pull des dernières modifications
git pull origin main

# Copier le fichier .env si il existe
if [ -f ".env.example" ] && [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  Veuillez configurer le fichier .env avec votre clé API OpenAI"
fi

# Redémarrer les services
docker-compose -f docker-compose-ubuntu.yml down
docker-compose -f docker-compose-ubuntu.yml build --no-cache
docker-compose -f docker-compose-ubuntu.yml up -d

echo "✅ Déploiement terminé!"
echo "🌐 Accès: http://$(hostname -I | awk '{print $1}')"
SCRIPT

    chmod +x deploy-auto.sh
    
    # Configurer le service systemd pour le déploiement automatique
    sudo tee /etc/systemd/system/constitutionia-deploy.service > /dev/null << 'SERVICE'
[Unit]
Description=ConstitutionIA Auto Deploy
After=network.target

[Service]
Type=oneshot
User=ubuntu
WorkingDirectory=/opt/constitutionia
ExecStart=/opt/constitutionia/deploy-auto.sh
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

    sudo systemctl daemon-reload
    sudo systemctl enable constitutionia-deploy
EOF

# 2. Configurer Git hooks sur votre machine locale
echo -e "${BLUE}🔧 Configuration des Git hooks locaux...${NC}"

# Créer le hook post-push
mkdir -p .git/hooks
cat > .git/hooks/post-push << 'HOOK'
#!/bin/bash
echo "🚀 Déploiement automatique déclenché..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "cd /opt/constitutionia && ./deploy-auto.sh"
HOOK

chmod +x .git/hooks/post-push

# 3. Créer un alias pour push + déploy
echo -e "${BLUE}📝 Configuration des alias Git...${NC}"
git config alias.deploy '!f() { git push origin main && ssh -i "'$SSH_KEY'" -o StrictHostKeyChecking=no "'$SERVER_USER@$SERVER_IP'" "cd /opt/constitutionia && ./deploy-auto.sh"; }; f'

echo -e "${GREEN}✅ Configuration terminée!${NC}"
echo -e "${BLUE}📋 Utilisation:${NC}"
echo -e "   - Déployer: git deploy"
echo -e "   - Push + déploy: git push origin main && ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP 'cd /opt/constitutionia && ./deploy-auto.sh'"
echo -e "   - Déployer manuellement: ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP 'cd /opt/constitutionia && ./deploy-auto.sh'" 