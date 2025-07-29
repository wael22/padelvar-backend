#!/usr/bin/env python3
"""
Script de diagnostic pour vérifier l'état des sessions et terrains
"""

from src.models.user import *
from src.main import create_app

def diagnose_court_status():
    app = create_app()
    with app.app_context():
        print('=== DIAGNOSTIC DES SESSIONS ET TERRAINS ===')
        print()
        
        # 1. Vérifier les sessions actives
        sessions = RecordingSession.query.all()
        print(f'📊 Total sessions: {len(sessions)}')
        
        active_sessions = RecordingSession.query.filter_by(status='active').all()
        print(f'🎬 Sessions actives: {len(active_sessions)}')
        
        for session in active_sessions:
            print(f'  - Session {session.recording_id}:')
            print(f'    Court ID: {session.court_id}')
            print(f'    User ID: {session.user_id}')
            print(f'    Durée: {session.planned_duration} min')
            print(f'    Début: {session.start_time}')
            print(f'    Écoulé: {session.get_elapsed_minutes()} min')
            print(f'    Restant: {session.get_remaining_minutes()} min')
            print(f'    Expiré?: {session.is_expired()}')
            print()
        
        # 2. Vérifier l'état des terrains
        courts = Court.query.all()
        print(f'🎾 Total terrains: {len(courts)}')
        
        for court in courts:
            print(f'  - {court.name} (ID: {court.id}):')
            print(f'    is_recording: {court.is_recording}')
            print(f'    current_recording_id: {court.current_recording_id}')
            print(f'    club_id: {court.club_id}')
            print()
        
        # 3. Vérifier la cohérence
        print('🔍 COHÉRENCE SESSIONS vs TERRAINS:')
        for session in active_sessions:
            court = Court.query.get(session.court_id)
            if court:
                print(f'  Session {session.recording_id} -> Terrain {court.name}')
                session_active = session.status == 'active' and not session.is_expired()
                print(f'    Session active: {session_active}')
                print(f'    Terrain marqué recording: {court.is_recording}')
                print(f'    Recording ID match: {court.current_recording_id == session.recording_id}')
                
                if session_active != court.is_recording:
                    print(f'    ❌ INCOHÉRENCE DÉTECTÉE!')
                else:
                    print(f'    ✅ Cohérent')
                print()
        
        # 4. Recommandations de correction
        print('🔧 CORRECTIONS NÉCESSAIRES:')
        corrections_needed = False
        
        for session in active_sessions:
            court = Court.query.get(session.court_id)
            if court:
                session_active = session.status == 'active' and not session.is_expired()
                
                if session_active and not court.is_recording:
                    print(f'❌ Terrain {court.name} devrait être marqué comme recording')
                    corrections_needed = True
                elif not session_active and court.is_recording:
                    print(f'❌ Terrain {court.name} devrait être marqué comme libre')
                    corrections_needed = True
                    
                if session_active and court.current_recording_id != session.recording_id:
                    print(f'❌ Terrain {court.name} a un mauvais recording_id')
                    corrections_needed = True
        
        if not corrections_needed:
            print('✅ Aucune correction nécessaire')

if __name__ == "__main__":
    diagnose_court_status()
