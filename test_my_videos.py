#!/usr/bin/env python3
"""Test de l'endpoint my-videos après correction"""

import requests
import json

print("🧪 Test de l'endpoint /api/videos/my-videos...")

try:
    # Test avec une session de connexion simulée
    session = requests.Session()
    
    # Login en tant qu'utilisateur test
    login_data = {
        'email': 'admin@padelvar.com',
        'password': 'admin123'
    }
    
    print("🔐 Connexion...")
    login_response = session.post('http://localhost:5000/api/auth/login', json=login_data)
    print(f"Login Status: {login_response.status_code}")
    
    if login_response.status_code == 200:
        # Tester l'endpoint my-videos
        print("📹 Test de l'endpoint my-videos...")
        videos_response = session.get('http://localhost:5000/api/videos/my-videos')
        print(f"Videos Status: {videos_response.status_code}")
        
        if videos_response.status_code == 200:
            data = videos_response.json()
            print(f"✅ Endpoint fonctionnel - {len(data.get('videos', []))} vidéos trouvées")
            if data.get('videos'):
                print(f"📄 Première vidéo: {data['videos'][0].get('title', 'Sans titre')}")
        else:
            print(f"❌ Erreur: {videos_response.status_code}")
            print(f"Réponse: {videos_response.text}")
    else:
        print(f"❌ Échec de connexion: {login_response.text}")
        
except Exception as e:
    print(f"❌ Erreur lors du test: {e}")

print("✅ Test terminé")
