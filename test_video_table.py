#!/usr/bin/env python3
"""Test simple de la table video après migration"""

import sqlite3
import os

print("🔍 Test de la structure de la table video...")

# Chemin vers la base de données
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'app.db')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Vérifier la structure de la table video
    cursor.execute("PRAGMA table_info(video)")
    columns = cursor.fetchall()
    
    print("📊 Colonnes de la table video:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # Test simple d'une requête
    cursor.execute("SELECT COUNT(*) FROM video")
    count = cursor.fetchone()[0]
    print(f"📈 Nombre de vidéos: {count}")
    
    # Test d'une requête avec les nouvelles colonnes
    try:
        cursor.execute("SELECT id, title, file_size, is_unlocked, credits_cost FROM video LIMIT 1")
        result = cursor.fetchone()
        print(f"✅ Test de requête réussi: {result}")
    except Exception as e:
        print(f"❌ Erreur de requête: {e}")
    
    conn.close()
    print("✅ Test terminé")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
