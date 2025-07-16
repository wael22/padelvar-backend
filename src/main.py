import os
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate

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

    # 3. Initialiser les extensions avec l'application
    db.init_app(app)
    Migrate(app, db)
    CORS(app, origins=["http://localhost:5173", "*"], supports_credentials=True)

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