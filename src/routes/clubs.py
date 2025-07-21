
from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, Club, Video, UserRole, Court, ClubHistory
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

clubs_bp = Blueprint("clubs", __name__)

def require_club_access():
    user = get_current_user()
    if not user or user.role != UserRole.CLUB:
        return None, (jsonify({"error": "Accès non autorisé"}), 403)
    if not getattr(user, 'club_id', None):
        return None, (jsonify({"error": "Club non associé à cet utilisateur"}), 404)
    return user, None

def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)

# --- ROUTES DE GESTION DES JOUEURS PAR LE CLUB ---
# CORRECTION: Simplification des URL. Ex: /api/clubs/players/3 -> /api/clubs/3

@clubs_bp.route("/<int:player_id>", methods=["PUT"])
def update_player_by_club(player_id):
    """Permet aux clubs de modifier les informations des joueurs"""
    club_user, error = require_club_access()
    if error: return error
    
    player = User.query.get(player_id)
    club_id = getattr(club_user, 'club_id', None)
    if not player or not getattr(player, 'club_id', None) or player.club_id != club_id:
        return jsonify({"error": "Joueur non trouvé dans ce club"}), 404
    
    data = request.get_json()
    if "name" in data: player.name = data["name"].strip()
    if "phone_number" in data: player.phone_number = data["phone_number"]
    if "credits_balance" in data: player.credits_balance = data["credits_balance"]
    
    db.session.commit()
    return jsonify({"message": "Joueur mis à jour", "player": player.to_dict()}), 200

@clubs_bp.route("/<int:player_id>/add-credits", methods=["POST"])
def add_credits_to_player_by_club(player_id):
    """Permet aux clubs d'ajouter des crédits à un joueur"""
    club_user, error = require_club_access()
    if error: return error

    player = User.query.get(player_id)
    club_id = getattr(club_user, 'club_id', None)
    if not player or not getattr(player, 'club_id', None) or player.club_id != club_id:
        return jsonify({"error": "Joueur non trouvé dans ce club"}), 404
        
    data = request.get_json()
    credits_to_add = data.get("credits", 0)
    if not isinstance(credits_to_add, int) or credits_to_add <= 0:
        return jsonify({"error": "Le nombre de crédits doit être un entier positif"}), 400
        
    player.credits_balance += credits_to_add
    db.session.commit()
    return jsonify({"message": "Crédits ajoutés", "player": player.to_dict()}), 200

# --- AUTRES ROUTES (Dashboard, Followers, etc.) ---
# Ces routes ne changent pas car elles ne prennent pas d'ID dans l'URL

@clubs_bp.route("/dashboard", methods=["GET"])
def get_club_dashboard():
    user, error = require_club_access()
    if error: return error
    try:
        club_id = getattr(user, 'club_id', None)
        if not club_id:
            return jsonify({"error": "Club non trouvé"}), 404
        club = Club.query.get(club_id)
        if not club:
            return jsonify({"error": "Club non trouvé"}), 404
        players = User.query.filter_by(club_id=club.id, role=UserRole.PLAYER).all()
        courts = Court.query.filter_by(club_id=club.id).all()
        player_ids = [p.id for p in players]
        videos = Video.query.filter(Video.user_id.in_(player_ids)).all()
        return jsonify({
            "club": club.to_dict(),
            "players": [p.to_dict() for p in players],
            "courts": [c.to_dict() for c in courts],
            "videos": [v.to_dict() for v in videos],
            "stats": {
                "total_players": len(players),
                "total_videos": len(videos),
                "total_credits_distributed": sum(p.credits_balance for p in players),
                "total_courts": len(courts)
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@clubs_bp.route("/followers", methods=["GET"])
def get_club_followers():
    user, error = require_club_access()
    if error: return error
    club_id = getattr(user, 'club_id', None)
    if not club_id:
        return jsonify({"error": "Club non trouvé"}), 404
    followers = User.query.filter(User.followed_clubs.any(id=club_id)).all()
    return jsonify({"followers": [f.to_dict() for f in followers]}), 200

@clubs_bp.route("/history", methods=["GET"])
def get_club_history():
    user, error = require_club_access()
    if error: return error
    club_id = getattr(user, 'club_id', None)
    if not club_id:
        return jsonify({"error": "Club non trouvé"}), 404
    history_entries = db.session.query(ClubHistory, User.name.label('player_name')).join(User, ClubHistory.player_id == User.id).filter(ClubHistory.club_id == club_id).order_by(ClubHistory.performed_at.desc()).limit(100).all()
    history_list = []
    for entry, name in history_entries:
        if entry and hasattr(entry, 'to_dict'):
            d = entry.to_dict()
            d['player_name'] = name
            history_list.append(d)
    return jsonify({"history": history_list}), 200

# ... (gardez les autres routes comme /all, /info, etc. si elles existent)
