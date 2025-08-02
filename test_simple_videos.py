#!/usr/bin/env python3
"""Test simple pour vérifier les noms de joueurs"""

import os
import sys
from pathlib import Path

# Configuration du chemin
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.main import create_app
from src.models.database import db, Video, User, Club

# Créer l'app
app = create_app()

with app.app_context():
    print("=== TEST NOMS DE JOUEURS ===")
    
    # Vérifier les vidéos en base
    videos = Video.query.all()
    print(f"Total vidéos: {len(videos)}")
    
    for video in videos[:5]:
        user = video.user
        user_name = user.name if user else "AUCUN UTILISATEUR"
        print(f"📹 Vidéo {video.id}: {video.title}")
        print(f"   👤 Joueur: {user_name} (user_id: {video.user_id})")
        print(f"   🏟️ Club: {video.club_id}, Court: {video.court_id}")
        print()
    
    # Test API endpoint
    print("=== TEST API ENDPOINT ===")
    club = Club.query.first()
    if club:
        print(f"Club de test: {club.name} (ID: {club.id})")
        
        # Import du module de routes pour tester la fonction
        from src.routes.clubs import get_club_videos
        
        # Simuler une requête (ne fonctionne que partiellement sans Flask context complet)
        print("⚠️ Pour tester l'API complète, utiliser le serveur démarré")
    else:
        print("❌ Aucun club trouvé")
