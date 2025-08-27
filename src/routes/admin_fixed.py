"""
Routes d'administration corrigées
===============================

Gestion des utilisateurs, clubs, et terrains avec logging approprié
"""

import json
import logging
import uuid
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, session
from sqlalchemy.orm import aliased
from werkzeug.security import generate_password_hash

from src.models.user import (
    db, User, Club, Court, Video, UserRole, 
    ClubActionHistory, RecordingSession
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__)


def require_super_admin():
    """Vérifier les permissions super admin"""
    user_id = session.get("user_id")
    user_role = session.get("user_role")
    
    # Debug logging pour comprendre le problème
    logger.info(
        f"🔍 Vérification admin - user_id: {user_id}, "
        f"user_role: {user_role}"
    )
    logger.info(f"🔍 UserRole.SUPER_ADMIN.value: {UserRole.SUPER_ADMIN.value}")
    
    if not user_id:
        logger.warning("❌ Pas d'user_id dans la session")
        return False
        
    if not user_role:
        logger.warning("❌ Pas de user_role dans la session")
        return False
    
    # Vérification flexible du rôle admin
    admin_roles = [
        UserRole.SUPER_ADMIN.value,
        "SUPER_ADMIN",
        "super_admin",
        "ADMIN",
        "admin"
    ]
    
    if user_role not in admin_roles:
        logger.warning(
            f"❌ Rôle '{user_role}' n'est pas admin. "
            f"Rôles acceptés: {admin_roles}"
        )
        return False
    
    logger.info(
        f"✅ Accès admin accordé pour user_id: {user_id} "
        f"avec rôle: {user_role}"
    )
    return True


