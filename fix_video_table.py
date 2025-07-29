#!/usr/bin/env python3
"""Script pour ajouter les colonnes manquantes à la table video"""

from src.main import create_app
from src.models.user import db

# Créer l'app
app = create_app()

with app.app_context():
    print("🔍 Vérification de la structure de la table video...")
    
    try:
        # Vérifier les colonnes existantes
        result = db.engine.execute("PRAGMA table_info(video)")
        columns = [row[1] for row in result]
        print(f"Colonnes existantes: {columns}")
        
        # Vérifier si file_size existe
        if 'file_size' not in columns:
            print("❌ Colonne file_size manquante, ajout en cours...")
            db.engine.execute("ALTER TABLE video ADD COLUMN file_size INTEGER")
            print("✅ Colonne file_size ajoutée")
        else:
            print("✅ Colonne file_size déjà présente")
            
        # Vérifier les autres colonnes potentiellement manquantes
        required_columns = ['duration', 'is_unlocked', 'credits_cost']
        for col in required_columns:
            if col not in columns:
                print(f"❌ Colonne {col} manquante")
                if col == 'duration':
                    db.engine.execute("ALTER TABLE video ADD COLUMN duration INTEGER")
                elif col == 'is_unlocked':
                    db.engine.execute("ALTER TABLE video ADD COLUMN is_unlocked BOOLEAN DEFAULT 1")
                elif col == 'credits_cost':
                    db.engine.execute("ALTER TABLE video ADD COLUMN credits_cost INTEGER DEFAULT 1")
                print(f"✅ Colonne {col} ajoutée")
        
        # Commit les changements
        db.session.commit()
        print("✅ Migration terminée avec succès")
        
        # Vérifier la nouvelle structure
        result = db.engine.execute("PRAGMA table_info(video)")
        new_columns = [row[1] for row in result]
        print(f"Nouvelles colonnes: {new_columns}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        db.session.rollback()
