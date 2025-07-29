#!/usr/bin/env python3
"""
Test des endpoints clubs pour diagnostiquer les erreurs 500
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"

def test_endpoint(url, method="GET", data=None):
    """Tester un endpoint et afficher les détails"""
    try:
        print(f"\n📍 Test {method} {url}")
        
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            response = requests.request(method, url, json=data)
        
        print(f"Status: {response.status_code}")
        
        try:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
        except:
            print(f"Response text: {response.text}")
            
        return response
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

def main():
    """Test principal"""
    print("🧪 Test des endpoints clubs")
    
    # Test de la session d'abord
    print("\n=== Test Session Debug ===")
    test_endpoint(f"{BASE_URL}/api/players/debug/session")
    
    # Test des endpoints qui causent les erreurs
    print("\n=== Test Available Clubs ===")
    test_endpoint(f"{BASE_URL}/api/players/clubs/available")
    
    print("\n=== Test Followed Clubs ===")
    test_endpoint(f"{BASE_URL}/api/players/clubs/followed")
    
    print("\n✅ Tests terminés")

if __name__ == "__main__":
    main()
