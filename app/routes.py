from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import db, User, EVVehicle, ContactUs, Feedback, ChargingStation, Booking, Slot
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from flask import jsonify, request
import math
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime
bp = Blueprint('main', __name__)
API_KEY = 'pk.218199c167e2d299d7a2ac441eac33b2'
import requests

def get_coordinates_from_location(location):
    api_key = 'pk.218199c167e2d299d7a2ac441eac33b2'  # Replace with your actual LocationIQ API key
    url = f'https://us1.locationiq.com/v1/search.php?key={api_key}&q={location}&format=json'

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data:
            latitude = float(data[0]['lat'])
            longitude = float(data[0]['lon'])
            print(f"User location: {latitude}, {longitude}")  # Debugging the user's coordinates
            return latitude, longitude
    # Debugging: If the coordinates aren't fetched properly, log it.
    print(f"Failed to fetch coordinates for location: {location}")
    return None, None  # Return None if location is not found

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/home')
def home():
    return render_template('home.html')

# Profile Page (Requires User to Be Logged In)
@bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash('Please log in to view your profile.', 'danger')
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        # Update profile details
        user.name = request.form['name']
        user.email = request.form['email']
        user.phone = request.form['phone']
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('main.profile'))
    
    return render_template('profile.html', user=user)

# Change Password (Requires User to Be Logged In)
@bp.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        
        # Check if the current password is correct
        if not check_password_hash(user.password, current_password):
            return "Incorrect password", 400
        
        user.password = generate_password_hash(new_password)
        
        db.session.commit()
        flash('Password changed successfully!', 'success')
        return redirect(url_for('main.profile'))
    
    return render_template('change_password.html')

# User Dashboard (Requires User to Be Logged In)
@bp.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        flash('Please log in to access the dashboard.', 'danger')
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])
    return render_template('user_dashboard.html', user=user)

# Login Route
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Find user by email
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            # Login success
            session['user_id'] = user.user_id
            session['user_name'] = user.name
            flash('Login successful!', 'success')
            return redirect(url_for('main.user_dashboard'))
        else:
            flash('Invalid email or password!', 'danger')
            return redirect(url_for('main.login'))
    
    return render_template('login.html')

# Logout Route
@bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.home'))

# Registration Route
@bp.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        name = request.form['fullname']
        email = request.form['email']
        phone = request.form['Phone Number']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validate passwords
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('main.register_user'))

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email is already registered!', 'danger')
            return redirect(url_for('main.register_user'))

        # Save user to database
        hashed_password = generate_password_hash(password)
        user = User(name=name, email=email, password=hashed_password, phone=phone)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful!', 'success')
        return redirect(url_for('main.home'))
    
    return render_template('home.html')

# Forgot Password Route
@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if user:
            # Send reset password email logic here
            flash('If the email exists, password recovery instructions have been sent.', 'info')
        else:
            flash('No account found with this email address.', 'danger')
        return redirect(url_for('main.login'))
    
    return render_template('forgot_password.html')

# Contact For
    

# Vehicle Management Routes
@bp.route('/manage_vehicles')
def manage_vehicles():
    if 'user_id' not in session:
        flash('Please log in to manage vehicles.', 'danger')
        return redirect(url_for('main.login'))
    
    return render_template('manage_vehicles.html')

# View All Vehicles
@bp.route('/vehicles')
def view_vehicles():
    if 'user_id' not in session:
        flash('Please log in to view your vehicles.', 'danger')
        return redirect(url_for('main.login'))

    user_id = session['user_id']
    vehicles = EVVehicle.query.filter_by(user_id=user_id).all()  # Filter by logged-in user's ID
    return render_template('view_vehicles.html', vehicles=vehicles)


