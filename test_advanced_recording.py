"""
Script de test pour les fonctionnalités d'enregistrement avancé
"""

import requests
import json
from datetime import datetime
import time

BASE_URL = "http://localhost:5000/api"

# Session pour maintenir les cookies
session = requests.Session()

def test_advanced_recording_system():
    """Test complet du système d'enregistrement avancé"""
    
    print("🧪 Test du système d'enregistrement avancé")
    print("=" * 50)
    
    # 1. Connexion en tant que joueur
    print("\n1. Connexion en tant que joueur...")
    login_response = session.post(f"{BASE_URL}/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    
    if login_response.status_code != 200:
        print("❌ Échec de la connexion")
        return
    print("✅ Connexion réussie")
    
    # 2. Vérifier les clubs suivis
    print("\n2. Récupération des clubs suivis...")
    clubs_response = session.get(f"{BASE_URL}/players/clubs/followed")
    if clubs_response.status_code == 200:
        clubs = clubs_response.json().get('clubs', [])
        print(f"✅ {len(clubs)} club(s) suivi(s)")
        
        if clubs:
            club_id = clubs[0]['id']
            print(f"   - Club sélectionné: {clubs[0]['name']} (ID: {club_id})")
        else:
            print("❌ Aucun club suivi, impossible de continuer le test")
            return
    else:
        print("❌ Erreur lors de la récupération des clubs")
        return
    
    # 3. Récupérer les terrains disponibles
    print("\n3. Récupération des terrains disponibles...")
    courts_response = session.get(f"{BASE_URL}/recording/available-courts/{club_id}")
    if courts_response.status_code == 200:
        courts_data = courts_response.json()
        courts = courts_data.get('courts', [])
        available_courts = [c for c in courts if c.get('available', True)]
        
        print(f"✅ {len(courts)} terrain(s) total, {len(available_courts)} disponible(s)")
        
        if available_courts:
            court_id = available_courts[0]['id']
            print(f"   - Terrain sélectionné: {available_courts[0]['name']} (ID: {court_id})")
        else:
            print("❌ Aucun terrain disponible")
            # Utiliser le premier terrain même s'il n'est pas disponible pour le test
            if courts:
                court_id = courts[0]['id']
                print(f"   - Utilisation du terrain {courts[0]['name']} pour le test")
            else:
                print("❌ Aucun terrain trouvé")
                return
    else:
        print("❌ Erreur lors de la récupération des terrains")
        return
    
    # 4. Démarrer un enregistrement avec durée
    print("\n4. Démarrage d'un enregistrement (60 minutes)...")
    recording_data = {
        "court_id": court_id,
        "duration": 60,
        "title": f"Test enregistrement {datetime.now().strftime('%H:%M:%S')}",
        "description": "Test du système d'enregistrement avancé"
    }
    
    start_response = session.post(f"{BASE_URL}/recording/start", json=recording_data)
    if start_response.status_code == 201:
        recording_session = start_response.json().get('recording_session', {})
        recording_id = recording_session.get('recording_id')
        print(f"✅ Enregistrement démarré: {recording_id}")
        print(f"   - Durée prévue: {recording_session.get('planned_duration')} minutes")
        print(f"   - Terrain réservé: {recording_session.get('court_id')}")
    else:
        error = start_response.json().get('error', 'Erreur inconnue')
        print(f"❌ Erreur lors du démarrage: {error}")
        return
    
    # 5. Vérifier l'enregistrement actif
    print("\n5. Vérification de l'enregistrement actif...")
    active_response = session.get(f"{BASE_URL}/recording/my-active")
    if active_response.status_code == 200:
        active_recording = active_response.json().get('active_recording')
        if active_recording:
            print(f"✅ Enregistrement actif détecté")
            print(f"   - ID: {active_recording.get('recording_id')}")
            print(f"   - Temps restant: {active_recording.get('remaining_minutes')} minutes")
            print(f"   - Temps écoulé: {active_recording.get('elapsed_minutes')} minutes")
        else:
            print("❌ Aucun enregistrement actif trouvé")
    else:
        print("❌ Erreur lors de la vérification")
    
    # 6. Attendre quelques secondes pour simuler l'enregistrement
    print("\n6. Simulation d'enregistrement (5 secondes)...")
    time.sleep(5)
    
    # 7. Vérifier que le terrain est réservé
    print("\n7. Vérification de la réservation du terrain...")
    courts_check_response = session.get(f"{BASE_URL}/recording/available-courts/{club_id}")
    if courts_check_response.status_code == 200:
        courts_check = courts_check_response.json().get('courts', [])
        reserved_court = next((c for c in courts_check if c['id'] == court_id), None)
        
        if reserved_court and not reserved_court.get('available', True):
            print("✅ Terrain correctement réservé")
            print(f"   - Statut: {reserved_court.get('is_recording', False)}")
            if 'recording_info' in reserved_court:
                info = reserved_court['recording_info']
                print(f"   - Joueur: {info.get('player_name', 'Inconnu')}")
                print(f"   - Temps restant: {info.get('remaining_minutes', 0)} min")
        else:
            print("❌ Le terrain n'est pas marqué comme réservé")
    
    # 8. Arrêter l'enregistrement
    print("\n8. Arrêt de l'enregistrement...")
    stop_response = session.post(f"{BASE_URL}/recording/stop", json={
        "recording_id": recording_id
    })
    
    if stop_response.status_code == 200:
        video_data = stop_response.json().get('video', {})
        print(f"✅ Enregistrement arrêté avec succès")
        print(f"   - Vidéo créée: {video_data.get('title')}")
        print(f"   - Durée: {video_data.get('duration', 0)} secondes")
        print(f"   - ID vidéo: {video_data.get('id')}")
    else:
        error = stop_response.json().get('error', 'Erreur inconnue')
        print(f"❌ Erreur lors de l'arrêt: {error}")
    
    # 9. Vérifier que le terrain est libéré
    print("\n9. Vérification de la libération du terrain...")
    courts_final_response = session.get(f"{BASE_URL}/recording/available-courts/{club_id}")
    if courts_final_response.status_code == 200:
        courts_final = courts_final_response.json().get('courts', [])
        liberated_court = next((c for c in courts_final if c['id'] == court_id), None)
        
        if liberated_court and liberated_court.get('available', True):
            print("✅ Terrain correctement libéré")
        else:
            print("❌ Le terrain n'a pas été libéré")
    
    print("\n" + "=" * 50)
    print("🎉 Test du système d'enregistrement avancé terminé")

def test_club_recording_management():
    """Test des fonctionnalités club pour gérer les enregistrements"""
    
    print("\n\n🏢 Test de la gestion des enregistrements par le club")
    print("=" * 50)
    
    # Connexion en tant que club
    print("\n1. Connexion en tant que club...")
    login_response = session.post(f"{BASE_URL}/auth/login", json={
        "email": "club@example.com",
        "password": "password123"
    })
    
    if login_response.status_code != 200:
        print("❌ Échec de la connexion club")
        return
    print("✅ Connexion club réussie")
    
    # Vérifier les enregistrements actifs
    print("\n2. Récupération des enregistrements actifs...")
    active_recordings_response = session.get(f"{BASE_URL}/recording/club/active")
    if active_recordings_response.status_code == 200:
        active_recordings = active_recordings_response.json().get('active_recordings', [])
        print(f"✅ {len(active_recordings)} enregistrement(s) actif(s)")
        
        for recording in active_recordings:
            print(f"   - {recording.get('title')} par {recording.get('player', {}).get('name', 'Inconnu')}")
            print(f"     Terrain: {recording.get('court', {}).get('name', 'Inconnu')}")
            print(f"     Temps restant: {recording.get('remaining_minutes', 0)} min")
    else:
        print("❌ Erreur lors de la récupération des enregistrements actifs")
    
    print("\n" + "=" * 50)
    print("🎉 Test de gestion club terminé")

if __name__ == "__main__":
    try:
        test_advanced_recording_system()
        test_club_recording_management()
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
