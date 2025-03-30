from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import db, Admin, Slot, Booking, User, ChargingStation, ContactUs, Feedback
from werkzeug.security import check_password_hash, generate_password_hash
import requests

from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin login
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            session['admin_id'] = admin.admin_id
            flash('Login successful!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid credentials.', 'error')
            return redirect(url_for('admin.login'))

    return render_template('admin_login.html')

# Admin dashboard
@admin_bp.route('/dashboard')
def dashboard():
    if 'admin_id' not in session:
        flash('You must log in to access this page.', 'error')
        return redirect(url_for('admin.login'))
    return render_template('admin.html')
@admin_bp.route('/appup')
def appup():
    if 'admin_id' not in session:
        flash('You must log in to access this page.', 'error')
        return redirect(url_for('admin.login'))

    stations = ChargingStation.query.all()
    return render_template('appup.html', stations=stations)
# Logout
@admin_bp.route('/logout')
def logout():
    session.pop('admin_id', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('admin.login'))

# Manage Stations (Admin View)
@admin_bp.route('/stations')
def stations_admin():
    if 'admin_id' not in session:
        flash('You must log in to access this page.', 'error')
        return redirect(url_for('admin.login'))

    stations = ChargingStation.query.all()
    return render_template('managestations.html', stations=stations)



@admin_bp.route('/view_bookings', methods=['GET', 'POST'])
def view_bookings():
    bookings = Booking.query.filter_by(status='Pending').all()  # Fetch pending bookings
    
    
    if request.method == 'POST':
        booking_id = request.form['booking_id']
        action = request.form['action']
        price = request.form.get('price')

        booking = Booking.query.get(booking_id)
        
        if action == 'accept':
            booking.status = 'Accepted'
            booking.price = float(price)  # Admin can set price
        elif action == 'reject':
            booking.status = 'Rejected'
        elif action == 'cancel':
            booking.status = 'Cancelled'

        db.session.commit()
        return redirect(url_for('admin.view_bookings'))
    
    return render_template('view_bookings.html', bookings=bookings)

def calculate_generated_price(kwh):
    # Your price calculation logic based on kWh or other criteria
    return kwh * 0.2  # Example rate per kWh



# Get Coordinates from Location Name
def get_coordinates_from_location(location_name):
    api_key = "pk.218199c167e2d299d7a2ac441eac33b2"  # Replace with your LocationIQ API key
    url = f"https://us1.locationiq.com/v1/search.php?key={api_key}&q={location_name}&format=json"
    response = requests.get(url)
    data = response.json()

    if data:
        lat = float(data[0]['lat'])
        lon = float(data[0]['lon'])
        return lat, lon
    else:
        return None, None

# Add Station
@admin_bp.route('/add_update_delete_view_stations', methods=['GET', 'POST'])
def add_update_delete_view_stations():
    stations = ChargingStation.query.all()

    if request.method == 'POST':
        # Handle different form operations
        if 'add_station' in request.form:
            name = request.form['name']
            location = request.form['location']
            latitude = request.form['latitude']
            longitude = request.form['longitude']
            if name and location and latitude and longitude:
                new_station = ChargingStation(name=name, location=location, latitude=latitude, longitude=longitude)
                db.session.add(new_station)
                db.session.commit()
                flash('Station added successfully!', 'success')
            else:
                flash('All fields are required to add a station.', 'error')

        if 'delete_station' in request.form:
            station_id = int(request.form['station_id'])
            station = ChargingStation.query.get_or_404(station_id)
            db.session.delete(station)
            db.session.commit()
            flash('Station deleted successfully!', 'success')

        if 'update_station' in request.form:
            station_id = int(request.form['station_id'])
            station = ChargingStation.query.get_or_404(station_id)
            station.name = request.form['station_name']
            station.location = request.form['station_location']
            db.session.commit()
            flash('Station updated successfully!', 'success')

        return redirect(url_for('admin.add_update_delete_view_stations'))

    return render_template('appup.html', stations=stations)





