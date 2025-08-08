#!/bin/bash
# Script de démarrage permanent avec RAG initialisé

cd /opt/constitutionia/backend
source rag_env/bin/activate

echo "🚀 Démarrage permanent du serveur avec RAG..."

# Tuer les processus existants
pkill -f "python -m uvicorn" || true
sleep 2

# Démarrer avec le script RAG
nohup python start_with_rag.py > server.log 2>&1 &

echo "✅ Serveur démarré en arrière-plan"
echo "📋 Logs: tail -f server.log"
echo "🔍 Status: curl http://localhost:8000/health" 