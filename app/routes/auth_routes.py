from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app.models.admin import Admin
from app import db, mail, bcrypt
from flask_mail import Message
import os
from datetime import datetime

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/check-setup', methods=['GET'])
def check_setup():
    admin_exists = Admin.query.first()
    return jsonify({'setup_needed': not admin_exists})

@auth_bp.route('/register', methods=['POST'])
def register():
    if Admin.query.first():
        return jsonify({'error': 'An admin account already exists.'}), 403

    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400
    
    if Admin.query.filter_by(username=username).first() or Admin.query.filter_by(email=email).first():
        return jsonify({'error': 'Username or email already exists'}), 409

    admin = Admin(username=username, email=email)
    admin.set_password(password)
    admin.generate_otp()

    try:
        msg = Message('Your Verification Code',
                      sender=os.environ.get('MAIL_FROM'),
                      recipients=[email])
        msg.body = f'Your verification code is: {admin.otp}'
        mail.send(msg)
        
        db.session.add(admin)
        db.session.commit()
        
        return jsonify({'message': 'Registration successful. Please check your email for the verification code.'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')

    admin = Admin.query.filter_by(email=email).first()

    if not admin:
        return jsonify({'error': 'Admin with that email not found.'}), 404
    
    if admin.is_verified:
        return jsonify({'message': 'Account already verified.'}), 200

    if admin.otp == otp and admin.otp_expiry > datetime.utcnow():
        admin.is_verified = True
        admin.otp = None
        admin.otp_expiry = None
        db.session.commit()
        return jsonify({'message': 'Account verified successfully!'}), 200
    else:
        return jsonify({'error': 'Invalid or expired OTP.'}), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    admin = Admin.query.filter_by(username=username).first()

    if not admin:
        return jsonify({'error': 'Invalid username or password.'}), 401
    
    if not admin.is_verified:
        return jsonify({'error': 'Account not verified. Please complete the setup process.'}), 403

    if admin.check_password(password):
        # THE FIX: Convert the integer ID to a string
        access_token = create_access_token(identity=str(admin.id))
        return jsonify(access_token=access_token)
    else:
        return jsonify({'error': 'Invalid username or password.'}), 401