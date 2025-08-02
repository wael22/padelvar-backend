#!/usr/bin/env python3
"""
Script pour corriger la table court en ajoutant la colonne recording_session_id manquante
"""

import sqlite3
import sys
import os

def fix_court_schema():
    """Ajouter la colonne recording_session_id à la table court"""
    
    db_path = 'instance/app.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Base de données non trouvée: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier l'état actuel de la table
        print("📋 Structure actuelle de la table court:")
        cursor.execute("PRAGMA table_info(court)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   {col[1]} ({col[2]})")
        
        # Vérifier si la colonne recording_session_id existe déjà
        column_names = [col[1] for col in columns]
        
        if 'recording_session_id' not in column_names:
            print("\n🔧 Ajout de la colonne recording_session_id...")
            cursor.execute("ALTER TABLE court ADD COLUMN recording_session_id VARCHAR(100)")
            print("✅ Colonne recording_session_id ajoutée")
        else:
            print("\n✅ La colonne recording_session_id existe déjà")
        
        # Vérifier la nouvelle structure
        print("\n📋 Structure mise à jour de la table court:")
        cursor.execute("PRAGMA table_info(court)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   {col[1]} ({col[2]})")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Correction de la table court terminée avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la correction: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("🛠️  Correction de la table court")
    success = fix_court_schema()
    
    if success:
        print("\n🎉 La table court a été corrigée!")
        print("   Les endpoints clubs devraient maintenant fonctionner.")
    else:
        print("\n💥 Échec de la correction")
        sys.exit(1)
