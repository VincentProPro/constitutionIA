#!/bin/bash

echo "🔄 Remplacement des images du slider par les versions optimisées..."

cd frontend/public/images/slider

# Sauvegarder les originaux
echo "📦 Sauvegarde des images originales..."
mkdir -p original
cp slide-*.jpg slide-*.png original/ 2>/dev/null || true

# Remplacer par les versions optimisées
echo "🔄 Remplacement des images..."
for optimized in *-optimized.jpg; do
    if [ -f "$optimized" ]; then
        # Extraire le nom de base
        base_name=$(echo "$optimized" | sed 's/-optimized\.jpg$/.jpg/')
        
        # Remplacer l'original par l'optimisé
        echo "   📸 $base_name → $optimized"
        mv "$optimized" "$base_name"
    fi
done

echo "✅ Remplacement terminé !"
echo "📁 Images originales sauvegardées dans: original/"

# Afficher les nouvelles tailles
echo ""
echo "📊 Nouvelles tailles des images:"
ls -lh slide-*.jpg | grep -E "(slide-[0-9]+\.jpg)"

echo ""
echo "🎯 Prochaines étapes:"
echo "   1. Tester le chargement de la page"
echo "   2. Vérifier les performances avec Lighthouse"
echo "   3. Déployer sur le serveur" 