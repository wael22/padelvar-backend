"""
Routes pour la gestion avancée des enregistrements
Fonctionnalités : durée sélectionnable, arrêt automatique, gestion par club
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
import uuid
import logging
import json
import os

from ..models.database import db
from ..models.user import (
    User, Club, Court, Video, RecordingSession, 
    ClubActionHistory, UserRole
)
from ..services.video_capture_service_ultimate import (
    DirectVideoCaptureService
)

# Instance globale du service
video_capture_service = DirectVideoCaptureService()

logger = logging.getLogger(__name__)

recording_bp = Blueprint('recording', __name__, url_prefix='/api/recording')

def get_current_user():
    """Récupérer l'utilisateur actuel"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

def log_recording_action(session_obj, action_type, action_details, performed_by_id):
    """Log d'action pour les enregistrements avec gestion d'erreur améliorée"""
    try:
        # Convertir les détails en JSON si nécessaire
        if isinstance(action_details, dict):
            details_json = json.dumps(action_details)
        elif isinstance(action_details, str):
            details_json = action_details
        else:
            details_json = json.dumps({"raw_details": str(action_details)})
        
        action_history = ClubActionHistory(
            club_id=session_obj.club_id,
            user_id=session_obj.user_id,
            action_type=action_type,
            action_details=details_json,
            performed_by_id=performed_by_id,
            performed_at=datetime.utcnow()
        )
        db.session.add(action_history)
        # Ne pas faire de flush ici pour éviter les problèmes de transaction
        logger.info(f"Action d'enregistrement préparée: {action_type}")
    except Exception as e:
        logger.error(f"Erreur lors du logging: {e}")
        # Ne pas lever l'exception pour ne pas interrompre le flux principal

def cleanup_expired_sessions(club_id=None):
    """Nettoyer toutes les sessions expirées pour un club ou globalement"""
    try:
        if club_id:
            expired_sessions = RecordingSession.query.filter_by(
                club_id=club_id,
                status='active'
            ).all()
        else:
            expired_sessions = RecordingSession.query.filter_by(status='active').all()
        
        cleaned_count = 0
        for session in expired_sessions:
            if session.is_expired():
                logger.info(f"Nettoyage automatique de la session expirée: {session.recording_id}")
                _stop_recording_session(session, 'auto', session.user_id)
                cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"Nettoyage terminé: {cleaned_count} sessions expirées fermées")
        
        return cleaned_count
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage automatique: {e}")
        return 0

# ====================================================================
# ROUTES DE DÉMARRAGE D'ENREGISTREMENT
# ====================================================================

