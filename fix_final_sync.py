#!/usr/bin/env python3
"""
Script de correction finale pour la synchronisation bidirectionnelle
Ce script corrige directement les problèmes dans la base de données
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash
import json

# Fonction principale
def fix_bidirectional_sync():
    """
    Répare la synchronisation bidirectionnelle entre clubs et utilisateurs
    """
    
    print("🔧 RÉPARATION SYNCHRONISATION BIDIRECTIONNELLE")
    print("=" * 60)
    
    # Vérifier l'existence de la base de données
    if not os.path.exists('instance/app.db'):
        print("❌ Erreur: Base de données 'instance/app.db' non trouvée!")
        print("💡 Assurez-vous d'être dans le bon répertoire")
        return False
    
    try:
        # Connexion à la base de données
        conn = sqlite3.connect('instance/app.db')
        cursor = conn.cursor()
        
        print("✅ Connexion à la base de données réussie")
        
        # 1. Diagnostic initial
        print("\n1️⃣ DIAGNOSTIC INITIAL")
        print("-" * 30)
        
        # Compter les clubs
        cursor.execute("SELECT COUNT(*) FROM club")
        total_clubs = cursor.fetchone()[0]
        print(f"📊 Clubs dans la base: {total_clubs}")
        
        # Compter les utilisateurs clubs
        cursor.execute("SELECT COUNT(*) FROM user WHERE role = 'CLUB'")
        total_club_users = cursor.fetchone()[0]
        print(f"👤 Utilisateurs clubs: {total_club_users}")
        
        # Identifier les problèmes de synchronisation
        cursor.execute("""
            SELECT c.id, c.name, c.email, c.phone_number,
                   u.id as user_id, u.name as user_name, u.email as user_email, u.phone_number as user_phone
            FROM club c
            LEFT JOIN user u ON c.id = u.club_id AND u.role = 'CLUB'
        """)
        
        clubs_data = cursor.fetchall()
        
        clubs_without_users = []
        desync_clubs = []
        
        for row in clubs_data:
            club_id, club_name, club_email, club_phone, user_id, user_name, user_email, user_phone = row
            
            if user_id is None:
                clubs_without_users.append((club_id, club_name, club_email, club_phone))
            else:
                # Vérifier la synchronisation
                if (club_name != user_name or 
                    club_email != user_email or 
                    club_phone != user_phone):
                    desync_clubs.append((club_id, club_name, club_email, club_phone, user_id))
        
        print(f"⚠️  Clubs sans utilisateur: {len(clubs_without_users)}")
        print(f"⚠️  Clubs désynchronisés: {len(desync_clubs)}")
        
        # 2. Corrections
        print("\n2️⃣ CORRECTIONS")
        print("-" * 30)
        
        corrections_count = 0
        
        # Créer des utilisateurs pour les clubs qui n'en ont pas
        for club_id, club_name, club_email, club_phone in clubs_without_users:
            print(f"➕ Création utilisateur pour club {club_id} ({club_name})")
            
            password_hash = generate_password_hash('club123')
            
            cursor.execute("""
                INSERT INTO user (email, password_hash, name, role, club_id, phone_number, credits_balance, created_at)
                VALUES (?, ?, ?, 'CLUB', ?, ?, 0, datetime('now'))
            """, (club_email, password_hash, club_name, club_id, club_phone))
            
            new_user_id = cursor.lastrowid
            print(f"   ✅ Utilisateur {new_user_id} créé (mot de passe: club123)")
            corrections_count += 1
        
        # Synchroniser les clubs désynchronisés
        for club_id, club_name, club_email, club_phone, user_id in desync_clubs:
            print(f"🔄 Synchronisation club {club_id} avec utilisateur {user_id}")
            
            cursor.execute("""
                UPDATE user 
                SET name = ?, email = ?, phone_number = ?
                WHERE id = ?
            """, (club_name, club_email, club_phone, user_id))
            
            print(f"   ✅ Utilisateur {user_id} synchronisé")
            corrections_count += 1
        
        # 3. Vérifier les comptes admin
        print("\n3️⃣ VÉRIFICATION COMPTES ADMIN")
        print("-" * 30)
        
        admin_accounts = [
            ('admin@padelvar.com', 'Super Admin'),
            ('admin2@padelvar.com', 'Super Admin 2')
        ]
        
        for admin_email, admin_name in admin_accounts:
            cursor.execute("SELECT id FROM user WHERE email = ? AND role = 'SUPER_ADMIN'", (admin_email,))
            admin_exists = cursor.fetchone()
            
            if admin_exists:
                print(f"✅ {admin_email} existe déjà")
            else:
                print(f"➕ Création de {admin_email}")
                password_hash = generate_password_hash('admin123')
                cursor.execute("""
                    INSERT INTO user (email, password_hash, name, role, credits_balance, created_at)
                    VALUES (?, ?, ?, 'SUPER_ADMIN', 100, datetime('now'))
                """, (admin_email, password_hash, admin_name))
                print(f"   ✅ {admin_email} créé (mot de passe: admin123)")
                corrections_count += 1
        
        # Commit des changements
        conn.commit()
        
        # 4. Vérification finale
        print("\n4️⃣ VÉRIFICATION FINALE")
        print("-" * 30)
        
        cursor.execute("""
            SELECT c.id, c.name, c.email, c.phone_number,
                   u.id as user_id, u.name as user_name, u.email as user_email, u.phone_number as user_phone
            FROM club c
            LEFT JOIN user u ON c.id = u.club_id AND u.role = 'CLUB'
        """)
        
        final_data = cursor.fetchall()
        
        final_problems = 0
        for row in final_data:
            club_id, club_name, club_email, club_phone, user_id, user_name, user_email, user_phone = row
            
            if user_id is None:
                print(f"❌ Club {club_id}: Toujours sans utilisateur")
                final_problems += 1
            elif (club_name != user_name or club_email != user_email or club_phone != user_phone):
                print(f"❌ Club {club_id}: Toujours désynchronisé")
                final_problems += 1
            else:
                print(f"✅ Club {club_id}: Parfaitement synchronisé")
        
        conn.close()
        
        # 5. Résumé
        print(f"\n5️⃣ RÉSUMÉ")
        print("-" * 30)
        print(f"🔧 Corrections appliquées: {corrections_count}")
        print(f"⚠️  Problèmes restants: {final_problems}")
        
        if final_problems == 0:
            print("\n🎯 SYNCHRONISATION BIDIRECTIONNELLE RÉPARÉE!")
            print("✅ Tous les clubs ont un utilisateur associé")
            print("✅ Toutes les données sont synchronisées")
            
            print("\n📝 PROCHAINES ÉTAPES:")
            print("1. Démarrez le serveur backend:")
            print("   \"C:/Users/PC/Desktop/1-Padel App/dev/venv/Scripts/python.exe\" app.py")
            print("\n2. Dans un autre terminal, démarrez le frontend:")
            print("   cd ../padelvar-frontend-main")
            print("   npm run dev")
            print("\n3. Testez la synchronisation:")
            print("   - Connectez-vous en tant que club")
            print("   - Modifiez votre profil")
            print("   - Vérifiez dans l'admin que les changements apparaissent")
            
            return True
        else:
            print(f"\n⚠️  Il reste {final_problems} problème(s)")
            print("🔄 Réexécutez ce script si nécessaire")
            return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # Changer vers le bon répertoire si nécessaire
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Exécuter la réparation
    success = fix_bidirectional_sync()
    
    if success:
        print("\n🚀 Synchronisation bidirectionnelle opérationnelle!")
    else:
        print("\n❌ Certains problèmes n'ont pas pu être résolus")
        print("💡 Vérifiez les messages d'erreur ci-dessus")
