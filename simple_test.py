#!/usr/bin/env python3

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from src.main import create_app

app = create_app('development')

with app.test_client() as client:
    # Connexion
    response = client.post('/api/auth/login', 
                         json={"email": "player@test.com", "password": "password123"},
                         content_type='application/json')
    
    if response.status_code == 200:
        print("✅ Connexion OK")
        
        # Test follow club (club ID 1)
        response = client.post('/api/players/clubs/1/follow')
        print(f"Follow club 1: {response.status_code}")
        if response.status_code != 200:
            print(f"   Erreur: {response.get_json()}")
        else:
            print(f"   ✅ Suivi réussi: {response.get_json()}")
    else:
        print(f"❌ Connexion failed: {response.status_code}")
        print(f"   Erreur: {response.get_json()}")