@recording_bp.route('/start', methods=['POST'])
@recording_bp.route('/v3/start', methods=['POST'])  # Nouvelle route v3 pour compatibilité frontend
def start_recording_with_duration():
    """Démarrer un enregistrement avec durée sélectionnable"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        data = request.get_json()
        court_id = data.get('court_id')
        duration = data.get('duration', 90)  # défaut: 90 minutes
        title = data.get('title', '')
        description = data.get('description', '')
        
        if not court_id:
            return jsonify({'error': 'Court ID requis'}), 400
        
        # Vérifier que le terrain existe et n'est pas occupé
        court = Court.query.get(court_id)
        if not court:
            return jsonify({'error': 'Terrain non trouvé'}), 404
        
        # Nettoyer les sessions expirées pour ce club avant de vérifier la disponibilité
        cleanup_expired_sessions(court.club_id)
        
        if court.is_recording:
            return jsonify({
                'error': 'Ce terrain est déjà utilisé pour un enregistrement',
                'current_recording_id': court.current_recording_id
            }), 409
        
        # Vérifier que l'utilisateur a des crédits
        if user.credits_balance < 1:
            return jsonify({'error': 'Crédits insuffisants'}), 400
        
        # Vérifier que l'utilisateur n'a pas déjà un enregistrement en cours
        existing_session = RecordingSession.query.filter_by(
            user_id=user.id,
            status='active'
        ).first()
        
        if existing_session:
            return jsonify({
                'error': 'Vous avez déjà un enregistrement en cours',
                'existing_recording': existing_session.to_dict()
            }), 409
        
        # Convertir la durée en minutes
        if duration == 'MAX':
            planned_duration = 200
        else:
            planned_duration = int(duration)
            if planned_duration not in [60, 90, 120, 200]:
                return jsonify({'error': 'Durée invalide. Utilisez 60, 90, 120 ou MAX'}), 400
        
        # Générer un ID unique pour l'enregistrement
        recording_id = f"rec_{user.id}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        
        # Créer la session d'enregistrement
        recording_session = RecordingSession(
            recording_id=recording_id,
            user_id=user.id,
            court_id=court_id,
            club_id=court.club_id,
            planned_duration=planned_duration,
            title=title or f'Match du {datetime.now().strftime("%d/%m/%Y %H:%M")}',
            description=description,
            status='active'
        )
        
        # Réserver le terrain
        court.is_recording = True
        court.current_recording_id = recording_id
        
        # Débiter un crédit
        user.credits_balance -= 1
        
        # Ajouter tous les objets à la session
        db.session.add(recording_session)
        
        # Log de l'action (sera ajouté à la session mais pas encore commité)
        log_recording_action(
            recording_session,
            'start_recording',
            {
                'court_name': court.name,
                'duration_minutes': planned_duration,
                'credits_used': 1,
                'new_balance': user.credits_balance
            },
            user.id
        )
        
        # Faire le commit de toutes les modifications en une fois
        db.session.commit()
        
        logger.info(f"Enregistrement démarré: {recording_id} sur terrain {court_id}")
        
        # ✨ DÉMARRER LA CAPTURE VIDÉO RÉELLE avec FFmpeg
        try:
            # Construire les paramètres pour la capture vidéo
            # Correspondance terrain → caméra
            camera_mapping = {
                1: "http://212.231.225.55:88/axis-cgi/mjpg/video.cgi",  # Terrain 1 - Axis
                2: "http://212.231.225.55:88/axis-cgi/mjpg/video.cgi",  # Terrain 2 - Axis
                4: "http://213.3.30.80:6001/mjpg/video.mjpg",          # Terrain 3 - MJPG
                5: "http://213.3.30.80:6001/mjpg/video.mjpg"           # Terrain 4 - MJPG
            }
            
            camera_url = camera_mapping.get(court_id, camera_mapping[1])  # Fallback Terrain 1
            logger.info(f"🎥 Terrain {court_id} → Caméra: {camera_url}")
            
            output_path = f"static/videos/{recording_id}.mp4"
            max_duration = planned_duration * 60  # Convertir en secondes
            
            capture_success = video_capture_service.start_recording(
                session_id=recording_id,
                camera_url=camera_url,
                output_path=output_path,
                max_duration=max_duration,
                user_id=user.id,
                court_id=court_id,
                session_name=title or f'Match du {datetime.now().strftime("%d/%m/%Y %H:%M")}'
            )
            
            if capture_success:
                logger.info(f"✅ Capture vidéo démarrée avec succès pour {recording_id}")
            else:
                logger.warning(f"⚠️ Erreur démarrage capture vidéo pour {recording_id}")
                # Ne pas bloquer l'enregistrement, mais noter l'erreur
                
        except Exception as capture_error:
            logger.error(f"❌ Erreur critique capture vidéo {recording_id}: {capture_error}")
            # Ne pas annuler l'enregistrement, la DB est déjà commitée
        
        # Préparer la réponse après le commit réussi
        response_data = {
            'message': 'Enregistrement démarré avec succès',
            'recording_session': recording_session.to_dict(),
            'court': court.to_dict(),
            'user_credits': user.credits_balance
        }
        
        return jsonify(response_data), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors du démarrage d'enregistrement: {str(e)}")
        logger.error(f"Type d'erreur: {type(e).__name__}")
        logger.error(f"Traceback: ", exc_info=True)
        return jsonify({
            'error': f'Erreur lors du démarrage: {str(e)}',
            'error_type': type(e).__name__
        }), 500

# ====================================================================
# ROUTES D'ARRÊT D'ENREGISTREMENT
# ====================================================================

@recording_bp.route('/stop', methods=['POST'])
@recording_bp.route('/v3/stop/<recording_id>', methods=['POST'])  # Route v3 pour compatibilité
def stop_recording(recording_id=None):
    """Arrêter un enregistrement (par le joueur)"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        # Si recording_id n'est pas dans l'URL, le chercher dans le JSON
        if not recording_id:
            data = request.get_json()
            recording_id = data.get('recording_id')
        
        if not recording_id:
            return jsonify({'error': 'Recording ID requis'}), 400
        
        # Récupérer la session d'enregistrement
        recording_session = RecordingSession.query.filter_by(
            recording_id=recording_id,
            user_id=user.id,
            status='active'
        ).first()
        
        if not recording_session:
            return jsonify({'error': 'Session d\'enregistrement non trouvée ou déjà terminée'}), 404
        
        # Arrêter l'enregistrement
        return _stop_recording_session(recording_session, 'player', user.id)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de l'arrêt d'enregistrement: {e}")
        return jsonify({'error': 'Erreur lors de l\'arrêt'}), 500

