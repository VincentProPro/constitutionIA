#!/usr/bin/env python3
"""
Script pour corriger les liens entre articles et constitutions
et démontrer l'avantage des données stockées en base
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.constitution import Constitution
from app.models.pdf_import import Article
from app.services.pdf_import import PDFImporter

def fix_articles_constitution_links():
    """Corriger les liens entre articles et constitutions"""
    
    print("🔧 Correction des liens entre articles et constitutions")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # 1. Analyser la situation actuelle
        print("\n1️⃣ Analyse de la situation actuelle:")
        
        # Constitutions actives
        constitutions = db.query(Constitution).filter(Constitution.is_active == True).all()
        print(f"   📊 Constitutions actives: {len(constitutions)}")
        for const in constitutions:
            print(f"      📄 ID {const.id}: {const.title}")
        
        # Articles orphelins (sans constitution valide)
        orphan_articles = db.query(Article).filter(
            ~Article.constitution_id.in_([c.id for c in constitutions])
        ).all()
        print(f"   📊 Articles orphelins: {len(orphan_articles)}")
        
        # Articles par constitution
        for const in constitutions:
            articles_count = db.query(Article).filter(Article.constitution_id == const.id).count()
            print(f"      📄 {const.title}: {articles_count} articles")
        
        # 2. Traiter chaque constitution active
        print("\n2️⃣ Traitement des constitutions actives:")
        
        for constitution in constitutions:
            print(f"\n   🔄 Traitement de: {constitution.title}")
            
            # Vérifier si des articles existent déjà
            existing_articles = db.query(Article).filter(Article.constitution_id == constitution.id).count()
            
            if existing_articles > 0:
                print(f"      ✅ {existing_articles} articles déjà présents")
                continue
            
            # Vérifier si le fichier PDF existe
            if not constitution.file_path or not Path(constitution.file_path).exists():
                print(f"      ⚠️ Fichier PDF non trouvé: {constitution.file_path}")
                continue
            
            print(f"      📄 Extraction depuis: {constitution.file_path}")
            
            # Extraire les articles du PDF
            importer = PDFImporter(db)
            result = importer.process_pdf_file(constitution.id, constitution.file_path)
            
            if result['success']:
                print(f"      ✅ {result['articles_count']} articles extraits et sauvegardés")
            else:
                print(f"      ❌ Erreur: {result.get('error', 'Erreur inconnue')}")
        
        # 3. Vérifier les résultats
        print("\n3️⃣ Vérification des résultats:")
        
        total_articles = 0
        for const in constitutions:
            articles_count = db.query(Article).filter(Article.constitution_id == const.id).count()
            total_articles += articles_count
            print(f"   📄 {const.title}: {articles_count} articles")
        
        print(f"   📊 Total des articles: {total_articles}")
        
        # 4. Test de recherche rapide
        print("\n4️⃣ Test de recherche rapide en base:")
        
        # Recherche par article spécifique
        article_44 = db.query(Article).filter(
            Article.article_number.like('%44%'),
            Article.constitution_id.in_([c.id for c in constitutions])
        ).all()
        
        print(f"   🔍 Article 44 trouvé dans {len(article_44)} constitution(s):")
        for article in article_44:
            constitution = db.query(Constitution).filter(Constitution.id == article.constitution_id).first()
            print(f"      📄 {article.article_number} - {constitution.title}")
            print(f"         Contenu: {article.content[:100]}...")
            print()
        
        # Recherche par mot-clé
        search_term = "souveraineté"
        matching_articles = db.query(Article).filter(
            Article.content.like(f'%{search_term}%'),
            Article.constitution_id.in_([c.id for c in constitutions])
        ).limit(3).all()
        
        print(f"   🔍 Articles contenant '{search_term}': {len(matching_articles)}")
        for article in matching_articles:
            constitution = db.query(Constitution).filter(Constitution.id == article.constitution_id).first()
            print(f"      📄 {article.article_number} - {constitution.title}")
            # Trouver le contexte
            content_lower = article.content.lower()
            term_pos = content_lower.find(search_term.lower())
            if term_pos != -1:
                start = max(0, term_pos - 50)
                end = min(len(article.content), term_pos + len(search_term) + 50)
                context = article.content[start:end]
                print(f"         Contexte: ...{context}...")
            print()
        
        # 5. Démonstration des avantages
        print("\n5️⃣ Démonstration des avantages:")
        print("   🚀 RAPIDITÉ:")
        print("      - Les articles sont déjà extraits et structurés")
        print("      - Pas besoin de relire les fichiers PDF")
        print("      - Recherche directe en base de données")
        
        print("\n   🎯 PRÉCISION:")
        print("      - Articles parsés individuellement")
        print("      - Métadonnées complètes (numéro, titre, partie, section)")
        print("      - Contexte préservé")
        
        print("\n   📚 RICHESSE:")
        print("      - Recherche par article spécifique")
        print("      - Recherche par thème/mot-clé")
        print("      - Recherche par constitution")
        print("      - Historique des versions")
        
        print("\n   💾 EFFICACITÉ:")
        print("      - Base vectorielle persistante")
        print("      - Cache des réponses")
        print("      - Mise à jour automatique après upload")
        
        print("\n✅ Correction et démonstration terminées!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    
    finally:
        db.close()

if __name__ == "__main__":
    fix_articles_constitution_links()
