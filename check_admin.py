#!/usr/bin/env python3
# Script pour vérifier et créer un compte super admin

import os
import sys
from pathlib import Path

# Configuration du chemin pour permettre l'importation du package src
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.models.user import db, User, UserRole
from src.main import create_app
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    print("=== VÉRIFICATION DES UTILISATEURS ===")
    
    # Vérifier tous les utilisateurs
    users = User.query.all()
    print(f"Total utilisateurs: {len(users)}")
    
    for user in users:
        print(f"ID: {user.id}, Email: {user.email}, Nom: {user.name}, Rôle: {user.role.value}")
    
    # Vérifier spécifiquement les super admins
    admins = User.query.filter_by(role=UserRole.SUPER_ADMIN).all()
    print(f"\n=== SUPER ADMINS ({len(admins)}) ===")
    
    if len(admins) == 0:
        print("❌ Aucun super admin trouvé!")
        
        # Créer un super admin
        print("\n🔧 Création d'un super admin...")
        
        admin_user = User(
            email="admin@padelvar.com",
            name="Super Admin",
            role=UserRole.SUPER_ADMIN,
            password_hash=generate_password_hash("admin123"),
            credits_balance=0
        )
        
        try:
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Super admin créé avec succès!")
            print("Email: admin@padelvar.com")
            print("Mot de passe: admin123")
        except Exception as e:
            print(f"❌ Erreur lors de la création: {e}")
            db.session.rollback()
    else:
        print("✅ Super admins existants:")
        for admin in admins:
            print(f"   - Email: {admin.email}, Nom: {admin.name}")
            
    print("\n=== VÉRIFICATION TERMINÉE ===")
