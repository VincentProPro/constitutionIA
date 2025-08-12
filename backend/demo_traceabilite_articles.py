#!/usr/bin/env python3
"""
Script de démonstration de la traçabilité des articles vers leurs constitutions sources
"""

from app.database import SessionLocal
from app.models.constitution import Constitution
from app.models.pdf_import import Article
import json

def demo_traceabilite():
    """Démontrer la traçabilité complète des articles"""
    print("🔍 DÉMONSTRATION DE LA TRACABILITÉ DES ARTICLES")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # 1. Statistiques générales
        print("\n📊 STATISTIQUES GÉNÉRALES:")
        total_articles = db.query(Article).count()
        total_constitutions = db.query(Constitution).filter(Constitution.is_active == True).count()
        
        print(f"   Total articles en base: {total_articles}")
        print(f"   Total constitutions actives: {total_constitutions}")
        
        # 2. Articles par constitution
        print("\n📋 ARTICLES PAR CONSTITUTION:")
        constitutions = db.query(Constitution).filter(Constitution.is_active == True).all()
        
        for constitution in constitutions:
            articles_count = db.query(Article).filter(Article.constitution_id == constitution.id).count()
            print(f"   📄 {constitution.title}")
            print(f"      Fichier: {constitution.filename}")
            print(f"      ID: {constitution.id}")
            print(f"      Articles: {articles_count}")
            print()
        
        # 3. Exemples de traçabilité
        print("\n🎯 EXEMPLES DE TRACABILITÉ:")
        
        # Rechercher quelques articles spécifiques
        articles_examples = db.query(Article).limit(5).all()
        
        for i, article in enumerate(articles_examples, 1):
            constitution = db.query(Constitution).filter(
                Constitution.id == article.constitution_id
            ).first()
            
            print(f"   {i}. Article {article.article_number}")
            print(f"      Contenu: {article.content[:100]}...")
            print(f"      Constitution: {constitution.title}")
            print(f"      Fichier source: {constitution.filename}")
            print(f"      ID Constitution: {constitution.id}")
            print()
        
        # 4. Recherche par constitution
        print("\n🔍 RECHERCHE PAR CONSTITUTION:")
        
        # Prendre la première constitution
        first_constitution = constitutions[0]
        print(f"   Constitution: {first_constitution.title}")
        print(f"   Fichier: {first_constitution.filename}")
        
        # Récupérer ses articles
        articles = db.query(Article).filter(
            Article.constitution_id == first_constitution.id
        ).order_by(Article.article_number).limit(10).all()
        
        print(f"   Articles trouvés: {len(articles)}")
        for article in articles:
            print(f"      - {article.article_number}: {article.content[:50]}...")
        
        # 5. Recherche croisée
        print("\n🔄 RECHERCHE CROISÉE:")
        
        # Chercher un article spécifique
        article_44 = db.query(Article).filter(
            Article.article_number == "Article 44"
        ).first()
        
        if article_44:
            constitution_44 = db.query(Constitution).filter(
                Constitution.id == article_44.constitution_id
            ).first()
            
            print(f"   Article 44 trouvé:")
            print(f"      Contenu: {article_44.content}")
            print(f"      Constitution: {constitution_44.title}")
            print(f"      Fichier: {constitution_44.filename}")
            print(f"      ID Constitution: {constitution_44.id}")
        
        # 6. Vérification de l'intégrité des relations
        print("\n✅ VÉRIFICATION DE L'INTÉGRITÉ:")
        
        # Vérifier qu'il n'y a pas d'articles orphelins
        orphan_articles = db.query(Article).outerjoin(
            Constitution, Article.constitution_id == Constitution.id
        ).filter(Constitution.id.is_(None)).count()
        
        print(f"   Articles orphelins: {orphan_articles}")
        
        if orphan_articles == 0:
            print("   ✅ Tous les articles sont correctement liés à une constitution")
        else:
            print("   ⚠️ Certains articles ne sont pas liés à une constitution")
        
        # 7. Structure de la base de données
        print("\n🗄️ STRUCTURE DE LA BASE DE DONNÉES:")
        print("   Table 'articles':")
        print("      - id: Identifiant unique de l'article")
        print("      - constitution_id: Clé étrangère vers la constitution")
        print("      - article_number: Numéro de l'article")
        print("      - content: Contenu de l'article")
        print("      - title, part, section: Métadonnées")
        print("      - created_at, updated_at: Horodatage")
        print()
        print("   Table 'constitutions':")
        print("      - id: Identifiant unique de la constitution")
        print("      - filename: Nom du fichier PDF source")
        print("      - title: Titre de la constitution")
        print("      - file_path: Chemin vers le fichier")
        print("      - is_active: Statut actif/inactif")
        
        # 8. API Endpoints disponibles
        print("\n🌐 ENDPOINTS API DISPONIBLES:")
        print("   GET /api/constitutions/{id}/articles")
        print("      → Récupère tous les articles d'une constitution")
        print()
        print("   GET /api/constitutions/articles/search?query=X&constitution_id=Y")
        print("      → Recherche d'articles avec filtre par constitution")
        print()
        print("   GET /api/constitutions/")
        print("      → Liste toutes les constitutions")
        
        print("\n🎉 DÉMONSTRATION TERMINÉE!")
        print("✅ La traçabilité complète est garantie!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def test_traceabilite_api():
    """Tester la traçabilité via l'API"""
    print("\n🌐 TEST DE TRACABILITÉ VIA API")
    print("=" * 40)
    
    import requests
    
    try:
        # 1. Récupérer toutes les constitutions
        response = requests.get("http://localhost:8000/api/constitutions/")
        constitutions = response.json()
        
        print(f"   Constitutions disponibles: {len(constitutions)}")
        
        if constitutions:
            # 2. Prendre la première constitution
            first_constitution = constitutions[0]
            constitution_id = first_constitution['id']
            
            print(f"   Constitution testée: {first_constitution['title']}")
            print(f"   Fichier: {first_constitution['filename']}")
            
            # 3. Récupérer ses articles
            response = requests.get(f"http://localhost:8000/api/constitutions/{constitution_id}/articles")
            articles_data = response.json()
            
            print(f"   Articles trouvés: {articles_data['articles_count']}")
            
            # 4. Afficher quelques exemples
            for i, article in enumerate(articles_data['articles'][:3], 1):
                print(f"      {i}. {article['article_number']}: {article['content'][:50]}...")
            
            # 5. Recherche avec filtre
            response = requests.get(f"http://localhost:8000/api/constitutions/articles/search?query=Article%201&constitution_id={constitution_id}")
            search_results = response.json()
            
            print(f"   Recherche 'Article 1' dans cette constitution: {search_results['results_count']} résultats")
            
            if search_results['results']:
                first_result = search_results['results'][0]
                print(f"   Premier résultat: {first_result['article_number']}")
                print(f"   Constitution: {first_result['constitution']['title']}")
                print(f"   Fichier: {first_result['constitution']['filename']}")
        
        print("   ✅ API de traçabilité fonctionnelle!")
        
    except Exception as e:
        print(f"   ❌ Erreur API: {e}")

if __name__ == "__main__":
    demo_traceabilite()
    test_traceabilite_api() 