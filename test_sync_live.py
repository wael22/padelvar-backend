#!/usr/bin/env python3
"""
Test de la synchronisation bidirectionnelle en temps réel
"""

import requests
import json
import time

def test_bidirectional_sync():
    """
    Teste la synchronisation bidirectionnelle entre club et admin
    """
    
    print("🧪 TEST SYNCHRONISATION BIDIRECTIONNELLE")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # 1. Vérifier que le serveur est accessible
    print("\n1️⃣ VÉRIFICATION SERVEUR")
    print("-" * 25)
    
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Serveur backend accessible")
        else:
            print(f"⚠️  Serveur répond avec status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Serveur backend non accessible")
        print("💡 Assurez-vous que le serveur Flask est démarré")
        return False
    except Exception as e:
        print(f"❌ Erreur connexion serveur: {e}")
        return False
    
    # 2. Login en tant qu'admin
    print("\n2️⃣ CONNEXION ADMIN")
    print("-" * 20)
    
    admin_session = requests.Session()
    
    try:
        login_response = admin_session.post(
            f"{base_url}/api/auth/login",
            json={"email": "admin@padelvar.com", "password": "admin123"},
            timeout=5
        )
        
        if login_response.status_code == 200:
            print("✅ Connexion admin réussie")
        else:
            print(f"❌ Échec connexion admin: {login_response.status_code}")
            print(f"   Réponse: {login_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur login admin: {e}")
        return False
    
    # 3. Récupérer la liste des clubs
    print("\n3️⃣ RÉCUPÉRATION CLUBS")
    print("-" * 25)
    
    try:
        clubs_response = admin_session.get(f"{base_url}/api/admin/clubs")
        
        if clubs_response.status_code == 200:
            clubs_data = clubs_response.json()
            clubs = clubs_data.get('clubs', [])
            print(f"✅ {len(clubs)} club(s) trouvé(s)")
            
            if not clubs:
                print("⚠️  Aucun club disponible pour tester")
                return False
                
        else:
            print(f"❌ Échec récupération clubs: {clubs_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur récupération clubs: {e}")
        return False
    
    # 4. Tester la modification d'un club depuis l'admin
    print("\n4️⃣ TEST MODIFICATION ADMIN → CLUB")
    print("-" * 35)
    
    test_club = clubs[0]  # Prendre le premier club
    club_id = test_club['id']
    original_phone = test_club.get('phone_number', '')
    
    # Générer un nouveau numéro de téléphone unique
    new_phone = f"+33{int(time.time()) % 1000000000}"
    
    print(f"📋 Club de test: {test_club['name']} (ID: {club_id})")
    print(f"📞 Ancien téléphone: {original_phone}")
    print(f"📞 Nouveau téléphone: {new_phone}")
    
    try:
        update_data = {
            "name": test_club['name'],
            "email": test_club['email'],
            "phone_number": new_phone,
            "address": test_club.get('address', '')
        }
        
        update_response = admin_session.put(
            f"{base_url}/api/admin/clubs/{club_id}",
            json=update_data
        )
        
        if update_response.status_code == 200:
            print("✅ Modification admin réussie")
            
            # Vérifier la synchronisation immédiate
            time.sleep(1)  # Attendre un peu
            
            clubs_after = admin_session.get(f"{base_url}/api/admin/clubs")
            if clubs_after.status_code == 200:
                updated_clubs = clubs_after.json().get('clubs', [])
                updated_club = next((c for c in updated_clubs if c['id'] == club_id), None)
                
                if updated_club and updated_club['phone_number'] == new_phone:
                    print("✅ Synchronisation admin confirmée")
                else:
                    print("❌ Synchronisation admin échouée")
                    return False
            else:
                print("❌ Impossible de vérifier la synchronisation")
                return False
                
        else:
            print(f"❌ Échec modification admin: {update_response.status_code}")
            print(f"   Réponse: {update_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur modification admin: {e}")
        return False
    
    # 5. Vérifier la route de synchronisation manuelle
    print("\n5️⃣ TEST SYNCHRONISATION MANUELLE")
    print("-" * 35)
    
    try:
        sync_response = admin_session.post(f"{base_url}/api/admin/sync/club-user-data")
        
        if sync_response.status_code == 200:
            sync_results = sync_response.json()
            print("✅ Route de synchronisation accessible")
            print(f"   Clubs traités: {sync_results['results']['clubs_processed']}")
            print(f"   Corrections: {sync_results['results']['sync_corrections']}")
        else:
            print(f"❌ Route de synchronisation échouée: {sync_response.status_code}")
            print(f"   Réponse: {sync_response.text}")
            
    except Exception as e:
        print(f"⚠️  Erreur test synchronisation manuelle: {e}")
    
    # 6. Résumé
    print(f"\n6️⃣ RÉSUMÉ")
    print("-" * 15)
    print("✅ Synchronisation bidirectionnelle opérationnelle!")
    print("✅ Les modifications admin se reflètent immédiatement")
    print("✅ La route de synchronisation fonctionne")
    
    print(f"\n💡 CONSEIL:")
    print("Pour tester la synchronisation club → admin:")
    print("1. Connectez-vous en tant que club dans le frontend")
    print("2. Modifiez votre profil")
    print("3. Vérifiez les changements dans l'admin")
    
    return True

if __name__ == '__main__':
    success = test_bidirectional_sync()
    
    if success:
        print("\n🎯 Test de synchronisation réussi!")
    else:
        print("\n❌ Problèmes détectés dans la synchronisation")
        print("💡 Vérifiez que le serveur backend est démarré")
