"""
Script pour réinitialiser la base de données et appliquer les nouvelles migrations
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire du projet au chemin Python
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from flask import Flask
from flask_migrate import init, migrate, upgrade, stamp
from src.main import create_app

def reset_and_migrate():
    """Réinitialiser la base de données et appliquer les migrations"""
    
    print("🔄 Réinitialisation de la base de données et migration")
    print("=" * 60)
    
    try:
        # Créer l'application
        app = create_app('development')
        
        with app.app_context():
            from src.models.database import db
            
            # Supprimer toutes les tables existantes
            print("\n🗑️  Suppression des tables existantes...")
            db.drop_all()
            print("✅ Tables supprimées")
            
            # Créer toutes les tables avec le nouveau schéma
            print("\n📋 Création des nouvelles tables...")
            db.create_all()
            print("✅ Nouvelles tables créées")
            
            # Marquer la migration comme appliquée
            print("\n📌 Marquage des migrations comme appliquées...")
            stamp('head')
            print("✅ Migrations marquées")
            
            # Créer les données de test
            print("\n👤 Création des utilisateurs de test...")
            from src.models.user import User, UserRole, Club, Court
            from werkzeug.security import generate_password_hash
            
            # Super admin
            if not User.query.filter_by(email='admin@padelvar.com').first():
                admin = User(
                    email='admin@padelvar.com',
                    password_hash=generate_password_hash('admin123'),
                    name='Super Admin',
                    role=UserRole.SUPER_ADMIN,
                    credits_balance=1000
                )
                db.session.add(admin)
            
            # Joueur de test
            if not User.query.filter_by(email='test@example.com').first():
                player = User(
                    email='test@example.com',
                    password_hash=generate_password_hash('password123'),
                    name='Joueur Test',
                    role=UserRole.PLAYER,
                    credits_balance=5
                )
                db.session.add(player)
            
            # Club de test
            if not Club.query.filter_by(name='Club Test').first():
                club = Club(
                    name='Club Test',
                    address='123 Rue Test',
                    phone_number='12345678',
                    email='club@test.com'
                )
                db.session.add(club)
                db.session.flush()  # Pour obtenir l'ID du club
                
                # Utilisateur club
                if not User.query.filter_by(email='club@example.com').first():
                    club_user = User(
                        email='club@example.com',
                        password_hash=generate_password_hash('password123'),
                        name='Club Manager',
                        role=UserRole.CLUB,
                        club_id=club.id,
                        credits_balance=0
                    )
                    db.session.add(club_user)
                
                # Terrains de test
                court1 = Court(
                    name='Terrain 1',
                    qr_code='QR001',
                    camera_url='rtmp://test.com/court1',
                    club_id=club.id,
                    is_recording=False
                )
                court2 = Court(
                    name='Terrain 2',
                    qr_code='QR002',
                    camera_url='rtmp://test.com/court2',
                    club_id=club.id,
                    is_recording=False
                )
                db.session.add_all([court1, court2])
                
                # Faire suivre le club par le joueur
                player.followed_clubs.append(club)
                player.club_id = club.id
            
            db.session.commit()
            print("✅ Données de test créées")
            
            print("\n🎉 Base de données réinitialisée avec succès!")
            print("\nComptes de test créés:")
            print("• Super Admin: admin@padelvar.com / admin123")
            print("• Joueur: test@example.com / password123")
            print("• Club: club@example.com / password123")
            print("\nNouveautés disponibles:")
            print("• Système d'enregistrement avec durée sélectionnable")
            print("• Bandeau d'enregistrement en cours")
            print("• Gestion des terrains par les clubs")
            print("• Réservation automatique des terrains")
            
    except Exception as e:
        print(f"❌ Erreur lors de la réinitialisation: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = reset_and_migrate()
    if success:
        print("\n🚀 Vous pouvez maintenant redémarrer le serveur!")
    else:
        print("\n💥 La réinitialisation a échoué.")
        sys.exit(1)
