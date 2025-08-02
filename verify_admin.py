#!/usr/bin/env python3
"""
Script pour vérifier le compte admin
"""

import sqlite3
from werkzeug.security import check_password_hash

def check_admin():
    try:
        conn = sqlite3.connect('instance/app.db')
        cursor = conn.cursor()
        
        # Récupérer l'admin
        cursor.execute("SELECT id, email, password_hash, name, role FROM user WHERE email = ?", ('admin@padelvar.com',))
        admin_data = cursor.fetchone()
        
        if admin_data:
            print("✅ Compte admin trouvé:")
            print(f"   ID: {admin_data[0]}")
            print(f"   Email: {admin_data[1]}")
            print(f"   Nom: {admin_data[3]}")
            print(f"   Rôle: {admin_data[4]}")
            print(f"   Hash présent: {admin_data[2] is not None}")
            
            # Tester le mot de passe
            if admin_data[2]:
                password_ok = check_password_hash(admin_data[2], 'admin123')
                print(f"   Mot de passe 'admin123' valide: {password_ok}")
                
                if not password_ok:
                    print("❌ Le mot de passe ne correspond pas!")
                    print("🔧 Essayons de mettre à jour le mot de passe...")
                    
                    from werkzeug.security import generate_password_hash
                    new_hash = generate_password_hash('admin123')
                    cursor.execute("UPDATE user SET password_hash = ? WHERE email = ?", (new_hash, 'admin@padelvar.com'))
                    conn.commit()
                    print("✅ Mot de passe mis à jour!")
            else:
                print("❌ Aucun hash de mot de passe trouvé!")
        else:
            print("❌ Compte admin non trouvé!")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    check_admin()
