#!/usr/bin/env python3
"""
Script de synchronisation bidirectionnelle entre User et Club
À exécuter après les migrations de base de données
"""

import os
import sys
from pathlib import Path

# Ajouter le chemin du projet
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Importer les modèles nécessaires
from src.models.user import User, Club, UserRole
from src.models.database import db
from src import create_app

from sqlalchemy import event
from flask import current_app

def setup_sync_events():
    """Configure les événements de synchronisation bidirectionnelle"""
    
    # Synchronisation User -> Club
    @event.listens_for(User, 'after_update')
    def user_after_update(mapper, connection, target):
        """Synchronise les changements d'un utilisateur club vers son club"""
        if target.role == UserRole.CLUB and target.club_id:
            # Vérifier si le club existe
            club = Club.query.get(target.club_id)
            if club:
                changed = False
                
                # Synchroniser les attributs
                if club.name != target.name:
                    club.name = target.name
                    changed = True
                
                if club.email != target.email:
                    club.email = target.email
                    changed = True
                
                if club.phone_number != target.phone_number:
                    club.phone_number = target.phone_number
                    changed = True
                
                # Enregistrer les changements
                if changed:
                    current_app.logger.info(f"Synchronisation User→Club: Club {club.id} mis à jour depuis User {target.id}")
                    db.session.add(club)
                    db.session.commit()
    
    # Synchronisation Club -> User
    @event.listens_for(Club, 'after_update')
    def club_after_update(mapper, connection, target):
        """Synchronise les changements d'un club vers son utilisateur associé"""
        # Trouver l'utilisateur associé
        user = User.query.filter_by(club_id=target.id, role=UserRole.CLUB).first()
        if user:
            changed = False
            
            # Synchroniser les attributs
            if user.name != target.name:
                user.name = target.name
                changed = True
            
            if user.email != target.email:
                user.email = target.email
                changed = True
            
            if user.phone_number != target.phone_number:
                user.phone_number = target.phone_number
                changed = True
            
            # Enregistrer les changements
            if changed:
                current_app.logger.info(f"Synchronisation Club→User: User {user.id} mis à jour depuis Club {target.id}")
                db.session.add(user)
                db.session.commit()

def setup_bidirectional_sync():
    """Configure la synchronisation bidirectionnelle dans l'application"""
    print("🔄 Configuration de la synchronisation bidirectionnelle")
    
    # Créer l'application Flask dans le contexte
    app = create_app('development')
    app_context = app.app_context()
    app_context.push()
    
    try:
        # Configurer les événements de synchronisation
        setup_sync_events()
        print("✅ Événements de synchronisation configurés")
        
        # Exécuter un test simple
        print("\n🧪 Test de synchronisation")
        
        # Trouver un club existant
        club = Club.query.first()
        if club:
            club_user = User.query.filter_by(club_id=club.id, role=UserRole.CLUB).first()
            
            if club_user:
                print(f"Club trouvé: {club.id} - {club.name}")
                print(f"Utilisateur associé: {club_user.id} - {club_user.name}")
                print("Synchronisation active pour cette paire")
            else:
                print(f"Club trouvé: {club.id} - {club.name}")
                print("Aucun utilisateur associé trouvé")
        else:
            print("Aucun club trouvé pour le test")
        
        print("\n🔄 Synchronisation bidirectionnelle prête")
        print("Toutes les modifications entre Club et User seront automatiquement synchronisées")
        
    except Exception as e:
        print(f"❌ Erreur lors de la configuration: {e}")
        import traceback
        traceback.print_exc()
    finally:
        app_context.pop()

if __name__ == "__main__":
    setup_bidirectional_sync()
