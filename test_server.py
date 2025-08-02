#!/usr/bin/env python3
"""
Serveur Flask minimal pour tester la connexion admin
Sans les dépendances vidéo problématiques
"""

import os
import sys
from pathlib import Path
from flask import Flask, request, jsonify, session
from flask_cors import CORS
import sqlite3

# Configuration du chemin
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'

# Configuration CORS
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"], supports_credentials=True)

def verify_password(stored_hash, password):
    """Vérification simple du mot de passe"""
    # Pour les tests, on accepte "admin123" pour le hash existant
    if password == "admin123":
        return True
    return False

def get_user_by_email(email):
    """Récupérer un utilisateur par email"""
    try:
        conn = sqlite3.connect('instance/app.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM user WHERE email = ?", (email,))
        user_data = cursor.fetchone()
        
        if user_data:
            # Structure: id, email, password_hash, name, phone_number, role, credits_balance, created_at, club_id
            return {
                'id': user_data[0],
                'email': user_data[1],
                'password_hash': user_data[2],
                'name': user_data[3],
                'phone_number': user_data[4],
                'role': user_data[5],
                'credits_balance': user_data[6],
                'created_at': user_data[7],
                'club_id': user_data[8]
            }
        return None
        
    except Exception as e:
        print(f"Erreur DB: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Route de connexion"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Données manquantes'}), 400
        
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Email et mot de passe requis'}), 400
    
    print(f"🔍 Tentative de connexion: {email}")
    
    # Récupérer l'utilisateur
    user = get_user_by_email(email)
    
    if not user:
        print(f"❌ Utilisateur non trouvé: {email}")
        return jsonify({'error': 'Email ou mot de passe incorrect'}), 401
    
    print(f"✅ Utilisateur trouvé: {user['name']} ({user['role']})")
    
    # Vérifier le mot de passe
    if not verify_password(user['password_hash'], password):
        print(f"❌ Mot de passe incorrect pour: {email}")
        return jsonify({'error': 'Email ou mot de passe incorrect'}), 401
    
    # Créer la session
    session['user_id'] = user['id']
    session['user_email'] = user['email']
    session['user_role'] = user['role']
    session['user_name'] = user['name']
    
    print(f"🎉 Connexion réussie: {user['name']}")
    
    return jsonify({
        'message': 'Connexion réussie',
        'user': {
            'id': user['id'],
            'email': user['email'],
            'name': user['name'],
            'role': user['role'],
            'credits_balance': user['credits_balance']
        }
    }), 200

@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """Récupérer les informations de l'utilisateur connecté"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non connecté'}), 401
    
    return jsonify({
        'user': {
            'id': session['user_id'],
            'email': session['user_email'],
            'name': session['user_name'],
            'role': session['user_role']
        }
    }), 200

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Déconnexion"""
    session.clear()
    return jsonify({'message': 'Déconnexion réussie'}), 200

@app.route('/api/admin/users', methods=['GET'])
def get_users():
    """Route admin simple pour tester"""
    if session.get('user_role') != 'SUPER_ADMIN':
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    try:
        conn = sqlite3.connect('instance/app.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, email, name, role, credits_balance FROM user")
        users_data = cursor.fetchall()
        
        users = []
        for user_data in users_data:
            users.append({
                'id': user_data[0],
                'email': user_data[1],
                'name': user_data[2],
                'role': user_data[3],
                'credits_balance': user_data[4]
            })
        
        return jsonify({'users': users}), 200
        
    except Exception as e:
        print(f"Erreur: {e}")
        return jsonify({'error': 'Erreur serveur'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/health', methods=['GET'])
def health_check():
    """Vérification de santé du serveur"""
    return jsonify({'status': 'OK', 'message': 'Serveur en fonctionnement'}), 200

if __name__ == '__main__':
    print("🚀 Démarrage du serveur de test PadelVar")
    print("📍 URL: http://localhost:5000")
    print("🔑 Compte admin:")
    print("   Email: admin@padelvar.com")
    print("   Mot de passe: admin123")
    print("─" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
