#!/usr/bin/env python3
"""
Script pour analyser les articles orphelins et proposer des solutions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.constitution import Constitution
from app.models.pdf_import import Article
from collections import defaultdict

def analyze_orphan_articles():
    """Analyser les articles orphelins et proposer des solutions"""
    
    print("🔍 ANALYSE DES ARTICLES ORPHELINS")
    print("=" * 80)
    
    db = SessionLocal()
    
    try:
        # 1. Identifier les articles orphelins
        orphan_articles = db.query(Article).filter(
            ~Article.constitution_id.in_(
                db.query(Constitution.id)
            )
        ).all()
        
        print(f"📊 Articles orphelins: {len(orphan_articles)}")
        
        # 2. Analyser les IDs de constitutions manquantes
        missing_constitution_ids = set()
        articles_by_missing_id = defaultdict(list)
        
        for article in orphan_articles:
            missing_constitution_ids.add(article.constitution_id)
            articles_by_missing_id[article.constitution_id].append(article)
        
        print(f"📋 IDs de constitutions manquantes: {sorted(missing_constitution_ids)}")
        print()
        
        # 3. Analyser chaque ID manquant
        for constitution_id in sorted(missing_constitution_ids):
            articles = articles_by_missing_id[constitution_id]
            print(f"🏛️  Constitution ID {constitution_id}:")
            print(f"   📄 Articles: {len(articles)}")
            
            # Analyser les articles pour deviner le type de constitution
            article_numbers = [a.article_number for a in articles]
            unique_numbers = sorted(set(article_numbers), key=lambda x: int(x) if x.isdigit() else float('inf'))
            
            print(f"   📝 Numéros d'articles: {', '.join(unique_numbers[:10])}")
            if len(unique_numbers) > 10:
                print(f"      ... et {len(unique_numbers) - 10} autres")
            
            # Chercher l'article 44
            article_44 = next((a for a in articles if a.article_number == "44"), None)
            if article_44:
                print(f"   ✅ Article 44 trouvé!")
                print(f"      Contenu: {article_44.content[:100]}...")
            else:
                print(f"   ❌ Article 44 non trouvé")
            
            # Analyser le contenu pour deviner le type
            sample_articles = articles[:3]
            print(f"   📖 Exemples d'articles:")
            for article in sample_articles:
                print(f"      Article {article.article_number}: {article.content[:50]}...")
            
            print()
        
        # 4. Analyser les constitutions existantes
        print("📚 CONSTITUTIONS EXISTANTES")
        print("-" * 50)
        
        existing_constitutions = db.query(Constitution).order_by(Constitution.id).all()
        for constitution in existing_constitutions:
            articles_count = db.query(Article).filter(Article.constitution_id == constitution.id).count()
            print(f"ID {constitution.id}: {constitution.title}")
            print(f"   📄 Articles: {articles_count}")
            print(f"   📅 Créé: {constitution.created_at}")
            print(f"   📊 Statut: {constitution.status}")
            print()
        
        # 5. Proposer des solutions
        print("💡 SOLUTIONS PROPOSÉES")
        print("=" * 50)
        
        print("🔧 Problème identifié:")
        print("   - Les articles sont associés à des constitutions qui ont été supprimées")
        print("   - Il n'y a pas de contraintes de clé étrangère pour empêcher cela")
        print("   - Cela indique un problème de synchronisation dans le système")
        print()
        
        print("🛠️ Solutions possibles:")
        print()
        
        print("1. RECRÉER LES CONSTITUTIONS MANQUANTES:")
        print("   - Recréer les constitutions avec les IDs 33, 35, 36")
        print("   - Associer les articles existants à ces nouvelles constitutions")
        print("   - Avantage: Préserve les données existantes")
        print("   - Inconvénient: Peut créer des doublons")
        print()
        
        print("2. RÉASSIGNER LES ARTICLES:")
        print("   - Réassigner les articles aux constitutions existantes")
        print("   - Basé sur la similarité des noms de fichiers")
        print("   - Avantage: Nettoie la base de données")
        print("   - Inconvénient: Peut perdre des informations")
        print()
        
        print("3. SUPPRIMER LES ARTICLES ORPHELINS:")
        print("   - Supprimer tous les articles orphelins")
        print("   - Recommencer l'import des PDF")
        print("   - Avantage: Base de données propre")
        print("   - Inconvénient: Perte de données")
        print()
        
        print("4. AJOUTER DES CONTRAINTES DE CLÉ ÉTRANGÈRE:")
        print("   - Modifier le schéma de base de données")
        print("   - Ajouter ON DELETE CASCADE")
        print("   - Avantage: Évite les problèmes futurs")
        print("   - Inconvénient: Nécessite une migration")
        print()
        
        # 6. Recommandation
        print("🎯 RECOMMANDATION:")
        print("   Pour résoudre immédiatement le problème de test de l'article 44:")
        print("   - Utiliser la solution 1 (recréer les constitutions)")
        print("   - Cela permettra de tester l'IA immédiatement")
        print("   - Puis implémenter la solution 4 (contraintes FK) pour l'avenir")
        
        # 7. Statistiques pour l'article 44
        print()
        print("📊 STATISTIQUES ARTICLE 44:")
        print("-" * 30)
        
        article_44_count = 0
        for constitution_id in missing_constitution_ids:
            articles = articles_by_missing_id[constitution_id]
            article_44 = next((a for a in articles if a.article_number == "44"), None)
            if article_44:
                article_44_count += 1
                print(f"   Constitution ID {constitution_id}: Article 44 présent")
        
        print(f"   Total articles 44 dans les données orphelines: {article_44_count}")
        
        if article_44_count > 0:
            print("   ✅ L'article 44 est disponible dans les données orphelines")
            print("   💡 Il suffit de recréer les constitutions pour pouvoir tester")
        else:
            print("   ❌ Aucun article 44 trouvé dans les données orphelines")
            print("   💡 Il faudra d'abord importer des PDF contenant l'article 44")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    analyze_orphan_articles()
