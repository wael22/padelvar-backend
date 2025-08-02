"""
Script de diagnostic pour tester la configuration OAuth de Google
"""
import os
import json
import requests
import sys

def check_google_oauth_config():
    """Vérifie la configuration OAuth de Google"""
    print("\n===== Diagnostic de la configuration OAuth Google =====\n")
    
    # Vérifier les variables d'environnement
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
    redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI')
    
    if not client_id or client_id == 'YOUR_GOOGLE_CLIENT_ID':
        print("❌ GOOGLE_CLIENT_ID manquant ou non configuré")
        print("   Exécutez setup_google_auth.ps1 après l'avoir modifié avec vos identifiants")
    else:
        print(f"✅ GOOGLE_CLIENT_ID configuré: {client_id[:10]}...{client_id[-5:]}")
        
    if not client_secret or client_secret == 'YOUR_GOOGLE_CLIENT_SECRET':
        print("❌ GOOGLE_CLIENT_SECRET manquant ou non configuré")
    else:
        print(f"✅ GOOGLE_CLIENT_SECRET configuré: {client_secret[:3]}...{client_secret[-3:]}")
        
    if not redirect_uri:
        print("❌ GOOGLE_REDIRECT_URI manquant")
    else:
        print(f"✅ GOOGLE_REDIRECT_URI configuré: {redirect_uri}")
    
    # Vérifier la validité du client ID
    if client_id and client_id != 'YOUR_GOOGLE_CLIENT_ID':
        try:
            discovery_url = "https://accounts.google.com/.well-known/openid-configuration"
            discovery_response = requests.get(discovery_url)
            discovery_data = discovery_response.json()
            
            print("\n--- Tentative de validation des identifiants ---")
            print(f"✅ Configuration OpenID récupérée avec succès")
            
            # Construction d'une URL d'authentification de test
            auth_endpoint = discovery_data.get('authorization_endpoint')
            if auth_endpoint:
                test_url = f"{auth_endpoint}?client_id={client_id}&response_type=code&scope=email%20profile&redirect_uri={redirect_uri}"
                print(f"✅ URL d'authentification de test construite")
                print(f"\nPour tester manuellement, ouvrez cette URL dans votre navigateur:")
                print(f"{test_url}\n")
            
        except Exception as e:
            print(f"❌ Erreur lors de la validation: {e}")
    
    print("\n===== Résolution des problèmes courants =====")
    print("1. Si vous voyez 'The OAuth client was not found':")
    print("   - Vérifiez que le CLIENT_ID est correct")
    print("   - Assurez-vous que votre projet Google Cloud est actif")
    print("   - Vérifiez que l'écran de consentement OAuth est configuré")
    
    print("\n2. Si vous voyez 'redirect_uri_mismatch':")
    print("   - Vérifiez que l'URI de redirection est exactement:")
    print(f"     {redirect_uri}")
    print("   - Ajoutez cette URI dans la console Google Cloud (API & Services > Credentials)")
    
    print("\n3. Si vous voyez d'autres erreurs:")
    print("   - Consultez le fichier GOOGLE_OAUTH_SETUP.md pour des instructions détaillées")
    print("   - Vérifiez les journaux du serveur pour plus d'informations")
    
    print("\n===== Comment exécuter correctement =====")
    print("1. Modifiez setup_google_auth.ps1 avec vos identifiants Google")
    print("2. Exécutez: ./setup_google_auth.ps1")
    print("3. Puis exécutez: python check_google_oauth.py")
    print("4. Redémarrez votre serveur Flask: python app.py")

if __name__ == "__main__":
    check_google_oauth_config()
