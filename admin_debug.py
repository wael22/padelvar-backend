#!/usr/bin/env python3
"""
Test simple pour vérifier pourquoi l'admin ne fonctionne pas
"""

import sqlite3
import requests
import json
from datetime import datetime

def check_database():
    """Vérifier la base de données"""
    print("🔍 VÉRIFICATION BASE DE DONNÉES")
    print("-" * 40)
    
    try:
        conn = sqlite3.connect("instance/app.db")
        cursor = conn.cursor()
        
        # Vérifier tous les utilisateurs
        cursor.execute("SELECT id, email, name, role FROM user ORDER BY id")
        users = cursor.fetchall()
        
        print(f"📊 Total utilisateurs: {len(users)}")
        
        admin_found = False
        for user in users:
            role_str = user[3] if user[3] else "NULL"
            print(f"   ID:{user[0]} | {user[1]} | {user[2]} | Rôle: '{role_str}'")
            
            if "ADMIN" in role_str.upper():
                admin_found = True
                print(f"   ✅ ADMIN TROUVÉ: {user[1]}")
        
        if not admin_found:
            print("   ❌ AUCUN ADMIN TROUVÉ!")
            
            # Créer un admin simple
            print("\n🔧 Création d'un admin...")
            cursor.execute("""
                INSERT OR REPLACE INTO user 
                (email, name, password_hash, role, credits_balance, created_at, club_id, phone_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "admin@padelvar.com",
                "Super Admin", 
                "pbkdf2:sha256:260000$test$simpletest",  # Hash simple pour test
                "SUPER_ADMIN",
                10000,
                datetime.now().isoformat(),
                None,
                None
            ))
            
            conn.commit()
            print("   ✅ Admin créé!")
        
        conn.close()
        return admin_found
        
    except Exception as e:
        print(f"❌ Erreur DB: {e}")
        return False

def test_server_health():
    """Tester si le serveur répond"""
    print("\n🌐 TEST SERVEUR")
    print("-" * 40)
    
    try:
        response = requests.get("http://localhost:5000/health", timeout=3)
        print(f"✅ Serveur accessible: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Message: {data.get('message', 'N/A')}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Serveur non accessible")
        print("💡 Démarrez le serveur avec: python simple_server.py")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_admin_login():
    """Tester la connexion admin"""
    print("\n🔐 TEST CONNEXION ADMIN")
    print("-" * 40)
    
    login_data = {
        "email": "admin@padelvar.com",
        "password": "admin123"
    }
    
    try:
        print(f"📤 Tentative de connexion avec: {login_data['email']}")
        
        response = requests.post(
            "http://localhost:5000/api/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        print(f"📊 Statut de réponse: {response.status_code}")
        print(f"📄 Réponse: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("✅ CONNEXION ADMIN RÉUSSIE!")
            data = response.json()
            user = data.get('user', {})
            print(f"👤 Connecté: {user.get('name')} ({user.get('role')})")
            return True
        else:
            print("❌ CONNEXION ÉCHOUÉE")
            try:
                error_data = response.json()
                print(f"   Erreur: {error_data.get('error', 'Inconnue')}")
            except:
                pass
            return False
            
    except Exception as e:
        print(f"❌ Erreur test login: {e}")
        return False

def test_player_creation():
    """Tester si on peut créer des joueurs (vous dites que ça marche)"""
    print("\n👤 TEST CRÉATION JOUEUR")
    print("-" * 40)
    
    # Simuler une création de joueur
    player_data = {
        "email": f"test_player_{datetime.now().strftime('%H%M%S')}@test.com",
        "name": "Test Player",
        "password": "test123"
    }
    
    try:
        response = requests.post(
            "http://localhost:5000/api/auth/register",  # ou l'endpoint de création
            json=player_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        print(f"📊 Création joueur: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print("✅ Création joueur fonctionne")
            return True
        else:
            print(f"❌ Problème création joueur: {response.text[:100]}")
            return False
            
    except Exception as e:
        print(f"⚠️ Test joueur non disponible: {e}")
        return None

def main():
    """Fonction principale"""
    print("🚀 DIAGNOSTIC PROBLÈME ADMIN PADELVAR")
    print("=" * 50)
    
    # 1. Vérifier la base de données
    db_ok = check_database()
    
    # 2. Vérifier le serveur
    server_ok = test_server_health()
    
    if server_ok:
        # 3. Tester la connexion admin
        admin_ok = test_admin_login()
        
        # 4. Tester création joueur
        player_ok = test_player_creation()
        
        print("\n" + "=" * 50)
        print("📋 RÉSUMÉ:")
        print(f"   Base de données: {'✅' if db_ok else '❌'}")
        print(f"   Serveur actif:   {'✅' if server_ok else '❌'}")
        print(f"   Connexion admin: {'✅' if admin_ok else '❌'}")
        print(f"   Création joueur: {'✅' if player_ok else '❌' if player_ok is False else '⚠️'}")
        
        if not admin_ok:
            print("\n💡 SOLUTIONS POSSIBLES:")
            print("1. Vérifiez que le serveur backend est démarré")
            print("2. Essayez: admin@padelvar.com / admin123")
            print("3. Vérifiez les logs du serveur pour les erreurs")
            print("4. Assurez-vous que l'interface utilise le bon port (5000)")
        else:
            print("\n🎉 L'admin devrait fonctionner maintenant!")
            
    else:
        print("\n❌ SERVEUR NON ACCESSIBLE")
        print("📋 ACTIONS REQUISES:")
        print("1. Ouvrez un terminal")
        print("2. Naviguez vers le dossier backend") 
        print("3. Exécutez: python simple_server.py")
        print("4. Puis testez la connexion admin")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
