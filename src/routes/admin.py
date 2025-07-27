# padelvar-backend/src/routes/admin.py

from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, Club, Court, Video, UserRole, ClubActionHistory
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
import uuid
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__)

# --- Fonctions Utilitaires ---

def require_super_admin():
    user_id = session.get("user_id")
    user_role = session.get("user_role")
    if not user_id or user_role != UserRole.SUPER_ADMIN.value:
        return False
    return True

def log_club_action(user_id, club_id, action_type, details=None, performed_by_id=None):
    try:
        if performed_by_id is None:
            performed_by_id = user_id
        
        if not club_id:
            db.session.commit()
            return

        history_entry = ClubActionHistory(
            user_id=user_id,
            club_id=club_id,
            action_type=action_type,
            action_details=json.dumps(details) if details else None,
            performed_by_id=performed_by_id,
            performed_at=datetime.utcnow()
        )
        db.session.add(history_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de l'enregistrement de l'historique: {e}")

# --- ROUTES DE GESTION DES UTILISATEURS (CRUD COMPLET) ---

@admin_bp.route("/users", methods=["GET"])
def get_all_users():
    if not require_super_admin(): return jsonify({"error": "Accès non autorisé"}), 403
    users = User.query.all()
    return jsonify({"users": [user.to_dict() for user in users]}), 200

@admin_bp.route("/users", methods=["POST"])
def create_user():
    if not require_super_admin(): return jsonify({"error": "Accès non autorisé"}), 403
    data = request.get_json()
    try:
        new_user = User(
            email=data["email"].lower().strip(),
            name=data["name"].strip(),
            role=UserRole(data["role"]),
            phone_number=data.get("phone_number"),
            credits_balance=data.get("credits_balance", 0)
        )
        if data.get("password"):
            new_user.password_hash = generate_password_hash(data["password"])
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "Utilisateur créé", "user": new_user.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la création"}), 500

@admin_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    if not require_super_admin(): return jsonify({"error": "Accès non autorisé"}), 403
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    try:
        if "name" in data: user.name = data["name"]
        if "phone_number" in data: user.phone_number = data["phone_number"]
        if "credits_balance" in data: user.credits_balance = data["credits_balance"]
        if "role" in data: user.role = UserRole(data["role"])
        db.session.commit()
        return jsonify({"message": "Utilisateur mis à jour", "user": user.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la mise à jour"}), 500

@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    if not require_super_admin(): return jsonify({"error": "Accès non autorisé"}), 403
    user = User.query.get_or_404(user_id)
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "Utilisateur supprimé"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la suppression"}), 500

@admin_bp.route("/users/<int:user_id>/credits", methods=["POST"])
def add_credits(user_id):
    if not require_super_admin(): return jsonify({"error": "Accès non autorisé"}), 403
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    credits_to_add = data.get("credits", 0)
    
    if not isinstance(credits_to_add, int) or credits_to_add <= 0:
        return jsonify({"error": "Le nombre de crédits doit être un entier positif"}), 400

    try:
        old_balance = user.credits_balance
        user.credits_balance += credits_to_add
        
        log_club_action(
            user_id=user.id, 
            club_id=user.club_id,
            action_type='add_credits', 
            details={'credits_added': credits_to_add, 'old_balance': old_balance, 'new_balance': user.credits_balance}, 
            performed_by_id=session.get('user_id')
        )
        
        return jsonify({"message": "Crédits ajoutés", "user": user.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de l'ajout de crédits: {e}")
        return jsonify({"error": "Erreur lors de l'ajout de crédits"}), 500

# --- ROUTES DE GESTION DES CLUBS (CRUD COMPLET) ---

@admin_bp.route("/clubs", methods=["GET"])
def get_all_clubs():
    if not require_super_admin(): return jsonify({"error": "Accès non autorisé"}), 403
    clubs = Club.query.all()
    return jsonify({"clubs": [club.to_dict() for club in clubs]}), 200

@admin_bp.route("/clubs", methods=["POST"])
def create_club():
    if not require_super_admin(): return jsonify({"error": "Accès non autorisé"}), 403
    data = request.get_json()
    try:
        new_club = Club(name=data["name"], email=data["email"], address=data.get("address"), phone_number=data.get("phone_number"))
        db.session.add(new_club)
        db.session.flush()
        club_user = User(email=data["email"], name=data["name"], role=UserRole.CLUB, club_id=new_club.id)
        if data.get("password"):
            club_user.password_hash = generate_password_hash(data["password"])
        db.session.add(club_user)
        db.session.commit()
        return jsonify({"message": "Club créé", "club": new_club.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la création"}), 500

@admin_bp.route("/clubs/<int:club_id>", methods=["PUT"])
def update_club(club_id):
    if not require_super_admin(): return jsonify({"error": "Accès non autorisé"}), 403
    club = Club.query.get_or_404(club_id)
    data = request.get_json()
    try:
        if "name" in data: club.name = data["name"]
        if "address" in data: club.address = data["address"]
        if "phone_number" in data: club.phone_number = data["phone_number"]
        if "email" in data: club.email = data["email"]
        db.session.commit()
        return jsonify({"message": "Club mis à jour", "club": club.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la mise à jour"}), 500

@admin_bp.route("/clubs/<int:club_id>", methods=["DELETE"])
def delete_club(club_id):
    if not require_super_admin(): return jsonify({"error": "Accès non autorisé"}), 403
    club = Club.query.get_or_404(club_id)
    try:
        Court.query.filter_by(club_id=club_id).delete()
        User.query.filter_by(club_id=club_id).delete()
        db.session.delete(club)
        db.session.commit()
        return jsonify({"message": "Club supprimé"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la suppression"}), 500

# --- ROUTES DE GESTION DES TERRAINS (CRUD COMPLET) ---

@admin_bp.route("/clubs/<int:club_id>/courts", methods=["GET"])
def get_club_courts(club_id):
    if not require_super_admin(): return jsonify({"error": "Accès non autorisé"}), 403
    club = Club.query.get_or_404(club_id)
    return jsonify({"courts": [court.to_dict() for court in club.courts]}), 200

@admin_bp.route("/clubs/<int:club_id>/courts", methods=["POST"])
def create_court(club_id):
    if not require_super_admin(): return jsonify({"error": "Accès non autorisé"}), 403
    data = request.get_json()
    try:
        new_court = Court(name=data["name"], camera_url=data["camera_url"], club_id=club_id, qr_code=str(uuid.uuid4()))
        db.session.add(new_court)
        db.session.commit()
        return jsonify({"message": "Terrain créé", "court": new_court.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la création"}), 500

@admin_bp.route("/courts/<int:court_id>", methods=["PUT"])
def update_court(court_id):
    if not require_super_admin(): return jsonify({"error": "Accès non autorisé"}), 403
    court = Court.query.get_or_404(court_id)
    data = request.get_json()
    try:
        if "name" in data: court.name = data["name"]
        if "camera_url" in data: court.camera_url = data["camera_url"]
        db.session.commit()
        return jsonify({"message": "Terrain mis à jour", "court": court.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la mise à jour"}), 500

@admin_bp.route("/courts/<int:court_id>", methods=["DELETE"])
def delete_court(court_id):
    if not require_super_admin(): return jsonify({"error": "Accès non autorisé"}), 403
    court = Court.query.get_or_404(court_id)
    try:
        db.session.delete(court)
        db.session.commit()
        return jsonify({"message": "Terrain supprimé"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la suppression"}), 500

# --- ROUTES VIDÉOS & HISTORIQUE ---

@admin_bp.route("/videos/all-clubs", methods=["GET"])
def get_all_clubs_videos():
    if not require_super_admin(): return jsonify({"error": "Accès non autorisé"}), 403
    try:
        results = db.session.query(
            Video,
            User.name.label('player_name'),
            Club.name.label('club_name')
        ).join(User, Video.user_id == User.id)\
         .join(Court, Video.court_id == Court.id)\
         .join(Club, Court.club_id == Club.id)\
         .order_by(Video.recorded_at.desc()).all()

        videos_data = []
        for video, player_name, club_name in results:
            video_dict = video.to_dict()
            video_dict['player_name'] = player_name
            video_dict['club_name'] = club_name
            videos_data.append(video_dict)
        
        return jsonify({"videos": videos_data}), 200
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des vidéos: {e}")
        return jsonify({"error": "Erreur serveur"}), 500

@admin_bp.route("/clubs/history/all", methods=["GET"])
def get_all_clubs_history():
    if not require_super_admin(): return jsonify({"error": "Accès non autorisé"}), 403
    try:
        history_entries = db.session.query(ClubActionHistory).order_by(ClubActionHistory.performed_at.desc()).all()
        
        user_ids = {h.user_id for h in history_entries} | {h.performed_by_id for h in history_entries}
        club_ids = {h.club_id for h in history_entries if h.club_id is not None}
        
        users = {u.id: u.name for u in User.query.filter(User.id.in_(user_ids)).all()}
        clubs = {c.id: c.name for c in Club.query.filter(Club.id.in_(club_ids)).all()}

        history_data = []
        for entry in history_entries:
            history_data.append({
                "id": entry.id,
                "user_id": entry.user_id,
                "club_id": entry.club_id,
                "player_name": users.get(entry.user_id, "N/A"),
                "club_name": clubs.get(entry.club_id, "N/A"),
                "action_type": entry.action_type,
                "action_details": entry.action_details,
                "performed_at": entry.performed_at.isoformat(),
                "performed_by_name": users.get(entry.performed_by_id, "N/A")
            })
            
        return jsonify({"history": history_data}), 200
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'historique: {e}")
        return jsonify({"error": "Erreur serveur"}), 500
