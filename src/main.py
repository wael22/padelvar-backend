"""
Fichier principal de l'application PadelVar
Factory pattern pour créer l'instance Flask
"""
import os
from flask import Flask
from flask_cors import CORS
from werkzeug.security import generate_password_hash
from flask_migrate import Migrate

# Importations relatives corrigées
from .config import config
from .models.database import db
from .models.user import User, UserRole
from .routes.auth import auth_bp
from .routes.admin import admin_bp
from .routes.videos import videos_bp
from .routes.clubs import clubs_bp
from .routes.frontend import frontend_bp
from .routes.all_clubs import all_clubs_bp
from .routes.players import players_bp
from .routes.recording import recording_bp

def create_app(config_name=None):
    """
    Factory pour créer l'application Flask
    
    Args:
        config_name (str): Nom de la configuration à utiliser ('development', 'production', 'testing')
                          Par défaut, utilise la variable d'environnement FLASK_ENV ou 'development'
    
    Returns:
        Flask: Instance de l'application configurée
    """
    
    # Déterminer la configuration à utiliser
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    # Créer l'instance Flask
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), 'static'),
        instance_relative_config=True
    )
    
    # Charger la configuration
    app.config.from_object(config[config_name])
    
    # S'assurer que le dossier instance existe
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass
    
    # Configuration de la base de données avec le chemin correct
    if config_name != 'testing':
        app.config['SQLALCHEMY_DATABASE_URI'] = config[config_name].get_database_uri(app)
    
    # Validation de la configuration en production
    if config_name == 'production':
        config[config_name].validate()
    
    # Initialisation des extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Configuration CORS
    CORS(app, 
         origins=app.config['CORS_ORIGINS'], 
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    # Enregistrement des blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(videos_bp, url_prefix='/api/videos')
    app.register_blueprint(clubs_bp, url_prefix='/api/clubs')
    app.register_blueprint(frontend_bp)
    app.register_blueprint(all_clubs_bp, url_prefix='/api/all-clubs')
    app.register_blueprint(players_bp, url_prefix='/api/players')
    app.register_blueprint(recording_bp, url_prefix='/api/recording')
    
    # Route de test pour le développement
    if config_name == 'development':
        @app.route('/test')
        def test_page():
            """Page de test d'authentification"""
            from flask import send_from_directory
            import os
            test_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_auth.html')
            if os.path.exists(test_file_path):
                return send_from_directory(os.path.dirname(test_file_path), 'test_auth.html')
            else:
                return """
                <html><body>
                <h1>Page de test PadelVar</h1>
                <p>Fichier test_auth.html non trouvé.</p>
                <p>Essayez d'accéder directement au fichier test_auth.html dans le répertoire backend.</p>
                </body></html>
                """
    
    # Routes de base
    @app.route('/api/health')
    def health_check():
        """Point de contrôle de santé de l'API"""
        return {
            'status': 'OK', 
            'message': 'PadelVar API is running',
            'environment': config_name
        }
    
    @app.route('/')
    def index():
        """Page d'accueil de l'API"""
        return {
            'message': 'Bienvenue sur l\'API PadelVar',
            'version': '1.0.0',
            'endpoints': {
                'health': '/api/health',
                'auth': '/api/auth',
                'admin': '/api/admin',
                'videos': '/api/videos',
                'clubs': '/api/clubs',
                'players': '/api/players'
            }
        }
    
    # Initialisation de la base de données et création de l'admin
    # Uniquement en mode développement et si la base n'existe pas
    if config_name == 'development':
        with app.app_context():
            # Créer toutes les tables
            db.create_all()
            
            # Créer l'admin par défaut s'il n'existe pas
            _create_default_admin(app)
    
    return app

def _create_default_admin(app):
    """
    Crée l'administrateur par défaut s'il n'existe pas
    
    Args:
        app: Instance Flask avec contexte d'application actif
    """
    try:
        admin_email = app.config['DEFAULT_ADMIN_EMAIL']
        super_admin = User.query.filter_by(email=admin_email).first()
        
        if not super_admin:
            super_admin = User(
                email=admin_email,
                password_hash=generate_password_hash(app.config['DEFAULT_ADMIN_PASSWORD']),
                name=app.config['DEFAULT_ADMIN_NAME'],
                role=UserRole.SUPER_ADMIN,
                credits_balance=app.config['DEFAULT_ADMIN_CREDITS']
            )
            db.session.add(super_admin)
            db.session.commit()
            
            print(f"✅ Super admin créé: {admin_email} / {app.config['DEFAULT_ADMIN_PASSWORD']}")
        else:
            print(f"ℹ️  Super admin existe déjà: {admin_email}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'admin: {e}")
        db.session.rollback()

def init_db(app):
    """
    Initialise la base de données avec les tables
    Fonction utilitaire pour les scripts d'initialisation
    
    Args:
        app: Instance Flask
    """
    with app.app_context():
        db.create_all()
        print("✅ Base de données initialisée")

def create_admin(app, email, password, name="Admin"):
    """
    Crée un administrateur
    Fonction utilitaire pour les scripts d'administration
    
    Args:
        app: Instance Flask
        email (str): Email de l'administrateur
        password (str): Mot de passe
        name (str): Nom de l'administrateur
    """
    with app.app_context():
        existing_admin = User.query.filter_by(email=email).first()
        if existing_admin:
            print(f"❌ Un utilisateur avec l'email {email} existe déjà")
            return False
        
        admin = User(
            email=email,
            password_hash=generate_password_hash(password),
            name=name,
            role=UserRole.SUPER_ADMIN,
            credits_balance=1000
        )
        
        db.session.add(admin)
        db.session.commit()
        print(f"✅ Administrateur créé: {email}")
        return True

