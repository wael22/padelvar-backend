#!/usr/bin/env python3
"""
Test du minuteur avec authentification
"""

import requests
import time
import json

# Configuration
BASE_URL = "http://127.0.0.1:5000"

def login_admin():
    """Se connecter en tant qu'admin"""
    login_data = {
        "email": "admin@padelvar.com",
        "password": "admin123"
    }
    
    session = requests.Session()
    response = session.post(f"{BASE_URL}/api/auth/login", json=login_data)
    
    if response.status_code == 200:
        print("✅ Connexion admin réussie")
        return session
    else:
        print(f"❌ Échec de connexion: {response.status_code}")
        print(f"   Réponse: {response.text}")
        return None

def test_timer_with_auth():
    """Test du minuteur avec authentification"""
    print("🎬 Test du minuteur d'enregistrement avec authentification")
    print("=" * 60)
    
    # Se connecter
    session = login_admin()
    if not session:
        return
    
    # Données pour l'enregistrement (1 minute pour test rapide)
    start_data = {
        "court_id": 2,  # Essayer terrain 2 au lieu de 1
        "session_name": "Test Timer",
        "duration_minutes": 1
    }
    
    # Démarrer l'enregistrement
    print("\n1. Démarrage de l'enregistrement (1 minute)...")
    response = session.post(f"{BASE_URL}/api/videos/record", json=start_data)
    
    if response.status_code == 200:
        result = response.json()
        session_id = result.get('session_id')
        print(f"✅ Enregistrement démarré: {session_id}")
        print(f"   Court ID: {start_data['court_id']}")
        print(f"   Durée: 1 minute")
        
        # Surveiller l'état pendant 70 secondes
        print("\n2. Surveillance de l'arrêt automatique...")
        for i in range(7):  # 7 vérifications de 10 secondes
            time.sleep(10)
            print(f"   ⏱️  Vérification après {(i+1)*10} secondes...")
            
            # Vérifier l'état du terrain
            court_response = session.get(f"{BASE_URL}/api/courts/2")
            if court_response.status_code == 200:
                court = court_response.json()
                is_recording = court.get('is_recording', False)
                
                if not is_recording:
                    print(f"✅ SUCCÈS: Enregistrement arrêté automatiquement après ~{(i+1)*10} secondes")
                    return
            else:
                print(f"   ⚠️  Erreur lors de la vérification du terrain: {court_response.status_code}")
        
        # Si on arrive ici, il y a un problème
        print("❌ PROBLÈME: L'enregistrement n'a pas été arrêté automatiquement")
        
        # Arrêt manuel
        print("   Tentative d'arrêt manuel...")
        stop_response = session.post(f"{BASE_URL}/api/videos/stop-recording", json={"court_id": 2})
        if stop_response.status_code == 200:
            print("✅ Arrêt manuel réussi")
        else:
            print(f"❌ Échec arrêt manuel: {stop_response.status_code}")
            
    else:
        print(f"❌ Erreur lors du démarrage: {response.status_code}")
        print(f"   Réponse: {response.text}")

if __name__ == "__main__":
    print("🧪 Test du système de minuteur PadelVar")
    print("ATTENTION: Assurez-vous que le serveur est démarré sur http://127.0.0.1:5000")
    print()
    
    input("Appuyez sur Entrée pour commencer le test...")
    test_timer_with_auth()
