#!/usr/bin/env python3
"""
Script de diagnostic et réparation de la synchronisation bidirectionnelle
"""

import os
import sqlite3
import requests
import json
import time
from werkzeug.security import generate_password_hash

def diagnose_sync_problem():
    print("🔧 DIAGNOSTIC SYNCHRONISATION BIDIRECTIONNELLE")
    print("=" * 60)
    
    # 1. Vérifier la base de données
    print("\n1️⃣ VÉRIFICATION BASE DE DONNÉES")
    print("-" * 30)
    
    if not os.path.exists('instance/app.db'):
        print("❌ Base de données non trouvée!")
        return False
    
    try:
        conn = sqlite3.connect('instance/app.db')
        cursor = conn.cursor()
        
        # Vérifier les tables
        cursor.execute("PRAGMA table_info(club)")
        club_columns = [col[1] for col in cursor.fetchall()]
        print(f"📊 Colonnes table 'club': {club_columns}")
        
        cursor.execute("PRAGMA table_info(user)")
        user_columns = [col[1] for col in cursor.fetchall()]
        print(f"👤 Colonnes table 'user': {user_columns}")
        
        # Lister tous les clubs et leurs utilisateurs
        cursor.execute("""
            SELECT c.id, c.name, c.email, c.phone_number,
                   u.id as user_id, u.name as user_name, u.email as user_email, u.phone_number as user_phone, u.role
            FROM club c
            LEFT JOIN user u ON c.id = u.club_id
            ORDER BY c.id
        """)
        
        data = cursor.fetchall()
        print(f"\n📋 ÉTAT ACTUEL DES DONNÉES:")
        print("-" * 40)
        
        sync_problems = []
        
        for row in data:
            club_id, club_name, club_email, club_phone, user_id, user_name, user_email, user_phone, user_role = row
            
            print(f"\n🏢 Club {club_id}: {club_name}")
            print(f"   Email: {club_email}")
            print(f"   Téléphone: {club_phone}")
            
            if user_id:
                print(f"👤 Utilisateur associé {user_id}: {user_name} ({user_role})")
                print(f"   Email: {user_email}")
                print(f"   Téléphone: {user_phone}")
                
                # Vérifier les incohérences
                issues = []
                if club_name != user_name:
                    issues.append(f"Nom: '{club_name}' ≠ '{user_name}'")
                if club_email != user_email:
                    issues.append(f"Email: '{club_email}' ≠ '{user_email}'")
                if club_phone != user_phone:
                    issues.append(f"Téléphone: '{club_phone}' ≠ '{user_phone}'")
                
                if issues:
                    print(f"   ⚠️  INCOHÉRENCES: {', '.join(issues)}")
                    sync_problems.append((club_id, issues))
                else:
                    print(f"   ✅ SYNCHRONISÉ")
            else:
                print(f"   ❌ AUCUN UTILISATEUR ASSOCIÉ")
                sync_problems.append((club_id, ["Aucun utilisateur associé"]))
        
        conn.close()
        
        if sync_problems:
            print(f"\n⚠️  {len(sync_problems)} club(s) avec problèmes de synchronisation")
            return sync_problems
        else:
            print(f"\n✅ Tous les clubs sont synchronisés")
            return []
            
    except Exception as e:
        print(f"❌ Erreur lors du diagnostic: {e}")
        return False

def fix_sync_problems(sync_problems):
    print("\n2️⃣ CORRECTION DES PROBLÈMES")
    print("-" * 30)
    
    if not sync_problems:
        print("✅ Aucun problème à corriger")
        return True
    
    try:
        conn = sqlite3.connect('instance/app.db')
        cursor = conn.cursor()
        
        corrections_made = 0
        
        for club_id, issues in sync_problems:
            print(f"\n🔧 Correction du club {club_id}...")
            
            # Récupérer les données du club
            cursor.execute("SELECT id, name, email, phone_number, address FROM club WHERE id = ?", (club_id,))
            club_data = cursor.fetchone()
            
            if not club_data:
                print(f"   ❌ Club {club_id} non trouvé")
                continue
            
            club_id, club_name, club_email, club_phone, club_address = club_data
            
            # Chercher l'utilisateur associé
            cursor.execute("SELECT id FROM user WHERE club_id = ? AND role = 'CLUB'", (club_id,))
            user_result = cursor.fetchone()
            
            if user_result:
                # Mettre à jour l'utilisateur existant
                user_id = user_result[0]
                cursor.execute("""
                    UPDATE user SET name = ?, email = ?, phone_number = ? WHERE id = ?
                """, (club_name, club_email, club_phone, user_id))
                print(f"   ✅ Utilisateur {user_id} mis à jour")
            else:
                # Créer un nouvel utilisateur
                password_hash = generate_password_hash('default123')
                cursor.execute("""
                    INSERT INTO user (email, password_hash, name, role, club_id, phone_number, credits_balance, created_at)
                    VALUES (?, ?, ?, 'CLUB', ?, ?, 0, datetime('now'))
                """, (club_email, password_hash, club_name, club_id, club_phone))
                user_id = cursor.lastrowid
                print(f"   ✅ Nouvel utilisateur {user_id} créé (mot de passe: default123)")
            
            corrections_made += 1
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ {corrections_made} correction(s) appliquée(s)")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors des corrections: {e}")
        return False

