from flask import Blueprint, request, jsonify
from app import db, mail
from app.models.booking import Availability, Booking
from flask_mail import Message
from flask_jwt_extended import jwt_required
from datetime import datetime
import os

booking_bp = Blueprint('booking_bp', __name__)

# --- Public Routes ---
@booking_bp.route('/availability', methods=['GET'])
def get_availability():
    availabilities = Availability.query.all()
    return jsonify([a.to_dict() for a in availabilities])

@booking_bp.route('/bookings', methods=['POST'])
def create_booking():
    data = request.get_json()
    
    # THE FIX: Replace 'Z' with '+00:00' to make it compatible with fromisoformat
    iso_time_str = data['time'].replace('Z', '+00:00')
    
    new_booking = Booking(
        client_name=data['name'], client_email=data['email'],
        meeting_time=datetime.fromisoformat(iso_time_str),
        meeting_duration=data['duration'], notes=data.get('notes')
    )
    db.session.add(new_booking)
    db.session.commit()

    try:
        msg_admin = Message(
            subject="New Booking Request",
            recipients=[os.environ.get('MAIL_FROM')],
            body=f"New booking request from {data['name']} ({data['email']}).\n"
                 f"Time: {new_booking.meeting_time.strftime('%A, %B %d, %Y at %I:%M %p UTC')}\n"
                 f"Duration: {data['duration']} minutes."
        )
        mail.send(msg_admin)
        msg_client = Message(
            subject="Your Booking Request is Received",
            recipients=[data['email']],
            body=f"Hi {data['name']},\n\nYour request for a {data['duration']}-minute session is received.\n"
                 f"I will confirm the appointment and send a meeting link shortly.\n\n"
                 f"Requested Time: {new_booking.meeting_time.strftime('%A, %B %d, %Y at %I:%M %p UTC')}\n\n"
                 f"Best,\nBolaji"
        )
        mail.send(msg_client)
    except Exception as e:
        print(f"Mail sending failed for booking: {e}")

    return jsonify(new_booking.to_dict()), 201

# --- Admin Routes ---
@booking_bp.route('/admin/availability', methods=['GET'])
@jwt_required()
def admin_get_availability():
    availabilities = Availability.query.all()
    return jsonify([a.to_dict() for a in availabilities])

@booking_bp.route('/admin/availability', methods=['POST'])
@jwt_required()
def admin_add_availability():
    data = request.get_json()
    new_avail = Availability(
        day_of_week=data['day_of_week'],
        start_time=datetime.strptime(data['start_time'], '%H:%M').time(),
        end_time=datetime.strptime(data['end_time'], '%H:%M').time()
    )
    db.session.add(new_avail)
    db.session.commit()
    return jsonify(new_avail.to_dict()), 201

@booking_bp.route('/admin/availability/<int:avail_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_availability(avail_id):
    avail = Availability.query.get_or_404(avail_id)
    db.session.delete(avail)
    db.session.commit()
    return jsonify({'message': 'Availability deleted'})

@booking_bp.route('/admin/bookings', methods=['GET'])
@jwt_required()
def admin_get_bookings():
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return jsonify([b.to_dict() for b in bookings])