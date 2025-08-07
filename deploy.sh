#!/bin/bash

# Déploiement ultra-simple ConstitutionIA
# Usage: ./deploy.sh IP UTILISATEUR CLE_SSH

echo "🚀 Déploiement ConstitutionIA..."

# Vérifier les arguments
if [ $# -ne 3 ]; then
    echo "❌ Usage: $0 IP UTILISATEUR CLE_SSH"
    echo "Exemple: $0 192.168.1.100 ubuntu ~/.ssh/id_rsa"
    exit 1
fi

IP=$1
USER=$2
SSH_KEY=$3

echo "📡 Connexion à $USER@$IP..."

# Créer le dossier sur le serveur
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$USER@$IP" "sudo mkdir -p /opt/constitutionia && sudo chown $USER:$USER /opt/constitutionia"

# Copier les fichiers
echo "📤 Copie des fichiers..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no -r backend/ frontend/ docker-compose-ubuntu.yml nginx-ubuntu.conf nginx/ constitutionia.service ufw-rules.txt backup-ubuntu.sh cron-jobs.txt .env "$USER@$IP:/opt/constitutionia/"

# Installer et démarrer
echo "🐳 Installation et démarrage..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$USER@$IP" << 'EOF'
    cd /opt/constitutionia
    
    # Installer Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    
    # Installer Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    # Firewall
    sudo ufw --force enable
    sudo ufw allow ssh
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow 8000/tcp
    
    # Service
    sudo cp constitutionia.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable constitutionia
    
    # Cron
    chmod +x backup-ubuntu.sh
    (crontab -l 2>/dev/null; cat cron-jobs.txt) | crontab -
    
    # Démarrer
    docker-compose -f docker-compose-ubuntu.yml down
    docker-compose -f docker-compose-ubuntu.yml build --no-cache
    docker-compose -f docker-compose-ubuntu.yml up -d
    
    sleep 30
    
    echo "📊 Statut:"
    docker-compose -f docker-compose-ubuntu.yml ps
    
    echo "🌐 Test:"
    curl -f http://localhost/health || echo "❌ Health check échoué"
EOF

echo "✅ Terminé!"
echo "🌐 Accès: http://$IP"
echo "📚 API: http://$IP:8000/docs" 