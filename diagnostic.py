"""
Script de diagnostic pour vérifier l'état de la base de données et les relations
entre les entités de l'application Padelvar.
"""
import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import json
from enum import Enum
from datetime import datetime

# Configurez le chemin de la base de données
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'src', 'database', 'app.db')

if not os.path.exists(db_path):
    db_path = os.path.join(basedir, 'instance', 'app.db')
    if not os.path.exists(db_path):
        print(f"ERREUR: Base de données non trouvée aux chemins attendus.")
        print(f"Chemins recherchés: {os.path.join(basedir, 'src', 'database', 'app.db')} et {os.path.join(basedir, 'instance', 'app.db')}")
        sys.exit(1)

print(f"Utilisation de la base de données: {db_path}")

# Initialisez l'application Flask pour le contexte
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Importer les modèles directement depuis les modules de l'application
# Si cela ne fonctionne pas, utilisez les définitions de modèles simplifiées
try:
    from src.models.user import User, Club, Court, Video, ClubActionHistory, UserRole, player_club_follows
    print("Modèles importés depuis les modules de l'application")
except ImportError:
    print("Impossible d'importer les modèles depuis les modules de l'application")
    print("Utilisation des définitions de modèles simplifiées")
    
    # Définitions simplifiées des modèles
    class UserRole(Enum):
        SUPER_ADMIN = "super_admin"
        PLAYER = "player"
        CLUB = "club"

    player_club_follows = db.Table(
        'player_club_follows',
        db.Column('player_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
        db.Column('club_id', db.Integer, db.ForeignKey('club.id'), primary_key=True)
    )

    class User(db.Model):
        __tablename__ = 'user'
        id = db.Column(db.Integer, primary_key=True)
        email = db.Column(db.String(120), unique=True, nullable=False)
        password_hash = db.Column(db.String(255), nullable=True)
        name = db.Column(db.String(100), nullable=False)
        phone_number = db.Column(db.String(20), nullable=True)
        role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.PLAYER)
        credits_balance = db.Column(db.Integer, default=0)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        
        club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=True)
        
        followed_clubs = db.relationship('Club', 
                                    secondary=player_club_follows,
                                    backref=db.backref('followers', lazy='dynamic'),
                                    lazy='dynamic')
    
    class Club(db.Model):
        __tablename__ = 'club'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)
        address = db.Column(db.String(255), nullable=True)
        phone_number = db.Column(db.String(20), nullable=True)
        email = db.Column(db.String(120), nullable=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        
        players = db.relationship('User', backref='club', lazy=True)
        courts = db.relationship('Court', backref='club', lazy=True)
    
    class Court(db.Model):
        __tablename__ = 'court'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)
        qr_code = db.Column(db.String(100), unique=True, nullable=False)
        camera_url = db.Column(db.String(255), nullable=False)
        club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    
    class Video(db.Model):
        __tablename__ = 'video'
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(200), nullable=False)
        file_url = db.Column(db.String(255), nullable=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        court_id = db.Column(db.Integer, db.ForeignKey('court.id'), nullable=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    class ClubActionHistory(db.Model):
        __tablename__ = 'club_action_history'
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=True)
        performed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        action_type = db.Column(db.String(50), nullable=False)
        action_details = db.Column(db.Text, nullable=True)
        performed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# Fonction de diagnostic pour afficher les statistiques du tableau de bord pour un club
def dashboard_diagnostic(club_id):
    try:
        # Récupérer le club
        club = Club.query.get(club_id)
        if not club:
            print(f"ERREUR: Club avec ID {club_id} non trouvé dans la base de données")
            return
            
        print(f"\n=== DIAGNOSTIC TABLEAU DE BORD DU CLUB {club.name} (ID: {club.id}) ===")
        
        # Compter les joueurs associés au club
        players = User.query.filter_by(club_id=club.id, role=UserRole.PLAYER).all()
        players_count = len(players)
        print(f"Nombre de joueurs associés au club: {players_count}")
        if players_count > 0:
            print("  Premiers joueurs:")
            for player in players[:3]:  # Limiter à 3 pour la lisibilité
                print(f"  - {player.name} (ID: {player.id}, Email: {player.email})")
        else:
            print("  PROBLÈME: Aucun joueur associé à ce club.")
        
        # Compter les terrains du club
        courts = Court.query.filter_by(club_id=club.id).all()
        courts_count = len(courts)
        print(f"Nombre de terrains du club: {courts_count}")
        if courts_count > 0:
            print("  Premiers terrains:")
            for court in courts[:3]:  # Limiter à 3 pour la lisibilité
                print(f"  - {court.name} (ID: {court.id}, QR Code: {court.qr_code})")
        else:
            print("  PROBLÈME: Aucun terrain associé à ce club.")
        
        # Compter les vidéos enregistrées sur les terrains du club
        court_ids = [court.id for court in courts]
        videos = []
        videos_count = 0
        if court_ids:
            videos = Video.query.filter(Video.court_id.in_(court_ids)).all()
            videos_count = len(videos)
        print(f"Nombre de vidéos enregistrées: {videos_count}")
        if videos_count > 0:
            print("  Premières vidéos:")
            for video in videos[:3]:  # Limiter à 3 pour la lisibilité
                print(f"  - {video.title} (ID: {video.id}, Court: {video.court_id})")
        else:
            print("  PROBLÈME: Aucune vidéo associée aux terrains de ce club.")
        
        # Compter les followers du club
        try:
            followers = club.followers.all()
            followers_count = len(followers)
            print(f"Nombre de followers du club: {followers_count}")
            if followers_count > 0:
                print("  Premiers followers:")
                for follower in followers[:3]:  # Limiter à 3 pour la lisibilité
                    print(f"  - {follower.name} (ID: {follower.id}, Email: {follower.email})")
            else:
                print("  PROBLÈME: Aucun follower pour ce club.")
        except Exception as e:
            print(f"  ERREUR lors du comptage des followers: {e}")
        
        # Compter les crédits offerts par le club
        try:
            history_entries = ClubActionHistory.query.filter(
                ClubActionHistory.club_id == club.id,
                ClubActionHistory.action_type == 'add_credits'
            ).all()
            
            credits_given = 0
            for entry in history_entries:
                try:
                    # Tenter de parser le JSON
                    details = json.loads(entry.action_details)
                    credits_added = details.get('credits_added', 0)
                    credits_given += int(credits_added)
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    print(f"  ERREUR lors du parsing des crédits pour l'entrée {entry.id}: {e}")
            
            print(f"Nombre de crédits offerts par le club: {credits_given}")
            if history_entries:
                print("  Premières entrées d'historique pour les crédits:")
                for entry in history_entries[:3]:  # Limiter à 3 pour la lisibilité
                    print(f"  - ID: {entry.id}, Utilisateur: {entry.user_id}, Détails: {entry.action_details}")
            else:
                print("  PROBLÈME: Aucune entrée d'historique pour les crédits offerts.")
        except Exception as e:
            print(f"  ERREUR lors du calcul des crédits: {e}")
        
        # Afficher toutes les entrées d'historique du club
        try:
            history_entries = ClubActionHistory.query.filter_by(club_id=club.id).all()
            print(f"\nNombre total d'entrées d'historique pour le club: {len(history_entries)}")
            if history_entries:
                print("  Types d'actions dans l'historique:")
                action_types = {}
                for entry in history_entries:
                    action_type = entry.action_type
                    action_types[action_type] = action_types.get(action_type, 0) + 1
                
                for action_type, count in action_types.items():
                    print(f"  - {action_type}: {count} entrées")
            else:
                print("  PROBLÈME: Aucune entrée d'historique pour ce club.")
        except Exception as e:
            print(f"  ERREUR lors de l'affichage de l'historique: {e}")
            
    except Exception as e:
        print(f"ERREUR CRITIQUE lors du diagnostic: {e}")

# Fonction principale
def main():
    with app.app_context():
        # Vérifier les tables de la base de données
        print("\n=== VÉRIFICATION DES TABLES DE LA BASE DE DONNÉES ===")
        tables = {
            'user': db.engine.has_table('user'),
            'club': db.engine.has_table('club'),
            'court': db.engine.has_table('court'),
            'video': db.engine.has_table('video'),
            'club_action_history': db.engine.has_table('club_action_history'),
            'player_club_follows': db.engine.has_table('player_club_follows')
        }
        
        for table_name, exists in tables.items():
            print(f"Table {table_name}: {'EXISTE' if exists else 'MANQUANTE'}")
        
        # Compter les entités dans chaque table
        print("\n=== NOMBRE D'ENTITÉS PAR TABLE ===")
        entity_counts = {
            'Users': User.query.count(),
            'Clubs': Club.query.count(),
            'Courts': Court.query.count(),
            'Videos': Video.query.count(),
            'ClubActionHistory': ClubActionHistory.query.count()
        }
        
        for entity_name, count in entity_counts.items():
            print(f"{entity_name}: {count}")
        
        # Afficher tous les clubs
        print("\n=== LISTE DES CLUBS ===")
        clubs = Club.query.all()
        if clubs:
            for club in clubs:
                print(f"Club: {club.name} (ID: {club.id})")
                # Exécuter le diagnostic pour chaque club
                dashboard_diagnostic(club.id)
        else:
            print("Aucun club trouvé dans la base de données.")
            
        # Afficher tous les utilisateurs avec le rôle "club"
        print("\n=== UTILISATEURS AVEC RÔLE 'CLUB' ===")
        club_users = User.query.filter_by(role=UserRole.CLUB).all()
        if club_users:
            for user in club_users:
                print(f"Utilisateur club: {user.name} (ID: {user.id}, Club ID: {user.club_id}, Email: {user.email})")
                # Vérifier si le club associé existe
                if user.club_id:
                    club = Club.query.get(user.club_id)
                    if club:
                        print(f"  → Club associé: {club.name} (ID: {club.id})")
                    else:
                        print(f"  → PROBLÈME: Club avec ID {user.club_id} non trouvé!")
                else:
                    print("  → PROBLÈME: Cet utilisateur n'a pas de club_id défini!")
        else:
            print("Aucun utilisateur avec le rôle 'club' trouvé.")
            
        # Vérifier les relations entre les modèles
        print("\n=== VÉRIFICATION DES RELATIONS ENTRE MODÈLES ===")
        try:
            # Vérifier la relation club → joueurs
            if clubs:
                first_club = clubs[0]
                players = User.query.filter_by(club_id=first_club.id, role=UserRole.PLAYER).all()
                print(f"Club '{first_club.name}' (ID: {first_club.id}) a {len(players)} joueurs associés")
            
            # Vérifier la relation club → terrains
            if clubs:
                first_club = clubs[0]
                courts = Court.query.filter_by(club_id=first_club.id).all()
                print(f"Club '{first_club.name}' (ID: {first_club.id}) a {len(courts)} terrains associés")
            
            # Vérifier la relation club → followers
            if clubs:
                try:
                    first_club = clubs[0]
                    followers = first_club.followers.all()
                    print(f"Club '{first_club.name}' (ID: {first_club.id}) a {len(followers)} followers")
                except Exception as e:
                    print(f"ERREUR lors de la vérification des followers: {e}")
        except Exception as e:
            print(f"ERREUR lors de la vérification des relations: {e}")
        
        print("\n=== DIAGNOSTIC TERMINÉ ===")

if __name__ == "__main__":
    main()
