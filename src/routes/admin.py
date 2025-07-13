from flask import Blueprint, request, jsonify, session
from models.user import db, User, Club, Court, Video, UserRole
from werkzeug.security import generate_password_hash
import uuid

admin_bp = Blueprint('admin', __name__)

def require_super_admin():
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    
    if not user_id or user_role != UserRole.SUPER_ADMIN.value:
        return False
    return True

@admin_bp.route('/users', methods=['GET'])
def get_all_users():
    if not require_super_admin():
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    try:
        users = User.query.all()
        return jsonify({
            'users': [user.to_dict() for user in users]
        }), 200
    except Exception as e:
        return jsonify({'error': 'Erreur lors de la récupération des utilisateurs'}), 500

@admin_bp.route('/users', methods=['POST'])
def create_user():
    if not require_super_admin():
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('name') or not data.get('role'):
            return jsonify({'error': 'Email, nom et rôle requis'}), 400
        
        email = data['email'].lower().strip()
        name = data['name'].strip()
        role = data['role']
        
        # Vérifier si l'utilisateur existe déjà
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'Un utilisateur avec cet email existe déjà'}), 409
        
        # Valider le rôle
        try:
            user_role = UserRole(role)
        except ValueError:
            return jsonify({'error': 'Rôle invalide'}), 400
        
        # Créer l'utilisateur
        new_user = User(
            email=email,
            name=name,
            role=user_role,
            phone_number=data.get('phone_number'),
            credits_balance=data.get('credits_balance', 0)
        )
        
        # Si un mot de passe est fourni
        if data.get('password'):
            new_user.password_hash = generate_password_hash(data['password'])
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'message': 'Utilisateur créé avec succès',
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erreur lors de la création de l\'utilisateur'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    if not require_super_admin():
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        data = request.get_json()
        
        # Mise à jour des champs
        if 'name' in data:
            user.name = data['name'].strip()
        if 'phone_number' in data:
            user.phone_number = data['phone_number']
        if 'credits_balance' in data:
            user.credits_balance = data['credits_balance']
        if 'role' in data:
            try:
                user.role = UserRole(data['role'])
            except ValueError:
                return jsonify({'error': 'Rôle invalide'}), 400
        if 'email' in data:
            user.email = data['email'].lower().strip()
        if 'password' in data and data['password']:
            user.password_hash = generate_password_hash(data['password'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Utilisateur mis à jour avec succès',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erreur lors de la mise à jour de l\'utilisateur'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if not require_super_admin():
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'Utilisateur supprimé avec succès'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erreur lors de la suppression de l\'utilisateur'}), 500

@admin_bp.route('/clubs', methods=['GET'])
def get_all_clubs():
    if not require_super_admin():
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    try:
        clubs = Club.query.all()
        return jsonify({
            'clubs': [club.to_dict() for club in clubs]
        }), 200
    except Exception as e:
        return jsonify({'error': 'Erreur lors de la récupération des clubs'}), 500

