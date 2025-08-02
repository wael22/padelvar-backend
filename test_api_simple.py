#!/usr/bin/env python3
"""
Script de test de l'API dashboard sans imports externes
"""

from src.models.user import *
from src.main import create_app
import json

def test_api_dashboard():
    app = create_app()
    with app.app_context():
        print('=== TEST API DASHBOARD CLUB1 ===')
        
        # Simuler la récupération des données dashboard comme la fonction le fait
        from src.routes.clubs import get_club_dashboard
        from src.models.user import User, UserRole, Club, Court, RecordingSession
        
        # Trouver l'utilisateur club1
        club_user = User.query.filter_by(email='club@test.com').first()
        if not club_user:
            print('❌ Utilisateur club@test.com non trouvé')
            return
        
        club = Club.query.get(club_user.club_id)
        if not club:
            print('❌ Club non trouvé')
            return
        
        print(f'✅ Club trouvé: {club.name} (ID: {club.id})')
        
        # Récupérer les terrains du club 1
        courts = Court.query.filter_by(club_id=club.id).all()
        print(f'✅ Terrains du club: {len(courts)}')
        
        courts_with_status = []
        for court in courts:
            court_dict = court.to_dict()
            
            # Vérifier s'il y a un enregistrement actif sur ce terrain (comme dans le code modifié)
            active_recording = RecordingSession.query.filter_by(
                court_id=court.id,
                status='active'
            ).first()
            
            if active_recording and not active_recording.is_expired():
                court_dict.update({
                    'is_occupied': True,
                    'occupation_status': 'Occupé - Enregistrement en cours',
                    'recording_player': active_recording.user.name if active_recording.user else 'Joueur inconnu',
                    'recording_remaining': active_recording.get_remaining_minutes(),
                    'recording_total': active_recording.planned_duration
                })
                print(f'🔴 {court.name}: OCCUPÉ par {active_recording.user.name} ({active_recording.get_remaining_minutes()} min)')
            else:
                court_dict.update({
                    'is_occupied': False,
                    'occupation_status': 'Disponible',
                    'recording_player': None,
                    'recording_remaining': None,
                    'recording_total': None
                })
                print(f'🟢 {court.name}: DISPONIBLE')
            
            courts_with_status.append(court_dict)
        
        print('\n=== DONNÉES QUI SERONT ENVOYÉES AU FRONTEND ===')
        for court in courts_with_status:
            print(f'Terrain: {court["name"]}')
            print(f'  - is_occupied: {court["is_occupied"]}')
            print(f'  - occupation_status: {court["occupation_status"]}')
            print(f'  - recording_player: {court["recording_player"]}')
            print(f'  - recording_remaining: {court["recording_remaining"]}')
            print()

if __name__ == "__main__":
    test_api_dashboard()
