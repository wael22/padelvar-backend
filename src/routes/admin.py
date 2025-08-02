# padelvar-backend/src/routes/admin.py

from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, Club, Court, Video, UserRole, ClubActionHistory, RecordingSession
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import aliased, joinedload
import uuid
import logging
import json
import random
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__)

# --- Fonctions Utilitaires ---

def require_super_admin():
    user_id = session.get("user_id")
    user_role = session.get("user_role")
    
    # Debug logging pour comprendre le problème
    logger.info(f"🔍 Vérification admin - user_id: {user_id}, user_role: {user_role}")
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
        logger.warning(f"❌ Rôle '{user_role}' n'est pas admin. Rôles acceptés: {admin_roles}")
        return False
    
    logger.info(f"✅ Accès admin accordé pour user_id: {user_id} avec rôle: {user_role}")
    return True

def log_club_action(user_id, club_id, action_type, details=None, performed_by_id=None):
    """Log d'action avec normalisation du type d'action"""
    try:
        if performed_by_id is None:
            performed_by_id = user_id
        
        if not club_id:
            db.session.commit()
            return

        # Normaliser le type d'action avant de l'enregistrer
        normalized_action_type = action_type.lower().strip().replace('-', '_').replace(' ', '_')
        
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
        
        logger.info(f"Action loggée: {normalized_action_type} pour utilisateur {user_id} dans club {club_id}")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de l'enregistrement de l'historique: {e}")
        # Ne pas lever l'exception pour éviter d'interrompre le flux principal

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
        print(f"🗑️ Suppression de l'utilisateur ID: {user_id} - {user.name} ({user.email})")
        
        # 1. Gérer les vidéos associées
        videos = Video.query.filter_by(user_id=user_id).all()
        for video in videos:
            video.user_id = None  # Rendre orpheline plutôt que supprimer
            print(f"   📹 Vidéo {video.id} rendue orpheline: user_id -> NULL")
        
        # 2. Gérer les sessions d'enregistrement
        recording_sessions = RecordingSession.query.filter_by(user_id=user_id).all()
        for session in recording_sessions:
            print(f"   🎬 Suppression session: {session.recording_id}")
            db.session.delete(session)
        
        # 3. Gérer l'historique des actions
        history_entries = ClubActionHistory.query.filter_by(user_id=user_id).all()
        for entry in history_entries:
            entry.user_id = None  # Garder l'historique mais anonymiser
            print(f"   📝 Historique {entry.id} anonymisé: user_id -> NULL")
        
        # 4. Gérer l'historique où l'utilisateur était le performeur
        performed_entries = ClubActionHistory.query.filter_by(performed_by_id=user_id).all()
        for entry in performed_entries:
            entry.performed_by_id = None
            print(f"   📝 Historique {entry.id} anonymisé: performed_by_id -> NULL")
        
        # 5. Si c'est un utilisateur club, gérer les relations club
        if user.role == UserRole.CLUB and user.club_id:
            club = Club.query.get(user.club_id)
            if club:
                print(f"   🏢 Utilisateur club détecté pour: {club.name}")
                # Optionnel: supprimer le club aussi ou le laisser orphelin
                # Pour l'instant, on le laisse orphelin
        
        # 6. Gérer les relations many-to-many (follows)
        if hasattr(user, 'followed_clubs'):
            # Pour les relations many-to-many, il faut supprimer les relations explicitement
            user.followed_clubs = []  # Vider la relation
            print(f"   🔗 Relations de suivi supprimées")
        
        # 7. Supprimer l'utilisateur lui-même
        print(f"   👤 Suppression de l'utilisateur: {user.name}")
        db.session.delete(user)
        
        db.session.commit()
        
        return jsonify({
            "message": "Utilisateur supprimé avec succès",
            "videos_orphaned": len(videos),
            "recording_sessions_deleted": len(recording_sessions),
            "history_entries_anonymized": len(history_entries) + len(performed_entries)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erreur lors de la suppression de l'utilisateur {user_id}: {e}")
        logger.error(f"Erreur lors de la suppression de l'utilisateur {user_id}: {e}")
        return jsonify({"error": f"Erreur lors de la suppression: {str(e)}"}), 500

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


# ====================================================================
# CORRECTION DE LA SYNCHRONISATION (ADMIN -> CLUB)
# ====================================================================

@admin_bp.route("/sync/club-user-data", methods=["POST"])
def sync_club_user_data():
    """Synchroniser les données entre les clubs et leurs utilisateurs associés"""
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        logger.info("Début de la synchronisation club-utilisateur")
        
        # Récupérer tous les clubs avec leurs utilisateurs associés
        clubs = Club.query.all()
        sync_results = {
            'clubs_processed': 0,
            'sync_corrections': 0,
            'errors': [],
            'details': []
        }
        
        for club in clubs:
            sync_results['clubs_processed'] += 1
            club_user = User.query.filter_by(club_id=club.id, role=UserRole.CLUB).first()
            
            if club_user:
                corrections_needed = []
                
                # Vérifier les divergences
                if club.name != club_user.name:
                    corrections_needed.append(f"Nom: '{club_user.name}' → '{club.name}'")
                    club_user.name = club.name
                
                if club.email != club_user.email:
                    corrections_needed.append(f"Email: '{club_user.email}' → '{club.email}'")
                    club_user.email = club.email
                
                if club.phone_number != club_user.phone_number:
                    corrections_needed.append(f"Téléphone: '{club_user.phone_number}' → '{club.phone_number}'")
                    club_user.phone_number = club.phone_number
                
                if corrections_needed:
                    sync_results['sync_corrections'] += 1
                    sync_results['details'].append({
                        'club_id': club.id,
                        'club_name': club.name,
                        'corrections': corrections_needed
                    })
                    logger.info(f"Synchronisation club {club.id}: {corrections_needed}")
                    
            else:
                # Club sans utilisateur associé - créer l'utilisateur
                try:
                    from werkzeug.security import generate_password_hash
                    new_club_user = User(
                        email=club.email,
                        password_hash=generate_password_hash('default123'),  # Mot de passe temporaire
                        name=club.name,
                        role=UserRole.CLUB,
                        club_id=club.id,
                        phone_number=club.phone_number,
                        credits_balance=0
                    )
                    db.session.add(new_club_user)
                    sync_results['details'].append({
                        'club_id': club.id,
                        'club_name': club.name,
                        'corrections': ['Utilisateur créé - mot de passe: default123']
                    })
                    logger.info(f"Utilisateur créé pour le club {club.id}")
                except Exception as e:
                    sync_results['errors'].append(f"Erreur création utilisateur club {club.id}: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'message': 'Synchronisation terminée',
            'results': sync_results
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la synchronisation: {e}")
        return jsonify({'error': f'Erreur synchronisation: {str(e)}'}), 500

@admin_bp.route("/clubs/<int:club_id>", methods=["PUT"])
def update_club(club_id):
    if not require_super_admin(): 
        return jsonify({"error": "Accès non autorisé"}), 403
    
    club = Club.query.get_or_404(club_id)
    # On trouve l'utilisateur associé à ce club
    club_user = User.query.filter_by(club_id=club_id, role=UserRole.CLUB).first()
    
    data = request.get_json()
    
    try:
        # Mettre à jour l'objet Club
        if "name" in data: 
            club.name = data["name"].strip()
        if "address" in data: 
            club.address = data["address"]
        if "phone_number" in data: 
            club.phone_number = data["phone_number"]
        if "email" in data: 
            club.email = data["email"].strip()
        
        # SYNCHRONISATION BIDIRECTIONNELLE: Mettre à jour l'utilisateur associé
        if club_user:
            if "name" in data:
                club_user.name = club.name
            if "email" in data:
                club_user.email = club.email  
            if "phone_number" in data:
                club_user.phone_number = club.phone_number
                
            logger.info(f"Synchronisation admin→club: Club {club_id} et utilisateur {club_user.id} mis à jour")
        else:
            logger.warning(f"Aucun utilisateur associé trouvé pour le club {club_id}")
        
        db.session.commit()
        
        # Log de l'action pour traçabilité
        log_club_action(
            user_id=club_user.id if club_user else None,
            club_id=club_id,
            action_type='admin_update_club',
            details={
                'updated_fields': list(data.keys()),
                'admin_user_id': session.get('user_id'),
                'sync_user_updated': club_user is not None
            },
            performed_by_id=session.get('user_id')
        )
        
        return jsonify({
            "message": "Club mis à jour avec succès", 
            "club": club.to_dict(),
            "user_synchronized": club_user is not None
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la mise à jour du club par l'admin: {e}")
        return jsonify({"error": "Erreur lors de la mise à jour"}), 500

@admin_bp.route("/clubs/<int:club_id>", methods=["DELETE"])
def delete_club(club_id):
    if not require_super_admin(): return jsonify({"error": "Accès non autorisé"}), 403
    club = Club.query.get_or_404(club_id)
    try:
        # Importer les modèles nécessaires
        from src.models.user import Video, RecordingSession, ClubActionHistory
        
        print(f"🗑️ Suppression du club ID: {club_id} - {club.name}")
        
        # 1. Gérer les terrains et leurs contraintes
        courts = Court.query.filter_by(club_id=club_id).all()
        videos_orphaned = 0
        recording_sessions_deleted = 0
        
        for court in courts:
            print(f"   🏟️ Traitement du terrain: {court.name}")
            
            # Gérer les vidéos de ce terrain
            court_videos = Video.query.filter_by(court_id=court.id).all()
            for video in court_videos:
                video.court_id = None
                videos_orphaned += 1
                print(f"     📹 Vidéo {video.id} rendue orpheline")
            
            # Gérer les sessions d'enregistrement de ce terrain
            court_sessions = RecordingSession.query.filter_by(court_id=court.id).all()
            for session in court_sessions:
                print(f"     🎬 Suppression session: {session.recording_id}")
                db.session.delete(session)
                recording_sessions_deleted += 1
        
        # 2. Supprimer tous les terrains du club
        Court.query.filter_by(club_id=club_id).delete()
        print(f"   🏟️ {len(courts)} terrain(s) supprimé(s)")
        
        # 3. Gérer les utilisateurs du club
        club_users = User.query.filter_by(club_id=club_id).all()
        for user in club_users:
            print(f"   👤 Traitement utilisateur: {user.name} ({user.role.value})")
            
            # Gérer les vidéos de cet utilisateur (les rendre orphelines)
            user_videos = Video.query.filter_by(user_id=user.id).all()
            for video in user_videos:
                if video.user_id == user.id:  # Éviter les doublons
                    video.user_id = None
                    print(f"     📹 Vidéo {video.id} rendue orpheline")
            
            # Gérer les sessions d'enregistrement de cet utilisateur
            user_sessions = RecordingSession.query.filter_by(user_id=user.id).all()
            for session in user_sessions:
                if session not in [s for s in RecordingSession.query.filter_by(court_id=None).all()]:
                    print(f"     🎬 Suppression session utilisateur: {session.recording_id}")
                    db.session.delete(session)
            
            # Gérer les relations many-to-many (follows)
            if hasattr(user, 'followed_clubs'):
                user.followed_clubs = []
        
        # 4. Gérer l'historique du club
        history_entries = ClubActionHistory.query.filter_by(club_id=club_id).all()
        for entry in history_entries:
            entry.club_id = None  # Anonymiser plutôt que supprimer
            print(f"   📝 Historique {entry.id} anonymisé")
        
        # 5. Supprimer les utilisateurs du club
        User.query.filter_by(club_id=club_id).delete()
        print(f"   👤 {len(club_users)} utilisateur(s) supprimé(s)")
        
        # 6. Gérer les relations many-to-many avec les followers
        if hasattr(club, 'followers'):
            # Supprimer toutes les relations de suivi de ce club
            club.followers = []
            print(f"   🔗 Relations de suivi du club supprimées")
        
        # 7. Supprimer le club lui-même
        print(f"   🏢 Suppression du club: {club.name}")
        db.session.delete(club)
        
        db.session.commit()
        
        return jsonify({
            "message": "Club supprimé avec succès",
            "courts_deleted": len(courts),
            "users_deleted": len(club_users),
            "videos_orphaned": videos_orphaned,
            "recording_sessions_deleted": recording_sessions_deleted,
            "history_entries_anonymized": len(history_entries)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erreur lors de la suppression du club {club_id}: {e}")
        logger.error(f"Erreur lors de la suppression du club {club_id}: {e}")
        return jsonify({"error": f"Erreur lors de la suppression: {str(e)}"}), 500

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
        print(f"🗑️ Suppression du terrain ID: {court_id} - {court.name}")
        
        # 1. Gérer les vidéos associées (les déplacer vers NULL)
        videos = Video.query.filter_by(court_id=court_id).all()
        for video in videos:
            video.court_id = None
            print(f"   📹 Vidéo {video.id} déplacée: court_id -> NULL")
        
        # 2. Gérer les sessions d'enregistrement (les supprimer ou les marquer)
        recording_sessions = RecordingSession.query.filter_by(court_id=court_id).all()
        for session in recording_sessions:
            print(f"   🎬 Suppression session: {session.recording_id} (statut: {session.status})")
            db.session.delete(session)
        
        # 3. Supprimer le terrain lui-même
        print(f"   🏟️ Suppression du terrain: {court.name}")
        db.session.delete(court)
        
        db.session.commit()
        
        return jsonify({
            "message": "Terrain supprimé avec succès",
            "videos_updated": len(videos),
            "recording_sessions_deleted": len(recording_sessions)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erreur lors de la suppression du terrain {court_id}: {e}")
        return jsonify({"error": f"Erreur lors de la suppression: {str(e)}"}), 500

# --- ROUTES VIDÉOS & HISTORIQUE ---

@admin_bp.route("/videos", methods=["GET"])
def get_all_clubs_videos():
    if not require_super_admin(): 
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        # Requête simplifiée sans les colonnes problématiques
        videos = db.session.query(Video).all()

        videos_data = []
        for video in videos:
            video_dict = {
                "id": video.id,
                "title": video.title,
                "description": video.description,
                "file_url": video.file_url,
                "thumbnail_url": video.thumbnail_url,
                "duration": getattr(video, 'duration', None),
                "file_size": getattr(video, 'file_size', None),
                "is_unlocked": getattr(video, 'is_unlocked', True),
                "credits_cost": getattr(video, 'credits_cost', 1),
                "recorded_at": video.recorded_at.isoformat() if video.recorded_at else None,
                "created_at": video.created_at.isoformat() if video.created_at else None,
                "user_id": video.user_id,
                "court_id": video.court_id
            }
            
            # Ajouter les informations relationnelles
            if hasattr(video, 'owner') and video.owner:
                video_dict['player_name'] = video.owner.name
            else:
                # Requête manuelle si la relation ne fonctionne pas
                user = User.query.get(video.user_id)
                video_dict['player_name'] = user.name if user else "Utilisateur supprimé"
            
            if hasattr(video, 'court') and video.court:
                video_dict['court_name'] = video.court.name
                if hasattr(video.court, 'club') and video.court.club:
                    video_dict['club_name'] = video.court.club.name
                else:
                    club = Club.query.get(video.court.club_id)
                    video_dict['club_name'] = club.name if club else "Club inconnu"
            else:
                # Requête manuelle si la relation ne fonctionne pas
                court = Court.query.get(video.court_id)
                if court:
                    video_dict['court_name'] = court.name
                    club = Club.query.get(court.club_id)
                    video_dict['club_name'] = club.name if club else "Club inconnu"
                else:
                    video_dict['court_name'] = "Terrain inconnu"
                    video_dict['club_name'] = "Club inconnu"
            
            videos_data.append(video_dict)
        
        return jsonify({"videos": videos_data}), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des vidéos: {e}")
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500

# ====================================================================
# CORRECTION MAJEURE ICI
# ====================================================================
def normalize_action_type(action_type):
    """Normalise et traduit les types d'actions pour l'affichage"""
    action_mapping = {
        'add_credits': 'Ajout de crédits',
        'buy_credits': 'Achat de crédits',
        'purchase_credits': 'Achat de crédits',
        'credit_purchase': 'Achat de crédits',
        'unlock_video': 'Déblocage vidéo',
        'follow_club': 'Suivi de club',
        'unfollow_club': 'Arrêt suivi club',
        'update_profile': 'Mise à jour profil',
        'create_user': 'Création utilisateur',
        'update_user': 'Modification utilisateur',
        'delete_user': 'Suppression utilisateur',
        'create_club': 'Création club',
        'update_club': 'Modification club',
        'delete_club': 'Suppression club',
        'create_court': 'Création terrain',
        'update_court': 'Modification terrain',
        'delete_court': 'Suppression terrain',
        'video_upload': 'Upload vidéo',
        'video_delete': 'Suppression vidéo',
        'login': 'Connexion',
        'logout': 'Déconnexion',
        'registration': 'Inscription',
        'password_change': 'Changement mot de passe',
        'payment_simulation': 'Simulation de paiement',
        'payment_konnect': 'Paiement Konnect',
        'payment_flouci': 'Paiement Flouci',
        'payment_card': 'Paiement carte bancaire',
        'unknown_action': 'Action inconnue'
    }
    
    if not action_type or action_type.strip() == '':
        return 'Action non spécifiée'
    
    # Nettoyer le type d'action
    clean_action = str(action_type).strip().lower()
    
    # Retourner la traduction ou le type original si non trouvé
    return action_mapping.get(clean_action, f'Action: {action_type}')

def parse_action_details(action_details_str):
    """Parse et nettoie les détails d'action"""
    if not action_details_str:
        return {}
    
    try:
        if isinstance(action_details_str, str):
            return json.loads(action_details_str)
        elif isinstance(action_details_str, dict):
            return action_details_str
        else:
            return {"raw_details": str(action_details_str)}
    except json.JSONDecodeError:
        return {"raw_details": str(action_details_str)}
    except Exception:
        return {}

@admin_bp.route("/clubs/history/all", methods=["GET"])
def get_all_clubs_history():
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    try:
        # Créer des alias pour joindre la table User deux fois
        Player = aliased(User, name='player')
        Performer = aliased(User, name='performer')

        # Requête unique avec des jointures externes (outerjoin) pour plus de robustesse
        history_query = (
            db.session.query(
                ClubActionHistory,
                Player.name.label('player_name'),
                Club.name.label('club_name'),
                Performer.name.label('performed_by_name')
            )
            .outerjoin(Player, ClubActionHistory.user_id == Player.id)
            .outerjoin(Performer, ClubActionHistory.performed_by_id == Performer.id)
            .outerjoin(Club, ClubActionHistory.club_id == Club.id)
            .order_by(ClubActionHistory.performed_at.desc())
            .limit(100)  # Limiter à 100 entrées pour les performances
            .all()
        )

        history_data = []
        for entry, player_name, club_name, performed_by_name in history_query:
            # Normaliser le type d'action
            normalized_action = normalize_action_type(entry.action_type)
            
            # Parser les détails d'action
            parsed_details = parse_action_details(entry.action_details)
            
            # Créer un résumé lisible de l'action
            action_summary = create_action_summary(normalized_action, parsed_details)
            
            history_data.append({
                "id": entry.id,
                "user_id": entry.user_id,
                "club_id": entry.club_id,
                "player_name": player_name or "Utilisateur supprimé",
                "club_name": club_name or "Club non spécifié",
                "action_type": normalized_action,
                "action_type_raw": entry.action_type,  # Garder l'original pour debug
                "action_details": entry.action_details,
                "action_summary": action_summary,
                "parsed_details": parsed_details,
                "performed_at": entry.performed_at.isoformat() if entry.performed_at else datetime.utcnow().isoformat(),
                "performed_by_id": entry.performed_by_id,
                "performed_by_name": performed_by_name or "Auteur inconnu"
            })
            
        return jsonify({
            "history": history_data,
            "total_count": len(history_data),
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'historique global: {e}")
        return jsonify({"error": "Erreur serveur"}), 500

def create_action_summary(action_type, details):
    """Crée un résumé lisible de l'action"""
    try:
        if 'crédits' in action_type.lower():
            if 'achat' in action_type.lower():
                # Pour les achats de crédits
                credits = details.get('credits_purchased') or details.get('credits_amount') or details.get('credits_involved', 'N/A')
                price = details.get('price_dt') or details.get('price_paid_dt')
                payment_method = details.get('payment_method', '')
                
                if price and payment_method:
                    return f"{action_type} - {credits} crédit(s) pour {price} DT via {payment_method}"
                elif price:
                    return f"{action_type} - {credits} crédit(s) pour {price} DT"
                else:
                    return f"{action_type} - {credits} crédit(s)"
            else:
                # Pour les ajouts de crédits (par admin)
                credits = details.get('credits_added') or details.get('credits_purchased') or details.get('credits_involved', 'N/A')
                return f"{action_type} - {credits} crédit(s)"
        elif 'suivi' in action_type.lower():
            club_name = details.get('club_name', 'Club inconnu')
            return f"{action_type} - {club_name}"
        elif 'vidéo' in action_type.lower():
            video_title = details.get('video_title') or details.get('title', 'Vidéo sans titre')
            return f"{action_type} - {video_title}"
        elif 'profil' in action_type.lower():
            fields = details.get('updated_fields', [])
            if fields:
                return f"{action_type} - Champs: {', '.join(fields)}"
            return action_type
        elif 'paiement' in action_type.lower():
            amount = details.get('amount') or details.get('price_dt') or details.get('total')
            method = details.get('method') or details.get('payment_method', '')
            if amount and method:
                return f"{action_type} - {amount} DT via {method}"
            elif amount:
                return f"{action_type} - {amount} DT"
            else:
                return action_type
        else:
            # Pour les autres actions, essayer d'extraire des informations utiles
            if details:
                key_info = []
                for key in ['name', 'email', 'amount', 'status', 'player_name', 'club_name']:
                    if key in details and details[key]:
                        key_info.append(f"{key}: {details[key]}")
                if key_info:
                    return f"{action_type} - {', '.join(key_info[:2])}"  # Limiter à 2 infos
            return action_type
    except Exception:
        return action_type

# --- ROUTES DE STATISTIQUES AVANCÉES ---

@admin_bp.route("/dashboard", methods=["GET"])
def get_admin_dashboard():
    """Dashboard complet pour l'administrateur avec toutes les statistiques"""
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        logger.info("Récupération du tableau de bord administrateur")
        
        # 1. Statistiques générales des utilisateurs
        total_users = User.query.count()
        total_players = User.query.filter_by(role=UserRole.PLAYER).count()
        total_clubs = User.query.filter_by(role=UserRole.CLUB).count()
        total_admins = User.query.filter_by(role=UserRole.SUPER_ADMIN).count()
        
        logger.info(f"Utilisateurs: {total_users} (Joueurs: {total_players}, Clubs: {total_clubs}, Admins: {total_admins})")
        
        # 2. Statistiques des clubs
        clubs_count = Club.query.count()
        total_courts = Court.query.count()
        total_videos = Video.query.count()
        
        # 3. Statistiques des crédits
        total_credits_in_system = db.session.query(db.func.sum(User.credits_balance)).scalar() or 0
        
        # 4. Dernières activités
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        recent_clubs = Club.query.order_by(Club.created_at.desc()).limit(5).all()
        recent_videos = Video.query.order_by(Video.recorded_at.desc()).limit(10).all()
        
        # 5. Statistiques par club
        clubs_stats = []
        for club in Club.query.all():
            club_players = User.query.filter_by(club_id=club.id, role=UserRole.PLAYER).count()
            club_courts = Court.query.filter_by(club_id=club.id).count()
            club_videos = db.session.query(Video).join(Court).filter(Court.club_id == club.id).count()
            club_followers = len(club.followers.all()) if hasattr(club, 'followers') else 0
            
            clubs_stats.append({
                'club': club.to_dict(),
                'players_count': club_players,
                'courts_count': club_courts,
                'videos_count': club_videos,
                'followers_count': club_followers
            })
        
        # 6. Activité récente par type
        activity_stats = {}
        recent_history = ClubActionHistory.query.order_by(ClubActionHistory.performed_at.desc()).limit(50).all()
        for entry in recent_history:
            action_type = entry.action_type
            activity_stats[action_type] = activity_stats.get(action_type, 0) + 1
        
        dashboard_data = {
            'overview': {
                'total_users': total_users,
                'total_players': total_players,
                'total_clubs_users': total_clubs,
                'total_admins': total_admins,
                'total_clubs': clubs_count,
                'total_courts': total_courts,
                'total_videos': total_videos,
                'total_credits_in_system': total_credits_in_system
            },
            'recent_activity': {
                'users': [user.to_dict() for user in recent_users],
                'clubs': [club.to_dict() for club in recent_clubs],
                'videos': [video.to_dict() for video in recent_videos],
                'activity_breakdown': activity_stats
            },
            'clubs_statistics': clubs_stats,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(dashboard_data), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du dashboard admin: {e}")
        return jsonify({"error": "Erreur lors de la récupération du dashboard"}), 500

@admin_bp.route("/statistics/users", methods=["GET"])
def get_users_statistics():
    """Statistiques détaillées sur les utilisateurs"""
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        # Statistiques par rôle
        users_by_role = {}
        for role in UserRole:
            count = User.query.filter_by(role=role).count()
            users_by_role[role.value] = count
        
        # Utilisateurs par club
        users_by_club = []
        for club in Club.query.all():
            club_users = User.query.filter_by(club_id=club.id).count()
            users_by_club.append({
                'club_name': club.name,
                'club_id': club.id,
                'users_count': club_users
            })
        
        # Répartition des crédits
        credits_stats = {
            'total_credits': db.session.query(db.func.sum(User.credits_balance)).scalar() or 0,
            'average_credits': db.session.query(db.func.avg(User.credits_balance)).scalar() or 0,
            'users_with_credits': User.query.filter(User.credits_balance > 0).count(),
            'users_without_credits': User.query.filter(User.credits_balance == 0).count()
        }
        
        # Utilisateurs récents (dernière semaine)
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_users_this_week = User.query.filter(User.created_at >= week_ago).count()
        
        return jsonify({
            'users_by_role': users_by_role,
            'users_by_club': users_by_club,
            'credits_statistics': credits_stats,
            'new_users_this_week': new_users_this_week,
            'total_users': User.query.count()
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques utilisateurs: {e}")
        return jsonify({"error": "Erreur serveur"}), 500

@admin_bp.route("/statistics/clubs", methods=["GET"])
def get_clubs_statistics():
    """Statistiques détaillées sur les clubs"""
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        clubs_detailed_stats = []
        
        for club in Club.query.all():
            # Compter les éléments associés
            players_count = User.query.filter_by(club_id=club.id, role=UserRole.PLAYER).count()
            courts_count = Court.query.filter_by(club_id=club.id).count()
            
            # Compter les vidéos
            videos_count = db.session.query(Video).join(Court).filter(Court.club_id == club.id).count()
            
            # Compter les followers
            followers_count = 0
            try:
                followers_count = len(club.followers.all())
            except:
                followers_count = 0
            
            # Calculer les crédits distribués
            credits_distributed = 0
            try:
                credit_entries = ClubActionHistory.query.filter_by(
                    club_id=club.id,
                    action_type='add_credits'
                ).all()
                
                for entry in credit_entries:
                    try:
                        if entry.action_details:
                            details = json.loads(entry.action_details)
                            credits_added = details.get('credits_added', 0)
                            if isinstance(credits_added, (int, float)):
                                credits_distributed += int(credits_added)
                    except:
                        pass
            except:
                credits_distributed = 0
            
            # Activité récente du club
            recent_activity_count = ClubActionHistory.query.filter_by(club_id=club.id).filter(
                ClubActionHistory.performed_at >= datetime.utcnow() - timedelta(days=30)
            ).count()
            
            clubs_detailed_stats.append({
                'club': club.to_dict(),
                'statistics': {
                    'players_count': players_count,
                    'courts_count': courts_count,
                    'videos_count': videos_count,
                    'followers_count': followers_count,
                    'credits_distributed': credits_distributed,
                    'recent_activity_count': recent_activity_count
                }
            })
        
        # Statistiques globales
        total_clubs = len(clubs_detailed_stats)
        active_clubs = len([c for c in clubs_detailed_stats if c['statistics']['recent_activity_count'] > 0])
        
        return jsonify({
            'clubs_detailed_statistics': clubs_detailed_stats,
            'global_statistics': {
                'total_clubs': total_clubs,
                'active_clubs_last_30_days': active_clubs,
                'average_players_per_club': sum(c['statistics']['players_count'] for c in clubs_detailed_stats) / total_clubs if total_clubs > 0 else 0,
                'average_courts_per_club': sum(c['statistics']['courts_count'] for c in clubs_detailed_stats) / total_clubs if total_clubs > 0 else 0
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques clubs: {e}")
        return jsonify({"error": "Erreur serveur"}), 500

@admin_bp.route("/clubs/history/cleanup", methods=["POST"])
def cleanup_history_actions():
    """Nettoie et corrige les actions incorrectes dans l'historique"""
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        logger.info("Début du nettoyage de l'historique des actions")
        
        # Récupérer toutes les entrées d'historique
        all_entries = ClubActionHistory.query.all()
        
        corrections_made = 0
        invalid_entries_found = 0
        
        for entry in all_entries:
            original_action_type = entry.action_type
            needs_update = False
            
            # Nettoyer les types d'actions invalides ou malformés
            if not entry.action_type or entry.action_type.strip() == '':
                entry.action_type = 'unknown_action'
                needs_update = True
                invalid_entries_found += 1
            elif entry.action_type.strip() != entry.action_type:
                entry.action_type = entry.action_type.strip()
                needs_update = True
            
            # Corriger les types d'actions malformés courants
            action_corrections = {
                'addcredits': 'add_credits',
                'add_credit': 'add_credits',
                'buycredits': 'buy_credits',
                'buy_credit': 'buy_credits',
                'purchasecredits': 'buy_credits',
                'purchase_credit': 'buy_credits',
                'creditpurchase': 'buy_credits',
                'credit_buy': 'buy_credits',
                'achatcredits': 'buy_credits',
                'achat_credits': 'buy_credits',
                'unlookvideo': 'unlock_video',
                'unlock_videos': 'unlock_video',
                'followclub': 'follow_club',
                'follow_clubs': 'follow_club',
                'unfollowclub': 'unfollow_club',
                'unfollow_clubs': 'unfollow_club',
                'updateprofile': 'update_profile',
                'update_profiles': 'update_profile',
                'createuser': 'create_user',
                'create_users': 'create_user',
                'updateuser': 'update_user',
                'update_users': 'update_user',
                'deleteuser': 'delete_user',
                'delete_users': 'delete_user',
                'paymentkonnect': 'payment_konnect',
                'payment_via_konnect': 'payment_konnect',
                'paymentflouci': 'payment_flouci',
                'payment_via_flouci': 'payment_flouci',
                'paymentcard': 'payment_card',
                'payment_via_card': 'payment_card',
                'carte_bancaire': 'payment_card'
            }
            
            clean_action = entry.action_type.lower().replace('-', '_').replace(' ', '_')
            if clean_action in action_corrections:
                entry.action_type = action_corrections[clean_action]
                needs_update = True
            
            # Vérifier et corriger les détails d'action
            if entry.action_details:
                try:
                    if isinstance(entry.action_details, str):
                        # Vérifier si c'est du JSON valide
                        json.loads(entry.action_details)
                except json.JSONDecodeError:
                    # Si ce n'est pas du JSON valide, l'envelopper
                    entry.action_details = json.dumps({"raw_details": entry.action_details})
                    needs_update = True
            
            # Vérifier les dates
            if not entry.performed_at:
                entry.performed_at = datetime.utcnow()
                needs_update = True
            
            if needs_update:
                corrections_made += 1
                logger.info(f"Correction de l'entrée {entry.id}: {original_action_type} -> {entry.action_type}")
        
        # Sauvegarder les changements
        db.session.commit()
        
        # Statistiques des types d'actions après nettoyage
        action_type_stats = {}
        for entry in ClubActionHistory.query.all():
            action_type = entry.action_type
            action_type_stats[action_type] = action_type_stats.get(action_type, 0) + 1
        
        return jsonify({
            "message": "Nettoyage de l'historique terminé avec succès",
            "corrections_made": corrections_made,
            "invalid_entries_found": invalid_entries_found,
            "total_entries": len(all_entries),
            "action_type_distribution": action_type_stats,
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors du nettoyage de l'historique: {e}")
        return jsonify({"error": f"Erreur lors du nettoyage: {str(e)}"}), 500

@admin_bp.route("/clubs/history/statistics", methods=["GET"])
def get_history_statistics():
    """Statistiques détaillées sur l'historique des actions"""
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        # Statistiques par type d'action
        action_type_stats = {}
        all_entries = ClubActionHistory.query.all()
        
        for entry in all_entries:
            action_type = normalize_action_type(entry.action_type)
            action_type_stats[action_type] = action_type_stats.get(action_type, 0) + 1
        
        # Statistiques par mois
        monthly_stats = {}
        for entry in all_entries:
            if entry.performed_at:
                month_key = entry.performed_at.strftime("%Y-%m")
                monthly_stats[month_key] = monthly_stats.get(month_key, 0) + 1
        
        # Statistiques par club
        club_stats = {}
        for entry in all_entries:
            if entry.club_id:
                club = Club.query.get(entry.club_id)
                club_name = club.name if club else f"Club {entry.club_id}"
                club_stats[club_name] = club_stats.get(club_name, 0) + 1
        
        # Actions récentes (dernières 24h)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_actions = ClubActionHistory.query.filter(
            ClubActionHistory.performed_at >= yesterday
        ).count()
        
        return jsonify({
            "action_type_statistics": action_type_stats,
            "monthly_statistics": monthly_stats,
            "club_statistics": club_stats,
            "recent_actions_24h": recent_actions,
            "total_actions": len(all_entries),
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques d'historique: {e}")
        return jsonify({"error": "Erreur serveur"}), 500

# --- ROUTES DE DIAGNOSTIC ET DEBUG ---

@admin_bp.route("/debug/fix-unknown-actions", methods=["POST"])
def fix_unknown_actions():
    """Fix immediate des actions inconnues dans l'historique"""
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        logger.info("Début de la correction des actions inconnues")
        
        # Récupérer toutes les entrées avec des actions potentiellement problématiques
        all_entries = ClubActionHistory.query.all()
        
        fixed_count = 0
        entries_updated = []
        
        for entry in all_entries:
            original_action = entry.action_type
            
            # Identifier les actions qui apparaissent comme "inconnues"
            normalized = normalize_action_type(original_action)
            
            if (not original_action or 
                original_action.strip() == '' or 
                normalized.startswith('Action:') or 
                'inconnue' in normalized.lower()):
                
                # Essayer de deviner le type d'action à partir des détails
                suggested_action = suggest_action_from_details(entry.action_details)
                
                if suggested_action and suggested_action != original_action:
                    entry.action_type = suggested_action
                    fixed_count += 1
                    entries_updated.append({
                        'id': entry.id,
                        'original': original_action,
                        'fixed': suggested_action,
                        'normalized': normalize_action_type(suggested_action)
                    })
                elif not original_action or original_action.strip() == '':
                    entry.action_type = 'unknown_action'
                    fixed_count += 1
                    entries_updated.append({
                        'id': entry.id,
                        'original': original_action,
                        'fixed': 'unknown_action',
                        'normalized': 'Action inconnue'
                    })
        
        if fixed_count > 0:
            db.session.commit()
            logger.info(f"Correction terminée: {fixed_count} entrées mises à jour")
        
        return jsonify({
            'message': f'Correction terminée: {fixed_count} actions corrigées',
            'entries_fixed': fixed_count,
            'updates_made': entries_updated,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la correction des actions inconnues: {e}")
        return jsonify({"error": f"Erreur: {str(e)}"}), 500

def suggest_action_from_details(action_details_str):
    """Suggère un type d'action basé sur les détails"""
    if not action_details_str:
        return 'unknown_action'
    
    try:
        if isinstance(action_details_str, str):
            details = json.loads(action_details_str)
        else:
            details = action_details_str
        
        # Analyser les clés pour deviner l'action
        if any(key in details for key in ['credits_added', 'credits_purchased', 'credits_amount']):
            if 'purchased' in str(details) or 'payment_method' in details or 'price' in str(details):
                return 'buy_credits'
            else:
                return 'add_credits'
        elif any(key in details for key in ['video_title', 'video_id', 'unlock']):
            return 'unlock_video'
        elif any(key in details for key in ['club_name', 'follow']):
            if 'unfollow' in str(details).lower():
                return 'unfollow_club'
            else:
                return 'follow_club'
        elif any(key in details for key in ['player_name', 'user_name', 'name']):
            return 'update_user'
        else:
            return 'unknown_action'
            
    except Exception:
        return 'unknown_action'

@admin_bp.route("/debug/action-types", methods=["GET"])
def debug_action_types():
    """Debug: Afficher tous les types d'actions dans la base"""
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        # Récupérer tous les types d'actions uniques
        action_types = db.session.query(
            ClubActionHistory.action_type,
            db.func.count(ClubActionHistory.action_type).label('count')
        ).group_by(ClubActionHistory.action_type).all()
        
        # Analyser et normaliser
        action_analysis = []
        for action_type, count in action_types:
            normalized = normalize_action_type(action_type)
            action_analysis.append({
                'original': action_type,
                'normalized': normalized,
                'count': count,
                'needs_cleanup': normalized.startswith('Action:') or 'inconnue' in normalized.lower()
            })
        
        # Statistiques
        total_entries = ClubActionHistory.query.count()
        unknown_actions = [a for a in action_analysis if a['needs_cleanup']]
        
        return jsonify({
            'total_history_entries': total_entries,
            'unique_action_types': len(action_analysis),
            'unknown_actions_count': len(unknown_actions),
            'action_types_analysis': action_analysis,
            'unknown_actions': unknown_actions,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors du debug des types d'actions: {e}")
        return jsonify({"error": f"Erreur: {str(e)}"}), 500

@admin_bp.route("/debug/system", methods=["GET"])
def debug_system():
    """Diagnostic complet du système"""
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        # Vérification des tables
        tables_status = {
            'User': db.engine.has_table('user'),
            'Club': db.engine.has_table('club'),
            'Court': db.engine.has_table('court'),
            'Video': db.engine.has_table('video'),
            'ClubActionHistory': db.engine.has_table('club_action_history'),
            'player_club_follows': db.engine.has_table('player_club_follows')
        }
        
        # Vérification de l'intégrité des données
        integrity_checks = {
            'users_with_invalid_club_id': User.query.filter(
                User.club_id.isnot(None),
                ~User.club_id.in_(db.session.query(Club.id))
            ).count(),
            'courts_with_invalid_club_id': Court.query.filter(
                ~Court.club_id.in_(db.session.query(Club.id))
            ).count(),
            'videos_with_invalid_user_id': Video.query.filter(
                ~Video.user_id.in_(db.session.query(User.id))
            ).count(),
            'videos_with_invalid_court_id': Video.query.filter(
                ~Video.court_id.in_(db.session.query(Court.id))
            ).count()
        }
        
        # Statistiques générales
        system_stats = {
            'database_tables': tables_status,
            'data_integrity': integrity_checks,
            'total_records': {
                'users': User.query.count(),
                'clubs': Club.query.count(),
                'courts': Court.query.count(),
                'videos': Video.query.count(),
                'history_entries': ClubActionHistory.query.count()
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(system_stats), 200
        
    except Exception as e:
        logger.error(f"Erreur lors du diagnostic système: {e}")
        return jsonify({"error": f"Erreur lors du diagnostic: {str(e)}"}), 500

# --- ROUTES DE GESTION DES DONNÉES DE TEST ---

@admin_bp.route("/test-data/create-complete", methods=["POST"])
def create_complete_test_data():
    """Création de données de test complètes pour tout le système"""
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        logger.info("Début de la création de données de test complètes")
        
        # 1. Créer des clubs de test
        clubs_created = []
        test_clubs_data = [
            {'name': 'Club Padel Excellence', 'email': 'excellence@test.com', 'address': '123 Rue du Sport, Paris'},
            {'name': 'Tennis Club Premium', 'email': 'premium@test.com', 'address': '456 Avenue des Champions, Lyon'},
            {'name': 'Padel Center Pro', 'email': 'pro@test.com', 'address': '789 Boulevard du Tennis, Marseille'}
        ]
        
        for club_data in test_clubs_data:
            existing_club = Club.query.filter_by(email=club_data['email']).first()
            if not existing_club:
                new_club = Club(
                    name=club_data['name'],
                    email=club_data['email'],
                    address=club_data['address'],
                    phone_number=f"+33{random.randint(100000000, 999999999)}"
                )
                db.session.add(new_club)
                db.session.flush()
                
                # Créer l'utilisateur club associé
                club_user = User(
                    email=club_data['email'],
                    name=club_data['name'],
                    role=UserRole.CLUB,
                    club_id=new_club.id,
                    password_hash=generate_password_hash('password123')
                )
                db.session.add(club_user)
                clubs_created.append(new_club)
                logger.info(f"Club créé: {new_club.name}")
        
        db.session.flush()
        
        # 2. Créer des terrains pour chaque club
        courts_created = 0
        for club in clubs_created:
            for i in range(1, random.randint(2, 5)):  # 1-4 terrains par club
                court = Court(
                    club_id=club.id,
                    name=f"Terrain {i}",
                    qr_code=f"QR_{club.id}_{i}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    camera_url=f"http://example.com/camera/{club.id}/{i}"
                )
                db.session.add(court)
                courts_created += 1
        
        db.session.flush()
        
        # 3. Créer des joueurs pour chaque club
        players_created = 0
        for club in clubs_created:
            for i in range(1, random.randint(5, 11)):  # 4-10 joueurs par club
                player_email = f"player{i}_club{club.id}@test.com"
                existing_player = User.query.filter_by(email=player_email).first()
                if not existing_player:
                    player = User(
                        email=player_email,
                        name=f"Joueur {i} - {club.name}",
                        password_hash=generate_password_hash('password123'),
                        role=UserRole.PLAYER,
                        club_id=club.id,
                        credits_balance=random.randint(5, 50)
                    )
                    db.session.add(player)
                    players_created += 1
        
        db.session.flush()
        
        # 4. Créer des followers externes
        followers_created = 0
        all_clubs = Club.query.all()
        for i in range(1, 11):  # 10 followers externes
            follower_email = f"external_follower{i}@test.com"
            existing_follower = User.query.filter_by(email=follower_email).first()
            if not existing_follower:
                follower = User(
                    email=follower_email,
                    name=f"Follower Externe {i}",
                    password_hash=generate_password_hash('password123'),
                    role=UserRole.PLAYER,
                    credits_balance=random.randint(1, 20)
                )
                db.session.add(follower)
                db.session.flush()
                
                # Faire suivre des clubs aléatoires
                clubs_to_follow = random.sample(all_clubs, random.randint(1, min(3, len(all_clubs))))
                for club in clubs_to_follow:
                    follower.followed_clubs.append(club)
                
                followers_created += 1
        
        # 5. Créer des vidéos
        videos_created = 0
        courts = Court.query.all()
        players = User.query.filter_by(role=UserRole.PLAYER).all()
        
        for court in courts:
            # Sélectionner des joueurs aléatoires pour ce terrain
            court_players = random.sample(players, min(random.randint(2, 6), len(players)))
            for player in court_players:
                for v in range(1, random.randint(2, 4)):  # 1-3 vidéos par joueur par terrain
                    video = Video(
                        title=f"Match {player.name} - {court.name} - Video {v}",
                        description=f"Enregistrement automatique du {datetime.now().strftime('%d/%m/%Y')}",
                        file_url=f"http://example.com/videos/{court.club_id}/{court.id}/{player.id}/{v}.mp4",
                        thumbnail_url=f"http://example.com/thumbs/{court.club_id}/{court.id}/{player.id}/{v}.jpg",
                        duration=random.randint(600, 7200),
                        is_unlocked=random.choice([True, False]),
                        credits_cost=random.randint(1, 5),
                        user_id=player.id,
                        court_id=court.id,
                        recorded_at=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                        created_at=datetime.utcnow()
                    )
                    db.session.add(video)
                    videos_created += 1
        
        # 6. Créer des entrées d'historique
        history_entries_created = 0
        club_users = User.query.filter_by(role=UserRole.CLUB).all()
        
        for club_user in club_users:
            club_players = User.query.filter_by(club_id=club_user.club_id, role=UserRole.PLAYER).all()
            for player in club_players:
                # Historique d'ajout de crédits
                for _ in range(random.randint(1, 4)):
                    credits_amount = random.randint(5, 25)
                    history_entry = ClubActionHistory(
                        user_id=player.id,
                        club_id=club_user.club_id,
                        performed_by_id=club_user.id,
                        action_type='add_credits',
                        action_details=json.dumps({
                            'credits_added': credits_amount,
                            'player_name': player.name,
                            'reason': 'Données de test'
                        }),
                        performed_at=datetime.utcnow() - timedelta(days=random.randint(1, 60))
                    )
                    db.session.add(history_entry)
                    history_entries_created += 1
                
                # Historique d'ajout de joueur
                history_entry = ClubActionHistory(
                    user_id=player.id,
                    club_id=club_user.club_id,
                    performed_by_id=club_user.id,
                    action_type='add_player',
                    action_details=json.dumps({
                        'player_name': player.name,
                        'player_email': player.email
                    }),
                    performed_at=datetime.utcnow() - timedelta(days=random.randint(1, 90))
                )
                db.session.add(history_entry)
                history_entries_created += 1
        
        # Commit final
        db.session.commit()
        
        logger.info(f"Données de test créées avec succès")
        
        return jsonify({
            'message': 'Données de test complètes créées avec succès',
            'created': {
                'clubs': len(clubs_created),
                'courts': courts_created,
                'players': players_created,
                'followers': followers_created,
                'videos': videos_created,
                'history_entries': history_entries_created
            },
            'verification': {
                'total_users': User.query.count(),
                'total_clubs': Club.query.count(),
                'total_courts': Court.query.count(),
                'total_videos': Video.query.count(),
                'total_history': ClubActionHistory.query.count()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la création des données de test: {e}")
        return jsonify({'error': f'Erreur: {str(e)}'}), 500

@admin_bp.route("/test-data/cleanup", methods=["POST"])
def cleanup_test_data():
    """Nettoyer toutes les données de test"""
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        # Supprimer les données de test identifiables
        test_users_deleted = User.query.filter(User.email.like('%@test.com')).delete(synchronize_session=False)
        test_clubs_deleted = Club.query.filter(Club.email.like('%@test.com')).delete(synchronize_session=False)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Données de test supprimées avec succès',
            'deleted': {
                'users': test_users_deleted,
                'clubs': test_clubs_deleted
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors du nettoyage des données de test: {e}")
        return jsonify({'error': f'Erreur: {str(e)}'}), 500

# --- ROUTES DE MAINTENANCE ---

@admin_bp.route("/maintenance/database-check", methods=["GET"])
def database_maintenance_check():
    """Vérification de maintenance de la base de données"""
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        maintenance_report = {
            'orphaned_data': {
                'users_without_valid_club': User.query.filter(
                    User.club_id.isnot(None),
                    ~User.club_id.in_(db.session.query(Club.id))
                ).count(),
                'courts_without_valid_club': Court.query.filter(
                    ~Court.club_id.in_(db.session.query(Club.id))
                ).count(),
                'videos_without_valid_user': Video.query.filter(
                    ~Video.user_id.in_(db.session.query(User.id))
                ).count(),
                'videos_without_valid_court': Video.query.filter(
                    ~Video.court_id.in_(db.session.query(Court.id))
                ).count(),
                'history_without_valid_club': ClubActionHistory.query.filter(
                    ClubActionHistory.club_id.isnot(None),
                    ~ClubActionHistory.club_id.in_(db.session.query(Club.id))
                ).count()
            },
            'duplicate_checks': {
                'duplicate_emails': db.session.query(User.email, db.func.count(User.email)).group_by(User.email).having(db.func.count(User.email) > 1).count(),
                'duplicate_club_emails': db.session.query(Club.email, db.func.count(Club.email)).group_by(Club.email).having(db.func.count(Club.email) > 1).count()
            },
            'data_consistency': {
                'clubs_without_admin_user': Club.query.filter(
                    ~Club.id.in_(db.session.query(User.club_id).filter(User.role == UserRole.CLUB))
                ).count(),
                'users_with_negative_credits': User.query.filter(User.credits_balance < 0).count()
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(maintenance_report), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de maintenance: {e}")
        return jsonify({"error": f"Erreur: {str(e)}"}), 500

# --- ROUTES DE BULK OPERATIONS ---

@admin_bp.route("/bulk/update-credits", methods=["POST"])
def bulk_update_credits():
    """Mise à jour en masse des crédits utilisateurs"""
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    data = request.get_json()
    operation = data.get('operation')  # 'add', 'set', 'multiply'
    amount = data.get('amount', 0)
    user_ids = data.get('user_ids', [])
    
    if operation not in ['add', 'set', 'multiply']:
        return jsonify({"error": "Opération non valide"}), 400
    
    try:
        users_updated = 0
        
        if user_ids:
            users = User.query.filter(User.id.in_(user_ids)).all()
        else:
            users = User.query.filter_by(role=UserRole.PLAYER).all()
        
        for user in users:
            old_balance = user.credits_balance
            
            if operation == 'add':
                user.credits_balance += amount
            elif operation == 'set':
                user.credits_balance = amount
            elif operation == 'multiply':
                user.credits_balance = int(user.credits_balance * amount)
            
            # Log the action
            log_club_action(
                user_id=user.id,
                club_id=user.club_id,
                action_type='bulk_update_credits',
                details={
                    'operation': operation,
                    'amount': amount,
                    'old_balance': old_balance,
                    'new_balance': user.credits_balance
                },
                performed_by_id=session.get('user_id')
            )
            
            users_updated += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'{len(users)} utilisateurs mis à jour',
            'operation': operation,
            'amount': amount,
            'users_updated': len(users)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la mise à jour en lot: {e}")
        return jsonify({"error": "Erreur serveur"}), 500

# --- ROUTE DE DEBUG POUR TESTER L'AUTHENTIFICATION ADMIN ---

@admin_bp.route("/debug/auth", methods=["GET"])
def debug_admin_auth():
    """Route de debug pour tester l'authentification admin"""
    
    debug_info = {
        "session_data": dict(session),
        "user_id": session.get("user_id"),
        "user_role": session.get("user_role"),
        "user_email": session.get("user_email"),
        "user_name": session.get("user_name"),
        "expected_admin_role": UserRole.SUPER_ADMIN.value,
        "is_admin": require_super_admin(),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.info(f"🔍 Debug auth admin: {debug_info}")
    
    return jsonify({
        "message": "Debug authentification admin",
        "debug": debug_info
    }), 200

@admin_bp.route("/test/simple", methods=["GET"])
def test_simple_admin():
    """Route de test simple pour admin (sans vérification stricte)"""
    
    user_role = session.get("user_role")
    
    # Test avec différents formats de rôle admin
    is_admin = (
        user_role == "SUPER_ADMIN" or
        user_role == "super_admin" or
        user_role == "ADMIN" or
        user_role == "admin" or
        (user_role and "admin" in user_role.lower())
    )
    
    return jsonify({
        "message": "Test admin simple",
        "user_role": user_role,
        "is_admin": is_admin,
        "session_user_id": session.get("user_id"),
        "session_user_name": session.get("user_name")
    }), 200