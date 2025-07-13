from flask import Blueprint, request, jsonify, session
from models.user import db, User, Video, Court, UserRole
from datetime import datetime
import os

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
        return jsonify({
            'videos': [video.to_dict() for video in videos]
        }), 200
    except Exception as e:
        return jsonify({'error': 'Erreur lors de la récupération des vidéos'}), 500

@videos_bp.route('/record', methods=['POST'])
def start_recording():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        data = request.get_json()
        
        # Vérifications obligatoires : club et terrain doivent être sélectionnés
        if not data.get('club_id'):
            return jsonify({'error': 'Le club doit être sélectionné'}), 400
        
        if not data.get('court_id'):
            return jsonify({'error': 'Le terrain doit être sélectionné'}), 400
        
        # Vérifier que le terrain existe et appartient au club
        court = Court.query.filter_by(id=data['court_id'], club_id=data['club_id']).first()
        if not court:
            return jsonify({'error': 'Terrain non trouvé ou ne correspond pas au club sélectionné'}), 400
        
        # Pour le MVP, on simule l'enregistrement
        # Dans une vraie implémentation, on démarrerait l'enregistrement vidéo
        
        return jsonify({
            'message': 'Enregistrement démarré',
            'recording_id': f"rec_{user.id}_{int(datetime.now().timestamp())}",
            'court_id': court.id,
            'club_id': data['club_id']
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erreur lors du démarrage de l\'enregistrement'}), 500

@videos_bp.route('/stop-recording', methods=['POST'])
def stop_recording():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        data = request.get_json()
        recording_id = data.get('recording_id')
        title = data.get('title', f'Match du {datetime.now().strftime("%d/%m/%Y %H:%M")}')
        description = data.get('description', '')
        court_id = data.get('court_id')
        
        # Vérifier que l'utilisateur a assez de crédits pour l'enregistrement
        credits_cost = 1  # Coût par enregistrement
        if user.credits_balance < credits_cost:
            return jsonify({'error': 'Crédits insuffisants pour effectuer cet enregistrement'}), 400
        
        # Débiter les crédits pour l'enregistrement
        user.credits_balance -= credits_cost
        
        new_video = Video(
            title=title,
            description=description,
            file_url=f'/videos/simulated_{recording_id}.mp4',  # URL simulée
            thumbnail_url=f'/thumbnails/simulated_{recording_id}.jpg',  # Thumbnail simulée
            duration=1800,  # 30 minutes par défaut
            file_size=500000000,  # 500MB par défaut
            user_id=user.id,
            court_id=court_id,
            is_unlocked=True,  # Vidéo directement accessible après enregistrement
            credits_cost=0  # Plus de coût pour déverrouiller
        )
        
        db.session.add(new_video)
        db.session.commit()
        
        return jsonify({
            'message': 'Enregistrement terminé et vidéo sauvegardée',
            'video': new_video.to_dict(),
            'remaining_credits': user.credits_balance
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erreur lors de l\'arrêt de l\'enregistrement'}), 500

@videos_bp.route('/<int:video_id>/unlock', methods=['POST'])
def unlock_video(video_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        video = Video.query.get(video_id)
        if not video:
            return jsonify({'error': 'Vidéo non trouvée'}), 404
        
        # Vérifier que la vidéo appartient à l'utilisateur
        if video.user_id != user.id:
            return jsonify({'error': 'Accès non autorisé à cette vidéo'}), 403
        
        # Vérifier si la vidéo est déjà déverrouillée
        if video.is_unlocked:
            return jsonify({'message': 'Vidéo déjà déverrouillée'}), 200
        
        # Vérifier si l'utilisateur a assez de crédits
        if user.credits_balance < video.credits_cost:
            return jsonify({'error': 'Crédits insuffisants'}), 400
        
        # Débiter les crédits et déverrouiller la vidéo
        user.credits_balance -= video.credits_cost
        video.is_unlocked = True
        
        db.session.commit()
        
        return jsonify({
            'message': 'Vidéo déverrouillée avec succès',
            'video': video.to_dict(),
            'remaining_credits': user.credits_balance
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erreur lors du déverrouillage de la vidéo'}), 500

@videos_bp.route('/<int:video_id>', methods=['GET'])
def get_video(video_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        video = Video.query.get(video_id)
        if not video:
            return jsonify({'error': 'Vidéo non trouvée'}), 404
        
        # Vérifier les permissions d'accès
        can_access = False
        
        if video.user_id == user.id:
            # Propriétaire de la vidéo
            can_access = True
        elif user.role == UserRole.SUPER_ADMIN:
            # Super admin peut voir toutes les vidéos
            can_access = True
        elif user.role == UserRole.CLUB and user.club_id:
            # Club peut voir les vidéos de ses joueurs
            video_owner = User.query.get(video.user_id)
            if video_owner and video_owner.club_id == user.club_id:
                can_access = True
        
        if not can_access:
            return jsonify({'error': 'Accès non autorisé à cette vidéo'}), 403
        
        return jsonify({'video': video.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': 'Erreur lors de la récupération de la vidéo'}), 500

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
        from models.user import Club
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

