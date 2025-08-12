#!/usr/bin/env python3
"""
Script de démonstration du système d'articles
"""

from app.database import SessionLocal
from app.models.constitution import Constitution
from app.models.pdf_import import Article
from sqlalchemy import func

def demo_articles_system():
    """Démonstration du système d'articles"""
    db = SessionLocal()
    
    try:
        print("🎯 DÉMONSTRATION DU SYSTÈME D'ARTICLES")
        print("=" * 50)
        
        # 1. Statistiques générales
        print("\n📊 STATISTIQUES GÉNÉRALES:")
        total_constitutions = db.query(Constitution).filter(Constitution.is_active == True).count()
        total_articles = db.query(Article).count()
        
        print(f"   • Constitutions actives: {total_constitutions}")
        print(f"   • Articles extraits: {total_articles}")
        
        # 2. Articles par constitution
        print("\n📋 ARTICLES PAR CONSTITUTION:")
        constitutions = db.query(Constitution).filter(Constitution.is_active == True).all()
        
        for constitution in constitutions:
            article_count = db.query(Article).filter(Article.constitution_id == constitution.id).count()
            print(f"   • {constitution.title}: {article_count} articles")
        
        # 3. Exemples d'articles
        print("\n📄 EXEMPLES D'ARTICLES:")
        articles = db.query(Article).limit(5).all()
        
        for article in articles:
            constitution = db.query(Constitution).filter(Constitution.id == article.constitution_id).first()
            print(f"\n   Article: {article.article_number}")
            print(f"   Constitution: {constitution.title if constitution else 'Inconnue'}")
            print(f"   Contenu: {article.content[:100]}...")
            if article.part:
                print(f"   Partie: {article.part}")
            if article.section:
                print(f"   Section: {article.section}")
        
        # 4. Recherche d'exemple
        print("\n🔍 RECHERCHE D'EXEMPLE:")
        search_term = "droits"
        articles_found = db.query(Article).filter(
            Article.content.ilike(f"%{search_term}%")
        ).limit(3).all()
        
        print(f"   Recherche pour '{search_term}': {len(articles_found)} résultats")
        for article in articles_found:
            constitution = db.query(Constitution).filter(Constitution.id == article.constitution_id).first()
            print(f"   • {article.article_number} ({constitution.title if constitution else 'Inconnue'}): {article.content[:80]}...")
        
        print("\n✅ Démonstration terminée!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    demo_articles_system() 