def create_slots_for_station(station_id):
    time_ranges = [
        ("06:00 AM", "09:00 AM"),
        ("09:00 AM", "12:00 PM"),
        ("12:00 PM", "03:00 PM"),
        ("03:00 PM", "06:00 PM"),
        ("06:00 PM", "09:00 PM"),
        ("09:00 PM", "12:00 AM"),
        ("12:00 AM", "03:00 AM"),
        ("03:00 PM", "06:00 AM")
        

    ]

    for i, (start, end) in enumerate(time_ranges):
        start_time = datetime.strptime(start, "%I:%M %p").time()
        end_time = datetime.strptime(end, "%I:%M %p").time()

        slot = Slot(
            station_id=station_id,
            slot_name=f"Slot {i+1}",
            start_time=start_time,
            end_time=end_time,
            price=50.0,  # Default price
            availability=10  # Set slot availability
        )
        db.session.add(slot)

    db.session.commit()

@admin_bp.route('/add_station', methods=['GET', 'POST'])
def add_station():
    if request.method == 'POST':
        name = request.form['name']
        location_name = request.form['location']
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')

        if not latitude or not longitude:
            flash('Invalid location name or coordinates not selected.', 'error')
            return redirect(url_for('admin.stations_admin'))

        new_station = ChargingStation(name=name, location=location_name, latitude=latitude, longitude=longitude)
        db.session.add(new_station)
        db.session.commit()

        # Create slots for the newly added station
        create_slots_for_station(new_station.id)

        flash('Charging station added successfully with default slots!', 'success')
        return redirect(url_for('admin.stations_admin'))

    return render_template('admin/stations.html')# Add your form HTML template here


# Edit Station
@admin_bp.route('/update_station', methods=['POST'])
def edit_station():
    station_id = int(request.form['station-id'])
    station = ChargingStation.query.get_or_404(station_id)

    # Update name and location only
    station.name = request.form.get('station-name-edit', station.name)
    station.location = request.form.get('station-location-edit', station.location)

    db.session.commit()
    flash('Station updated successfully!', 'success')
    return redirect(url_for('admin.appup'))


# Delete Station
@admin_bp.route('/delete_station', methods=['POST'])
def delete_station():
    station_id = int(request.form['station-id-delete'])
    station = ChargingStation.query.get_or_404(station_id)

    # Remove manual check and allow database cascade delete to handle it
    db.session.delete(station)
    db.session.commit()

    flash("Station deleted successfully!", "success")
    return redirect(url_for('admin.stations_admin'))



# Toggle Station Status
# Toggle Station Status


@admin_bp.route('/toggle_station', methods=['GET', 'POST'])
def toggle_station():
    if request.method == 'POST':
        station_id = request.form['station_id']
        status = request.form['status']

        # Debugging: Check the data
        print(f"Station ID: {station_id}, New Status: {status}")

        # Fetch the station by ID
        station = ChargingStation.query.get(station_id)
        if station:
            station.status = status  # Update the status
            db.session.commit()  # Commit the changes to the database
            print(f"Updated station {station.name} to status {status}")  # Debugging

        return redirect(url_for('admin.toggle_station'))  

    stations = ChargingStation.query.all()   # Fetch stations
    return render_template('toggle_station.html', stations=stations)


@admin_bp.route('/view_slot_bookings')
def view_slot_bookings():
    bookings = Booking.query.filter_by(status='Pending').all()  
    slots = Slot.query.all()# Fetch all pending bookings
    return render_template('view_slot_bookings.html', bookings=bookings)



@admin_bp.route('/accept_booking/<int:booking_id>', methods=['POST'])
def accept_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if request.method == 'POST':
        price = request.form['price']
        booking.status = 'Accepted'
        booking.price = price  # Admin sets the price
        slot = Slot.query.get(booking.slot_id)  
        if slot:
            if slot.availability > 0:  # Ensure slot is available
                slot.price = price  
                slot.availability -= 1  # Reduce availability

                try:
                    db.session.commit()
                    flash("Booking accepted and price set.", 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f"Error accepting booking: {str(e)}", 'danger')
            else:
                flash("No available slots for this booking.", 'danger')
                db.session.rollback()
        

        return redirect(url_for('admin.view_slot_bookings'))  # Redirect back to the view bookings page

    return render_template('accept_booking.html', booking=booking)



