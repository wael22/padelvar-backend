# padelvar-backend/src/config.py

import os

class Config:
    """Configuration de base."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'une-cle-secrete-difficile-a-deviner'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_HTTPONLY = True
    
    DEFAULT_ADMIN_EMAIL = os.environ.get('DEFAULT_ADMIN_EMAIL', 'admin@padelvar.com')
    DEFAULT_ADMIN_PASSWORD = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'password123')
    DEFAULT_ADMIN_NAME = 'Super Admin'
    DEFAULT_ADMIN_CREDITS = 10000

    @staticmethod
    def init_app(app):
        pass

    # ====================================================================
    # CORRECTION ICI : Ajout de @staticmethod et suppression de 'self'
    # ====================================================================
    @staticmethod
    def get_database_uri(app):
        """Retourne l'URI de la base de données."""
        return 'sqlite:///' + os.path.join(app.instance_path, 'app.db')

    def validate(self):
        """Valide que les variables critiques sont définies."""
        if not self.SECRET_KEY or self.SECRET_KEY == 'une-cle-secrete-difficile-a-deviner':
            raise ValueError("SECRET_KEY n'est pas définie ou est la valeur par défaut !")


class DevelopmentConfig(Config):
    """Configuration pour le développement."""
    DEBUG = True
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000"
    ]
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = None  # Pour le développement


class ProductionConfig(Config):
    """Configuration pour la production."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',')

    # ====================================================================
    # CORRECTION ICI : Ajout de @staticmethod et suppression de 'self'
    # ====================================================================
    @staticmethod
    def get_database_uri(app):
        """En production, utiliser une base de données plus robuste."""
        # On appelle directement la méthode statique de la classe parente
        return os.environ.get('DATABASE_URL') or Config.get_database_uri(app)


class TestingConfig(Config):
    """Configuration pour les tests."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    CORS_ORIGINS = "*"


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}