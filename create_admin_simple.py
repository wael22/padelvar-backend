#!/usr/bin/env python3
"""
Script simple pour créer un super admin pour PadelVar
Sans dépendances complexes
"""

import sqlite3
import hashlib
import sys
from datetime import datetime

def hash_password(password):
    """Hash un mot de passe comme le fait Werkzeug"""
    import base64
    import os
    
    # Génération d'un salt
    salt = base64.b64encode(os.urandom(16)).decode('ascii')
    
    # Hash avec SHA256 (simple version)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    
    # Format Werkzeug simplifié
    return f"pbkdf2:sha256:260000${salt}${hashed}"

def create_admin():
    """Créer un super admin directement dans la base de données"""
    
    # Chemin vers la base de données
    db_path = "instance/app.db"
    
    print("=== CRÉATION SUPER ADMIN PADELVAR ===")
    
    try:
        # Connexion à la base de données
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier si la table user existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='user';
        """)
        
        if not cursor.fetchone():
            print("❌ Table 'user' non trouvée. Assurez-vous que la base de données est initialisée.")
            return False
        
        # Vérifier les colonnes existantes
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Colonnes dans la table user: {columns}")
        
        # Vérifier si un super admin existe déjà
        cursor.execute("SELECT * FROM user WHERE role = 'SUPER_ADMIN' OR role = 'super_admin'")
        existing_admin = cursor.fetchone()
        
        if existing_admin:
            print("✅ Un super admin existe déjà:")
            print(f"   ID: {existing_admin[0]}")
            if len(existing_admin) > 2:
                print(f"   Email: {existing_admin[2] if 'email' in columns else 'N/A'}")
                print(f"   Nom: {existing_admin[1] if 'name' in columns else 'N/A'}")
            return True
        
        # Créer un nouveau super admin
        email = "admin@padelvar.com"
        name = "Super Admin"
        password = "admin123"
        role = "SUPER_ADMIN"
        
        # Hash du mot de passe
        password_hash = hash_password(password)
        
        # Créer l'entrée
        now = datetime.utcnow().isoformat()
        
        if 'club_id' in columns:
            # Structure complète
            cursor.execute("""
                INSERT INTO user (email, name, password_hash, role, credits_balance, created_at, club_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (email, name, password_hash, role, 0, now, None))
        else:
            # Structure minimale
            cursor.execute("""
                INSERT INTO user (email, name, password_hash, role, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (email, name, password_hash, role, now))
        
        conn.commit()
        
        print("✅ Super admin créé avec succès!")
        print(f"   Email: {email}")
        print(f"   Mot de passe: {password}")
        print(f"   Rôle: {role}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Erreur SQLite: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = create_admin()
    if success:
        print("\n🎉 Vous pouvez maintenant vous connecter avec:")
        print("   Email: admin@padelvar.com")
        print("   Mot de passe: admin123")
    else:
        print("\n❌ Échec de la création du super admin")
        sys.exit(1)
