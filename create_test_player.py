#!/usr/bin/env python3
"""
Script pour créer un utilisateur joueur de test
"""

import sys
import os

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.models.database import db
from src.models.user import User, UserRole
from src.main import create_app
from werkzeug.security import generate_password_hash

def create_test_player():
    """Créer un utilisateur joueur de test"""
    app = create_app()
    
    with app.app_context():
        try:
            # Vérifier si l'utilisateur existe déjà
            existing_user = User.query.filter_by(email='player@test.com').first()
            if existing_user:
                print(f"Utilisateur joueur déjà existant: {existing_user.email} (ID: {existing_user.id}, Rôle: {existing_user.role})")
                return
            
            # Créer un nouvel utilisateur joueur
            player_user = User(
                name='Test Player',
                email='player@test.com',
                password_hash=generate_password_hash('password123'),
                phone_number='+33123456789',
                role=UserRole.PLAYER,
                credits_balance=100  # Crédits de départ
            )
            
            db.session.add(player_user)
            db.session.commit()
            
            print(f"Utilisateur joueur créé avec succès:")
            print(f"  Nom: {player_user.name}")
            print(f"  Email: {player_user.email}")
            print(f"  ID: {player_user.id}")
            print(f"  Rôle: {player_user.role}")
            print(f"  Crédits: {player_user.credits_balance}")
            print(f"  Mot de passe: password123")
            
        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de la création de l'utilisateur joueur: {e}")

if __name__ == '__main__':
    create_test_player()
