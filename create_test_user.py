import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

# Configurez le chemin de la base de données
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'src', 'database', 'app.db')

# Initialisez l'application Flask pour le contexte
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Définition du modèle User (copiez-collez la définition de votre modèle User ici)
# Assurez-vous que cette définition correspond exactement à celle de votre fichier user.py
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False) # Assurez-vous que cette ligne est présente
    role = db.Column(db.String(80), nullable=False, default='player')
    # ... autres colonnes de votre modèle User


    def __repr__(self):
        return f'<User {self.email}>'

# Définition de la table d'association player_club_follows (si elle est dans user.py)
# Si player_club_follows est une relation dans la classe User, vous n'avez pas besoin de la définir ici.
# Si c'est une table séparée comme dans votre log, incluez-la ici.
# Pour l'instant, je vais l'inclure comme une table séparée pour correspondre à l'erreur.
player_club_follows = db.Table(
    'player_club_follows',
    db.Column('player_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('club_id', db.Integer, db.ForeignKey('club.id'), primary_key=True),
    db.Column('followed_at', db.DateTime, default=db.func.now())
)

# Définition du modèle Club (si nécessaire pour les relations)
class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    # Ajoutez d'autres colonnes de votre modèle Club si nécessaire

    def __repr__(self):
        return f'<Club {self.name}>'

with app.app_context():
    # Créez toutes les tables si elles n'existent pas
    db.create_all()

    # Créez un utilisateur de test
    email = 'test@example.com'
    password = 'testpassword'
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    # Vérifiez si l'utilisateur existe déjà
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        print(f"L'utilisateur {email} existe déjà. Mise à jour du mot de passe.")
        existing_user.password = hashed_password
    else:
        new_user = User(email=email, password_hash=hashed_password, role='player', name='Test User')

        db.session.add(new_user)
        print(f"Utilisateur {email} créé avec succès !")

    db.session.commit()

    # Vérifiez si l'utilisateur est bien là
    user = User.query.filter_by(email=email).first()
    if user:
        print(f"Utilisateur trouvé : {user.email}, Rôle : {user.role}")
    else:
        print("Utilisateur non trouvé.")
