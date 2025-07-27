# padelvar-backend/src/models/user.py

from datetime import datetime
from enum import Enum
from .database import db
from werkzeug.security import generate_password_hash, check_password_hash

# --- Énumérations pour les Rôles et Actions ---

class UserRole(Enum):
    SUPER_ADMIN = "super_admin"
    PLAYER = "player"
    CLUB = "club"

# --- Table d'Association pour les Joueurs qui suivent des Clubs ---

player_club_follows = db.Table(
    'player_club_follows',
    db.Column('player_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('club_id', db.Integer, db.ForeignKey('club.id'), primary_key=True)
)

# --- Modèle Principal : User ---

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
    
    # Relation avec les vidéos
    videos = db.relationship('Video', backref='owner', lazy=True, cascade='all, delete-orphan')
    
    # Relation avec le club (pour les joueurs inscrits et les comptes club)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=True)
    
    # Relation avec les clubs suivis (pour les joueurs)
    followed_clubs = db.relationship('Club', 
                                   secondary=player_club_follows,
                                   backref=db.backref('followers', lazy='dynamic'),
                                   lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'phone_number': self.phone_number,
            'role': self.role.value,
            'credits_balance': self.credits_balance,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'club_id': self.club_id
        }

# --- Modèle : Club ---

class Club(db.Model):
    __tablename__ = 'club'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relation avec les joueurs et les terrains
    players = db.relationship('User', backref='club', lazy=True)
    courts = db.relationship('Court', backref='club', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'phone_number': self.phone_number,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# --- Modèle : Court (Terrain) ---

class Court(db.Model):
    __tablename__ = 'court'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    qr_code = db.Column(db.String(100), unique=True, nullable=False)
    camera_url = db.Column(db.String(255), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    
    videos = db.relationship('Video', backref='court', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'qr_code': self.qr_code,
            'camera_url': self.camera_url,
            'club_id': self.club_id
        }

# --- Modèle : Video ---

class Video(db.Model):
    __tablename__ = 'video'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_url = db.Column(db.String(255), nullable=False)
    is_unlocked = db.Column(db.Boolean, default=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    court_id = db.Column(db.Integer, db.ForeignKey('court.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'file_url': self.file_url,
            'is_unlocked': self.is_unlocked,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'user_id': self.user_id,
            'court_id': self.court_id
        }

# --- Modèle : ClubActionHistory ---

class ClubActionHistory(db.Model):
    __tablename__ = 'club_action_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=True)
    performed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)
    action_details = db.Column(db.Text, nullable=True)
    performed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id], backref='actions_suffered')
    club = db.relationship('Club', backref='history_actions')
    performed_by = db.relationship('User', foreign_keys=[performed_by_id], backref='actions_performed')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'club_id': self.club_id,
            'performed_by_id': self.performed_by_id,
            'action_type': self.action_type,
            'action_details': self.action_details,
            'performed_at': self.performed_at.isoformat() if self.performed_at else None
        }
