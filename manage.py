import os
import sys
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from main import create_app
from models.database import db
from models.user import User, UserRole

app = create_app()

@app.cli.command("init-db")
def init_db_command():
    """Crée les tables de la DB et l'utilisateur admin."""
    with app.app_context():
        db.create_all()
        print("✅ Base de données initialisée et tables créées.")

        if User.query.filter_by(email='admin@padelvar.com').first():
            print("ℹ️ L'utilisateur Super Admin existe déjà.")
        else:
            super_admin = User(
                email='admin@padelvar.com',
                password_hash=generate_password_hash('admin123'),
                name='Super Admin',
                role=UserRole.SUPER_ADMIN,
                credits_balance=1000
            )
            db.session.add(super_admin)
            db.session.commit()
            print("✅ Super admin créé: admin@padelvar.com / admin123")


