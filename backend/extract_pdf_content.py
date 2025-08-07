#!/usr/bin/env python3
"""
Script pour extraire le contenu des PDFs et le sauvegarder dans la base de données
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.constitution import Constitution
from app.services.pdf_analyzer import PDFAnalyzer
from app.core.config import settings
from pathlib import Path

def extract_pdf_content():
    """Extrait le contenu des PDFs et le sauvegarde"""
    print("📄 Extraction du contenu des PDFs")
    print("=" * 40)
    
    db = SessionLocal()
    
    try:
        # Récupérer toutes les constitutions
        constitutions = db.query(Constitution).filter(Constitution.is_active == True).all()
        print(f"📚 Constitutions trouvées: {len(constitutions)}")
        
        if not constitutions:
            print("❌ Aucune constitution trouvée")
            return
        
        for constitution in constitutions:
            print(f"\n📄 Traitement: {constitution.title}")
            
            # Vérifier si le contenu existe déjà
            if constitution.content and len(constitution.content) > 100:
                print(f"✅ Contenu déjà extrait ({len(constitution.content)} caractères)")
                continue
            
            # Vérifier si le fichier existe
            file_path = Path(constitution.file_path) if constitution.file_path else Path("Fichier") / constitution.filename
            if not file_path.exists():
                print(f"❌ Fichier non trouvé: {file_path}")
                continue
            
            print(f"📂 Fichier: {file_path}")
            
            # Extraire le contenu
            try:
                pdf_analyzer = PDFAnalyzer(settings.OPENAI_API_KEY or "dummy_key")
                content = pdf_analyzer.extract_text_from_pdf(str(file_path))
                
                if content and len(content) > 100:
                    # Mettre à jour la base de données
                    constitution.content = content
                    db.commit()
                    print(f"✅ Contenu extrait et sauvegardé ({len(content)} caractères)")
                    
                    # Afficher un aperçu
                    preview = content[:200].replace('\n', ' ')
                    print(f"📝 Aperçu: {preview}...")
                    
                else:
                    print(f"❌ Contenu trop court ou vide ({len(content) if content else 0} caractères)")
                    
            except Exception as e:
                print(f"❌ Erreur lors de l'extraction: {e}")
        
        print("\n✅ Extraction terminée!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    extract_pdf_content() 