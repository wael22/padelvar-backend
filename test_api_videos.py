#!/usr/bin/env python3
"""Test de l'API pour vérifier les noms de joueurs"""

import requests
import json

def test_videos_api():
    base_url = "http://localhost:5000"
    
    print("=== TEST API NOMS DE JOUEURS ===")
    
    # 1. Login
    print("1. Connexion...")
    login_data = {
        'email': 'admin@padelvar.com',
        'password': 'admin123'
    }
    
    session = requests.Session()
    response = session.post(f"{base_url}/api/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Échec du login: {response.status_code}")
        print(response.text)
        return
    
    print("✅ Login réussi")
    
    # 2. Test dashboard (qui contient des vidéos)
    print("\n2. Test dashboard...")
    response = session.get(f"{base_url}/api/clubs/dashboard")
    
    if response.status_code == 200:
        data = response.json()
        videos = data.get('videos', [])
        print(f"✅ Dashboard retourne {len(videos)} vidéos")
        
        for i, video in enumerate(videos[:3], 1):
            player_name = video.get('player_name', 'CHAMP MANQUANT')
            print(f"  📹 Vidéo {i}: {video.get('title', 'Sans titre')}")
            print(f"     👤 Nom joueur: {player_name}")
            
        if videos:
            missing_names = [v for v in videos if v.get('player_name') in [None, 'N/A', '']]
            if missing_names:
                print(f"⚠️ {len(missing_names)} vidéos ont des noms manquants")
            else:
                print("✅ Toutes les vidéos ont des noms de joueurs!")
        else:
            print("ℹ️ Aucune vidéo trouvée")
    else:
        print(f"❌ Erreur dashboard: {response.status_code}")
        print(response.text)
    
    # 3. Test endpoint vidéos spécifique
    print("\n3. Test endpoint vidéos...")
    response = session.get(f"{base_url}/api/clubs/1/videos")
    
    if response.status_code == 200:
        data = response.json()
        videos = data.get('videos', [])
        print(f"✅ Endpoint vidéos retourne {len(videos)} vidéos")
        
        for i, video in enumerate(videos[:3], 1):
            player_name = video.get('player_name', 'CHAMP MANQUANT')
            print(f"  📹 Vidéo {i}: {video.get('title', 'Sans titre')}")
            print(f"     👤 Nom joueur: {player_name}")
            
        if videos:
            missing_names = [v for v in videos if v.get('player_name') in [None, 'N/A', '']]
            if missing_names:
                print(f"⚠️ {len(missing_names)} vidéos ont des noms manquants")
            else:
                print("✅ Toutes les vidéos ont des noms de joueurs!")
        else:
            print("ℹ️ Aucune vidéo trouvée")
    else:
        print(f"❌ Erreur endpoint vidéos: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    try:
        test_videos_api()
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur. Est-il démarré?")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
