"""
Script pour initialiser la base de données avec des données de test plus complètes.
Ce script va créer des utilisateurs, clubs, terrains, vidéos et historiques de manière
cohérente pour s'assurer que toutes les relations fonctionnent correctement.
"""
import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
import json
from enum import Enum
from datetime import datetime, timedelta
import random

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
        description = db.Column(db.Text, nullable=True)
        file_url = db.Column(db.String(255), nullable=True)
        thumbnail_url = db.Column(db.String(255), nullable=True)
        duration = db.Column(db.Integer, nullable=True)
        is_unlocked = db.Column(db.Boolean, default=True)
        credits_cost = db.Column(db.Integer, default=1)
        recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        court_id = db.Column(db.Integer, db.ForeignKey('court.id'), nullable=True)
    
    class ClubActionHistory(db.Model):
        __tablename__ = 'club_action_history'
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=True)
        performed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        action_type = db.Column(db.String(50), nullable=False)
        action_details = db.Column(db.Text, nullable=True)
        performed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


# Fonction pour créer des données de test complètes
def create_test_data(club_user_email=None):
    """
    Crée des données de test complètes avec relations pour le tableau de bord.
    Si club_user_email est fourni, utilise ce club existant, sinon crée un nouveau club.
    """
    try:
        # 1. Récupérer ou créer un club utilisateur
        club_user = None
        club = None
        
        if club_user_email:
            club_user = User.query.filter_by(email=club_user_email).first()
            if club_user and club_user.club_id:
                club = Club.query.get(club_user.club_id)
                print(f"Utilisation du club existant: {club.name} (ID: {club.id})")
        
        if not club:
            # Créer un nouveau club et utilisateur associé
            club_name = f"Club Test {random.randint(1000, 9999)}"
            club_email = f"club{random.randint(1000, 9999)}@example.com"
            
            # Créer l'entité Club
            club = Club(
                name=club_name,
                address="123 rue de Test, 75000 Paris",
                phone_number="01 23 45 67 89",
                email=club_email
            )
            db.session.add(club)
            db.session.flush()  # Pour obtenir l'ID du club
            
            # Créer l'utilisateur Club associé
            club_user = User(
                email=club_email,
                name=club_name,
                password_hash=generate_password_hash("password123"),
                role=UserRole.CLUB,
                club_id=club.id
            )
            db.session.add(club_user)
            print(f"Nouveau club créé: {club.name} (ID: {club.id})")
        
        # 2. Créer des terrains pour le club
        courts = []
        for i in range(1, 4):  # 3 terrains
            court_name = f"Terrain {i}"
            
            # Vérifier si le terrain existe déjà
            existing_court = Court.query.filter_by(club_id=club.id, name=court_name).first()
            if not existing_court:
                court = Court(
                    club_id=club.id,
                    name=court_name,
                    qr_code=f"QR_TERRAIN_{club.id}_{i}_{random.randint(1000, 9999)}",
                    camera_url=f"http://exemple.com/camera/{club.id}/{i}"
                )
                db.session.add(court)
                courts.append(court)
                print(f"Terrain créé: {court_name}")
            else:
                courts.append(existing_court)
                print(f"Terrain existant: {court_name}")
        
        # Commit pour avoir les IDs des terrains
        db.session.commit()
        
        # 3. Créer des joueurs associés au club
        players = []
        for i in range(1, 6):  # 5 joueurs
            player_email = f"joueur{i}_{club.id}_{random.randint(1000, 9999)}@example.com"
            
            # Vérifier si le joueur existe déjà
            existing_player = User.query.filter_by(email=player_email).first()
            if not existing_player:
                player = User(
                    email=player_email,
                    name=f"Joueur {i} du club {club.id}",
                    password_hash=generate_password_hash("password123"),
                    role=UserRole.PLAYER,
                    club_id=club.id,
                    credits_balance=10
                )
                db.session.add(player)
                players.append(player)
                
                # Créer une entrée d'historique pour l'ajout du joueur
                history_entry = ClubActionHistory(
                    user_id=player.id,
                    club_id=club.id,
                    performed_by_id=club_user.id,
                    action_type='add_player',
                    action_details=json.dumps({
                        'player_name': player.name,
                        'player_email': player.email
                    }),
                    performed_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                )
                db.session.add(history_entry)
                print(f"Joueur créé: {player.name}")
            else:
                players.append(existing_player)
                print(f"Joueur existant: {existing_player.name}")
        
        # Commit pour avoir les IDs des joueurs
        db.session.commit()
        
        # 4. Créer des entrées pour les crédits
        for player in players:
            # Ajouter des crédits plusieurs fois avec différentes valeurs
            for _ in range(random.randint(1, 3)):
                credits_to_add = random.randint(5, 20)
                
                history_entry = ClubActionHistory(
                    user_id=player.id,
                    club_id=club.id,
                    performed_by_id=club_user.id,
                    action_type='add_credits',
                    action_details=json.dumps({
                        'credits_added': credits_to_add,
                        'player_name': player.name
                    }),
                    performed_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                )
                db.session.add(history_entry)
                print(f"Ajout de {credits_to_add} crédits à {player.name}")
        
        # 5. Créer des vidéos associées aux terrains
        for court in courts:
            for player in players[:3]:  # Limiter à 3 joueurs par terrain pour la lisibilité
                # Créer 1 à 3 vidéos par joueur et par terrain
                for i in range(random.randint(1, 3)):
                    video = Video(
                        title=f"Match de {player.name} sur {court.name} #{i+1}",
                        description=f"Description de la vidéo {i+1} pour {player.name}",
                        file_url=f"http://exemple.com/videos/{club.id}/{court.id}/{player.id}/{i+1}.mp4",
                        thumbnail_url=f"http://exemple.com/thumbnails/{club.id}/{court.id}/{player.id}/{i+1}.jpg",
                        duration=random.randint(300, 3600),  # 5 minutes à 1 heure
                        is_unlocked=random.choice([True, False]),
                        credits_cost=random.randint(1, 5),
                        recorded_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                        created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                        user_id=player.id,
                        court_id=court.id
                    )
                    db.session.add(video)
                    print(f"Vidéo créée: {video.title}")
        
        # 6. Créer des followers pour le club
        # Créer quelques joueurs externes (qui ne sont pas membres du club)
        external_players = []
        for i in range(1, 4):  # 3 joueurs externes
            player_email = f"externe{i}_{random.randint(1000, 9999)}@example.com"
            
            # Vérifier si le joueur existe déjà
            existing_player = User.query.filter_by(email=player_email).first()
            if not existing_player:
                player = User(
                    email=player_email,
                    name=f"Joueur Externe {i}",
                    password_hash=generate_password_hash("password123"),
                    role=UserRole.PLAYER,
                    credits_balance=5
                    # Pas de club_id pour les joueurs externes
                )
                db.session.add(player)
                external_players.append(player)
                print(f"Joueur externe créé: {player.name}")
            else:
                external_players.append(existing_player)
                print(f"Joueur externe existant: {existing_player.name}")
        
        db.session.commit()
        
        # Faire suivre le club par tous les joueurs (membres et externes)
        all_players = players + external_players
        for player in all_players:
            if club not in player.followed_clubs.all():
                player.followed_clubs.append(club)
                print(f"{player.name} suit maintenant le club {club.name}")
        
        # Commit final
        db.session.commit()
        
        return {
            'success': True,
            'club': {
                'id': club.id,
                'name': club.name,
                'email': club.email
            },
            'stats': {
                'courts_created': len(courts),
                'players_created': len(players),
                'external_players_created': len(external_players),
                'followers_count': len(all_players)
            }
        }
        
    except Exception as e:
        db.session.rollback()
        print(f"ERREUR lors de la création des données de test: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def main():
    with app.app_context():
        print("=== Initialisation de la base de données avec des données de test ===")
        
        # Demander si l'utilisateur veut utiliser un club existant
        use_existing = input("Voulez-vous utiliser un club existant? (o/n): ").lower() == 'o'
        
        club_email = None
        if use_existing:
            # Lister tous les clubs
            clubs = Club.query.all()
            if clubs:
                print("\nListe des clubs existants:")
                for i, club in enumerate(clubs):
                    users = User.query.filter_by(club_id=club.id, role=UserRole.CLUB).all()
                    club_emails = [user.email for user in users]
                    print(f"{i+1}. {club.name} (ID: {club.id}, Emails: {', '.join(club_emails)})")
                
                club_idx = int(input("\nChoisissez un club par son numéro: ")) - 1
                if 0 <= club_idx < len(clubs):
                    selected_club = clubs[club_idx]
                    club_user = User.query.filter_by(club_id=selected_club.id, role=UserRole.CLUB).first()
                    if club_user:
                        club_email = club_user.email
            else:
                print("Aucun club existant trouvé. Un nouveau club sera créé.")
        
        # Créer les données de test
        result = create_test_data(club_email)
        
        if result['success']:
            print("\n=== Données de test créées avec succès ===")
            print(f"Club: {result['club']['name']} (ID: {result['club']['id']})")
            print(f"Email du club: {result['club']['email']} (Mot de passe: password123)")
            print("\nStatistiques:")
            for key, value in result['stats'].items():
                print(f"- {key}: {value}")
            
            print("\nUtilisez ces informations pour vous connecter à l'application.")
        else:
            print(f"\nÉCHEC de la création des données: {result['error']}")

if __name__ == "__main__":
    main()
