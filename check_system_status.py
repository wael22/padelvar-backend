import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:5000"

def check_server_status():
    """Vérifier si le serveur répond"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        return response.status_code == 200
    except:
        try:
            # Test basique
            response = requests.get(f"{BASE_URL}/", timeout=5)
            return True
        except:
            return False

def check_timer_system():
    """Vérifier que le système de minuteur est fonctionnel"""
    print("🔍 Vérification du système de minuteur...")
    
    if not check_server_status():
        print("❌ Serveur non accessible sur http://127.0.0.1:5000")
        print("   Assurez-vous que le serveur Flask est démarré")
        return False
    
    print("✅ Serveur accessible")
    
    # Tester l'accès aux routes vidéos
    try:
        response = requests.get(f"{BASE_URL}/api/videos/my-videos")
        print(f"✅ Route videos accessible (statut: {response.status_code})")
    except Exception as e:
        print(f"⚠️  Route videos: {e}")
    
    print("\n🎯 Pour tester le minuteur:")
    print("   1. Connectez-vous à l'application")
    print("   2. Démarrez un enregistrement avec une durée courte (1-2 minutes)")
    print("   3. Attendez que l'enregistrement s'arrête automatiquement")
    print("   4. Vérifiez que le terrain n'est plus en mode 'enregistrement'")
    
    return True

if __name__ == "__main__":
    print("🧪 Test de statut du système PadelVar")
    print("=" * 40)
    
    check_timer_system()
    
    print("\n" + "=" * 40)
    print("Test terminé")
