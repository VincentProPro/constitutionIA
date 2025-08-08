#!/usr/bin/env python3
"""
Script de débogage pour initialiser le RAG
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.optimized_ai_service import OptimizedAIService
import logging

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("🚀 Initialisation du RAG - Mode Debug")
    print("=" * 50)
    
    try:
        # Créer l'instance du service
        print("1. Création du service IA...")
        ai_service = OptimizedAIService()
        
        print(f"2. Clé API configurée: {'OUI' if ai_service.openai_api_key else 'NON'}")
        print(f"3. État initial: is_initialized = {ai_service.is_initialized}")
        
        # Vérifier les fichiers PDF
        print("\n4. Vérification des fichiers PDF...")
        import os
        pdf_dir = "Fichier/"
        if os.path.exists(pdf_dir):
            pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
            print(f"   Fichiers PDF trouvés: {pdf_files}")
        else:
            print("   ❌ Répertoire Fichier/ non trouvé")
            return
        
        # Forcer l'initialisation
        print("\n5. Tentative d'initialisation du RAG...")
        success = ai_service._initialize_rag_lazy()
        print(f"   Résultat: {success}")
        
        if success:
            print(f"   - Embeddings: {ai_service.embeddings is not None}")
            print(f"   - LLM: {ai_service.llm is not None}")
            print(f"   - Vector DB: {ai_service.vector_db is not None}")
            print(f"   - QA Chain: {ai_service.qa_chain is not None}")
            print(f"   - is_initialized: {ai_service.is_initialized}")
            
            # Test d'une requête
            print("\n6. Test d'une requête RAG...")
            test_query = "Quels sont les droits fondamentaux dans la constitution ?"
            response = ai_service._rag_search_optimized(test_query)
            print(f"   Réponse: {response.get('answer', 'Aucune réponse')[:100]}...")
            print(f"   Méthode: {response.get('method', 'N/A')}")
            print(f"   Confiance: {response.get('confidence', 0)}")
        else:
            print("   ❌ Échec de l'initialisation")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 