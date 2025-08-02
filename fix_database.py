#!/usr/bin/env python3
"""
Script pour diagnostiquer et corriger les problèmes de base de données
"""

import os
import sqlite3
import sys
from werkzeug.security import check_password_hash, generate_password_hash

def check_db_exists():
    """Vérifier si la base de données existe"""
    print("🔍 Vérification de l'existence de la base de données...")
    
    db_paths = [
        'instance/app.db',
        'src/database/app.db',
        'app.db'
    ]
    
    for path in db_paths:
        if os.path.exists(path):
            print(f"✅ Base de données trouvée: {path}")
            return path
        else:
            print(f"❌ Pas trouvée: {path}")
    
    print("❌ Aucune base de données trouvée!")
    return None

def examine_database(db_path):
    """Examiner le contenu de la base de données"""
    print(f"\n🔍 Examen de la base de données: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Lister toutes les tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📊 Tables trouvées: {len(tables)}")
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   - {table_name}: {count} enregistrements")
        
        # Examiner spécifiquement la table user
        if ('user',) in tables:
            print(f"\n👥 Contenu de la table 'user':")
            cursor.execute("SELECT id, email, name, role FROM user")
            users = cursor.fetchall()
            
            for user in users:
                print(f"   ID: {user[0]}, Email: {user[1]}, Nom: {user[2]}, Rôle: {user[3]}")
            
            # Vérifier spécifiquement l'admin
            cursor.execute("SELECT * FROM user WHERE email = ?", ('admin@padelvar.com',))
            admin = cursor.fetchone()
            
            if admin:
                print(f"\n🔑 Détails du compte admin:")
                print(f"   ID: {admin[0]}")
                print(f"   Email: {admin[1]}")
                print(f"   Hash présent: {admin[2] is not None}")
                print(f"   Nom: {admin[3]}")
                
                # Vérifier les colonnes de la table
                cursor.execute("PRAGMA table_info(user)")
                columns = cursor.fetchall()
                print(f"   Colonnes de la table user:")
                for col in columns:
                    print(f"     - {col[1]} ({col[2]})")
                
                return admin
            else:
                print("❌ Compte admin non trouvé!")
                return None
        else:
            print("❌ Table 'user' non trouvée!")
            return None
            
    except Exception as e:
        print(f"❌ Erreur lors de l'examen: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()

def fix_admin_password(db_path):
    """Corriger le mot de passe admin"""
    print(f"\n🔧 Correction du mot de passe admin...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Générer un nouveau hash
        new_password_hash = generate_password_hash('admin123')
        print(f"🔐 Nouveau hash généré: {new_password_hash[:20]}...")
        
        # Mettre à jour le mot de passe
        cursor.execute("UPDATE user SET password_hash = ? WHERE email = ?", 
                      (new_password_hash, 'admin@padelvar.com'))
        
        if cursor.rowcount > 0:
            conn.commit()
            print("✅ Mot de passe admin mis à jour!")
            
            # Vérifier que ça marche
            cursor.execute("SELECT password_hash FROM user WHERE email = ?", ('admin@padelvar.com',))
            stored_hash = cursor.fetchone()[0]
            
            if check_password_hash(stored_hash, 'admin123'):
                print("✅ Vérification réussie: le mot de passe fonctionne!")
                return True
            else:
                print("❌ Erreur: le mot de passe ne fonctionne toujours pas!")
                return False
        else:
            print("❌ Aucune ligne mise à jour - admin non trouvé!")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la correction: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def create_admin_if_missing(db_path):
    """Créer le compte admin s'il n'existe pas"""
    print(f"\n➕ Création du compte admin...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier la structure de la table user
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 Colonnes disponibles: {column_names}")
        
        # Préparer les données admin
        admin_data = {
            'email': 'admin@padelvar.com',
            'password_hash': generate_password_hash('admin123'),
            'name': 'Super Admin',
            'role': 'SUPER_ADMIN'
        }
        
        # Construire la requête d'insertion selon les colonnes disponibles
        if 'role' in column_names:
            cursor.execute("""
                INSERT INTO user (email, password_hash, name, role) 
                VALUES (?, ?, ?, ?)
            """, (admin_data['email'], admin_data['password_hash'], 
                  admin_data['name'], admin_data['role']))
        else:
            cursor.execute("""
                INSERT INTO user (email, password_hash, name) 
                VALUES (?, ?, ?)
            """, (admin_data['email'], admin_data['password_hash'], admin_data['name']))
        
        conn.commit()
        print("✅ Compte admin créé avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    print("🗄️  DIAGNOSTIC ET RÉPARATION BASE DE DONNÉES")
    print("=" * 60)
    
    # 1. Vérifier l'existence de la DB
    db_path = check_db_exists()
    if not db_path:
        print("\n❌ Impossible de continuer sans base de données!")
        print("💡 Essayez de démarrer le serveur Flask une fois pour créer la DB")
        return
    
    # 2. Examiner la base de données
    admin_data = examine_database(db_path)
    
    # 3. Corriger les problèmes
    if admin_data:
        # Admin existe, vérifier/corriger le mot de passe
        if admin_data[2]:  # password_hash existe
            try:
                if check_password_hash(admin_data[2], 'admin123'):
                    print("✅ Mot de passe admin déjà correct!")
                else:
                    print("❌ Mot de passe admin incorrect, correction...")
                    fix_admin_password(db_path)
            except Exception as e:
                print(f"❌ Erreur vérification: {e}")
                print("🔧 Tentative de correction...")
                fix_admin_password(db_path)
        else:
            print("❌ Aucun hash de mot de passe, correction...")
            fix_admin_password(db_path)
    else:
        # Admin n'existe pas, le créer
        print("❌ Admin n'existe pas, création...")
        create_admin_if_missing(db_path)
    
    print(f"\n{'='*60}")
    print("✅ Diagnostic terminé!")
    print("\n🚀 Maintenant vous pouvez:")
    print("1. Démarrer le serveur: python app.py")
    print("2. Vous connecter avec: admin@padelvar.com / admin123")
    print('='*60)

if __name__ == '__main__':
    main()
