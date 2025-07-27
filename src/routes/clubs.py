# padelvar-backend/src/routes/clubs.py

from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, Club, Video, UserRole, Court, ClubActionHistory
import logging
import json
from datetime import datetime
from sqlalchemy.orm import aliased
from sqlalchemy import func, cast

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

clubs_bp = Blueprint("clubs", __name__)

# --- Fonctions Utilitaires ---

def get_current_user():
    user_id = session.get("user_id")
    if not user_id: return None
    return User.query.get(user_id)

def require_club_access():
    user = get_current_user()
    if not user or user.role != UserRole.CLUB: return None
    return user

def log_club_action(club_id, user_id, action_type, details, performed_by_id):
    try:
        history_entry = ClubActionHistory(
            club_id=club_id, user_id=user_id, action_type=action_type,
            action_details=json.dumps(details) if details else None,
            performed_by_id=performed_by_id, performed_at=datetime.utcnow()
        )
        db.session.add(history_entry)
    except Exception as e:
        logger.error(f"Erreur lors de la préparation du log d'historique: {e}")

# --- Routes du Club ---

@clubs_bp.route("/dashboard", methods=["GET"])
def get_club_dashboard():
    user = require_club_access()
    if not user: return jsonify({"error": "Accès non autorisé"}), 401
    
    club = Club.query.get(user.club_id)
    if not club: return jsonify({"error": "Club non trouvé"}), 404

    registered_players = User.query.filter_by(club_id=club.id, role=UserRole.PLAYER).all()
    
    videos_results = db.session.query(Video, User.name.label('player_name'))\
        .join(Court, Video.court_id == Court.id)\
        .join(User, Video.user_id == User.id)\
        .filter(Court.club_id == club.id)\
        .order_by(Video.recorded_at.desc()).all()
    
    videos_data = [dict(video.to_dict(), player_name=player_name) for video, player_name in videos_results]

    history_credits = ClubActionHistory.query.filter_by(club_id=club.id, action_type='add_credits').all()
    total_credits_offered = sum(int(json.loads(e.action_details).get('credits_added', 0)) for e in history_credits if e.action_details)

    return jsonify({
        "club": club.to_dict(),
        "stats": {
            "total_players": len(registered_players), "total_videos": len(videos_data),
            "total_credits_offered": total_credits_offered,
            "total_courts": len(club.courts) if club.courts else 0
        },
        "players": [p.to_dict() for p in registered_players],
        "videos": videos_data,
        "courts": [court.to_dict() for court in club.courts] if hasattr(club, 'courts') else []
    }), 200

