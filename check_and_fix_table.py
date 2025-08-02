"""
Script pour vérifier la structure de la table video et écrire le résultat dans un fichier
"""
import os
import sys
import sqlite3
import logging
from datetime import datetime

def check_table_structure():
    """Vérifier la structure de la table video"""
    with open("table_structure_results.txt", "w") as output_file:
        try:
            # Chemin vers la base de données SQLite
            db_path = os.path.join(os.path.dirname(__file__), 'instance', 'app.db')
            
            # Vérifier si le fichier existe
            if not os.path.exists(db_path):
                output_file.write(f"❌ Base de données non trouvée: {db_path}\n")
                return False
                
            output_file.write(f"📂 Connexion à la base de données: {db_path}\n")
            
            # Connecter à la base de données
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Vérifier si la table video existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='video'")
            if not cursor.fetchone():
                output_file.write("❌ La table video n'existe pas!\n")
                conn.close()
                return False
                
            # Récupérer la structure de la table
            cursor.execute("PRAGMA table_info(video)")
            columns = cursor.fetchall()
            
            output_file.write("=== Structure de la table video ===\n")
            for col in columns:
                output_file.write(f"- {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] else ''}\n")
                
            # Vérifier si la colonne cdn_migrated_at existe
            column_names = [col[1] for col in columns]
            if 'cdn_migrated_at' in column_names:
                output_file.write("✅ La colonne cdn_migrated_at existe dans la table video\n")
            else:
                output_file.write("❌ La colonne cdn_migrated_at n'existe pas dans la table video\n")
                
                # Si la colonne n'existe pas, l'ajouter
                output_file.write("🔄 Ajout de la colonne cdn_migrated_at à la table video...\n")
                try:
                    cursor.execute("ALTER TABLE video ADD COLUMN cdn_migrated_at DATETIME")
                    conn.commit()
                    output_file.write("✅ Colonne cdn_migrated_at ajoutée avec succès!\n")
                except Exception as e:
                    output_file.write(f"❌ Erreur lors de l'ajout de la colonne: {str(e)}\n")
                
            # Fermer la connexion
            conn.close()
            output_file.write(f"Vérification terminée à {datetime.now()}\n")
            return True
            
        except Exception as e:
            output_file.write(f"❌ Erreur lors de la vérification de la structure: {str(e)}\n")
            return False

if __name__ == "__main__":
    check_table_structure()
    print("Vérification terminée. Voir table_structure_results.txt pour les résultats.")
