import random
from datetime import datetime, timedelta
from .extensions import db
from .models import User, ParkingSpot, Booking

def seed_data():
    """Generates a large amount of realistic booking data for testing."""
    print("Seeding database with test bookings...")
    
    # Check if there is already a large amount of data
    if Booking.query.count() >= 100:
        print("Database already contains sufficient booking data. Skipping seeding.")
        return

    users = User.query.all()
    spots = ParkingSpot.query.all()

    if not users or not spots:
        print("Cannot seed data without users and parking spots.")
        return

    new_bookings = []
    for _ in range(100):
        # Select random user and spot
        user = random.choice(users)
        spot = random.choice(spots)

        # Generate random start and end times within the last 30 days
        start_time_offset = random.randint(1, 30 * 24) # hours ago
        start_time = datetime.now() - timedelta(hours=start_time_offset)
        
        duration_hours = random.uniform(0.5, 8.0) # 30 mins to 8 hours
        end_time = start_time + timedelta(hours=duration_hours)

        # Calculate cost
        total_cost = round(duration_hours * spot.hourly_rate, 2)

        # Assign a status
        status_choice = random.choices(
            ['Paid', 'Completed', 'Cancelled'], 
            weights=[70, 20, 10], 
            k=1
        )[0]
        
        booking = Booking(
            user_id=user.id,
            spot_id=spot.id,
            start_time=start_time,
            end_time=end_time,
            total_cost=total_cost,
            status=status_choice,
            created_at=start_time - timedelta(minutes=random.randint(5, 60)) # Booking created before start
        )
        new_bookings.append(booking)

    db.session.add_all(new_bookings)
    db.session.commit()
    print(f"Successfully created {len(new_bookings)} new booking entries.")
