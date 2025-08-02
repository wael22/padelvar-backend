#!/usr/bin/env python3
"""
Test simple du minuteur sans interaction
"""

import requests
import time
import json

BASE_URL = "http://127.0.0.1:5000"

def test_timer_simple():
    """Test automatique du minuteur"""
    print("🎬 Test automatique du minuteur")
    print("=" * 40)
    
    # Session pour maintenir les cookies
    session = requests.Session()
    
    # 1. Connexion admin
    print("1. Connexion admin...")
    login_data = {
        "email": "admin@padelvar.com",
        "password": "admin123"
    }
    
    response = session.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Échec connexion: {response.status_code}")
        return False
    
    print("✅ Connexion réussie")
    
    # 2. Test d'enregistrement
    print("2. Démarrage enregistrement (1 minute)...")
    start_data = {
        "court_id": 3,  # Essayons terrain 3
        "session_name": "Test Auto",
        "duration_minutes": 1
    }
    
    response = session.post(f"{BASE_URL}/api/videos/record", json=start_data)
    print(f"   Statut: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        session_id = result.get('session_id')
        print(f"✅ Enregistrement démarré: {session_id}")
        
        # 3. Attendre et vérifier
        print("3. Surveillance (70 secondes)...")
        for i in range(7):
            time.sleep(10)
            print(f"   ⏱️  {(i+1)*10}s écoulées...")
        
        print("✅ Test terminé - Vérifiez manuellement si l'enregistrement s'est arrêté")
        return True
        
    else:
        print(f"❌ Erreur démarrage: {response.status_code}")
        try:
            error = response.json()
            print(f"   Détail: {error}")
        except:
            print(f"   Réponse: {response.text[:200]}")
        return False

if __name__ == "__main__":
    test_timer_simple()
