# 🎯 Système d'Articles Constitutionnels

## 📋 Vue d'ensemble

Le système d'articles constitutionnels permet d'extraire automatiquement et de structurer les articles des constitutions PDF en base de données. Chaque article est indexé, recherchable et lié à sa constitution source.

## 🏗️ Architecture

### Tables de Base de Données

#### Table `articles`
```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY,
    constitution_id INTEGER REFERENCES constitutions(id),
    article_number VARCHAR(50) NOT NULL,  -- "Article 1", "Article 2", etc.
    title VARCHAR(255),                   -- Titre optionnel
    content TEXT NOT NULL,                -- Contenu complet de l'article
    part VARCHAR(100),                    -- "PREMIÈRE PARTIE", "DEUXIÈME PARTIE"
    section VARCHAR(100),                 -- "TITRE I", "TITRE II"
    page_number INTEGER,                  -- Numéro de page (optionnel)
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### Table `metadata`
```sql
CREATE TABLE metadata (
    id INTEGER PRIMARY KEY,
    constitution_id INTEGER REFERENCES constitutions(id),
    key VARCHAR(100) NOT NULL,            -- "last_parsed", "extraction_method"
    value TEXT,                           -- Valeur associée
    created_at TIMESTAMP
);
```

## 🔄 Fonctionnement Automatique

### Upload de Fichier
1. **Upload PDF** → Route `/api/constitutions/upload`
2. **Création Constitution** → Entrée dans table `constitutions`
3. **Extraction Automatique** → Appel `process_uploaded_pdf()`
4. **Parsing Articles** → Extraction avec regex patterns
5. **Sauvegarde DB** → Articles stockés dans table `articles`

### Suppression de Fichier
1. **Suppression PDF** → Route `/api/constitutions/files/{filename}`
2. **Nettoyage Articles** → Appel `delete_pdf_articles()`
3. **Suppression Constitution** → Entrée supprimée de `constitutions`

## 🛠️ Extraction de Texte

### Méthodes d'Extraction (Fallback)
1. **PyPDF2** → Extraction standard
2. **LangChain PyPDFLoader** → Extraction avancée
3. **PyMuPDF (fitz)** → Extraction robuste
4. **Tesseract OCR** → Pour PDFs scannés

### Patterns Regex
```python
patterns = [
    r'(Article\s+\d+[^\n]*)\n((?:[^\n]+\n)+)',           # Article X
    r'(ART\.\s*\d+[^\n]*)\n((?:[^\n]+\n)+)',            # ART. X
    r'(Article\s+\d+\s*:[^\n]*)\n((?:[^\n]+\n)+)',      # Article X :
    r'(Article\s+\d+\s*-[^\n]*)\n((?:[^\n]+\n)+)',      # Article X -
    # ... et plus
]
```

## 📡 API Endpoints

### Récupérer les Articles d'une Constitution
```http
GET /api/constitutions/{constitution_id}/articles
```

**Réponse:**
```json
{
  "constitution": {
    "id": 1,
    "title": "Constitution de Guinée",
    "filename": "constitution.pdf"
  },
  "articles_count": 185,
  "articles": [
    {
      "id": 1,
      "article_number": "Article 1",
      "title": null,
      "content": "La Guinée est une République...",
      "part": "PREMIÈRE PARTIE",
      "section": "TITRE I",
      "page_number": null,
      "created_at": "2024-01-12T10:30:00",
      "updated_at": "2024-01-12T10:30:00"
    }
  ]
}
```

### Rechercher dans les Articles
```http
GET /api/constitutions/articles/search?query=droits&constitution_id=1
```

**Réponse:**
```json
{
  "query": "droits",
  "results_count": 15,
  "results": [
    {
      "id": 7,
      "article_number": "Article 7",
      "title": null,
      "content": "Tous les êtres humains naissent libres et égaux en dignité et en droits...",
      "part": null,
      "section": null,
      "constitution": {
        "id": 1,
        "title": "Constitution de Guinée",
        "filename": "constitution.pdf"
      }
    }
  ]
}
```

## 🚀 Utilisation

### Scripts Disponibles

#### 1. Créer les Tables
```bash
cd backend
source rag_env/bin/activate
python create_tables.py
```

#### 2. Traiter les Fichiers Existants
```bash
python process_existing_files.py
```

#### 3. Démonstration
```bash
python demo_articles.py
```

### Intégration dans le Code

#### Upload Automatique
```python
from app.services.pdf_import import process_uploaded_pdf

# Dans la route d'upload
result = process_uploaded_pdf(db, constitution.id, file_path)
if result['success']:
    print(f"✅ {result['articles_count']} articles extraits")
```

#### Suppression Automatique
```python
from app.services.pdf_import import delete_pdf_articles

# Dans la route de suppression
delete_pdf_articles(db, constitution.id)
```

## 📊 Statistiques Actuelles

- **Constitutions actives**: 2
- **Articles extraits**: 376
- **Méthode d'extraction**: OCR + PyPDF2
- **Patterns regex**: 10 patterns différents

## 🔍 Fonctionnalités Avancées

### Recherche Intelligente
- Recherche dans le contenu des articles
- Recherche par numéro d'article
- Recherche par titre
- Filtrage par constitution

### Structure Hiérarchique
- Détection automatique des parties (PREMIÈRE PARTIE, etc.)
- Détection des sections (TITRE I, TITRE II, etc.)
- Organisation par numéro d'article

### Gestion des Erreurs
- Fallback automatique entre méthodes d'extraction
- Logging détaillé des opérations
- Gestion des doublons
- Validation du contenu

## 🎯 Avantages

1. **Automatisation** → Pas d'intervention manuelle
2. **Précision** → Extraction structurée des articles
3. **Recherche** → API de recherche puissante
4. **Évolutivité** → Support de multiples formats
5. **Robustesse** → Fallbacks et gestion d'erreurs
6. **Intégration** → Compatible avec l'IA existante

## 🔮 Améliorations Futures

- [ ] Détection des numéros de page
- [ ] Extraction des titres d'articles
- [ ] Support des amendements
- [ ] Versioning des articles
- [ ] Export en formats structurés (JSON, XML)
- [ ] Interface de visualisation des articles 