# Dossier Slider Images

Ce dossier contient les images utilisées pour le slider de la page d'accueil.

## Formats supportés

✅ **PNG** (.png) - Format recommandé pour les images avec transparence
✅ **JPG** (.jpg) - Format recommandé pour les photos et images complexes

## Structure recommandée

```
slider/
├── slide-1.jpg          # Image pour ConstitutionIA
├── slide-2.png          # Image pour Copilot IA  
├── slide-3.jpg          # Image pour Recherche Avancée
└── README.md            # Ce fichier
```

## Spécifications des images

- **Formats supportés** : JPG (.jpg) et PNG (.png)
- **Dimensions recommandées** : 1920x1080px (16:9)
- **Taille maximale** : 2MB par image
- **Optimisation** : Compresser les images pour le web

## Utilisation dans le code

```javascript
// Dans App.js ou HomePage.tsx
const sliderData = [
  {
    id: 1,
    title: "ConstitutionIA",
    image: "/images/slider/slide-1.jpg", // ou .png
    // ...
  }
];
```

## Thèmes des images

1. **slide-1.jpg/png** - IA qui analyse des documents/constitutions
2. **slide-2.jpg/png** - Interface d'assistant IA/Chat
3. **slide-3.jpg/png** - Recherche et filtrage de documents

## Avantages des formats

### PNG (.png)
- ✅ Support de la transparence
- ✅ Qualité sans perte
- ✅ Idéal pour les graphiques et logos
- ❌ Fichiers plus volumineux

### JPG (.jpg)
- ✅ Compression efficace
- ✅ Idéal pour les photos
- ✅ Chargement plus rapide
- ❌ Pas de transparence
- ❌ Perte de qualité

## Notes importantes

- Les images doivent être optimisées pour le web
- Utiliser des images libres de droits ou sous licence appropriée
- Tester la lisibilité du texte blanc sur les images
- Ajouter un overlay sombre si nécessaire pour la lisibilité
- Le navigateur supporte automatiquement les deux formats 