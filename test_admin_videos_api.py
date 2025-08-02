"""
Script pour tester l'accès à l'API admin/videos
"""
import requests
import json
import sys

def test_admin_videos_api():
    """Tester l'accès à l'API admin/videos"""
    url = "http://localhost:5000/api/admin/videos"
    
    try:
        response = requests.get(url)
        
        # Écrire la réponse dans un fichier
        with open("api_response.txt", "w") as f:
            f.write(f"Status code: {response.status_code}\n")
            f.write(f"Headers: {json.dumps(dict(response.headers), indent=2)}\n\n")
            
            if response.status_code == 200:
                f.write("Contenu de la réponse:\n")
                try:
                    f.write(json.dumps(response.json(), indent=2))
                except:
                    f.write(response.text)
            else:
                f.write(f"Erreur {response.status_code}: {response.text}")
        
        print(f"Test terminé. Status: {response.status_code}")
        print("Voir api_response.txt pour les détails")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Erreur lors du test: {e}")
        with open("api_response.txt", "w") as f:
            f.write(f"Erreur: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_admin_videos_api()
    sys.exit(0 if success else 1)
