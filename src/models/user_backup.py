
# padelvar-backend/src/models/user.py

from datetime import datetime
from enum import Enum
from .database import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event
import logging

# Logging
logger = logging.getLogger(__name__)

class UserRole(Enum):
    SUPER_ADMIN = "super_admin"
    PLAYER = "player"
    CLUB = "club"

class UserStatus(Enum):
    ACTIVE = "active"
    PENDING_VERIFICATION = "pending_verification"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"

class TransactionStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class NotificationType(Enum):
    VIDEO_READY = "video_ready"
    RECORDING_STARTED = "recording_started"
    RECORDING_STOPPED = "recording_stopped"
    CREDITS_ADDED = "credits_added"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    ACCOUNT_SUSPENDED = "account_suspended"
    SESSION_EXPIRED = "session_expired"
    SYSTEM_MAINTENANCE = "system_maintenance"

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
    status = db.Column(db.Enum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
    credits_balance = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)
    email_verified_at = db.Column(db.DateTime, nullable=True)
    google_id = db.Column(db.String(100), nullable=True, unique=True)  # ID Google pour l'authentification
    
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
            'status': self.status.value,
            'credits_balance': self.credits_balance,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'email_verified_at': self.email_verified_at.isoformat() if self.email_verified_at else None,
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
    
    # Champs de recording supprimés
    
    videos = db.relationship('Video', backref='court', lazy=True)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "club_id": self.club_id,
            "camera_url": self.camera_url, "qr_code": self.qr_code,
            "available": True
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
    cdn_migrated_at = db.Column(db.DateTime, nullable=True)  # Date de migration vers Bunny Stream
    bunny_video_id = db.Column(db.String(100), nullable=True)  # ID vidéo Bunny CDN
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
            "bunny_video_id": self.bunny_video_id,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "cdn_migrated_at": self.cdn_migrated_at.isoformat() if self.cdn_migrated_at else None
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
        """Vérifier si l'enregistrement a expiré
        
        L'enregistrement est considéré comme expiré dans les cas suivants:
        1. La durée planifiée est dépassée
        2. La durée maximale autorisée est dépassée
        3. Le statut indique que l'enregistrement n'est plus actif
        """
        # Si l'enregistrement n'est pas actif, il n'est pas expiré (déjà arrêté)
        if self.status != 'active':
            return False
            
        # Calcul du temps écoulé
        elapsed = self.get_elapsed_minutes()
        
        # Vérifier si la durée planifiée est dépassée
        planned_exceeded = elapsed >= self.planned_duration
        
        # Vérifier si la durée maximale autorisée est dépassée
        max_exceeded = elapsed >= self.max_duration
        
        # Vérifier si end_time est défini et dans le passé
        time_expired = False
        if self.end_time:
            time_expired = datetime.utcnow() >= self.end_time
            
        # L'enregistrement expire si l'une des conditions est remplie
        return planned_exceeded or max_exceeded or time_expired

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

class Transaction(db.Model):
    """Modèle pour gérer les transactions de paiement et d'achat de crédits"""
    __tablename__ = 'transaction'
    
    id = db.Column(db.Integer, primary_key=True)
    # Identifiant unique pour l'idempotence
    idempotency_key = db.Column(db.String(100), unique=True, nullable=True)
    
    # Relation utilisateur
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='transactions')
    
    # Type et détails de la transaction
    transaction_type = db.Column(db.String(50), nullable=False)  # 'credit_purchase', 'credit_usage', 'refund'
    package_name = db.Column(db.String(100), nullable=True)  # '10_credits', '50_credits', etc.
    credits_amount = db.Column(db.Integer, nullable=False)  # Nombre de crédits
    
    # Montant financier (en centimes pour éviter les problèmes de virgule)
    amount_cents = db.Column(db.Integer, nullable=True)  # Prix en centimes
    currency = db.Column(db.String(3), default='EUR')  # Code devise ISO
    
    # Statut et prestataire de paiement
    status = db.Column(db.Enum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING)
    payment_gateway = db.Column(db.String(50), nullable=True)  # 'stripe', 'paypal', etc.
    payment_gateway_id = db.Column(db.String(100), nullable=True)  # ID transaction chez le prestataire
    payment_intent_id = db.Column(db.String(100), nullable=True)  # Stripe Payment Intent ID
    
    # Métadonnées
    description = db.Column(db.Text, nullable=True)
    failure_reason = db.Column(db.Text, nullable=True)
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'idempotency_key': self.idempotency_key,
            'user_id': self.user_id,
            'transaction_type': self.transaction_type,
            'package_name': self.package_name,
            'credits_amount': self.credits_amount,
            'amount_euros': self.amount_cents / 100.0 if self.amount_cents else None,
            'currency': self.currency,
            'status': self.status.value,
            'payment_gateway': self.payment_gateway,
            'payment_gateway_id': self.payment_gateway_id,
            'description': self.description,
            'failure_reason': self.failure_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None
        }

