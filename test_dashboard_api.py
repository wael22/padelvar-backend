#!/usr/bin/env python3
"""
Test pour simuler l'appel au dashboard du club1 et vérifier
pourquoi l'affichage montre "Disponible" au lieu d'"Occupé"
"""

import requests
import json

def test_club_dashboard():
    """Test du dashboard club"""
    
    print("🏢 Test du dashboard club1")
    print("=" * 40)
    
    # 1. Connexion en tant que club1
    login_data = {
        "email": "club1@test.com",
        "password": "password123"
    }
    
    session = requests.Session()
    
    try:
        # Login
        print("1. Connexion au club1...")
        login_response = session.post(
            "http://localhost:5000/api/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Échec de connexion: {login_response.status_code}")
            return
        
        print("✅ Connexion réussie")
        
        # 2. Récupérer le dashboard
        print("\n2. Récupération du dashboard...")
        dashboard_response = session.get("http://localhost:5000/api/clubs/dashboard")
        
        if dashboard_response.status_code != 200:
            print(f"❌ Échec dashboard: {dashboard_response.status_code}")
            print(f"Réponse: {dashboard_response.text}")
            return
        
        data = dashboard_response.json()
        print("✅ Dashboard récupéré")
        
        # 3. Analyser les terrains
        courts = data.get('courts', [])
        print(f"\n3. Analyse des terrains ({len(courts)} trouvés):")
        
        for court in courts:
            print(f"\n🎾 {court['name']} (ID: {court['id']})")
            print(f"   - is_recording: {court.get('is_recording', 'N/A')}")
            print(f"   - available: {court.get('available', 'N/A')}")
            print(f"   - current_recording_id: {court.get('current_recording_id', 'N/A')}")
            
            # Nouvelles données d'occupation
            print(f"   - is_occupied: {court.get('is_occupied', 'N/A')}")
            print(f"   - occupation_status: {court.get('occupation_status', 'N/A')}")
            print(f"   - recording_player: {court.get('recording_player', 'N/A')}")
            print(f"   - recording_remaining: {court.get('recording_remaining', 'N/A')}")
        
        # 4. Vérifier les stats générales
        stats = data.get('stats', {})
        print(f"\n4. Statistiques:")
        print(f"   - Terrains total: {stats.get('total_courts', 'N/A')}")
        print(f"   - Joueurs total: {stats.get('total_players', 'N/A')}")
        
        # 5. Test de l'API terrains disponibles (vue joueur)
        print(f"\n5. Test des terrains disponibles (vue joueur):")
        courts_response = session.get("http://localhost:5000/api/recording/available-courts/1")
        
        if courts_response.status_code == 200:
            courts_data = courts_response.json()
            available_courts = courts_data.get('courts', [])
            
            for court in available_courts:
                print(f"\n🎾 {court['name']} (vue joueur)")
                print(f"   - available: {court.get('available', 'N/A')}")
                print(f"   - is_recording: {court.get('is_recording', 'N/A')}")
                
                if court.get('recording_info'):
                    rec_info = court['recording_info']
                    print(f"   - Joueur en cours: {rec_info.get('player_name', 'N/A')}")
                    print(f"   - Temps restant: {rec_info.get('remaining_minutes', 'N/A')} min")
        else:
            print(f"❌ Échec API terrains: {courts_response.status_code}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_club_dashboard()
