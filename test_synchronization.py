#!/usr/bin/env python3
"""
Test de synchronisation entre joueur et club après arrêt d'enregistrement
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime, timedelta
from src.models.user import db, User, Club, Court, RecordingSession, Video, UserRole
from src.main import create_app

def test_synchronization():
    """Test de synchronisation après arrêt par le club"""
    app = create_app()
    
    with app.app_context():
        print("=== Test de Synchronisation ===")
        
        # Trouver un club et un terrain
        club = Club.query.first()
        court = Court.query.filter_by(club_id=club.id).first()
        player = User.query.filter_by(role=UserRole.PLAYER).first()
        
        print(f"✅ Setup:")
        print(f"   Club: {club.name}")
        print(f"   Terrain: {court.name}")
        print(f"   Joueur: {player.name}")
        
        # 1. État initial du terrain
        print(f"\n🏁 État initial:")
        print(f"   Terrain is_recording: {court.is_recording}")
        print(f"   Terrain current_recording_id: {court.current_recording_id}")
        
        # 2. Simuler le démarrage d'un enregistrement
        start_time = datetime.utcnow() - timedelta(minutes=20)
        
        recording = RecordingSession(
            recording_id=f"SYNC_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            user_id=player.id,
            court_id=court.id,
            club_id=club.id,
            planned_duration=90,
            start_time=start_time,
            status='active',
            title="Test Sync",
            description="Test de synchronisation"
        )
        
        # Marquer le terrain comme occupé
        court.is_recording = True
        court.current_recording_id = recording.recording_id
        
        db.session.add(recording)
        db.session.commit()
        
        print(f"\n🎬 Après démarrage enregistrement:")
        print(f"   Enregistrement ID: {recording.id}")
        print(f"   Terrain is_recording: {court.is_recording}")
        print(f"   Terrain current_recording_id: {court.current_recording_id}")
        print(f"   Status: {recording.status}")
        
        # 3. Simuler l'arrêt par le club (comme dans notre fonction corrigée)
        print(f"\n🛑 Simulation arrêt par le club...")
        
        # Arrêter l'enregistrement
        recording.status = 'stopped'
        recording.end_time = datetime.utcnow()
        recording.stopped_by = 'club'
        
        # IMPORTANT: Libérer le terrain (notre correction)
        court.is_recording = False
        court.current_recording_id = None
        
        # Calculer la durée
        duration_delta = recording.end_time - recording.start_time
        duration_minutes = max(1, int(duration_delta.total_seconds() / 60))
        
        # Créer la vidéo
        video = Video(
            title=f"Test Match - {court.name}",
            description=f"Test automatique sur {court.name}",
            duration=duration_minutes,
            user_id=recording.user_id,
            court_id=court.id,
            recorded_at=recording.start_time,
            is_unlocked=True,
            credits_cost=0
        )
        
        db.session.add(video)
        db.session.commit()
        
        print(f"✅ Après arrêt par le club:")
        print(f"   Enregistrement status: {recording.status}")
        print(f"   Terrain is_recording: {court.is_recording}")
        print(f"   Terrain current_recording_id: {court.current_recording_id}")
        print(f"   Vidéo créée: {video.title} ({video.duration}m)")
        
        # 4. Vérifier le statut côté joueur
        print(f"\n📱 Vérification côté joueur:")
        
        # Simuler la requête côté joueur pour les terrains disponibles
        courts_list = Court.query.filter_by(club_id=club.id).all()
        
        for c in courts_list:
            status = "DISPONIBLE" if not c.is_recording else "OCCUPÉ"
            print(f"   {c.name}: {status}")
            
            if c.is_recording and c.current_recording_id:
                active_rec = RecordingSession.query.filter_by(
                    recording_id=c.current_recording_id,
                    status='active'
                ).first()
                if active_rec:
                    print(f"     -> Enregistrement actif: {active_rec.recording_id}")
                else:
                    print(f"     -> Enregistrement ID {c.current_recording_id} mais pas actif")
        
        # 5. Test de la fonction de nettoyage automatique
        print(f"\n🧹 Test nettoyage automatique:")
        
        # Compter les sessions arrêtées
        stopped_sessions = RecordingSession.query.filter_by(
            club_id=club.id,
            status='stopped'
        ).count()
        
        active_sessions = RecordingSession.query.filter_by(
            club_id=club.id,
            status='active'
        ).count()
        
        print(f"   Sessions arrêtées: {stopped_sessions}")
        print(f"   Sessions actives: {active_sessions}")
        
        # 6. Nettoyer le test
        print(f"\n🧹 Nettoyage du test...")
        db.session.delete(video)
        db.session.delete(recording)
        db.session.commit()
        
        print("✅ Test de synchronisation terminé!")

if __name__ == "__main__":
    test_synchronization()
