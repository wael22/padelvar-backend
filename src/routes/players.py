from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, Club, ClubHistory, ActionType, UserRole
import logging
import json

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

players_bp = Blueprint("players", __name__)

def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)

def require_player_access():
    user = get_current_user()
    if not user or user.role != UserRole.PLAYER:
        return None
    return user

def log_club_action(club_id, player_id, action_type, action_details, performed_by_id):
    """Enregistre une action dans l'historique du club"""
    try:
        history_entry = ClubHistory(
            club_id=club_id,
            player_id=player_id,
            action_type=action_type,
            action_details=json.dumps(action_details) if action_details else None,
            performed_by_id=performed_by_id
        )
        db.session.add(history_entry)
        db.session.commit()
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement de l'historique: {e}")

@players_bp.route("/clubs/available", methods=["GET"])
def get_available_clubs():
    """Récupère tous les clubs disponibles pour qu'un joueur puisse les suivre"""
    user = require_player_access()
    if not user:
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        # Récupérer tous les clubs
        all_clubs = Club.query.all()
        
        # Pour l'instant, marquer tous les clubs comme non suivis
        # TODO: Implémenter la logique de suivi après création des tables
        clubs_data = []
        for club in all_clubs:
            club_dict = club.to_dict()
            club_dict["is_followed"] = False  # Temporaire
            clubs_data.append(club_dict)
        
        return jsonify({"clubs": clubs_data}), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des clubs disponibles: {e}")
        return jsonify({"error": f"Erreur lors de la récupération des clubs: {str(e)}"}), 500

@players_bp.route("/clubs/<int:club_id>/follow", methods=["POST"])
def follow_club(club_id):
    """Permet à un joueur de suivre un club"""
    user = require_player_access()
    if not user:
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        club = Club.query.get(club_id)
        if not club:
            return jsonify({"error": "Club non trouvé"}), 404
        
        # Vérifier si le joueur suit déjà ce club
        if user.followed_clubs.filter_by(id=club_id).first():
            return jsonify({"error": "Vous suivez déjà ce club"}), 409
        
        # Ajouter le club aux clubs suivis
        user.followed_clubs.append(club)
        db.session.commit()
        
        # Enregistrer l'action dans l'historique
        log_club_action(
            club_id=club_id,
            player_id=user.id,
            action_type=ActionType.FOLLOW_CLUB,
            action_details={"club_name": club.name},
            performed_by_id=user.id
        )
        
        return jsonify({
            "message": f"Vous suivez maintenant {club.name}",
            "club": club.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors du suivi du club {club_id}: {e}")
        return jsonify({"error": "Erreur lors du suivi du club"}), 500

@players_bp.route("/clubs/<int:club_id>/unfollow", methods=["POST"])
def unfollow_club(club_id):
    """Permet à un joueur de ne plus suivre un club"""
    user = require_player_access()
    if not user:
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        club = Club.query.get(club_id)
        if not club:
            return jsonify({"error": "Club non trouvé"}), 404
        
        # Vérifier si le joueur suit ce club
        followed_club = user.followed_clubs.filter_by(id=club_id).first()
        if not followed_club:
            return jsonify({"error": "Vous ne suivez pas ce club"}), 409
        
        # Retirer le club des clubs suivis
        user.followed_clubs.remove(club)
        db.session.commit()
        
        # Enregistrer l'action dans l'historique
        log_club_action(
            club_id=club_id,
            player_id=user.id,
            action_type=ActionType.UNFOLLOW_CLUB,
            action_details={"club_name": club.name},
            performed_by_id=user.id
        )
        
        return jsonify({
            "message": f"Vous ne suivez plus {club.name}",
            "club": club.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de l'arrêt du suivi du club {club_id}: {e}")
        return jsonify({"error": "Erreur lors de l'arrêt du suivi du club"}), 500

@players_bp.route("/clubs/followed", methods=["GET"])
def get_followed_clubs():
    """Récupère la liste des clubs suivis par le joueur"""
    user = require_player_access()
    if not user:
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        followed_clubs = user.followed_clubs.all()
        
        return jsonify({
            "clubs": [club.to_dict() for club in followed_clubs]
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des clubs suivis: {e}")
        return jsonify({"error": "Erreur lors de la récupération des clubs suivis"}), 500