class Notification(db.Model):
    """Modèle pour gérer les notifications utilisateur"""
    __tablename__ = 'notification'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relation utilisateur
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='notifications')
    
    # Contenu de la notification
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.Enum(NotificationType), nullable=False)
    
    # Statut et priorité
    is_read = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(10), default='normal')  # 'low', 'normal', 'high', 'urgent'
    
    # Métadonnées optionnelles pour des actions spécifiques
    related_resource_type = db.Column(db.String(50), nullable=True)  # 'video', 'transaction', 'recording'
    related_resource_id = db.Column(db.String(100), nullable=True)  # ID de la ressource liée
    
    # Actions possibles (pour les notifications interactives)
    action_url = db.Column(db.String(500), nullable=True)  # URL d'action (bouton dans la notification)
    action_label = db.Column(db.String(100), nullable=True)  # Texte du bouton
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)  # Date d'expiration de la notification
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type.value,
            'is_read': self.is_read,
            'is_archived': self.is_archived,
            'priority': self.priority,
            'related_resource_type': self.related_resource_type,
            'related_resource_id': self.related_resource_id,
            'action_url': self.action_url,
            'action_label': self.action_label,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
        
    def mark_as_read(self):
        """Marquer la notification comme lue"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()
            
    def is_expired(self):
        """Vérifier si la notification a expiré"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

class IdempotencyKey(db.Model):
    """Modèle pour gérer l'idempotence des requêtes critiques"""
    __tablename__ = 'idempotency_key'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Optionnel
    endpoint = db.Column(db.String(100), nullable=False)  # Endpoint concerné
    
    # Réponse stockée pour rejouer la même réponse
    response_status_code = db.Column(db.Integer, nullable=True)
    response_body = db.Column(db.Text, nullable=True)
    response_headers = db.Column(db.Text, nullable=True)  # JSON stringifié
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)  # Clé expire après 24h
    
    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'user_id': self.user_id,
            'endpoint': self.endpoint,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
        
    def is_expired(self):
        """Vérifier si la clé d'idempotence a expiré"""
        return datetime.utcnow() > self.expires_at

# ====================================================================
# CONFIGURATION DE LA SYNCHRONISATION BIDIRECTIONNELLE
# ====================================================================

# Synchronisation User -> Club
@event.listens_for(User, 'after_update')
def sync_user_to_club(mapper, connection, target):
    """Synchronise les changements d'un utilisateur club vers son club"""
    if target.role == UserRole.CLUB and target.club_id:
        try:
            # Cette fonction est appelée dans une transaction, on doit utiliser la session actuelle
            club = db.session.query(Club).get(target.club_id)
            if club:
                changed = False
                
                # Synchroniser les attributs
                if club.name != target.name:
                    club.name = target.name
                    changed = True
                
                if club.email != target.email:
                    club.email = target.email
                    changed = True
                
                if club.phone_number != target.phone_number:
                    club.phone_number = target.phone_number
                    changed = True
                
                # Log des changements
                if changed:
                    logger.info(f"Synchronisation User→Club: Club {club.id} mis à jour depuis User {target.id}")
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation User→Club: {e}")