@admin_bp.route('/reject_booking/<int:booking_id>', methods=['POST'])
def reject_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    slot = Slot.query.get(booking.slot_id)  
    if slot and booking.status == 'Accepted':
        slot.availability += 1  # Restore slot availability

    try:
        db.session.commit()
        flash("Booking rejected.", 'success')
    except Exception as e:
        db.session.rollback()
        flash("Error rejecting booking: " + str(e), 'danger')

    return redirect(url_for('admin.view_slot_bookings'))



@admin_bp.route('/update_slot/<int:slot_id>', methods=['GET', 'POST'])
def update_slot(slot_id):
    slot = Slot.query.get_or_404(slot_id)

    if request.method == 'POST':
        slot.station_id = request.form['station_id']
        slot.slot_name = request.form['slot_name']
        slot.price = request.form['price']
        
        db.session.commit()
        flash('Slot updated successfully', 'success')
        return redirect(url_for('admin.manage_slots'))

    # Fetch all stations for the dropdown in the form
    stations = ChargingStation.query.all()
    return render_template('update_slot.html', slot=slot, stations=stations)

@admin_bp.route('/delete_slot/<int:slot_id>', methods=['POST'])
def delete_slot(slot_id):
    slot = Slot.query.get_or_404(slot_id)

    # Delete all bookings that reference the slot
    bookings = Booking.query.filter_by(slot_id=slot_id).all()
    for booking in bookings:
        db.session.delete(booking)

    # Now delete the slot
    db.session.delete(slot)
    db.session.commit()

    flash('Slot and its associated bookings deleted successfully', 'success')
    return redirect(url_for('admin.manage_slots'))


@admin_bp.route('/manage_slots')
def manage_slots():
    slots = Slot.query.all()  # Fetch all slots
    return render_template('manage_slots.html', slots=slots)

# Admin Registration
@admin_bp.route('/register', methods=['GET', 'POST'])
def register_admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for('admin.register_admin'))

        if Admin.query.filter_by(username=username).first():
            flash("Admin with this username already exists.", "error")
            return redirect(url_for('admin.register_admin'))

        hashed_password = generate_password_hash(password)
        new_admin = Admin(username=username, password=hashed_password)
        db.session.add(new_admin)
        db.session.commit()

        flash("Admin registered successfully!", "success")
        return redirect(url_for('admin.login'))

    return render_template('admin_register.html')



@admin_bp.route('/view_users')
def view_users():
    users = User.query.all()  # Fetch all users from the database
    return render_template('view_users.html', users=users)

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)  # Fetch user by ID or return 404 if not found
    try:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted successfully", 'success')
    except Exception as e:
        db.session.rollback()
        flash("Error deleting user: " + str(e), 'danger')
    return redirect(url_for('admin.view_users'))  # Redirect back to the user list

@admin_bp.route('/update_user/<int:user_id>', methods=['GET', 'POST'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)  # Fetch user by ID or return 404 if not found
    if request.method == 'POST':
        user.name = request.form['name']
        user.email = request.form['email']
        user.phone = request.form['phone']
        
        try:
            db.session.commit()
            flash("User updated successfully", 'success')
            return redirect(url_for('admin.view_users'))
        except Exception as e:
            db.session.rollback()
            flash("Error updating user: " + str(e), 'danger')
    
    return render_template('update_user.html', user=user)



@admin_bp.route('/contact_us', methods=['GET'])
def admin_contact_us():
    # Ensure the user is an admin, you can check by user role if needed
   
    # Retrieve all contact messages
    contact_messages = ContactUs.query.all()

    # Fetch user details for each contact message (if needed)
    for contact in contact_messages:
        user = User.query.get(contact.user_id)  # Fetch user details for each contact message
        contact.user_name = user.name if user else 'Unknown'  # Add user name to contact message
    
    return render_template('admin_contact_us.html', contact_messages=contact_messages)


@admin_bp.route('/feedback', methods=['GET'])
def admin_feedback():
    # Ensure the user is an admin
  # Redirect non-admin users to home page

    # Retrieve all feedback messages
    feedback_messages = Feedback.query.all()

    # Fetch user details for each feedback (if needed)
    for feedback in feedback_messages:
        user = User.query.get(feedback.user_id)  # Fetch user details for each feedback
        feedback.user_name = user.name if user else 'Unknown'  # Add user name to feedback

    return render_template('admin_feedback.html', feedback_messages=feedback_messages)

