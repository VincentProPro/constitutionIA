#!/usr/bin/env python3
"""
Script d'initialisation pour l'analyseur PDF
Traite automatiquement tous les fichiers PDF dans le dossier Fichier
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Ajouter le répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).parent))

from app.services.pdf_analyzer import PDFAnalyzer
from app.services.file_watcher import FileWatcher
from app.database import engine, Base
from app.core.config import settings

def init_database():
    """Initialise la base de données"""
    print("Création des tables de base de données...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables créées avec succès")

def process_existing_files():
    """Traite tous les fichiers PDF existants"""
    print("Traitement des fichiers PDF existants...")
    
    # Vérifier la clé API OpenAI
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ Erreur: OPENAI_API_KEY non définie dans .env")
        return False
    
    # Initialiser l'analyseur PDF
    pdf_analyzer = PDFAnalyzer(openai_api_key)
    file_watcher = FileWatcher(pdf_analyzer)
    
    # Traiter tous les nouveaux fichiers
    processed_files = file_watcher.process_all_new_files()
    
    if processed_files:
        print(f"✓ {len(processed_files)} fichiers traités avec succès:")
        for constitution in processed_files:
            print(f"  - {constitution.filename}: {constitution.title}")
    else:
        print("✓ Aucun nouveau fichier à traiter")
    
    return True

def main():
    """Fonction principale"""
    print("🚀 Initialisation du système d'analyse PDF")
    print("=" * 50)
    
    # Initialiser la base de données
    init_database()
    
    # Traiter les fichiers existants
    success = process_existing_files()
    
    if success:
        print("\n✅ Initialisation terminée avec succès!")
        print("\nLe système est maintenant prêt à:")
        print("- Analyser automatiquement les nouveaux fichiers PDF")
        print("- Extraire les métadonnées avec GPT-4")
        print("- Stocker les informations en base de données")
        print("\nPour démarrer la surveillance continue, utilisez:")
        print("python -m app.services.file_watcher")
    else:
        print("\n❌ Erreur lors de l'initialisation")
        sys.exit(1)

if __name__ == "__main__":
    main() 