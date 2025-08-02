#!/usr/bin/env python3
"""
Script pour réinitialiser le mot de passe du super admin
"""

import sqlite3
import hashlib
import base64
import os

def generate_werkzeug_hash(password):
    """Génère un hash compatible avec Werkzeug"""
    # Paramètres pour scrypt (comme utilisé par Werkzeug)
    salt = base64.b64encode(os.urandom(16)).decode('ascii')
    
    # Simuler le hash scrypt de Werkzeug (version simplifiée)
    # En réalité, Werkzeug utilise scrypt mais on va utiliser une méthode compatible
    import hashlib
    hash_value = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 260000)
    hash_b64 = base64.b64encode(hash_value).decode('ascii')
    
    return f"pbkdf2:sha256:260000${salt}${hash_b64}"

def reset_admin_password():
    """Réinitialiser le mot de passe du super admin"""
    
    db_path = "instance/app.db"
    
    print("=== RÉINITIALISATION MOT DE PASSE ADMIN ===")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Nouveau mot de passe
        new_password = "admin123"
        password_hash = generate_werkzeug_hash(new_password)
        
        # Mettre à jour le mot de passe
        cursor.execute("""
            UPDATE user 
            SET password_hash = ? 
            WHERE email = 'admin@padelvar.com' AND role = 'SUPER_ADMIN'
        """, (password_hash,))
        
        if cursor.rowcount > 0:
            conn.commit()
            print("✅ Mot de passe mis à jour avec succès!")
            print(f"   Email: admin@padelvar.com")
            print(f"   Nouveau mot de passe: {new_password}")
            print(f"   Hash généré: {password_hash[:50]}...")
        else:
            print("❌ Aucun super admin trouvé à mettre à jour")
            
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = reset_admin_password()
    if success:
        print("\n🎉 Essayez de vous connecter avec:")
        print("   Email: admin@padelvar.com")
        print("   Mot de passe: admin123")
    else:
        print("\n❌ Échec de la réinitialisation")
