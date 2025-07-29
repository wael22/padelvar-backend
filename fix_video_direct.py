#!/usr/bin/env python3
"""Correction directe de la table video avec SQLite"""

import sqlite3
import os

print("🔧 Correction directe de la table video...")

# Chemin vers la base de données
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'app.db')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("📊 Structure actuelle:")
    cursor.execute("PRAGMA table_info(video)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Colonnes: {columns}")
    
    # Ajouter file_size si manquante
    if 'file_size' not in columns:
        print("➕ Ajout de la colonne file_size...")
        cursor.execute("ALTER TABLE video ADD COLUMN file_size INTEGER")
        print("✅ Colonne file_size ajoutée")
    else:
        print("✅ Colonne file_size déjà présente")
    
    # Vérifier la structure finale
    cursor.execute("PRAGMA table_info(video)")
    final_columns = [row[1] for row in cursor.fetchall()]
    print(f"🎯 Structure finale: {final_columns}")
    
    # Test d'une requête complète
    print("🧪 Test de requête...")
    cursor.execute("SELECT id, title, file_size, is_unlocked, credits_cost FROM video LIMIT 1")
    result = cursor.fetchone()
    print(f"✅ Résultat test: {result}")
    
    # Commit et fermer
    conn.commit()
    conn.close()
    
    print("✅ Correction terminée avec succès!")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    if 'conn' in locals():
        conn.rollback()
        conn.close()
