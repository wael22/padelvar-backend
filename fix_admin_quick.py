#!/usr/bin/env python3
"""
Script pour corriger rapidement le problème de base de données admin
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

def fix_admin_db():
    print("🔧 CORRECTION RAPIDE DE LA BASE DE DONNÉES ADMIN")
    print("=" * 50)
    
    # Vérifier si la base existe
    db_path = 'instance/app.db'
    if not os.path.exists(db_path):
        print("❌ Base de données non trouvée !")
        print("💡 Démarrez d'abord le serveur Flask pour créer la DB")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier la table user
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user';")
        if not cursor.fetchone():
            print("❌ Table 'user' non trouvée !")
            return False
        
        print("✅ Table 'user' trouvée")
        
        # Vérifier l'admin
        cursor.execute("SELECT id, email, password_hash, name, role FROM user WHERE email = ?", 
                      ('admin@padelvar.com',))
        admin = cursor.fetchone()
        
        if admin:
            print(f"✅ Admin trouvé: {admin[3]} ({admin[1]})")
            print(f"   Rôle: {admin[4]}")
            
            # Corriger le mot de passe
            new_hash = generate_password_hash('admin123')
            cursor.execute("UPDATE user SET password_hash = ? WHERE email = ?", 
                          (new_hash, 'admin@padelvar.com'))
            conn.commit()
            
            # Vérifier que ça marche
            if check_password_hash(new_hash, 'admin123'):
                print("✅ Mot de passe admin corrigé et testé !")
            else:
                print("❌ Erreur lors de la correction")
                return False
                
        else:
            print("❌ Admin non trouvé, création...")
            # Créer l'admin
            admin_hash = generate_password_hash('admin123')
            cursor.execute("""
                INSERT INTO user (email, password_hash, name, role, credits_balance, created_at) 
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, ('admin@padelvar.com', admin_hash, 'Super Admin', 'SUPER_ADMIN', 100))
            conn.commit()
            print("✅ Admin créé avec succès !")
        
        # Lister tous les utilisateurs pour debug
        print("\n👥 Tous les utilisateurs:")
        cursor.execute("SELECT id, email, name, role FROM user")
        users = cursor.fetchall()
        for user in users:
            print(f"   {user[0]}: {user[1]} - {user[2]} ({user[3]})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_login():
    print(f"\n🧪 TEST DE CONNEXION")
    print("=" * 30)
    
    try:
        import requests
        
        login_data = {
            "email": "admin@padelvar.com",
            "password": "admin123"
        }
        
        print("🔑 Test de connexion...")
        response = requests.post(
            "http://localhost:5000/api/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=3
        )
        
        print(f"📊 Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ CONNEXION RÉUSSIE !")
            print("🎉 Vous pouvez maintenant vous connecter sur l'interface web")
        else:
            print(f"❌ Échec: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Serveur non accessible - démarrez d'abord le serveur Flask")
    except Exception as e:
        print(f"❌ Erreur test: {e}")

if __name__ == '__main__':
    print("🚀 DÉMARRAGE DE LA CORRECTION...")
    
    if fix_admin_db():
        print(f"\n{'='*50}")
        print("✅ BASE DE DONNÉES CORRIGÉE !")
        print(f"{'='*50}")
        print("\n📋 ÉTAPES SUIVANTES:")
        print("1. Démarrez le serveur: python app.py")
        print("2. Accédez à: http://localhost:5173")
        print("3. Connectez-vous avec:")
        print("   Email: admin@padelvar.com")
        print("   Mot de passe: admin123")
        
        # Test automatique si serveur en cours
        test_login()
    else:
        print("\n❌ ÉCHEC DE LA CORRECTION")
        print("💡 Vérifiez que le serveur Flask a été démarré au moins une fois")
