#!/usr/bin/env python3
"""
Vider le cache et tester les améliorations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.services.chatnow_service import OptimizedChatNowService
from app.models.constitution_data import ConstitutionArticle, ConstitutionCache
from app.core.config import settings
import logging
import time

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def vider_cache_et_tester():
    """Vide le cache et teste les améliorations"""
    try:
        # Créer l'engine de base de données
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        logger.info("🧹 VIDAGE DU CACHE ET TEST DES AMÉLIORATIONS")
        logger.info("=" * 60)
        
        # Vider le cache
        logger.info("🧹 Vidage du cache...")
        cache_count = db.execute(text("SELECT COUNT(*) FROM constitution_cache")).scalar()
        logger.info(f"   Entrées en cache avant vidage: {cache_count}")
        
        db.execute(text("DELETE FROM constitution_cache"))
        db.commit()
        
        cache_count_apres = db.execute(text("SELECT COUNT(*) FROM constitution_cache")).scalar()
        logger.info(f"   Entrées en cache après vidage: {cache_count_apres}")
        logger.info("✅ Cache vidé avec succès")
        
        # Initialiser le service ChatNow
        chatnow_service = OptimizedChatNowService(db)
        
        # Questions problématiques à tester
        questions_test = [
            ("Formation du gouvernement", "comment est formé le gouvernement"),
            ("Liberté d'expression", "que dit la constitution sur la liberté d'expression"),
            ("Devoirs des citoyens", "quels sont les devoirs des citoyens"),
            ("Révision constitutionnelle", "comment peut-on réviser la constitution"),
            ("Promulgation des lois", "comment sont promulguées les lois"),
            ("Haute trahison", "qu'est-ce que la haute trahison selon la constitution"),
            ("État d'urgence", "quand peut-on déclarer l'état d'urgence"),
            ("Dissolution parlementaire", "quand peut-on dissoudre l'assemblée nationale")
        ]
        
        results = []
        total_time = 0
        
        logger.info("\n🧪 TEST DES AMÉLIORATIONS (CACHE VIDÉ)")
        logger.info("-" * 60)
        
        for i, (description, question) in enumerate(questions_test, 1):
            logger.info(f"\nTest {i}: {description}")
            logger.info(f"Question: {question}")
            
            start_time = time.time()
            
            # Générer la réponse
            response = chatnow_service.create_chat_response(
                question=question,
                chat_history=None,
                user_id=f"test_cache_vide_{i}"
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            total_time += response_time
            
            logger.info(f"⏱️ Temps: {response_time:.2f}s")
            logger.info(f"📝 Réponse: {response}")
            
            # Analyser la qualité de la réponse
            quality_score = analyser_qualite_reponse(response, question)
            
            results.append({
                'test': i,
                'description': description,
                'question': question,
                'response': response,
                'time': response_time,
                'quality_score': quality_score
            })
            
            logger.info(f"📊 Score qualité: {quality_score}/10")
        
        # Analyse des résultats
        logger.info("\n" + "=" * 60)
        logger.info("📊 ANALYSE DES RÉSULTATS")
        logger.info("=" * 60)
        
        # Statistiques générales
        avg_time = total_time / len(results)
        avg_quality = sum(r['quality_score'] for r in results) / len(results)
        
        logger.info(f"⏱️ Temps moyen: {avg_time:.2f}s")
        logger.info(f"📊 Qualité moyenne: {avg_quality:.1f}/10")
        
        # Répartition des scores
        excellent = sum(1 for r in results if r['quality_score'] >= 8)
        bon = sum(1 for r in results if 6 <= r['quality_score'] < 8)
        moyen = sum(1 for r in results if 4 <= r['quality_score'] < 6)
        faible = sum(1 for r in results if r['quality_score'] < 4)
        
        logger.info(f"\n📈 RÉPARTITION DES SCORES:")
        logger.info(f"   Excellent (8-10): {excellent}/{len(results)} ({excellent/len(results)*100:.1f}%)")
        logger.info(f"   Bon (6-7): {bon}/{len(results)} ({bon/len(results)*100:.1f}%)")
        logger.info(f"   Moyen (4-5): {moyen}/{len(results)} ({moyen/len(results)*100:.1f}%)")
        logger.info(f"   Faible (0-3): {faible}/{len(results)} ({faible/len(results)*100:.1f}%)")
        
        # Compter les réponses qui citent des articles
        reponses_avec_citations = sum(1 for r in results if contient_citations_articles(r['response']))
        logger.info(f"\n💾 UTILISATION DE LA BASE DE DONNÉES:")
        logger.info(f"   Réponses avec citations d'articles: {reponses_avec_citations}/{len(results)} ({reponses_avec_citations/len(results)*100:.1f}%)")
        
        # Vérifier le nouveau cache
        nouveau_cache_count = db.execute(text("SELECT COUNT(*) FROM constitution_cache")).scalar()
        logger.info(f"   Nouvelles entrées en cache: {nouveau_cache_count}")
        
        # Évaluation des améliorations
        logger.info(f"\n🎯 ÉVALUATION DES AMÉLIORATIONS:")
        
        if avg_quality >= 7.0:
            logger.info("✅ EXCELLENT - Les améliorations ont considérablement amélioré la précision")
        elif avg_quality >= 6.0:
            logger.info("✅ BON - Les améliorations ont amélioré la précision")
        elif avg_quality >= 5.0:
            logger.info("⚠️ MOYEN - Les améliorations ont eu un effet modéré")
        else:
            logger.info("❌ FAIBLE - Les améliorations nécessitent des ajustements")
        
        # Comparaison avec les scores précédents
        amelioration = avg_quality - 2.5  # Score moyen avant améliorations
        logger.info(f"📈 Amélioration estimée: +{amelioration:.1f} points")
        
        # Questions améliorées
        questions_ameliores = sum(1 for r in results if r['quality_score'] >= 6)
        logger.info(f"   Questions améliorées: {questions_ameliores}/{len(results)} ({questions_ameliores/len(results)*100:.1f}%)")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {e}")
        return False

def analyser_qualite_reponse(reponse, question):
    """Analyse la qualité d'une réponse (0-10)"""
    score = 0
    
    # Vérifier la longueur de la réponse
    if len(reponse) > 50:
        score += 2
    elif len(reponse) > 20:
        score += 1
    
    # Vérifier la présence de citations d'articles
    if contient_citations_articles(reponse):
        score += 3
    
    # Vérifier la pertinence (pas de réponse générique)
    if "n'est pas disponible" not in reponse.lower() and "pas trouvé" not in reponse.lower():
        score += 2
    
    # Vérifier la structure (format cohérent)
    if "- Article" in reponse or "Article" in reponse:
        score += 1
    
    # Vérifier la précision (réponse spécifique à la question)
    if question.lower() in reponse.lower() or any(mot in reponse.lower() for mot in question.lower().split()):
        score += 1
    
    # Bonus pour les réponses très détaillées
    if len(reponse) > 200:
        score += 1
    
    return min(score, 10)

def contient_citations_articles(reponse):
    """Vérifie si la réponse contient des citations d'articles"""
    import re
    patterns = [
        r'Article\s+\d+',
        r'article\s+\d+',
        r'Art\.\s*\d+',
        r'art\.\s*\d+'
    ]
    
    for pattern in patterns:
        if re.search(pattern, reponse, re.IGNORECASE):
            return True
    return False

if __name__ == "__main__":
    success = vider_cache_et_tester()
    if success:
        logger.info("\n🎉 Test avec cache vidé terminé!")
    else:
        logger.error("❌ Test avec cache vidé échoué!")
        sys.exit(1)
