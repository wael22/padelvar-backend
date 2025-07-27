from flask import Blueprint, request, jsonify, session
# MODIFIÉ : On importe ClubActionHistory
from src.models.user import db, User, Club, Video, UserRole, Court, ClubActionHistory
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

clubs_bp = Blueprint("clubs", __name__)

# Route pour qu'un joueur suive un club et soit ajouté à la liste des joueurs du club
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
    # Ajoute le club à la liste des clubs suivis
    if club not in user.followed_clubs:
        user.followed_clubs.append(club)
    # Met à jour le club_id pour l'afficher dans Joueurs du Club
    user.club_id = club.id
    db.session.commit()
    return jsonify({"success": True, "user": user.to_dict()}), 200
from flask import Blueprint, request, jsonify, session
# MODIFIÉ : On importe ClubActionHistory
from src.models.user import db, User, Club, Video, UserRole, Court, ClubActionHistory
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

clubs_bp = Blueprint("clubs", __name__)

# Nouvelle route pour récupérer les followers du club
@clubs_bp.route("/followers", methods=["GET"])
def get_club_followers():
    user = require_club_access()
    if not user:
        return jsonify({"error": "Accès non autorisé"}), 403
    club = Club.query.get(user.club_id)
    if not club:
        return jsonify({"error": "Club non trouvé"}), 404
    # Les followers sont les joueurs qui suivent ce club
    followers = club.followers.all() if hasattr(club, 'followers') else []
    return jsonify({"followers": [f.to_dict() for f in followers]}), 200

from flask import Blueprint, request, jsonify, session
# MODIFIÉ : On importe ClubActionHistory
from src.models.user import db, User, Club, Video, UserRole, Court, ClubActionHistory
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

clubs_bp = Blueprint("clubs", __name__)

def get_current_user():
    user_id = session.get("user_id")
    if not user_id: return None
    return User.query.get(user_id)

def require_club_access():
    user = get_current_user()
    if not user or user.role != UserRole.CLUB: return None
    return user

@clubs_bp.route("/dashboard", methods=["GET"])
def get_club_dashboard():
    user = require_club_access()
    if not user: return jsonify({"error": "Accès non autorisé"}), 403
    
    club = Club.query.get(user.club_id)
    if not club: return jsonify({"error": "Club non trouvé"}), 404

    # On récupère les joueurs inscrits (ceux qui ont ce club_id)
    registered_players = User.query.filter_by(club_id=club.id, role=UserRole.PLAYER).all()
    
    # On récupère les vidéos de ces joueurs
    player_ids = [p.id for p in registered_players]
    videos = Video.query.filter(Video.user_id.in_(player_ids)).all() if player_ids else []

    return jsonify({
        "club": club.to_dict(),
        "stats": {
            "total_players": len(registered_players),
            "total_videos": len(videos),
            "total_credits_distributed": sum(p.credits_balance for p in registered_players),
            "total_courts": len(club.courts)
        },
        "players": [p.to_dict() for p in registered_players],
        "videos": [v.to_dict() for v in videos],
        "courts": [court.to_dict() for court in club.courts] if hasattr(club, 'courts') else []
    }), 200

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

    # MODIFIÉ : On utilise ClubActionHistory
    # Join User twice: once for the player, once for performed_by
    from sqlalchemy.orm import aliased
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

# ... (gardez les autres routes du club si elles existent)
