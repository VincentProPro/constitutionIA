#!/bin/bash

echo "🔧 Configuration du projet ConstitutionIA sur Ubuntu..."

# Vérifier la clé API OpenAI
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ La variable OPENAI_API_KEY n'est pas définie"
    echo "Exportez-la avec: export OPENAI_API_KEY='votre_clé_api'"
    exit 1
fi

# Créer le fichier .env
echo "📝 Création du fichier .env..."
cat > .env << EOF
OPENAI_API_KEY=$OPENAI_API_KEY
DATABASE_URL=sqlite:///./constitutionia.db
HOST=0.0.0.0
PORT=8000
ENABLE_MONITORING=true
EOF

# Créer les dossiers nécessaires
echo "📁 Création des dossiers..."
mkdir -p backend/Fichier
mkdir -p logs
mkdir -p ssl

# Donner les bonnes permissions
echo "🔐 Configuration des permissions..."
sudo chown -R $USER:$USER .
chmod +x deploy.sh
chmod +x deploy_ubuntu.sh

# Copier les fichiers PDF existants (si présents)
if [ -d "backend/Fichier" ] && [ "$(ls -A backend/Fichier)" ]; then
    echo "📄 Fichiers PDF trouvés, ils seront inclus dans le déploiement"
else
    echo "⚠️  Aucun fichier PDF trouvé dans backend/Fichier"
    echo "   Ajoutez vos constitutions PDF dans ce dossier"
fi

echo "✅ Configuration terminée!"
echo "🚀 Vous pouvez maintenant exécuter: ./deploy.sh" 