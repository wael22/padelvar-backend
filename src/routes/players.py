from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, Club, UserRole
# MODIFICATION : On importe la fonction de log depuis admin
from src.routes.admin import log_club_action
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

players_bp = Blueprint("players", __name__)

def get_current_user():
    user_id = session.get("user_id")
    if not user_id: return None
    return User.query.get(user_id)

def require_player_access():
    user = get_current_user()
    if not user or user.role != UserRole.PLAYER: return None
    return user

@players_bp.route("/clubs/available", methods=["GET"])
def get_available_clubs():
    user = require_player_access()
    if not user: return jsonify({"error": "Accès non autorisé"}), 403
    all_clubs = Club.query.all()
    followed_ids = {c.id for c in user.followed_clubs}
    clubs_data = []
    for club in all_clubs:
        club_dict = club.to_dict()
        club_dict["is_followed"] = club.id in followed_ids
        clubs_data.append(club_dict)
    return jsonify({"clubs": clubs_data}), 200

@players_bp.route("/clubs/<int:club_id>/follow", methods=["POST"])
def follow_club(club_id):
    user = require_player_access()
    if not user: return jsonify({"error": "Accès non autorisé"}), 403
    club = Club.query.get_or_404(club_id)
    if user in club.followers:
        return jsonify({"error": "Vous suivez déjà ce club"}), 409
    
    club.followers.append(user)
    if user.club_id is None:
        user.club_id = club.id
    
    # MODIFICATION : Utilisation de la fonction de log centralisée
    log_club_action(
        user_id=user.id,
        club_id=club_id,
        action_type='follow_club',
        details={"club_name": club.name},
        performed_by_id=user.id
    )
    # db.session.commit() est déjà appelé dans log_club_action
    
    return jsonify({"message": f"Vous suivez maintenant {club.name}"}), 200

@players_bp.route("/clubs/<int:club_id>/unfollow", methods=["POST"])
def unfollow_club(club_id):
    user = require_player_access()
    if not user: return jsonify({"error": "Accès non autorisé"}), 403
    club = Club.query.get_or_404(club_id)
    if user not in club.followers:
        return jsonify({"error": "Vous ne suivez pas ce club"}), 409
        
    club.followers.remove(user)
    
    # MODIFICATION : Utilisation de la fonction de log centralisée
    log_club_action(
        user_id=user.id,
        club_id=club_id,
        action_type='unfollow_club',
        details={"club_name": club.name},
        performed_by_id=user.id
    )
    # db.session.commit() est déjà appelé dans log_club_action

    return jsonify({"message": f"Vous ne suivez plus {club.name}"}), 200

@players_bp.route("/clubs/followed", methods=["GET"])
def get_followed_clubs():
    user = require_player_access()
    if not user: return jsonify({"error": "Accès non autorisé"}), 403
    return jsonify({"clubs": [club.to_dict() for club in user.followed_clubs]}), 200
