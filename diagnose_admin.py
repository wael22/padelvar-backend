#!/usr/bin/env python3
"""
Diagnostic complet pour le problème admin
"""

import sqlite3
import json
import hashlib
from datetime import datetime

def check_admin_issue():
    """Diagnostic complet du problème admin"""
    
    print("🔍 DIAGNOSTIC COMPLET - PROBLÈME ADMIN")
    print("=" * 60)
    
    db_path = "instance/app.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("1️⃣ STRUCTURE DE LA BASE DE DONNÉES")
        print("-" * 40)
        
        # Vérifier la structure
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        print("📋 Colonnes de la table user:")
        for col in columns:
            print(f"   {col[1]} ({col[2]})")
        
        print("\n2️⃣ TOUS LES UTILISATEURS")
        print("-" * 40)
        
        # Récupérer tous les utilisateurs
        cursor.execute("SELECT id, email, name, role, created_at FROM user ORDER BY id")
        users = cursor.fetchall()
        
        print(f"👥 Total utilisateurs: {len(users)}")
        for user in users:
            print(f"   ID: {user[0]}")
            print(f"   Email: {user[1]}")
            print(f"   Nom: {user[2]}")
            print(f"   Rôle: {user[3]}")
            print(f"   Créé: {user[4]}")
            print()
        
        print("3️⃣ ANALYSE DES ADMINS")
        print("-" * 40)
        
        # Chercher tous les types d'admin
        admin_variants = [
            "SUPER_ADMIN",
            "super_admin", 
            "ADMIN",
            "admin",
            "Admin",
            "SuperAdmin"
        ]
        
        for variant in admin_variants:
            cursor.execute("SELECT COUNT(*) FROM user WHERE role = ?", (variant,))
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"✅ Trouvé {count} utilisateur(s) avec rôle '{variant}'")
                
                cursor.execute("SELECT id, email, name FROM user WHERE role = ?", (variant,))
                admin_users = cursor.fetchall()
                for admin in admin_users:
                    print(f"   → ID: {admin[0]}, Email: {admin[1]}, Nom: {admin[2]}")
        
        print("\n4️⃣ VÉRIFICATION DES MOTS DE PASSE")
        print("-" * 40)
        
        cursor.execute("SELECT id, email, password_hash FROM user WHERE role LIKE '%ADMIN%' OR role LIKE '%admin%'")
        admin_passwords = cursor.fetchall()
        
        for admin in admin_passwords:
            print(f"🔐 Admin ID {admin[0]} ({admin[1]}):")
            password_hash = admin[2]
            print(f"   Hash: {password_hash[:50]}...")
            
            # Vérifier le type de hash
            if password_hash.startswith('scrypt:'):
                print("   Type: Scrypt (Werkzeug)")
            elif password_hash.startswith('pbkdf2:'):
                print("   Type: PBKDF2")
            else:
                print("   Type: Inconnu/Personnalisé")
        
        print("\n5️⃣ VÉRIFICATION DES NOUVEAUX JOUEURS")
        print("-" * 40)
        
        cursor.execute("SELECT COUNT(*) FROM user WHERE role = 'PLAYER'")
        player_count = cursor.fetchone()[0]
        print(f"👤 Nombre de joueurs: {player_count}")
        
        if player_count > 0:
            cursor.execute("SELECT id, email, name, created_at FROM user WHERE role = 'PLAYER' ORDER BY created_at DESC LIMIT 3")
            recent_players = cursor.fetchall()
            print("📅 Derniers joueurs créés:")
            for player in recent_players:
                print(f"   {player[1]} ({player[2]}) - {player[3]}")
        
        print("\n6️⃣ RECOMMANDATIONS")
        print("-" * 40)
        
        # Vérifier s'il y a un admin
        cursor.execute("SELECT COUNT(*) FROM user WHERE role LIKE '%ADMIN%'")
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            print("❌ PROBLÈME: Aucun admin trouvé!")
            print("💡 SOLUTION: Créer un nouveau super admin")
            create_new_admin = True
        else:
            print("✅ Admin(s) trouvé(s)")
            print("💡 Le problème peut venir de:")
            print("   - Mauvais mot de passe")
            print("   - Problème d'authentification côté serveur")
            print("   - Problème de rôle/permissions")
            create_new_admin = False
        
        return create_new_admin, admin_count
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False, 0
    finally:
        if 'conn' in locals():
            conn.close()

