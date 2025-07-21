from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, Club, Court, Video, UserRole
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
import uuid
import logging








# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__)

def require_super_admin():
    user_id = session.get("user_id")
    user_role = session.get("user_role")
    
    if not user_id or user_role != UserRole.SUPER_ADMIN.value:
        return False
    return True


@admin_bp.route("/users", methods=["GET"])
def get_all_users():
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        users = User.query.all()
        return jsonify({"users": [user.to_dict() for user in users]}), 200
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des utilisateurs: {e}")
        return jsonify({"error": "Erreur lors de la récupération des utilisateurs"}), 500


@admin_bp.route("/users", methods=["POST"])
def create_user():
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    data = request.get_json()
    if not data or not data.get("email") or not data.get("name") or not data.get("role"):
        return jsonify({"error": "Email, nom et rôle requis"}), 400
    
    try:
        email = data["email"].lower().strip()
        name = data["name"].strip()
        role = data["role"]
        
        # Valider rôle
        try:
            user_role = UserRole(role)
        except ValueError:
            return jsonify({"error": "Rôle invalide"}), 400
        
        new_user = User()
        new_user.email = email
        new_user.name = name
        new_user.role = user_role
        new_user.phone_number = data.get("phone_number")
        new_user.credits_balance = data.get("credits_balance", 0)
        if data.get("password"):
            new_user.password_hash = generate_password_hash(data["password"])
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({"message": "Utilisateur créé avec succès", "user": new_user.to_dict()}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Un utilisateur avec cet email existe déjà"}), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la création de l'utilisateur: {e}")
        return jsonify({"error": "Erreur lors de la création de l'utilisateur"}), 500


@admin_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Données requises"}), 400
    
    try:
        if "name" in data:
            user.name = data["name"].strip()
        if "phone_number" in data:
            user.phone_number = data["phone_number"]
        if "credits_balance" in data:
            user.credits_balance = data["credits_balance"]
        if "role" in data:
            try:
                user.role = UserRole(data["role"])
            except ValueError:
                return jsonify({"error": "Rôle invalide"}), 400
        if "email" in data:
            user.email = data["email"].lower().strip()
        if "password" in data and data["password"]:
            user.password_hash = generate_password_hash(data["password"])
        
        # Si c'est un utilisateur de type CLUB, mettre à jour aussi le club associé
        if user.role == UserRole.CLUB and user.club_id:
            club = Club.query.get(user.club_id)
            if club:
                if "name" in data:
                    club.name = data["name"].strip()
                if "email" in data:
                    club.email = data["email"].lower().strip()
                if "phone_number" in data:
                    club.phone_number = data["phone_number"]
        
        db.session.commit()
        return jsonify({"message": "Utilisateur mis à jour avec succès", "user": user.to_dict()}), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Un utilisateur avec cet email existe déjà"}), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la mise à jour de l'utilisateur: {e}")
        return jsonify({"error": "Erreur lors de la mise à jour de l'utilisateur"}), 500


@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "Utilisateur supprimé avec succès"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la suppression de l'utilisateur: {e}")
        return jsonify({"error": "Erreur lors de la suppression de l'utilisateur"}), 500


@admin_bp.route("/clubs", methods=["GET"])
def get_all_clubs():
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        clubs = Club.query.all()
        return jsonify({"clubs": [club.to_dict() for club in clubs]}), 200
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des clubs: {e}")
        return jsonify({"error": "Erreur lors de la récupération des clubs"}), 500


@admin_bp.route("/clubs", methods=["POST"])
def create_club():
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    data = request.get_json()
    if not data or not data.get("name") or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Nom, email et mot de passe requis"}), 400
    
    try:
        email = data["email"].lower().strip()

        # Créer le club
        new_club = Club()
        new_club.name = data["name"].strip()
        new_club.address = data.get("address")
        new_club.phone_number = data.get("phone_number")
        new_club.email = email
        db.session.add(new_club)
        db.session.flush() # Pour obtenir l'ID du club avant le commit

        # Créer automatiquement un utilisateur de type CLUB lié au club créé
        club_user = User()
        club_user.email = email
        club_user.password_hash = generate_password_hash(data["password"])
        club_user.name = data["name"].strip()
        club_user.role = UserRole.CLUB
        club_user.club_id = new_club.id
        db.session.add(club_user)
        db.session.commit()

        return jsonify({
            "message": "Club et utilisateur créés avec succès",
            "club": new_club.to_dict(),
            "user": club_user.to_dict()
        }), 201
    
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Un utilisateur avec cet email existe déjà"}), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la création du club: {e}")
        return jsonify({"error": "Erreur lors de la création du club"}), 500


