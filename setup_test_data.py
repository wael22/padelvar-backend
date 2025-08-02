#!/usr/bin/env python3
"""
Script pour créer un joueur et une session d'enregistrement de test
"""

from src.models.user import *
from src.main import create_app
from datetime import datetime, timedelta
import uuid
from werkzeug.security import generate_password_hash

def create_test_player_and_session():
    app = create_app()
    with app.app_context():
        print('=== CRÉATION JOUEUR ET SESSION TEST ===')
        
        # 1. Créer un joueur pour le club 1 s'il n'existe pas
        player = User.query.filter_by(email='testplayer_club1@example.com').first()
        if not player:
            player = User(
                email='testplayer_club1@example.com',
                name='Test Player Club1',
                password_hash=generate_password_hash('password123'),
                role=UserRole.PLAYER,
                club_id=1,
                credits_balance=10
            )
            db.session.add(player)
            print('✅ Joueur créé: Test Player Club1')
        else:
            print('✅ Joueur existant trouvé: Test Player Club1')
        
        # 2. Trouver le terrain 2 du club 1 (Terrain Annexe)
        court = Court.query.filter_by(club_id=1, name='Terrain Annexe').first()
        if not court:
            print('❌ Terrain Annexe non trouvé')
            return
        
        # 3. Vérifier s'il y a déjà une session active sur ce terrain
        existing_session = RecordingSession.query.filter_by(
            court_id=court.id,
            status='active'
        ).first()
        
        if existing_session:
            print(f'ℹ️ Session déjà active sur {court.name}: {existing_session.recording_id}')
            print(f'   Temps restant: {existing_session.get_remaining_minutes()} min')
        else:
            # 4. Créer une nouvelle session d'enregistrement
            recording_id = f"test_rec_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
            
            session = RecordingSession(
                recording_id=recording_id,
                user_id=player.id,
                court_id=court.id,
                club_id=1,
                planned_duration=60,  # 60 minutes
                start_time=datetime.utcnow()
            )
            
            db.session.add(session)
            
            # 5. Mettre à jour le terrain
            court.is_recording = True
            court.current_recording_id = recording_id
            
            db.session.commit()
            
            print(f'✅ Session créée:')
            print(f'   - ID: {recording_id}')
            print(f'   - Terrain: {court.name}')
            print(f'   - Joueur: {player.name}')
            print(f'   - Durée: 60 minutes')
            print(f'   - Temps restant: {session.get_remaining_minutes()} min')
        
        # 6. Vérifier l'état de tous les terrains du club 1
        print('\n🏢 État des terrains du club 1:')
        all_courts = Court.query.filter_by(club_id=1).all()
        for c in all_courts:
            active_session = RecordingSession.query.filter_by(
                court_id=c.id,
                status='active'
            ).first()
            
            if active_session and not active_session.is_expired():
                player_name = User.query.get(active_session.user_id).name
                print(f'🔴 {c.name}: OCCUPÉ par {player_name} ({active_session.get_remaining_minutes()} min restant)')
            else:
                print(f'🟢 {c.name}: DISPONIBLE')
        
        print('\n🔄 Maintenant, actualisez le dashboard club pour voir les changements')

if __name__ == "__main__":
    create_test_player_and_session()
