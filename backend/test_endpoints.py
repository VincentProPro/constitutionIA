#!/usr/bin/env python3
"""
Script de test pour les endpoints du backend
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoints():
    """Teste les endpoints du backend"""
    print("🧪 Test des endpoints du backend")
    print("=" * 40)
    
    # Test 1: Vérifier que le serveur répond
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ Serveur accessible")
        else:
            print(f"❌ Serveur répond avec code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur")
        print("   Assurez-vous que le backend est démarré: python -m uvicorn main:app --reload")
        return False
    
    # Test 2: Lister les fichiers PDF
    try:
        response = requests.get(f"{BASE_URL}/api/constitutions/files/list")
        if response.status_code == 200:
            files = response.json()
            print(f"✅ Endpoint /files/list fonctionne ({len(files)} fichiers)")
            for file in files:
                print(f"   - {file['filename']}")
        else:
            print(f"❌ Endpoint /files/list échoue: {response.status_code}")
            print(f"   Réponse: {response.text}")
    except Exception as e:
        print(f"❌ Erreur lors du test /files/list: {e}")
    
    # Test 3: Lister les constitutions depuis la DB
    try:
        response = requests.get(f"{BASE_URL}/api/constitutions/db/list")
        if response.status_code == 200:
            constitutions = response.json()
            print(f"✅ Endpoint /db/list fonctionne ({len(constitutions)} constitutions)")
            for constitution in constitutions:
                print(f"   - {constitution.get('title', 'N/A')} ({constitution.get('filename', 'N/A')})")
        else:
            print(f"❌ Endpoint /db/list échoue: {response.status_code}")
            print(f"   Réponse: {response.text}")
    except Exception as e:
        print(f"❌ Erreur lors du test /db/list: {e}")
    
    # Test 4: Analyser les fichiers
    try:
        response = requests.post(f"{BASE_URL}/api/constitutions/analyze-files")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Endpoint /analyze-files fonctionne")
            print(f"   Message: {result.get('message', 'N/A')}")
            processed_files = result.get('processed_files', [])
            if processed_files:
                print(f"   Fichiers traités: {len(processed_files)}")
                for file in processed_files:
                    print(f"     - {file.get('filename', 'N/A')}: {file.get('title', 'N/A')}")
            else:
                print("   Aucun nouveau fichier à traiter")
        else:
            print(f"❌ Endpoint /analyze-files échoue: {response.status_code}")
            print(f"   Réponse: {response.text}")
    except Exception as e:
        print(f"❌ Erreur lors du test /analyze-files: {e}")
    
    print("\n" + "=" * 40)
    print("🎯 Résumé des tests")
    print("Si tous les tests sont passés, le backend fonctionne correctement.")
    print("Si certains tests échouent, vérifiez:")
    print("1. Que le backend est démarré")
    print("2. Que la base de données est initialisée")
    print("3. Que les fichiers PDF sont dans le dossier 'Fichier'")
    print("4. Que OPENAI_API_KEY est configurée dans .env")

if __name__ == "__main__":
    test_endpoints() 