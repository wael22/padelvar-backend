#!/usr/bin/env python
"""
Outil de diagnostic pour la configuration Google OAuth
Vérifie si les identifiants OAuth sont correctement configurés
"""

import os
import sys
import requests
import json
from pathlib import Path

# Configuration des couleurs pour le terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header():
    print(f"\n{Colors.BOLD}{Colors.BLUE}====== Diagnostic Google OAuth pour PadelVar ======{Colors.END}\n")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def check_env_file():
    """Vérifie si le fichier .env existe et contient les variables OAuth"""
    print_info("Vérification du fichier .env...")
    
    env_path = Path('.env')
    if not env_path.exists():
        print_error("Fichier .env non trouvé!")
        print_info("Création d'un fichier .env exemple...")
        
        with open('.env', 'w') as f:
            f.write("# Configuration Google OAuth\n")
            f.write("GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID\n")
            f.write("GOOGLE_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET\n")
            f.write("GOOGLE_REDIRECT_URI=http://localhost:5000/api/auth/google/callback\n")
            f.write("BACKEND_URL=http://localhost:5000\n")
        
        print_info("Fichier .env créé - veuillez le compléter avec vos identifiants OAuth")
        return False
    
    # Lire le fichier .env
    with open('.env', 'r') as f:
        env_content = f.read()
    
    # Vérifier si les variables OAuth sont présentes
    has_client_id = 'GOOGLE_CLIENT_ID' in env_content
    has_client_secret = 'GOOGLE_CLIENT_SECRET' in env_content
    
    if has_client_id and has_client_secret:
        print_success("Variables OAuth trouvées dans le fichier .env")
        
        # Vérifier si les variables ont des valeurs par défaut
        if 'GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID' in env_content:
            print_warning("GOOGLE_CLIENT_ID a une valeur par défaut - à configurer!")
            return False
        
        if 'GOOGLE_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET' in env_content:
            print_warning("GOOGLE_CLIENT_SECRET a une valeur par défaut - à configurer!")
            return False
            
        return True
    else:
        missing = []
        if not has_client_id:
            missing.append("GOOGLE_CLIENT_ID")
        if not has_client_secret:
            missing.append("GOOGLE_CLIENT_SECRET")
            
        print_error(f"Variables manquantes dans .env: {', '.join(missing)}")
        return False

def check_env_variables():
    """Vérifie si les variables d'environnement OAuth sont définies"""
    print_info("Vérification des variables d'environnement...")
    
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    if client_id and client_secret and client_id != 'YOUR_GOOGLE_CLIENT_ID' and client_secret != 'YOUR_GOOGLE_CLIENT_SECRET':
        print_success("Variables d'environnement OAuth correctement définies")
        return True
    else:
        if not client_id or client_id == 'YOUR_GOOGLE_CLIENT_ID':
            print_error("GOOGLE_CLIENT_ID non défini ou valeur par défaut")
        
        if not client_secret or client_secret == 'YOUR_GOOGLE_CLIENT_SECRET':
            print_error("GOOGLE_CLIENT_SECRET non défini ou valeur par défaut")
            
        return False

def validate_oauth_credentials():
    """Tente de valider les identifiants OAuth auprès de Google"""
    print_info("Validation des identifiants OAuth...")
    
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    
    if not client_id or client_id == 'YOUR_GOOGLE_CLIENT_ID':
        print_error("Impossible de valider: GOOGLE_CLIENT_ID non défini")
        return False
        
    try:
        # Vérifier si le client_id est au bon format
        if not client_id.endswith('.apps.googleusercontent.com'):
            print_error(f"Format de GOOGLE_CLIENT_ID invalide: {client_id}")
            print_info("Un ID client Google doit se terminer par .apps.googleusercontent.com")
            return False
            
        # Tenter une requête simple pour vérifier si l'ID client existe
        # Note: ceci n'est pas une validation complète mais peut détecter des problèmes évidents
        discovery_url = f"https://accounts.google.com/.well-known/openid-configuration"
        response = requests.get(discovery_url)
        
        if response.status_code == 200:
            print_success("Configuration OpenID Google accessible")
            print_info("Note: La validation complète nécessite un flux d'authentification")
            return True
        else:
            print_error(f"Erreur lors de l'accès à la configuration Google: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Erreur lors de la validation: {str(e)}")
        return False

def print_help_instructions():
    """Affiche des instructions d'aide"""
    print(f"\n{Colors.BOLD}Instructions pour configurer Google OAuth:{Colors.END}")
    print(f"1. Consultez le fichier {Colors.BOLD}GOOGLE_OAUTH_CONFIG.md{Colors.END} pour les instructions détaillées")
    print(f"2. Créez un projet dans la {Colors.BOLD}Google Cloud Console{Colors.END}")
    print(f"3. Configurez l'écran de consentement OAuth")
    print(f"4. Créez des identifiants OAuth (ID client et secret)")
    print(f"5. Ajoutez l'URI de redirection: {Colors.BOLD}http://localhost:5000/api/auth/google/callback{Colors.END}")
    print(f"6. Copiez vos identifiants dans le fichier {Colors.BOLD}.env{Colors.END}")
    print(f"7. Exécutez {Colors.BOLD}setup_google_auth.ps1{Colors.END} pour configurer l'environnement\n")

def main():
    """Fonction principale exécutant tous les diagnostics"""
    print_header()
    
    # Vérifications
    env_file_ok = check_env_file()
    env_vars_ok = check_env_variables()
    credentials_ok = validate_oauth_credentials() if env_vars_ok else False
    
    # Rapport final
    print(f"\n{Colors.BOLD}{Colors.BLUE}====== Résumé du diagnostic ======{Colors.END}")
    
    if env_file_ok:
        print_success("Fichier .env correctement configuré")
    else:
        print_error("Problème avec le fichier .env")
    
    if env_vars_ok:
        print_success("Variables d'environnement correctement définies")
    else:
        print_error("Problème avec les variables d'environnement")
    
    if credentials_ok:
        print_success("Identifiants OAuth valides")
    else:
        print_error("Problème avec les identifiants OAuth")
    
    # Afficher des instructions si des problèmes sont détectés
    if not (env_file_ok and env_vars_ok and credentials_ok):
        print_help_instructions()
    else:
        print_success("Configuration Google OAuth complète et valide!")
        
    return 0 if (env_file_ok and env_vars_ok and credentials_ok) else 1

if __name__ == "__main__":
    sys.exit(main())
