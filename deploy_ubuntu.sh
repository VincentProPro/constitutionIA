#!/bin/bash

echo "🚀 Déploiement ConstitutionIA sur Ubuntu..."

# Vérifier que c'est bien Ubuntu
if ! grep -q "Ubuntu" /etc/os-release; then
    echo "❌ Ce script est conçu pour Ubuntu uniquement"
    exit 1
fi

# Mettre à jour le système
echo "📦 Mise à jour du système..."
sudo apt update && sudo apt upgrade -y

# Installer les dépendances système
echo "🔧 Installation des dépendances..."
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
echo "🐳 Installation de Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Installer Docker Compose
echo "📦 Installation de Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Vérifier les installations
echo "✅ Vérification des installations..."
docker --version
docker-compose --version

echo "🎉 Installation terminée! Redémarrez votre session ou exécutez: newgrp docker" 