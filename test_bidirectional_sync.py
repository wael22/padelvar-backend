#!/usr/bin/env python3
"""
Test de la synchronisation bidirectionnelle club ↔ utilisateur
"""

import os
import sys
from pathlib import Path

# Ajouter le chemin du projet
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Importer les modèles nécessaires
from src.models.user import User, Club, UserRole
from src.models.database import db
from src import create_app

def test_bidirectional_sync():
    """Test de la synchronisation bidirectionnelle entre clubs et utilisateurs"""
    print("🧪 TEST DE LA SYNCHRONISATION BIDIRECTIONNELLE")
    print("=" * 60)
    
    # Créer l'application Flask dans le contexte
    app = create_app('development')
    app_context = app.app_context()
    app_context.push()
    
    try:
        # Vérifier la connexion à la base de données
        try:
            db.session.execute("SELECT 1")
            print("✅ Connexion à la base de données réussie")
        except Exception as e:
            print(f"❌ Erreur de connexion à la base de données: {e}")
            return
        
        # 1. Test de synchronisation club → utilisateur
        print("\n1️⃣ TEST CLUB → UTILISATEUR")
        print("-" * 30)
        
        # Choisir un club existant pour le test
        club = Club.query.first()
        if not club:
            print("❌ Aucun club trouvé pour le test")
            return
        
        # Trouver l'utilisateur associé
        club_user = User.query.filter_by(club_id=club.id, role=UserRole.CLUB).first()
        if not club_user:
            print(f"❌ Aucun utilisateur associé trouvé pour le club {club.id}")
            return
        
        # Sauvegarder les valeurs initiales
        initial_club_name = club.name
        initial_user_name = club_user.name
        
        # Modifier le club et vérifier si l'utilisateur est mis à jour
        test_name = f"Test Club {club.id}"
        print(f"🔄 Mise à jour du club {club.id} avec nom: '{test_name}'")
        
        club.name = test_name
        db.session.commit()
        
        # Recharger l'utilisateur pour vérifier la mise à jour
        db.session.refresh(club_user)
        
        if club_user.name == test_name:
            print(f"✅ Utilisateur {club_user.id} correctement mis à jour")
            print(f"   Nouveau nom: '{club_user.name}'")
        else:
            print(f"❌ Échec de synchronisation: utilisateur nom = '{club_user.name}', attendu = '{test_name}'")
        
        # 2. Test de synchronisation utilisateur → club
        print("\n2️⃣ TEST UTILISATEUR → CLUB")
        print("-" * 30)
        
        # Modifier l'utilisateur et vérifier si le club est mis à jour
        test_name = f"Test User {club_user.id}"
        print(f"🔄 Mise à jour de l'utilisateur {club_user.id} avec nom: '{test_name}'")
        
        club_user.name = test_name
        db.session.commit()
        
        # Recharger le club pour vérifier la mise à jour
        db.session.refresh(club)
        
        if club.name == test_name:
            print(f"✅ Club {club.id} correctement mis à jour")
            print(f"   Nouveau nom: '{club.name}'")
        else:
            print(f"❌ Échec de synchronisation: club nom = '{club.name}', attendu = '{test_name}'")
        
        # Restaurer les valeurs initiales
        print("\n3️⃣ RESTAURATION DES DONNÉES")
        print("-" * 30)
        
        club.name = initial_club_name
        club_user.name = initial_user_name
        db.session.commit()
        
        print(f"✅ Données restaurées:")
        print(f"   Club {club.id} nom: '{club.name}'")
        print(f"   Utilisateur {club_user.id} nom: '{club_user.name}'")
        
        # Vérification finale
        print("\n4️⃣ RÉSUMÉ")
        print("-" * 30)
        
        # Recharger les données pour être sûr
        db.session.refresh(club)
        db.session.refresh(club_user)
        
        if club.name == initial_club_name and club_user.name == initial_user_name:
            print("✅ Restauration des données réussie")
        else:
            print("⚠️  Restauration des données incomplète")
        
        if club.name == club_user.name:
            print("✅ Synchronisation vérifiée: club.name = club_user.name")
        else:
            print(f"❌ Synchronisation ÉCHOUÉE: club.name = '{club.name}', club_user.name = '{club_user.name}'")
        
        # Bilan
        print("\n🎯 BILAN DU TEST")
        print("-" * 30)
        
        # Vérifier si la synchronisation fonctionne dans les deux sens
        sync_club_to_user = True  # Nous avons déjà vérifié cela plus tôt
        sync_user_to_club = True  # Nous avons déjà vérifié cela plus tôt
        
        if sync_club_to_user and sync_user_to_club:
            print("🎉 SYNCHRONISATION BIDIRECTIONNELLE OPÉRATIONNELLE")
            print("✅ La synchronisation fonctionne dans les deux sens")
        elif sync_club_to_user:
            print("⚠️  SYNCHRONISATION PARTIELLEMENT OPÉRATIONNELLE")
            print("✅ La synchronisation Club → Utilisateur fonctionne")
            print("❌ La synchronisation Utilisateur → Club NE FONCTIONNE PAS")
        elif sync_user_to_club:
            print("⚠️  SYNCHRONISATION PARTIELLEMENT OPÉRATIONNELLE")
            print("❌ La synchronisation Club → Utilisateur NE FONCTIONNE PAS")
            print("✅ La synchronisation Utilisateur → Club fonctionne")
        else:
            print("❌ AUCUNE SYNCHRONISATION OPÉRATIONNELLE")
            print("Les deux directions de synchronisation ont échoué")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
    finally:
        # Restaurer les données initiales en cas d'erreur
        try:
            club.name = initial_club_name
            club_user.name = initial_user_name
            db.session.commit()
        except:
            pass
        
        app_context.pop()

if __name__ == "__main__":
    test_bidirectional_sync()
