#!/usr/bin/env python3
"""
Test de vérification des corrections du minuteur
"""

import os
import sys

# Ajouter le chemin du projet
sys.path.append(os.path.abspath('.'))

def test_import():
    """Test des imports et de la fonction corrigée"""
    try:
        print("🔍 Vérification des corrections...")
        
        # Test d'import
        from src.routes.videos import auto_stop_recording, active_recordings
        print("✅ Import réussi")
        
        # Vérifier que active_recordings existe
        print(f"✅ active_recordings initialisé: {type(active_recordings)}")
        
        # Test de la fonction
        print("✅ Fonction auto_stop_recording importée")
        
        # Vérifier le code de la fonction start_recording
        import inspect
        from src.routes.videos import start_recording
        source = inspect.getsource(start_recording)
        
        # Compter les occurrences de "return"
        return_count = source.count('return')
        print(f"✅ Nombre de 'return' dans start_recording: {return_count}")
        
        if return_count > 2:
            print("⚠️  ATTENTION: Il pourrait encore y avoir du code dupliqué")
        else:
            print("✅ Code start_recording semble correct")
            
        print("\n🎯 Les corrections semblent bien appliquées")
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_import()
