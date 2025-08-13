#!/usr/bin/env python3
"""
Script pour vérifier le contenu de la base de données de constitution
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.constitution_data import ConstitutionArticle, ConstitutionStructure, ConstitutionKeyword
from app.core.config import settings
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_content():
    """Vérifie le contenu de la base de données"""
    try:
        # Créer l'engine de base de données
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Compter les articles
        article_count = db.query(ConstitutionArticle).count()
        logger.info(f"📊 Nombre total d'articles: {article_count}")
        
        # Afficher tous les articles
        articles = db.query(ConstitutionArticle).all()
        logger.info("📄 ARTICLES DANS LA BASE DE DONNÉES:")
        logger.info("=" * 50)
        
        for article in articles:
            logger.info(f"Article {article.article_number}:")
            logger.info(f"  Titre: {article.title or 'Sans titre'}")
            logger.info(f"  Catégorie: {article.category}")
            logger.info(f"  Contenu: {article.content[:200]}...")
            logger.info(f"  Mots-clés: {article.keywords}")
            logger.info("-" * 30)
        
        # Rechercher spécifiquement les articles sur le président
        president_articles = db.query(ConstitutionArticle).filter(
            ConstitutionArticle.content.ilike('%président%')
        ).all()
        
        logger.info("🏛️ ARTICLES CONCERNANT LE PRÉSIDENT:")
        logger.info("=" * 50)
        
        for article in president_articles:
            logger.info(f"Article {article.article_number}:")
            logger.info(f"  Contenu: {article.content}")
            logger.info("-" * 30)
        
        # Rechercher les articles avec "mandat"
        mandat_articles = db.query(ConstitutionArticle).filter(
            ConstitutionArticle.content.ilike('%mandat%')
        ).all()
        
        logger.info("⏰ ARTICLES CONCERNANT LES MANDATS:")
        logger.info("=" * 50)
        
        for article in mandat_articles:
            logger.info(f"Article {article.article_number}:")
            logger.info(f"  Contenu: {article.content}")
            logger.info("-" * 30)
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification: {e}")
        return False

if __name__ == "__main__":
    success = check_database_content()
    if success:
        logger.info("✅ Vérification terminée!")
    else:
        logger.error("❌ Erreur lors de la vérification!")
        sys.exit(1)
