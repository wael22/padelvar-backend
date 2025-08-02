#!/usr/bin/env python3
"""Test complet des endpoints après corrections"""

from src.main import create_app
from src.models.user import User, Video, Club
import json

# Créer l'app de test
app = create_app()

print("🧪 Test complet des endpoints après corrections...")

with app.test_client() as client:
    with app.app_context():
        print("1️⃣ Test de connexion admin...")
        
        # Login admin
        login_response = client.post('/api/auth/login', 
                                   json={'email': 'admin@padelvar.com', 'password': 'admin123'})
        print(f"   Login Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            # Test endpoint my-videos
            print("2️⃣ Test endpoint /api/videos/my-videos...")
            videos_response = client.get('/api/videos/my-videos')
            print(f"   Videos Status: {videos_response.status_code}")
            
            if videos_response.status_code == 200:
                data = videos_response.get_json()
                print(f"   ✅ {len(data.get('videos', []))} vidéos trouvées")
            else:
                print(f"   ❌ Erreur: {videos_response.get_data(as_text=True)}")
            
            # Test endpoint admin videos
            print("3️⃣ Test endpoint /api/admin/videos...")
            admin_videos_response = client.get('/api/admin/videos')
            print(f"   Admin Videos Status: {admin_videos_response.status_code}")
            
            if admin_videos_response.status_code == 200:
                data = admin_videos_response.get_json()
                print(f"   ✅ {len(data.get('videos', []))} vidéos admin trouvées")
            else:
                print(f"   ❌ Erreur: {admin_videos_response.get_data(as_text=True)}")
            
            # Test endpoint clubs available (en tant que player)
            print("4️⃣ Test endpoint /api/players/clubs/available...")
            clubs_response = client.get('/api/players/clubs/available')
            print(f"   Clubs Status: {clubs_response.status_code}")
            
            if clubs_response.status_code == 200:
                data = clubs_response.get_json()
                print(f"   ✅ {len(data.get('clubs', []))} clubs disponibles")
            else:
                print(f"   ❌ Erreur: {clubs_response.get_data(as_text=True)}")
        
        print("✅ Test terminé")
