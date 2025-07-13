from datetime import datetime
from enum import Enum
from .database import db

class UserRole(Enum):
    SUPER_ADMIN = "super_admin"
    PLAYER = "player"
    CLUB = "club"

class User(db.Model):
    __tablename__ = "users"
    
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
    
    # Relations
    videos = db.relationship('Video', backref='owner', lazy=True, cascade='all, delete-orphan')
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'), nullable=True)
    club = db.relationship('Club', back_populates='users')

    def __repr__(self):
        return f'<User {self.email}>'

    def to_dict(self):
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

class Club(db.Model):
    __tablename__ = "clubs"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    users = db.relationship('User', back_populates='club', lazy=True)
    courts = db.relationship('Court', back_populates='club', lazy=True, cascade='all, delete-orphan')

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
    __tablename__ = "courts"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    qr_code = db.Column(db.String(255), unique=True, nullable=False)
    camera_url = db.Column(db.String(255), nullable=False, default='http://212.231.225.55:88/axis-cgi/mjpg/video.cgi')
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    club = db.relationship('Club', back_populates='courts')
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
    __tablename__ = "videos"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_url = db.Column(db.String(255), nullable=False)
    thumbnail_url = db.Column(db.String(255), nullable=True)
    duration = db.Column(db.Integer, nullable=True)  # en secondes
    file_size = db.Column(db.Integer, nullable=True)  # en bytes
    is_unlocked = db.Column(db.Boolean, default=False)
    credits_cost = db.Column(db.Integer, default=1)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    court_id = db.Column(db.Integer, db.ForeignKey('courts.id'), nullable=True)

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