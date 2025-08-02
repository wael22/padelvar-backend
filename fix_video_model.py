"""
Script pour vérifier et corriger les modèles de données
Ajoute la colonne cdn_migrated_at à la table video si elle n'existe pas
"""
import os
import sys
import sqlite3
from pathlib import Path

def fix_video_model():
    """Vérifier et corriger le modèle Video"""
    # Chemin vers la base de données SQLite
    db_path = Path(__file__).parent / 'instance' / 'app.db'
    
    if not db_path.exists():
        print(f"Base de données non trouvée: {db_path}")
        return False
    
    print(f"Connexion à la base de données: {db_path}")
    
    # Connexion à la base de données
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Vérifier la structure de la table video
    cursor.execute("PRAGMA table_info(video)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Vérifier si la colonne cdn_migrated_at existe
    if 'cdn_migrated_at' not in columns:
        print("La colonne cdn_migrated_at n'existe pas, ajout en cours...")
        try:
            cursor.execute("ALTER TABLE video ADD COLUMN cdn_migrated_at DATETIME")
            conn.commit()
            print("✓ Colonne cdn_migrated_at ajoutée avec succès!")
        except Exception as e:
            print(f"Erreur lors de l'ajout de la colonne: {e}")
            conn.close()
            return False
    else:
        print("✓ La colonne cdn_migrated_at existe déjà")
    
    # Fermer la connexion
    conn.close()
    print("Modification terminée!")
    return True

if __name__ == "__main__":
    success = fix_video_model()
    sys.exit(0 if success else 1)
