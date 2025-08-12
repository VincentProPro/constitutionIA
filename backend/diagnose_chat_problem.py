#!/usr/bin/env python3
"""
Script de diagnostic pour le problème du chat
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.constitution import Constitution
from app.models.pdf_import import Article
from app.services.pdf_analyzer import PDFAnalyzer
from app.services.optimized_ai_service import OptimizedAIService
from app.core.config import settings

def diagnose_chat_problem():
    """Diagnostiquer le problème du chat"""
    
    print("🔍 Diagnostic du problème du chat")
    print("=" * 50)
    
    # 1. Vérifier les constitutions et articles
    print("\n1️⃣ Vérification des données en base:")
    db = SessionLocal()
    
    try:
        constitutions = db.query(Constitution).filter(Constitution.is_active == True).all()
        print(f"   📊 Constitutions actives: {len(constitutions)}")
        
        total_articles = 0
        for const in constitutions:
            articles_count = db.query(Article).filter(Article.constitution_id == const.id).count()
            total_articles += articles_count
            print(f"      📄 {const.title}: {articles_count} articles")
        
        print(f"   📊 Total des articles: {total_articles}")
        
        if total_articles == 0:
            print("   ❌ PROBLÈME: Aucun article en base!")
            return
        
        # 2. Tester l'extraction PDF
        print("\n2️⃣ Test d'extraction PDF:")
        
        pdf_analyzer = PDFAnalyzer(settings.OPENAI_API_KEY)
        
        for const in constitutions:
            if const.file_path and Path(const.file_path).exists():
                print(f"   📄 Test de: {const.title}")
                print(f"      Fichier: {const.file_path}")
                
                # Test d'extraction
                extracted_text = pdf_analyzer.extract_text_from_pdf(const.file_path)
                print(f"      Caractères extraits: {len(extracted_text)}")
                
                if len(extracted_text) == 0:
                    print("      ❌ PROBLÈME: Aucun texte extrait!")
                else:
                    print(f"      ✅ Texte extrait: {extracted_text[:100]}...")
                print()
        
        # 3. Tester le service IA
        print("\n3️⃣ Test du service IA:")
        
        try:
            ai_service = OptimizedAIService()
            
            # Test de chargement des documents
            print("   📚 Test de chargement des documents...")
            documents = ai_service._load_pdf_documents()
            print(f"      Documents chargés: {len(documents)}")
            
            if len(documents) == 0:
                print("      ❌ PROBLÈME: Aucun document chargé!")
            else:
                print("      ✅ Documents chargés avec succès")
                print(f"      📋 Exemples: {[doc.metadata.get('article_number', 'N/A') for doc in documents[:3]]}")
            
        except Exception as e:
            print(f"      ❌ Erreur service IA: {e}")
        
        # 4. Test de recherche directe
        print("\n4️⃣ Test de recherche directe:")
        
        # Recherche de l'article 44
        article_44 = db.query(Article).filter(
            Article.article_number.like('%44%'),
            Article.constitution_id.in_([c.id for c in constitutions])
        ).all()
        
        print(f"   🔍 Article 44 trouvé: {len(article_44)} articles")
        
        for article in article_44:
            constitution = db.query(Constitution).filter(Constitution.id == article.constitution_id).first()
            print(f"      📄 {article.article_number} - {constitution.title}")
            print(f"         Contenu: {article.content[:100]}...")
            print()
        
        # 5. Recommandations
        print("\n5️⃣ Recommandations:")
        
        if total_articles == 0:
            print("   🔧 SOLUTION: Réextraire les articles des PDF")
            print("      Exécuter: python fix_articles_constitution_links.py")
        
        if len(documents) == 0:
            print("   🔧 SOLUTION: Recharger la base vectorielle")
            print("      Appeler l'endpoint: POST /api/ai/refresh-vector-db")
        
        print("\n   🔧 SOLUTION: Redémarrer le backend")
        print("      Arrêter et relancer: python -m uvicorn app.main:app --reload")
        
        print("\n✅ Diagnostic terminé!")
        
    except Exception as e:
        print(f"❌ Erreur lors du diagnostic: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    diagnose_chat_problem()
