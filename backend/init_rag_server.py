#!/usr/bin/env python3
"""
Script pour initialiser le RAG sur le serveur en ligne
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.optimized_ai_service import OptimizedAIService
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Initialise le système RAG sur le serveur"""
    try:
        logger.info("🚀 Initialisation du système RAG sur le serveur...")
        
        # Créer l'instance du service IA
        ai_service = OptimizedAIService()
        
        # Forcer l'initialisation du RAG
        logger.info("📚 Initialisation du RAG...")
        success = ai_service._initialize_rag_lazy()
        
        if success:
            logger.info("✅ RAG initialisé avec succès!")
            
            # Test avec une requête simple
            logger.info("🧪 Test du RAG avec une requête...")
            response = ai_service.generate_response("Qu'est-ce que la constitution?", "test.pdf")
            logger.info(f"📝 Réponse de test: {response['answer'][:100]}...")
            
            # Afficher le statut final
            status = ai_service.get_system_status()
            logger.info(f"📊 Statut final: {status}")
            
        else:
            logger.error("❌ Échec de l'initialisation du RAG")
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 