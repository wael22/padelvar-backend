#!/usr/bin/env python3
"""
Script pour créer une session d'enregistrement de test sur le terrain 2 du club1
afin de tester l'affichage "Occupé"
"""

from src.models.user import *
from src.main import create_app
from datetime import datetime, timedelta
import uuid

def create_test_recording():
    app = create_app()
    with app.app_context():
        print('=== CRÉATION D\'UNE SESSION TEST ===')
        
        # Trouver le terrain 2 du club 1 (Terrain Annexe)
        court = Court.query.filter_by(club_id=1, name='Terrain Annexe').first()
        if not court:
            print('❌ Terrain Annexe non trouvé')
            return
        
        # Trouver un joueur pour la session
        player = User.query.filter_by(role=UserRole.PLAYER, club_id=1).first()
        if not player:
            print('❌ Aucun joueur trouvé pour le club 1')
            return
        
        # Créer une nouvelle session d'enregistrement
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
        
        # Mettre à jour le terrain
        court.is_recording = True
        court.current_recording_id = recording_id
        
        db.session.commit()
        
        print(f'✅ Session créée:')
        print(f'   - ID: {recording_id}')
        print(f'   - Terrain: {court.name}')
        print(f'   - Joueur: {player.name}')
        print(f'   - Durée: 60 minutes')
        print(f'   - Temps restant: {session.get_remaining_minutes()} min')
        
        print('\n🔄 Maintenant, actualisez le dashboard club pour voir "Occupé"')

if __name__ == "__main__":
    create_test_recording()
