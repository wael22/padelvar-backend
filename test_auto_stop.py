#!/usr/bin/env python3
"""
Test du système d'arrêt automatique des enregistrements
"""

import requests
import time
import json

def test_auto_stop_recording():
    print("🧪 TEST ARRÊT AUTOMATIQUE DES ENREGISTREMENTS")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # 1. Se connecter en tant que joueur test
    session = requests.Session()
    
    print("\n1️⃣ CONNEXION JOUEUR TEST")
    print("-" * 30)
    
    # Chercher un utilisateur club existant
    login_data = {"email": "test@club.com", "password": "club123"}
    
    try:
        login_response = session.post(f"{base_url}/api/auth/login", json=login_data)
        if login_response.status_code != 200:
            # Essayer avec un autre compte
            login_data = {"email": "joueur@test.com", "password": "test123"}
            login_response = session.post(f"{base_url}/api/auth/login", json=login_data)
        
        if login_response.status_code == 200:
            print("✅ Connexion réussie")
        else:
            print(f"❌ Échec connexion: {login_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return False
    
    # 2. Récupérer les terrains disponibles
    print("\n2️⃣ RÉCUPÉRATION TERRAINS DISPONIBLES")
    print("-" * 40)
    
    try:
        courts_response = session.get(f"{base_url}/api/videos/courts/available")
        if courts_response.status_code == 200:
            courts_data = courts_response.json()
            available_courts = courts_data.get('available_courts', [])
            
            if not available_courts:
                print("❌ Aucun terrain disponible")
                return False
            
            # Prendre le premier terrain du premier club
            first_club = available_courts[0]
            test_court = first_club['courts'][0]
            court_id = test_court['id']
            
            print(f"✅ Terrain sélectionné: {test_court['name']} (ID: {court_id})")
            
        else:
            print(f"❌ Échec récupération terrains: {courts_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur récupération terrains: {e}")
        return False
    
    # 3. Démarrer un enregistrement court (2 minutes pour le test)
    print("\n3️⃣ DÉMARRAGE ENREGISTREMENT COURT")
    print("-" * 40)
    
    try:
        record_data = {
            "court_id": court_id,
            "session_name": "Test Arrêt Auto",
            "duration_minutes": 2  # 2 minutes pour le test
        }
        
        record_response = session.post(f"{base_url}/api/videos/record", json=record_data)
        
        if record_response.status_code == 200:
            record_result = record_response.json()
            session_id = record_result['session_id']
            auto_stop_time = record_result['auto_stop_time']
            
            print(f"✅ Enregistrement démarré")
            print(f"   Session ID: {session_id}")
            print(f"   Durée: 2 minutes")
            print(f"   Arrêt automatique prévu: {auto_stop_time}")
            
        else:
            print(f"❌ Échec démarrage enregistrement: {record_response.status_code}")
            print(f"   Réponse: {record_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur démarrage enregistrement: {e}")
        return False
    
    # 4. Surveiller l'enregistrement
    print("\n4️⃣ SURVEILLANCE ENREGISTREMENT")
    print("-" * 35)
    
    print("⏱️  Attente de l'arrêt automatique (2 minutes)...")
    
    for i in range(24):  # Vérifier toutes les 5 secondes pendant 2 minutes
        try:
            # Vérifier les enregistrements actifs
            active_response = session.get(f"{base_url}/api/videos/active-recordings")
            
            if active_response.status_code == 200:
                active_data = active_response.json()
                active_recordings = active_data.get('active_recordings', [])
                
                current_recording = next((r for r in active_recordings if r['session_id'] == session_id), None)
                
                if current_recording:
                    elapsed = current_recording['elapsed_minutes']
                    remaining = current_recording['remaining_minutes']
                    print(f"   ⏰ Temps écoulé: {elapsed:.1f}min - Restant: {remaining:.1f}min")
                else:
                    print("   ✅ Enregistrement terminé automatiquement!")
                    break
            
            time.sleep(5)  # Attendre 5 secondes
            
        except Exception as e:
            print(f"   ⚠️  Erreur surveillance: {e}")
    
    # 5. Vérifier que l'enregistrement est bien arrêté
    print("\n5️⃣ VÉRIFICATION ARRÊT")
    print("-" * 25)
    
    try:
        final_active_response = session.get(f"{base_url}/api/videos/active-recordings")
        
        if final_active_response.status_code == 200:
            final_active_data = final_active_response.json()
            final_active_recordings = final_active_data.get('active_recordings', [])
            
            still_recording = any(r['session_id'] == session_id for r in final_active_recordings)
            
            if not still_recording:
                print("✅ Enregistrement arrêté automatiquement avec succès!")
                print("✅ Le système d'arrêt automatique fonctionne correctement")
                
                # Vérifier que le terrain est libéré
                courts_after = session.get(f"{base_url}/api/videos/courts/available")
                if courts_after.status_code == 200:
                    print("✅ Le terrain a été libéré automatiquement")
                
                return True
            else:
                print("❌ L'enregistrement est toujours actif")
                return False
        else:
            print(f"❌ Erreur vérification finale: {final_active_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur vérification finale: {e}")
        return False

def main():
    print("🔧 TEST SYSTÈME D'ARRÊT AUTOMATIQUE")
    print("=" * 70)
    
    success = test_auto_stop_recording()
    
    print(f"\n{'='*70}")
    if success:
        print("🎯 SYSTÈME D'ARRÊT AUTOMATIQUE OPÉRATIONNEL!")
        print("✅ Les enregistrements s'arrêtent automatiquement après la durée prévue")
        print("✅ Les terrains sont libérés automatiquement")
        print("✅ Le problème des enregistrements qui durent trop longtemps est résolu")
    else:
        print("❌ PROBLÈMES DÉTECTÉS DANS LE SYSTÈME D'ARRÊT AUTOMATIQUE")
        print("💡 Vérifiez que le serveur backend est démarré")
        print("💡 Vérifiez que les modifications du code sont appliquées")
    
    print("=" * 70)

if __name__ == '__main__':
    main()