# Synchronisation Club -> User
@event.listens_for(Club, 'after_update')
def sync_club_to_user(mapper, connection, target):
    """Synchronise les changements d'un club vers son utilisateur associé"""
    try:
        # Trouver l'utilisateur associé - on doit utiliser la session active
        user = db.session.query(User).filter_by(club_id=target.id, role=UserRole.CLUB).first()
        if user:
            changed = False
            
            # Synchroniser les attributs
            if user.name != target.name:
                user.name = target.name
                changed = True
            
            if user.email != target.email:
                user.email = target.email
                changed = True
            
            if user.phone_number != target.phone_number:
                user.phone_number = target.phone_number
                changed = True
            
            # Log des changements
            if changed:
                logger.info(f"Synchronisation Club→User: User {user.id} mis à jour depuis Club {target.id}")
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation Club→User: {e}")


# ====================================================================
# MODÈLES POUR L'ENREGISTREMENT VIDÉO
# ====================================================================

class RecordingStatus(Enum):
    IDLE = "idle"
    RECORDING = "recording"
    DONE = "done"
    ERROR = "error"

class Match(db.Model):
    """Modèle pour les matchs de padel avec enregistrement vidéo"""
    __tablename__ = 'match'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Informations du match
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    court_id = db.Column(db.Integer, db.ForeignKey('court.id'), nullable=False)
    
    # Joueurs (4 joueurs maximum pour un match de padel)
    player1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    player2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    player3_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    player4_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Timing
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    planned_duration_minutes = db.Column(db.Integer, default=90)
    
    # Enregistrement vidéo
    video_path = db.Column(db.String(500), nullable=True)
    recording_status = db.Column(db.Enum(RecordingStatus), default=RecordingStatus.IDLE)
    recording_started_at = db.Column(db.DateTime, nullable=True)
    recording_ended_at = db.Column(db.DateTime, nullable=True)
    video_file_size_mb = db.Column(db.Float, nullable=True)
    video_duration_seconds = db.Column(db.Integer, nullable=True)
    
    # Métadonnées
    title = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    club = db.relationship('Club', backref='matches')
    court = db.relationship('Court', backref='matches')
    player1 = db.relationship('User', foreign_keys=[player1_id], backref='matches_as_player1')
    player2 = db.relationship('User', foreign_keys=[player2_id], backref='matches_as_player2') 
    player3 = db.relationship('User', foreign_keys=[player3_id], backref='matches_as_player3')
    player4 = db.relationship('User', foreign_keys=[player4_id], backref='matches_as_player4')
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        return {
            'id': self.id,
            'club_id': self.club_id,
            'court_id': self.court_id,
            'player1_id': self.player1_id,
            'player2_id': self.player2_id,
            'player3_id': self.player3_id,
            'player4_id': self.player4_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'planned_duration_minutes': self.planned_duration_minutes,
            'video_path': self.video_path,
            'recording_status': self.recording_status.value if self.recording_status else 'idle',
            'recording_started_at': self.recording_started_at.isoformat() if self.recording_started_at else None,
            'recording_ended_at': self.recording_ended_at.isoformat() if self.recording_ended_at else None,
            'video_file_size_mb': self.video_file_size_mb,
            'video_duration_seconds': self.video_duration_seconds,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_all_players(self):
        """Obtenir tous les joueurs du match"""
        players = [self.player1, self.player2]
        if self.player3:
            players.append(self.player3)
        if self.player4:
            players.append(self.player4)
        return players
    
    def start_recording(self):
        """Marquer le début d'enregistrement"""
        self.recording_status = RecordingStatus.RECORDING
        self.recording_started_at = datetime.utcnow()
        
    def stop_recording(self, video_path=None, file_size_mb=None, duration_seconds=None):
        """Marquer la fin d'enregistrement"""
        self.recording_status = RecordingStatus.DONE
        self.recording_ended_at = datetime.utcnow()
        if video_path:
            self.video_path = video_path
        if file_size_mb:
            self.video_file_size_mb = file_size_mb
        if duration_seconds:
            self.video_duration_seconds = duration_seconds
    
    def mark_recording_error(self):
        """Marquer une erreur d'enregistrement"""
        self.recording_status = RecordingStatus.ERROR
        self.recording_ended_at = datetime.utcnow()


class VideoRecordingLog(db.Model):
    """Log des actions d'enregistrement vidéo"""
    __tablename__ = 'video_recording_log'
    
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)  # start, stop, error, etc.
    details = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    match = db.relationship('Match', backref='recording_logs')
    user = db.relationship('User', backref='recording_actions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'match_id': self.match_id,
            'action_type': self.action_type,
            'details': self.details,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
