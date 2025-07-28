# ConstitutionIA - Gestion des Constitutions avec Copilot IA

Application de gestion des constitutions avec intégration d'un agent IA pour faciliter la recherche de documents constitutionnels.

## Fonctionnalités

- **Page d'accueil** : Interface inspirée du site officiel cnt.gov.gn
- **Gestion des constitutions** : Recherche et consultation par année
- **Copilot IA** : Agent intelligent pour la recherche de documents
- **Statuts** : Gestion des phases de développement (2025 en développement)

## Architecture

- **Backend** : FastAPI avec base de données PostgreSQL
- **Frontend** : React (version stable) avec TypeScript
- **IA** : Intégration d'un agent IA pour la recherche sémantique

## Installation

### Prérequis
- Python 3.8+
- Node.js 18+
- PostgreSQL

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm start
```

## Structure du Projet

```
constitutionIA/
├── backend/          # API FastAPI
├── frontend/         # Application React
├── docs/            # Documentation
└── README.md
``` 