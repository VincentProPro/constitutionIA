#!/usr/bin/env python3
"""
Initialisation de la base de données avec la constitution complète
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.constitution_data import Base
from app.services.constitution_parser import ConstitutionParser
from app.core.config import settings
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_constitution_complete():
    """Initialise la base de données avec la constitution complète"""
    try:
        # Créer l'engine de base de données
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        logger.info("🏗️ INITIALISATION DE LA BASE DE DONNÉES COMPLÈTE")
        logger.info("=" * 60)
        
        # Vérifier que le fichier existe
        constitution_file = "Correction/02.txt"
        if not os.path.exists(constitution_file):
            logger.error(f"❌ Fichier de constitution non trouvé: {constitution_file}")
            return False
        
        logger.info(f"📄 Fichier trouvé: {constitution_file}")
        logger.info(f"📏 Taille du fichier: {os.path.getsize(constitution_file)} octets")
        
        # Nettoyer la base de données existante
        logger.info("🧹 Nettoyage de la base de données...")
        try:
            # Supprimer toutes les tables existantes
            db.execute(text("DROP TABLE IF EXISTS constitution_cache"))
            db.execute(text("DROP TABLE IF EXISTS constitution_keywords"))
            db.execute(text("DROP TABLE IF EXISTS constitution_structure"))
            db.execute(text("DROP TABLE IF EXISTS constitution_articles"))
            db.commit()
            logger.info("✅ Tables supprimées")
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors du nettoyage: {e}")
        
        # Créer les nouvelles tables
        logger.info("🔨 Création des nouvelles tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tables créées")
        
        # Parser le fichier de constitution
        logger.info("📖 Parsing du fichier de constitution...")
        parser = ConstitutionParser(db)
        
        try:
            parsed_data = parser.parse_constitution_file(constitution_file)
            logger.info(f"✅ Parsing terminé: {parsed_data['total_articles']} articles trouvés")
        except Exception as e:
            logger.error(f"❌ Erreur lors du parsing: {e}")
            return False
        
        # Sauvegarder dans la base de données
        logger.info("💾 Sauvegarde dans la base de données...")
        try:
            success = parser.save_to_database(parsed_data)
            if success:
                logger.info("✅ Données sauvegardées avec succès")
            else:
                logger.error("❌ Erreur lors de la sauvegarde")
                return False
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde: {e}")
            return False
        
        # Vérifier les résultats
        logger.info("🔍 Vérification des résultats...")
        try:
            # Compter les articles
            article_count = db.execute(text("SELECT COUNT(*) FROM constitution_articles")).scalar()
            logger.info(f"📊 Articles dans la base: {article_count}")
            
            # Afficher quelques exemples
            articles = db.execute(text("SELECT article_number, LEFT(content, 100) as preview FROM constitution_articles ORDER BY CAST(article_number AS INTEGER) LIMIT 10")).fetchall()
            
            logger.info("📋 Exemples d'articles:")
            for article in articles:
                logger.info(f"   Article {article.article_number}: {article.preview}...")
            
            # Vérifier la couverture
            if article_count > 0:
                logger.info("✅ Initialisation réussie!")
                logger.info(f"📈 {article_count} articles disponibles dans la base")
            else:
                logger.warning("⚠️ Aucun article trouvé - vérifier le parsing")
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la vérification: {e}")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation: {e}")
        return False

if __name__ == "__main__":
    success = init_constitution_complete()
    if success:
        logger.info("\n🎉 Initialisation terminée avec succès!")
    else:
        logger.error("❌ Initialisation échouée!")
        sys.exit(1)
