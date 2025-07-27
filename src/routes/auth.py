# padelvar-backend/src/routes/auth.py

from flask import Blueprint, request, jsonify, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from ..models.user import User, UserRole
from ..models.database import db
import re
import traceback
import logging # Ajout du logger

logger = logging.getLogger(__name__)

# La définition du Blueprint doit être ici, avant les routes
auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@auth_bp.route('/register', methods=['POST'])
def register():
    # ... (code de la fonction register inchangé)
    try:
        data = request.get_json()
        if not data or not data.get('email') or not data.get('password') or not data.get('name'):
            return jsonify({'error': 'Email, mot de passe et nom requis'}), 400
        email = data['email'].lower().strip()
        password = data['password']
        name = data['name'].strip()
        phone_number = data.get('phone_number', '').strip()
        if not validate_email(email):
            return jsonify({'error': 'Format d\'email invalide'}), 400
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'Un utilisateur avec cet email existe déjà'}), 409
        if len(password) < 6:
            return jsonify({'error': 'Le mot de passe doit contenir au moins 6 caractères'}), 400
        password_hash = generate_password_hash(password)
        new_user = User(
            email=email, password_hash=password_hash, name=name,
            phone_number=phone_number if phone_number else None,
            role=UserRole.PLAYER, credits_balance=5
        )
        db.session.add(new_user)
        db.session.commit()
        session.permanent = True
        session['user_id'] = new_user.id
        session['user_role'] = new_user.role.value
        response = make_response(jsonify({'message': 'Inscription réussie', 'user': new_user.to_dict()}), 201)
        return response
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': 'Erreur lors de l\'inscription'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    # ... (code de la fonction login inchangé)
    try:
        data = request.get_json()
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email et mot de passe requis'}), 400
        email = data['email'].lower().strip()
        password = data['password']
        user = User.query.filter_by(email=email).first()
        if not user or not user.password_hash or not check_password_hash(user.password_hash, password):
            return jsonify({'error': 'Email ou mot de passe incorrect'}), 401
        session.permanent = True
        session['user_id'] = user.id
        session['user_role'] = user.role.value
        response = make_response(jsonify({'message': 'Connexion réussie', 'user': user.to_dict()}), 200)
        return response
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Erreur lors de la connexion'}), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    # ... (code de la fonction logout inchangé)
    session.clear()
    response = make_response(jsonify({'message': 'Déconnexion réussie'}), 200)
    return response


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    # ... (code de la fonction get_current_user inchangé)
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({'error': 'Non authentifié'}), 401
        user = User.query.get(user_id)
        if not user:
            session.clear()
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        return jsonify({'user': user.to_dict()}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Erreur lors de la récupération de l\'utilisateur'}), 500


@auth_bp.route('/update-profile', methods=['PUT'])
def update_profile():
    # ... (code de la fonction update_profile inchangé)
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Non authentifié'}), 401
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        data = request.get_json()
        if 'name' in data:
            user.name = data['name'].strip()
        if 'phone_number' in data:
            user.phone_number = data['phone_number'].strip() if data['phone_number'] else None
        db.session.commit()
        return jsonify({'message': 'Profil mis à jour avec succès', 'user': user.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': 'Erreur lors de la mise à jour du profil'}), 500


# ====================================================================
# NOUVELLE ROUTE PLACÉE À LA FIN DU FICHIER
# ====================================================================
@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Non authentifié'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return jsonify({'error': 'Ancien et nouveau mots de passe requis'}), 400
        
    if not user.password_hash or not check_password_hash(user.password_hash, old_password):
        return jsonify({'error': 'Ancien mot de passe incorrect'}), 403
        
    if len(new_password) < 6:
        return jsonify({'error': 'Le nouveau mot de passe doit contenir au moins 6 caractères'}), 400
        
    try:
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        return jsonify({'message': 'Mot de passe mis à jour avec succès'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors du changement de mot de passe pour l'utilisateur {user.id}: {e}")
        return jsonify({'error': 'Erreur interne lors de la mise à jour'}), 500