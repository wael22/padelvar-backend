#!/usr/bin/env python3
"""
Script de diagnostic complet pour PadelVar
"""

import os
import sqlite3
import subprocess
import sys
import time
import requests
from werkzeug.security import check_password_hash, generate_password_hash

def print_section(title):
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

def check_files():
    print_section("VÉRIFICATION DES FICHIERS")
    
    files_to_check = [
        'instance/app.db',
        'app.py', 
        'simple_server.py',
        'src/main.py',
        'src/routes/auth.py',
        'src/routes/admin.py'
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} MANQUANT")

def check_database():
    print_section("VÉRIFICATION BASE DE DONNÉES")
    
    try:
        if not os.path.exists('instance/app.db'):
            print("❌ Base de données non trouvée!")
            return False
            
        conn = sqlite3.connect('instance/app.db')
        cursor = conn.cursor()
        
        # Vérifier les tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📊 Tables trouvées: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Vérifier et créer les comptes admin
        admin_accounts = [
            ('admin@padelvar.com', 'Super Admin'),
            ('admin2@padelvar.com', 'Super Admin 2')
        ]
        
        admin_found = False
        
        for admin_email, admin_name in admin_accounts:
            cursor.execute("SELECT id, email, password_hash, name, role FROM user WHERE email = ?", (admin_email,))
            admin_data = cursor.fetchone()
            
            if admin_data:
                print(f"\n✅ Compte admin trouvé: {admin_email}")
                print(f"   ID: {admin_data[0]}")
                print(f"   Email: {admin_data[1]}")
                print(f"   Nom: {admin_data[3]}")
                print(f"   Rôle: {admin_data[4]}")
                
                # Tester le mot de passe
                if admin_data[2]:
                    try:
                        password_ok = check_password_hash(admin_data[2], 'admin123')
                        print(f"   Mot de passe valide: {password_ok}")
                        
                        if not password_ok:
                            print("🔧 Correction du mot de passe...")
                            new_hash = generate_password_hash('admin123')
                            cursor.execute("UPDATE user SET password_hash = ? WHERE email = ?", 
                                         (new_hash, admin_email))
                            conn.commit()
                            print("✅ Mot de passe corrigé!")
                            
                    except Exception as e:
                        print(f"❌ Erreur vérification mot de passe: {e}")
                else:
                    print("❌ Aucun hash de mot de passe!")
                
                admin_found = True
            else:
                print(f"\n➕ Création du compte admin: {admin_email}")
                try:
                    new_hash = generate_password_hash('admin123')
                    cursor.execute("""
                        INSERT INTO user (email, password_hash, name, role, credits_balance, created_at) 
                        VALUES (?, ?, ?, ?, ?, datetime('now'))
                    """, (admin_email, new_hash, admin_name, 'SUPER_ADMIN', 100))
                    conn.commit()
                    print(f"✅ Compte {admin_email} créé avec succès!")
                    admin_found = True
                except Exception as e:
                    print(f"❌ Erreur création {admin_email}: {e}")
        
        if not admin_found:
            print("❌ Aucun compte admin trouvé ou créé!")
            return False
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur base de données: {e}")
        return False

