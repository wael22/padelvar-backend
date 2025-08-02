#!/usr/bin/env python3
"""
Script de test pour vérifier la connexion admin
"""

import requests
import json

def test_login():
    """Tester la connexion admin"""
    
    url = "http://localhost:5000/api/auth/login"
    
    payload = {
        "email": "admin@padelvar.com",
        "password": "admin123"
    }
    
    print("🧪 Test de connexion admin...")
    print(f"URL: {url}")
    print(f"Payload: {payload}")
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Connexion réussie!")
            return True
        else:
            print("❌ Connexion échouée")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur. Assurez-vous qu'il est démarré.")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_health():
    """Tester la santé du serveur"""
    
    url = "http://localhost:5000/health"
    
    try:
        response = requests.get(url, timeout=5)
        print(f"Health check: {response.status_code} - {response.text}")
        return response.status_code == 200
    except:
        print("❌ Serveur non accessible")
        return False

if __name__ == "__main__":
    print("=== TEST DE CONNEXION PADELVAR ===")
    
    # Test de santé
    if test_health():
        print("✅ Serveur accessible")
        
        # Test de connexion
        if test_login():
            print("\n🎉 Tout fonctionne! Vous pouvez vous connecter sur l'interface web avec:")
            print("   Email: admin@padelvar.com")
            print("   Mot de passe: admin123")
        else:
            print("\n❌ Problème de connexion")
    else:
        print("❌ Serveur non démarré. Lancez d'abord: python test_server.py")
