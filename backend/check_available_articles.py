#!/usr/bin/env python3
"""
Script pour vérifier quels articles sont disponibles dans la base de données
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.constitution import Constitution
from app.models.pdf_import import Article
from collections import defaultdict

def check_available_articles():
    """Vérifier quels articles sont disponibles dans la base de données"""
    
    print("🔍 Vérification des articles disponibles dans la base de données")
    print("=" * 80)
    
    db = SessionLocal()
    
    try:
        # Récupérer toutes les constitutions
        constitutions = db.query(Constitution).filter(Constitution.is_active == True).all()
        
        if not constitutions:
            print("❌ Aucune constitution active trouvée dans la base de données")
            return
        
        print(f"📚 {len(constitutions)} constitution(s) active(s) trouvée(s)")
        print()
        
        # Statistiques globales
        total_articles = db.query(Article).count()
        print(f"📊 Total d'articles dans la base: {total_articles}")
        
        # Articles par constitution
        articles_by_constitution = defaultdict(list)
        for constitution in constitutions:
            articles = db.query(Article).filter(Article.constitution_id == constitution.id).all()
            articles_by_constitution[constitution.id] = articles
        
        # Afficher les détails par constitution
        for constitution in constitutions:
            print(f"🏛️  Constitution: {constitution.title}")
            print(f"📄 Fichier: {constitution.filename}")
            print(f"🌍 Pays: {constitution.country}")
            print(f"📅 Année: {constitution.year}")
            print(f"📊 Statut: {constitution.status}")
            
            articles = articles_by_constitution[constitution.id]
            print(f"📋 Articles trouvés: {len(articles)}")
            
            if articles:
                # Grouper les articles par numéro
                article_numbers = [article.article_number for article in articles]
                unique_numbers = sorted(set(article_numbers), key=lambda x: int(x) if x.isdigit() else float('inf'))
                
                print(f"📝 Numéros d'articles: {', '.join(unique_numbers[:20])}")
                if len(unique_numbers) > 20:
                    print(f"   ... et {len(unique_numbers) - 20} autres")
                
                # Vérifier spécifiquement l'article 44
                article_44 = db.query(Article).filter(
                    Article.constitution_id == constitution.id,
                    Article.article_number == "44"
                ).first()
                
                if article_44:
                    print(f"✅ Article 44 trouvé!")
                    print(f"   Titre: {article_44.title or 'Aucun titre'}")
                    print(f"   Contenu: {article_44.content[:100]}...")
                else:
                    print("❌ Article 44 non trouvé")
                    
                    # Chercher des articles contenant "44"
                    articles_with_44 = [a for a in articles if '44' in a.article_number or '44' in (a.content or '')]
                    if articles_with_44:
                        print(f"🔍 Articles contenant '44':")
                        for article in articles_with_44[:3]:
                            print(f"   - Article {article.article_number}: {article.content[:50]}...")
            else:
                print("❌ Aucun article trouvé pour cette constitution")
            
            print("-" * 60)
            print()
        
        # Statistiques détaillées
        print("📊 STATISTIQUES DÉTAILLÉES")
        print("=" * 50)
        
        # Articles les plus fréquents
        article_counts = defaultdict(int)
        for articles in articles_by_constitution.values():
            for article in articles:
                article_counts[article.article_number] += 1
        
        print("📈 Articles les plus fréquents:")
        sorted_articles = sorted(article_counts.items(), key=lambda x: x[1], reverse=True)
        for article_num, count in sorted_articles[:10]:
            print(f"   Article {article_num}: {count} occurrence(s)")
        
        # Vérifier l'article 44 spécifiquement
        print(f"\n🎯 Article 44:")
        article_44_count = db.query(Article).filter(Article.article_number == "44").count()
        print(f"   Total d'articles 44: {article_44_count}")
        
        if article_44_count > 0:
            article_44_instances = db.query(Article).filter(Article.article_number == "44").all()
            for i, article in enumerate(article_44_instances, 1):
                constitution = db.query(Constitution).filter(Constitution.id == article.constitution_id).first()
                print(f"   {i}. Constitution: {constitution.title if constitution else 'Inconnue'}")
                print(f"      Contenu: {article.content[:100]}...")
        
        # Recommandations pour les tests
        print(f"\n💡 RECOMMANDATIONS POUR LES TESTS")
        print("=" * 50)
        
        if article_44_count > 0:
            print("✅ L'article 44 est disponible dans la base de données")
            print("   Vous pouvez utiliser les scripts de test pour interroger l'IA")
        else:
            print("❌ L'article 44 n'est pas disponible dans la base de données")
            print("   Suggestions:")
            
            # Trouver des articles similaires
            similar_articles = []
            for article_num in article_counts.keys():
                if article_num.isdigit() and 40 <= int(article_num) <= 50:
                    similar_articles.append(article_num)
            
            if similar_articles:
                print(f"   - Articles similaires disponibles: {', '.join(similar_articles)}")
                print(f"   - Vous pouvez tester avec ces articles à la place")
            
            # Trouver des articles avec du contenu
            articles_with_content = []
            for articles in articles_by_constitution.values():
                for article in articles:
                    if article.content and len(article.content) > 50:
                        articles_with_content.append(article.article_number)
                        break
            
            if articles_with_content:
                print(f"   - Articles avec contenu disponible: {', '.join(articles_with_content[:5])}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_available_articles()
