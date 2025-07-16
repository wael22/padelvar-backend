from datetime import datetime
from enum import Enum
import traceback

from .database import db

class UserRole(Enum):
    SUPER_ADMIN = "super_admin"
    PLAYER = "player"
    CLUB = "club"

class ActionType(Enum):
    FOLLOW_CLUB = "follow_club"
    UNFOLLOW_CLUB = "unfollow_club"
    UPDATE_PLAYER = "update_player"
    ADD_CREDITS = "add_credits"
    CREATE_PLAYER = "create_player"
    DELETE_PLAYER = "delete_player"

# Table d'association pour les joueurs qui suivent des clubs
player_club_follows = db.Table(
    'player_club_follows',
    db.Column('player_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('club_id', db.Integer, db.ForeignKey('club.id'), primary_key=True),
    db.Column('followed_at', db.DateTime, default=datetime.utcnow),
    extend_existing=True
)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    profile_photo_url = db.Column(db.String(255), nullable=True)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.PLAYER)
    credits_balance = db.Column(db.Integer, default=0)
    google_id = db.Column(db.String(100), nullable=True)
    facebook_id = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    videos = db.relationship('Video', backref='owner', lazy=True, cascade='all, delete-orphan')
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=True)
    
    followed_clubs = db.relationship('Club', 
                                   secondary=player_club_follows,
                                   backref=db.backref('followers', lazy='dynamic'),
                                   lazy='dynamic')

    def __repr__(self):
        return f'<User {self.email}>'

    def to_dict(self):
        try:
            return {
                'id': self.id,
                'email': self.email,
                'name': self.name,
                'phone_number': self.phone_number,
                'profile_photo_url': self.profile_photo_url,
                'role': self.role.value,
                'credits_balance': self.credits_balance,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'club_id': self.club_id
            }
        except Exception as e:
            print(f"Erreur lors de la sérialisation de l'utilisateur en dictionnaire: {e}")
            traceback.print_exc()
            return {'error': 'Erreur de sérialisation de l\'utilisateur'}

class Club(db.Model):
    __tablename__ = 'club'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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

class Court(db.Model):
    __tablename__ = 'court'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    qr_code = db.Column(db.String(255), unique=True, nullable=False)
    camera_url = db.Column(db.String(255), nullable=False, default='http://212.231.225.55:88/axis-cgi/mjpg/video.cgi')
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    videos = db.relationship('Video', backref='court', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'qr_code': self.qr_code,
            'camera_url': self.camera_url,
            'club_id': self.club_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Video(db.Model):
    __tablename__ = 'video'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_url = db.Column(db.String(255), nullable=False)
    thumbnail_url = db.Column(db.String(255), nullable=True)
    duration = db.Column(db.Integer, nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    is_unlocked = db.Column(db.Boolean, default=False)
    credits_cost = db.Column(db.Integer, default=1)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    court_id = db.Column(db.Integer, db.ForeignKey('court.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'file_url': self.file_url,
            'thumbnail_url': self.thumbnail_url,
            'duration': self.duration,
            'file_size': self.file_size,
            'is_unlocked': self.is_unlocked,
            'credits_cost': self.credits_cost,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_id': self.user_id,
            'court_id': self.court_id
        }

class ClubHistory(db.Model):
    __tablename__ = 'club_history'
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action_type = db.Column(db.Enum(ActionType), nullable=False)
    action_details = db.Column(db.Text, nullable=True)
    performed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    performed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    club = db.relationship('Club', backref='history')
    player = db.relationship('User', foreign_keys=[player_id], backref='player_history')
    performed_by = db.relationship('User', foreign_keys=[performed_by_id], backref='performed_actions')

    def to_dict(self):
        return {
            'id': self.id,
            'club_id': self.club_id,
            'player_id': self.player_id,
            'action_type': self.action_type.value,
            'action_details': self.action_details,
            'performed_by_id': self.performed_by_id,
            'performed_at': self.performed_at.isoformat() if self.performed_at else None,
            'club_name': self.club.name if self.club else None,
            'player_name': self.player.name if self.player else None,
            'performed_by_name': self.performed_by.name if self.performed_by else None
        }


