"""
NOUVELLES ROUTES D'ENREGISTREMENT ROBUSTES
==========================================

Remplace les anciennes routes pour utiliser le nouveau VideoRecordingEngine
avec gestion d'erreurs robuste et APIs JSON garanties.
"""

from flask import Blueprint, request, jsonify, session
import logging
from datetime import datetime
from functools import wraps
from typing import Optional

from ..models.database import db
from ..models.user import Court, User
from ..services.video_recording_engine import video_recording_engine

logger = logging.getLogger(__name__)

# Décorateurs d'authentification
def login_required(f):
    """Décorateur pour vérifier que l'utilisateur est authentifié."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Non authentifié'}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_current_user() -> Optional[User]:
    """Récupère l'utilisateur connecté depuis la session."""
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

def api_response(data=None, error=None, message=None, status=200):
    """Génère une réponse API standardisée."""
    response = {}
    if data is not None:
        response['data'] = data
    if error:
        response['error'] = error
    if message:
        response['message'] = message
    return jsonify(response), status

def handle_api_error(f):
    """Décorateur pour gérer les erreurs d'API."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Erreur API {f.__name__}: {e}")
            return api_response(error="Erreur interne du serveur", status=500)
    return decorated_function

logger = logging.getLogger(__name__)

# Blueprint pour les nouvelles routes d'enregistrement
recording_bp = Blueprint('recording_v2', __name__, url_prefix='/api/recording')

# Configuration des durées autorisées
ALLOWED_DURATIONS = [60, 90, 120, 'MAX']  # en minutes
MAX_DURATION_MINUTES = 200  # 3h20 max pour 'MAX'

@recording_bp.route('/start', methods=['POST'])
@login_required
@handle_api_error
def start_recording_v2():
    """
    NOUVELLE API DE DÉMARRAGE D'ENREGISTREMENT
    ==========================================
    
    Version robuste qui utilise le VideoRecordingEngine unifié :
    - Validation stricte des paramètres
    - Gestion d'erreurs complète
    - Réponse JSON garantie
    - Nettoyage automatique en cas d'erreur
    """
    try:
        user = get_current_user()
        if not user:
            return api_response(error="Utilisateur non authentifié", status=401)
        
        # Récupération et validation des données
        data = request.get_json()
        if not data:
            return api_response(error="Données JSON requises", status=400)
        
        court_id = data.get('court_id')
        session_name = data.get('session_name')
        duration = data.get('duration', 60)
        keep_local_files = data.get('keep_local_files', True)  # Par défaut: garder localement
        upload_to_bunny = data.get('upload_to_bunny', False)  # Par défaut: pas d'upload automatique
        
        # Validations
        if not court_id:
            return api_response(error="L'ID du terrain est requis", status=400)
        
        # Validation de la durée
        if duration not in ALLOWED_DURATIONS:
            return api_response(
                error=f"Durée invalide. Utilisez {', '.join(map(str, ALLOWED_DURATIONS))}",
                status=400
            )
        
        # Convertir 'MAX' en minutes
        if duration == 'MAX':
            duration_minutes = MAX_DURATION_MINUTES
        else:
            duration_minutes = int(duration)
        
        # Vérifier que le terrain existe et est disponible
        court = Court.query.get(court_id)
        if not court:
            return api_response(error="Terrain non trouvé", status=404)
        
        # Vérifier si le terrain est déjà en cours d'enregistrement
        if hasattr(court, 'is_recording') and court.is_recording:
            current_recording_id = getattr(court, 'current_recording_id', 'unknown')
            return api_response(
                error="Ce terrain est déjà utilisé pour un enregistrement",
                data={'current_recording_id': current_recording_id},
                status=409
            )
        
        # Générer le nom de session si non fourni
        if not session_name:
            session_name = f"Match du {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        logger.info(f"🎬 Démarrage enregistrement: Utilisateur {user.id}, "
                   f"Terrain {court_id}, Durée {duration_minutes}min, "
                   f"Local: {'Oui' if keep_local_files else 'Non'}, "
                   f"Bunny: {'Oui' if upload_to_bunny else 'Non'}")
        
        # Démarrer l'enregistrement avec le nouveau moteur
        result = video_recording_engine.start_recording(
            court_id=court_id,
            user_id=user.id,
            session_name=session_name,
            keep_local_files=keep_local_files,
            upload_to_bunny=upload_to_bunny
        )
        
        # Programmer l'arrêt automatique
        _schedule_auto_stop(result['session_id'], duration_minutes)
        
        # Réponse de succès
        return api_response(
            data={
                'session_id': result['session_id'],
                'court_id': court_id,
                'session_name': session_name,
                'camera_url': result['camera_url'],
                'method': result['method'],
                'duration_minutes': duration_minutes,
                'start_time': datetime.now().isoformat(),
                'status': 'recording'
            },
            message="Enregistrement démarré avec succès",
            status=201
        )
        
    except ValueError as e:
        logger.warning(f"⚠️ Erreur validation enregistrement: {e}")
        return api_response(error=str(e), status=400)
        
    except Exception as e:
        logger.error(f"❌ Erreur démarrage enregistrement: {e}")
        return api_response(
            error="Erreur interne lors du démarrage de l'enregistrement",
            status=500
        )

@recording_bp.route('/stop', methods=['POST'])
@login_required
@handle_api_error  
def stop_recording_v2():
    """
    NOUVELLE API D'ARRÊT D'ENREGISTREMENT
    ====================================
    
    Version robuste avec validation et nettoyage automatique.
    """
    try:
        user = get_current_user()
        if not user:
            return api_response(error="Utilisateur non authentifié", status=401)
        
        data = request.get_json()
        if not data:
            return api_response(error="Données JSON requises", status=400)
        
        # Support de deux formats : recording_id ou session_id
        session_id = data.get('recording_id') or data.get('session_id')
        
        if not session_id:
            return api_response(error="L'ID de l'enregistrement est requis", status=400)
        
        logger.info(f"⏹️ Arrêt enregistrement: {session_id} par utilisateur {user.id}")
        
        # Arrêter l'enregistrement
        result = video_recording_engine.stop_recording(session_id)
        
        if result['status'] == 'error':
            return api_response(
                error=result.get('error', 'Erreur inconnue'),
                status=400 if 'non trouvée' in result.get('error', '') else 500
            )
        
        # Récupérer les informations de la session pour la réponse
        session_data = _get_session_data_for_response(session_id, result)
        
        return api_response(
            data={
                'session_id': session_id,
                'stopped_by': 'player',
                'video': session_data.get('video', {}),
                'session': session_data.get('session', {}),
                'message': result.get('message', 'Enregistrement arrêté avec succès')
            },
            message="Enregistrement arrêté avec succès"
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur arrêt enregistrement: {e}")
        return api_response(
            error="Erreur interne lors de l'arrêt de l'enregistrement",
            status=500
        )

@recording_bp.route('/status', methods=['GET'])
@login_required
@handle_api_error
def get_recording_status_v2():
    """
    STATUT DES ENREGISTREMENTS ACTIFS
    =================================
    
    Retourne le statut de tous les enregistrements actifs pour l'utilisateur.
    """
    try:
        user = get_current_user()
        if not user:
            return api_response(error="Utilisateur non authentifié", status=401)
        
        # Récupérer tous les enregistrements actifs
        active_recordings = video_recording_engine.list_active_recordings()
        
        # Filtrer par utilisateur
        user_recordings = [
            rec for rec in active_recordings 
            if rec['user_id'] == user.id
        ]
        
        # Ajouter des informations détaillées
        detailed_recordings = []
        for rec in user_recordings:
            # Récupérer le statut détaillé
            status = video_recording_engine.get_recording_status(rec['session_id'])
            
            detailed_recordings.append({
                'session_id': rec['session_id'],
                'court_id': rec['court_id'],
                'session_name': rec['session_name'],
                'status': status['status'],
                'method': status['method'],
                'duration': status['duration'],
                'start_time': status['start_time'],
                'camera_url': status['camera_url'],
                'stats': status['stats']
            })
        
        return api_response(
            data={
                'active_recordings': detailed_recordings,
                'total_count': len(detailed_recordings)
            },
            message=f"{len(detailed_recordings)} enregistrement(s) actif(s)"
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération statut: {e}")
        return api_response(
            error="Erreur lors de la récupération du statut",
            status=500
        )

@recording_bp.route('/list', methods=['GET'])
@login_required  
@handle_api_error
def list_all_recordings_v2():
    """
    LISTE TOUS LES ENREGISTREMENTS ACTIFS
    =====================================
    
    Admin endpoint pour voir tous les enregistrements du système.
    """
    try:
        user = get_current_user()
        
        # Vérifier les permissions admin (optionnel)
        # if not user.is_admin:
        #     return api_response(error="Accès non autorisé", status=403)
        
        active_recordings = video_recording_engine.list_active_recordings()
        
        return api_response(
            data={
                'active_recordings': active_recordings,
                'total_count': len(active_recordings)
            },
            message=f"{len(active_recordings)} enregistrement(s) actif(s) dans le système"
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur liste enregistrements: {e}")
        return api_response(
            error="Erreur lors de la récupération de la liste",
            status=500
        )

@recording_bp.route('/cleanup', methods=['POST'])
@login_required
@handle_api_error
def cleanup_phantom_recordings():
    """
    NETTOYAGE DES ENREGISTREMENTS FANTÔMES
    =====================================
    
    Force le nettoyage des enregistrements abandonnés.
    """
    try:
        user = get_current_user()
        
        logger.info(f"🧹 Nettoyage fantômes demandé par utilisateur {user.id}")
        
        # Compter les enregistrements fantômes avant nettoyage
        phantom_courts = Court.query.filter_by(is_recording=True).all()
        phantom_count = len(phantom_courts)
        
        # Libérer tous les terrains marqués comme "en enregistrement"
        for court in phantom_courts:
            logger.info(f"🧹 Libération terrain fantôme: {court.id}")
            court.is_recording = False
            court.current_recording_id = None
        
        db.session.commit()
        
        return api_response(
            data={
                'cleaned_courts': phantom_count,
                'message': f"{phantom_count} terrain(s) libéré(s)"
            },
            message="Nettoyage des enregistrements fantômes terminé"
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur nettoyage fantômes: {e}")
        return api_response(
            error="Erreur lors du nettoyage",
            status=500
        )

def _schedule_auto_stop(session_id: str, duration_minutes: int):
    """Programme l'arrêt automatique d'un enregistrement"""
    try:
        import threading
        import time
        
        def auto_stop_worker():
            try:
                # Attendre la durée spécifiée
                time.sleep(duration_minutes * 60)
                
                # Vérifier si l'enregistrement est toujours actif
                status = video_recording_engine.get_recording_status(session_id)
                if status['status'] not in ['not_found', 'completed', 'error']:
                    logger.info(f"⏰ Arrêt automatique: {session_id} après {duration_minutes}min")
                    video_recording_engine.stop_recording(session_id)
                else:
                    logger.info(f"ℹ️ Enregistrement {session_id} déjà terminé")
                    
            except Exception as e:
                logger.error(f"❌ Erreur arrêt automatique {session_id}: {e}")
        
        # Lancer le timer en arrière-plan
        timer_thread = threading.Thread(
            target=auto_stop_worker,
            daemon=True,
            name=f"AutoStop-{session_id}"
        )
        timer_thread.start()
        
        logger.info(f"⏰ Timer programmé: {session_id} → {duration_minutes} minutes")
        
    except Exception as e:
        logger.error(f"❌ Erreur programmation timer {session_id}: {e}")

def _get_session_data_for_response(session_id: str, stop_result: dict) -> dict:
    """Prépare les données de session pour la réponse d'arrêt"""
    try:
        # Format de compatibilité avec l'ancien système
        return {
            'session': {
                'id': session_id,
                'status': 'stopped',
                'stopped_by': 'player',
                'end_time': datetime.now().isoformat()
            },
            'video': {
                'id': stop_result.get('video_id'),
                'title': stop_result.get('message', ''),
                'duration': stop_result.get('duration', 0),
                'file_size': stop_result.get('file_size', 0),
                'file_url': stop_result.get('video_url', ''),
                'thumbnail_url': stop_result.get('thumbnail_url', ''),
                'created_at': datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"❌ Erreur préparation données session: {e}")
        return {'session': {}, 'video': {}}

# Endpoint de test pour vérifier le fonctionnement
@recording_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint de santé pour le système d'enregistrement"""
    try:
        active_count = len(video_recording_engine.list_active_recordings())
        
        return api_response(
            data={
                'status': 'healthy',
                'engine': 'VideoRecordingEngine',
                'active_recordings': active_count,
                'timestamp': datetime.now().isoformat()
            },
            message="Système d'enregistrement opérationnel"
        )
    except Exception as e:
        logger.error(f"❌ Erreur health check: {e}")
        return api_response(
            error="Système d'enregistrement non disponible",
            status=503
        )

logger.info("🎬 Nouvelles routes d'enregistrement chargées avec succès")
