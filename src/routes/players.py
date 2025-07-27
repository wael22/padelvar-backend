# padelvar-backend/src/routes/players.py

from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, Club, UserRole, ClubActionHistory
import logging
import json

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

def log_action(club_id, player_id, action_type, action_details, performed_by_id):
    try:
        history_entry = ClubActionHistory(
            club_id=club_id, user_id=player_id, action_type=action_type,
            action_details=json.dumps(action_details) if action_details else None,
            performed_by_id=performed_by_id
        )
        db.session.add(history_entry)
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de l'enregistrement de l'historique: {e}")

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
    
    if club in user.followed_clubs:
        return jsonify({"error": "Vous suivez déjà ce club"}), 409
        
    user.followed_clubs.append(club)
    user.club_id = club.id
    
    log_action(
        club_id=club_id, player_id=user.id, action_type='follow_club',
        action_details={"club_name": club.name}, performed_by_id=user.id
    )
    
    db.session.commit()
    return jsonify({"message": f"Vous suivez maintenant {club.name}"}), 200

# ====================================================================
# CORRECTION APPLIQUÉE ICI
# ====================================================================
@players_bp.route("/clubs/<int:club_id>/unfollow", methods=["POST"])
def unfollow_club(club_id):
    user = require_player_access()
    if not user: return jsonify({"error": "Accès non autorisé"}), 403
    
    club = Club.query.get_or_404(club_id)
    
    if club not in user.followed_clubs:
        return jsonify({"error": "Vous ne suivez pas ce club"}), 409
        
    user.followed_clubs.remove(club)
    
    # LIGNE CRUCIALE POUR CORRIGER LE COMPTAGE DES JOUEURS
    # Si le joueur quitte le club qui était défini comme son club principal,
    # on réinitialise son affiliation à "Aucun club".
    if user.club_id == club_id:
        user.club_id = None
    
    log_action(
        club_id=club_id, player_id=user.id, action_type='unfollow_club',
        action_details={"club_name": club.name}, performed_by_id=user.id
    )
    
    db.session.commit()
    
    return jsonify({"message": f"Vous ne suivez plus {club.name}"}), 200

@players_bp.route("/clubs/followed", methods=["GET"])
def get_followed_clubs():
    user = require_player_access()
    if not user: return jsonify({"error": "Accès non autorisé"}), 403
    
    return jsonify({"clubs": [club.to_dict() for club in user.followed_clubs]}), 200