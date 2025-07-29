#!/usr/bin/env python3
"""
Test script pour déboguer le problème de durée des enregistrements
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime, timedelta
from src.models.user import db, User, Club, Court, RecordingSession, Video, UserRole
from src.main import create_app

def test_recording_duration():
    """Test pour vérifier le calcul de durée des enregistrements"""
    app = create_app()
    
    with app.app_context():
        print("=== Test de calcul de durée ===")
        
        # Trouver un club et un terrain
        club = Club.query.first()
        if not club:
            print("❌ Aucun club trouvé")
            return
            
        court = Court.query.filter_by(club_id=club.id).first()
        if not court:
            print("❌ Aucun terrain trouvé")
            return
            
        # Trouver un joueur
        player = User.query.filter_by(role=UserRole.PLAYER).first()
        if not player:
            print("❌ Aucun joueur trouvé")
            return
            
        print(f"✅ Club: {club.name}")
        print(f"✅ Terrain: {court.name}")
        print(f"✅ Joueur: {player.name}")
        
        # Créer un enregistrement de test
        start_time = datetime.utcnow() - timedelta(minutes=45)  # Démarré il y a 45 minutes
        
        test_recording = RecordingSession(
            recording_id=f"TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            user_id=player.id,
            court_id=court.id,
            club_id=club.id,
            planned_duration=60,
            start_time=start_time,
            status='active',
            title="Test Recording",
            description="Test pour déboguer la durée"
        )
        
        db.session.add(test_recording)
        db.session.commit()
        
        print(f"✅ Enregistrement de test créé avec ID: {test_recording.id}")
        print(f"   Start time: {test_recording.start_time}")
        print(f"   Status: {test_recording.status}")
        
        # Simuler l'arrêt par le club
        end_time = datetime.utcnow()
        test_recording.status = 'stopped'
        test_recording.end_time = end_time
        test_recording.stopped_by = 'club'
        
        # Calculer la durée
        duration_delta = end_time - start_time
        duration_seconds = duration_delta.total_seconds()
        duration_minutes = max(1, int(duration_seconds / 60))
        
        print(f"📊 Calcul de durée:")
        print(f"   Start: {start_time}")
        print(f"   End: {end_time}")
        print(f"   Delta: {duration_delta}")
        print(f"   Secondes: {duration_seconds}")
        print(f"   Minutes: {duration_minutes}")
        
        # Créer la vidéo
        video_title = f"Test Match - {court.name}"
        
        new_video = Video(
            title=video_title,
            description=f"Test automatique sur {court.name}",
            duration=duration_minutes,
            user_id=player.id,
            court_id=court.id,
            recorded_at=start_time,
            is_unlocked=True,
            credits_cost=0
        )
        
        db.session.add(new_video)
        db.session.commit()
        
        print(f"✅ Vidéo créée avec ID: {new_video.id}")
        print(f"   Titre: {new_video.title}")
        print(f"   Durée: {new_video.duration} minutes")
        print(f"   Joueur: {player.name}")
        
        # Vérifier que la vidéo est bien dans les vidéos du joueur
        player_videos = Video.query.filter_by(user_id=player.id).all()
        print(f"🎥 Total vidéos du joueur: {len(player_videos)}")
        
        # Nettoyer le test
        db.session.delete(new_video)
        db.session.delete(test_recording)
        db.session.commit()
        
        print("🧹 Test nettoyé")
        print("=== Test terminé ===")

if __name__ == "__main__":
    test_recording_duration()