# Add a New Vehicle (Requires User to Be Logged In)
@bp.route('/add_vehicle', methods=['GET', 'POST'])
def add_vehicle():
    if 'user_id' not in session:
        flash('Please log in to add a vehicle.', 'danger')
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        vehicle_name = request.form['vehicle_name']
        vehicle_type = request.form['vehicle_type']
        license_plate = request.form['license_plate']
        battery_capacity = request.form['battery_capacity']
        range_per_charge = request.form['range_per_charge']
        
        new_vehicle = EVVehicle(
            user_id=session['user_id'],  # Use the user_id from the session
            vehicle_name=vehicle_name,
            vehicle_type=vehicle_type,
            license_plate=license_plate,
            battery_capacity=battery_capacity,
            range_per_charge=range_per_charge
        )
        
        db.session.add(new_vehicle)
        db.session.commit()
        flash('Vehicle added successfully', 'success')
        return redirect(url_for('main.view_vehicles'))  # Update the URL endpoint
        
    return render_template('add_vehicle.html')

# Update an Existing Vehicle (Requires User to Be Logged In)
@bp.route('/update_vehicle/<int:vehicle_id>', methods=['GET', 'POST'])
def update_vehicle(vehicle_id):
    if 'user_id' not in session:
        flash('Please log in to update a vehicle.', 'danger')
        return redirect(url_for('main.login'))
    
    vehicle = EVVehicle.query.get_or_404(vehicle_id)  # Get vehicle by ID
    
    if request.method == 'POST':
        vehicle.vehicle_name = request.form['vehicle_name']
        vehicle.vehicle_type = request.form['vehicle_type']
        vehicle.license_plate = request.form['license_plate']
        vehicle.battery_capacity = request.form['battery_capacity']
        vehicle.range_per_charge = request.form['range_per_charge']
        
        db.session.commit()
        flash('Vehicle updated successfully', 'success')
        return redirect(url_for('main.view_vehicles'))  # Update the URL endpoint
    
    return render_template('update_vehicle.html', vehicle=vehicle)

# Delete a Vehicle (Requires User to Be Logged In)
@bp.route('/delete_vehicle/<int:vehicle_id>', methods=['GET'])
def delete_vehicle(vehicle_id):
    if 'user_id' not in session:
        flash('Please log in to delete a vehicle.', 'danger')
        return redirect(url_for('main.login'))
    
    vehicle = EVVehicle.query.get_or_404(vehicle_id)  # Get vehicle by ID
    db.session.delete(vehicle)
    db.session.commit()
    flash('Vehicle deleted successfully', 'danger')
    return redirect(url_for('main.view_vehicles'))  # Update the URL endpoint

# Bookings (Requires User to Be Logged In)
from datetime import datetime

@bp.route('/my_bookings', methods=['GET', 'POST'])
def my_bookings():
    if 'user_id' not in session:
        flash('Please log in to view your bookings.', 'danger')
        return redirect(url_for('main.login'))

    user_id = session['user_id']
    date_filter = request.args.get('date')  # Get the date filter from URL parameters
    
    # Fetch bookings
    if date_filter:
        # Convert date string to datetime object and filter by the date
        date_obj = datetime.strptime(date_filter, '%Y-%m-%d')
        bookings = Booking.query.filter(
            Booking.user_id == user_id,
            Booking.booking_time.date() == date_obj.date(),
            ChargingStation.status == 'enabled'  # Only show enabled stations
        ).join(ChargingStation).all()
    else:
        bookings = Booking.query.filter(
            Booking.user_id == user_id,
            ChargingStation.status == 'enabled'
        ).join(ChargingStation).all()

    return render_template('my_bookings.html', bookings=bookings)



@bp.route('/features')

def features():

        
        return render_template('features.html')
    # Default response if the user is logged in
    # Adjust the template as needed

      # Ensure function name matches the route
# Charging Stations Page
@bp.route('/charging_stations')
def charging_stations():
    return render_template('chargingstations.html')

# Find Stations
def haversine(lat1, lon1, lat2, lon2):
    # Radius of the Earth in km
    R = 6371.0

    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Difference in coordinates
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Distance in km
    distance = R * c
    return distance
@bp.route('/payment-success')
def payment_success():
    # Logic to handle successful payment (e.g., updating booking status in DB)
    return render_template('payment_success.html')

