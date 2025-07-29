from flask import Blueprint, request, jsonify, session, send_file, Response
from src.models.user import db, User, Video, Court, Club
from src.services.video_capture_service import video_capture_service
from datetime import datetime, timedelta
import os
import io
import logging

logger = logging.getLogger(__name__)
videos_bp = Blueprint('videos', __name__)

def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

@videos_bp.route('/my-videos', methods=['GET'])
def get_my_videos():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        videos = Video.query.filter_by(user_id=user.id).order_by(Video.recorded_at.desc()).all()
        
        # Créer une version sécurisée du to_dict()
        videos_data = []
        for video in videos:
            video_dict = {
                "id": video.id,
                "title": video.title,
                "description": video.description,
                "file_url": video.file_url,
                "thumbnail_url": video.thumbnail_url,
                "duration": getattr(video, 'duration', None),
                "file_size": getattr(video, 'file_size', None),
                "is_unlocked": getattr(video, 'is_unlocked', True),
                "credits_cost": getattr(video, 'credits_cost', 1),
                "recorded_at": video.recorded_at.isoformat() if video.recorded_at else None,
                "created_at": video.created_at.isoformat() if video.created_at else None,
                "user_id": video.user_id,
                "court_id": video.court_id
            }
            videos_data.append(video_dict)
        
        return jsonify({'videos': videos_data}), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des vidéos: {e}")
        return jsonify({'error': 'Erreur lors de la récupération des vidéos'}), 500

