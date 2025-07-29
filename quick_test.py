#!/usr/bin/env python3
"""
Test final du système de suivi de clubs
"""
try:
    import sys
    import os
    from pathlib import Path

    project_root = Path(__file__).parent.absolute()
    sys.path.insert(0, str(project_root))

    from src.main import create_app

    app = create_app('development')

    print("🎯 Test système de suivi de clubs")
    print("=" * 50)

    with app.test_client() as client:
        # 1. Connexion
        print("1. 🔐 Test de connexion...")
        response = client.post('/api/auth/login', 
                             json={"email": "player@test.com", "password": "password123"},
                             content_type='application/json')
        
        if response.status_code == 200:
            print("   ✅ Connexion réussie")
        else:
            print(f"   ❌ Connexion échouée: {response.status_code}")
            print(f"   Réponse: {response.get_json()}")
            exit(1)

        # 2. Récupérer les clubs
        print("\n2. 📋 Récupération des clubs...")
        response = client.get('/api/players/clubs/available')
        
        if response.status_code == 200:
            clubs_data = response.get_json()
            clubs = clubs_data.get('clubs', [])
            print(f"   ✅ {len(clubs)} clubs disponibles")
            
            if len(clubs) == 0:
                print("   ⚠️ Aucun club pour tester")
                exit(0)
                
        else:
            print(f"   ❌ Erreur récupération clubs: {response.status_code}")
            print(f"   Réponse: {response.get_json()}")
            exit(1)

        # 3. Test de suivi du premier club
        club_id = clubs[0]['id']
        club_name = clubs[0]['name']
        
        print(f"\n3. ❤️ Test de suivi du club '{club_name}' (ID: {club_id})...")
        response = client.post(f'/api/players/clubs/{club_id}/follow')
        
        if response.status_code == 200:
            data = response.get_json()
            print(f"   ✅ Suivi réussi: {data.get('message', 'N/A')}")
            print(f"   Clubs suivis: {data.get('followed_clubs_count', 'N/A')}")
        else:
            print(f"   ❌ Erreur de suivi: {response.status_code}")
            print(f"   Réponse: {response.get_json()}")
            # Continuer pour voir les détails
            
        # 4. Vérification des clubs suivis
        print(f"\n4. ✅ Vérification des clubs suivis...")
        response = client.get('/api/players/clubs/followed')
        
        if response.status_code == 200:
            followed_data = response.get_json()
            followed_clubs = followed_data.get('clubs', [])
            print(f"   ✅ {len(followed_clubs)} clubs suivis")
            
            if len(followed_clubs) > 0:
                print(f"   Clubs: {[c['name'] for c in followed_clubs]}")
        else:
            print(f"   ❌ Erreur récupération clubs suivis: {response.status_code}")
            print(f"   Réponse: {response.get_json()}")

    print("\n🎉 Test terminé")

except Exception as e:
    print(f"\n❌ Erreur générale: {e}")
    import traceback
    traceback.print_exc()
