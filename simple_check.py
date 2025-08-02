import sqlite3
import sys
import os

print("=== DEBUT SCRIPT ===")

try:
    print("Connexion à la base de données...")
    conn = sqlite3.connect('instance/app.db')
    cursor = conn.cursor()
    print("Connexion réussie!")
    
    print("\nVérification des tables...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables trouvées: {[t[0] for t in tables]}")
    
    print("\nVérification des clubs...")
    cursor.execute("SELECT COUNT(*) FROM club")
    club_count = cursor.fetchone()[0]
    print(f"Nombre de clubs: {club_count}")
    
    if club_count > 0:
        print("\nDétails des clubs:")
        cursor.execute("SELECT id, name, email FROM club LIMIT 5")
        clubs = cursor.fetchall()
        for club in clubs:
            print(f"  Club {club[0]}: {club[1]} ({club[2]})")
    
    print("\nVérification des utilisateurs...")
    cursor.execute("SELECT COUNT(*) FROM user WHERE role = 'CLUB'")
    club_users_count = cursor.fetchone()[0]
    print(f"Nombre d'utilisateurs clubs: {club_users_count}")
    
    if club_users_count > 0:
        print("\nDétails des utilisateurs clubs:")
        cursor.execute("SELECT id, name, email, club_id FROM user WHERE role = 'CLUB' LIMIT 5")
        users = cursor.fetchall()
        for user in users:
            print(f"  User {user[0]}: {user[1]} ({user[2]}) - Club ID: {user[3]}")
    
    print("\nVérification de la synchronisation...")
    cursor.execute("""
        SELECT c.id, c.name, c.email, u.id as user_id, u.name as user_name, u.email as user_email
        FROM club c
        LEFT JOIN user u ON c.id = u.club_id AND u.role = 'CLUB'
        LIMIT 10
    """)
    
    sync_data = cursor.fetchall()
    sync_problems = 0
    
    for row in sync_data:
        club_id, club_name, club_email, user_id, user_name, user_email = row
        print(f"\nClub {club_id}: {club_name} ({club_email})")
        
        if user_id:
            print(f"  -> User {user_id}: {user_name} ({user_email})")
            if club_name != user_name or club_email != user_email:
                print("  ❌ DÉSYNCHRONISÉ")
                sync_problems += 1
            else:
                print("  ✅ SYNCHRONISÉ")
        else:
            print("  ❌ AUCUN UTILISATEUR ASSOCIÉ")
            sync_problems += 1
    
    print(f"\nProblèmes de synchronisation: {sync_problems}")
    
    conn.close()
    print("\nConnexion fermée.")
    
except Exception as e:
    print(f"ERREUR: {e}")
    import traceback
    traceback.print_exc()

print("=== FIN SCRIPT ===")
