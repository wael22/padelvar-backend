
from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, Club, Video, UserRole, Court
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

clubs_bp = Blueprint("clubs", __name__)

def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)

def require_club_access():
    user = get_current_user()
    if not user or user.role != UserRole.CLUB:
        return None
    return user


@clubs_bp.route("/players", methods=["GET"])
def get_club_players():
    user = require_club_access()
    if not user:
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        if not user.club_id:
            return jsonify({"error": "Club non trouvé"}), 404
        
        players = User.query.filter_by(club_id=user.club_id, role=UserRole.PLAYER).all()
        
        return jsonify({
            "players": [player.to_dict() for player in players]
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des joueurs du club: {e}")
        return jsonify({"error": "Erreur lors de la récupération des joueurs"}), 500

@clubs_bp.route("/players/<int:player_id>/videos", methods=["GET"])
def get_player_videos(player_id):
    user = require_club_access()
    if not user:
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        # Vérifier que le joueur appartient au club
        player = User.query.get(player_id)
        if not player or player.club_id != user.club_id:
            return jsonify({"error": "Joueur non trouvé dans ce club"}), 404
        
        videos = Video.query.filter_by(user_id=player_id).order_by(Video.recorded_at.desc()).all()
        
        return jsonify({
            "player": player.to_dict(),
            "videos": [video.to_dict() for video in videos]
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des vidéos du joueur {player_id}: {e}")
        return jsonify({"error": "Erreur lors de la récupération des vidéos du joueur"}), 500

@clubs_bp.route("/players/<int:player_id>/add-credits", methods=["POST"])
def add_credits_to_player(player_id):
    user = require_club_access()
    if not user:
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        # Vérifier que le joueur appartient au club
        player = User.query.get(player_id)
        if not player or player.club_id != user.club_id:
            return jsonify({"error": "Joueur non trouvé dans ce club"}), 404
        
        data = request.get_json()
        credits_to_add = data.get("credits", 0)
        
        if not isinstance(credits_to_add, int) or credits_to_add <= 0:
            return jsonify({"error": "Le nombre de crédits doit être un entier positif"}), 400
        
        player.credits_balance += credits_to_add
        db.session.commit()
        
        return jsonify({
            "message": f"{credits_to_add} crédits ajoutés avec succès à {player.name}",
            "player": player.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de l'ajout de crédits au joueur {player_id}: {e}")
        return jsonify({"error": "Erreur lors de l'ajout de crédits"}), 500

@clubs_bp.route("/videos", methods=["GET"])
def get_club_videos():
    user = require_club_access()
    if not user:
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        if not user.club_id:
            return jsonify({"error": "Club non trouvé"}), 404
        
        # Récupérer tous les joueurs du club
        players = User.query.filter_by(club_id=user.club_id, role=UserRole.PLAYER).all()
        player_ids = [player.id for player in players]
        
        # Récupérer toutes les vidéos des joueurs du club
        videos = Video.query.filter(Video.user_id.in_(player_ids)).order_by(Video.recorded_at.desc()).all()
        
        # Enrichir les vidéos avec les informations du joueur
        videos_with_player = []
        for video in videos:
            video_dict = video.to_dict()
            player = next((p for p in players if p.id == video.user_id), None)
            if player:
                video_dict["player_name"] = player.name
                video_dict["player_email"] = player.email
            videos_with_player.append(video_dict)
        
        return jsonify({
            "videos": videos_with_player
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des vidéos du club: {e}")
        return jsonify({"error": "Erreur lors de la récupération des vidéos du club"}), 500

@clubs_bp.route("/info", methods=["GET"])
def get_club_info():
    user = require_club_access()
    if not user:
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        if not user.club_id:
            return jsonify({"error": "Club non trouvé"}), 404
        
        club = Club.query.get(user.club_id)
        if not club:
            return jsonify({"error": "Club non trouvé"}), 404
        
        return jsonify({
            "club": club.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des informations du club: {e}")
        return jsonify({"error": "Erreur lors de la récupération des informations du club"}), 500


@clubs_bp.route("/players", methods=["POST"])
def create_player():
    """Permet aux clubs de créer de nouveaux joueurs"""
    user = require_club_access()
    if not user:
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        if not user.club_id:
            return jsonify({"error": "Club non trouvé"}), 404
        
        data = request.get_json()
        
        if not data or not data.get("email") or not data.get("name"):
            return jsonify({"error": "Email et nom requis"}), 400
        
        email = data["email"].lower().strip()
        name = data["name"].strip()
        
        # Vérifier si l'utilisateur existe déjà
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"error": "Un utilisateur avec cet email existe déjà"}), 409
        
        # Créer le nouveau joueur
        new_player = User(
            email=email,
            name=name,
            role=UserRole.PLAYER,
            club_id=user.club_id,
            phone_number=data.get("phone_number"),
            credits_balance=data.get("credits_balance", 0)
        )
        
        # Si un mot de passe est fourni
        if data.get("password"):
            from werkzeug.security import generate_password_hash
            new_player.password_hash = generate_password_hash(data["password"])
        
        db.session.add(new_player)
        db.session.commit()
        
        return jsonify({
            "message": "Joueur créé avec succès",
            "player": new_player.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la création du joueur: {e}")
        return jsonify({"error": "Erreur lors de la création du joueur"}), 500

@clubs_bp.route("/players/<int:player_id>", methods=["PUT"])
def update_player(player_id):
    """Permet aux clubs de modifier les informations des joueurs"""
    user = require_club_access()
    if not user:
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        # Vérifier que le joueur appartient au club
        player = User.query.get(player_id)
        if not player or player.club_id != user.club_id:
            return jsonify({"error": "Joueur non trouvé dans ce club"}), 404
        
        data = request.get_json()
        
        # Mise à jour des champs autorisés
        if "name" in data:
            player.name = data["name"].strip()
        if "phone_number" in data:
            player.phone_number = data["phone_number"]
        if "credits_balance" in data:
            player.credits_balance = data["credits_balance"]
        if "profile_photo_url" in data:
            player.profile_photo_url = data["profile_photo_url"]
        
        # Mise à jour du mot de passe si fourni
        if data.get("password"):
            from werkzeug.security import generate_password_hash
            player.password_hash = generate_password_hash(data["password"])
        
        db.session.commit()
        
        return jsonify({
            "message": "Joueur mis à jour avec succès",
            "player": player.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la mise à jour du joueur {player_id}: {e}")
        return jsonify({"error": "Erreur lors de la mise à jour du joueur"}), 500

@clubs_bp.route("/courts", methods=["GET"])
def get_club_courts():
    """Récupère tous les terrains du club avec leurs caméras"""
    user = require_club_access()
    if not user:
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        if not user.club_id:
            return jsonify({"error": "Club non trouvé"}), 404
        
        courts = Court.query.filter_by(club_id=user.club_id).all()
        
        return jsonify({
            "courts": [court.to_dict() for court in courts]
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des terrains du club: {e}")
        return jsonify({"error": "Erreur lors de la récupération des terrains"}), 500


@clubs_bp.route("/dashboard", methods=["GET"])
def get_club_dashboard():
    user = require_club_access()
    if not user:
        return jsonify({"error": "Accès non autorisé"}), 403

    try:
        # Récupérer les informations du club
        club = Club.query.get(user.club_id) if user.club_id else None
        if not club:
            return jsonify({"error": "Club non trouvé"}), 404

        # Récupérer les joueurs du club
        players = User.query.filter_by(club_id=club.id, role=UserRole.PLAYER).all()

        # Récupérer les terrains du club
        courts = Court.query.filter_by(club_id=club.id).all()

        # Récupérer toutes les vidéos des joueurs du club
        player_ids = [player.id for player in players]
        videos = Video.query.filter(Video.user_id.in_(player_ids)).order_by(Video.recorded_at.desc()).all()

        # Statistiques
        total_videos = len(videos)
        total_players = len(players)
        total_credits_distributed = sum(player.credits_balance for player in players)
        total_courts = len(courts)

        return jsonify({
            "club": club.to_dict(),
            "players": [player.to_dict() for player in players],
            "courts": [court.to_dict() for court in courts],  # TERRAINS INCLUS
            "videos": [video.to_dict() for video in videos],
            "stats": {
                "total_videos": total_videos,
                "total_players": total_players,
                "total_credits_distributed": total_credits_distributed,
                "total_courts": total_courts
            }
        }), 200

    except Exception as e:
        logger.error(f"Erreur serveur lors du chargement du tableau de bord du club: {e}")
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500
