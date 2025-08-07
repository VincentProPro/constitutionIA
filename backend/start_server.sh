#!/bin/bash

# Script pour démarrer le serveur ConstitutionIA avec l'environnement virtuel

echo "🚀 Démarrage de ConstitutionIA..."

# Activer l'environnement virtuel
source venv/bin/activate

# Vérifier que l'environnement virtuel est activé
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Environnement virtuel activé: $VIRTUAL_ENV"
else
    echo "❌ Erreur: Environnement virtuel non activé"
    exit 1
fi

# Vérifier les dépendances
echo "📦 Vérification des dépendances..."
python3 -c "import fastapi, openai, sqlalchemy; print('✅ Toutes les dépendances sont installées')"

# Démarrer le serveur
echo "🌐 Démarrage du serveur FastAPI..."
echo "📡 Le serveur sera accessible sur: http://localhost:8000"
echo "📚 Documentation API: http://localhost:8000/docs"
echo ""
echo "Pour arrêter le serveur, appuyez sur Ctrl+C"
echo ""

uvicorn main:app --reload --host 0.0.0.0 --port 8000 