@admin_bp.route('/clubs', methods=['POST'])
def create_club():
    if not require_super_admin():
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    try:
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({'error': 'Nom du club requis'}), 400
        
        new_club = Club(
            name=data['name'].strip(),
            address=data.get('address'),
            phone_number=data.get('phone_number'),
            email=data.get('email')
        )
        
        db.session.add(new_club)
        db.session.commit()
        
        return jsonify({
            'message': 'Club créé avec succès',
            'club': new_club.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erreur lors de la création du club'}), 500

@admin_bp.route('/clubs/<int:club_id>/courts', methods=['POST'])
def create_court(club_id):
    if not require_super_admin():
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    try:
        club = Club.query.get(club_id)
        if not club:
            return jsonify({'error': 'Club non trouvé'}), 404
        
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({'error': 'Nom du terrain requis'}), 400
        
        if not data.get('camera_url'):
            return jsonify({'error': 'URL de la caméra obligatoire'}), 400
        
        # Générer un QR code unique
        qr_code = str(uuid.uuid4())
        
        new_court = Court(
            name=data['name'].strip(),
            qr_code=qr_code,
            camera_url=data['camera_url'].strip(),
            club_id=club_id
        )
        
        db.session.add(new_court)
        db.session.commit()
        
        return jsonify({
            'message': 'Terrain créé avec succès',
            'court': new_court.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erreur lors de la création du terrain'}), 500

@admin_bp.route('/videos', methods=['GET'])
def get_all_videos():
    if not require_super_admin():
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    try:
        videos = Video.query.all()
        return jsonify({
            'videos': [video.to_dict() for video in videos]
        }), 200
    except Exception as e:
        return jsonify({'error': 'Erreur lors de la récupération des vidéos'}), 500

@admin_bp.route('/users/<int:user_id>/credits', methods=['POST'])
def add_credits(user_id):
    if not require_super_admin():
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        data = request.get_json()
        credits_to_add = data.get('credits', 0)
        
        if credits_to_add <= 0:
            return jsonify({'error': 'Le nombre de crédits doit être positif'}), 400
        
        user.credits_balance += credits_to_add
        db.session.commit()
        
        return jsonify({
            'message': f'{credits_to_add} crédits ajoutés avec succès',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erreur lors de l\'ajout de crédits'}), 500


@admin_bp.route('/videos/all-clubs', methods=['GET'])
def get_all_clubs_videos():
    """Permet au super admin de voir toutes les vidéos de tous les clubs"""
    if not require_super_admin():
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    try:
        # Récupérer toutes les vidéos avec les informations du terrain et du club
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
            video_dict['court_name'] = court.name
            video_dict['club_name'] = club.name
            video_dict['player_name'] = user.name
            videos_data.append(video_dict)
        
        return jsonify({
            'videos': videos_data
        }), 200
    except Exception as e:
        return jsonify({'error': 'Erreur lors de la récupération des vidéos'}), 500



@admin_bp.route("/clubs/<int:club_id>/courts", methods=["GET"])
def get_club_courts(club_id):
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        club = Club.query.get(club_id)
        if not club:
            return jsonify({"error": "Club non trouvé"}), 404
        
        courts = Court.query.filter_by(club_id=club_id).all()
        return jsonify({"courts": [court.to_dict() for court in courts]}), 200
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la récupération des terrains: {str(e)}"}), 500

@admin_bp.route("/courts/<int:court_id>", methods=["PUT"])
def update_court(court_id):
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        court = Court.query.get(court_id)
        if not court:
            return jsonify({"error": "Terrain non trouvé"}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "Données requises"}), 400
        
        if "name" in data:
            court.name = data["name"].strip()
        if "camera_url" in data:
            court.camera_url = data["camera_url"].strip()
        
        db.session.commit()
        return jsonify({"message": "Terrain mis à jour avec succès", "court": court.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erreur lors de la mise à jour du terrain: {str(e)}"}), 500

@admin_bp.route("/courts/<int:court_id>", methods=["DELETE"])
def delete_court(court_id):
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        court = Court.query.get(court_id)
        if not court:
            return jsonify({"error": "Terrain non trouvé"}), 404
        
        db.session.delete(court)
        db.session.commit()
        return jsonify({"message": "Terrain supprimé avec succès"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erreur lors de la suppression du terrain: {str(e)}"}), 500




@admin_bp.route("/clubs/<int:club_id>", methods=["PUT"])
def update_club(club_id):
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        club = Club.query.get(club_id)
        if not club:
            return jsonify({"error": "Club non trouvé"}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "Données requises"}), 400
        
        if "name" in data:
            club.name = data["name"].strip()
        if "address" in data:
            club.address = data["address"].strip()
        if "phone_number" in data:
            club.phone_number = data["phone_number"].strip()
        if "email" in data:
            club.email = data["email"].strip()
        
        db.session.commit()
        return jsonify({"message": "Club mis à jour avec succès", "club": club.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erreur lors de la mise à jour du club: {str(e)}"}), 500

@admin_bp.route("/clubs/<int:club_id>", methods=["DELETE"])
def delete_club(club_id):
    if not require_super_admin():
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        club = Club.query.get(club_id)
        if not club:
            return jsonify({"error": "Club non trouvé"}), 404
        
        # Supprimer les terrains associés au club
        Court.query.filter_by(club_id=club_id).delete()
        
        # Supprimer les utilisateurs (joueurs) associés au club
        User.query.filter_by(club_id=club_id).delete()

        db.session.delete(club)
        db.session.commit()
        return jsonify({"message": "Club supprimé avec succès"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erreur lors de la suppression du club: {str(e)}"}), 500


