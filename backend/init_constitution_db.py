#!/usr/bin/env python3
"""
Script d'initialisation de la base de données de constitution
Parse le fichier 02.txt et stocke les données structurées
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.constitution_data import Base
from app.services.constitution_parser import ConstitutionParser
from app.core.config import settings
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialise la base de données et les tables"""
    try:
        # Créer l'engine de base de données
        engine = create_engine(settings.DATABASE_URL)
        
        # Créer toutes les tables
        Base.metadata.create_all(bind=engine)
        logger.info("Tables de constitution créées avec succès")
        
        # Créer une session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        return db, engine
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
        raise

def parse_and_store_constitution():
    """Parse le fichier 02.txt et stocke les données"""
    try:
        # Initialiser la base de données
        db, engine = init_database()
        
        # Chemin vers le fichier 02.txt
        constitution_file = "Correction/02.txt"
        
        if not os.path.exists(constitution_file):
            logger.error(f"Fichier de constitution non trouvé: {constitution_file}")
            return False
        
        # Créer le parser
        parser = ConstitutionParser(db)
        
        # Parser le fichier
        logger.info("Début du parsing de la constitution...")
        parsed_data = parser.parse_constitution_file(constitution_file)
        
        logger.info(f"Parsing terminé: {parsed_data['total_articles']} articles, {parsed_data['total_sections']} sections")
        
        # Sauvegarder dans la base de données
        logger.info("Sauvegarde dans la base de données...")
        success = parser.save_to_database(parsed_data)
        
        if success:
            logger.info("✅ Constitution parsée et sauvegardée avec succès!")
            logger.info(f"📊 Statistiques:")
            logger.info(f"   - Articles: {parsed_data['total_articles']}")
            logger.info(f"   - Sections: {parsed_data['total_sections']}")
            logger.info(f"   - Mots-clés: {len(parsed_data['keywords'])}")
        else:
            logger.error("❌ Erreur lors de la sauvegarde")
            return False
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors du parsing: {e}")
        return False

def verify_database():
    """Vérifie que les données ont été correctement stockées"""
    try:
        db, engine = init_database()
        
        from app.models.constitution_data import ConstitutionArticle, ConstitutionStructure, ConstitutionKeyword
        
        # Compter les articles
        article_count = db.query(ConstitutionArticle).count()
        structure_count = db.query(ConstitutionStructure).count()
        keyword_count = db.query(ConstitutionKeyword).count()
        
        logger.info("📋 Vérification de la base de données:")
        logger.info(f"   - Articles: {article_count}")
        logger.info(f"   - Structures: {structure_count}")
        logger.info(f"   - Mots-clés: {keyword_count}")
        
        # Afficher quelques exemples
        if article_count > 0:
            sample_articles = db.query(ConstitutionArticle).limit(3).all()
            logger.info("📄 Exemples d'articles:")
            for article in sample_articles:
                logger.info(f"   - Article {article.article_number}: {article.title or 'Sans titre'}")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Initialisation de la base de données de constitution")
    logger.info("=" * 50)
    
    # Parser et stocker la constitution
    if parse_and_store_constitution():
        logger.info("✅ Parsing et stockage réussi!")
        
        # Vérifier la base de données
        if verify_database():
            logger.info("✅ Vérification réussie!")
            logger.info("🎉 Base de données de constitution initialisée avec succès!")
        else:
            logger.error("❌ Erreur lors de la vérification")
    else:
        logger.error("❌ Erreur lors du parsing et stockage")
        sys.exit(1)
