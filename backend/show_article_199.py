#!/usr/bin/env python3
"""
Script pour afficher les informations détaillées de l'article 199
"""

from app.database import SessionLocal
from app.models.constitution import Constitution
from app.models.pdf_import import Article
import json

def show_article_199():
    """Afficher les informations de l'article 199"""
    db = SessionLocal()
    
    try:
        print("📋 INFORMATIONS SUR L'ARTICLE 199")
        print("=" * 50)
        
        # Rechercher l'article 199
        article = db.query(Article).filter(
            Article.article_number == "Article 199",
            Article.constitution_id == 35  # ID de la constitution testée
        ).first()
        
        if not article:
            print("❌ Article 199 non trouvé")
            return
        
        # Récupérer les informations de la constitution
        constitution = db.query(Constitution).filter(
            Constitution.id == article.constitution_id
        ).first()
        
        print(f"\n📄 ARTICLE 199")
        print(f"   ID en base: {article.id}")
        print(f"   Numéro: {article.article_number}")
        print(f"   Titre: {article.title or 'Non spécifié'}")
        print(f"   Partie: {article.part or 'Non spécifiée'}")
        print(f"   Section: {article.section or 'Non spécifiée'}")
        print(f"   Page: {article.page_number or 'Non spécifiée'}")
        print(f"   Créé le: {article.created_at}")
        print(f"   Modifié le: {article.updated_at or 'Non modifié'}")
        
        print(f"\n📝 CONTENU COMPLET:")
        print(f"   {article.content}")
        
        print(f"\n📊 STATISTIQUES:")
        print(f"   Longueur du contenu: {len(article.content)} caractères")
        print(f"   Nombre de mots: {len(article.content.split())}")
        print(f"   Nombre de lignes: {len(article.content.split(chr(10)))}")
        
        print(f"\n📋 CONSTITUTION SOURCE:")
        print(f"   ID: {constitution.id}")
        print(f"   Titre: {constitution.title}")
        print(f"   Fichier: {constitution.filename}")
        print(f"   Statut: {constitution.status}")
        print(f"   Pays: {constitution.country}")
        print(f"   Année: {constitution.year or 'Non spécifiée'}")
        
        # Rechercher les articles voisins
        print(f"\n🔍 ARTICLES VOISINS:")
        prev_article = db.query(Article).filter(
            Article.constitution_id == article.constitution_id,
            Article.id < article.id
        ).order_by(Article.id.desc()).first()
        
        next_article = db.query(Article).filter(
            Article.constitution_id == article.constitution_id,
            Article.id > article.id
        ).order_by(Article.id.asc()).first()
        
        if prev_article:
            print(f"   Précédent: {prev_article.article_number} - {prev_article.content[:50]}...")
        else:
            print(f"   Précédent: Aucun")
            
        if next_article:
            print(f"   Suivant: {next_article.article_number} - {next_article.content[:50]}...")
        else:
            print(f"   Suivant: Aucun")
        
        # Rechercher des articles similaires (même longueur)
        similar_length = len(article.content)
        similar_articles = db.query(Article).filter(
            Article.constitution_id == article.constitution_id,
            Article.id != article.id,
            Article.content.like(f"%{similar_length}%")
        ).limit(3).all()
        
        if similar_articles:
            print(f"\n📊 ARTICLES DE LONGUEUR SIMILAIRE:")
            for sim_article in similar_articles:
                print(f"   {sim_article.article_number}: {len(sim_article.content)} caractères")
        
        # Analyse du contenu
        print(f"\n🔍 ANALYSE DU CONTENU:")
        content_lower = article.content.lower()
        
        # Mots-clés importants
        keywords = ["référendum", "promulgation", "président", "république", "journal officiel", "conakry", "plénière"]
        found_keywords = []
        
        for keyword in keywords:
            if keyword in content_lower:
                found_keywords.append(keyword)
        
        if found_keywords:
            print(f"   Mots-clés trouvés: {', '.join(found_keywords)}")
        
        # Date mentionnée
        if "2025" in article.content:
            print(f"   Date mentionnée: 2025")
        
        # Lieu mentionné
        if "conakry" in content_lower:
            print(f"   Lieu mentionné: Conakry")
        
        print(f"\n✅ Affichage terminé!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    show_article_199() 