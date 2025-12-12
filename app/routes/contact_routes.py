from flask import Blueprint, request, jsonify
from flask_mail import Message
from app import mail
import os

contact_bp = Blueprint('contact_bp', __name__)

@contact_bp.route('/contact', methods=['POST'])
def send_contact_email():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    message = data.get('message')

    if not name or not email or not message:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        msg = Message(
            subject=f"New Portfolio Inquiry from {name}",
            recipients=[os.environ.get('MAIL_FROM')],
            body=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
        )
        mail.send(msg)
        return jsonify({'message': 'Message sent successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500