@clubs_bp.route("/<int:player_id>/add-credits", methods=["POST"])
def add_credits_to_player(player_id):
    club_user = require_club_access()
    if not club_user: return jsonify({"error": "Accès non autorisé"}), 403

    data = request.get_json()
    credits_to_add = data.get("credits")
    if not isinstance(credits_to_add, int) or credits_to_add <= 0:
        return jsonify({"error": "Le nombre de crédits doit être un entier positif."}), 400

    player = User.query.get_or_404(player_id)
    if player.club_id != club_user.club_id:
        return jsonify({"error": "Ce joueur n'appartient pas à votre club."}), 403

    try:
        old_balance = player.credits_balance
        player.credits_balance += credits_to_add
        log_club_action(
            club_id=club_user.club_id, user_id=player.id, action_type='add_credits',
            details={'credits_added': credits_to_add, 'old_balance': old_balance, 'new_balance': player.credits_balance},
            performed_by_id=club_user.id
        )
        db.session.commit()
        return jsonify({"message": f"{credits_to_add} crédits ajoutés à {player.name}."}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de l'ajout de crédits par le club: {e}")
        return jsonify({"error": "Une erreur interne est survenue."}), 500

# ====================================================================
# VERSION FINALE ET CORRIGÉE DE LA MISE À JOUR DU PROFIL
# ====================================================================
@clubs_bp.route("/profile", methods=["PUT"])
def update_club_profile():
    user = require_club_access()
    if not user:
        return jsonify({"error": "Accès non autorisé"}), 401

    club = Club.query.get(user.club_id)
    if not club:
        return jsonify({"error": "Club non trouvé"}), 404
        
    data = request.get_json()
    if not data:
        return jsonify({"error": "Données manquantes"}), 400
    
    try:
        # On garde une trace si des changements ont été faits
        has_changed = False

        # Mise à jour du nom
        if 'name' in data and data['name'].strip() != club.name:
            new_name = data['name'].strip()
            if new_name: # On ne met pas à jour avec un nom vide
                club.name = new_name
                user.name = new_name # Important de synchroniser le nom de l'utilisateur
                has_changed = True

        # Mise à jour de l'adresse
        if 'address' in data and data['address'] != club.address:
            club.address = data['address']
            has_changed = True

        # Mise à jour du numéro de téléphone
        if 'phone_number' in data and data['phone_number'] != club.phone_number:
            club.phone_number = data['phone_number']
            has_changed = True
        
        # On ne commit que si quelque chose a réellement changé
        if has_changed:
            db.session.add(club)
            db.session.add(user)
            db.session.commit()
        
        return jsonify({"message": "Profil du club mis à jour", "club": club.to_dict()}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la mise à jour du profil club: {e}")
        return jsonify({"error": "Erreur lors de la mise à jour"}), 500

# ... (le reste des routes /videos, /history, etc. sont ici)
@clubs_bp.route("/videos", methods=["GET"])
def get_club_videos():
    user = require_club_access()
    if not user: return jsonify({"error": "Accès non autorisé"}), 403
    
    club = Club.query.get(user.club_id)
    if not club: return jsonify({"error": "Club non trouvé"}), 404

    registered_players = User.query.filter_by(club_id=club.id, role=UserRole.PLAYER).all()
    player_ids = [p.id for p in registered_players]
    
    videos = db.session.query(Video, User.name.label('player_name'))\
        .join(User, Video.user_id == User.id)\
        .filter(Video.user_id.in_(player_ids)).order_by(Video.recorded_at.desc()).all() if player_ids else []

    videos_data = []
    for video, player_name in videos:
        video_dict = video.to_dict()
        video_dict['player_name'] = player_name
        videos_data.append(video_dict)
        
    return jsonify({"videos": videos_data}), 200

@clubs_bp.route("/history", methods=["GET"])
def get_club_history():
    user = require_club_access()
    if not user: return jsonify({"error": "Accès non autorisé"}), 403
    
    club = Club.query.get(user.club_id)
    if not club: return jsonify({"error": "Club non trouvé"}), 404

    Player = aliased(User)
    Performer = aliased(User)
    history_entries = (
        db.session.query(
            ClubActionHistory,
            Player.name.label('player_name'),
            Performer.name.label('performed_by_name')
        )
        .join(Player, ClubActionHistory.user_id == Player.id)
        .join(Performer, ClubActionHistory.performed_by_id == Performer.id)
        .filter(ClubActionHistory.club_id == club.id)
        .order_by(ClubActionHistory.performed_at.desc())
        .limit(100)
        .all()
    )

    history_data = []
    for entry, player_name, performed_by_name in history_entries:
        entry_dict = entry.to_dict()
        entry_dict['player_name'] = player_name
        entry_dict['performed_by_name'] = performed_by_name
        history_data.append(entry_dict)
    return jsonify({"history": history_data}), 200

@clubs_bp.route("/followers", methods=["GET"])
def get_club_followers():
    user = require_club_access()
    if not user:
        return jsonify({"error": "Accès non autorisé"}), 403
    club = Club.query.get(user.club_id)
    if not club:
        return jsonify({"error": "Club non trouvé"}), 404
    followers = club.followers.all() if hasattr(club, 'followers') else []
    return jsonify({"followers": [f.to_dict() for f in followers]}), 200

@clubs_bp.route("/follow", methods=["POST"])
def follow_club():
    user_id = session.get("user_id")
    club_id = request.json.get("club_id")
    if not user_id or not club_id:
        return jsonify({"error": "Données manquantes"}), 400
    user = User.query.get(user_id)
    club = Club.query.get(club_id)
    if not user or not club:
        return jsonify({"error": "Utilisateur ou club introuvable"}), 404

    if club not in user.followed_clubs:
        user.followed_clubs.append(club)
    
    user.club_id = club.id
    db.session.commit()
    return jsonify({"success": True, "user": user.to_dict()}), 200