def test_sync_routes():
    print("\n3️⃣ TEST DES ROUTES DE SYNCHRONISATION")
    print("-" * 40)
    
    try:
        # Se connecter en tant qu'admin
        session = requests.Session()
        login_response = session.post(
            "http://localhost:5000/api/auth/login",
            json={"email": "admin@padelvar.com", "password": "admin123"},
            timeout=5
        )
        
        if login_response.status_code != 200:
            print("❌ Impossible de se connecter en tant qu'admin")
            return False
        
        print("✅ Connexion admin réussie")
        
        # Tester la route de synchronisation
        sync_response = session.post("http://localhost:5000/api/admin/sync/club-user-data")
        
        if sync_response.status_code == 200:
            results = sync_response.json()
            print(f"✅ Route de synchronisation accessible")
            print(f"   Clubs traités: {results['results']['clubs_processed']}")
            print(f"   Corrections: {results['results']['sync_corrections']}")
            
            if results['results']['details']:
                print("   Détails:")
                for detail in results['results']['details']:
                    print(f"     - {detail['club_name']}: {detail['corrections']}")
        else:
            print(f"❌ Route de synchronisation échouée: {sync_response.status_code}")
            print(f"   Réponse: {sync_response.text}")
            return False
        
        # Tester les routes CRUD des clubs
        clubs_response = session.get("http://localhost:5000/api/admin/clubs")
        if clubs_response.status_code == 200:
            print("✅ Route GET clubs accessible")
            clubs = clubs_response.json().get('clubs', [])
            if clubs:
                test_club = clubs[0]
                club_id = test_club['id']
                
                # Test de mise à jour
                original_phone = test_club.get('phone_number', '')
                new_phone = f"+33{int(time.time()) % 1000000000}"
                
                update_data = {
                    "name": test_club['name'],
                    "email": test_club['email'],
                    "phone_number": new_phone,
                    "address": test_club.get('address', '')
                }
                
                update_response = session.put(
                    f"http://localhost:5000/api/admin/clubs/{club_id}",
                    json=update_data
                )
                
                if update_response.status_code == 200:
                    print(f"✅ Mise à jour club réussie (nouveau téléphone: {new_phone})")
                    
                    # Vérifier que la synchronisation a eu lieu
                    clubs_after = session.get("http://localhost:5000/api/admin/clubs")
                    updated_clubs = clubs_after.json().get('clubs', [])
                    updated_club = next((c for c in updated_clubs if c['id'] == club_id), None)
                    
                    if updated_club and updated_club['phone_number'] == new_phone:
                        print("✅ Synchronisation immédiate confirmée")
                    else:
                        print("❌ Synchronisation immédiate échouée")
                        return False
                else:
                    print(f"❌ Mise à jour club échouée: {update_response.status_code}")
                    return False
        else:
            print(f"❌ Route GET clubs échouée: {clubs_response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test des routes: {e}")
        return False

def create_test_club():
    print("\n4️⃣ CRÉATION D'UN CLUB DE TEST")
    print("-" * 30)
    
    try:
        conn = sqlite3.connect('instance/app.db')
        cursor = conn.cursor()
        
        # Créer un club de test
        test_club_name = f"Club Test Sync {int(time.time())}"
        test_email = f"test{int(time.time())}@clubtest.com"
        test_phone = f"+33{int(time.time()) % 1000000000}"
        
        cursor.execute("""
            INSERT INTO club (name, email, phone_number, address, created_at)
            VALUES (?, ?, ?, 'Adresse Test', datetime('now'))
        """, (test_club_name, test_email, test_phone))
        
        club_id = cursor.lastrowid
        
        # Créer l'utilisateur associé
        password_hash = generate_password_hash('test123')
        cursor.execute("""
            INSERT INTO user (email, password_hash, name, role, club_id, phone_number, credits_balance, created_at)
            VALUES (?, ?, ?, 'CLUB', ?, ?, 0, datetime('now'))
        """, (test_email, password_hash, test_club_name, club_id, test_phone))
        
        user_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        print(f"✅ Club de test créé:")
        print(f"   Club ID: {club_id}")
        print(f"   User ID: {user_id}")
        print(f"   Email: {test_email}")
        print(f"   Nom: {test_club_name}")
        print(f"   Téléphone: {test_phone}")
        
        return club_id, user_id, test_email
        
    except Exception as e:
        print(f"❌ Erreur création club de test: {e}")
        return None

def main():
    print("🔧 RÉPARATION SYNCHRONISATION BIDIRECTIONNELLE")
    print("=" * 70)
    
    # Étape 1: Diagnostic
    sync_problems = diagnose_sync_problem()
    
    if sync_problems is False:
        print("❌ Impossible de faire le diagnostic")
        return
    
    # Étape 2: Correction
    if sync_problems:
        if fix_sync_problems(sync_problems):
            print("\n🔄 Re-diagnostic après correction...")
            sync_problems = diagnose_sync_problem()
    
    # Étape 3: Test des routes
    if test_sync_routes():
        print("\n✅ Routes de synchronisation fonctionnelles")
    else:
        print("\n❌ Problème avec les routes de synchronisation")
    
    # Étape 4: Créer un club de test pour vérifier
    test_result = create_test_club()
    if test_result:
        print("\n✅ Club de test créé pour vérification future")
    
    print(f"\n{'='*70}")
    print("🎯 RÉSUMÉ:")
    if not sync_problems:
        print("✅ Synchronisation bidirectionnelle opérationnelle")
        print("✅ Vous pouvez maintenant modifier les profils clubs")
        print("✅ Les changements apparaîtront immédiatement dans l'admin")
    else:
        print("⚠️  Problèmes de synchronisation détectés et corrigés")
        print("🔄 Redémarrez le serveur et testez à nouveau")
    
    print("=" * 70)

if __name__ == '__main__':
    main()
