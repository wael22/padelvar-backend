"""
Script pour appliquer la migration du système d'enregistrement avancé
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire du projet au chemin Python
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from flask import Flask
from flask_migrate import upgrade
from src.main import create_app

def apply_recording_migration():
    """Appliquer la migration pour le système d'enregistrement"""
    
    print("🔄 Application de la migration pour le système d'enregistrement avancé")
    print("=" * 60)
    
    try:
        # Créer l'application
        app = create_app('development')
        
        with app.app_context():
            # Appliquer toutes les migrations en attente
            print("\n📋 Application des migrations...")
            upgrade()
            print("✅ Migrations appliquées avec succès")
            
            # Vérifier que les nouvelles tables existent
            from src.models.database import db
            from src.models.user import RecordingSession, Court
            
            print("\n🔍 Vérification des nouvelles structures...")
            
            # Vérifier la table recording_session
            try:
                result = db.session.execute("SELECT COUNT(*) FROM recording_session")
                count = result.scalar()
                print(f"✅ Table recording_session créée (0 enregistrements)")
            except Exception as e:
                print(f"❌ Erreur avec la table recording_session: {e}")
            
            # Vérifier les nouvelles colonnes de Court
            try:
                result = db.session.execute("SELECT is_recording, current_recording_id FROM court LIMIT 1")
                print("✅ Colonnes is_recording et current_recording_id ajoutées à Court")
            except Exception as e:
                print(f"❌ Erreur avec les nouvelles colonnes de Court: {e}")
            
            print("\n🎉 Migration du système d'enregistrement terminée avec succès!")
            print("\nNouveautés disponibles:")
            print("• Sélection de durée d'enregistrement (60, 90, 120 min ou MAX)")
            print("• Arrêt automatique après la durée sélectionnée")
            print("• Bandeau d'enregistrement en cours pour les joueurs")
            print("• Gestion des enregistrements actifs pour les clubs")
            print("• Réservation automatique des terrains pendant l'enregistrement")
            
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = apply_recording_migration()
    if success:
        print("\n🚀 Vous pouvez maintenant redémarrer le serveur pour utiliser les nouvelles fonctionnalités!")
    else:
        print("\n💥 La migration a échoué. Vérifiez les erreurs ci-dessus.")
        sys.exit(1)
