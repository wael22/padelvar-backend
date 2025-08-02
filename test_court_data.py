from src.models.user import db, Club, Court
from src.main import create_app

app = create_app()
with app.app_context():
    clubs = Club.query.all()
    print(f'Total clubs: {len(clubs)}')
    
    for club in clubs[:3]:
        print(f'Club: {club.name} (ID: {club.id})')
        courts = Court.query.filter_by(club_id=club.id).all()
        print(f'  Courts: {len(courts)}')
        
        for court in courts:
            print(f'    - {court.name} (ID: {court.id})')
            court_dict = court.to_dict()
            print(f'      to_dict: {court_dict}')
            print(f'      has id: {"id" in court_dict}')
            print(f'      id value: {court_dict.get("id", "MISSING")}')
            print()
