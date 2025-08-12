#!/usr/bin/env python3
"""
Script pour nettoyer les articles orphelins après suppression d'une constitution
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.constitution import Constitution
from app.models.pdf_import import Article

def cleanup_orphaned_articles():
    """Nettoyer les articles orphelins"""
    
    print("🧹 Nettoyage des articles orphelins")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # 1. Identifier les constitutions actives
        active_constitutions = db.query(Constitution).filter(Constitution.is_active == True).all()
        active_constitution_ids = [c.id for c in active_constitutions]
        
        print(f"📊 Constitutions actives: {len(active_constitutions)}")
        for const in active_constitutions:
            print(f"   📄 ID {const.id}: {const.title}")
        
        # 2. Identifier les articles orphelins
        orphaned_articles = db.query(Article).filter(
            ~Article.constitution_id.in_(active_constitution_ids)
        ).all()
        
        print(f"\n📊 Articles orphelins trouvés: {len(orphaned_articles)}")
        
        if orphaned_articles:
            print("   📋 Détails des articles orphelins:")
            for article in orphaned_articles[:10]:  # Afficher les 10 premiers
                print(f"      - Article {article.article_number} (ID: {article.id}, Constitution ID: {article.constitution_id})")
            
            if len(orphaned_articles) > 10:
                print(f"      ... et {len(orphaned_articles) - 10} autres")
            
            # 3. Demander confirmation
            print(f"\n❓ Voulez-vous supprimer {len(orphaned_articles)} articles orphelins? (y/N): ", end="")
            response = input().strip().lower()
            
            if response == 'y' or response == 'yes':
                # 4. Supprimer les articles orphelins
                deleted_count = db.query(Article).filter(
                    ~Article.constitution_id.in_(active_constitution_ids)
                ).delete()
                
                db.commit()
                print(f"✅ {deleted_count} articles orphelins supprimés")
            else:
                print("❌ Suppression annulée")
        else:
            print("✅ Aucun article orphelin trouvé")
        
        # 5. Vérifier l'état final
        print("\n📊 État final:")
        total_articles = db.query(Article).count()
        print(f"   📄 Total des articles: {total_articles}")
        
        for const in active_constitutions:
            articles_count = db.query(Article).filter(Article.constitution_id == const.id).count()
            print(f"   📄 {const.title}: {articles_count} articles")
        
        print("\n✅ Nettoyage terminé!")
        
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_orphaned_articles()