@bp.route('/find_stations', methods=['GET'])
def find_stations():
    
    location = request.args.get('location')

    # Validate user input
    if not location:
        return jsonify({"error": "Location is required."}), 400

    # Get coordinates from the user's location
    latitude, longitude = get_coordinates_from_location(location)

    if latitude is None or longitude is None:
        return jsonify({"error": "Location not found or invalid."}), 400

    # Query the database for stations
    stations = ChargingStation.query.all()
    nearby_stations = []

    for station in stations:
        print(f"Station {station.name} - Latitude: {station.latitude}, Longitude: {station.longitude}")
        
        # Check if coordinates are missing and fetch them using LocationIQ
        if station.latitude is None or station.longitude is None:
            print(f"Station {station.name} is missijhfbehfng coordinates. Trying to fetch...")
            # Fetch coordinates using station's address
            station_lat, station_lon = get_coordinates_from_location(station.location)
            if station_lat is None or station_lon is None:
                print(f"Failed to fetch coordinates for {station.name}. Skipping...")
                continue  # Skip station if coordinates can't be fetched
            station.latitude = station_lat
            station.longitude = station_lon
            print(f"ni yabba {station_lat} nen unna")
        # Calculate the distance between the user's location and the station
        distance = haversine(latitude, longitude, station.latitude, station.longitude)
        print(f"Distance from user to {station.name}: {distance} km")  # Debug log

        # Filter stations within a 10 km radius
        if distance <= 10:
            nearby_stations.append({
            'name': station.name,
            'address': station.location,
            'latitude': station.latitude,   # Add latitude to the response
            'longitude': station.longitude,
             'stationid': station.id,
             # Add longitude to the response
            'distance': round(distance, 2)
        })

    # Handle case when no stations are nearby
    if not nearby_stations:
        return jsonify({"message": "No nearby stations found."}), 200

    return jsonify({'stations': nearby_stations})




@bp.route('/get_user_vehicles', methods=['GET'])
def get_user_vehicles():
    user_id = session['user_id']  # Use your method to get the logged-in user's ID
    vehicles = EVVehicle.query.filter_by(user_id=user_id).all()
    vehicle_list = [{"id": vehicle.id, "vehicle_name": vehicle.vehicle_name, "license_plate": vehicle.license_plate} for vehicle in vehicles]
    return jsonify({"vehicles": vehicle_list})



locationiq_api_key = 'pk.218199c167e2d299d7a2ac441eac33b2'  # Replace with your LocationIQ API key

@bp.route('/route-to-station', methods=['GET'])
def route_to_station():
    user_lat = request.args.get('lat')
    user_lon = request.args.get('lon')
    station_lat = request.args.get('station_lat')
    station_lon = request.args.get('station_lon')
    station_name = request.args.get('station')

    # Pass these details to the HTML template for rendering
    return render_template('route_to_station.html', 
                           user_lat=user_lat, 
                           user_lon=user_lon,
                           station_lat=station_lat, 
                           station_lon=station_lon,
                           station_name=station_name)
@bp.route('/get_slots', methods=['GET'])
def get_available_slots():
    station_id = request.args.get('station_id')
    if not station_id:
        return jsonify({'status': 'error', 'message': 'Station ID required'}), 400

    slots = Slot.query.filter(Slot.station_id == station_id, Slot.availability > 0).all()

    if not slots:
        return jsonify({'status': 'error', 'message': 'No available slots at this station'}), 404

    formatted_slots = [
        {
            'slot_id': slot.id,   # ✅ Keep slot_id
            'slot_number': slot.slot_name,  # ✅ Change slot_name → slot_number
            'start_time': slot.start_time.strftime("%I:%M %p"),
            'end_time': slot.end_time.strftime("%I:%M %p"),
            'price': slot.price,
            'availability': slot.availability
        }
        for slot in slots
    ]
    return jsonify({'status': 'success', 'slots': formatted_slots})


