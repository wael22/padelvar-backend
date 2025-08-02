#!/usr/bin/env python3
"""
Script pour appliquer la migration 'cdn_migrated_at' 
Ce script ajoute la colonne cdn_migrated_at à la table video
"""

import os
import sys
import logging
from datetime import datetime

# Configurer le logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ajouter le répertoire parent au chemin Python pour pouvoir importer l'application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importer les modules de l'application
from src.main import create_app
from flask_migrate import upgrade

def apply_cdn_migration():
    """Applique la migration pour la colonne cdn_migrated_at"""
    try:
        app = create_app()
        with app.app_context():
            logger.info("Démarrage de la migration...")
            upgrade(revision='add_cdn_migrated_at')
            logger.info("✅ Migration terminée avec succès!")
            return True
    except Exception as e:
        logger.error(f"❌ Erreur lors de la migration: {str(e)}")
        return False

if __name__ == "__main__":
    success = apply_cdn_migration()
    sys.exit(0 if success else 1)
