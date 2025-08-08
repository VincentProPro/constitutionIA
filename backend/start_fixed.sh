#!/bin/bash
# Script de démarrage avec RAG pré-initialisé

cd /opt/constitutionia/backend
source rag_env/bin/activate

echo "🚀 Démarrage avec RAG pré-initialisé..."

# Tuer les processus existants
pkill -f "python -m uvicorn" || true
sleep 2

# Initialiser le RAG d'abord
echo "📚 Initialisation du RAG..."
python init_rag_server.py

if [ $? -eq 0 ]; then
    echo "✅ RAG initialisé, démarrage du serveur..."
    # Démarrer le serveur
    nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
    SERVER_PID=$!
    echo "✅ Serveur démarré avec PID: $SERVER_PID"
    echo "📋 Logs: tail -f server.log"
    echo "🔍 Status: curl http://localhost:8000/health"
else
    echo "❌ Échec de l'initialisation du RAG"
    exit 1
fi 