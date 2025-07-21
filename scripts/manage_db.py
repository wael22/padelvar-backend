#!/usr/bin/env python3
"""
Script de gestion de la base de données PadelVar
Usage: python scripts/manage_db.py [command]

Commandes disponibles:
- init: Initialise les migrations
- migrate: Crée une nouvelle migration
- upgrade: Applique les migrations
- downgrade: Annule la dernière migration
- reset: Remet à zéro la base de données
"""
import os
import sys
from pathlib import Path
import argparse
import shutil

# Ajouter le dossier racine au path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

from flask_migrate import init, migrate, upgrade, downgrade
from src.main import create_app

def init_migrations(app):
    """Initialise le système de migrations"""
    print("🔧 Initialisation des migrations...")
    
    with app.app_context():
        try:
            init()
            print("✅ Migrations initialisées")
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
            return False
    return True

def create_migration(app, message="Auto migration"):
    """Crée une nouvelle migration"""
    print(f"📝 Création d'une migration: {message}")
    
    with app.app_context():
        try:
            migrate(message=message)
            print("✅ Migration créée")
        except Exception as e:
            print(f"❌ Erreur lors de la création de la migration: {e}")
            return False
    return True

def apply_migrations(app):
    """Applique les migrations"""
    print("⬆️  Application des migrations...")
    
    with app.app_context():
        try:
            upgrade()
            print("✅ Migrations appliquées")
        except Exception as e:
            print(f"❌ Erreur lors de l'application des migrations: {e}")
            return False
    return True

def rollback_migration(app):
    """Annule la dernière migration"""
    print("⬇️  Annulation de la dernière migration...")
    
    with app.app_context():
        try:
            downgrade()
            print("✅ Migration annulée")
        except Exception as e:
            print(f"❌ Erreur lors de l'annulation: {e}")
            return False
    return True

def reset_database(app):
    """Remet à zéro la base de données"""
    print("🗑️  Remise à zéro de la base de données...")
    
    # Supprimer le fichier de base de données
    db_path = Path(app.instance_path) / 'app.db'
    if db_path.exists():
        db_path.unlink()
        print(f"🗑️  Base de données supprimée: {db_path}")
    
    # Supprimer le dossier migrations
    migrations_path = project_root / 'migrations'
    if migrations_path.exists():
        shutil.rmtree(migrations_path)
        print("🗑️  Dossier migrations supprimé")
    
    # Réinitialiser les migrations
    if init_migrations(app):
        # Créer une migration initiale
        if create_migration(app, "Initial migration"):
            # Appliquer la migration
            apply_migrations(app)
    
    print("✅ Base de données remise à zéro")

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description='Gestion de la base de données PadelVar')
    parser.add_argument('command', choices=['init', 'migrate', 'upgrade', 'downgrade', 'reset'],
                       help='Commande à exécuter')
    parser.add_argument('--message', '-m', default='Auto migration',
                       help='Message pour la migration (utilisé avec migrate)')
    
    args = parser.parse_args()
    
    print(f"🔧 Gestion de la base de données PadelVar - Commande: {args.command}")
    
    # Créer l'application
    app = create_app('development')
    
    # Exécuter la commande
    success = False
    
    if args.command == 'init':
        success = init_migrations(app)
    elif args.command == 'migrate':
        success = create_migration(app, args.message)
    elif args.command == 'upgrade':
        success = apply_migrations(app)
    elif args.command == 'downgrade':
        success = rollback_migration(app)
    elif args.command == 'reset':
        reset_database(app)
        success = True
    
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()