@admin_bp.route("/clubs/<int:club_id>/courts", methods=["POST"])
def create_court(club_id):
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    club = Club.query.get(club_id)
    if not club:
        return jsonify({"error": "Club non trouvé"}), 404
    
    data = request.get_json()
    if not data or not data.get("name") or not data.get("camera_url"):
        return jsonify({"error": "Nom du terrain et URL de la caméra requis"}), 400
    
    try:
        qr_code = str(uuid.uuid4())
        new_court = Court()
        new_court.name = data["name"].strip()
        new_court.qr_code = qr_code
        new_court.camera_url = data["camera_url"].strip()
        new_court.club_id = club_id
        db.session.add(new_court)
        db.session.commit()
        return jsonify({"message": "Terrain créé avec succès", "court": new_court.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la création du terrain: {e}")
        return jsonify({"error": "Erreur lors de la création du terrain"}), 500


@admin_bp.route("/videos", methods=["GET"])
def get_all_videos():
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        videos = Video.query.all()
        return jsonify({"videos": [video.to_dict() for video in videos]}), 200
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des vidéos: {e}")
        return jsonify({"error": "Erreur lors de la récupération des vidéos"}), 500


@admin_bp.route("/users/<int:user_id>/credits", methods=["POST"])
def add_credits(user_id):
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    
    data = request.get_json()
    credits_to_add = data.get("credits", 0)
    if not isinstance(credits_to_add, int) or credits_to_add <= 0:
        return jsonify({"error": "Le nombre de crédits doit être un entier positif"}), 400
    
    try:
        user.credits_balance += credits_to_add
        db.session.commit()
        return jsonify({"message": f"{credits_to_add} crédits ajoutés avec succès", "user": user.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de l'ajout de crédits: {e}")
        return jsonify({"error": "Erreur lors de l'ajout de crédits"}), 500


@admin_bp.route("/videos/all-clubs", methods=["GET"])
def get_all_clubs_videos():
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        videos = db.session.query(Video, Court, Club, User).join(
            Court, Video.court_id == Court.id
        ).join(
            Club, Court.club_id == Club.id
        ).join(
            User, Video.user_id == User.id
        ).all()

        videos_data = []
        for video, court, club, user in videos:
            video_dict = video.to_dict()
            video_dict["court_name"] = court.name
            video_dict["club_name"] = club.name
            video_dict["player_name"] = user.name
            videos_data.append(video_dict)
        
        return jsonify({"videos": videos_data}), 200
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des vidéos de tous les clubs: {e}")
        return jsonify({"error": "Erreur lors de la récupération des vidéos"}), 500


@admin_bp.route("/clubs/<int:club_id>/courts", methods=["GET"])
def get_club_courts(club_id):
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    club = Club.query.get(club_id)
    if not club:
        return jsonify({"error": "Club non trouvé"}), 404
    
    try:
        courts = Court.query.filter_by(club_id=club_id).all()
        return jsonify({"courts": [court.to_dict() for court in courts]}), 200
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des terrains du club {club_id}: {e}")
        return jsonify({"error": f"Erreur lors de la récupération des terrains: {str(e)}"}), 500


@admin_bp.route("/courts/<int:court_id>", methods=["PUT"])
def update_court(court_id):
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    court = Court.query.get(court_id)
    if not court:
        return jsonify({"error": "Terrain non trouvé"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Données requises"}), 400
    
    try:
        if "name" in data:
            court.name = data["name"].strip()
        if "camera_url" in data:
            court.camera_url = data["camera_url"].strip()
        db.session.commit()
        return jsonify({"message": "Terrain mis à jour avec succès", "court": court.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la mise à jour du terrain {court_id}: {e}")
        return jsonify({"error": f"Erreur lors de la mise à jour du terrain: {str(e)}"}), 500


@admin_bp.route("/courts/<int:court_id>", methods=["DELETE"])
def delete_court(court_id):
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    court = Court.query.get(court_id)
    if not court:
        return jsonify({"error": "Terrain non trouvé"}), 404
    
    try:
        db.session.delete(court)
        db.session.commit()
        return jsonify({"message": "Terrain supprimé avec succès"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la suppression du terrain {court_id}: {e}")
        return jsonify({"error": f"Erreur lors de la suppression du terrain: {str(e)}"}), 500


@admin_bp.route("/clubs/<int:club_id>", methods=["PUT"])
def update_club(club_id):
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    club = Club.query.get(club_id)
    if not club:
        return jsonify({"error": "Club non trouvé"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Données requises"}), 400
    
    try:
        # Mettre à jour les informations du club
        if "name" in data:
            club.name = data["name"].strip()
        if "address" in data:
            club.address = data["address"].strip()
        if "phone_number" in data:
            club.phone_number = data["phone_number"].strip()
        if "email" in data:
            club.email = data["email"].strip()
        
        # Trouver et mettre à jour l'utilisateur associé au club
        club_user = User.query.filter_by(club_id=club_id, role=UserRole.CLUB).first()
        if club_user:
            # Mettre à jour les informations de l'utilisateur pour qu'elles correspondent au club
            if "name" in data:
                club_user.name = data["name"].strip()
            if "email" in data:
                club_user.email = data["email"].strip()
            if "phone_number" in data:
                club_user.phone_number = data["phone_number"].strip()
        
        db.session.commit()
        
        return jsonify({
            "message": "Club et utilisateur associé mis à jour avec succès", 
            "club": club.to_dict(),
            "user": club_user.to_dict() if club_user else None
        }), 200
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Un utilisateur avec cet email existe déjà"}), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la mise à jour du club {club_id}: {e}")
        return jsonify({"error": f"Erreur lors de la mise à jour du club: {str(e)}"}), 500


@admin_bp.route("/clubs/<int:club_id>", methods=["DELETE"])
def delete_club(club_id):
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    club = Club.query.get(club_id)
    if not club:
        return jsonify({"error": "Club non trouvé"}), 404
    
    try:
        # Supprimer les terrains associés
        Court.query.filter_by(club_id=club_id).delete()
        # Supprimer les utilisateurs associés
        User.query.filter_by(club_id=club_id).delete()
        
        db.session.delete(club)
        db.session.commit()
        return jsonify({"message": "Club supprimé avec succès"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la suppression du club {club_id}: {e}")
        return jsonify({"error": f"Erreur lors de la suppression du club: {str(e)}"}), 500