@recording_bp.route('/force-stop/<recording_id>', methods=['POST'])
@recording_bp.route('/v3/force-stop/<recording_id>', methods=['POST'])  # Route v3
def force_stop_recording(recording_id):
    """Arrêter un enregistrement (par le club)"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    if user.role != UserRole.CLUB:
        return jsonify({'error': 'Accès réservé aux clubs'}), 403
    
    try:
        # Récupérer la session d'enregistrement
        recording_session = RecordingSession.query.filter_by(
            recording_id=recording_id,
            club_id=user.club_id,
            status='active'
        ).first()
        
        if not recording_session:
            return jsonify({'error': 'Session d\'enregistrement non trouvée'}), 404
        
        # Arrêter l'enregistrement
        return _stop_recording_session(recording_session, 'club', user.id)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de l'arrêt forcé: {e}")
        return jsonify({'error': 'Erreur lors de l\'arrêt forcé'}), 500

def _stop_recording_session(recording_session, stopped_by, performed_by_id):
    """Fonction utilitaire pour arrêter une session d'enregistrement"""
    try:
        # Mettre à jour la session
        recording_session.status = 'stopped'
        recording_session.stopped_by = stopped_by
        recording_session.end_time = datetime.utcnow()
        
        # Libérer le terrain
        court = Court.query.get(recording_session.court_id)
        if court:
            court.is_recording = False
            court.current_recording_id = None
        
        # Créer la vidéo
        elapsed_minutes = recording_session.get_elapsed_minutes()
        
        # � LOGS DÉTAILLÉS DURÉE - Début analyse
        logger.info(f"🕐 ANALYSE DURÉE pour {recording_session.recording_id}:")
        logger.info(f"   📅 Start time: {recording_session.start_time}")
        logger.info(f"   📅 End time: {recording_session.end_time}")
        logger.info(f"   ⏱️ Durée calculée DB: {elapsed_minutes:.2f} minutes = {elapsed_minutes * 60:.0f} secondes")
        
        # �🔍 VÉRIFICATION DURÉE RÉELLE avec ffprobe (CORRECTION CRITIQUE)
        video_file_path = f"static/videos/{recording_session.recording_id}.mp4"
        real_duration_seconds = None
        
        logger.info(f"🔍 Vérification fichier vidéo: {video_file_path}")
        
        if os.path.exists(video_file_path):
            file_size = os.path.getsize(video_file_path)
            logger.info(f"📁 Fichier trouvé: {file_size:,} bytes")
            
            try:
                # Utiliser le service pour obtenir la durée réelle du fichier vidéo
                logger.info("🔍 Lecture durée réelle avec ffprobe...")
                real_duration_seconds = video_capture_service._get_video_duration_accurate(video_file_path)
                
                if real_duration_seconds:
                    real_duration_minutes = real_duration_seconds / 60
                    difference_seconds = abs(real_duration_seconds - (elapsed_minutes * 60))
                    difference_minutes = difference_seconds / 60
                    
                    logger.info(f"📊 COMPARAISON DURÉES:")
                    logger.info(f"   🗄️ DB (start-end): {elapsed_minutes:.2f} min = {elapsed_minutes * 60:.0f}s")
                    logger.info(f"   🎥 Fichier réel:   {real_duration_minutes:.2f} min = {real_duration_seconds:.0f}s")
                    logger.info(f"   📈 Différence:     {difference_minutes:.2f} min = {difference_seconds:.0f}s")
                    
                    if difference_seconds > 10:  # Différence significative
                        logger.warning(f"⚠️ ÉCART IMPORTANT détecté: {difference_seconds:.0f}s d'écart!")
                        logger.warning("🔧 Utilisation durée réelle du fichier (correction appliquée)")
                    else:
                        logger.info("✅ Durées cohérentes - fichier et DB correspondent")
                else:
                    logger.warning("⚠️ Impossible de lire durée réelle - utilisation durée DB")
            except Exception as e:
                logger.error(f"❌ Erreur lecture durée réelle: {e}")
        else:
            logger.warning(f"⚠️ Fichier vidéo non trouvé: {video_file_path}")
        
        # Utiliser durée réelle si disponible, sinon fallback sur durée DB
        final_duration = real_duration_seconds if real_duration_seconds else (elapsed_minutes * 60)
        
        # 📊 LOGS DÉTAILLÉS - Résultat final
        logger.info(f"🎯 DURÉE FINALE RETENUE:")
        logger.info(f"   💾 Stockage en DB: {final_duration:.0f} secondes = {final_duration/60:.2f} minutes")
        logger.info(f"   🔄 Source: {'📹 Fichier réel (ffprobe)' if real_duration_seconds else '🗄️ Calcul DB (fallback)'}")
        
        video = Video(
            user_id=recording_session.user_id,
            court_id=recording_session.court_id,
            title=recording_session.title,
            description=recording_session.description,
            duration=final_duration,  # ✅ DURÉE RÉELLE du fichier vidéo
            file_url=f'/videos/rec_{recording_session.recording_id}.mp4',
            is_unlocked=True
        )
        
        db.session.add(video)
        
        # Log de l'action
        log_recording_action(
            recording_session,
            'stop_recording',
            {
                'stopped_by': stopped_by,
                'duration_minutes': elapsed_minutes,
                'court_name': court.name if court else 'Inconnu'
            },
            performed_by_id
        )
        
        db.session.commit()
        
        # ✨ ARRÊTER LA CAPTURE VIDÉO RÉELLE
        try:
            stop_success = video_capture_service.stop_recording(recording_session.recording_id)
            
            if stop_success:
                logger.info(f"✅ Capture vidéo arrêtée avec succès pour {recording_session.recording_id}")
            else:
                logger.warning(f"⚠️ Erreur arrêt capture vidéo pour {recording_session.recording_id}")
                
        except Exception as capture_error:
            logger.error(f"❌ Erreur critique arrêt capture {recording_session.recording_id}: {capture_error}")
        
        # 🚀 UPLOAD AUTOMATIQUE VERS BUNNY CDN
        try:
            from ..services.bunny_storage_service import bunny_storage_service
            
            # Chemin du fichier vidéo local
            video_file_path = f"static/videos/{recording_session.recording_id}.mp4"
            
            if os.path.exists(video_file_path):
                # 🔧 RÉPARATION AUTOMATIQUE MP4 avant upload (CORRECTION CRITIQUE)
                logger.info(f"🔧 Vérification/réparation MP4 avant upload...")
                
                try:
                    # Utiliser la fonction de réparation du service vidéo
                    repair_success = video_capture_service._repair_video_metadata(video_file_path)
                    if repair_success:
                        logger.info("✅ MP4 réparé/validé - prêt pour upload")
                        # Re-vérifier la durée après réparation
                        repaired_duration = video_capture_service._get_video_duration_accurate(video_file_path)
                        if repaired_duration and repaired_duration != final_duration:
                            logger.info(f"📊 Durée mise à jour après réparation: {repaired_duration}s")
                            video.duration = repaired_duration
                            db.session.commit()
                    else:
                        logger.warning("⚠️ Réparation MP4 échouée - upload du fichier original")
                except Exception as repair_error:
                    logger.error(f"❌ Erreur réparation MP4: {repair_error}")
                
                logger.info(f"📤 Démarrage upload Bunny pour {recording_session.recording_id}")
                
                # Upload immédiat vers Bunny
                success, video_id, stream_url = bunny_storage_service.upload_immediately(
                    local_path=video_file_path,
                    title=recording_session.title or f"Enregistrement automatique - {court.name if court else 'Terrain'}"
                )
                
                if success and stream_url:
                    # Mettre à jour l'URL de la vidéo avec l'URL Bunny
                    video.file_url = stream_url
                    video.bunny_video_id = video_id
                    db.session.commit()
                    
                    logger.info(f"✅ Upload Bunny réussi pour {recording_session.recording_id}")
                    logger.info(f"🎬 URL de streaming: {stream_url}")
                else:
                    logger.warning(f"⚠️ Échec upload Bunny pour {recording_session.recording_id}")
            else:
                logger.warning(f"📁 Fichier vidéo non trouvé: {video_file_path}")
                
        except Exception as bunny_error:
            logger.error(f"❌ Erreur upload Bunny {recording_session.recording_id}: {bunny_error}")
            # Ne pas faire échouer l'arrêt d'enregistrement pour autant
        
        logger.info(f"Enregistrement arrêté: {recording_session.recording_id} par {stopped_by}")
        
        return jsonify({
            'message': 'Enregistrement arrêté avec succès',
            'video': video.to_dict(),
            'session': recording_session.to_dict(),
            'stopped_by': stopped_by
        }), 200
        
    except Exception as e:
        db.session.rollback()
        raise e

