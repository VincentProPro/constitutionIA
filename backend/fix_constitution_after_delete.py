#!/usr/bin/env python3
"""
Script simple pour réactiver automatiquement une constitution après suppression
Usage: python fix_constitution_after_delete.py
"""

import requests
import json
import subprocess
import sys

BASE_URL = "http://localhost:8000"

def main():
    """Fonction principale"""
    
    print("🔧 Réparation automatique après suppression de constitution")
    print("=" * 55)
    
    # 1. Vérifier s'il y a des constitutions actives
    print("\n1️⃣ Vérification de l'état actuel...")
    try:
        response = requests.get(f"{BASE_URL}/api/constitutions/")
        if response.status_code == 200:
            active_constitutions = response.json()
            if len(active_constitutions) > 0:
                print("   ✅ Il y a déjà des constitutions actives:")
                for const in active_constitutions:
                    print(f"      📄 {const['title']}")
                print("\n   💡 Le système fonctionne correctement!")
                return
            else:
                print("   ❌ Aucune constitution active trouvée")
        else:
            print(f"   ❌ Erreur de connexion: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("   ❌ Impossible de se connecter au serveur")
        print("   💡 Assurez-vous que le backend est démarré")
        return
    
    # 2. Réactiver automatiquement une constitution
    print("\n2️⃣ Réactivation automatique d'une constitution...")
    try:
        response = requests.get(f"{BASE_URL}/api/constitutions/all")
        if response.status_code == 200:
            all_constitutions = response.json()
            inactive_constitutions = [c for c in all_constitutions if not c['is_active']]
            
            if len(inactive_constitutions) == 0:
                print("   ❌ Aucune constitution inactive trouvée")
                return
            
            # Prendre la plus récente
            latest_constitution = max(inactive_constitutions, key=lambda x: x.get('created_at', ''))
            print(f"   📄 Réactivation de: {latest_constitution['title']}")
            
            # Réactiver
            response = requests.post(f"{BASE_URL}/api/constitutions/{latest_constitution['id']}/reactivate")
            if response.status_code == 200:
                print("   ✅ Constitution réactivée")
            else:
                print(f"   ❌ Erreur lors de la réactivation: {response.status_code}")
                return
        else:
            print(f"   ❌ Erreur: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return
    
    # 3. Vérifier si la constitution active a des articles
    print("\n3️⃣ Vérification des articles...")
    try:
        response = requests.get(f"{BASE_URL}/api/constitutions/")
        if response.status_code == 200:
            active_constitutions = response.json()
            if len(active_constitutions) > 0:
                constitution = active_constitutions[0]
                
                # Tester le chat pour voir s'il y a des articles
                chat_data = {
                    "question": "Test",
                    "filename": constitution['filename']
                }
                
                response = requests.post(f"{BASE_URL}/api/ai/chat/pdf", json=chat_data)
                if response.status_code == 200:
                    print("   ✅ Constitution active avec articles")
                    return  # Tout va bien
                elif "Aucun article trouvé" in response.text:
                    print("   ❌ Constitution active sans articles - Import nécessaire")
                else:
                    print(f"   ❌ Erreur chat: {response.status_code}")
                    return
            else:
                print("   ❌ Aucune constitution active")
                return
        else:
            print(f"   ❌ Erreur: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return
    
    # 4. Importer les articles si nécessaire
    print("\n4️⃣ Import des articles...")
    try:
        print("   🔄 Extraction et import des articles...")
        result = subprocess.run([sys.executable, "fix_articles_constitution_links.py"], 
                              capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print("   ✅ Articles importés avec succès")
        else:
            print("   ❌ Erreur lors de l'import des articles")
            print(f"   📝 Détail: {result.stderr}")
            return
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return
    
    # 5. Vérification finale
    print("\n5️⃣ Vérification finale...")
    try:
        response = requests.get(f"{BASE_URL}/api/constitutions/")
        if response.status_code == 200:
            final_constitutions = response.json()
            if len(final_constitutions) > 0:
                print("   ✅ Constitution active trouvée:")
                for const in final_constitutions:
                    print(f"      📄 {const['title']}")
                
                # Test du chat
                print("\n6️⃣ Test du chat...")
                constitution = final_constitutions[0]
                chat_data = {
                    "question": "Quelle est la durée du mandat présidentiel?",
                    "filename": constitution['filename']
                }
                
                response = requests.post(f"{BASE_URL}/api/ai/chat/pdf", json=chat_data)
                if response.status_code == 200:
                    result = response.json()
                    print("   ✅ Chat fonctionnel")
                    print(f"   💬 Réponse: {result.get('response', 'N/A')[:80]}...")
                else:
                    print(f"   ❌ Erreur chat: {response.status_code}")
            else:
                print("   ❌ Aucune constitution active après réparation")
        else:
            print(f"   ❌ Erreur: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print("\n✅ Réparation terminée!")

if __name__ == "__main__":
    main()
