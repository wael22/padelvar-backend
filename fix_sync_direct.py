#!/usr/bin/env python3
"""
Correction directe de la synchronisation dans la base de données
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

def fix_sync_database():
    print("🔧 CORRECTION SYNCHRONISATION BASE DE DONNÉES")
    print("=" * 60)
    
    if not os.path.exists('instance/app.db'):
        print("❌ Base de données non trouvée!")
        return False
    
    try:
        conn = sqlite3.connect('instance/app.db')
        cursor = conn.cursor()
        
        print("\n1️⃣ ANALYSE DES DONNÉES ACTUELLES")
        print("-" * 40)
        
        # Récupérer tous les clubs et leurs utilisateurs
        cursor.execute("""
            SELECT c.id, c.name, c.email, c.phone_number, c.address,
                   u.id as user_id, u.name as user_name, u.email as user_email, u.phone_number as user_phone
            FROM club c
            LEFT JOIN user u ON c.id = u.club_id AND u.role = 'CLUB'
            ORDER BY c.id
        """)
        
        clubs_data = cursor.fetchall()
        
        print(f"📊 {len(clubs_data)} club(s) trouvé(s)")
        
        corrections = 0
        created_users = 0
        
        print("\n2️⃣ CORRECTION DES PROBLÈMES")
        print("-" * 40)
        
        for club_data in clubs_data:
            club_id, club_name, club_email, club_phone, club_address, user_id, user_name, user_email, user_phone = club_data
            
            print(f"\n🏢 Club {club_id}: {club_name}")
            
            if user_id is None:
                # Créer un nouvel utilisateur pour ce club
                print(f"   ➕ Création d'un utilisateur pour le club {club_id}")
                
                password_hash = generate_password_hash('club123')  # Mot de passe par défaut
                
                cursor.execute("""
                    INSERT INTO user (email, password_hash, name, role, club_id, phone_number, credits_balance, created_at)
                    VALUES (?, ?, ?, 'CLUB', ?, ?, 0, datetime('now'))
                """, (club_email, password_hash, club_name, club_id, club_phone))
                
                new_user_id = cursor.lastrowid
                print(f"   ✅ Utilisateur {new_user_id} créé (mot de passe: club123)")
                created_users += 1
                
            else:
                # Vérifier la synchronisation
                sync_issues = []
                
                if club_name != user_name:
                    sync_issues.append(f"nom: '{club_name}' ≠ '{user_name}'")
                if club_email != user_email:
                    sync_issues.append(f"email: '{club_email}' ≠ '{user_email}'")
                if club_phone != user_phone:
                    sync_issues.append(f"téléphone: '{club_phone}' ≠ '{user_phone}'")
                
                if sync_issues:
                    print(f"   🔧 Correction de la synchronisation pour utilisateur {user_id}")
                    print(f"      Problèmes: {', '.join(sync_issues)}")
                    
                    # Mettre à jour l'utilisateur avec les données du club
                    cursor.execute("""
                        UPDATE user 
                        SET name = ?, email = ?, phone_number = ?
                        WHERE id = ?
                    """, (club_name, club_email, club_phone, user_id))
                    
                    print(f"   ✅ Utilisateur {user_id} synchronisé")
                    corrections += 1
                else:
                    print(f"   ✅ Utilisateur {user_id} déjà synchronisé")
        
        # Commit des changements
        conn.commit()
        
        print(f"\n3️⃣ RÉSULTATS")
        print("-" * 40)
        print(f"✅ {created_users} utilisateur(s) créé(s)")
        print(f"✅ {corrections} correction(s) appliquée(s)")
        
        # Vérification finale
        print(f"\n4️⃣ VÉRIFICATION FINALE")
        print("-" * 40)
        
        cursor.execute("""
            SELECT c.id, c.name, c.email, c.phone_number,
                   u.id as user_id, u.name as user_name, u.email as user_email, u.phone_number as user_phone
            FROM club c
            LEFT JOIN user u ON c.id = u.club_id AND u.role = 'CLUB'
            ORDER BY c.id
        """)
        
        final_data = cursor.fetchall()
        
        all_sync = True
        for row in final_data:
            club_id, club_name, club_email, club_phone, user_id, user_name, user_email, user_phone = row
            
            if user_id is None:
                print(f"❌ Club {club_id}: Toujours sans utilisateur")
                all_sync = False
            elif (club_name != user_name or club_email != user_email or club_phone != user_phone):
                print(f"❌ Club {club_id}: Toujours désynchronisé")
                all_sync = False
            else:
                print(f"✅ Club {club_id}: Parfaitement synchronisé")
        
        conn.close()
        
        print(f"\n{'='*60}")
        if all_sync:
            print("🎯 SYNCHRONISATION BIDIRECTIONNELLE COMPLÈTE!")
            print("✅ Tous les clubs ont un utilisateur associé")
            print("✅ Toutes les données sont synchronisées")
            print("✅ Vous pouvez maintenant tester les modifications")
        else:
            print("⚠️  Il reste des problèmes de synchronisation")
            print("🔄 Réexécutez ce script si nécessaire")
        
        print("=" * 60)
        
        return all_sync
        
    except Exception as e:
        print(f"❌ Erreur lors de la correction: {e}")
        return False

def create_admin_if_missing():
    print("\n🔑 VÉRIFICATION COMPTES ADMIN")
    print("-" * 40)
    
    try:
        conn = sqlite3.connect('instance/app.db')
        cursor = conn.cursor()
        
        admin_accounts = [
            ('admin@padelvar.com', 'Super Admin'),
            ('admin2@padelvar.com', 'Super Admin 2')
        ]
        
        for admin_email, admin_name in admin_accounts:
            cursor.execute("SELECT id FROM user WHERE email = ? AND role = 'SUPER_ADMIN'", (admin_email,))
            if cursor.fetchone():
                print(f"✅ {admin_email} existe déjà")
            else:
                print(f"➕ Création de {admin_email}")
                password_hash = generate_password_hash('admin123')
                cursor.execute("""
                    INSERT INTO user (email, password_hash, name, role, credits_balance, created_at)
                    VALUES (?, ?, ?, 'SUPER_ADMIN', 100, datetime('now'))
                """, (admin_email, password_hash, admin_name))
                print(f"✅ {admin_email} créé (mot de passe: admin123)")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur création admin: {e}")

def main():
    create_admin_if_missing()
    success = fix_sync_database()
    
    if success:
        print("\n📝 ÉTAPES SUIVANTES:")
        print("1. Démarrez le serveur backend: python app.py")
        print("2. Démarrez le frontend: npm run dev")
        print("3. Testez les modifications de profil club")
        print("4. Vérifiez que les changements apparaissent dans l'admin")

if __name__ == '__main__':
    main()
