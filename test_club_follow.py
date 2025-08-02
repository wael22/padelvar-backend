#!/usr/bin/env python3
"""
Test spécifique pour le suivi de clubs
"""

import sys
import os
from pathlib import Path

# Configuration du chemin
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def test_club_following():
    """Test du suivi et arrêt de suivi de clubs"""
    print("🎯 Test de suivi de clubs PadelVar")
    print("=" * 60)
    
    try:
        # Import et création de l'app
        from src.main import create_app
        
        app = create_app('development')
        
        with app.test_client() as client:
            # 1. Connexion
            print("1. 🔐 Connexion...")
            login_data = {
                "email": "player@test.com",
                "password": "password123"
            }
            
            response = client.post('/api/auth/login', 
                                 json=login_data,
                                 content_type='application/json')
            
            if response.status_code != 200:
                print(f"❌ Échec de connexion: {response.status_code}")
                return False
            
            print("✅ Connexion réussie")
            
            # 2. Récupérer les clubs disponibles
            print("\n2. 📋 Récupération des clubs disponibles...")
            response = client.get('/api/players/clubs/available')
            
            if response.status_code != 200:
                print(f"❌ Échec récupération clubs: {response.status_code}")
                print(f"   Erreur: {response.get_json()}")
                return False
            
            clubs_data = response.get_json()
            clubs = clubs_data.get('clubs', [])
            print(f"✅ {len(clubs)} clubs disponibles")
            
            if not clubs:
                print("❌ Aucun club disponible pour tester")
                return False
            
            # 3. Tester le suivi d'un club
            club_to_follow = clubs[0]
            club_id = club_to_follow['id']
            club_name = club_to_follow['name']
            
            print(f"\n3. ❤️ Test de suivi du club '{club_name}' (ID: {club_id})...")
            response = client.post(f'/api/players/clubs/{club_id}/follow')
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                print(f"✅ Suivi réussi: {data.get('message', 'N/A')}")
                print(f"   Clubs suivis: {data.get('followed_clubs_count', 'N/A')}")
            else:
                error_data = response.get_json()
                print(f"❌ Échec du suivi: {error_data}")
                return False
            
            # 4. Vérifier que le club est maintenant suivi
            print(f"\n4. ✅ Vérification du suivi...")
            response = client.get('/api/players/clubs/followed')
            
            if response.status_code == 200:
                followed_data = response.get_json()
                followed_clubs = followed_data.get('clubs', [])
                print(f"✅ {len(followed_clubs)} clubs suivis")
                
                # Vérifier que notre club est dans la liste
                club_found = any(club['id'] == club_id for club in followed_clubs)
                if club_found:
                    print(f"✅ Club '{club_name}' trouvé dans les clubs suivis")
                else:
                    print(f"❌ Club '{club_name}' non trouvé dans les clubs suivis")
                    return False
            else:
                print(f"❌ Échec récupération clubs suivis: {response.status_code}")
                return False
            
            # 5. Tester l'arrêt de suivi
            print(f"\n5. 💔 Test d'arrêt de suivi du club '{club_name}'...")
            response = client.post(f'/api/players/clubs/{club_id}/unfollow')
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                print(f"✅ Arrêt de suivi réussi: {data.get('message', 'N/A')}")
                print(f"   Clubs suivis: {data.get('followed_clubs_count', 'N/A')}")
            else:
                error_data = response.get_json()
                print(f"❌ Échec arrêt de suivi: {error_data}")
                return False
            
            # 6. Vérifier que le club n'est plus suivi
            print(f"\n6. ✅ Vérification de l'arrêt de suivi...")
            response = client.get('/api/players/clubs/followed')
            
            if response.status_code == 200:
                followed_data = response.get_json()
                followed_clubs = followed_data.get('clubs', [])
                print(f"✅ {len(followed_clubs)} clubs suivis")
                
                # Vérifier que notre club n'est plus dans la liste
                club_found = any(club['id'] == club_id for club in followed_clubs)
                if not club_found:
                    print(f"✅ Club '{club_name}' retiré des clubs suivis")
                else:
                    print(f"❌ Club '{club_name}' encore présent dans les clubs suivis")
                    return False
            else:
                print(f"❌ Échec récupération clubs suivis: {response.status_code}")
                return False
            
            print("\n" + "=" * 60)
            print("🎉 TOUS LES TESTS DE SUIVI RÉUSSIS !")
            print("✅ Le système de suivi de clubs fonctionne parfaitement")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_club_following()
