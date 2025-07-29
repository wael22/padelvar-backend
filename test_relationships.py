#!/usr/bin/env python3
"""
Test de diagnostic pour les relationships dynamiques
"""
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

print("🔍 Diagnostic des relationships dynamiques...")

try:
    from src.main import create_app
    from src.models.user import User, Club
    
    app = create_app('development')
    
    with app.app_context():
        print("✅ Contexte d'application créé")
        
        # Récupérer l'utilisateur test
        user = User.query.filter_by(email='player@test.com').first()
        if not user:
            print("❌ Utilisateur test non trouvé")
            exit(1)
        else:
            print(f"✅ Utilisateur trouvé: {user.name} (ID: {user.id})")
            
            # Tester les relationships
            print(f"📊 Type de followed_clubs: {type(user.followed_clubs)}")
            print(f"📊 Méthodes disponibles: {[m for m in dir(user.followed_clubs) if not m.startswith('_')]}")
            
            try:
                count = user.followed_clubs.count()
                print(f"📊 Nombre de clubs suivis: {count}")
            except Exception as e:
                print(f"❌ Erreur count(): {e}")
            
            # Récupérer un club
            club = Club.query.first()
            if club:
                print(f"✅ Club trouvé: {club.name} (ID: {club.id})")
                print(f"📊 Type de club.followers: {type(club.followers)}")
                
                try:
                    followers_count = club.followers.count()
                    print(f"📊 Nombre de followers: {followers_count}")
                except Exception as e:
                    print(f"❌ Erreur followers count(): {e}")
                
                # Tester la vérification
                try:
                    is_following = user.followed_clubs.filter_by(id=club.id).first()
                    print(f"📊 User suit le club? {bool(is_following)}")
                except Exception as e:
                    print(f"❌ Erreur filter_by(): {e}")
                    
                # Test de l'ajout/suppression
                try:
                    print(f"\n🧪 Test d'ajout de club...")
                    user.followed_clubs.append(club)
                    print(f"✅ Club ajouté")
                    
                    # Vérifier
                    is_following_after = user.followed_clubs.filter_by(id=club.id).first()
                    print(f"📊 User suit le club après ajout? {bool(is_following_after)}")
                    
                    # Retirer
                    print(f"🧪 Test de suppression de club...")
                    user.followed_clubs.remove(club)
                    print(f"✅ Club retiré")
                    
                except Exception as e:
                    print(f"❌ Erreur manipulation: {e}")
                    import traceback
                    traceback.print_exc()
                    
            else:
                print("❌ Aucun club trouvé")
                
        print("\n🎉 Diagnostic terminé")
                
except Exception as e:
    print(f"❌ Erreur générale: {e}")
    import traceback
    traceback.print_exc()
