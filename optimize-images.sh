#!/bin/bash

# Script d'optimisation des images du slider
# Usage: ./optimize-images.sh

echo "🖼️  Optimisation des images du slider..."

# Vérifier si sips est disponible (Mac)
if command -v sips &> /dev/null; then
    echo "✅ sips trouvé, optimisation en cours..."
    
    cd frontend/public/images/slider
    
    # Créer un dossier pour les images optimisées
    mkdir -p optimized
    
    # Optimiser les images du slider
    for file in slide-*.jpg slide-*.png; do
        if [ -f "$file" ]; then
            echo "📸 Optimisation de $file..."
            
            # Obtenir l'extension
            extension="${file##*.}"
            filename="${file%.*}"
            
            # Optimiser avec sips
            sips -Z 1920 \
                 -s format jpeg \
                 --setProperty format jpeg \
                 --setProperty quality 0.8 \
                 "$file" \
                 --out "optimized/${filename}-optimized.jpg"
            
            # Afficher la taille avant/après
            original_size=$(stat -f%z "$file")
            optimized_size=$(stat -f%z "optimized/${filename}-optimized.jpg")
            
            echo "   📊 $file: ${original_size} → ${optimized_size} bytes"
        fi
    done
    
    echo "✅ Optimisation terminée !"
    echo "📁 Images optimisées dans: frontend/public/images/slider/optimized/"
    
else
    echo "❌ sips non trouvé (Mac uniquement)"
    echo "💡 Alternatives:"
    echo "   1. TinyPNG: https://tinypng.com/"
    echo "   2. Squoosh: https://squoosh.app/"
    echo "   3. ImageOptim: https://imageoptim.com/"
fi

echo ""
echo "🎯 Prochaines étapes:"
echo "   1. Remplacer les images originales par les optimisées"
echo "   2. Tester le chargement de la page"
echo "   3. Vérifier les performances avec Lighthouse" 