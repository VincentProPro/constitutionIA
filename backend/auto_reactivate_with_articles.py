#!/usr/bin/env python3
"""
Script pour réactiver automatiquement une constitution et importer ses articles
"""

import requests
import json
import time
import subprocess
import sys

BASE_URL = "http://localhost:8000"

def auto_reactivate_constitution():
    """Réactiver automatiquement une constitution et importer ses articles"""
    
    print("🔄 Réactivation automatique avec import d'articles")
    print("=" * 50)
    
    # 1. Vérifier s'il y a des constitutions actives
    print("\n1️⃣ Vérification des constitutions actives:")
    response = requests.get(f"{BASE_URL}/api/constitutions/")
    if response.status_code == 200:
        active_constitutions = response.json()
        print(f"   📊 Constitutions actives: {len(active_constitutions)}")
        
        if len(active_constitutions) > 0:
            print("   ✅ Il y a déjà des constitutions actives")
            for const in active_constitutions:
                print(f"      📄 {const['title']} (ID: {const['id']})")
            return
    else:
        print(f"   ❌ Erreur: {response.status_code}")
        return
    
    # 2. Si aucune constitution active, réactiver la plus récente
    print("\n2️⃣ Aucune constitution active trouvée. Réactivation automatique:")
    response = requests.get(f"{BASE_URL}/api/constitutions/all")
    if response.status_code == 200:
        all_constitutions = response.json()
        inactive_constitutions = [c for c in all_constitutions if not c['is_active']]
        
        if len(inactive_constitutions) == 0:
            print("   ❌ Aucune constitution inactive trouvée")
            return
        
        # Prendre la plus récente
        latest_constitution = max(inactive_constitutions, key=lambda x: x.get('created_at', ''))
        print(f"   📄 Réactivation de: {latest_constitution['title']} (ID: {latest_constitution['id']})")
        
        # Réactiver la constitution
        response = requests.post(f"{BASE_URL}/api/constitutions/{latest_constitution['id']}/reactivate")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Réactivation réussie")
            print(f"   📝 Message: {result.get('message', 'N/A')}")
        else:
            print(f"   ❌ Erreur lors de la réactivation: {response.status_code}")
            return
    
    # 3. Importer les articles
    print("\n3️⃣ Import des articles:")
    try:
        print("   🔄 Lancement de fix_articles_constitution_links.py...")
        result = subprocess.run([sys.executable, "fix_articles_constitution_links.py"], 
                              capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print("   ✅ Import des articles réussi")
            print("   📄 Sortie:")
            for line in result.stdout.split('\n')[-10:]:  # Afficher les 10 dernières lignes
                if line.strip():
                    print(f"      {line}")
        else:
            print("   ❌ Erreur lors de l'import des articles")
            print(f"   📝 Erreur: {result.stderr}")
    except Exception as e:
        print(f"   ❌ Exception lors de l'import: {e}")
    
    # 4. Vérifier le résultat
    print("\n4️⃣ Vérification finale:")
    response = requests.get(f"{BASE_URL}/api/constitutions/")
    if response.status_code == 200:
        active_constitutions = response.json()
        print(f"   📊 Constitutions actives: {len(active_constitutions)}")
        for const in active_constitutions:
            print(f"      📄 {const['title']} (ID: {const['id']})")
    
    # 5. Test du chat
    if len(active_constitutions) > 0:
        print("\n5️⃣ Test du chat:")
        constitution = active_constitutions[0]
        chat_data = {
            "question": "Quelle est la durée du mandat présidentiel?",
            "filename": constitution['filename']
        }
        
        response = requests.post(f"{BASE_URL}/api/ai/chat/pdf", json=chat_data)
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Chat fonctionnel")
            print(f"   💬 Réponse: {result.get('response', 'N/A')[:100]}...")
        else:
            print(f"   ❌ Erreur chat: {response.status_code}")
            print(f"   📝 Détail: {response.text}")
    
    print("\n✅ Réactivation automatique terminée!")

if __name__ == "__main__":
    try:
        auto_reactivate_constitution()
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur. Assurez-vous que le backend est démarré.")
    except Exception as e:
        print(f"❌ Erreur: {e}")
