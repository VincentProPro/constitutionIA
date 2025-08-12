#!/usr/bin/env python3
"""
Script pour traiter tous les fichiers PDF existants et extraire leurs articles
"""

from app.database import SessionLocal
from app.models.constitution import Constitution
from app.services.pdf_import import process_uploaded_pdf
from pathlib import Path
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_all_existing_files():
    """Traiter tous les fichiers PDF existants"""
    db = SessionLocal()
    
    try:
        # Récupérer toutes les constitutions actives
        constitutions = db.query(Constitution).filter(
            Constitution.is_active == True
        ).all()
        
        logger.info(f"📋 {len(constitutions)} constitutions trouvées")
        
        processed_count = 0
        success_count = 0
        
        for constitution in constitutions:
            processed_count += 1
            logger.info(f"🔄 Traitement {processed_count}/{len(constitutions)}: {constitution.filename}")
            
            # Vérifier que le fichier existe
            file_path = Path("Fichier") / constitution.filename
            if not file_path.exists():
                logger.warning(f"⚠️ Fichier non trouvé: {file_path}")
                continue
            
            # Traiter le fichier
            try:
                result = process_uploaded_pdf(db, constitution.id, str(file_path))
                
                if result['success']:
                    success_count += 1
                    logger.info(f"✅ {constitution.filename}: {result['articles_count']} articles extraits")
                else:
                    logger.error(f"❌ {constitution.filename}: {result.get('error', 'Erreur inconnue')}")
                    
            except Exception as e:
                logger.error(f"❌ Erreur lors du traitement de {constitution.filename}: {e}")
        
        logger.info(f"🎉 Traitement terminé!")
        logger.info(f"📊 Résultats: {success_count}/{processed_count} fichiers traités avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur générale: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    process_all_existing_files() 