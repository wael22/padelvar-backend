# padelvar-backend/src/models/user.py

from datetime import datetime
from enum import Enum
## Suppression de l'import enum
from .database import db
from werkzeug.security import generate_password_hash, check_password_hash

# --- Énumérations pour les Rôles et Actions ---

class UserRole(Enum):
    SUPER_ADMIN = "super_admin"
    PLAYER = "player"
    CLUB = "club"

# --- Table d'Association pour les Joueurs qui suivent des Clubs ---


from datetime import datetime
from enum import Enum
from .database import db
from werkzeug.security import generate_password_hash, check_password_hash

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
    
    videos = db.relationship('Video', backref='owner', lazy=True, cascade='all, delete-orphan')
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=True)
    
    followed_clubs = db.relationship('Club', 
                                   secondary=player_club_follows,
                                   backref=db.backref('followers', lazy='dynamic'),
                                   lazy='dynamic')

    def to_dict(self):
        user_dict = {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'phone_number': self.phone_number,
            'role': self.role.value,
            'credits_balance': self.credits_balance,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'club_id': self.club_id
        }
        if self.role == UserRole.CLUB and self.club_id:
            club = Club.query.get(self.club_id)
            if club:
                user_dict['club'] = club.to_dict()
        return user_dict

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
            'id': self.id, 'name': self.name, 'address': self.address,
            'phone_number': self.phone_number, 'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Court(db.Model):
    __tablename__ = 'court'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    qr_code = db.Column(db.String(100), unique=True, nullable=False)
    camera_url = db.Column(db.String(255), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    
    # Nouveau : statut d'occupation pour l'enregistrement
    is_recording = db.Column(db.Boolean, default=False)
    recording_session_id = db.Column(db.String(100), nullable=True)
    current_recording_id = db.Column(db.String(100), nullable=True)
    
    videos = db.relationship('Video', backref='court', lazy=True)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "club_id": self.club_id,
            "camera_url": self.camera_url, "qr_code": self.qr_code,
            "is_recording": self.is_recording,
            "recording_session_id": self.recording_session_id,
            "current_recording_id": self.current_recording_id,
            "available": not self.is_recording
        }

class Video(db.Model):
    __tablename__ = 'video'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_url = db.Column(db.String(255), nullable=True)
    thumbnail_url = db.Column(db.String(255), nullable=True)
    duration = db.Column(db.Integer, nullable=True)
    file_size = db.Column(db.Integer, nullable=True)  # Taille du fichier en octets
    is_unlocked = db.Column(db.Boolean, default=True)
    credits_cost = db.Column(db.Integer, default=1)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    court_id = db.Column(db.Integer, db.ForeignKey('court.id'), nullable=True)
    
    # Relations (en utilisant les backrefs existants)
    # user = défini via backref='owner' dans User.videos
    # court = défini via backref='court' dans Court.videos

    def to_dict(self):
        return {
            "id": self.id, "user_id": self.user_id, "court_id": self.court_id,
            "file_url": self.file_url, "thumbnail_url": self.thumbnail_url,
            "title": self.title, "description": self.description, "duration": self.duration,
            "file_size": self.file_size, "is_unlocked": self.is_unlocked, "credits_cost": self.credits_cost,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class RecordingSession(db.Model):
    """Modèle pour gérer les sessions d'enregistrement en cours"""
    __tablename__ = 'recording_session'
    id = db.Column(db.Integer, primary_key=True)
    recording_id = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    court_id = db.Column(db.Integer, db.ForeignKey('court.id'), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    
    # Durée et timing
    planned_duration = db.Column(db.Integer, nullable=False)  # en minutes
    max_duration = db.Column(db.Integer, default=200)  # limite max en minutes
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    
    # Statut
    status = db.Column(db.String(20), default='active')  # active, stopped, completed, expired
    stopped_by = db.Column(db.String(20), nullable=True)  # player, club, auto
    
    # Métadonnées
    title = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    user = db.relationship('User', backref='recording_sessions')
    court = db.relationship('Court', backref='recording_sessions')
    club = db.relationship('Club', backref='recording_sessions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'recording_id': self.recording_id,
            'user_id': self.user_id,
            'court_id': self.court_id,
            'club_id': self.club_id,
            'planned_duration': self.planned_duration,
            'max_duration': self.max_duration,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'stopped_by': self.stopped_by,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'elapsed_minutes': self.get_elapsed_minutes(),
            'remaining_minutes': self.get_remaining_minutes(),
            'is_expired': self.is_expired()
        }
    
    def get_elapsed_minutes(self):
        """Calculer le temps écoulé en minutes"""
        if not self.start_time:
            return 0
        end_time = self.end_time or datetime.utcnow()
        delta = end_time - self.start_time
        return int(delta.total_seconds() / 60)
    
    def get_remaining_minutes(self):
        """Calculer le temps restant en minutes"""
        if self.status != 'active':
            return 0
        elapsed = self.get_elapsed_minutes()
        return max(0, self.planned_duration - elapsed)
    
    def is_expired(self):
        """Vérifier si l'enregistrement a expiré"""
        if self.status != 'active':
            return False
        elapsed = self.get_elapsed_minutes()
        return elapsed >= self.planned_duration

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
