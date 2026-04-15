"""
Natural VPS - Updated Authentication Routes
Implements automatic @naturalvps email generation
"""

import uuid
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g
from app.database import db
from app.utils import (
    get_client_ip, generate_id, hash_password, verify_password,
    generate_tokens, validate_username_format, validate_password_strength
)
from app.decorators import require_auth
from app.config import Config
from app.spam_detector import SpamDetector
from app.email_service import EmailService, NotificationService, CREDENTIALS_EMAIL_TEMPLATE
from app.email_verification import EmailVerificationSystem
import json

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register_auto_credentials():
    """
    Register new user with auto-generated credentials
    
    Request JSON:
    {
        "real_email": "user@gmail.com"  # For notifications
    }
    
    Response includes @naturalvps email, auto-generated username and password
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        real_email = data.get('real_email', '').strip()
        client_ip = get_client_ip()
        
        # Validate real email
        if not real_email:
            return jsonify({'success': False, 'error': 'Real email address is required'}), 400
        
        is_valid, error = EmailService.validate_real_email(real_email)
        if not is_valid:
            return jsonify({'success': False, 'error': f'Invalid email: {error}'}), 400
        
        # Check if email already registered
        existing_by_real_email = db.fetchone(
            "SELECT id FROM users WHERE real_email = ?",
            (real_email,)
        )
        if existing_by_real_email:
            return jsonify({
                'success': False,
                'error': 'This email is already registered',
                'help': 'Try logging in or use a different email address'
            }), 400
        
        # Check for spam
        is_spam, spam_reason = SpamDetector.check_registration_spam(client_ip, real_email)
        if is_spam:
            return jsonify({'success': False, 'error': f'Registration blocked: {spam_reason}'}), 429
        
        # Generate credentials
        vps_email = EmailService.generate_vpn_email()
        web_username = EmailService.generate_web_username()
        web_password = EmailService.generate_secure_password()
        
        # Ensure uniqueness
        while db.fetchone("SELECT id FROM users WHERE vps_email = ?", (vps_email,)):
            vps_email = EmailService.generate_vpn_email()
        
        while db.fetchone("SELECT id FROM users WHERE web_username = ?", (web_username,)):
            web_username = EmailService.generate_web_username()
        
        # Create user
        user_id = str(uuid.uuid4())
        password_hash = hash_password(web_password)
        api_key = f"nv_{generate_id(16)}"
        
        # Create default notification preferences
        default_prefs = NotificationService.get_default_preferences()
        
        db.execute('''
            INSERT INTO users (
                id, username, vps_email, real_email, web_username,
                email, password_hash, created_at, api_key,
                notification_preferences, email_verified
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            web_username,  # For compatibility
            vps_email,
            real_email,
            web_username,
            vps_email,  # Store as email for compatibility
            password_hash,
            datetime.now().isoformat(),
            api_key,
            json.dumps(default_prefs),
            0
        ))
        
        # Create notification preferences record
        db.execute('''
            INSERT INTO notification_preferences (user_id, updated_at)
            VALUES (?, ?)
        ''', (user_id, datetime.now().isoformat()))
        
        # Generate tokens
        access_token, refresh_token = generate_tokens(user_id)
        
        # Create session
        session_id = str(uuid.uuid4())
        db.execute('''
            INSERT INTO sessions (
                id, user_id, token, refresh_token, created_at,
                expires_at, ip, user_agent
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, user_id, access_token, refresh_token,
            datetime.now().isoformat(),
            (datetime.now() + timedelta(hours=Config.JWT_EXPIRE_HOURS)).isoformat(),
            client_ip,
            request.headers.get('User-Agent', '')
        ))
        
        # Log activity
        db.execute('''
            INSERT INTO user_activity_logs (
                user_id, action, resource_type, details, ip_address, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            'account_created',
            'user',
            'New account registration',
            client_ip,
            datetime.now().isoformat()
        ))
        
        # TODO: Send credentials email to real_email
        # EmailService.send_credentials_email(real_email, vps_email, web_username, web_password)
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully!',
            'user': {
                'id': user_id,
                'vps_email': vps_email,
                'web_username': web_username,
                'real_email': real_email,
                'api_key': api_key
            },
            'token': access_token,
            'refresh_token': refresh_token,
            'credentials_sent': False  # Change to True when email is implemented
        }), 201
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login with username or vps_email and password
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        username_or_email = data.get('username', '').strip()
        password = data.get('password', '')
        client_ip = get_client_ip()
        
        if not username_or_email or not password:
            return jsonify({'success': False, 'error': 'Username/email and password required'}), 400
        
        # Find user by username or vps_email
        user = db.fetchone(
            "SELECT * FROM users WHERE web_username = ? OR vps_email = ? OR username = ?",
            (username_or_email, username_or_email, username_or_email)
        )
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        if not verify_password(password, user['password_hash']):
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        # Update last login
        db.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.now().isoformat(), user['id'])
        )
        
        # Generate tokens
        access_token, refresh_token = generate_tokens(user['id'])
        
        # Create session
        session_id = str(uuid.uuid4())
        db.execute('''
            INSERT INTO sessions (
                id, user_id, token, refresh_token, created_at,
                expires_at, ip, user_agent
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, user['id'], access_token, refresh_token,
            datetime.now().isoformat(),
            (datetime.now() + timedelta(hours=Config.JWT_EXPIRE_HOURS)).isoformat(),
            client_ip,
            request.headers.get('User-Agent', '')
        ))
        
        # Log activity
        db.execute('''
            INSERT INTO user_activity_logs (
                user_id, action, resource_type, details,
                ip_address, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user['id'],
            'login',
            'auth',
            'User login',
            client_ip,
            datetime.now().isoformat()
        ))
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'web_username': user['web_username'],
                'vps_email': user['vps_email'],
                'real_email': user['real_email'],
                'display_name': user.get('display_name') or user['web_username']
            },
            'token': access_token,
            'refresh_token': refresh_token
        }), 200
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """Logout user"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        db.execute("DELETE FROM sessions WHERE token = ?", (token,))
        
        db.execute('''
            INSERT INTO user_activity_logs (
                user_id, action, resource_type, details, ip_address, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            g.user_id,
            'logout',
            'auth',
            'User logout',
            get_client_ip(),
            datetime.now().isoformat()
        ))
        
        return jsonify({'success': True, 'message': 'Logged out successfully'}), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get user profile"""
    try:
        user = db.fetchone("SELECT * FROM users WHERE id = ?", (g.user_id,))
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'profile': {
                'id': user['id'],
                'web_username': user['web_username'],
                'vps_email': user['vps_email'],
                'real_email': user['real_email'],
                'display_name': user.get('display_name') or user['web_username'],
                'bio': user.get('bio'),
                'timezone': user.get('timezone', 'UTC'),
                'created_at': user['created_at'],
                'last_login': user.get('last_login')
            }
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/profile', methods=['PUT'])
@require_auth
def update_profile():
    """Update user profile"""
    try:
        data = request.get_json()
        user_id = g.user_id
        
        # Allowed fields to update
        allowed_fields = ['display_name', 'bio', 'timezone', 'real_email']
        updates = {}
        
        for field in allowed_fields:
            if field in data:
                updates[field] = data[field]
        
        if not updates:
            return jsonify({'success': False, 'error': 'No valid fields to update'}), 400
        
        # Build update query
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [user_id]
        
        db.execute(
            f"UPDATE users SET {set_clause} WHERE id = ?",
            values
        )
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully'
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
