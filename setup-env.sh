#!/bin/bash

# Script de configuration du fichier .env
# Usage: ./setup-env.sh

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔧 Configuration du fichier .env${NC}"

# Vérifier si le fichier .env existe
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        echo -e "${YELLOW}📝 Création du fichier .env à partir de env.example...${NC}"
        cp env.example .env
    else
        echo -e "${RED}❌ Fichier env.example non trouvé${NC}"
        exit 1
    fi
fi

echo -e "${YELLOW}⚠️  IMPORTANT: Vous devez configurer votre clé API OpenAI${NC}"
echo -e "${BLUE}📝 Éditez le fichier .env et ajoutez votre OPENAI_API_KEY${NC}"
echo -e "${BLUE}   Exemple: OPENAI_API_KEY=sk-your-actual-api-key-here${NC}"

# Ouvrir le fichier .env pour édition
if command -v nano &> /dev/null; then
    nano .env
elif command -v vim &> /dev/null; then
    vim .env
elif command -v vi &> /dev/null; then
    vi .env
else
    echo -e "${YELLOW}⚠️  Éditeur non trouvé. Veuillez éditer le fichier .env manuellement${NC}"
    echo -e "${BLUE}   Fichier: $(pwd)/.env${NC}"
fi

# Vérifier que la clé API est configurée
if grep -q "OPENAI_API_KEY=sk-" .env; then
    echo -e "${GREEN}✅ Clé API OpenAI configurée${NC}"
else
    echo -e "${RED}❌ Clé API OpenAI non configurée ou invalide${NC}"
    echo -e "${YELLOW}   Veuillez ajouter votre clé API dans le fichier .env${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Configuration terminée!${NC}"
echo -e "${BLUE}🚀 Prêt pour le déploiement${NC}" 