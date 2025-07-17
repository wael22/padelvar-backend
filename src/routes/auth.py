from flask import Blueprint, request, jsonify, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from src.models.user import User, UserRole # Assurez-vous que UserRole est défini dans user.py
from src.models.database import db
import re
import traceback

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validation des données
        if not data or not data.get('email') or not data.get('password') or not data.get('name'):
            return jsonify({'error': 'Email, mot de passe et nom requis'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        name = data['name'].strip()
        phone_number = data.get('phone_number', '').strip()
        
        # Validation de l'email
        if not validate_email(email):
            return jsonify({'error': 'Format d\'email invalide'}), 400
        
        # Vérifier si l'utilisateur existe déjà
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'Un utilisateur avec cet email existe déjà'}), 409
        
        # Validation du mot de passe
        if len(password) < 6:
            return jsonify({'error': 'Le mot de passe doit contenir au moins 6 caractères'}), 400
        
        # Créer un nouvel utilisateur
        password_hash = generate_password_hash(password)
        new_user = User(
            email=email,
            password_hash=password_hash,
            name=name,
            phone_number=phone_number if phone_number else None,
            role=UserRole.PLAYER,
            credits_balance=5  # 5 crédits gratuits à l'inscription
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Créer une session permanente
        session.permanent = True
        session['user_id'] = new_user.id
        session['user_role'] = new_user.role.value
        
        print(f"Session créée pour l'utilisateur {new_user.id}: {dict(session)}")
        
        response = make_response(jsonify({
            'message': 'Inscription réussie',
            'user': new_user.to_dict()
        }), 201)
        
        return response
        
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de l'inscription: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Erreur lors de l\'inscription'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email et mot de passe requis'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Trouver l'utilisateur
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.password_hash or not check_password_hash(user.password_hash, password):
            return jsonify({'error': 'Email ou mot de passe incorrect'}), 401
        
        # Créer une session permanente
        session.permanent = True
        session['user_id'] = user.id
        session['user_role'] = user.role.value
        
        print(f"Session créée pour l'utilisateur {user.id}: {dict(session)}")
        
        response = make_response(jsonify({
            'message': 'Connexion réussie',
            'user': user.to_dict()
        }), 200)
        
        return response
        
    except Exception as e:
        print(f"Erreur lors de la connexion: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Erreur lors de la connexion'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    print(f"Déconnexion de l'utilisateur: {session.get('user_id')}")
    session.clear()
    response = make_response(jsonify({'message': 'Déconnexion réussie'}), 200)
    return response

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    try:
        print(f"Vérification de session dans /me: {dict(session)}")
        user_id = session.get("user_id")
        if not user_id:
            print("Aucun user_id dans la session")
            return jsonify({'error': 'Non authentifié'}), 401
        
        user = User.query.get(user_id)
        if not user:
            print(f"Utilisateur {user_id} non trouvé en base")
            session.clear()
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        print(f"Utilisateur trouvé: {user.email}")
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        print(f"Erreur lors de la récupération de l'utilisateur: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Erreur lors de la récupération de l\'utilisateur'}), 500

@auth_bp.route('/update-profile', methods=['PUT'])
def update_profile():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Non authentifié'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        data = request.get_json()
        
        # Mise à jour des champs autorisés
        if 'name' in data:
            user.name = data['name'].strip()
        if 'phone_number' in data:
            user.phone_number = data['phone_number'].strip() if data['phone_number'] else None
        if 'profile_photo_url' in data:
            user.profile_photo_url = data['profile_photo_url']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profil mis à jour avec succès',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de la mise à jour du profil: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Erreur lors de la mise à jour du profil'}), 500