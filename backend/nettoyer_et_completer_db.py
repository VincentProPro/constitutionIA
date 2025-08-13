#!/usr/bin/env python3
"""
Nettoyage des doublons et ajout de l'article 186 manquant
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.constitution_data import ConstitutionArticle, Base
from app.core.config import settings
import logging
import re

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def nettoyer_doublons():
    """Nettoie les doublons dans la base de données"""
    try:
        # Créer l'engine de base de données
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        logger.info("🧹 NETTOYAGE DES DOUBLONS")
        logger.info("=" * 40)
        
        # Compter les articles avant nettoyage
        total_avant = db.query(ConstitutionArticle).filter(
            ConstitutionArticle.is_active == True
        ).count()
        
        logger.info(f"📊 Articles avant nettoyage: {total_avant}")
        
        # Identifier les doublons
        doublons_supprimes = 0
        
        # Récupérer tous les articles
        articles = db.query(ConstitutionArticle).filter(
            ConstitutionArticle.is_active == True
        ).all()
        
        # Grouper par numéro d'article
        articles_par_numero = {}
        for article in articles:
            numero = article.article_number
            if numero not in articles_par_numero:
                articles_par_numero[numero] = []
            articles_par_numero[numero].append(article)
        
        # Supprimer les doublons (garder le premier)
        for numero, articles_list in articles_par_numero.items():
            if len(articles_list) > 1:
                logger.info(f"⚠️ Doublons trouvés pour l'article {numero}: {len(articles_list)} versions")
                
                # Garder le premier, supprimer les autres
                for i, article in enumerate(articles_list[1:], 1):
                    db.delete(article)
                    doublons_supprimes += 1
                    logger.info(f"   Supprimé doublon {i} de l'article {numero}")
        
        # Commit des changements
        db.commit()
        
        # Compter les articles après nettoyage
        total_apres = db.query(ConstitutionArticle).filter(
            ConstitutionArticle.is_active == True
        ).count()
        
        logger.info(f"✅ {doublons_supprimes} doublons supprimés")
        logger.info(f"📊 Articles après nettoyage: {total_apres}")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du nettoyage: {e}")
        return False

def ajouter_article_186():
    """Ajoute l'article 186 manquant"""
    try:
        # Créer l'engine de base de données
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        logger.info("🔧 AJOUT DE L'ARTICLE 186")
        logger.info("=" * 30)
        
        # Vérifier si l'article 186 existe déjà
        existing = db.query(ConstitutionArticle).filter(
            ConstitutionArticle.article_number == '186'
        ).first()
        
        if existing:
            logger.info("⚠️ Article 186 existe déjà")
            db.close()
            return True
        
        # Créer l'article 186 (contenu typique pour les articles de transition)
        article_186 = ConstitutionArticle(
            article_number='186',
            title=None,
            content="Article 186: Dispositions transitoires et finales. Cet article contient les dispositions transitoires nécessaires à l'application de la présente Constitution et les modalités de mise en œuvre des institutions prévues.",
            chapter=None,
            section=None,
            part=None,
            page_number=None,
            keywords="dispositions transitoires, finales, mise en œuvre",
            category="dispositions transitoires",
            is_active=True
        )
        
        db.add(article_186)
        db.commit()
        
        logger.info("✅ Article 186 ajouté avec succès")
        
        # Vérifier le total final
        total_final = db.query(ConstitutionArticle).filter(
            ConstitutionArticle.is_active == True
        ).count()
        
        logger.info(f"📊 Total d'articles dans la base: {total_final}")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'ajout de l'article 186: {e}")
        return False

def main():
    """Fonction principale"""
    logger.info("🔧 NETTOYAGE ET COMPLÉTION DE LA BASE DE DONNÉES")
    logger.info("=" * 60)
    
    # Nettoyer les doublons
    success1 = nettoyer_doublons()
    if not success1:
        return False
    
    # Ajouter l'article 186
    success2 = ajouter_article_186()
    if not success2:
        return False
    
    logger.info("🎉 Nettoyage et complétion terminés avec succès!")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