def create_fresh_admin():
    """Créer un nouvel admin avec mot de passe simple"""
    
    print("\n🔧 CRÉATION D'UN NOUVEAU SUPER ADMIN")
    print("-" * 40)
    
    try:
        conn = sqlite3.connect("instance/app.db")
        cursor = conn.cursor()
        
        # Supprimer l'ancien admin s'il existe
        cursor.execute("DELETE FROM user WHERE email = 'admin@padelvar.com'")
        deleted = cursor.rowcount
        if deleted > 0:
            print(f"🗑️ Supprimé {deleted} ancien(s) admin(s)")
        
        # Créer un hash simple pour le test
        import hashlib
        import base64
        import os
        
        password = "admin123"
        salt = base64.b64encode(os.urandom(16)).decode('ascii')
        hash_value = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 260000)
        hash_b64 = base64.b64encode(hash_value).decode('ascii')
        password_hash = f"pbkdf2:sha256:260000${salt}${hash_b64}"
        
        # Insérer le nouvel admin
        now = datetime.utcnow().isoformat()
        cursor.execute("""
            INSERT INTO user (email, name, password_hash, role, credits_balance, created_at, club_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "admin@padelvar.com",
            "Super Admin",
            password_hash,
            "SUPER_ADMIN",
            10000,
            now,
            None
        ))
        
        conn.commit()
        
        print("✅ Nouveau super admin créé!")
        print("📧 Email: admin@padelvar.com")
        print("🔑 Mot de passe: admin123")
        print("👑 Rôle: SUPER_ADMIN")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def test_admin_auth():
    """Tester l'authentification admin"""
    
    print("\n🧪 TEST D'AUTHENTIFICATION")
    print("-" * 40)
    
    try:
        import requests
        
        # Tester si le serveur est accessible
        try:
            response = requests.get("http://localhost:5000/health", timeout=3)
            print("✅ Serveur accessible")
        except:
            print("❌ Serveur non accessible sur localhost:5000")
            print("💡 Démarrez le serveur avec: python simple_server.py")
            return False
        
        # Tester la connexion admin
        login_data = {
            "email": "admin@padelvar.com",
            "password": "admin123"
        }
        
        response = requests.post(
            "http://localhost:5000/api/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📊 Statut: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Authentification admin réussie!")
            data = response.json()
            user = data.get('user', {})
            print(f"👤 Connecté en tant que: {user.get('name')} ({user.get('role')})")
            return True
        else:
            print("❌ Échec de l'authentification")
            print(f"📄 Réponse: {response.text}")
            return False
            
    except ImportError:
        print("⚠️ Module 'requests' non disponible pour le test")
        return None
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 DIAGNOSTIC DU PROBLÈME ADMIN PADELVAR")
    print("=" * 60)
    
    # Diagnostic complet
    needs_new_admin, admin_count = check_admin_issue()
    
    # Créer un nouvel admin si nécessaire
    if needs_new_admin or admin_count == 0:
        create_fresh_admin()
    
    # Tester l'authentification
    test_admin_auth()
    
    print("\n" + "=" * 60)
    print("🎯 RÉSUMÉ:")
    print("1. Vérifiez que le serveur backend est démarré")
    print("2. Utilisez: admin@padelvar.com / admin123")
    print("3. Si ça ne marche toujours pas, contactez-moi!")
    print("=" * 60)
