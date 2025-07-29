#!/usr/bin/env python3
"""Test simple pour vérifier les noms de joueurs"""

import sys
from pathlib import Path

# Configuration du chemin
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.main import create_app
from src.models.user import User, Club, Video, Court, db
from sqlalchemy.orm import joinedload

# Créer l'app
app = create_app()

with app.app_context():
    print("=== TEST NOMS DE JOUEURS ===")
    
    # Test direct
    videos = Video.query.all()
    print(f"Total vidéos: {len(videos)}")
    
    for video in videos[:3]:
        owner_name = video.owner.name if video.owner else "AUCUN"
        print(f"  Vidéo {video.id}: owner={owner_name}")
    
    # Test jointure comme dans l'API
    print("\n=== TEST API SIMULATION ===")
    club = Club.query.first()
    if club:
        videos = db.session.query(Video).options(joinedload(Video.owner)).join(Court, Video.court_id == Court.id).filter(
            Court.club_id == club.id
        ).all()
        
        print(f"Vidéos club via API: {len(videos)}")
        
        for video in videos:
            player_name = video.owner.name if video.owner else 'Joueur inconnu'
            video_dict = video.to_dict()
            video_dict['player_name'] = player_name
            print(f"  API: {video_dict['title']} -> player_name: {video_dict['player_name']}")
        
        missing = sum(1 for v in videos if not v.owner)
        if missing:
            print(f"⚠️ {missing} vidéos sans propriétaire")
        else:
            print("✅ Toutes les vidéos ont un propriétaire!")
    else:
        print("Aucun club trouvé")
