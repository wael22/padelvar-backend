import os
import sys

# Ajouter le répertoire src au chemin Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import app



if __name__ == "__main__":
    app.run(debug=True)