def check_sync_integrity():
    print_section("VÉRIFICATION SYNCHRONISATION CLUB-ADMIN")
    
    try:
        if not os.path.exists('instance/app.db'):
            print("❌ Base de données non trouvée!")
            return False
            
        conn = sqlite3.connect('instance/app.db')
        cursor = conn.cursor()
        
        # Vérifier les clubs et leurs utilisateurs associés
        cursor.execute("""
            SELECT c.id, c.name, c.email, c.phone_number,
                   u.id as user_id, u.name as user_name, u.email as user_email, u.phone_number as user_phone
            FROM club c
            LEFT JOIN user u ON c.id = u.club_id AND u.role = 'CLUB'
        """)
        
        clubs_data = cursor.fetchall()
        sync_issues = []
        
        print(f"📊 Vérification de {len(clubs_data)} club(s):")
        
        for club_data in clubs_data:
            club_id, club_name, club_email, club_phone, user_id, user_name, user_email, user_phone = club_data
            
            if user_id is None:
                sync_issues.append(f"Club {club_id} ({club_name}) sans utilisateur associé")
                print(f"   ❌ Club {club_id}: Aucun utilisateur associé")
            else:
                issues = []
                if club_name != user_name:
                    issues.append(f"nom: '{club_name}' ≠ '{user_name}'")
                if club_email != user_email:
                    issues.append(f"email: '{club_email}' ≠ '{user_email}'")
                if club_phone != user_phone:
                    issues.append(f"téléphone: '{club_phone}' ≠ '{user_phone}'")
                
                if issues:
                    sync_issues.append(f"Club {club_id} ({club_name}): {', '.join(issues)}")
                    print(f"   ⚠️  Club {club_id}: Désynchronisé - {', '.join(issues)}")
                else:
                    print(f"   ✅ Club {club_id}: Synchronisé")
        
        if sync_issues:
            print(f"\n⚠️  {len(sync_issues)} problème(s) de synchronisation détecté(s):")
            for issue in sync_issues:
                print(f"     - {issue}")
            print("\n💡 Utilisez la route /api/admin/sync/club-user-data pour corriger")
        else:
            print("\n✅ Tous les clubs sont correctement synchronisés!")
        
        conn.close()
        return len(sync_issues) == 0
        
    except Exception as e:
        print(f"❌ Erreur vérification synchronisation: {e}")
        return False

def check_ports():
    print_section("VÉRIFICATION DES PORTS")
    
    ports_to_check = [
        (5000, "Backend Flask"),
        (5173, "Frontend React")
    ]
    
    for port, description in ports_to_check:
        try:
            response = requests.get(f"http://localhost:{port}", timeout=2)
            print(f"✅ Port {port} ({description}): Accessible")
        except requests.exceptions.ConnectionError:
            print(f"❌ Port {port} ({description}): Non accessible")
        except Exception as e:
            print(f"⚠️  Port {port} ({description}): {e}")

def test_authentication():
    print_section("TEST D'AUTHENTIFICATION")
    
    admin_accounts = [
        'admin@padelvar.com',
        'admin2@padelvar.com'
    ]
    
    for admin_email in admin_accounts:
        try:
            # Test de login
            login_data = {
                "email": admin_email,
                "password": "admin123"
            }
            
            print(f"🔑 Test de connexion {admin_email}...")
            response = requests.post(
                "http://localhost:5000/api/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            print(f"📊 Statut: {response.status_code}")
            if response.status_code == 200:
                print(f"✅ Authentification réussie pour {admin_email}!")
            else:
                print(f"❌ Échec authentification pour {admin_email}")
                print(f"📄 Réponse: {response.text}")
                
        except Exception as e:
            print(f"❌ Erreur test auth {admin_email}: {e}")
        print()  # Ligne vide entre les tests

def show_recommendations():
    print_section("RECOMMANDATIONS")
    
    print("📋 Pour démarrer l'application correctement:")
    print()
    print("1. Backend (Terminal 1):")
    print("   cd padelvar-backend-main")
    print("   python app.py")
    print()
    print("2. Frontend (Terminal 2):")
    print("   cd padelvar-frontend-main") 
    print("   npm run dev")
    print()
    print("3. Accéder à l'application:")
    print("   http://localhost:5173")
    print()
    print("4. Identifiants admin:")
    print("   Option 1:")
    print("     Email: admin@padelvar.com")
    print("     Mot de passe: admin123")
    print("   Option 2:")
    print("     Email: admin2@padelvar.com")
    print("     Mot de passe: admin123")

def main():
    print("🧪 DIAGNOSTIC COMPLET PADELVAR")
    print(f"📅 Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    check_files()
    db_ok = check_database()
    sync_ok = check_sync_integrity()
    check_ports()
    
    if db_ok:
        test_authentication()
    
    show_recommendations()
    
    print(f"\n{'='*60}")
    print("✅ Diagnostic terminé!")
    print('='*60)

if __name__ == '__main__':
    main()