# ====================================================================
# ROUTES DE CONSULTATION
# ====================================================================

@recording_bp.route('/my-active', methods=['GET'])
@recording_bp.route('/v3/my-active', methods=['GET'])  # Route v3
def get_my_active_recording():
    """Récupérer l'enregistrement actif de l'utilisateur"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        recording_session = RecordingSession.query.filter_by(
            user_id=user.id,
            status='active'
        ).first()
        
        if not recording_session:
            return jsonify({'active_recording': None}), 200
        
        # Vérifier si l'enregistrement a expiré
        if recording_session.is_expired():
            # Arrêter automatiquement l'enregistrement expiré
            _stop_recording_session(recording_session, 'auto', user.id)
            return jsonify({'active_recording': None, 'message': 'Enregistrement expiré et arrêté automatiquement'}), 200
        
        # Enrichir avec les données du terrain et club
        court = Court.query.get(recording_session.court_id)
        club = Club.query.get(recording_session.club_id)
        
        result = recording_session.to_dict()
        if court:
            result['court'] = court.to_dict()
        if club:
            result['club'] = club.to_dict()
        
        return jsonify({'active_recording': result}), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'enregistrement actif: {e}")
        return jsonify({'error': 'Erreur lors de la récupération'}), 500

@recording_bp.route('/club/active', methods=['GET'])
@recording_bp.route('/v3/club/active', methods=['GET'])  # Route v3
def get_club_active_recordings():
    """Récupérer tous les enregistrements actifs d'un club"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    if user.role != UserRole.CLUB:
        return jsonify({'error': 'Accès réservé aux clubs'}), 403
    
    try:
        # Récupérer toutes les sessions actives du club
        active_sessions = RecordingSession.query.filter_by(
            club_id=user.club_id,
            status='active'
        ).all()
        
        # Enrichir avec les données utilisateur et terrain
        recordings_data = []
        for session in active_sessions:
            session_data = session.to_dict()
            
            # Ajouter les infos utilisateur
            player = User.query.get(session.user_id)
            if player:
                session_data['player'] = {
                    'id': player.id,
                    'name': player.name,
                    'email': player.email
                }
            
            # Ajouter les infos terrain
            court = Court.query.get(session.court_id)
            if court:
                session_data['court'] = court.to_dict()
            
            recordings_data.append(session_data)
        
        return jsonify({
            'active_recordings': recordings_data,
            'count': len(recordings_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des enregistrements du club: {e}")
        return jsonify({'error': 'Erreur lors de la récupération'}), 500

@recording_bp.route('/v3/clubs/<int:club_id>/courts', methods=['GET'])
def get_available_courts(club_id):
    """Récupérer les terrains disponibles d'un club"""
    print(f"=== DEBUG TERRAINS DISPONIBLES ===")
    print(f"Club ID demandé: {club_id}")
    
    user = get_current_user()
    if not user:
        print("❌ Utilisateur non authentifié")
        return jsonify({'error': 'Non authentifié'}), 401
    
    print(f"👤 Utilisateur: {user.email} (ID: {user.id})")
    
    try:
        # Nettoyer automatiquement les enregistrements expirés pour ce club
        cleanup_expired_sessions(club_id)
        
        # Récupérer tous les terrains du club
        courts = Court.query.filter_by(club_id=club_id).all()
        print(f"🏟️ Terrains trouvés pour club {club_id}: {len(courts)}")
        
        courts_data = []
        for court in courts:
            court_data = court.to_dict()
            print(f"📍 Terrain '{court.name}' (ID: {court.id}) - Disponible: {court_data['available']}")
            
            # Si le terrain est en cours d'enregistrement, ajouter les détails
            if court.is_recording and court.current_recording_id:
                recording_session = RecordingSession.query.filter_by(
                    recording_id=court.current_recording_id,
                    status='active'
                ).first()
                
                if recording_session and not recording_session.is_expired():
                    player = User.query.get(recording_session.user_id)
                    court_data['recording_info'] = {
                        'player_name': player.name if player else 'Inconnu',
                        'start_time': recording_session.start_time.isoformat(),
                        'planned_duration': recording_session.planned_duration,
                        'elapsed_minutes': recording_session.get_elapsed_minutes(),
                        'remaining_minutes': recording_session.get_remaining_minutes()
                    }
            
            courts_data.append(court_data)
        
        print(f"✅ Réponse API: {len(courts_data)} terrains retournés")
        print(f"📋 Terrains: {[c['name'] for c in courts_data]}")
        
        # Créer la réponse avec headers anti-cache
        response = jsonify({'courts': courts_data})
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response, 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des terrains: {e}")
        return jsonify({'error': 'Erreur lors de la récupération'}), 500

# ====================================================================
# TÂCHE DE NETTOYAGE AUTOMATIQUE
# ====================================================================

@recording_bp.route('/cleanup-expired', methods=['POST'])
@recording_bp.route('/v3/cleanup-expired', methods=['POST'])  # Route v3
def cleanup_expired_recordings():
    """Nettoyer les enregistrements expirés (tâche de maintenance)"""
    user = get_current_user()
    if not user or user.role != UserRole.SUPER_ADMIN:
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    try:
        # Récupérer toutes les sessions actives expirées
        expired_sessions = RecordingSession.query.filter_by(status='active').all()
        expired_count = 0
        
        for session in expired_sessions:
            if session.is_expired():
                _stop_recording_session(session, 'auto', user.id)
                expired_count += 1
        
        logger.info(f"Nettoyage automatique: {expired_count} enregistrements expirés arrêtés")
        
        return jsonify({
            'message': f'{expired_count} enregistrements expirés ont été arrêtés',
            'expired_count': expired_count
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage: {e}")
        return jsonify({'error': 'Erreur lors du nettoyage'}), 500
