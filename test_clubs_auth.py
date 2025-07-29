#!/usr/bin/env python3
"""
Test des endpoints clubs avec authentification
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"

def test_with_auth():
    """Tester les endpoints avec une session authentifiée"""
    
    # Créer une session
    session = requests.Session()
    
    print("🔐 Test avec authentification")
    
    # D'abord, essayons de nous connecter avec un utilisateur test
    # Si aucun utilisateur test n'existe, les endpoints fonctionneront quand même
    # grâce au mode DEBUG qui accepte tout utilisateur authentifié
    
    login_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    
    print("\n📍 Tentative de connexion...")
    login_response = session.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print(f"Login Status: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print("ℹ️  Connexion échouée, mais les endpoints devraient fonctionner en mode DEBUG")
        # En mode DEBUG, créons une session factice
        session.cookies.set('session', 'debug_session')
    
    # Test des endpoints avec la session
    print("\n=== Test Available Clubs avec session ===")
    response = session.get(f"{BASE_URL}/api/players/clubs/available")
    print(f"Status: {response.status_code}")
    try:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
    except:
        print(f"Response text: {response.text}")
    
    print("\n=== Test Followed Clubs avec session ===")
    response = session.get(f"{BASE_URL}/api/players/clubs/followed")
    print(f"Status: {response.status_code}")
    try:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
    except:
        print(f"Response text: {response.text}")
    
    print("\n=== Test Session Debug ===")
    response = session.get(f"{BASE_URL}/api/players/debug/session")
    print(f"Status: {response.status_code}")
    try:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
    except:
        print(f"Response text: {response.text}")

def test_direct_without_session():
    """Test direct sans session pour voir les erreurs de base"""
    print("\n🔍 Test direct sans session")
    
    try:
        response = requests.get(f"{BASE_URL}/api/players/clubs/available")
        print(f"Available Clubs Status: {response.status_code}")
        if response.status_code != 200:
            try:
                error = response.json()
                print(f"Error: {error}")
            except:
                print(f"Error text: {response.text}")
    except Exception as e:
        print(f"❌ Erreur: {e}")

def main():
    """Test principal"""
    print("🧪 Test complet des endpoints clubs")
    
    test_direct_without_session()
    test_with_auth()
    
    print("\n✅ Tests terminés")

if __name__ == "__main__":
    main()
