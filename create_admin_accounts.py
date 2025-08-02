#!/usr/bin/env python3
"""
Script pour créer/corriger les deux comptes admin
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

def create_admin_accounts():
    print("🔧 CRÉATION DES COMPTES ADMIN")
    print("=" * 40)
    
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
        
        # Définir les comptes admin
        admin_accounts = [
            ('admin@padelvar.com', 'Super Admin'),
            ('admin2@padelvar.com', 'Super Admin 2')
        ]
        
        success_count = 0
        
        for admin_email, admin_name in admin_accounts:
            print(f"\n🔍 Traitement de {admin_email}...")
            
            # Vérifier si l'admin existe
            cursor.execute("SELECT id, email, password_hash, name, role FROM user WHERE email = ?", 
                          (admin_email,))
            admin = cursor.fetchone()
            
            if admin:
                print(f"✅ Compte existant: {admin[3]} ({admin[1]})")
                print(f"   Rôle: {admin[4]}")
                
                # Corriger le mot de passe
                new_hash = generate_password_hash('admin123')
                cursor.execute("UPDATE user SET password_hash = ?, role = ? WHERE email = ?", 
                              (new_hash, 'SUPER_ADMIN', admin_email))
                
                # Vérifier que ça marche
                if check_password_hash(new_hash, 'admin123'):
                    print("✅ Mot de passe corrigé et testé !")
                    success_count += 1
                else:
                    print("❌ Erreur lors de la correction")
                    
            else:
                print(f"❌ Compte non trouvé, création de {admin_email}...")
                try:
                    # Créer l'admin
                    admin_hash = generate_password_hash('admin123')
                    cursor.execute("""
                        INSERT INTO user (email, password_hash, name, role, credits_balance, created_at) 
                        VALUES (?, ?, ?, ?, ?, datetime('now'))
                    """, (admin_email, admin_hash, admin_name, 'SUPER_ADMIN', 100))
                    
                    print(f"✅ {admin_email} créé avec succès !")
                    success_count += 1
                except Exception as e:
                    print(f"❌ Erreur création {admin_email}: {e}")
        
        conn.commit()
        
        # Lister tous les admins pour vérification
        print(f"\n👑 COMPTES ADMIN DISPONIBLES:")
        cursor.execute("SELECT id, email, name, role FROM user WHERE role LIKE '%ADMIN%'")
        admins = cursor.fetchall()
        for admin in admins:
            print(f"   {admin[0]}: {admin[1]} - {admin[2]} ({admin[3]})")
        
        conn.close()
        
        if success_count > 0:
            print(f"\n✅ {success_count} compte(s) admin opérationnel(s) !")
            return True
        else:
            print("\n❌ Aucun compte admin fonctionnel")
            return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_logins():
    print(f"\n🧪 TEST DES CONNEXIONS ADMIN")
    print("=" * 35)
    
    admin_accounts = ['admin@padelvar.com', 'admin2@padelvar.com']
    
    try:
        import requests
        
        working_accounts = []
        
        for admin_email in admin_accounts:
            print(f"\n🔑 Test {admin_email}...")
            
            login_data = {
                "email": admin_email,
                "password": "admin123"
            }
            
            try:
                response = requests.post(
                    "http://localhost:5000/api/auth/login",
                    json=login_data,
                    headers={"Content-Type": "application/json"},
                    timeout=3
                )
                
                print(f"📊 Status: {response.status_code}")
                if response.status_code == 200:
                    print(f"✅ CONNEXION RÉUSSIE pour {admin_email} !")
                    working_accounts.append(admin_email)
                else:
                    print(f"❌ Échec: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                print("❌ Serveur non accessible")
            except Exception as e:
                print(f"❌ Erreur: {e}")
        
        if working_accounts:
            print(f"\n🎉 COMPTES FONCTIONNELS:")
            for account in working_accounts:
                print(f"   ✅ {account}")
        else:
            print(f"\n❌ Aucun compte ne fonctionne")
            
    except ImportError:
        print("❌ Module requests non disponible pour les tests")

if __name__ == '__main__':
    print("🚀 CRÉATION DES COMPTES ADMIN")
    print("=" * 50)
    
    if create_admin_accounts():
        print(f"\n{'='*50}")
        print("✅ COMPTES ADMIN CRÉÉS/CORRIGÉS !")
        print(f"{'='*50}")
        print("\n📋 UTILISATION:")
        print("1. Démarrez le serveur: python app.py")
        print("2. Accédez à: http://localhost:5173")
        print("3. Connectez-vous avec:")
        print("   Option 1: admin@padelvar.com / admin123")
        print("   Option 2: admin2@padelvar.com / admin123")
        
        # Test automatique si serveur en cours
        test_logins()
    else:
        print("\n❌ ÉCHEC DE LA CRÉATION DES COMPTES")
        print("💡 Vérifiez que le serveur Flask a été démarré au moins une fois")
