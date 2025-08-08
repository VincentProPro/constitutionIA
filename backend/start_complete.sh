#!/bin/bash
# Script de démarrage complet avec RAG et serveur

cd /opt/constitutionia/backend
source rag_env/bin/activate

echo "🚀 Démarrage complet du système..."

# Tuer les processus existants
pkill -f "python -m uvicorn" || true
pkill -f "start_with_rag.py" || true
sleep 2

# Démarrer le RAG en arrière-plan
echo "📚 Démarrage du RAG..."
nohup python start_with_rag.py > rag.log 2>&1 &
RAG_PID=$!

# Attendre que le RAG soit initialisé
echo "⏳ Attente de l'initialisation du RAG..."
sleep 30

# Démarrer le serveur
echo "🌐 Démarrage du serveur..."
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
SERVER_PID=$!

echo "✅ Système démarré!"
echo "📋 RAG PID: $RAG_PID"
echo "📋 Server PID: $SERVER_PID"
echo "📋 Logs RAG: tail -f rag.log"
echo "📋 Logs Server: tail -f server.log"
echo "🔍 Status: curl http://localhost:8000/health" 