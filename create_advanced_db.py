"""
Script simple pour créer la base de données avec les nouvelles fonctionnalités
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire du projet au chemin Python
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def create_database_with_new_features():
    """Créer la base de données avec toutes les nouvelles fonctionnalités"""
    
    print("🔄 Création de la base de données avec fonctionnalités d'enregistrement avancé")
    print("=" * 70)
    
    try:
        from src.main import create_app
        
        # Créer l'application
        app = create_app('development')
        
        with app.app_context():
            from src.models.database import db
            from src.models.user import User, UserRole, Club, Court, RecordingSession
            from werkzeug.security import generate_password_hash
            
            # Supprimer et recréer toutes les tables
            print("\n🗑️  Suppression des anciennes tables...")
            db.drop_all()
            
            print("📋 Création des nouvelles tables...")
            db.create_all()
            print("✅ Tables créées avec succès")
            
            # Vérifier que les nouvelles tables existent
            print("\n🔍 Vérification des nouvelles structures...")
            
            # Test RecordingSession
            test_recording = RecordingSession(
                recording_id='test',
                user_id=1,
                court_id=1,
                club_id=1,
                planned_duration=90
            )
            print("✅ Modèle RecordingSession validé")
            
            # Test Court avec nouvelles colonnes
            inspector = db.inspect(db.engine)
            court_columns = [col['name'] for col in inspector.get_columns('court')]
            if 'is_recording' in court_columns and 'current_recording_id' in court_columns:
                print("✅ Nouvelles colonnes Court validées")
            else:
                print("❌ Colonnes Court manquantes")
            
            # Créer les données de test
            print("\n👤 Création des utilisateurs et données de test...")
            
            # Super admin
            admin = User(
                email='admin@padelvar.com',
                password_hash=generate_password_hash('admin123'),
                name='Super Admin',
                role=UserRole.SUPER_ADMIN,
                credits_balance=1000
            )
            db.session.add(admin)
            
            # Joueur de test
            player = User(
                email='test@example.com',
                password_hash=generate_password_hash('password123'),
                name='Joueur Test',
                role=UserRole.PLAYER,
                credits_balance=10
            )
            db.session.add(player)
            
            # Club de test
            club = Club(
                name='Club Test',
                address='123 Rue Test',
                phone_number='12345678',
                email='club@test.com'
            )
            db.session.add(club)
            db.session.flush()  # Pour obtenir l'ID du club
            
            # Utilisateur club
            club_user = User(
                email='club@example.com',
                password_hash=generate_password_hash('password123'),
                name='Club Manager',
                role=UserRole.CLUB,
                club_id=club.id,
                credits_balance=0
            )
            db.session.add(club_user)
            
            # Terrains de test avec nouvelles colonnes
            court1 = Court(
                name='Terrain Principal',
                qr_code='QR001',
                camera_url='rtmp://test.com/court1',
                club_id=club.id,
                is_recording=False,
                current_recording_id=None
            )
            court2 = Court(
                name='Terrain Annexe',
                qr_code='QR002',
                camera_url='rtmp://test.com/court2',
                club_id=club.id,
                is_recording=False,
                current_recording_id=None
            )
            db.session.add_all([court1, court2])
            
            # Club supplémentaire
            club2 = Club(
                name='Club Avancé',
                address='456 Avenue Sport',
                phone_number='87654321',
                email='advanced@club.com'
            )
            db.session.add(club2)
            db.session.flush()
            
            # Terrain pour le second club
            court3 = Court(
                name='Court Professionnel',
                qr_code='QR003',
                camera_url='rtmp://test.com/court3',
                club_id=club2.id,
                is_recording=False,
                current_recording_id=None
            )
            db.session.add(court3)
            
            # Faire suivre les clubs par le joueur
            player.followed_clubs.append(club)
            player.followed_clubs.append(club2)
            player.club_id = club.id
            
            db.session.commit()
            print("✅ Données de test créées")
            
            # Vérifier les relations
            player_clubs = player.followed_clubs.all()
            print(f"✅ Joueur suit {len(player_clubs)} clubs")
            
            print("\n🎉 Base de données créée avec succès!")
            print("\n" + "="*50)
            print("COMPTES DE TEST:")
            print("• Super Admin: admin@padelvar.com / admin123")
            print("• Joueur: test@example.com / password123 (10 crédits)")
            print("• Club: club@example.com / password123")
            print("\nDONNÉES CRÉÉES:")
            print("• 2 clubs avec 3 terrains au total")
            print("• Relations club-joueur configurées")
            print("• Terrains avec QR codes")
            print("\nNOUVELLES FONCTIONNALITÉS:")
            print("• ✨ Sélection de durée d'enregistrement (60, 90, 120 min, MAX)")
            print("• ⏰ Arrêt automatique après la durée choisie")
            print("• 📺 Bandeau d'enregistrement en cours pour les joueurs")
            print("• 🏢 Interface de gestion des enregistrements pour les clubs")
            print("• 🔒 Réservation automatique des terrains pendant l'enregistrement")
            print("• 🛑 Possibilité d'arrêt forcé par le club")
            
    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = create_database_with_new_features()
    if success:
        print("\n🚀 Redémarrez le serveur pour utiliser les nouvelles fonctionnalités!")
        print("   python app.py")
    else:
        print("\n💥 Échec de la création de la base de données.")
        sys.exit(1)
