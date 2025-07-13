# padelvar-backend/src/models/__init__.py
from .database import db
from .user import User, Club, Court, Video, UserRole

# Exporter tous les modèles pour un accès facile
__all__ = ['db', 'User', 'Club', 'Court', 'Video', 'UserRole']