from flask import render_template, request, redirect, url_for, flash, session
from flask import current_app as app
from .extensions import db
from .models import User, ParkingSpot, Booking

@app.route('/')
def index():
    spots = ParkingSpot.query.order_by(ParkingSpot.spot_number).all()
    return render_template('index.html', spots=spots)

@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        error = None

        if not username:
            error = 'Username is required.'
        elif not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif User.query.filter_by(username=username).first() is not None:
            error = f"User {username} is already registered."
        elif User.query.filter_by(email=email).first() is not None:
            error = f"Email {email} is already registered."

        if error is None:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Successfully registered! Please log in.', 'success')
            return redirect(url_for('login'))
        
        flash(error, 'error')

    return render_template('register.html')

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        user = User.query.filter_by(username=username).first()

        if user is None:
            error = 'Incorrect username.'
        elif not user.check_password(password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            flash('Login successful!', 'success')
            return redirect(url_for('index'))

        flash(error, 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

from datetime import datetime, timedelta

# Decorator to require login
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to be logged in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/book/<int:spot_id>', methods=('GET', 'POST'))
@login_required
def book_spot(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)

    if request.method == 'POST':
        start_time_str = request.form['start_time']
        end_time_str = request.form['end_time']
        
        start_time = datetime.fromisoformat(start_time_str)
        end_time = datetime.fromisoformat(end_time_str)

        error = None

        if not spot.is_available:
            error = 'This spot is no longer available.'
        elif start_time >= end_time:
            error = 'End time must be after start time.'
        elif start_time < datetime.now():
            error = 'Booking cannot be in the past.'
        
        # A more complex app would check for conflicts in future bookings.
        # For this version, we simplify: booking makes it unavailable until freed.

        if error is None:
            duration_hours = (end_time - start_time).total_seconds() / 3600
            total_cost = round(duration_hours * spot.hourly_rate, 2)

            new_booking = Booking(
                user_id=session['user_id'],
                spot_id=spot.id,
                start_time=start_time,
                end_time=end_time,
                total_cost=total_cost
            )

            spot.is_available = False # Simplified logic
            db.session.add(new_booking)
            db.session.commit()

            flash(f'Successfully booked spot {spot.spot_number}!', 'success')
            return redirect(url_for('my_bookings'))

        flash(error, 'error')

    return render_template('book_spot.html', spot=spot)


@app.route('/my_bookings')
@login_required
def my_bookings():
    now = datetime.now()
    bookings = Booking.query.filter_by(user_id=session['user_id']).order_by(Booking.start_time.desc()).all()
    return render_template('my_bookings.html', bookings=bookings, now=now)

@app.route('/cancel_booking/<int:booking_id>')
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != session['user_id']:
        flash('You do not have permission to cancel this booking.', 'error')
        return redirect(url_for('my_bookings'))

    # In a real app, you might have rules (e.g., can only cancel 24h in advance)
    if booking.status == 'Confirmed':
        booking.status = 'Cancelled'
        
        # Make the spot available again (simplified logic)
        spot = ParkingSpot.query.get(booking.spot_id)
        if spot:
            spot.is_available = True

        db.session.commit()
        flash('Booking has been cancelled.', 'success')
    else:
        flash('This booking cannot be cancelled.', 'error')

    return redirect(url_for('my_bookings'))

# ===== ADMIN ROUTES =====

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

import numpy as np

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    # Basic stats
    total_revenue = db.session.query(db.func.sum(Booking.total_cost)).filter(Booking.status == 'Paid').scalar() or 0
    stats = {
        'total_users': User.query.count(),
        'total_spots': ParkingSpot.query.count(),
        'available_spots': ParkingSpot.query.filter_by(is_available=True).count(),
        'total_bookings': Booking.query.count(),
        'total_revenue': total_revenue
    }

    # Booking duration analytics
    completed_bookings = Booking.query.filter_by(status='Paid').all()
    if completed_bookings:
        durations = [(b.end_time - b.start_time).total_seconds() / 3600 for b in completed_bookings]
        stats['avg_duration'] = np.mean(durations)
        stats['median_duration'] = np.median(durations)
        stats['std_dev_duration'] = np.std(durations)
    
    # Advanced analytics for charts
    charts_data = {}
    bookings_df_data = [{
        'start_time': b.start_time, 
        'total_cost': b.total_cost, 
        'spot_type': b.spot.spot_type
    } for b in completed_bookings]

    if bookings_df_data:
        df = pd.DataFrame(bookings_df_data)
        df['start_time'] = pd.to_datetime(df['start_time'])
        
        # 1. Revenue over last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        revenue_by_day = df[df['start_time'] >= thirty_days_ago].set_index('start_time').resample('D')['total_cost'].sum()
        charts_data['revenue_over_time'] = {
            'labels': revenue_by_day.index.strftime('%Y-%m-%d').tolist(),
            'data': revenue_by_day.values.tolist(),
        }

        # 2. Bookings by hour of day
        bookings_by_hour = df['start_time'].dt.hour.value_counts().sort_index()
        charts_data['bookings_by_hour'] = {
            'labels': [f"{h}:00" for h in bookings_by_hour.index],
            'data': bookings_by_hour.values.tolist(),
        }

        # 3. Revenue by spot type
        revenue_by_spot_type = df.groupby('spot_type')['total_cost'].sum()
        charts_data['revenue_by_spot_type'] = {
            'labels': revenue_by_spot_type.index.tolist(),
            'data': revenue_by_spot_type.values.tolist(),
        }
        
    return render_template('admin_dashboard.html', stats=stats, charts_data=charts_data)

@app.route('/admin/spots')
@login_required
@admin_required
def admin_manage_spots():
    spots = ParkingSpot.query.order_by(ParkingSpot.spot_number).all()
    return render_template('admin_manage_spots.html', spots=spots)

@app.route('/admin/spots/add', methods=('GET', 'POST'))
@login_required
@admin_required
def admin_add_spot():
    if request.method == 'POST':
        spot_number = request.form['spot_number']
        spot_type = request.form['spot_type']
        hourly_rate = float(request.form['hourly_rate'])
        is_available = 'is_available' in request.form

        new_spot = ParkingSpot(
            spot_number=spot_number,
            spot_type=spot_type,
            hourly_rate=hourly_rate,
            is_available=is_available
        )
        db.session.add(new_spot)
        db.session.commit()
        flash('New spot added successfully.', 'success')
        return redirect(url_for('admin_manage_spots'))

    return render_template('admin_edit_spot.html')

@app.route('/admin/spots/edit/<int:spot_id>', methods=('GET', 'POST'))
@login_required
@admin_required
def admin_edit_spot(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    if request.method == 'POST':
        spot.spot_number = request.form['spot_number']
        spot.spot_type = request.form['spot_type']
        spot.hourly_rate = float(request.form['hourly_rate'])
        spot.is_available = 'is_available' in request.form
        db.session.commit()
        flash('Spot updated successfully.', 'success')
        return redirect(url_for('admin_manage_spots'))

    return render_template('admin_edit_spot.html', spot=spot)

@app.route('/admin/spots/delete/<int:spot_id>', methods=('POST',))
@login_required
@admin_required
def admin_delete_spot(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    # Check if there are any active bookings for this spot first
    active_bookings = Booking.query.filter_by(spot_id=spot.id).filter(Booking.status == 'Confirmed').count()
    if active_bookings > 0:
        flash('Cannot delete spot with active bookings.', 'error')
        return redirect(url_for('admin_manage_spots'))

    db.session.delete(spot)
    db.session.commit()
    flash('Spot deleted successfully.', 'success')
    return redirect(url_for('admin_manage_spots'))

import pandas as pd
import io
from flask import make_response

@app.route('/admin/reports/revenue')
@login_required
@admin_required
def download_revenue_report():
    bookings = Booking.query.all()
    if not bookings:
        flash('No booking data to generate a report.', 'error')
        return redirect(url_for('admin_dashboard'))

    # Prepare data for DataFrame
    data = []
    for booking in bookings:
        data.append({
            'Booking ID': booking.id,
            'User': booking.user.username,
            'Spot Number': booking.spot.spot_number,
            'Start Time': booking.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'End Time': booking.end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'Total Cost': booking.total_cost,
            'Status': booking.status
        })
    
    df = pd.DataFrame(data)

    # Create CSV in memory
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=revenue_report.csv'
    response.headers['Content-type'] = 'text/csv'

    return response

@app.route('/admin/bookings')
@login_required
@admin_required
def admin_manage_bookings():
    bookings = Booking.query.order_by(Booking.start_time.desc()).all()
    return render_template('admin_manage_bookings.html', bookings=bookings)

@app.route('/admin/bookings/edit/<int:booking_id>', methods=('GET', 'POST'))
@login_required
@admin_required
def admin_edit_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if request.method == 'POST':
        booking.status = request.form['status']
        # More fields could be editable here if needed
        db.session.commit()
        flash('Booking updated successfully.', 'success')
        return redirect(url_for('admin_manage_bookings'))
    return render_template('admin_edit_booking.html', booking=booking) # Need to create admin_edit_booking.html

@app.route('/admin/bookings/delete/<int:booking_id>', methods=('POST',))
@login_required
@admin_required
def admin_delete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    db.session.delete(booking)
    db.session.commit()
    flash('Booking deleted successfully.', 'success')
    return redirect(url_for('admin_manage_bookings'))

@app.route('/admin/users')
@login_required
@admin_required
def admin_manage_users():
    users = User.query.order_by(User.username).all()
    return render_template('admin_manage_users.html', users=users)

@app.route('/admin/users/toggle_admin/<int:user_id>', methods=('POST',))
@login_required
@admin_required
def admin_toggle_admin_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == session['user_id']: # Prevent admin from revoking their own admin status
        flash('You cannot change your own admin status.', 'error')
        return redirect(url_for('admin_manage_users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    flash(f"Admin status for {user.username} toggled to {user.is_admin}.", 'success')
    return redirect(url_for('admin_manage_users'))

@app.route('/admin/users/delete/<int:user_id>', methods=('POST',))
@login_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == session['user_id']: # Prevent admin from deleting themselves
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin_manage_users'))
    
    db.session.delete(user)
    db.session.commit()
    flash(f"User {user.username} deleted successfully.", 'success')
    return redirect(url_for('admin_manage_users'))

@app.route('/check_in/<int:booking_id>')
@login_required
def check_in(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != session['user_id']:
        flash('You do not have permission to check-in to this booking.', 'error')
        return redirect(url_for('my_bookings'))

    if booking.status == 'Confirmed' and booking.start_time <= datetime.now():
        booking.status = 'Occupied'
        db.session.commit()
        flash('You have successfully checked-in. Happy parking!', 'success')
    else:
        flash('Cannot check-in to this booking.', 'error')
    
    return redirect(url_for('my_bookings'))

@app.route('/check_out/<int:booking_id>')
@login_required
def check_out(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != session['user_id']:
        flash('You do not have permission to check-out from this booking.', 'error')
        return redirect(url_for('my_bookings'))

    if booking.status == 'Occupied':
        booking.status = 'Completed'
        # Ensure the spot is available again
        spot = ParkingSpot.query.get(booking.spot_id)
        if spot:
            spot.is_available = True # This might need more complex logic for simultaneous bookings
        db.session.commit()
        flash('You have successfully checked-out. Your bill is ready!', 'success')
        return redirect(url_for('view_bill', booking_id=booking.id))
    else:
        flash('This booking cannot be checked-out.', 'error')
    
    return redirect(url_for('my_bookings'))

@app.route('/my_bookings/<int:booking_id>/bill')
@login_required
def view_bill(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != session['user_id']:
        flash('You do not have permission to view this bill.', 'error')
        return redirect(url_for('my_bookings'))

    # Calculate duration for display on the bill
    booking.duration_hours = (booking.end_time - booking.start_time).total_seconds() / 3600

    return render_template('bill_slip.html', booking=booking)

@app.route('/my_bookings/<int:booking_id>/pay')
@login_required
def process_payment(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != session['user_id']:
        flash('You do not have permission to pay for this booking.', 'error')
        return redirect(url_for('my_bookings'))

    if booking.status == 'Completed':
        # Simulate payment processing
        # In a real application, this would involve integrating with a payment gateway (Stripe, PayPal etc.)
        # and handling success/failure responses.
        booking.status = 'Paid'
        db.session.commit()
        flash('Payment successful! Your booking is now paid.', 'success')
    else:
        flash('This booking cannot be paid at this time.', 'error')
    
    return redirect(url_for('view_bill', booking_id=booking.id))

@app.route('/admin/bookings/bulk_update', methods=('POST',))
@login_required
@admin_required
def admin_bulk_update_bookings():
    if 'csv_file' not in request.files:
        flash('No file part in the request.', 'error')
        return redirect(url_for('admin_manage_bookings'))
    
    file = request.files['csv_file']
    if file.filename == '':
        flash('No file selected for uploading.', 'error')
        return redirect(url_for('admin_manage_bookings'))

    if file and file.filename.endswith('.csv'):
        try:
            # Use StringIO to process the file in memory without saving it
            csv_data = io.StringIO(file.stream.read().decode('UTF8'))
            df = pd.read_csv(csv_data)

            required_cols = ['booking_id', 'status']
            if not all(col in df.columns for col in required_cols):
                flash(f"CSV must have the following columns: {', '.join(required_cols)}.", 'error')
                return redirect(url_for('admin_manage_bookings'))

            updated_count = 0
            failed_ids = []

            for index, row in df.iterrows():
                booking_id = row['booking_id']
                booking = Booking.query.get(booking_id)

                if booking:
                    # Update status
                    booking.status = row['status']
                    
                    # Update total_cost if the column exists and value is provided
                    if 'total_cost' in df.columns and pd.notna(row['total_cost']):
                        booking.total_cost = float(row['total_cost'])
                    
                    updated_count += 1
                else:
                    failed_ids.append(str(booking_id))
            
            db.session.commit()

            success_message = f"Successfully updated {updated_count} bookings."
            flash(success_message, 'success')
            if failed_ids:
                error_message = f"Could not find bookings with the following IDs: {', '.join(failed_ids)}."
                flash(error_message, 'error')

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while processing the file: {e}", 'error')
    else:
        flash('Invalid file type. Please upload a .csv file.', 'error')

    return redirect(url_for('admin_manage_bookings'))

@app.route('/admin/bookings/template')
@login_required
@admin_required
def admin_download_booking_template():
    """Generates and serves a blank CSV template for bulk booking updates."""
    # Define the CSV headers
    csv_headers = "booking_id,status,total_cost\n"

    # Create a response object
    response = make_response(csv_headers)
    
    # Set the appropriate headers for a file download
    response.headers['Content-Disposition'] = 'attachment; filename=booking_update_template.csv'
    response.headers['Content-type'] = 'text/csv'
    
    return response
