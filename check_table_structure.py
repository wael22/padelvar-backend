"""
Script pour vérifier la structure de la table video
"""
import os
import sys
import sqlite3
import logging

# Configurer le logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_table_structure():
    """Vérifier la structure de la table video"""
    try:
        # Chemin vers la base de données SQLite
        db_path = os.path.join(os.path.dirname(__file__), 'instance', 'app.db')
        
        # Vérifier si le fichier existe
        if not os.path.exists(db_path):
            print(f"❌ Base de données non trouvée: {db_path}")
            return False
            
        print(f"📂 Connexion à la base de données: {db_path}")
        
        # Connecter à la base de données
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier si la table video existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='video'")
        if not cursor.fetchone():
            print("❌ La table video n'existe pas!")
            conn.close()
            return False
            
        # Récupérer la structure de la table
        cursor.execute("PRAGMA table_info(video)")
        columns = cursor.fetchall()
        
        print("=== Structure de la table video ===")
        for col in columns:
            print(f"- {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] else ''}")
            
        # Vérifier si la colonne cdn_migrated_at existe
        column_names = [col[1] for col in columns]
        if 'cdn_migrated_at' in column_names:
            print("✅ La colonne cdn_migrated_at existe dans la table video")
        else:
            print("❌ La colonne cdn_migrated_at n'existe pas dans la table video")
            
        # Fermer la connexion
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de la structure: {str(e)}")
        return False

if __name__ == "__main__":
    check_table_structure()
