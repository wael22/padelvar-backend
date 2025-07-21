"""
Configuration centralisée pour l'application PadelVar
"""
import os
from pathlib import Path

class Config:
    """Configuration de base"""
    
    # Clé secrète - à définir via variable d'environnement en production
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'padelvar_secret_key_2024_secure'
    
    # Configuration de la base de données
    # Utilise le dossier instance de Flask pour stocker la base de données
    @staticmethod
    def get_database_uri(app):
        """Retourne l'URI de la base de données basée sur le dossier instance de l'app"""
        db_path = os.path.join(app.instance_path, 'app.db')
        return f'sqlite:///{db_path}'
    
    # Configuration SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.environ.get('SQLALCHEMY_ECHO', 'False').lower() == 'true'
    
    # Configuration CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5173').split(',')
    
    # Configuration de l'admin par défaut
    DEFAULT_ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@padelvar.com')
    DEFAULT_ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    DEFAULT_ADMIN_NAME = os.environ.get('ADMIN_NAME', 'Super Admin')
    DEFAULT_ADMIN_CREDITS = int(os.environ.get('ADMIN_CREDITS', '1000'))

class DevelopmentConfig(Config):
    """Configuration pour le développement"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Configuration pour la production"""
    DEBUG = False
    # En production, la clé secrète DOIT être définie via variable d'environnement
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    @classmethod
    def validate(cls):
        """Valide que la configuration de production est correcte"""
        if not cls.SECRET_KEY:
            raise ValueError("SECRET_KEY doit être définie en production")

class TestingConfig(Config):
    """Configuration pour les tests"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Dictionnaire des configurations disponibles
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

