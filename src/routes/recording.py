"""
Routes pour la gestion avancée des enregistrements
Fonctionnalités : durée sélectionnable, arrêt automatique, gestion par club
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
import uuid
import logging
import json

from ..models.database import db
from ..models.user import (
    User, Club, Court, Video, RecordingSession, 
    ClubActionHistory, UserRole
)

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
def stop_recording():
    """Arrêter un enregistrement (par le joueur)"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
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
        
        video = Video(
            user_id=recording_session.user_id,
            court_id=recording_session.court_id,
            title=recording_session.title,
            description=recording_session.description,
            duration=elapsed_minutes * 60,  # en secondes
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

@recording_bp.route('/available-courts/<int:club_id>', methods=['GET'])
def get_available_courts(club_id):
    """Récupérer les terrains disponibles d'un club"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        # Nettoyer automatiquement les enregistrements expirés pour ce club
        cleanup_expired_sessions(club_id)
        
        # Récupérer tous les terrains du club
        courts = Court.query.filter_by(club_id=club_id).all()
        
        courts_data = []
        for court in courts:
            court_data = court.to_dict()
            
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
        
        return jsonify({'courts': courts_data}), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des terrains: {e}")
        return jsonify({'error': 'Erreur lors de la récupération'}), 500

# ====================================================================
# TÂCHE DE NETTOYAGE AUTOMATIQUE
# ====================================================================

@recording_bp.route('/cleanup-expired', methods=['POST'])
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
