#!/usr/bin/env python3
"""
Script pour afficher l'article 44 de toutes les constitutions stockées dans la base de données
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.pdf_import import Article
from app.models.constitution import Constitution
from sqlalchemy.orm import joinedload

def show_article_44():
    """Afficher l'article 44 de toutes les constitutions"""
    db = SessionLocal()
    
    try:
        print("🔍 Recherche de l'article 44 dans toutes les constitutions...")
        print("=" * 80)
        
        # Récupérer toutes les constitutions avec leurs articles
        constitutions = db.query(Constitution).filter(Constitution.is_active == True).all()
        
        if not constitutions:
            print("❌ Aucune constitution active trouvée dans la base de données")
            return
        
        print(f"📚 {len(constitutions)} constitution(s) active(s) trouvée(s)")
        print()
        
        for constitution in constitutions:
            print(f"🏛️  Constitution: {constitution.title}")
            print(f"📄 Fichier: {constitution.filename}")
            print(f"🌍 Pays: {constitution.country}")
            print(f"📅 Année: {constitution.year}")
            print(f"📊 Statut: {constitution.status}")
            print("-" * 60)
            
            # Rechercher l'article 44 pour cette constitution
            article_44 = db.query(Article).filter(
                Article.constitution_id == constitution.id,
                Article.article_number == "44"
            ).first()
            
            if article_44:
                print(f"✅ Article 44 trouvé!")
                print(f"📝 Titre: {article_44.title or 'Aucun titre'}")
                print(f"📄 Partie: {article_44.part or 'Non spécifiée'}")
                print(f"📋 Section: {article_44.section or 'Non spécifiée'}")
                print(f"📖 Page: {article_44.page_number or 'Non spécifiée'}")
                print()
                print("📜 Contenu:")
                print("=" * 40)
                print(article_44.content)
                print("=" * 40)
            else:
                print("❌ Article 44 non trouvé pour cette constitution")
                
                # Afficher les articles disponibles
                articles = db.query(Article).filter(
                    Article.constitution_id == constitution.id
                ).order_by(Article.article_number).limit(10).all()
                
                if articles:
                    print("📋 Articles disponibles (10 premiers):")
                    for article in articles:
                        print(f"  - Article {article.article_number}: {article.title or 'Sans titre'}")
                else:
                    print("📋 Aucun article trouvé pour cette constitution")
            
            print("\n" + "=" * 80 + "\n")
        
        # Statistiques globales
        print("📊 Statistiques globales:")
        total_articles = db.query(Article).count()
        article_44_count = db.query(Article).filter(Article.article_number == "44").count()
        print(f"  - Total d'articles: {total_articles}")
        print(f"  - Articles 44: {article_44_count}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la recherche: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    show_article_44() 