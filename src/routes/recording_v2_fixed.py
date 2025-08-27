"""
ROUTES D'ENREGISTREMENT VIDÉO CORRIGÉES
======================================

Routes principales pour la gestion des enregistrements vidéo:
- Démarrage d'enregistrement avec paramètres upload
- Arrêt d'enregistrement avec finalisation
- Statut en temps réel
- Gestion d'erreurs robuste
"""

from flask import Blueprint, request, jsonify, session
import logging
from datetime import datetime
from functools import wraps
from typing import Optional

from ..models.database import db
from ..models.user import Court, User
from ..services.video_recording_engine_fixed import video_recording_engine

logger = logging.getLogger(__name__)


def login_required(f):
    """Décorateur pour vérifier l'authentification."""
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
    """Décorateur pour la gestion d'erreurs API."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"❌ Erreur API {f.__name__}: {e}")
            return api_response(
                error="Erreur serveur interne",
                message=str(e),
                status=500
            )
    return decorated_function


# Blueprint pour les routes d'enregistrement
recording_bp = Blueprint('recording_v2', __name__, url_prefix='/api/v2/recording')


@recording_bp.route('/start', methods=['POST'])
@login_required
@handle_api_error
def start_recording():
    """
    Démarrer un enregistrement vidéo
    
    Body JSON:
    {
        "court_id": int,
        "duration_minutes": int (optionnel, défaut: 5),
        "session_name": str (optionnel),
        "keep_local_files": bool (optionnel, défaut: true),
        "upload_to_bunny": bool (optionnel, défaut: false)
    }
    """
    
    # Récupérer l'utilisateur actuel
    user = get_current_user()
    if not user:
        return api_response(error="Utilisateur non authentifié", status=401)
    
    # Récupérer les données de la requête
    data = request.get_json()
    if not data:
        return api_response(error="Données JSON requises", status=400)
    
    # Paramètres d'enregistrement
    court_id = data.get('court_id')
    duration_minutes = data.get('duration_minutes', 5)
    session_name = data.get('session_name')
    keep_local_files = data.get('keep_local_files', True)  # Défaut: garder
    upload_to_bunny = data.get('upload_to_bunny', False)  # Défaut: pas upload
    
    # Validation des paramètres
    if not court_id:
        return api_response(error="court_id requis", status=400)
    
    ALLOWED_DURATIONS = [1, 2, 3, 5, 10, 15, 30, 60]
    if duration_minutes not in ALLOWED_DURATIONS:
        return api_response(
            error=f"Durée invalide. Utilisez: {', '.join(map(str, ALLOWED_DURATIONS))}",
            status=400
        )
    
    # Vérifier que le terrain existe
    court = Court.query.get(court_id)
    if not court:
        return api_response(
            error=f"Terrain {court_id} non trouvé",
            status=404
        )
    
    # Vérifier si le terrain n'est pas déjà en cours d'enregistrement
    if hasattr(court, 'current_recording_id') and court.current_recording_id:
        current_id = getattr(court, 'current_recording_id', 'unknown')
        return api_response(
            error=f"Terrain {court_id} déjà en cours d'enregistrement",
            data={
                "current_recording_id": current_id
            },
            status=409
        )
    
    # Nom de session par défaut
    if not session_name:
        date_str = datetime.now().strftime('%d/%m/%Y %H:%M')
        session_name = f"Match du {date_str}"
    
    # Logger les paramètres d'enregistrement
    logger.info(
        f"🎬 Nouvel enregistrement: "
        f"Terrain {court_id}, Durée {duration_minutes}min, "
        f"Local: {'Oui' if keep_local_files else 'Non'}, "
        f"Bunny: {'Oui' if upload_to_bunny else 'Non'}"
    )
    
    # Démarrer l'enregistrement via le moteur
    result = video_recording_engine.start_recording(
        court_id=court_id,
        user_id=user.id,
        session_name=session_name,
        keep_local_files=keep_local_files,
        upload_to_bunny=upload_to_bunny
    )
    
    if result.get('success'):
        logger.info(f"✅ Enregistrement démarré: {result.get('session_id')}")
        
        return api_response(
            data={
                'session_id': result.get('session_id'),
                'court_id': court_id,
                'user_id': user.id,
                'session_name': session_name,
                'duration_minutes': duration_minutes,
                'config': {
                    'keep_local_files': keep_local_files,
                    'upload_to_bunny': upload_to_bunny
                },
                'details': result.get('details', {})
            },
            message="Enregistrement démarré avec succès",
            status=201
        )
    else:
        logger.error(f"❌ Échec démarrage: {result.get('error')}")
        
        return api_response(
            error=result.get('error', 'Erreur inconnue'),
            message=result.get('message', 'Échec du démarrage'),
            status=400
        )


@recording_bp.route('/stop', methods=['POST'])
@login_required
@handle_api_error
def stop_recording():
    """
    Arrêter un enregistrement vidéo
    
    Body JSON:
    {
        "session_id": str
    }
    """
    
    # Récupérer l'utilisateur actuel
    user = get_current_user()
    if not user:
        return api_response(error="Utilisateur non authentifié", status=401)
    
    # Récupérer les données
    data = request.get_json()
    if not data:
        return api_response(error="Données JSON requises", status=400)
    
    session_id = data.get('session_id')
    if not session_id:
        return api_response(
            error="L'ID de l'enregistrement est requis",
            status=400
        )
    
    logger.info(f"⏹️ Arrêt enregistrement: {session_id} par user {user.id}")
    
    # Arrêter l'enregistrement via le moteur
    result = video_recording_engine.stop_recording(session_id)
    
    if result.get('success'):
        logger.info(f"✅ Enregistrement arrêté: {session_id}")
        
        return api_response(
            data={
                'session_id': session_id,
                'stopped_by': user.id,
                'stopped_at': datetime.now().isoformat(),
                'result': result.get('result', {})
            },
            message=result.get('message', 'Enregistrement arrêté avec succès'),
            status=200
        )
    else:
        logger.error(f"❌ Échec arrêt: {result.get('error')}")
        
        return api_response(
            error=result.get('error', 'Erreur inconnue'),
            message=result.get('message', 'Échec de l\'arrêt'),
            status=400
        )


@recording_bp.route('/status', methods=['GET'])
@login_required
@handle_api_error
def get_recording_status():
    """
    Obtenir le statut d'un enregistrement
    
    Query parameters:
    - session_id: ID de la session
    """
    
    # Récupérer l'utilisateur actuel
    user = get_current_user()
    if not user:
        return api_response(error="Utilisateur non authentifié", status=401)
    
    session_id = request.args.get('session_id')
    if not session_id:
        return api_response(error="session_id requis", status=400)
    
    # Obtenir le statut via le moteur
    status = video_recording_engine.get_recording_status(session_id)
    
    if status.get('success'):
        return api_response(
            data=status,
            message="Statut récupéré avec succès",
            status=200
        )
    else:
        return api_response(
            error=status.get('error', 'Session non trouvée'),
            status=404
        )


@recording_bp.route('/active', methods=['GET'])
@login_required
@handle_api_error
def get_active_recordings():
    """Obtenir la liste des enregistrements actifs"""
    
    # Récupérer l'utilisateur actuel
    user = get_current_user()
    if not user:
        return api_response(error="Utilisateur non authentifié", status=401)
    
    # Obtenir les enregistrements actifs
    active_recordings = video_recording_engine.get_active_recordings()
    
    return api_response(
        data=active_recordings,
        message="Enregistrements actifs récupérés",
        status=200
    )


@recording_bp.route('/cleanup', methods=['POST'])
@login_required
@handle_api_error
def cleanup_recordings():
    """Nettoyer les anciens fichiers temporaires"""
    
    # Récupérer l'utilisateur actuel
    user = get_current_user()
    if not user:
        return api_response(error="Utilisateur non authentifié", status=401)
    
    # Vérifier les permissions (admin seulement)
    if not hasattr(user, 'role') or user.role.value != 'SUPER_ADMIN':
        return api_response(
            error="Permissions insuffisantes",
            status=403
        )
    
    # Paramètres de nettoyage
    data = request.get_json() or {}
    max_age_hours = data.get('max_age_hours', 24)
    
    # Effectuer le nettoyage
    video_recording_engine.cleanup_old_files(max_age_hours)
    
    return api_response(
        data={
            'max_age_hours': max_age_hours,
            'cleanup_completed': True
        },
        message="Nettoyage effectué avec succès",
        status=200
    )


@recording_bp.route('/test', methods=['GET'])
@handle_api_error
def test_recording_system():
    """Test de connectivité du système d'enregistrement"""
    
    try:
        # Test de base du moteur
        active = video_recording_engine.get_active_recordings()
        
        # Test de la base de données
        courts_count = Court.query.count()
        
        return api_response(
            data={
                'system_status': 'operational',
                'active_recordings_count': active.get('count', 0),
                'courts_available': courts_count,
                'engine_initialized': True,
                'timestamp': datetime.now().isoformat()
            },
            message="Système d'enregistrement opérationnel",
            status=200
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur test système: {e}")
        
        return api_response(
            data={
                'system_status': 'error',
                'error_details': str(e)
            },
            error="Système d'enregistrement non opérationnel",
            status=500
        )


# Handlers d'erreurs spécifiques au blueprint
@recording_bp.errorhandler(404)
def not_found(error):
    """Handler pour les erreurs 404"""
    return api_response(error="Endpoint non trouvé", status=404)


@recording_bp.errorhandler(405)
def method_not_allowed(error):
    """Handler pour les erreurs 405"""
    return api_response(error="Méthode HTTP non autorisée", status=405)


@recording_bp.errorhandler(500)
def internal_error(error):
    """Handler pour les erreurs 500"""
    return api_response(error="Erreur serveur interne", status=500)
