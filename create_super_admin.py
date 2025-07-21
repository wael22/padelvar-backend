from src.main import create_app
from src.models.database import db
from src.models.user import User

app = create_app()

with app.app_context():
    # Vérifier si un super admin existe déjà
    super_admin_exists = User.query.filter_by(role=\'super_admin\').first()
    if super_admin_exists:
        print("Un super admin existe déjà. Veuillez le supprimer manuellement si vous souhaitez en créer un nouveau.")
    else:
        username = input("Entrez le nom d\'utilisateur du super admin: ")
        email = input("Entrez l\'adresse email du super admin: ")
        password = input("Entrez le mot de passe du super admin: ")

        new_super_admin = User()
        new_super_admin.username = username
        new_super_admin.email = email
        new_super_admin.role = \'super_admin\'
        new_super_admin.set_password(password)

        db.session.add(new_super_admin)
        db.session.commit()
        print(f"Super admin {username} créé avec succès!")