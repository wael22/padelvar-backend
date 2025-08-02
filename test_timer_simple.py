#!/usr/bin/env python3
"""
Test simple du système de minuteur d'enregistrement
"""

import requests
import time
import json

# Configuration
BASE_URL = "http://127.0.0.1:5000"
TEST_USER_ID = 1
TEST_COURT_ID = 1

def test_recording_timer():
    """Test du minuteur d'enregistrement avec un délai court"""
    
    print("🎬 Test du minuteur d'enregistrement")
    print("=" * 50)
    
    # Étape 1: Démarrer un enregistrement avec 1 minute
    print("\n1. Démarrage de l'enregistrement (1 minute)...")
    
    start_data = {
        "court_id": TEST_COURT_ID,
        "user_id": TEST_USER_ID,
        "duration_minutes": 1  # 1 minute pour test rapide
    }
    
    response = requests.post(f"{BASE_URL}/api/videos/record", json=start_data)
    
    if response.status_code == 200:
        result = response.json()
        session_id = result.get('session_id')
        print(f"✅ Enregistrement démarré: {session_id}")
        print(f"   Court ID: {TEST_COURT_ID}")
        print(f"   Durée prévue: 1 minute")
    else:
        print(f"❌ Erreur lors du démarrage: {response.status_code}")
        print(f"   Réponse: {response.text}")
        return
    
    # Étape 2: Vérifier l'état du terrain
    print("\n2. Vérification de l'état du terrain...")
    response = requests.get(f"{BASE_URL}/api/courts/{TEST_COURT_ID}")
    
    if response.status_code == 200:
        court = response.json()
        print(f"   Terrain en enregistrement: {court.get('is_recording', False)}")
        print(f"   Session ID: {court.get('recording_session_id', 'None')}")
    
    # Étape 3: Attendre et vérifier périodiquement
    print("\n3. Attente de l'arrêt automatique (70 secondes)...")
    
    for i in range(7):  # Vérifier toutes les 10 secondes pendant 70 secondes
        print(f"   Vérification {i+1}/7 après {(i+1)*10} secondes...")
        time.sleep(10)
        
        # Vérifier l'état du terrain
        response = requests.get(f"{BASE_URL}/api/courts/{TEST_COURT_ID}")
        if response.status_code == 200:
            court = response.json()
            is_recording = court.get('is_recording', False)
            
            if not is_recording:
                print(f"✅ Enregistrement arrêté automatiquement après ~{(i+1)*10} secondes")
                break
            else:
                print(f"   🔴 Encore en cours d'enregistrement...")
    
    # Étape 4: Vérification finale
    print("\n4. Vérification finale...")
    response = requests.get(f"{BASE_URL}/api/courts/{TEST_COURT_ID}")
    
    if response.status_code == 200:
        court = response.json()
        is_recording = court.get('is_recording', False)
        
        if is_recording:
            print("❌ PROBLÈME: L'enregistrement n'a pas été arrêté automatiquement")
            print(f"   Session ID: {court.get('recording_session_id', 'None')}")
            
            # Arrêter manuellement
            print("   Arrêt manuel...")
            stop_data = {"court_id": TEST_COURT_ID, "user_id": TEST_USER_ID}
            requests.post(f"{BASE_URL}/api/videos/stop-recording", json=stop_data)
        else:
            print("✅ SUCCESS: Le minuteur a fonctionné correctement")
    
    print("\n" + "=" * 50)
    print("🏁 Test terminé")

if __name__ == "__main__":
    print("Démarrage du test du minuteur d'enregistrement")
    print("ATTENTION: Ce test va prendre environ 70 secondes")
    
    input("Appuyez sur Entrée pour continuer...")
    
    test_recording_timer()
