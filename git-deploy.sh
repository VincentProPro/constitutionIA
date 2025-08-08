#!/bin/bash

# Déploiement simple via Git
# Usage: ./git-deploy.sh IP UTILISATEUR CLE_SSH

echo "🚀 Déploiement ConstitutionIA via Git..."

if [ $# -ne 3 ]; then
    echo "❌ Usage: $0 IP UTILISATEUR CLE_SSH"
    echo "Exemple: $0 192.168.1.100 ubuntu ~/.ssh/id_rsa"
    exit 1
fi

IP=$1
USER=$2
SSH_KEY=$3

echo "📡 Configuration du serveur $USER@$IP..."

# 1. Configurer le serveur
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$USER@$IP" << 'EOF'
    # Créer le dossier
    sudo mkdir -p /opt/constitutionia
    sudo chown $USER:$USER /opt/constitutionia
    cd /opt/constitutionia
    
    # Installer les prérequis
    sudo apt update
    sudo apt install -y git docker.io docker-compose
    
    # Cloner le repository
    if [ ! -d ".git" ]; then
        git clone https://github.com/VincentProPro/constitutionIA.git .
    fi
    
    # Créer le script de déploiement
    cat > deploy.sh << 'SCRIPT'
#!/bin/bash
echo "🔄 Déploiement en cours..."
cd /opt/constitutionia

# Pull des dernières modifications
git pull origin main

# Configurer .env si nécessaire
if [ -f ".env.example" ] && [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  Configurez le fichier .env avec votre clé API OpenAI"
fi

# Redémarrer les services
docker-compose -f docker-compose-ubuntu.yml down
docker-compose -f docker-compose-ubuntu.yml build --no-cache
docker-compose -f docker-compose-ubuntu.yml up -d

echo "✅ Déploiement terminé!"
echo "🌐 Accès: http://$(hostname -I | awk '{print $1}')"
SCRIPT

    chmod +x deploy.sh
    
    # Premier déploiement
    ./deploy.sh
EOF

echo "✅ Configuration terminée!"
echo "📋 Commandes utiles:"
echo "   - Déployer: ssh -i $SSH_KEY $USER@$IP 'cd /opt/constitutionia && ./deploy.sh'"
echo "   - Voir les logs: ssh -i $SSH_KEY $USER@$IP 'cd /opt/constitutionia && docker-compose -f docker-compose-ubuntu.yml logs -f'"
echo "   - Statut: ssh -i $SSH_KEY $USER@$IP 'cd /opt/constitutionia && docker-compose -f docker-compose-ubuntu.yml ps'" 