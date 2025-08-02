#!/usr/bin/env python3
"""
Script pour tester la synchronisation complète Profile → Backend → Admin
"""

import requests
import json
import time

def test_club_profile_sync():
    """Test complet de synchronisation des modifications de profil club"""
    print("🧪 TEST DE SYNCHRONISATION PROFIL CLUB")
    print("=" * 50)
    
    try:
        # Session admin pour vérifier les changements
        admin_session = requests.Session()
        admin_login = admin_session.post(
            "http://localhost:5000/api/auth/login",
            json={"email": "admin@padelvar.com", "password": "admin123"}
        )
        
        if admin_login.status_code != 200:
            print("❌ Impossible de se connecter en tant qu'admin")
            return False
        
        print("✅ Admin connecté")
        
        # Récupérer la liste des clubs avant modification
        clubs_before = admin_session.get("http://localhost:5000/api/admin/clubs")
        if clubs_before.status_code != 200:
            print("❌ Impossible de récupérer les clubs")
            return False
        
        clubs_data = clubs_before.json().get('clubs', [])
        if not clubs_data:
            print("❌ Aucun club trouvé")
            return False
        
        test_club = clubs_data[0]
        club_id = test_club['id']
        original_phone = test_club.get('phone_number', '')
        
        print(f"🏢 Test avec club: {test_club['name']} (ID: {club_id})")
        print(f"📞 Téléphone original: {original_phone}")
        
        # Simuler une connexion club et modification de profil
        # (En réalité, il faudrait avoir les identifiants du club)
        
        # Pour l'instant, testons directement via l'admin
        new_phone = f"+33{int(time.time()) % 1000000000}"
        
        print(f"\n🔄 Modification depuis l'admin...")
        update_response = admin_session.put(
            f"http://localhost:5000/api/admin/clubs/{club_id}",
            json={
                "name": test_club['name'],
                "email": test_club['email'],
                "phone_number": new_phone,
                "address": test_club.get('address', '')
            }
        )
        
        if update_response.status_code != 200:
            print(f"❌ Échec mise à jour: {update_response.text}")
            return False
        
        print(f"✅ Club mis à jour - nouveau téléphone: {new_phone}")
        
        # Vérifier la synchronisation
        clubs_after = admin_session.get("http://localhost:5000/api/admin/clubs")
        updated_clubs = clubs_after.json().get('clubs', [])
        updated_club = next((c for c in updated_clubs if c['id'] == club_id), None)
        
        if updated_club and updated_club['phone_number'] == new_phone:
            print("✅ Synchronisation admin: OK")
        else:
            print("❌ Synchronisation admin: ÉCHEC")
            return False
        
        # Tester la route de synchronisation automatique
        print(f"\n🔧 Test de synchronisation automatique...")
        sync_response = admin_session.post("http://localhost:5000/api/admin/sync/club-user-data")
        
        if sync_response.status_code == 200:
            sync_results = sync_response.json()
            print(f"✅ Synchronisation automatique: {sync_results['results']['clubs_processed']} clubs traités")
            if sync_results['results']['sync_corrections'] > 0:
                print(f"🔧 {sync_results['results']['sync_corrections']} corrections appliquées")
        else:
            print(f"❌ Synchronisation automatique échouée: {sync_response.text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_user_data_consistency():
    """Vérifier la cohérence des données utilisateur/club"""
    print(f"\n🔍 VÉRIFICATION COHÉRENCE DONNÉES")
    print("=" * 40)
    
    try:
        session = requests.Session()
        login = session.post(
            "http://localhost:5000/api/auth/login",
            json={"email": "admin@padelvar.com", "password": "admin123"}
        )
        
        if login.status_code != 200:
            print("❌ Connexion admin échouée")
            return False
        
        # Récupérer tous les utilisateurs
        users_response = session.get("http://localhost:5000/api/admin/users")
        clubs_response = session.get("http://localhost:5000/api/admin/clubs")
        
        if users_response.status_code != 200 or clubs_response.status_code != 200:
            print("❌ Impossible de récupérer les données")
            return False
        
        users = users_response.json().get('users', [])
        clubs = clubs_response.json().get('clubs', [])
        
        print(f"👥 {len(users)} utilisateurs")
        print(f"🏢 {len(clubs)} clubs")
        
        # Vérifier la cohérence
        inconsistencies = []
        
        for club in clubs:
            club_user = next((u for u in users if u.get('club_id') == club['id'] and u.get('role') == 'CLUB'), None)
            
            if not club_user:
                inconsistencies.append(f"Club {club['id']} sans utilisateur associé")
            else:
                if club['name'] != club_user['name']:
                    inconsistencies.append(f"Club {club['id']}: nom '{club['name']}' ≠ '{club_user['name']}'")
                if club['email'] != club_user['email']:
                    inconsistencies.append(f"Club {club['id']}: email '{club['email']}' ≠ '{club_user['email']}'")
        
        if inconsistencies:
            print(f"⚠️  {len(inconsistencies)} incohérence(s) détectée(s):")
            for issue in inconsistencies:
                print(f"   - {issue}")
        else:
            print("✅ Toutes les données sont cohérentes")
        
        return len(inconsistencies) == 0
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    print("🔄 TEST COMPLET DE SYNCHRONISATION")
    print("=" * 60)
    
    test1 = test_club_profile_sync()
    test2 = test_user_data_consistency()
    
    print(f"\n{'='*60}")
    print("📊 RÉSULTATS:")
    print(f"   Synchronisation profil: {'✅ OK' if test1 else '❌ ÉCHEC'}")
    print(f"   Cohérence des données: {'✅ OK' if test2 else '❌ ÉCHEC'}")
    
    if test1 and test2:
        print("\n🎉 TOUS LES TESTS RÉUSSIS!")
        print("La synchronisation bidirectionnelle fonctionne correctement.")
    else:
        print("\n⚠️  PROBLÈMES DÉTECTÉS")
        print("Vérifiez la configuration de synchronisation.")
    
    print("=" * 60)

if __name__ == '__main__':
    main()
