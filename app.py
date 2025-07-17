import os
import sys

# Ajouter le répertoire parent de 'src' au chemin Python
# Cela permet à Python de reconnaître 'src' comme un package de premier niveau
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Importer la fonction de création d'application depuis src.main
# Maintenant que le répertoire parent de src est dans sys.path, on peut importer src.main
from src.main import create_app

# Créer l'instance de l'application en appelant la fonction
app = create_app()

# Ce bloc ne s'exécutera que lorsque vous lancez "python app.py"
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)