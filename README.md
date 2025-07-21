# PadelVar Backend

API backend pour l'application PadelVar - Plateforme de gestion de vidéos de padel.

## 🚀 Démarrage rapide

### Prérequis

- Python 3.11+
- pip

### Installation

1. **Cloner le projet**
   ```bash
   git clone <repository-url>
   cd padelvar-backend
   ```

2. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configuration (optionnel)**
   ```bash
   cp .env.example .env
   # Modifier les variables dans .env selon vos besoins
   ```

4. **Initialiser la base de données**
   ```bash
   python scripts/manage_db.py reset
   ```

5. **Lancer l'application**
   ```bash
   python app.py
   ```

L'API sera accessible sur `http://localhost:5000`

## 📁 Structure du projet

```
padelvar-backend/
├── app.py                 # Point d'entrée principal
├── requirements.txt       # Dépendances Python
├── .env.example          # Variables d'environnement (exemple)
├── instance/             # Dossier de données (base de données)
├── migrations/           # Migrations de base de données
├── scripts/              # Scripts utilitaires
│   ├── init_db.py       # Initialisation de la base
│   ├── create_admin.py  # Création d'administrateur
│   └── manage_db.py     # Gestion de la base de données
└── src/                  # Code source principal
    ├── main.py          # Factory Flask
    ├── config.py        # Configuration centralisée
    ├── models/          # Modèles de données
    │   ├── database.py  # Configuration SQLAlchemy
    │   └── user.py      # Modèles User, Club, Court, Video
    └── routes/          # Routes API
        ├── auth.py      # Authentification
        ├── admin.py     # Administration
        ├── clubs.py     # Gestion des clubs
        ├── players.py   # Gestion des joueurs
        ├── videos.py    # Gestion des vidéos
        └── frontend.py  # Routes frontend
```

## 🔧 Configuration

### Variables d'environnement

Créez un fichier `.env` basé sur `.env.example` :

```bash
# Environnement Flask
FLASK_ENV=development

# Sécurité
SECRET_KEY=votre_cle_secrete_unique

# Base de données
SQLALCHEMY_ECHO=False

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Administrateur par défaut
ADMIN_EMAIL=admin@padelvar.com
ADMIN_PASSWORD=admin123
ADMIN_NAME=Super Admin
ADMIN_CREDITS=1000

# Serveur
HOST=0.0.0.0
PORT=5000
DEBUG=True
```

### Configurations disponibles

- **development** : Mode développement (par défaut)
- **production** : Mode production
- **testing** : Mode test

## 🗄️ Base de données

### Gestion des migrations

```bash
# Initialiser les migrations
python scripts/manage_db.py init

# Créer une nouvelle migration
python scripts/manage_db.py migrate -m "Description de la migration"

# Appliquer les migrations
python scripts/manage_db.py upgrade

# Annuler la dernière migration
python scripts/manage_db.py downgrade

# Remettre à zéro la base de données
python scripts/manage_db.py reset
```

### Création d'un administrateur

```bash
python scripts/create_admin.py email@example.com motdepasse --name "Nom Admin"
```

## 🌐 API Endpoints

### Santé de l'API
- `GET /api/health` - Vérification du statut de l'API

### Authentification
- `POST /api/auth/login` - Connexion
- `POST /api/auth/register` - Inscription
- `POST /api/auth/logout` - Déconnexion

### Administration
- `GET /api/admin/users` - Liste des utilisateurs
- `POST /api/admin/clubs` - Créer un club
- `PUT /api/admin/users/{id}` - Modifier un utilisateur

### Clubs
- `GET /api/clubs` - Liste des clubs
- `GET /api/clubs/{id}` - Détails d'un club
- `POST /api/clubs/{id}/follow` - Suivre un club

### Joueurs
- `GET /api/players` - Liste des joueurs
- `GET /api/players/{id}` - Profil d'un joueur

### Vidéos
- `GET /api/videos` - Liste des vidéos
- `POST /api/videos` - Uploader une vidéo
- `GET /api/videos/{id}` - Détails d'une vidéo

## 🔒 Sécurité

### Authentification par défaut

- **Email** : admin@padelvar.com
- **Mot de passe** : admin123

⚠️ **Important** : Changez ces identifiants en production !

### CORS

L'API est configurée pour accepter les requêtes depuis :
- `http://localhost:5173` (Vite/React)
- `http://localhost:3000` (Create React App)

Modifiez `CORS_ORIGINS` dans `.env` pour ajouter d'autres origines.

## 🚀 Déploiement

### Mode production

1. **Définir les variables d'environnement**
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY=votre_cle_secrete_unique_et_complexe
   ```

2. **Utiliser un serveur WSGI**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 "src.main:create_app('production')"
   ```

### Docker (optionnel)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "src.main:create_app('production')"]
```

## 🛠️ Développement

### Structure des modèles

- **User** : Utilisateurs (joueurs, clubs, admins)
- **Club** : Clubs de padel
- **Court** : Terrains de padel
- **Video** : Vidéos de matchs
- **ClubHistory** : Historique des actions

### Ajout de nouvelles fonctionnalités

1. Créer les modèles dans `src/models/`
2. Ajouter les routes dans `src/routes/`
3. Créer une migration : `python scripts/manage_db.py migrate -m "Description"`
4. Appliquer la migration : `python scripts/manage_db.py upgrade`

## 📝 Logs

Les logs SQLAlchemy sont activés en mode développement. Pour les désactiver :

```bash
export SQLALCHEMY_ECHO=False
```

## 🐛 Dépannage

### Problèmes courants

1. **Erreur de base de données** : Vérifiez les permissions du dossier `instance/`
2. **Port déjà utilisé** : Changez le port dans `.env` ou tuez le processus existant
3. **Erreur d'importation** : Vérifiez que toutes les dépendances sont installées

### Réinitialisation complète

```bash
# Supprimer la base de données et les migrations
rm -rf instance/ migrations/

# Réinitialiser
python scripts/manage_db.py reset
```

## 📄 Licence

Ce projet est sous licence MIT.

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