# 🔹 Book Slot
@bp.route('/book_slot', methods=['POST'])
def book_slot():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Please log in to book a slot'}), 401

    data = request.json
    station_id = data.get('station_id')
    slot_name = data.get('slot_name')
    datetime_str = data.get('datetime')
    vehicle_id = data.get('vehicle_id')
    kwh = data.get('kwh')

    # ✅ Validate input data
    if not all([station_id, slot_name, datetime_str, vehicle_id, kwh]):
        return jsonify({'status': 'error', 'message': 'Missing required data'}), 400

    station = ChargingStation.query.get(station_id)
    if not station or station.status.strip().lower() != 'enabled':
        return jsonify({'status': 'error', 'message': 'The selected station is disabled. Please choose another station'}), 400

    try:
        slot = Slot.query.filter_by(station_id=station_id, slot_name=slot_name).first()
        if not slot or slot.availability <= 0:
            return jsonify({'status': 'error', 'message': 'Slot unavailable. Choose another slot'}), 400

        # Decrease slot availability
        slot.availability -= 1
        db.session.commit()

        # Price Calculation (assuming ₹9 per kWh)
        price = float(kwh) * 9.0
        booking_time = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')

        # Create new booking entry
        new_booking = Booking(
            user_id=session['user_id'],
            station_id=station_id,
            slot_id=slot.id,
            status='Pending',
            booking_time=booking_time,
            price=price
        )
        db.session.add(new_booking)
        db.session.commit()

        # ✅ Update Vehicle Charge Cycles
        vehicle = EVVehicle.query.get(vehicle_id)
        if vehicle:
            vehicle.charge_cycles += 1
            vehicle.update_battery_health()
            db.session.commit()

        return jsonify({'status': 'success', 'message': 'Slot booked successfully. Await admin confirmation'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    


@bp.route('/battery_health')
def battery_health():
    user = session.get('user_id')  # Assuming you're getting the current user
    vehicles = EVVehicle.query.filter_by(user_id=user).all()  # Fetch all vehicles for the current user

    # Prepare data for Matplotlib graph
    vehicle_data = {}
    for vehicle in vehicles:
        charge_cycles = vehicle.charge_cycles
        battery_health = vehicle.battery_health
        vehicle_data[vehicle.vehicle_name] = {
            'charge_cycles': charge_cycles,
            'battery_health': battery_health
        }

    # Create a Matplotlib graph
    fig, ax = plt.subplots()

    # Ensure there are at least two points (even for small data)
    for vehicle_name, data in vehicle_data.items():
        charge_cycles = data['charge_cycles']
        battery_health = data['battery_health']

        # Plot the data as a line (or scatter for individual points)
        # Even if there's one point, ensure it's plotted to avoid empty graphs
        if charge_cycles and battery_health is not None:
            ax.plot([charge_cycles], [battery_health], marker='o', label=vehicle_name)
    
    ax.set(xlabel='Charge Cycles', ylabel='Battery Health (%)', title='Battery Health Over Charge Cycles')
    ax.legend()

    # Save the plot to a BytesIO object
    img = io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode('utf-8')

    return render_template('battery_health.html', vehicles=vehicles, graph_url=graph_url)

@bp.route('/energy-tips')
def energy_tips():
    return render_template('energytips.html')



@bp.route('/contact_us', methods=['GET', 'POST'])
def contact_us():
    if request.method == 'POST':
        subject = request.form['subject']
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        # Check if user_id is available in the session
        user_id = session.get('user_id')

        if user_id is None:
            flash("You must be logged in to submit a contact form.", 'danger')
            return redirect(url_for('main.login'))  # Or redirect to your login page

        # Save the contact message to the database
        contact = ContactUs(
            user_id=user_id,  # Automatically assign user_id from session
            subject=subject,
            name=name,
            email=email,
            message=message
        )
        db.session.add(contact)
        db.session.commit()

        flash('Your contact message has been sent successfully!', 'success')
        return redirect(url_for('main.contact_us'))

    return render_template('features.html')


@bp.route('/submit_feedback', methods=['GET', 'POST'])
def submit_feedback():
    if request.method == 'POST':
        name = request.form['name']
        comments = request.form['comments']
        rating = int(request.form['rating'])
        user_id = session.get('user_id')

        if user_id is None:
            flash("You must be logged in to submit a contact form.", 'danger')
            return redirect(url_for('main.login'))  # Or redirect to your login page
        # Save feedback to the database
        feedback = Feedback(user_id=user_id,name=name, comments=comments, rating=rating)
        db.session.add(feedback)
        db.session.commit()
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('main.submit_feedback'))

    return render_template('features.html')
