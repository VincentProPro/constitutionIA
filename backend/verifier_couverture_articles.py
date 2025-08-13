#!/usr/bin/env python3
"""
Vérification de la couverture complète des articles de 1 à 199
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.constitution_data import ConstitutionArticle
from app.core.config import settings
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verifier_couverture_articles():
    """Vérifie la couverture des articles de 1 à 199"""
    try:
        # Créer l'engine de base de données
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        logger.info("🔍 VÉRIFICATION DE LA COUVERTURE DES ARTICLES (1-199)")
        logger.info("=" * 70)
        
        # Récupérer tous les articles de la base
        all_articles = db.query(ConstitutionArticle).filter(
            ConstitutionArticle.is_active == True
        ).order_by(ConstitutionArticle.article_number).all()
        
        logger.info(f"📊 Total d'articles dans la base: {len(all_articles)}")
        
        # Extraire les numéros d'articles présents
        present_articles = set()
        for article in all_articles:
            try:
                article_num = int(article.article_number)
                present_articles.add(article_num)
            except ValueError:
                logger.warning(f"⚠️ Numéro d'article invalide: {article.article_number}")
        
        logger.info(f"📋 Articles présents: {sorted(present_articles)}")
        
        # Vérifier la couverture de 1 à 199
        missing_articles = []
        present_in_range = []
        
        for i in range(1, 200):
            if i in present_articles:
                present_in_range.append(i)
            else:
                missing_articles.append(i)
        
        # Statistiques
        logger.info(f"\n📈 STATISTIQUES DE COUVERTURE:")
        logger.info(f"   Articles présents (1-199): {len(present_in_range)}")
        logger.info(f"   Articles manquants (1-199): {len(missing_articles)}")
        logger.info(f"   Taux de couverture: {(len(present_in_range)/199)*100:.1f}%")
        
        # Afficher les articles présents
        logger.info(f"\n✅ ARTICLES PRÉSENTS (1-199):")
        if present_in_range:
            # Grouper par plages pour une meilleure lisibilité
            ranges = []
            start = present_in_range[0]
            end = start
            
            for i in range(1, len(present_in_range)):
                if present_in_range[i] == end + 1:
                    end = present_in_range[i]
                else:
                    if start == end:
                        ranges.append(str(start))
                    else:
                        ranges.append(f"{start}-{end}")
                    start = present_in_range[i]
                    end = start
            
            # Ajouter la dernière plage
            if start == end:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{end}")
            
            logger.info(f"   {', '.join(ranges)}")
        else:
            logger.info("   Aucun article dans la plage 1-199")
        
        # Afficher les articles manquants
        if missing_articles:
            logger.info(f"\n❌ ARTICLES MANQUANTS (1-199):")
            # Grouper par plages pour une meilleure lisibilité
            ranges = []
            start = missing_articles[0]
            end = start
            
            for i in range(1, len(missing_articles)):
                if missing_articles[i] == end + 1:
                    end = missing_articles[i]
                else:
                    if start == end:
                        ranges.append(str(start))
                    else:
                        ranges.append(f"{start}-{end}")
                    start = missing_articles[i]
                    end = start
            
            # Ajouter la dernière plage
            if start == end:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{end}")
            
            logger.info(f"   {', '.join(ranges)}")
        
        # Articles hors plage (au-delà de 199)
        beyond_199 = [num for num in present_articles if num > 199]
        if beyond_199:
            logger.info(f"\n🔍 ARTICLES AU-DELÀ DE 199:")
            logger.info(f"   {sorted(beyond_199)}")
        
        # Analyse détaillée des articles présents
        logger.info(f"\n📋 DÉTAIL DES ARTICLES PRÉSENTS:")
        for article in all_articles:
            try:
                article_num = int(article.article_number)
                if 1 <= article_num <= 199:
                    content_preview = article.content[:50] + "..." if len(article.content) > 50 else article.content
                    logger.info(f"   Article {article_num}: {content_preview}")
            except ValueError:
                continue
        
        # Recommandations
        logger.info(f"\n💡 RECOMMANDATIONS:")
        if len(missing_articles) > 0:
            logger.info(f"   ⚠️ {len(missing_articles)} articles manquants - Considérer l'ajout des articles manquants")
        else:
            logger.info("   ✅ Couverture complète - Tous les articles de 1 à 199 sont présents")
        
        if len(present_in_range) < 50:
            logger.info("   ⚠️ Couverture faible - Seulement quelques articles présents")
        elif len(present_in_range) < 150:
            logger.info("   ⚠️ Couverture partielle - Beaucoup d'articles manquants")
        else:
            logger.info("   ✅ Couverture bonne - La plupart des articles sont présents")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification: {e}")
        return False

if __name__ == "__main__":
    success = verifier_couverture_articles()
    if success:
        logger.info("\n🎉 Vérification terminée!")
    else:
        logger.error("❌ Vérification échouée!")
        sys.exit(1)
