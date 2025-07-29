#!/usr/bin/env python3
"""Test avec client Flask pour vérifier les noms de joueurs"""

import sys
from pathlib import Path
import json

# Configuration du chemin
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.main import create_app
from src.models.user import User, UserRole

# Créer l'app
app = create_app()

with app.app_context():
    print("=== TEST API AVEC FLASK CLIENT ===")
    
    # Trouver un utilisateur club
    user = User.query.filter_by(role=UserRole.CLUB).first()
    if not user:
        print("❌ Aucun utilisateur club trouvé")
        exit(1)
        
    print(f"✅ Utilisateur trouvé: {user.name} (club_id: {user.club_id})")
    
    with app.test_client() as client:
        # Simuler une session authentifiée
        with client.session_transaction() as sess:
            sess['user_id'] = user.id
            sess['logged_in'] = True
        
        print("\n1. Test dashboard...")
        response = client.get('/api/clubs/dashboard')
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.get_json()
            videos = data.get('videos', [])
            print(f"✅ {len(videos)} vidéos retournées")
            
            for i, video in enumerate(videos, 1):
                title = video.get('title', 'Sans titre')
                player_name = video.get('player_name', 'CHAMP MANQUANT')
                print(f"  📹 Vidéo {i}: {title}")
                print(f"     👤 player_name: {player_name}")
                
            # Compter les noms manquants
            missing_names = [v for v in videos if v.get('player_name') in [None, 'N/A', '', 'Joueur inconnu']]
            if missing_names:
                print(f"\n⚠️ {len(missing_names)} vidéos ont des noms manquants ou génériques")
            else:
                print(f"\n✅ Toutes les {len(videos)} vidéos ont des noms de joueurs valides!")
                
        else:
            print(f"❌ Erreur: {response.status_code}")
            print(response.get_data(as_text=True))
            
        print("\n2. Test endpoint vidéos spécifique...")
        response = client.get(f'/api/clubs/{user.club_id}/videos')
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.get_json()
            videos = data.get('videos', [])
            print(f"✅ {len(videos)} vidéos retournées")
            
            for i, video in enumerate(videos, 1):
                title = video.get('title', 'Sans titre')
                player_name = video.get('player_name', 'CHAMP MANQUANT')
                print(f"  📹 Vidéo {i}: {title}")
                print(f"     👤 player_name: {player_name}")
                
            # Compter les noms manquants
            missing_names = [v for v in videos if v.get('player_name') in [None, 'N/A', '', 'Joueur inconnu']]
            if missing_names:
                print(f"\n⚠️ {len(missing_names)} vidéos ont des noms manquants ou génériques")
            else:
                print(f"\n✅ Toutes les {len(videos)} vidéos ont des noms de joueurs valides!")
                
        else:
            print(f"❌ Erreur: {response.status_code}")
            print(response.get_data(as_text=True))
