#!/usr/bin/env python3
"""
Test des endpoints clubs avec un vrai utilisateur de la base de données
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"

def test_with_real_user():
    """Tester avec un utilisateur réel de la base de données"""
    
    # Créer une session
    session = requests.Session()
    
    print("🔐 Test avec utilisateur réel")
    
    # Essayer de se connecter avec l'utilisateur player existant
    # D'abord, essayons avec l'admin pour voir si ça marche
    login_data = {
        "email": "admin@padelvar.com",
        "password": "admin123"  # Password par défaut souvent utilisé
    }
    
    print("\n📍 Tentative de connexion avec admin...")
    login_response = session.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print(f"Login Status: {login_response.status_code}")
    
    if login_response.status_code != 200:
        # Essayer avec un joueur
        login_data = {
            "email": "wael@padelvar.com",
            "password": "password123"  
        }
        
        print("\n📍 Tentative de connexion avec joueur...")
        login_response = session.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"Login Status: {login_response.status_code}")
    
    if login_response.status_code == 200:
        print("✅ Connexion réussie!")
        try:
            login_result = login_response.json()
            print(f"Login response: {json.dumps(login_result, indent=2)}")
        except:
            print("Login response text:", login_response.text)
    else:
        print("❌ Connexion échouée, utilisation du mode manuel")
        # Simuler une session manuellement en ajoutant user_id directement
        # Pour cela, modifions temporairement le code pour bypasser l'auth
    
    # Test des endpoints avec la session
    print("\n=== Test Debug Session ===")
    response = session.get(f"{BASE_URL}/api/players/debug/session")
    print(f"Status: {response.status_code}")
    try:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
    except:
        print(f"Response text: {response.text}")
    
    print("\n=== Test Available Clubs ===")
    response = session.get(f"{BASE_URL}/api/players/clubs/available")
    print(f"Status: {response.status_code}")
    try:
        result = response.json()
        if result:
            # Limiter l'affichage pour éviter trop de texte
            if isinstance(result, dict) and 'clubs' in result:
                print(f"Clubs trouvés: {len(result.get('clubs', []))}")
                print(f"Total clubs: {result.get('total_clubs', 0)}")
                print(f"Followed count: {result.get('followed_count', 0)}")
            else:
                print(f"Response: {json.dumps(result, indent=2)}")
    except:
        print(f"Response text: {response.text}")
    
    print("\n=== Test Followed Clubs ===")
    response = session.get(f"{BASE_URL}/api/players/clubs/followed")
    print(f"Status: {response.status_code}")
    try:
        result = response.json()
        if result:
            if isinstance(result, dict) and 'clubs' in result:
                print(f"Clubs suivis: {len(result.get('clubs', []))}")
                print(f"Total followed: {result.get('total_followed', 0)}")
            else:
                print(f"Response: {json.dumps(result, indent=2)}")
    except:
        print(f"Response text: {response.text}")

def main():
    """Test principal"""
    print("🧪 Test des endpoints clubs avec authentification réelle")
    test_with_real_user()
    print("\n✅ Tests terminés")

if __name__ == "__main__":
    main()
