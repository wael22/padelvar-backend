#!/usr/bin/env python3
"""
Test complet du workflow d'enregistrement et d'arrêt par le club
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime, timedelta
from src.models.user import db, User, Club, Court, RecordingSession, Video, UserRole
from src.main import create_app

def test_complete_workflow():
    """Test complet du workflow d'enregistrement"""
    app = create_app()
    
    with app.app_context():
        print("=== Test Workflow Complet ===")
        
        # Trouver un club et un terrain
        club = Club.query.first()
        court = Court.query.filter_by(club_id=club.id).first()
        player = User.query.filter_by(role=UserRole.PLAYER).first()
        
        print(f"✅ Setup:")
        print(f"   Club: {club.name}")
        print(f"   Terrain: {court.name}")
        print(f"   Joueur: {player.name}")
        
        # 1. Créer un enregistrement actif (simuler le joueur qui démarre)
        start_time = datetime.utcnow() - timedelta(minutes=30)  # Il y a 30 minutes
        
        recording = RecordingSession(
            recording_id=f"WORKFLOW_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            user_id=player.id,
            court_id=court.id,
            club_id=club.id,
            planned_duration=90,  # 90 minutes planifiées
            start_time=start_time,
            status='active',
            title="Match Test Workflow",
            description="Test du workflow complet"
        )
        
        db.session.add(recording)
        db.session.commit()
        
        print(f"🎬 Enregistrement créé:")
        print(f"   ID: {recording.id}")
        print(f"   Status: {recording.status}")
        print(f"   Démarré: {recording.start_time}")
        print(f"   Durée planifiée: {recording.planned_duration} min")
        
        # 2. Simuler l'arrêt par le club (comme le fait la route)
        print(f"\n🛑 Simulation arrêt par le club...")
        
        # Arrêter l'enregistrement
        recording.status = 'stopped'
        recording.end_time = datetime.utcnow()
        recording.stopped_by = 'club'
        
        # Calculer la durée
        duration_delta = recording.end_time - recording.start_time
        duration_seconds = duration_delta.total_seconds()
        duration_minutes = max(1, int(duration_seconds / 60))
        
        print(f"   Durée calculée: {duration_minutes} minutes ({duration_seconds} secondes)")
        
        # Créer la vidéo
        video_title = recording.title or f"Match du {recording.start_time.strftime('%d/%m/%Y')} - {court.name}"
        
        video = Video(
            title=video_title,
            description=recording.description or f"Enregistrement automatique sur {court.name}",
            duration=duration_minutes,  # EN MINUTES
            user_id=recording.user_id,
            court_id=court.id,
            recorded_at=recording.start_time,
            is_unlocked=True,
            credits_cost=0
        )
        
        db.session.add(video)
        db.session.commit()
        
        print(f"🎥 Vidéo créée:")
        print(f"   ID: {video.id}")
        print(f"   Titre: {video.title}")
        print(f"   Durée: {video.duration} minutes")
        print(f"   Joueur ID: {video.user_id}")
        print(f"   Débloquée: {video.is_unlocked}")
        print(f"   Coût: {video.credits_cost} crédits")
        
        # 3. Vérifier que la vidéo est dans les vidéos du joueur
        player_videos = Video.query.filter_by(user_id=player.id).all()
        print(f"\n📊 Vérification:")
        print(f"   Total vidéos du joueur: {len(player_videos)}")
        
        for v in player_videos:
            print(f"   - {v.title}: {v.duration} min")
        
        # 4. Test du formatage frontend
        print(f"\n🎨 Test formatage frontend:")
        
        # Simulation de la fonction JavaScript
        def format_duration_js(minutes):
            if not minutes:
                return 'N/A'
            
            # Si c'est déjà en minutes (notre nouveau format)
            if minutes < 200:
                return f"{minutes}m"
            
            # Si c'est en secondes (ancien format), convertir
            return f"{int(minutes / 60)}m"
        
        formatted = format_duration_js(video.duration)
        print(f"   Durée brute: {video.duration}")
        print(f"   Durée formatée: {formatted}")
        
        # 5. Nettoyer
        print(f"\n🧹 Nettoyage...")
        db.session.delete(video)
        db.session.delete(recording)
        db.session.commit()
        
        print("✅ Test terminé avec succès!")

if __name__ == "__main__":
    test_complete_workflow()
