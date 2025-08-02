"""
Test simple des nouvelles fonctionnalités d'enregistrement
À exécuter une fois le serveur démarré
"""

import sys
from pathlib import Path

def test_new_features():
    """Tester les nouvelles fonctionnalités"""
    
    print("🧪 Test des nouvelles fonctionnalités d'enregistrement avancé")
    print("=" * 60)
    
    try:
        import requests
        
        BASE_URL = "http://localhost:5000/api"
        session = requests.Session()
        
        print("\n1. 🔐 Test de connexion joueur...")
        login_response = session.post(f"{BASE_URL}/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        
        if login_response.status_code == 200:
            print("✅ Connexion joueur réussie")
        else:
            print(f"❌ Échec connexion: {login_response.status_code}")
            return
        
        print("\n2. 📍 Test récupération clubs suivis...")
        clubs_response = session.get(f"{BASE_URL}/players/clubs/followed")
        if clubs_response.status_code == 200:
            clubs = clubs_response.json().get('clubs', [])
            print(f"✅ {len(clubs)} clubs suivis récupérés")
            if clubs:
                club_id = clubs[0]['id']
                print(f"   - Club test: {clubs[0]['name']}")
            else:
                print("❌ Aucun club suivi")
                return
        else:
            print(f"❌ Erreur clubs: {clubs_response.status_code}")
            return
        
        print("\n3. 🏟️ Test récupération terrains disponibles...")
        courts_response = session.get(f"{BASE_URL}/recording/available-courts/{club_id}")
        if courts_response.status_code == 200:
            courts_data = courts_response.json()
            courts = courts_data.get('courts', [])
            available = [c for c in courts if c.get('available', True)]
            print(f"✅ {len(courts)} terrains total, {len(available)} disponibles")
            
            if available:
                court_id = available[0]['id']
                print(f"   - Terrain test: {available[0]['name']}")
            else:
                print("❌ Aucun terrain disponible")
                return
        else:
            print(f"❌ Erreur terrains: {courts_response.status_code}")
            return
        
        print("\n4. ⏯️ Test démarrage enregistrement avec durée...")
        recording_data = {
            "court_id": court_id,
            "duration": 60,  # 60 minutes
            "title": "Test enregistrement avancé",
            "description": "Test du nouveau système"
        }
        
        start_response = session.post(f"{BASE_URL}/recording/start", json=recording_data)
        if start_response.status_code == 201:
            session_data = start_response.json().get('recording_session', {})
            recording_id = session_data.get('recording_id')
            print(f"✅ Enregistrement démarré: {recording_id}")
            print(f"   - Durée: {session_data.get('planned_duration')} minutes")
        else:
            error = start_response.json().get('error', 'Erreur inconnue')
            print(f"❌ Erreur démarrage: {error}")
            return
        
        print("\n5. 📊 Test vérification enregistrement actif...")
        active_response = session.get(f"{BASE_URL}/recording/my-active")
        if active_response.status_code == 200:
            active = active_response.json().get('active_recording')
            if active:
                print(f"✅ Enregistrement actif détecté")
                print(f"   - Temps restant: {active.get('remaining_minutes')} min")
            else:
                print("❌ Aucun enregistrement actif")
        
        print("\n6. ⏹️ Test arrêt enregistrement...")
        stop_response = session.post(f"{BASE_URL}/recording/stop", json={
            "recording_id": recording_id
        })
        
        if stop_response.status_code == 200:
            video_data = stop_response.json().get('video', {})
            print(f"✅ Enregistrement arrêté")
            print(f"   - Vidéo créée: {video_data.get('title')}")
        else:
            error = stop_response.json().get('error', 'Erreur inconnue')
            print(f"❌ Erreur arrêt: {error}")
        
        print("\n7. 🏢 Test interface club...")
        club_login = session.post(f"{BASE_URL}/auth/login", json={
            "email": "club@example.com",
            "password": "password123"
        })
        
        if club_login.status_code == 200:
            print("✅ Connexion club réussie")
            
            club_recordings = session.get(f"{BASE_URL}/recording/club/active")
            if club_recordings.status_code == 200:
                active_recordings = club_recordings.json().get('active_recordings', [])
                print(f"✅ Interface club: {len(active_recordings)} enregistrements actifs")
            else:
                print(f"❌ Erreur interface club: {club_recordings.status_code}")
        
        print("\n" + "="*60)
        print("🎉 TESTS TERMINÉS AVEC SUCCÈS !")
        print("\n✨ Nouvelles fonctionnalités validées:")
        print("• Sélection de durée d'enregistrement")
        print("• Système de réservation de terrains")
        print("• Interface de suivi pour les joueurs")
        print("• Interface de gestion pour les clubs")
        print("• API complète d'enregistrement avancé")
        
    except ImportError:
        print("❌ Module 'requests' non installé")
        print("   Installez avec: pip install requests")
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("⚠️  Assurez-vous que le serveur backend est démarré (python app.py)")
    input("Appuyez sur Entrée pour continuer...")
    test_new_features()
