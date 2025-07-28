#!/usr/bin/env python3
"""
Script pour afficher le contenu de la base de données
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

def show_database():
    """Affiche le contenu de la base de données"""
    print("📊 Contenu de la base de données")
    print("=" * 50)
    
    # Vérifier si la base de données existe
    db_file = Path("constitutionia.db")
    if not db_file.exists():
        print("❌ Base de données non trouvée")
        print("   La base de données n'a pas encore été créée.")
        print("   Lancez d'abord le serveur ou init_pdf_analyzer.py")
        return
    
    print(f"✅ Base de données trouvée: {db_file}")
    print(f"📏 Taille: {db_file.stat().st_size} bytes")
    
    try:
        # Créer les tables si elles n'existent pas
        Base.metadata.create_all(bind=engine)
        
        # Connexion à la base de données
        Session = sessionmaker(bind=engine)
        db = Session()
        
        try:
            # Compter les constitutions
            count = db.query(Constitution).count()
            print(f"📈 Nombre total de constitutions: {count}")
            
            if count == 0:
                print("ℹ️ Aucune constitution en base de données")
                return
            
            # Afficher toutes les constitutions
            constitutions = db.query(Constitution).all()
            
            for i, constitution in enumerate(constitutions, 1):
                print(f"\n📄 Constitution #{i}")
                print(f"   ID: {constitution.id}")
                print(f"   Titre: {constitution.title}")
                print(f"   Fichier: {constitution.filename}")
                print(f"   Description: {constitution.description}")
                print(f"   Année: {constitution.year}")
                print(f"   Pays: {constitution.country}")
                print(f"   Statut: {constitution.status}")
                print(f"   Résumé: {constitution.summary}")
                print(f"   Taille fichier: {constitution.file_size} bytes")
                print(f"   Chemin: {constitution.file_path}")
                print(f"   Créé le: {constitution.created_at}")
                print(f"   Modifié le: {constitution.updated_at}")
                print(f"   Actif: {constitution.is_active}")
                
                if constitution.key_topics:
                    print(f"   Thèmes clés: {constitution.key_topics}")
                
                print("-" * 40)
        
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Erreur lors de l'affichage: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    show_database() 