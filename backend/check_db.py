#!/usr/bin/env python3
"""
Script pour vérifier l'état de la base de données
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Ajouter le répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).parent))

from app.database import engine, Base
from app.models.constitution import Constitution
from sqlalchemy.orm import sessionmaker

def check_database():
    """Vérifie l'état de la base de données"""
    print("🔍 Vérification de la base de données")
    print("=" * 40)
    
    try:
        # Créer les tables si elles n'existent pas
        print("📋 Création des tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tables créées/vérifiées")
        
        # Vérifier les constitutions existantes
        Session = sessionmaker(bind=engine)
        db = Session()
        
        try:
            constitutions = db.query(Constitution).all()
            print(f"📊 {len(constitutions)} constitution(s) trouvée(s) en base:")
            
            for constitution in constitutions:
                print(f"   - ID: {constitution.id}")
                print(f"     Titre: {constitution.title}")
                print(f"     Fichier: {constitution.filename}")
                print(f"     Année: {constitution.year}")
                print(f"     Statut: {constitution.status}")
                print(f"     Créé le: {constitution.created_at}")
                print()
            
            if not constitutions:
                print("ℹ️ Aucune constitution en base de données")
                print("   Cela peut être normal si aucun fichier n'a encore été analysé")
        
        finally:
            db.close()
        
        # Vérifier les fichiers PDF
        files_dir = Path("Fichier")
        if files_dir.exists():
            pdf_files = list(files_dir.glob("*.pdf"))
            print(f"📁 {len(pdf_files)} fichier(s) PDF trouvé(s) dans le dossier 'Fichier':")
            for pdf_file in pdf_files:
                print(f"   - {pdf_file.name}")
        else:
            print("❌ Dossier 'Fichier' non trouvé")
        
        # Vérifier la configuration OpenAI
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            print("✅ OPENAI_API_KEY configurée")
        else:
            print("❌ OPENAI_API_KEY non configurée dans .env")
        
        print("\n" + "=" * 40)
        print("🎯 Résumé:")
        if constitutions:
            print("✅ Base de données initialisée avec des données")
        else:
            print("ℹ️ Base de données vide - normal si aucun fichier n'a été analysé")
        
        if pdf_files:
            print(f"✅ {len(pdf_files)} fichier(s) PDF prêt(s) à être analysé(s)")
        else:
            print("❌ Aucun fichier PDF trouvé")
        
        if openai_api_key:
            print("✅ Configuration OpenAI OK")
        else:
            print("❌ Configuration OpenAI manquante")
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False
    
    return True

if __name__ == "__main__":
    check_database() 