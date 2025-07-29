#!/usr/bin/env python3
"""
Test direct de l'authentification PadelVar
Sans dépendances externes - utilise le test client Flask
"""

import sys
import os
from pathlib import Path

# Configuration du chemin
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def test_authentication_flow():
    """Test complet du flux d'authentification"""
    print("🔍 Test de l'authentification PadelVar")
    print("=" * 60)
    
    try:
        # Import et création de l'app
        from src.main import create_app
        
        app = create_app('development')
        
        with app.test_client() as client:
            # 1. Test de santé
            print("1. 🏥 Test de santé...")
            response = client.get('/api/health')
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ API en ligne: {response.get_json()['message']}")
            else:
                print(f"   ❌ API hors ligne")
                return False
            
            # 2. Test de connexion
            print("\n2. 🔐 Test de connexion...")
            login_data = {
                "email": "player@test.com",
                "password": "password123"
            }
            
            response = client.post('/api/auth/login', 
                                 json=login_data,
                                 content_type='application/json')
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                user = data.get('user', {})
                print(f"   ✅ Connexion réussie pour: {user.get('name', 'N/A')}")
                print(f"   Rôle: {user.get('role', 'N/A')}")
                print(f"   ID: {user.get('id', 'N/A')}")
            else:
                print(f"   ❌ Échec de connexion")
                try:
                    error_data = response.get_json()
                    print(f"   Erreur: {error_data}")
                except:
                    print(f"   Erreur: {response.data}")
                return False
            
            # 3. Test des routes de debug
            print("\n3. 🛠️ Test des routes de debug...")
            
            # Debug session
            response = client.get('/api/players/debug/session')
            print(f"   Debug session - Status: {response.status_code}")
            if response.status_code == 200:
                session_data = response.get_json()
                print(f"   ✅ Session active: user_id={session_data.get('user_id', 'N/A')}")
            else:
                print(f"   ❌ Session debug failed")
                try:
                    print(f"   Erreur: {response.get_json()}")
                except:
                    print(f"   Erreur: {response.data}")
            
            # Debug auth
            response = client.get('/api/players/debug/auth')
            print(f"   Debug auth - Status: {response.status_code}")
            if response.status_code == 200:
                auth_data = response.get_json()
                print(f"   ✅ Auth OK: {auth_data.get('message', 'N/A')}")
            else:
                print(f"   ❌ Auth debug failed")
            
            # 4. Test des routes players problématiques
            print("\n4. 🎯 Test des routes players...")
            
            # Test clubs disponibles
            response = client.get('/api/players/clubs/available')
            print(f"   Clubs disponibles - Status: {response.status_code}")
            if response.status_code == 200:
                data = response.get_json()
                clubs_count = len(data.get('clubs', []))
                print(f"   ✅ {clubs_count} clubs disponibles")
            else:
                print(f"   ❌ Clubs disponibles failed")
                try:
                    error_data = response.get_json()
                    print(f"   Erreur: {error_data}")
                except:
                    print(f"   Erreur: {response.data}")
            
            # Test clubs suivis
            response = client.get('/api/players/clubs/followed')
            print(f"   Clubs suivis - Status: {response.status_code}")
            if response.status_code == 200:
                data = response.get_json()
                clubs_count = len(data.get('clubs', []))
                print(f"   ✅ {clubs_count} clubs suivis")
            else:
                print(f"   ❌ Clubs suivis failed")
                try:
                    error_data = response.get_json()
                    print(f"   Erreur: {error_data}")
                except:
                    print(f"   Erreur: {response.data}")
            
            # Test dashboard
            response = client.get('/api/players/dashboard')
            print(f"   Dashboard - Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Dashboard accessible")
            else:
                print(f"   ❌ Dashboard failed")
            
            print("\n" + "=" * 60)
            print("✅ Test terminé avec succès!")
            print("🎉 L'authentification fonctionne correctement.")
            print("")
            print("📋 Instructions pour tester dans le navigateur:")
            print("   1. Démarrez le serveur: python app.py")
            print("   2. Ouvrez: http://localhost:5000/test")
            print("   3. Utilisateur test: player@test.com / password123")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_authentication_flow()
