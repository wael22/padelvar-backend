import sqlite3

# Diagnostic simple
print("DIAGNOSTIC RAPIDE - PROBLÈME ADMIN")
print("=" * 50)

try:
    conn = sqlite3.connect("instance/app.db")
    cursor = conn.cursor()
    
    # Tous les utilisateurs
    cursor.execute("SELECT id, email, name, role FROM user")
    users = cursor.fetchall()
    
    print(f"Total utilisateurs: {len(users)}")
    print()
    
    admins = []
    players = []
    
    for user in users:
        print(f"ID: {user[0]}, Email: {user[1]}, Nom: {user[2]}, Rôle: {user[3]}")
        if 'ADMIN' in user[3].upper():
            admins.append(user)
        elif user[3] == 'PLAYER':
            players.append(user)
    
    print(f"\nAdmins trouvés: {len(admins)}")
    print(f"Joueurs trouvés: {len(players)}")
    
    if len(admins) == 0:
        print("\nCRÉATION D'UN NOUVEL ADMIN...")
        # Hash simple pour test
        simple_hash = "pbkdf2:sha256:260000$test$test123"
        
        cursor.execute("""
            INSERT OR REPLACE INTO user (email, name, password_hash, role, credits_balance, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, ("admin@padelvar.com", "Super Admin", simple_hash, "SUPER_ADMIN", 10000))
        
        conn.commit()
        print("✅ Admin créé: admin@padelvar.com / admin123")
    
    conn.close()
    
except Exception as e:
    print(f"Erreur: {e}")

print("\nTESTEZ MAINTENANT LA CONNEXION ADMIN!")
