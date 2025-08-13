#!/usr/bin/env python3
"""
Ajout des articles manquants à la base de données
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

def extraire_articles_manquants():
    """Extrait les articles manquants du fichier de constitution"""
    try:
        constitution_file = "Correction/02.txt"
        
        if not os.path.exists(constitution_file):
            logger.error(f"❌ Fichier de constitution non trouvé: {constitution_file}")
            return None
        
        logger.info(f"📖 Lecture du fichier: {constitution_file}")
        
        # Lire le fichier avec différents encodages
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        content = None
        
        for encoding in encodings:
            try:
                with open(constitution_file, 'r', encoding=encoding) as file:
                    content = file.read()
                logger.info(f"✅ Fichier lu avec succès en {encoding}")
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            logger.error("❌ Impossible de lire le fichier avec les encodages supportés")
            return None
        
        # Articles manquants à extraire
        articles_manquants = []
        
        # Patterns pour différents formats d'articles
        patterns = [
            r'Article\s+(\d+)\s*[:.]?\s*(.*?)(?=Article\s+\d+|$)',
            r'Article\s+(\d+er)\s*[:.]?\s*(.*?)(?=Article\s+\d+|$)',
            r'Article\s+(\d+)\s*[:.]?\s*(.*?)(?=\n\s*Article\s+\d+|$)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                article_num = match[0]
                article_content = match[1].strip()
                
                # Nettoyer le numéro d'article
                if article_num.lower() == '1er':
                    article_num = '1'
                elif article_num.lower() == '2e':
                    article_num = '2'
                elif article_num.lower() == '3e':
                    article_num = '3'
                
                try:
                    article_num_int = int(article_num)
                    if 1 <= article_num_int <= 199:
                        articles_manquants.append({
                            'number': article_num,
                            'content': article_content
                        })
                except ValueError:
                    continue
        
        # Filtrer les articles manquants (1-14, 158-160, 162-166, 186)
        articles_a_ajouter = []
        articles_manquants_nums = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,158,159,160,162,163,164,165,166,186]
        
        for article in articles_manquants:
            if int(article['number']) in articles_manquants_nums:
                articles_a_ajouter.append(article)
        
        logger.info(f"📋 Articles manquants trouvés: {len(articles_a_ajouter)}")
        for article in articles_a_ajouter:
            logger.info(f"   Article {article['number']}: {article['content'][:50]}...")
        
        return articles_a_ajouter
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'extraction: {e}")
        return None

def ajouter_articles_manquants(articles):
    """Ajoute les articles manquants à la base de données"""
    try:
        # Créer l'engine de base de données
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        logger.info("💾 Ajout des articles manquants à la base de données...")
        
        articles_ajoutes = 0
        
        for article_data in articles:
            try:
                # Vérifier si l'article existe déjà
                existing = db.query(ConstitutionArticle).filter(
                    ConstitutionArticle.article_number == article_data['number']
                ).first()
                
                if existing:
                    logger.info(f"⚠️ Article {article_data['number']} existe déjà")
                    continue
                
                # Créer le nouvel article
                new_article = ConstitutionArticle(
                    article_number=article_data['number'],
                    title=None,
                    content=article_data['content'],
                    chapter=None,
                    section=None,
                    part=None,
                    page_number=None,
                    keywords=None,
                    category=None,
                    is_active=True
                )
                
                db.add(new_article)
                articles_ajoutes += 1
                logger.info(f"✅ Article {article_data['number']} ajouté")
                
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'ajout de l'article {article_data['number']}: {e}")
                continue
        
        # Commit des changements
        db.commit()
        logger.info(f"💾 {articles_ajoutes} articles ajoutés avec succès")
        
        # Vérifier le total
        total_articles = db.query(ConstitutionArticle).filter(
            ConstitutionArticle.is_active == True
        ).count()
        
        logger.info(f"📊 Total d'articles dans la base: {total_articles}")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'ajout: {e}")
        return False

def main():
    """Fonction principale"""
    logger.info("🔧 AJOUT DES ARTICLES MANQUANTS")
    logger.info("=" * 50)
    
    # Extraire les articles manquants
    articles = extraire_articles_manquants()
    
    if not articles:
        logger.error("❌ Aucun article manquant trouvé")
        return False
    
    # Ajouter les articles à la base de données
    success = ajouter_articles_manquants(articles)
    
    if success:
        logger.info("🎉 Articles manquants ajoutés avec succès!")
        return True
    else:
        logger.error("❌ Échec de l'ajout des articles")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
