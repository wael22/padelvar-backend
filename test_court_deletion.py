#!/usr/bin/env python3
"""
Diagnostic pour voir ce qui empêche la suppression du terrain ID 6
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.models.user import db, Court, Video, RecordingSession
from src.main import create_app

def diagnose_court_deletion(court_id):
    """Diagnostiquer pourquoi un terrain ne peut pas être supprimé"""
    app = create_app()
    
    with app.app_context():
        print(f"=== Diagnostic Terrain ID: {court_id} ===")
        
        # Vérifier si le terrain existe
        court = Court.query.get(court_id)
        if not court:
            print(f"❌ Terrain {court_id} n'existe pas")
            return
            
        print(f"✅ Terrain trouvé: {court.name} (Club ID: {court.club_id})")
        
        # Vérifier les vidéos liées
        videos = Video.query.filter_by(court_id=court_id).all()
        print(f"📹 Vidéos liées: {len(videos)}")
        for video in videos:
            print(f"   - Vidéo {video.id}: {video.title} (Joueur ID: {video.user_id})")
        
        # Vérifier les sessions d'enregistrement
        recording_sessions = RecordingSession.query.filter_by(court_id=court_id).all()
        print(f"🎬 Sessions d'enregistrement: {len(recording_sessions)}")
        for session in recording_sessions:
            print(f"   - Session {session.id}: {session.recording_id} (Statut: {session.status})")
        
        # Vérifier les terrains avec des enregistrements actifs
        if court.is_recording:
            print(f"⚠️ Terrain en cours d'enregistrement: {court.current_recording_id}")
        
        print(f"\n📊 Résumé:")
        print(f"   Vidéos à déplacer: {len(videos)}")
        print(f"   Sessions à supprimer: {len(recording_sessions)}")
        print(f"   Terrain actif: {'Oui' if court.is_recording else 'Non'}")
        
        if len(videos) == 0 and len(recording_sessions) == 0:
            print("✅ Le terrain peut être supprimé sans contraintes")
        else:
            print("⚠️ Des contraintes existent, mais notre fonction corrigée peut les gérer")

if __name__ == "__main__":
    diagnose_court_deletion(6)
