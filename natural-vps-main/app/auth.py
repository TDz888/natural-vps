"""
Natural VPS - Authentication Routes
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
from app.email_verification import EmailVerificationSystem

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip() or None
        client_ip = get_client_ip()
        
        valid, error = validate_username_format(username)
        if not valid:
            return jsonify({'success': False, 'error': error}), 400
        
        valid, error = validate_password_strength(password)
        if not valid:
            return jsonify({'success': False, 'error': error}), 400
        
        # Validate email if provided
        if email:
            is_valid, error = EmailVerificationSystem.validate_email(email)
            if not is_valid:
                return jsonify({'success': False, 'error': f'Email validation failed: {error}'}), 400
            
            # Check if email registration should be blocked
            should_block, reason = EmailVerificationSystem.should_block_registration(email)
            if should_block:
                return jsonify({'success': False, 'error': reason}), 400
        
        existing = db.fetchone("SELECT id FROM users WHERE username = ?", (username,))
        if existing:
            return jsonify({'success': False, 'error': 'Username already taken'}), 400
        
        # Check for spam patterns
        is_spam, spam_reason = SpamDetector.check_registration_spam(client_ip, email or username)
        if is_spam:
            return jsonify({'success': False, 'error': f'Registration blocked: {spam_reason}'}), 429
        
        user_id = str(uuid.uuid4())
        password_hash = hash_password(password)
        api_key = f"nv_{generate_id(16)}"
        
        # Store creator IP
        from app.utils import hash_ip
        creator_ip_hash = hash_ip(client_ip)
        
        db.execute('''
            INSERT INTO users (id, username, email, password_hash, created_at, api_key)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, email, password_hash, datetime.now().isoformat(), api_key))
        
        # If email verification is required, generate code
        require_verification = email and EmailVerificationSystem.should_require_email_verification(email)
        if require_verification:
            code = EmailVerificationSystem.generate_verification_code(email)
            success, error_msg = EmailVerificationSystem.send_verification_code(email, code)
            if not success:
                return jsonify({'success': False, 'error': f'Failed to send verification code: {error_msg}'}), 500
            return jsonify({
                'success': True,
                'message': 'Registration successful. Verification code sent to email.',
                'requires_verification': True
            }), 201
        
        access_token, refresh_token = generate_tokens(user_id)
        
        # Clean up any old sessions first
        db.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        
        session_id = str(uuid.uuid4())
        db.execute('''
            INSERT INTO sessions (id, user_id, token, refresh_token, created_at, expires_at, ip, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, user_id, access_token, refresh_token,
            datetime.now().isoformat(),
            (datetime.now() + timedelta(hours=Config.JWT_EXPIRE_HOURS)).isoformat(),
            client_ip,
            request.headers.get('User-Agent', '')
        ))
        
        response = jsonify({
            'success': True,
            'message': 'Registration successful',
            'user': {'id': user_id, 'username': username, 'api_key': api_key}
        })
        response.set_cookie('access_token', access_token, httponly=True, samesite='Lax', max_age=Config.JWT_EXPIRE_HOURS * 3600)
        return response, 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        client_ip = get_client_ip()
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'}), 400
        
        # Check for login spam
        is_spam, spam_reason = SpamDetector.check_login_spam(username, client_ip)
        if is_spam:
            return jsonify({'success': False, 'error': f'Too many login attempts: {spam_reason}'}), 429
        
        user = db.fetchone("SELECT * FROM users WHERE username = ?", (username,))
        if not user:
            # Log failed attempt
            from app.utils import hash_ip
            db.execute(
                "INSERT INTO login_attempts (ip_hash, username, user_id, success, timestamp) VALUES (?, ?, ?, ?, ?)",
                (hash_ip(client_ip), username, None, 0, datetime.now().isoformat())
            )
            return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
        
        if not user['is_active']:
            return jsonify({'success': False, 'error': 'Account suspended'}), 403
        
        if not verify_password(password, user['password_hash']):
            # Log failed attempt
            from app.utils import hash_ip
            db.execute(
                "INSERT INTO login_attempts (ip_hash, username, user_id, success, timestamp) VALUES (?, ?, ?, ?, ?)",
                (hash_ip(client_ip), username, user['id'], 0, datetime.now().isoformat())
            )
            return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
        
        db.execute("UPDATE users SET last_login = ? WHERE id = ?", (datetime.now().isoformat(), user['id']))
        
        # Log successful login attempt
        from app.utils import hash_ip
        db.execute(
            "INSERT INTO login_attempts (ip_hash, username, user_id, success, timestamp) VALUES (?, ?, ?, ?, ?)",
            (hash_ip(client_ip), username, user['id'], 1, datetime.now().isoformat())
        )
        
        # Clean up old sessions for this user
        db.execute("DELETE FROM sessions WHERE user_id = ?", (user['id'],))
        
        access_token, refresh_token = generate_tokens(user['id'])
        
        session_id = str(uuid.uuid4())
        db.execute('''
            INSERT INTO sessions (id, user_id, token, refresh_token, created_at, expires_at, ip, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, user['id'], access_token, refresh_token,
            datetime.now().isoformat(),
            (datetime.now() + timedelta(hours=Config.JWT_EXPIRE_HOURS)).isoformat(),
            get_client_ip(),
            request.headers.get('User-Agent', '')
        ))
        
        response = jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {'id': user['id'], 'username': user['username'], 'email': user['email'], 'api_key': user['api_key']}
        })
        response.set_cookie('access_token', access_token, httponly=True, samesite='Lax', max_age=Config.JWT_EXPIRE_HOURS * 3600)
        return response
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    token = request.cookies.get('access_token')
    if token:
        db.execute("DELETE FROM sessions WHERE token = ?", (token,))
    response = jsonify({'success': True, 'message': 'Logged out'})
    response.delete_cookie('access_token')
    return response

@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user():
    user = db.fetchone("SELECT id, username, email, created_at, last_login, api_key FROM users WHERE id = ?", (g.user_id,))
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    return jsonify({'success': True, 'user': dict(user)})

@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """Verify email with code"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip()
        code = data.get('code', '').strip()
        
        if not email or not code:
            return jsonify({'success': False, 'error': 'Email and code required'}), 400
        
        success, error = EmailVerificationSystem.verify_email_code(email, code)
        if not success:
            return jsonify({'success': False, 'error': error}), 400
        
        # Update user's verified status if they exist
        user = db.fetchone("SELECT id FROM users WHERE email = ?", (email,))
        if user:
            db.execute("UPDATE users SET email_verified = 1 WHERE id = ?", (user['id'],))
        
        return jsonify({
            'success': True,
            'message': 'Email verified successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/request-verification-code', methods=['POST'])
def request_verification_code():
    """Request verification code for email"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip()
        
        # Validate email
        is_valid, error = EmailVerificationSystem.validate_email(email)
        if not is_valid:
            return jsonify({'success': False, 'error': f'Email validation failed: {error}'}), 400
        
        # Check if email registration should be blocked
        should_block, reason = EmailVerificationSystem.should_block_registration(email)
        if should_block:
            return jsonify({'success': False, 'error': reason}), 400
        
        # Generate and send code
        code = EmailVerificationSystem.generate_verification_code(email)
        success, error_msg = EmailVerificationSystem.send_verification_code(email, code)
        
        if not success:
            return jsonify({'success': False, 'error': f'Failed to send code: {error_msg}'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Verification code sent to email'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/check-email-status', methods=['GET'])
def check_email_status():
    """Check verification status of email"""
    try:
        email = request.args.get('email', '').strip()
        if not email:
            return jsonify({'success': False, 'error': 'Email required'}), 400
        
        status = EmailVerificationSystem.get_verification_status(email)
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

