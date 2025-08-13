#!/usr/bin/env python3
"""
Analyse critique du système IA ChatNow
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.chatnow_service import OptimizedChatNowService
from app.core.config import settings
import logging
import time

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def critique_ia_system():
    """Analyse critique du système IA"""
    try:
        # Créer l'engine de base de données
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Initialiser le service ChatNow
        chatnow_service = OptimizedChatNowService(db)
        
        logger.info("🔍 ANALYSE CRITIQUE DU SYSTÈME IA")
        logger.info("=" * 60)
        
        # Tests de différents types de questions
        test_cases = [
            {
                "category": "Question générale vague",
                "questions": [
                    "que dit la constitution sur les enfants",
                    "parle-moi de la constitution",
                    "quels sont les droits",
                    "comment ça marche"
                ]
            },
            {
                "category": "Question spécifique avec numéro d'article",
                "questions": [
                    "que dit l'article 22",
                    "article 26",
                    "l'article 44 parle de quoi"
                ]
            },
            {
                "category": "Question avec mots-clés précis",
                "questions": [
                    "durée mandat présidentiel",
                    "élection président",
                    "droits enfants jeunes"
                ]
            },
            {
                "category": "Question contextuelle",
                "questions": [
                    "à quel âge les enfants doivent aller à l'école",
                    "qui peut être président",
                    "comment sont protégés les jeunes"
                ]
            }
        ]
        
        results = {}
        
        for test_case in test_cases:
            category = test_case["category"]
            questions = test_case["questions"]
            
            logger.info(f"\n📋 CATÉGORIE: {category}")
            logger.info("-" * 40)
            
            category_results = []
            
            for question in questions:
                logger.info(f"\n❓ Question: {question}")
                
                start_time = time.time()
                
                # Générer la réponse
                response = chatnow_service.create_chat_response(
                    question=question,
                    chat_history=None,
                    user_id=f"critique_{category}_{questions.index(question)}"
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                # Analyser la réponse
                analysis = analyze_response_quality(question, response, response_time)
                category_results.append(analysis)
                
                logger.info(f"⏱️ Temps de réponse: {response_time:.2f}s")
                logger.info(f"📝 Réponse: {response[:100]}...")
                logger.info(f"🎯 Score: {analysis['score']}/10")
                logger.info(f"⚠️ Problèmes: {', '.join(analysis['issues'])}")
            
            results[category] = category_results
        
        # Analyse globale
        logger.info("\n" + "=" * 60)
        logger.info("📊 ANALYSE GLOBALE")
        logger.info("=" * 60)
        
        all_scores = []
        all_issues = []
        
        for category, category_results in results.items():
            category_scores = [r['score'] for r in category_results]
            avg_score = sum(category_scores) / len(category_scores)
            all_scores.extend(category_scores)
            
            logger.info(f"\n📈 {category}:")
            logger.info(f"   Score moyen: {avg_score:.2f}/10")
            logger.info(f"   Meilleur score: {max(category_scores)}/10")
            logger.info(f"   Pire score: {min(category_scores)}/10")
            
            for result in category_results:
                all_issues.extend(result['issues'])
        
        # Statistiques globales
        global_avg = sum(all_scores) / len(all_scores)
        logger.info(f"\n🌍 SCORE GLOBAL MOYEN: {global_avg:.2f}/10")
        
        # Problèmes les plus fréquents
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        logger.info(f"\n🚨 PROBLÈMES IDENTIFIÉS:")
        for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"   {issue}: {count} fois")
        
        # Recommandations
        logger.info(f"\n💡 RECOMMANDATIONS D'AMÉLIORATION:")
        recommendations = generate_recommendations(results, issue_counts)
        for i, rec in enumerate(recommendations, 1):
            logger.info(f"   {i}. {rec}")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'analyse: {e}")
        return False

def analyze_response_quality(question: str, response: str, response_time: float) -> dict:
    """Analyse la qualité d'une réponse"""
    score = 10.0
    issues = []
    
    # Critères d'évaluation
    
    # 1. Pertinence du contenu
    if "ne contient pas" in response.lower() or "n'est pas abordé" in response.lower():
        score -= 4
        issues.append("Contenu non pertinent")
    
    # 2. Précision des informations
    if "article" in question.lower() and "article" not in response.lower():
        score -= 2
        issues.append("Numéro d'article manquant")
    
    # 3. Longueur de la réponse
    if len(response) < 50:
        score -= 2
        issues.append("Réponse trop courte")
    elif len(response) > 500:
        score -= 1
        issues.append("Réponse trop longue")
    
    # 4. Temps de réponse
    if response_time > 5.0:
        score -= 1
        issues.append("Réponse lente")
    
    # 5. Cohérence
    if "désolé" in response.lower() or "impossible" in response.lower():
        score -= 3
        issues.append("Réponse d'échec")
    
    # 6. Spécificité
    if "général" in response.lower() and "spécifique" in question.lower():
        score -= 2
        issues.append("Manque de spécificité")
    
    return {
        "score": max(0, score),
        "issues": issues,
        "response_time": response_time,
        "response_length": len(response)
    }

def generate_recommendations(results: dict, issue_counts: dict) -> list:
    """Génère des recommandations d'amélioration"""
    recommendations = []
    
    # Recommandations basées sur les problèmes identifiés
    if "Contenu non pertinent" in issue_counts:
        recommendations.append("Améliorer l'algorithme de recherche sémantique")
    
    if "Numéro d'article manquant" in issue_counts:
        recommendations.append("Renforcer la détection des références d'articles")
    
    if "Réponse d'échec" in issue_counts:
        recommendations.append("Implémenter un système de fallback pour les questions non trouvées")
    
    if "Manque de spécificité" in issue_counts:
        recommendations.append("Améliorer la génération de réponses contextuelles")
    
    # Recommandations générales
    recommendations.extend([
        "Ajouter plus de données d'entraînement pour améliorer la compréhension",
        "Implémenter un système de feedback utilisateur",
        "Optimiser les prompts pour l'API OpenAI",
        "Ajouter un système de cache plus intelligent",
        "Créer des templates de réponses pour les questions fréquentes"
    ])
    
    return recommendations

if __name__ == "__main__":
    success = critique_ia_system()
    if success:
        logger.info("\n🎉 Analyse critique terminée!")
    else:
        logger.error("❌ Analyse critique échouée!")
        sys.exit(1)
