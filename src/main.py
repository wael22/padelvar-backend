import os
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from datetime import timedelta

# 1. Importer l'instance db centralisée
from src.models.database import db

# 2. Importer tous vos blueprints avec le chemin complet depuis src
from src.routes.auth import auth_bp
from src.routes.admin import admin_bp
from src.routes.videos import videos_bp
from src.routes.clubs import clubs_bp
from src.routes.frontend import frontend_bp
from src.routes.all_clubs import all_clubs_bp
from src.routes.players import players_bp

def create_app():
    """Crée et configure l'instance de l'application Flask."""
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), 'static')
    )

    # Configuration de l'application
    app.config['SECRET_KEY'] = 'padelvar_secret_key_2024_secure'
    # Construit le chemin absolu vers la base de données
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configuration des sessions
    app.config['SESSION_COOKIE_SECURE'] = False  # True en production avec HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Permet les requêtes cross-origin
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # Session de 24h
    app.config['SESSION_COOKIE_NAME'] = 'padelvar_session'

    # 3. Initialiser les extensions avec l'application
    db.init_app(app)
    Migrate(app, db)
    
    # Configuration CORS corrigée
    CORS(app, 
         origins=["http://localhost:5173", "http://127.0.0.1:5173"], 
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

    # 4. Enregistrer les Blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(videos_bp, url_prefix='/api/videos')
    app.register_blueprint(clubs_bp, url_prefix='/api/clubs')
    app.register_blueprint(frontend_bp)
    app.register_blueprint(all_clubs_bp, url_prefix='/api/all-clubs') # Changement de préfixe pour éviter conflit
    app.register_blueprint(players_bp, url_prefix='/api/players')

    # Route de santé
    @app.route('/api/health')
    def health_check():
        return {'status': 'OK', 'message': 'PadelVar API is running'}

    return app