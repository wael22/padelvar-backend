#!/usr/bin/env python3
"""
Script de nettoyage des enregistrements actifs
"""

import requests
import json

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
        return None

def check_and_clean_courts():
    """Vérifier et nettoyer l'état des terrains"""
    print("🧹 Nettoyage des terrains en cours d'enregistrement")
    print("=" * 50)
    
    session = login_admin()
    if not session:
        return
    
    # Vérifier les terrains 1 à 5
    for court_id in range(1, 6):
        print(f"\n🔍 Vérification terrain {court_id}...")
        
        response = session.get(f"{BASE_URL}/api/courts/{court_id}")
        if response.status_code == 200:
            court = response.json()
            is_recording = court.get('is_recording', False)
            session_id = court.get('recording_session_id')
            
            print(f"   Statut: {'🔴 En cours' if is_recording else '🟢 Libre'}")
            if session_id:
                print(f"   Session: {session_id}")
            
            # Arrêter si en cours d'enregistrement
            if is_recording:
                print(f"   🛑 Arrêt de l'enregistrement...")
                stop_data = {"court_id": court_id}
                stop_response = session.post(f"{BASE_URL}/api/videos/stop-recording", json=stop_data)
                
                if stop_response.status_code == 200:
                    print(f"   ✅ Enregistrement arrêté avec succès")
                else:
                    print(f"   ⚠️  Erreur lors de l'arrêt: {stop_response.status_code}")
                    print(f"       Réponse: {stop_response.text}")
        else:
            print(f"   ⚠️  Terrain {court_id} non trouvé ou erreur: {response.status_code}")
    
    print("\n🎯 Nettoyage terminé - Tous les terrains devraient être libres")

if __name__ == "__main__":
    check_and_clean_courts()
