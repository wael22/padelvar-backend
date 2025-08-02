#!/usr/bin/env python3
"""
Serveur HTTP simple pour tester l'authentification
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sqlite3
from urllib.parse import urlparse, parse_qs
import hashlib

class AuthHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Gérer les requêtes CORS OPTIONS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', 'http://localhost:5173')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.end_headers()

    def do_POST(self):
        """Gérer les requêtes POST"""
        if self.path == '/api/auth/login':
            self.handle_login()
        else:
            self.send_error(404)

    def do_GET(self):
        """Gérer les requêtes GET"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', 'http://localhost:5173')
            self.end_headers()
            response = json.dumps({'status': 'OK', 'message': 'Serveur en fonctionnement'})
            self.wfile.write(response.encode())
        elif self.path == '/api/auth/me':
            self.handle_me()
        else:
            self.send_error(404)

    def handle_login(self):
        """Gérer la connexion"""
        try:
            # Lire les données POST
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')
            
            print(f"🔍 Tentative de connexion: {email}")
            print(f"🔑 Mot de passe reçu: {'*' * len(password)}")
            
            # Vérifier dans la base de données
            user = self.get_user_by_email(email)
            print(f"👤 Utilisateur trouvé: {user is not None}")
            
            if user:
                print(f"📝 Nom: {user.get('name')}")
                print(f"🎭 Rôle: {user.get('role')}")
                print(f"🔐 Hash présent: {user.get('password_hash') is not None}")
            
            if user and self.verify_password(password, user.get('password_hash')):
                # Succès
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', 'http://localhost:5173')
                self.send_header('Access-Control-Allow-Credentials', 'true')
                self.end_headers()
                
                response = {
                    'message': 'Connexion réussie',
                    'user': {
                        'id': user['id'],
                        'email': user['email'],
                        'name': user['name'],
                        'role': user['role']
                    }
                }
                self.wfile.write(json.dumps(response).encode())
                print(f"✅ Connexion réussie: {user['name']}")
            else:
                # Échec
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', 'http://localhost:5173')
                self.end_headers()
                
                response = {'error': 'Email ou mot de passe incorrect'}
                self.wfile.write(json.dumps(response).encode())
                print(f"❌ Connexion échouée: {email}")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
            self.send_error(500)

    def handle_me(self):
        """Gérer la route /api/auth/me pour vérifier l'authentification"""
        try:
            # Pour simplifier, on retourne toujours non authentifié
            # Dans un vrai système, on vérifierait le token/session
            self.send_response(401)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', 'http://localhost:5173')
            self.end_headers()
            
            response = {'error': 'Non authentifié'}
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"❌ Erreur /me: {e}")
            self.send_error(500)

    def get_user_by_email(self, email):
        """Récupérer un utilisateur par email"""
        try:
            conn = sqlite3.connect('instance/app.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM user WHERE email = ?", (email,))
            user_data = cursor.fetchone()
            
            if user_data:
                return {
                    'id': user_data[0],
                    'email': user_data[1],
                    'password_hash': user_data[2],
                    'name': user_data[3],
                    'role': user_data[5]
                }
            return None
            
        except Exception as e:
            print(f"❌ Erreur DB: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()

    def verify_password(self, password, password_hash):
        """Vérifier le mot de passe"""
        # Pour simplifier, on accepte le mot de passe admin123 OU on vérifie le hash
        if password == "admin123":
            return True
        
        # Vérification du hash (si disponible)
        try:
            import hashlib
            from werkzeug.security import check_password_hash
            
            # Si c'est un hash Werkzeug
            if password_hash and password_hash.startswith('pbkdf2:'):
                return check_password_hash(password_hash, password)
            
            # Fallback pour hash simple
            if password_hash:
                return hashlib.sha256(password.encode()).hexdigest() == password_hash
                
        except:
            pass
        
        return False

    def log_message(self, format, *args):
        """Supprimer les logs HTTP par défaut"""
        pass

def run_server():
    """Démarrer le serveur"""
    server_address = ('', 5000)
    httpd = HTTPServer(server_address, AuthHandler)
    
    print("🚀 Serveur de test PadelVar démarré")
    print("📍 URL: http://localhost:5000")
    print("🔑 Identifiants:")
    print("   Email: admin@padelvar.com")
    print("   Mot de passe: admin123")
    print("─" * 50)
    print("⏹️  Appuyez sur Ctrl+C pour arrêter")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du serveur...")
        httpd.shutdown()

if __name__ == '__main__':
    run_server()
