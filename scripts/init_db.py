#!/usr/bin/env python3
"""
Script d'initialisation de la base de données PadelVar
Usage: python scripts/init_db.py
"""
import os
import sys
from pathlib import Path

# Ajouter le dossier racine au path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

from src.main import create_app, init_db

def main():
    """Initialise la base de données"""
    print("🔧 Initialisation de la base de données PadelVar")
    
    # Créer l'application
    app = create_app('development')
    
    # Initialiser la base de données
    init_db(app)
    
    print("✅ Base de données initialisée avec succès")
    print(f"📁 Fichier de base de données: {os.path.join(app.instance_path, 'app.db')}")

if __name__ == '__main__':
    main()

