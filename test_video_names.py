#!/usr/bin/env python3
"""Test pour vérifier que les noms de joueurs s'affichent dans les vidéos"""

import requests
import json
from datetime import datetime
from src.main import app
from src.models.database import db, Video, User, Club, Court
from src.config import Config

# Configuration de test
app.config.from_object(Config)

with app.app_context():
    print("=== TEST NOMS DE JOUEURS DANS LES VIDÉOS ===")
    
    # Trouver un club avec des vidéos
    club = Club.query.first()
    if not club:
        print("❌ Aucun club trouvé")
        exit(1)
    
    print(f"✅ Club trouvé: {club.name} (ID: {club.id})")
    
    # Vérifier les vidéos directement en base
    videos = Video.query.filter(Video.club_id == club.id).all()
    print(f"✅ Vidéos trouvées en base: {len(videos)}")
    
    for video in videos[:3]:
        user = video.user
        user_name = user.name if user else "Utilisateur inconnu"
        print(f"  📹 Vidéo: {video.title}")
        print(f"     👤 Joueur: {user_name} (user_id: {video.user_id})")
        print(f"     🏟️ Court: {video.court_id}")
        print()
    
    # Test de l'API GET /clubs/videos
    print("=== TEST API GET /clubs/videos ===")
    
    try:
        with app.test_client() as client:
            # Login d'abord
            login_data = {'email': 'admin@padelvar.com', 'password': 'admin123'}
            login_response = client.post('/api/login', json=login_data)
            
            if login_response.status_code != 200:
                print(f"❌ Échec du login: {login_response.status_code}")
                print(login_response.get_json())
                exit(1)
            
            print("✅ Login réussi")
            
            # Maintenant tester l'API videos
            response = client.get(f'/api/clubs/{club.id}/videos')
            
            if response.status_code == 200:
                data = response.get_json()
                videos_api = data.get('videos', [])
                
                print(f"✅ API répondu avec {len(videos_api)} vidéos")
                
                for video in videos_api[:3]:
                    player_name = video.get('player_name', 'CHAMP MANQUANT')
                    print(f"  📹 Vidéo API: {video.get('title', 'Sans titre')}")
                    print(f"     👤 Nom joueur: {player_name}")
                    print(f"     🏟️ Court ID: {video.get('court_id', 'N/A')}")
                    print()
                
                # Vérifier si tous ont des noms
                missing_names = [v for v in videos_api if v.get('player_name') in [None, 'N/A', '']]
                if missing_names:
                    print(f"⚠️ {len(missing_names)} vidéos ont des noms manquants")
                else:
                    print("✅ Toutes les vidéos ont des noms de joueurs!")
                    
            else:
                print(f"❌ Erreur API: {response.status_code}")
                print(response.get_json())
                
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()
