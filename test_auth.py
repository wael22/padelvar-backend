#!/usr/bin/env python3
"""
Script de test pour vérifier l'authentification
"""
import requests
import json

# URL de base du serveur
BASE_URL = "http://localhost:5000"

def test_authentication():
    """Test de l'authentification complète"""
    print("🔍 Test de l'authentification PadelVar")
    print("=" * 50)
    
    # Données de connexion
    login_data = {
        "email": "player@test.com",
        "password": "password123"
    }
    
    # Créer une session pour maintenir les cookies
    session = requests.Session()
    
    try:
        # 1. Test de connexion
        print("1. 🔐 Test de connexion...")
        response = session.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Connexion réussie pour: {data.get('user', {}).get('name', 'N/A')}")
            print(f"   Rôle: {data.get('user', {}).get('role', 'N/A')}")
        else:
            print(f"   ❌ Échec de connexion: {response.text}")
            return
        
        # 2. Test des routes de debug
        print("\n2. 🛠️ Test des routes de debug...")
        
        # Test session debug
        response = session.get(f"{BASE_URL}/api/players/debug/session")
        print(f"   Debug session - Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Session data: {response.json()}")
        else:
            print(f"   ❌ Session debug failed: {response.text}")
        
        # Test auth debug
        response = session.get(f"{BASE_URL}/api/players/debug/auth")
        print(f"   Debug auth - Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Auth data: {response.json()}")
        else:
            print(f"   ❌ Auth debug failed: {response.text}")
        
        # 3. Test des routes players problématiques
        print("\n3. 🎯 Test des routes players...")
        
        # Test clubs disponibles
        response = session.get(f"{BASE_URL}/api/players/clubs/available")
        print(f"   Clubs disponibles - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ {len(data.get('clubs', []))} clubs trouvés")
        else:
            print(f"   ❌ Clubs disponibles failed: {response.text}")
        
        # Test clubs suivis
        response = session.get(f"{BASE_URL}/api/players/clubs/followed")
        print(f"   Clubs suivis - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ {len(data.get('clubs', []))} clubs suivis")
        else:
            print(f"   ❌ Clubs suivis failed: {response.text}")
        
        # 4. Test dashboard player
        print("\n4. 📊 Test dashboard...")
        response = session.get(f"{BASE_URL}/api/players/dashboard")
        print(f"   Dashboard - Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Dashboard accessible")
        else:
            print(f"   ❌ Dashboard failed: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur. Assurez-vous que Flask est en cours d'exécution.")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")

if __name__ == "__main__":
    test_authentication()
