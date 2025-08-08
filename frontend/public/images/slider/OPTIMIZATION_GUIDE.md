# Guide d'Optimisation des Images du Slider

## 🚨 Problème actuel
Les images du slider sont trop volumineuses :
- `slide-7.jpg` : 6.1MB
- `slide-2.jpg` : 12MB
- `slide-4.jpg` : 12MB

## 🎯 Objectifs d'optimisation
- **Taille cible** : < 500KB par image
- **Format** : WebP (moderne) ou JPG optimisé
- **Dimensions** : 1920x1080px max
- **Qualité** : 80-85% (bon compromis)

## 🛠️ Solutions

### Option 1 : Optimisation en ligne (Recommandée)
1. **TinyPNG** : https://tinypng.com/
2. **Squoosh** : https://squoosh.app/
3. **Compressor.io** : https://compressor.io/

### Option 2 : Script d'optimisation local
```bash
# Installer ImageOptim (Mac)
brew install --cask imageoptim

# Ou utiliser sips (Mac natif)
sips -Z 1920 -s format jpeg --setProperty format jpeg --setProperty quality 0.8 slide-7.jpg --out slide-7-optimized.jpg
```

### Option 3 : Conversion en WebP
```bash
# Installer cwebp
brew install webp

# Convertir en WebP
cwebp -q 80 slide-7.jpg -o slide-7.webp
```

## 📋 Actions recommandées

### Phase 1 : Optimisation immédiate
1. **slide-7.jpg** → Optimiser à < 500KB
2. **slide-2.jpg** → Optimiser à < 500KB  
3. **slide-4.jpg** → Optimiser à < 500KB
4. **slide-5.jpg** → Déjà OK (128KB)

### Phase 2 : Amélioration du code
1. **Lazy loading** pour les images
2. **Responsive images** avec srcset
3. **Preload** des images critiques
4. **Compression progressive**

### Phase 3 : Optimisation avancée
1. **WebP** avec fallback JPG
2. **Service Worker** pour cache
3. **CDN** pour les images
4. **Compression automatique**

## 🔧 Code d'amélioration

### Lazy Loading
```jsx
<img 
  src={slide.image} 
  loading="lazy"
  alt={slide.title}
  className="w-full h-full object-cover"
/>
```

### Responsive Images
```jsx
<picture>
  <source srcSet={`${slide.image}.webp`} type="image/webp" />
  <source srcSet={slide.image} type="image/jpeg" />
  <img src={slide.image} alt={slide.title} />
</picture>
```

## 📊 Métriques cibles
- **Temps de chargement** : < 2s
- **Taille totale slider** : < 2MB
- **Performance Lighthouse** : > 90
- **Core Web Vitals** : Tous verts

## 🎨 Conseils visuels
- **Overlay sombre** pour la lisibilité du texte
- **Contraste** suffisant pour l'accessibilité
- **Focal point** centré sur le contenu important
- **Cohérence** visuelle entre les slides 