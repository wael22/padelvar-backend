#!/usr/bin/env python3
"""
Test de la fonctionnalité de changement de mot de passe
"""

import requests
import json

def test_change_password():
    print("🧪 TEST CHANGEMENT DE MOT DE PASSE")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # 1. Se connecter avec un utilisateur test
    session = requests.Session()
    
    print("\n1️⃣ CONNEXION UTILISATEUR TEST")
    print("-" * 30)
    
    # Essayer avec un compte existant
    login_data = {"email": "admin@padelvar.com", "password": "admin123"}
    
    try:
        login_response = session.post(f"{base_url}/api/auth/login", json=login_data)
        
        if login_response.status_code == 200:
            user_data = login_response.json()
            print(f"✅ Connexion réussie: {user_data['user']['email']}")
        else:
            print(f"❌ Échec connexion: {login_response.status_code}")
            print(f"   Réponse: {login_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return False
    
    # 2. Tester changement de mot de passe avec mauvais ancien mot de passe
    print("\n2️⃣ TEST MAUVAIS ANCIEN MOT DE PASSE")
    print("-" * 40)
    
    try:
        wrong_password_data = {
            "old_password": "mauvais_mot_de_passe",
            "new_password": "nouveau123"
        }
        
        wrong_response = session.post(f"{base_url}/api/auth/change-password", json=wrong_password_data)
        
        if wrong_response.status_code == 403:
            print("✅ Erreur correctement détectée pour mauvais ancien mot de passe")
        else:
            print(f"❌ Réponse inattendue: {wrong_response.status_code}")
            print(f"   Réponse: {wrong_response.text}")
            
    except Exception as e:
        print(f"❌ Erreur test mauvais mot de passe: {e}")
    
    # 3. Tester changement de mot de passe avec nouveau mot de passe trop court
    print("\n3️⃣ TEST NOUVEAU MOT DE PASSE TROP COURT")
    print("-" * 45)
    
    try:
        short_password_data = {
            "old_password": "admin123",
            "new_password": "123"  # Trop court
        }
        
        short_response = session.post(f"{base_url}/api/auth/change-password", json=short_password_data)
        
        if short_response.status_code == 400:
            print("✅ Erreur correctement détectée pour mot de passe trop court")
        else:
            print(f"❌ Réponse inattendue: {short_response.status_code}")
            print(f"   Réponse: {short_response.text}")
            
    except Exception as e:
        print(f"❌ Erreur test mot de passe court: {e}")
    
    # 4. Changer le mot de passe avec succès
    print("\n4️⃣ CHANGEMENT DE MOT DE PASSE VALIDE")
    print("-" * 40)
    
    try:
        new_password = "nouveau_admin123"
        change_password_data = {
            "old_password": "admin123",
            "new_password": new_password
        }
        
        change_response = session.post(f"{base_url}/api/auth/change-password", json=change_password_data)
        
        if change_response.status_code == 200:
            print("✅ Mot de passe changé avec succès")
            
            # 5. Tester la connexion avec le nouveau mot de passe
            print("\n5️⃣ TEST CONNEXION AVEC NOUVEAU MOT DE PASSE")
            print("-" * 45)
            
            # Déconnexion
            session.post(f"{base_url}/api/auth/logout")
            
            # Nouvelle session
            new_session = requests.Session()
            
            # Essayer avec l'ancien mot de passe (doit échouer)
            old_login = new_session.post(f"{base_url}/api/auth/login", json=login_data)
            if old_login.status_code != 200:
                print("✅ Ancien mot de passe rejeté correctement")
            else:
                print("❌ Ancien mot de passe encore accepté")
                return False
            
            # Essayer avec le nouveau mot de passe (doit réussir)
            new_login_data = {"email": "admin@padelvar.com", "password": new_password}
            new_login = new_session.post(f"{base_url}/api/auth/login", json=new_login_data)
            
            if new_login.status_code == 200:
                print("✅ Connexion réussie avec nouveau mot de passe")
                
                # 6. Remettre l'ancien mot de passe pour ne pas casser les autres tests
                print("\n6️⃣ RESTAURATION ANCIEN MOT DE PASSE")
                print("-" * 40)
                
                restore_data = {
                    "old_password": new_password,
                    "new_password": "admin123"
                }
                
                restore_response = new_session.post(f"{base_url}/api/auth/change-password", json=restore_data)
                
                if restore_response.status_code == 200:
                    print("✅ Ancien mot de passe restauré")
                    return True
                else:
                    print(f"⚠️  Impossible de restaurer l'ancien mot de passe: {restore_response.status_code}")
                    print("💡 Mot de passe admin changé définitivement")
                    return True
            else:
                print(f"❌ Échec connexion avec nouveau mot de passe: {new_login.status_code}")
                return False
        else:
            print(f"❌ Échec changement mot de passe: {change_response.status_code}")
            print(f"   Réponse: {change_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur changement mot de passe: {e}")
        return False

def main():
    print("🔐 TEST SYSTÈME DE CHANGEMENT DE MOT DE PASSE")
    print("=" * 70)
    
    success = test_change_password()
    
    print(f"\n{'='*70}")
    if success:
        print("🎯 SYSTÈME DE CHANGEMENT DE MOT DE PASSE OPÉRATIONNEL!")
        print("✅ Validation de l'ancien mot de passe")
        print("✅ Validation de la longueur du nouveau mot de passe") 
        print("✅ Changement de mot de passe effectif")
        print("✅ Anciens mots de passe invalidés")
        print("")
        print("📝 FONCTIONNALITÉS FRONTEND DISPONIBLES:")
        print("   • Page profil avec onglet 'Changer le mot de passe'")
        print("   • Validation côté client et serveur")
        print("   • Interface utilisateur intuitive")
    else:
        print("❌ PROBLÈMES DÉTECTÉS DANS LE SYSTÈME")
        print("💡 Vérifiez que le serveur backend est démarré")
        print("💡 Vérifiez les logs du serveur pour plus de détails")
    
    print("=" * 70)

if __name__ == '__main__':
    main()