@videos_bp.route('/record', methods=['POST'])
def start_recording():
    """Démarrage d'enregistrement avec service de capture vidéo"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    data = request.get_json()
    court_id = data.get('court_id')
    session_name = data.get('session_name', f"Match du {datetime.now().strftime('%d/%m/%Y')}")
    
    if not court_id:
        return jsonify({'error': 'Le terrain est requis'}), 400
    
    try:
        # Vérifier que le terrain existe
        court = Court.query.get(court_id)
        if not court:
            return jsonify({'error': 'Terrain non trouvé'}), 400
        
        # Vérifier que le terrain n'est pas déjà en cours d'enregistrement
        if hasattr(court, 'is_recording') and court.is_recording:
            return jsonify({'error': 'Ce terrain est déjà en cours d\'enregistrement'}), 400
        
        # Démarrer l'enregistrement avec le service de capture
        result = video_capture_service.start_recording(
            court_id=court_id,
            user_id=user.id,
            session_name=session_name
        )
        
        # Marquer le terrain comme en cours d'enregistrement
        court.is_recording = True
        court.recording_session_id = result['session_id']
        db.session.commit()
        
        logger.info(f"Enregistrement démarré par utilisateur {user.id} sur terrain {court_id}")
        
        return jsonify({
            'message': 'Enregistrement démarré avec succès',
            'session_id': result['session_id'],
            'court_id': court_id,
            'session_name': session_name,
            'camera_url': result['camera_url'],
            'status': 'recording'
        }), 200
        court.is_recording = True
        court.current_recording_id = recording_id
        
        # Créer une session d'enregistrement (si vous utilisez l'API avancée)
        try:
            from src.models.user import RecordingSession
            recording_session = RecordingSession(
                recording_id=recording_id,
                user_id=user.id,
                court_id=court_id,
                club_id=court.club_id,
                planned_duration=duration,
                status='recording',
                start_time=datetime.utcnow()
            )
            db.session.add(recording_session)
        except ImportError:
            # Si RecordingSession n'existe pas, on continue sans
            pass
        
        db.session.commit()
        
        return jsonify({
            'message': 'Enregistrement démarré avec succès',
            'recording_id': recording_id,
            'court': court.to_dict(),
            'duration': duration,
            'estimated_end_time': (datetime.now() + timedelta(minutes=duration)).isoformat(),
            'camera_url': court.camera_url
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erreur lors du démarrage: {str(e)}'}), 500

@videos_bp.route('/stop-recording', methods=['POST'])
def stop_recording():
    """Arrêter l'enregistrement avec service de capture vidéo"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    data = request.get_json()
    session_id = data.get('session_id')
    court_id = data.get('court_id')
    
    if not session_id:
        return jsonify({'error': 'session_id manquant'}), 400
    
    try:
        # Arrêter l'enregistrement avec le service de capture
        result = video_capture_service.stop_recording(session_id)
        
        if result.get('status') == 'error':
            return jsonify({'error': result.get('error', 'Erreur lors de l\'arrêt')}), 500
        
        # Mettre à jour le terrain
        if court_id:
            court = Court.query.get(court_id)
            if court:
                court.is_recording = False
                court.recording_session_id = None
                db.session.commit()
        
        logger.info(f"Enregistrement arrêté par utilisateur {user.id}: {session_id}")
        
        return jsonify({
            'message': 'Enregistrement arrêté avec succès',
            'session_id': session_id,
            'status': result.get('status'),
            'video_id': result.get('video_id'),
            'video_filename': result.get('video_filename'),
            'duration': result.get('duration'),
            'file_size': result.get('file_size')
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de l'arrêt de l'enregistrement: {e}")
        return jsonify({"error": f"Erreur lors de l'arrêt: {str(e)}"}), 500

@videos_bp.route('/<int:video_id>', methods=['DELETE'])
def delete_video(video_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    video = Video.query.get_or_404(video_id)
    if video.user_id != user.id:
        return jsonify({'error': 'Accès non autorisé'}), 403
    try:
        db.session.delete(video)
        db.session.commit()
        return jsonify({'message': 'Vidéo supprimée'}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la suppression"}), 500

@videos_bp.route("/clubs/<int:club_id>/courts", methods=["GET"])
def get_courts_for_club(club_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "Accès non autorisé"}), 401
    courts = Court.query.filter_by(club_id=club_id).all()
    return jsonify({"courts": [c.to_dict() for c in courts]}), 200

@videos_bp.route('/<int:video_id>/share', methods=['POST'])
def share_video(video_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        video = Video.query.get(video_id)
        if not video:
            return jsonify({'error': 'Vidéo non trouvée'}), 404
        
        # Vérifier que la vidéo appartient à l'utilisateur et est déverrouillée
        if video.user_id != user.id:
            return jsonify({'error': 'Accès non autorisé à cette vidéo'}), 403
        
        if not video.is_unlocked:
            return jsonify({'error': 'La vidéo doit être déverrouillée pour être partagée'}), 400
        
        data = request.get_json()
        platform = data.get('platform')  # 'facebook', 'instagram', 'youtube'
        
        # Générer les liens de partage
        base_url = request.host_url
        video_url = f"{base_url}videos/{video_id}/watch"
        
        share_urls = {
            'facebook': f"https://www.facebook.com/sharer/sharer.php?u={video_url}",
            'instagram': video_url,  # Instagram nécessite une approche différente
            'youtube': video_url,  # YouTube nécessite l'API YouTube
            'direct': video_url
        }
        
        return jsonify({
            'message': 'Liens de partage générés',
            'share_urls': share_urls,
            'video_url': video_url
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erreur lors de la génération des liens de partage'}), 500

@videos_bp.route('/<int:video_id>/watch', methods=['GET'])
def watch_video(video_id):
    """Route publique pour regarder une vidéo partagée"""
    try:
        video = Video.query.get(video_id)
        if not video:
            return jsonify({'error': 'Vidéo non trouvée'}), 404
        
        if not video.is_unlocked:
            return jsonify({'error': 'Vidéo non disponible'}), 403
        
        # Retourner les informations de la vidéo pour le lecteur
        return jsonify({
            'video': {
                'id': video.id,
                'title': video.title,
                'description': video.description,
                'file_url': video.file_url,
                'thumbnail_url': video.thumbnail_url,
                'duration': video.duration,
                'recorded_at': video.recorded_at.isoformat() if video.recorded_at else None
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erreur lors de la lecture de la vidéo'}), 500


@videos_bp.route('/buy-credits', methods=['POST'])
def buy_credits():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        data = request.get_json()
        credits_to_buy = data.get('credits', 0)
        payment_method = data.get('payment_method', 'simulation')
        
        if credits_to_buy <= 0:
            return jsonify({'error': 'Le nombre de crédits doit être positif'}), 400
        
        # Pour le MVP, on simule le paiement
        # Dans une vraie implémentation, on intégrerait un système de paiement
        
        # Ajouter les crédits au solde de l'utilisateur
        user.credits_balance += credits_to_buy
        db.session.commit()
        
        return jsonify({
            'message': f'{credits_to_buy} crédits achetés avec succès',
            'new_balance': user.credits_balance,
            'transaction_id': f'txn_{user.id}_{int(datetime.now().timestamp())}'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erreur lors de l\'achat de crédits'}), 500


@videos_bp.route('/qr-scan', methods=['POST'])
def scan_qr_code():
    """Endpoint pour gérer le scan QR code et ouvrir la caméra sur mobile"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        data = request.get_json()
        qr_code = data.get('qr_code')
        
        if not qr_code:
            return jsonify({'error': 'QR code requis'}), 400
        
        # Rechercher le terrain correspondant au QR code
        court = Court.query.filter_by(qr_code=qr_code).first()
        if not court:
            return jsonify({'error': 'QR code invalide ou terrain non trouvé'}), 404
        
        # Récupérer les informations du club
        club = Club.query.get(court.club_id)
        
        return jsonify({
            'message': 'QR code scanné avec succès',
            'court': court.to_dict(),
            'club': club.to_dict() if club else None,
            'camera_url': court.camera_url,
            'can_record': True  # L'utilisateur peut démarrer un enregistrement
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erreur lors du scan du QR code'}), 500

@videos_bp.route('/courts/<int:court_id>/camera-stream', methods=['GET'])
def get_camera_stream(court_id):
    """Endpoint pour récupérer le flux de la caméra d'un terrain"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        court = Court.query.get(court_id)
        if not court:
            return jsonify({'error': 'Terrain non trouvé'}), 404
        
        return jsonify({
            'court_id': court.id,
            'court_name': court.name,
            'camera_url': court.camera_url,
            'stream_type': 'mjpeg'  # Type de flux pour la caméra par défaut
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erreur lors de la récupération du flux caméra'}), 500


# ====================================================================
# NOUVELLE ROUTE POUR METTRE À JOUR UNE VIDÉO
# ====================================================================
@videos_bp.route('/<int:video_id>', methods=['PUT'])
def update_video(video_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    video = Video.query.get_or_404(video_id)
    if video.user_id != user.id:
        return jsonify({'error': 'Accès non autorisé'}), 403
        
    data = request.get_json()
    try:
        if 'title' in data:
            video.title = data['title']
        if 'description' in data:
            video.description = data['description']
        
        db.session.commit()
        return jsonify({'message': 'Vidéo mise à jour', 'video': video.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la mise à jour"}), 500


# ====================================================================
# ENDPOINTS POUR SERVIR LES VIDÉOS ET THUMBNAILS
# ====================================================================

@videos_bp.route('/stream/<filename>', methods=['GET'])
def stream_video(filename):
    """Servir les fichiers vidéo (simulation pour le MVP)"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        # Pour le MVP, on génère une vidéo de test
        # Dans la vraie implémentation, on servirait le fichier réel
        
        # Créer une réponse de stream vidéo simulée
        def generate_fake_video():
            # Données de test pour simuler une vidéo MP4
            # En production, on lirait le vrai fichier
            fake_video_data = b'\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom' + b'\x00' * 1000
            yield fake_video_data
        
        return Response(
            generate_fake_video(),
            mimetype='video/mp4',
            headers={
                'Content-Disposition': f'inline; filename="{filename}"',
                'Accept-Ranges': 'bytes',
                'Content-Length': '1024'
            }
        )
    except Exception as e:
        return jsonify({'error': 'Erreur lors du streaming vidéo'}), 500

@videos_bp.route('/thumbnail/<filename>', methods=['GET'])
def get_thumbnail(filename):
    """Servir les thumbnails (simulation pour le MVP)"""
    try:
        # Pour le MVP, on génère une image de placeholder
        # Dans la vraie implémentation, on servirait la vraie thumbnail
        
        # Créer une image placeholder simple (1x1 pixel transparent PNG)
        placeholder_png = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x01\x00\x00\x00\x007n\xf9$\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01U\r\r\x82\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        
        return Response(
            placeholder_png,
            mimetype='image/png',
            headers={
                'Content-Disposition': f'inline; filename="{filename}"',
                'Cache-Control': 'public, max-age=3600'
            }
        )
    except Exception as e:
        return jsonify({'error': 'Erreur lors du chargement de la thumbnail'}), 500

@videos_bp.route('/download/<int:video_id>', methods=['GET'])
def download_video(video_id):
    """Télécharger une vidéo"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        video = Video.query.get(video_id)
        if not video:
            return jsonify({'error': 'Vidéo non trouvée'}), 404
        
        # Vérifier les permissions
        if video.user_id != user.id and not video.is_unlocked:
            return jsonify({'error': 'Accès non autorisé'}), 403
        
        # Pour le MVP, rediriger vers le stream
        filename = video.file_url.split('/')[-1]
        return Response(
            b'fake video data for download',
            mimetype='video/mp4',
            headers={
                'Content-Disposition': f'attachment; filename="{video.title}.mp4"',
                'Content-Type': 'application/octet-stream'
            }
        )
    except Exception as e:
        return jsonify({'error': 'Erreur lors du téléchargement'}), 500


# ====================================================================
# ENDPOINTS POUR LA GESTION D'ENREGISTREMENT
# ====================================================================

@videos_bp.route('/recording/<recording_id>/status', methods=['GET'])
def get_recording_status_by_id(recording_id):
    """Obtenir le statut d'un enregistrement en cours avec le service de capture"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        # Obtenir le statut depuis le service de capture
        status = video_capture_service.get_recording_status(recording_id)
        
        if 'error' in status:
            return jsonify(status), 404
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut: {e}")
        return jsonify({'error': 'Erreur lors de la récupération du statut'}), 500

@videos_bp.route('/recording/<recording_id>/stop', methods=['POST'])
def stop_recording_by_id(recording_id):
    """Arrêter un enregistrement spécifique par son ID avec le service de capture"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        # Arrêter l'enregistrement avec le service de capture
        result = video_capture_service.stop_recording(recording_id)
        
        if result.get('status') == 'error':
            return jsonify({'error': result.get('error', 'Erreur lors de l\'arrêt')}), 500
        
        # Mettre à jour le terrain qui était en cours d'enregistrement
        court = Court.query.filter_by(recording_session_id=recording_id).first()
        if court:
            court.is_recording = False
            court.recording_session_id = None
            db.session.commit()
        
        logger.info(f"Enregistrement arrêté par utilisateur {user.id}: {recording_id}")
        
        return jsonify({
            'message': 'Enregistrement arrêté avec succès',
            'recording_id': recording_id,
            'status': result.get('status'),
            'video_id': result.get('video_id'),
            'video_filename': result.get('video_filename'),
            'duration': result.get('duration'),
            'file_size': result.get('file_size')
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de l'arrêt de l'enregistrement {recording_id}: {e}")
        return jsonify({'error': f'Erreur lors de l\'arrêt: {str(e)}'}), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de l'arrêt de l'enregistrement {recording_id}: {e}")
        return jsonify({'error': f'Erreur lors de l\'arrêt: {str(e)}'}), 500

@videos_bp.route('/courts/available', methods=['GET'])
def get_available_courts():
    """Obtenir la liste des terrains disponibles pour l'enregistrement"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        # Récupérer tous les terrains non occupés
        courts = Court.query.filter_by(is_recording=False).all()
        
        # Grouper par club
        courts_by_club = {}
        for court in courts:
            club = Club.query.get(court.club_id)
            if club:
                if club.id not in courts_by_club:
                    courts_by_club[club.id] = {
                        'club': club.to_dict(),
                        'courts': []
                    }
                courts_by_club[club.id]['courts'].append(court.to_dict())
        
        return jsonify({
            'available_courts': list(courts_by_club.values()),
            'total_available': len(courts)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la récupération des terrains: {str(e)}'}), 500
