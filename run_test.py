#!/usr/bin/env python3
"""
Script simple pour démarrer et tester le serveur
"""
import subprocess
import time
import requests
import sys
import threading

def start_server():
    """Démarre le serveur en arrière-plan"""
    print("🚀 Démarrage du serveur...")
    try:
        process = subprocess.Popen([
            sys.executable, "test_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process
    except Exception as e:
        print(f"❌ Erreur démarrage serveur: {e}")
        return None

def test_connection():
    """Test la connexion après quelques secondes"""
    print("⏳ Attente 3 secondes pour le démarrage du serveur...")
    time.sleep(3)
    
    try:
        print("🔍 Test de connexion...")
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Serveur accessible!")
            
            # Test de login
            login_data = {
                "email": "admin@padelvar.com",
                "password": "admin123"
            }
            
            login_response = requests.post(
                "http://localhost:5000/api/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"📊 Test login: {login_response.status_code}")
            if login_response.status_code == 200:
                print("✅ Authentification OK!")
                print("🎉 Vous pouvez maintenant utiliser l'interface web")
            else:
                print(f"❌ Problème auth: {login_response.text}")
                
        else:
            print(f"❌ Serveur non accessible: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur")
    except Exception as e:
        print(f"❌ Erreur test: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 SCRIPT DE TEST PADELVAR")
    print("=" * 60)
    
    # Démarrer le serveur
    server_process = start_server()
    
    if server_process:
        try:
            # Tester la connexion dans un thread séparé
            test_thread = threading.Thread(target=test_connection)
            test_thread.start()
            
            print("\n📝 Instructions:")
            print("1. Le serveur démarre sur http://localhost:5000")
            print("2. Utilisez ces identifiants sur l'interface web:")
            print("   Email: admin@padelvar.com")
            print("   Mot de passe: admin123")
            print("\n⏹️  Appuyez sur Ctrl+C pour arrêter le serveur")
            print("=" * 60)
            
            # Attendre que le serveur soit interrompu
            server_process.wait()
            
        except KeyboardInterrupt:
            print("\n🛑 Arrêt du serveur...")
            server_process.terminate()
            server_process.wait()
            print("✅ Serveur arrêté")
    else:
        print("❌ Impossible de démarrer le serveur")
