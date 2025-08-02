"""
Script pour ajouter directement la colonne cdn_migrated_at à la table video
"""
import os
import sys
import sqlite3
import logging

# Configurer le logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_column_directly():
    """Ajouter directement la colonne cdn_migrated_at à la table video"""
    try:
        # Chemin vers la base de données SQLite
        db_path = os.path.join(os.path.dirname(__file__), 'instance', 'app.db')
        
        # Vérifier si le fichier existe
        if not os.path.exists(db_path):
            logger.error(f"❌ Base de données non trouvée: {db_path}")
            return False
            
        logger.info(f"📂 Connexion à la base de données: {db_path}")
        
        # Connecter à la base de données
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier si la colonne existe déjà
        cursor.execute("PRAGMA table_info(video)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'cdn_migrated_at' in column_names:
            logger.info("✅ La colonne cdn_migrated_at existe déjà dans la table video")
            conn.close()
            return True
            
        # Ajouter la colonne
        logger.info("🔄 Ajout de la colonne cdn_migrated_at à la table video...")
        cursor.execute("ALTER TABLE video ADD COLUMN cdn_migrated_at DATETIME")
        
        # Valider et fermer
        conn.commit()
        conn.close()
        
        logger.info("✅ Colonne cdn_migrated_at ajoutée avec succès!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'ajout de la colonne: {str(e)}")
        return False

if __name__ == "__main__":
    success = add_column_directly()
    sys.exit(0 if success else 1)
