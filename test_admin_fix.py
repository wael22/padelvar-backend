#!/usr/bin/env python3
"""Test de l'endpoint admin vidéos après correction"""

from src.main import create_app
from src.models.user import db, User, Video, Court, Club, UserRole
import requests

# Créer l'app
app = create_app()

print("🔍 Test de l'endpoint admin vidéos...")

with app.app_context():
    # Vérifier les données
    print(f"📊 Données dans la base:")
    print(f"  - Videos: {Video.query.count()}")
    print(f"  - Users: {User.query.count()}")
    print(f"  - Courts: {Court.query.count()}")
    print(f"  - Clubs: {Club.query.count()}")
    
    # Trouver un admin
    admin = User.query.filter_by(role=UserRole.SUPER_ADMIN).first()
    if admin:
        print(f"✅ Super Admin trouvé: {admin.email}")
    else:
        print("❌ Aucun super admin trouvé")

# Test de l'endpoint
try:
    print("\n🌐 Test de l'endpoint admin/videos...")
    
    # Créer une session pour les tests
    session = requests.Session()
    
    # Login en tant qu'admin
    login_data = {
        'email': 'admin@padelvar.com',
        'password': 'admin123'
    }
    
    login_response = session.post('http://localhost:5000/api/auth/login', json=login_data)
    print(f"Login Status: {login_response.status_code}")
    
    if login_response.status_code == 200:
        # Tester l'endpoint admin
        admin_response = session.get('http://localhost:5000/api/admin/videos')
        print(f"Admin Videos Status: {admin_response.status_code}")
        
        if admin_response.status_code == 200:
            data = admin_response.json()
            print(f"✅ Endpoint fonctionnel - {len(data.get('videos', []))} vidéos trouvées")
        else:
            print(f"❌ Erreur: {admin_response.text}")
    else:
        print(f"❌ Échec de connexion: {login_response.text}")
        
except Exception as e:
    print(f"❌ Erreur lors du test: {e}")

print("\n✅ Test terminé")
