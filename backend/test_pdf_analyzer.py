#!/usr/bin/env python3
"""
Script de test pour l'analyseur PDF
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

def test_pdf_analyzer():
    """Teste l'analyseur PDF"""
    print("🧪 Test de l'analyseur PDF")
    print("=" * 40)
    
    # Vérifier la clé API OpenAI
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ Erreur: OPENAI_API_KEY non définie dans .env")
        return False
    
    # Vérifier que le dossier Fichier existe
    files_dir = Path("Fichier")
    if not files_dir.exists():
        print("❌ Erreur: Dossier 'Fichier' n'existe pas")
        return False
    
    # Lister les fichiers PDF
    pdf_files = list(files_dir.glob("*.pdf"))
    if not pdf_files:
        print("❌ Erreur: Aucun fichier PDF trouvé dans le dossier 'Fichier'")
        return False
    
    print(f"📁 Trouvé {len(pdf_files)} fichier(s) PDF:")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file.name}")
    
    # Initialiser l'analyseur
    pdf_analyzer = PDFAnalyzer(openai_api_key)
    
    # Tester l'extraction de texte
    print("\n📖 Test d'extraction de texte...")
    test_file = pdf_files[0]
    text = pdf_analyzer.extract_text_from_pdf(str(test_file))
    
    if text.strip():
        print(f"✅ Texte extrait avec succès ({len(text)} caractères)")
        print(f"   Aperçu: {text[:200]}...")
    else:
        print("❌ Aucun texte extrait")
        return False
    
    # Tester l'analyse GPT-4
    print("\n🤖 Test d'analyse GPT-4...")
    try:
        analysis = pdf_analyzer.analyze_pdf_with_gpt4(str(test_file), test_file.name)
        print("✅ Analyse GPT-4 réussie:")
        print(f"   Titre: {analysis.get('title', 'N/A')}")
        print(f"   Année: {analysis.get('year', 'N/A')}")
        print(f"   Statut: {analysis.get('status', 'N/A')}")
        print(f"   Description: {analysis.get('description', 'N/A')[:100]}...")
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse GPT-4: {e}")
        return False
    
    # Tester le FileWatcher
    print("\n👁️ Test du FileWatcher...")
    try:
        file_watcher = FileWatcher(pdf_analyzer)
        new_files = file_watcher.scan_for_new_files()
        print(f"✅ FileWatcher initialisé, {len(new_files)} nouveau(x) fichier(s) détecté(s)")
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation du FileWatcher: {e}")
        return False
    
    print("\n✅ Tous les tests sont passés avec succès!")
    return True

def main():
    """Fonction principale"""
    success = test_pdf_analyzer()
    
    if success:
        print("\n🎉 Le système est prêt à être utilisé!")
        print("\nProchaines étapes:")
        print("1. Démarrer le backend: python -m uvicorn main:app --reload")
        print("2. Aller sur http://localhost:3000/constitutions")
        print("3. Cliquer sur 'Analyser les fichiers'")
    else:
        print("\n❌ Des erreurs ont été détectées")
        sys.exit(1)

if __name__ == "__main__":
    main() 