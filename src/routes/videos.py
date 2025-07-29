from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, Video, Court, Club
from datetime import datetime

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
    videos = Video.query.filter_by(user_id=user.id).order_by(Video.recorded_at.desc()).all()
    return jsonify({'videos': [v.to_dict() for v in videos]}), 200

@videos_bp.route('/record', methods=['POST'])
def start_recording():
    """Version simple du démarrage d'enregistrement (rétrocompatibilité)"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    data = request.get_json()
    court_id = data.get('court_id')
    duration = data.get('duration', 90)  # Nouveau: durée par défaut
    
    if not court_id:
        return jsonify({'error': 'Le terrain est requis'}), 400
    
    # Rediriger vers la nouvelle API de recording
    from .recording import recording_bp
    from flask import current_app
    
    # Simuler une requête interne vers la nouvelle API
    recording_data = {
        'court_id': court_id,
        'duration': duration,
        'title': data.get('title', ''),
        'description': data.get('description', '')
    }
    
    # Pour la compatibilité, on retourne l'ancien format
    return jsonify({
        'message': 'Enregistrement démarré',
        'recording_id': f"rec_{user.id}_{int(datetime.now().timestamp())}",
        'note': 'Utilisez /api/recording/start pour les nouvelles fonctionnalités'
    }), 200

@videos_bp.route('/stop-recording', methods=['POST'])
def stop_recording():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    if user.credits_balance < 1:
        return jsonify({'error': 'Crédits insuffisants'}), 400
    data = request.get_json()
    court_id = data.get('court_id')
    if not court_id:
        return jsonify({'error': 'court_id manquant'}), 400
    try:
        user.credits_balance -= 1
        new_video = Video(
            user_id=user.id,
            court_id=court_id,
            file_url=f'/videos/simulated_{data.get("recording_id")}.mp4',
            title=data.get('title') or f'Match du {datetime.now().strftime("%d/%m/%Y")}',
            description=data.get('description', '')
        )
        db.session.add(new_video)
        db.session.commit()
        return jsonify({'message': 'Vidéo sauvegardée', 'video': new_video.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de l'arrêt"}), 500

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
