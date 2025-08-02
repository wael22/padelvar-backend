#!/usr/bin/env python3
"""
Script simple pour démarrer le serveur Flask
"""
import sys
import os
from pathlib import Path

# Ajouter le chemin du projet
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Importer et démarrer l'application
from src.main import create_app

if __name__ == "__main__":
    print("🚀 Démarrage du serveur PadelVar...")
    
    # Configuration
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    try:
        # Créer l'application
        app = create_app('development')
        print("✅ Application créée avec succès")
        
        # Démarrer le serveur
        print("🌐 Serveur disponible sur: http://localhost:5000")
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)
