#!/bin/bash

echo "📊 Monitoring ConstitutionIA sur Ubuntu..."

# Vérifier les conteneurs Docker
echo "🐳 Statut des conteneurs:"
docker-compose ps

# Vérifier l'utilisation des ressources
echo "💾 Utilisation des ressources:"
docker stats --no-stream

# Vérifier les logs récents
echo "📝 Logs récents du backend:"
docker-compose logs --tail=20 backend

echo "📝 Logs récents du frontend:"
docker-compose logs --tail=10 frontend

# Vérifier l'espace disque
echo "💿 Espace disque:"
df -h

# Vérifier la mémoire
echo "🧠 Utilisation mémoire:"
free -h

# Test de connectivité
echo "🌐 Test de connectivité:"
curl -s -o /dev/null -w "Frontend: %{http_code}\n" http://localhost
curl -s -o /dev/null -w "Backend API: %{http_code}\n" http://localhost:8000/docs

echo "✅ Monitoring terminé!" 