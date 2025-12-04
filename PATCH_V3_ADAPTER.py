# PATCH pour recording.py
# Remplacer la fonction start_recording_v3 (lignes 572-636)

@recording_bp.route('/v3/start', methods=['POST'])
def start_recording_v3():
    """🆕 ADAPTATEUR: Redirige vers le nouveau système vidéo stable"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        # 🆕 Utiliser le NOUVEAU système vidéo stable
        from src.video_system.session_manager import session_manager
        from src.video_system.recording import video_recorder
        
        data = request.get_json()
        court_id = data.get('court_id')
        duration_minutes = data.get('duration_minutes', 90)
        
        if not court_id:
            return jsonify({'error': 'court_id requis'}), 400
        
        # Get court
        court = Court.query.get(court_id)
        if not court:
            return jsonify({'error': 'Terrain non trouvé'}), 404
        
        if not court.camera_url:
            return jsonify({'error': f'Caméra non configurée pour le terrain {court_id}'}), 400
        
        logger.info(f"🎬 V3 Adapter: Nouvelle demande d'enregistrement - Terrain {court_id}")
        
        # 1. Créer session caméra
        try:
            session = session_manager.create_session(
                terrain_id=court_id,
                camera_url=court.camera_url,
                club_id=court.club_id,
                user_id=user.id
            )
            logger.info(f"✅ Session créée: {session.session_id}")
        except Exception as e:
            logger.error(f"❌ Erreur création session: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Erreur création session: {str(e)}'
            }), 500
        
        # 2. Démarrer enregistrement
        try:
            success = video_recorder.start_recording(
                session=session,
                duration_seconds=duration_minutes * 60
            )
            
            if not success:
                session_manager.close_session(session.session_id)
                return jsonify({
                    'success': False,
                    'error': 'Échec démarrage enregistrement'
                }), 500
            
            logger.info(f"✅ Enregistrement démarré via nouveau système: {session.session_id}")
            
            # Retourner format compatible avec l'ancien système
            return jsonify({
                'success': True,
                'message': 'Enregistrement démarré',
                'recording_id': session.session_id,
                'recording_info': {
                    'session_id': session.session_id,
                    'terrain_id': court_id,
                    'duration_seconds': duration_minutes * 60
                }
            }), 201
            
        except Exception as e:
            logger.error(f"❌ Erreur démarrage enregistrement: {e}", exc_info=True)
            session_manager.close_session(session.session_id)
            return jsonify({
                'success': False,
                'error': f'Erreur enregistrement: {str(e)}'
            }), 500
        
    except Exception as e:
        logger.error(f"Error in v3 adapter: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Erreur: {str(e)}'
        }), 500


# Instructions:
# 1. Ouvrir src/routes/recording.py
# 2. Localiser @recording_bp.route('/v3/start', methods=['POST']) (ligne 572)
# 3. Remplacer toute la fonction jusqu'à la ligne 636
# 4. Coller ce nouveau code
# 5. Sauvegarder
# 6. Redémarrer le serveur
