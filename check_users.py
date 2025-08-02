#!/usr/bin/env python3
"""
Script pour vérifier les utilisateurs dans la base de données
"""

import sqlite3

def check_users():
    """Vérifier tous les utilisateurs dans la base de données"""
    
    db_path = "instance/app.db"
    
    print("=== VÉRIFICATION DES UTILISATEURS ===")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtenir la structure de la table
        cursor.execute("PRAGMA table_info(user)")
        columns_info = cursor.fetchall()
        column_names = [col[1] for col in columns_info]
        
        print(f"📋 Structure de la table user:")
        for i, col in enumerate(columns_info):
            print(f"   {i}: {col[1]} ({col[2]})")
        
        # Récupérer tous les utilisateurs
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()
        
        print(f"\n👥 Utilisateurs trouvés: {len(users)}")
        
        for user in users:
            print(f"\n🔍 Utilisateur ID {user[0]}:")
            for i, value in enumerate(user):
                if i < len(column_names):
                    print(f"   {column_names[i]}: {value}")
        
        # Vérifier spécifiquement les admins
        cursor.execute("SELECT * FROM user WHERE role LIKE '%ADMIN%' OR role LIKE '%admin%'")
        admins = cursor.fetchall()
        
        print(f"\n👑 Administrateurs trouvés: {len(admins)}")
        for admin in admins:
            email_idx = column_names.index('email') if 'email' in column_names else 1
            name_idx = column_names.index('name') if 'name' in column_names else 2
            role_idx = column_names.index('role') if 'role' in column_names else 3
            
            print(f"   Email: {admin[email_idx]}")
            print(f"   Nom: {admin[name_idx]}")
            print(f"   Rôle: {admin[role_idx]}")
            
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_users()