def log_club_action(user_id, club_id, action_type, 
                   details=None, performed_by_id=None):
    """Log d'action avec normalisation du type d'action"""
    try:
        if performed_by_id is None:
            performed_by_id = user_id
        
        if not club_id:
            db.session.commit()
            return

        # Normaliser le type d'action avant de l'enregistrer
        normalized_action_type = (
            action_type.lower().strip()
            .replace('-', '_').replace(' ', '_')
        )
        
        # S'assurer que les détails sont en format JSON
        details_json = None
        if details:
            if isinstance(details, dict):
                details_json = json.dumps(details)
            elif isinstance(details, str):
                try:
                    # Vérifier si c'est déjà du JSON valide
                    json.loads(details)
                    details_json = details
                except json.JSONDecodeError:
                    # Si ce n'est pas du JSON, l'envelopper
                    details_json = json.dumps({"raw_details": details})
            else:
                details_json = json.dumps({"raw_details": str(details)})

        history_entry = ClubActionHistory(
            user_id=user_id,
            club_id=club_id,
            action_type=normalized_action_type,
            action_details=details_json,
            performed_by_id=performed_by_id,
            performed_at=datetime.utcnow()
        )
        db.session.add(history_entry)
        db.session.commit()
        
        logger.info(
            f"Action loggée: {normalized_action_type} "
            f"pour utilisateur {user_id} dans club {club_id}"
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de l'enregistrement de l'historique: {e}")
        # Ne pas lever l'exception pour éviter d'interrompre le flux principal


# --- ROUTES DE GESTION DES UTILISATEURS (CRUD COMPLET) ---

@admin_bp.route("/users", methods=["GET"])
def get_all_users():
    """Récupérer tous les utilisateurs"""
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    users = User.query.all()
    return jsonify({"users": [user.to_dict() for user in users]}), 200


@admin_bp.route("/users", methods=["POST"])
def create_user():
    """Créer un nouvel utilisateur"""
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
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
        
        return jsonify({
            "message": "Utilisateur créé", 
            "user": new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur création utilisateur: {e}")
        return jsonify({"error": "Erreur lors de la création"}), 500


@admin_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    """Mettre à jour un utilisateur"""
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    try:
        if "name" in data:
            user.name = data["name"]
        if "phone_number" in data:
            user.phone_number = data["phone_number"]
        if "credits_balance" in data:
            user.credits_balance = data["credits_balance"]
        if "role" in data:
            user.role = UserRole(data["role"])
        
        db.session.commit()
        
        return jsonify({
            "message": "Utilisateur mis à jour", 
            "user": user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur mise à jour utilisateur: {e}")
        return jsonify({"error": "Erreur lors de la mise à jour"}), 500


@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    """Supprimer un utilisateur avec gestion des dépendances"""
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    user = User.query.get_or_404(user_id)
    
    try:
        logger.info(
            f"🗑️ Suppression de l'utilisateur ID: {user_id} - "
            f"{user.name} ({user.email})"
        )
        
        # 1. Gérer les vidéos associées
        videos = Video.query.filter_by(user_id=user_id).all()
        for video in videos:
            video.user_id = None  # Rendre orpheline plutôt que supprimer
            logger.info(f"   📹 Vidéo {video.id} rendue orpheline: user_id -> NULL")
        
        # 2. Gérer les sessions d'enregistrement
        recording_sessions = RecordingSession.query.filter_by(
            user_id=user_id
        ).all()
        for rec_session in recording_sessions:
            logger.info(f"   🎬 Suppression session: {rec_session.recording_id}")
            db.session.delete(rec_session)
        
        # 3. Gérer l'historique des actions
        history_entries = ClubActionHistory.query.filter_by(
            user_id=user_id
        ).all()
        for entry in history_entries:
            entry.user_id = None  # Garder l'historique mais anonymiser
            logger.info(f"   📝 Historique {entry.id} anonymisé: user_id -> NULL")
        
        # 4. Gérer l'historique où l'utilisateur était le performeur
        performed_entries = ClubActionHistory.query.filter_by(
            performed_by_id=user_id
        ).all()
        for entry in performed_entries:
            entry.performed_by_id = None
            logger.info(
                f"   📝 Historique {entry.id} anonymisé: performed_by_id -> NULL"
            )
        
        # 5. Si c'est un utilisateur club, gérer les relations club
        if user.role == UserRole.CLUB and user.club_id:
            club = Club.query.get(user.club_id)
            if club:
                logger.info(f"   🏢 Utilisateur club détecté pour: {club.name}")
                # Optionnel: supprimer le club aussi ou le laisser orphelin
                # Pour l'instant, on le laisse orphelin
        
        # 6. Gérer les relations many-to-many (follows)
        if hasattr(user, 'followed_clubs'):
            # Pour les relations many-to-many, 
            # il faut supprimer les relations explicitement
            user.followed_clubs = []  # Vider la relation
            logger.info("   🔗 Relations de suivi supprimées")
        
        # 7. Supprimer l'utilisateur lui-même
        logger.info(f"   👤 Suppression de l'utilisateur: {user.name}")
        db.session.delete(user)
        
        db.session.commit()
        
        return jsonify({
            "message": "Utilisateur supprimé avec succès",
            "videos_orphaned": len(videos),
            "recording_sessions_deleted": len(recording_sessions),
            "history_entries_anonymized": (
                len(history_entries) + len(performed_entries)
            )
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Erreur lors de la suppression de l'utilisateur {user_id}: {e}")
        return jsonify({
            "error": f"Erreur lors de la suppression: {str(e)}"
        }), 500


@admin_bp.route("/users/<int:user_id>/credits", methods=["POST"])
def add_credits(user_id):
    """Ajouter des crédits à un utilisateur"""
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    credits_to_add = data.get("credits", 0)
    
    if not isinstance(credits_to_add, int) or credits_to_add <= 0:
        return jsonify({
            "error": "Le nombre de crédits doit être un entier positif"
        }), 400

    try:
        old_balance = user.credits_balance
        user.credits_balance += credits_to_add
        
        log_club_action(
            user_id=user.id, 
            club_id=user.club_id,
            action_type='add_credits', 
            details={
                'credits_added': credits_to_add, 
                'old_balance': old_balance, 
                'new_balance': user.credits_balance
            }, 
            performed_by_id=session.get('user_id')
        )
        
        return jsonify({
            "message": "Crédits ajoutés", 
            "user": user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de l'ajout de crédits: {e}")
        return jsonify({"error": "Erreur lors de l'ajout de crédits"}), 500


# --- ROUTES DE GESTION DES CLUBS (CRUD COMPLET) ---

@admin_bp.route("/clubs", methods=["GET"])
def get_all_clubs():
    """Récupérer tous les clubs"""
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    clubs = Club.query.all()
    return jsonify({"clubs": [club.to_dict() for club in clubs]}), 200


@admin_bp.route("/clubs", methods=["POST"])
def create_club():
    """Créer un nouveau club"""
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    data = request.get_json()
    try:
        new_club = Club(
            name=data["name"], 
            email=data["email"], 
            address=data.get("address"), 
            phone_number=data.get("phone_number")
        )
        db.session.add(new_club)
        db.session.flush()
        
        club_user = User(
            email=data["email"], 
            name=data["name"], 
            role=UserRole.CLUB, 
            club_id=new_club.id
        )
        if data.get("password"):
            club_user.password_hash = generate_password_hash(data["password"])
        
        db.session.add(club_user)
        db.session.commit()
        
        return jsonify({
            "message": "Club créé", 
            "club": new_club.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur création club: {e}")
        return jsonify({"error": "Erreur lors de la création"}), 500
