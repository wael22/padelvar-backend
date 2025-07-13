import os
import sys
from flask import Flask
from flask_cors import CORS
from werkzeug.security import generate_password_hash
from flask_migrate import Migrate

# Add src to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import extensions and blueprints
from models.database import db
from models.user import User
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.videos import videos_bp
from routes.clubs import clubs_bp
from routes.frontend import frontend_bp

def create_app():
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), 'static')
    )

    app.config['SECRET_KEY'] = 'padelvar_secret_key_2024_secure'
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Init extensions
    db.init_app(app)
    Migrate(app, db)

    # Enable CORS
    CORS(app, origins=["http://localhost:5173", "*"], supports_credentials=True)

    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(videos_bp, url_prefix='/api/videos')
    app.register_blueprint(clubs_bp, url_prefix='/api/clubs')
    app.register_blueprint(frontend_bp)

    # Health check
    @app.route('/api/health')
    def health_check():
        return {'status': 'OK', 'message': 'PadelVar API is running'}

    return app


app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Créer les tables
        db.create_all()

        # Créer un super admin par défaut s'il n'existe pas
        super_admin = User.query.filter_by(email='admin@padelvar.com').first()
        if not super_admin:
            super_admin = User(
                email='admin@padelvar.com',
                password_hash=generate_password_hash('admin123'),
                name='Super Admin',
                role='super_admin',
                credits_balance=1000
            )
            db.session.add(super_admin)
            db.session.commit()
            print("✅ Super admin créé: admin@padelvar.com / admin123")

    app.run(host='0.0.0.0', port=5000, debug=True)
