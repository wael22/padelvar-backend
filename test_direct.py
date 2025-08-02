#!/usr/bin/env python3
"""
Test direct du système de minuteur - version autonome
"""

import sys
import os
from pathlib import Path

# Ajouter le chemin du projet
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def test_timer_logic():
    """Test de la logique du minuteur sans serveur"""
    print("🧪 Test de la logique du minuteur")
    print("=" * 40)
    
    try:
        # Import des modules
        from src.routes.videos import active_recordings, auto_stop_recording
        import threading
        import time
        
        print("✅ Imports réussis")
        
        # Simuler un enregistrement actif
        test_session_id = "test_session_123"
        active_recordings[test_session_id] = {
            'user_id': 1,
            'court_id': 1,
            'start_time': None,
            'duration_minutes': 0.1,  # 6 secondes pour test rapide
            'session_name': 'Test'
        }
        
        print(f"✅ Enregistrement simulé ajouté: {test_session_id}")
        print("⏱️  Démarrage du timer (6 secondes)...")
        
        # Démarrer le timer
        timer_thread = threading.Thread(
            target=auto_stop_recording,
            args=(test_session_id, 1, 0.1, 1),  # 0.1 minute = 6 secondes
            daemon=True
        )
        timer_thread.start()
        
        # Surveiller
        for i in range(8):  # 8 secondes de surveillance
            time.sleep(1)
            if test_session_id not in active_recordings:
                print(f"✅ SUCCESS: Enregistrement retiré après {i+1} secondes")
                return True
            print(f"   ⏳ Seconde {i+1}/8 - encore actif")
        
        print("❌ ÉCHEC: Timer n'a pas fonctionné")
        return False
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_routes_structure():
    """Test de la structure des routes"""
    print("\n🔍 Vérification de la structure des routes")
    print("=" * 40)
    
    try:
        from src.routes.videos import videos_bp
        print("✅ Blueprint videos importé")
        
        # Lister les routes
        rules = []
        for rule in videos_bp.url_map.iter_rules():
            if rule.endpoint.startswith('videos.'):
                rules.append(f"{rule.rule} -> {rule.endpoint}")
        
        if rules:
            print("✅ Routes trouvées:")
            for rule in rules:
                print(f"   {rule}")
        else:
            print("⚠️  Aucune route spécifique trouvée")
            
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Tests directs du système PadelVar")
    print("=" * 50)
    
    # Test 1: Structure
    test_routes_structure()
    
    # Test 2: Logique du minuteur
    success = test_timer_logic()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Tests réussis - Le système de minuteur fonctionne!")
    else:
        print("⚠️  Tests partiellement réussis - Vérifiez le serveur")
    
    print("\n💡 Pour test complet:")
    print("   1. Démarrez le serveur: python start_server.py")
    print("   2. Lancez: python test_timer_auth.py")
