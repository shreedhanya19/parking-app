from .extensions import db
from .models import User, ParkingSpot

def init_db():
    """Initializes the database with some data."""
    # Check if we already have an admin user
    if User.query.filter_by(username='admin').first() is None:
        print("Creating admin user...")
        admin_user = User(username='admin', email='admin@example.com', is_admin=True)
        admin_user.set_password('admin')
        db.session.add(admin_user)
        db.session.commit()
    
    # Check if we already have parking spots
    if ParkingSpot.query.count() == 0:
        print("Creating initial parking spots...")
        spots = []
        for i in range(1, 11):
            spot = ParkingSpot(spot_number=f'A{i}', spot_type='Compact', hourly_rate=5.0)
            spots.append(spot)
        for i in range(11, 21):
            spot = ParkingSpot(spot_number=f'B{i}', spot_type='SUV', hourly_rate=7.5)
            spots.append(spot)
        db.session.add_all(spots)
        db.session.commit()

    print("Database initialized.")
