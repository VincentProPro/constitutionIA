#!/usr/bin/env python3
"""
Diagnostic complet des problèmes de chat
"""

import requests
import json
import subprocess
import sys

BASE_URL = "http://localhost:8000"

def diagnose_chat_problem():
    """Diagnostic complet des problèmes de chat"""
    
    print("🔍 Diagnostic complet des problèmes de chat")
    print("=" * 50)
    
    # 1. Vérifier la connexion au serveur
    print("\n1️⃣ Test de connexion au serveur...")
    try:
        response = requests.get(f"{BASE_URL}/api/constitutions/")
        if response.status_code == 200:
            print("   ✅ Serveur accessible")
        else:
            print(f"   ❌ Erreur serveur: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("   ❌ Impossible de se connecter au serveur")
        print("   💡 Vérifiez que le backend est démarré")
        return
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return
    
    # 2. Vérifier les constitutions actives
    print("\n2️⃣ Vérification des constitutions actives...")
    try:
        response = requests.get(f"{BASE_URL}/api/constitutions/")
        active_constitutions = response.json()
        print(f"   📊 Constitutions actives: {len(active_constitutions)}")
        
        if len(active_constitutions) == 0:
            print("   ❌ Aucune constitution active")
            print("   💡 Réactivez une constitution")
            return
        
        for const in active_constitutions:
            print(f"      📄 {const['title']} (ID: {const['id']})")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return
    
    # 3. Vérifier les articles de chaque constitution active
    print("\n3️⃣ Vérification des articles...")
    for constitution in active_constitutions:
        print(f"   🔍 Constitution: {constitution['title']}")
        
        # Test du chat
        chat_data = {
            "question": "Test de diagnostic",
            "filename": constitution['filename']
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/ai/chat/pdf", json=chat_data)
            if response.status_code == 200:
                result = response.json()
                print(f"      ✅ Chat fonctionnel")
                print(f"      💬 Réponse: {result.get('response', 'N/A')[:50]}...")
            elif response.status_code == 404:
                error_detail = response.json().get('detail', '')
                if "Aucun article trouvé" in error_detail:
                    print(f"      ❌ Aucun article trouvé")
                    print(f"      💡 Importez les articles avec: python fix_articles_constitution_links.py")
                elif "non trouvée" in error_detail:
                    print(f"      ❌ Constitution non trouvée")
                else:
                    print(f"      ❌ Erreur 404: {error_detail}")
            else:
                print(f"      ❌ Erreur {response.status_code}: {response.text}")
        except Exception as e:
            print(f"      ❌ Erreur: {e}")
    
    # 4. Vérifier la base de données
    print("\n4️⃣ Vérification de la base de données...")
    try:
        result = subprocess.run([sys.executable, "check_available_articles.py"], 
                              capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print("   ✅ Vérification de la base réussie")
            # Afficher les dernières lignes importantes
            lines = result.stdout.split('\n')
            for line in lines[-10:]:
                if line.strip() and ('articles trouvés' in line or 'Aucun article' in line):
                    print(f"      {line}")
        else:
            print("   ❌ Erreur lors de la vérification de la base")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # 5. Recommandations
    print("\n5️⃣ Recommandations...")
    
    # Vérifier s'il y a des problèmes détectés
    has_problems = False
    
    # Si aucune constitution active
    if len(active_constitutions) == 0:
        has_problems = True
        print("   🔧 Aucune constitution active:")
        print("      → Utilisez: python fix_constitution_after_delete.py")
    
    # Si constitution active mais pas d'articles
    for constitution in active_constitutions:
        chat_data = {"question": "Test", "filename": constitution['filename']}
        try:
            response = requests.post(f"{BASE_URL}/api/ai/chat/pdf", json=chat_data)
            if response.status_code == 404 and "Aucun article trouvé" in response.text:
                has_problems = True
                print("   🔧 Constitution active sans articles:")
                print("      → Utilisez: python fix_articles_constitution_links.py")
                break
        except:
            pass
    
    if not has_problems:
        print("   ✅ Aucun problème détecté")
        print("   💡 Le chat devrait fonctionner correctement")
    
    print("\n✅ Diagnostic terminé!")

if __name__ == "__main__":
    diagnose_chat_problem()
