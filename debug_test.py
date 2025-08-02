#!/usr/bin/env python3
"""Test de debug pour trouver où est l'erreur video.user"""

import sys
from pathlib import Path

# Configuration du chemin
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.main import create_app
from src.models.user import User, UserRole

# Créer l'app
app = create_app()

with app.test_client() as client:
    with app.app_context():
        print("=== DEBUG VIDEO.USER ERROR ===")
        
        # Trouver un utilisateur club
        user = User.query.filter_by(role=UserRole.CLUB).first()
        if not user:
            print("❌ Aucun utilisateur club trouvé")
            exit(1)
            
        print(f"✅ Utilisateur: {user.name}")
        
        # Simuler session
        with client.session_transaction() as sess:
            sess['user_id'] = user.id
            sess['logged_in'] = True
        
        print("Test dashboard...")
        try:
            response = client.get('/api/clubs/dashboard')
            print(f"Status: {response.status_code}")
            if response.status_code != 200:
                print("Response:", response.get_data(as_text=True))
        except Exception as e:
            print(f"ERREUR: {e}")
            import traceback
            traceback.print_exc()
