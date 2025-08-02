#!/usr/bin/env python3
"""
Test rapide de synchronisation
"""

import sqlite3
import os

def check_sync():
    print("🔍 VÉRIFICATION SYNCHRONISATION")
    print("=" * 50)
    
    if not os.path.exists('instance/app.db'):
        print("❌ Base de données non trouvée!")
        return
    
    conn = sqlite3.connect('instance/app.db')
    cursor = conn.cursor()
    
    print("\n📊 CLUBS ET UTILISATEURS:")
    print("-" * 30)
    
    cursor.execute("""
        SELECT c.id, c.name, c.email, c.phone_number,
               u.id as user_id, u.name as user_name, u.email as user_email, u.phone_number as user_phone
        FROM club c
        LEFT JOIN user u ON c.id = u.club_id AND u.role = 'CLUB'
        ORDER BY c.id
    """)
    
    results = cursor.fetchall()
    
    for row in results:
        club_id, club_name, club_email, club_phone, user_id, user_name, user_email, user_phone = row
        
        print(f"\n🏢 Club {club_id}:")
        print(f"  Nom: {club_name}")
        print(f"  Email: {club_email}")
        print(f"  Téléphone: {club_phone}")
        
        if user_id:
            print(f"👤 Utilisateur {user_id}:")
            print(f"  Nom: {user_name}")
            print(f"  Email: {user_email}")
            print(f"  Téléphone: {user_phone}")
            
            # Vérifier synchronisation
            sync_ok = (club_name == user_name and 
                      club_email == user_email and 
                      club_phone == user_phone)
            
            if sync_ok:
                print("  ✅ SYNCHRONISÉ")
            else:
                print("  ❌ DÉSYNCHRONISÉ")
                if club_name != user_name:
                    print(f"    Nom: '{club_name}' ≠ '{user_name}'")
                if club_email != user_email:
                    print(f"    Email: '{club_email}' ≠ '{user_email}'")
                if club_phone != user_phone:
                    print(f"    Téléphone: '{club_phone}' ≠ '{user_phone}'")
        else:
            print("  ❌ AUCUN UTILISATEUR ASSOCIÉ")
    
    conn.close()

if __name__ == '__main__':
    check_sync()
