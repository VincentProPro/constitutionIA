#!/bin/bash

echo "🔥 Configuration du firewall Ubuntu (UFW)..."

# Activer UFW
sudo ufw --force enable

# Autoriser SSH (important!)
sudo ufw allow ssh

# Autoriser HTTP et HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Autoriser le port de l'API (optionnel, pour accès direct)
sudo ufw allow 8000/tcp

# Vérifier le statut
echo "📊 Statut du firewall:"
sudo ufw status

echo "✅ Firewall configuré!"
echo "🌐 Ports ouverts:"
echo "   - 22 (SSH)"
echo "   - 80 (HTTP)"
echo "   - 443 (HTTPS)"
echo "   - 8000 (API - optionnel)" 