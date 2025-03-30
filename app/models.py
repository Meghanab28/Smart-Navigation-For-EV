from datetime import datetime
from . import db

class User(db.Model):
    __tablename__ = 'Users'
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(15))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class EVVehicle(db.Model):
    __tablename__ = 'ev_vehicles'

    id = db.Column(db.Integer, primary_key=True)  # Primary key for the vehicle
    user_id = db.Column(db.Integer, nullable=False)  # The user (admin or other) who added the vehicle
    vehicle_name = db.Column(db.String(100), nullable=False)  # Name of the vehicle
    vehicle_type = db.Column(db.String(100), nullable=False)  # Type of vehicle (e.g., Electric, Hybrid)
    license_plate = db.Column(db.String(20), nullable=False, unique=True)  # License plate (must be unique)
    battery_capacity = db.Column(db.Float, nullable=False)  # Battery capacity in kWh
    range_per_charge = db.Column(db.Float, nullable=False)  # Range per charge in km
    charge_cycles = db.Column(db.Integer, default=0)  # Number of charge cycles (defaults to 0)
    battery_health = db.Column(db.Float, default=100.0)  # Battery health in percentage, defaults to 100%

    def __repr__(self):
        return f'<EVVehicle {self.vehicle_name} ({self.license_plate})>'

    def __init__(self, user_id, vehicle_name, vehicle_type, license_plate, battery_capacity, range_per_charge):
        self.user_id = user_id
        self.vehicle_name = vehicle_name
        self.vehicle_type = vehicle_type
        self.license_plate = license_plate
        self.battery_capacity = battery_capacity
        self.range_per_charge = range_per_charge

    def update_battery_health(self):
        """
        Update the battery health based on the number of charge cycles.
        Assumes 20% degradation after 1200 charge cycles (example).
        """
        nominal_cycle_life =self.charge_cycles  # Nominal cycle life for the battery (example)
        total_degradation = 20  # Total degradation after the nominal cycle life (example: 20%)
        degradation_per_cycle = total_degradation / nominal_cycle_life
        
        # Calculate degradation
        self.battery_health = 100 - (self.charge_cycles * degradation_per_cycle)
        if self.battery_health < 0:
            self.battery_health = 0  # Battery health cannot go below 0%

        db.session.commit()

    def add_charge_cycle(self):
        """
        Increment the charge cycle and update battery health.
        """
        self.charge_cycles += 1
        self.update_battery_health()

class ContactUs(db.Model):
    __tablename__ = 'contact_us'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id', ondelete='CASCADE'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum('Resolved', 'Ongoing', 'Closed'), default='Ongoing')
    contact_date = db.Column(db.DateTime, server_default=db.func.now())
    name = db.Column(db.String(200), nullable=False)  # Add name column
    email = db.Column(db.String(200), nullable=False)  # Add email column

    user = db.relationship('User', backref='contacts')
# Assuming you're using SQLAlchemy
class Slot(db.Model):
    __tablename__ = 'slots'

    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('charging_stations.id'), nullable=False)
    slot_name = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.Time, nullable=False)  # Start of slot
    end_time = db.Column(db.Time, nullable=False)    # End of slot (3-hour range)
    price = db.Column(db.Float, nullable=False)
    availability = db.Column(db.Integer, nullable=False, default=1)

    # Relationships
    station = db.relationship('ChargingStation', backref='slots')
    bookings = db.relationship('Booking', backref='slot', cascade="all, delete-orphan")


    @property
    def station_name(self):
        return self.station.name

    def decrease_availability(self):
        """Decrease availability when a booking is made."""
        if self.availability > 0:
            self.availability -= 1
            db.session.commit()

    def increase_availability(self):
        """Increase availability when a booking is canceled."""
        self.availability += 1
        db.session.commit()





class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'), nullable=False)
    station_id = db.Column(db.Integer, db.ForeignKey('charging_stations.id'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('slots.id'), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)  # New Column (Date of Booking)
    start_time = db.Column(db.Time, nullable=False)    # New Column (Start Time)
    end_time = db.Column(db.Time, nullable=False)      # New Column (End Time)
    status = db.Column(db.String(20), default='Pending')
    price = db.Column(db.Float)

    # Relationships
    user = db.relationship('User', backref='bookings')
    station = db.relationship('ChargingStation', back_populates='bookings')

    station = db.relationship('ChargingStation', back_populates='bookings')

    def cancel_booking(self):
        """Cancel booking and restore slot availability."""
        slot = Slot.query.get(self.slot_id)
        if slot:
            slot.increase_availability()
        db.session.delete(self)
        db.session.commit()




class Payment(db.Model):
    __tablename__ = 'Payments'
    payment_id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)  # Fix: Referencing 'bookings.id'
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, server_default=db.func.now())
    payment_status = db.Column(db.Enum('Pending', 'Completed', 'Failed'), default='Pending')

class Admin(db.Model):
    __tablename__ = 'Admin'
    admin_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())






class ChargingStation(db.Model):
    __tablename__ = 'charging_stations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum('Enabled', 'Disabled'), nullable=False, default='Enabled')

    bookings = db.relationship('Booking', back_populates='station', cascade='all, delete-orphan')
class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    comments = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    feedback_date = db.Column(db.DateTime, server_default=db.func.now())

    # Add a check constraint for the rating to ensure it's between 1 and 5
    __table_args__ = (
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='rating_check'),
    )


