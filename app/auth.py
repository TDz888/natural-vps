"""
Natural VPS - Authentication Routes
"""

import uuid
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g
from app.database import db
from app.utils import (
    get_client_ip, hash_ip, generate_id, hash_password, verify_password,
    generate_tokens, verify_token, validate_username, validate_password,
    validate_email, require_auth
)
from app.config import Config

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip() or None
        
        # Validate
        valid, error = validate_username(username)
        if not valid:
            return jsonify({'success': False, 'error': error}), 400
        
        valid, error = validate_password(password)
        if not valid:
            return jsonify({'success': False, 'error': error}), 400
        
        if email:
            valid, error = validate_email(email)
            if not valid:
                return jsonify({'success': False, 'error': error}), 400
        
        # Check existing user
        existing = db.fetchone("SELECT id FROM users WHERE username = ?", (username,))
        if existing:
            return jsonify({'success': False, 'error': 'Username already taken'}), 400
        
        if email:
            existing = db.fetchone("SELECT id FROM users WHERE email = ?", (email,))
            if existing:
                return jsonify({'success': False, 'error': 'Email already registered'}), 400
        
        # Create user
        user_id = str(uuid.uuid4())
        password_hash = hash_password(password)
        api_key = f"nv_{generate_id(16)}"
        
        db.execute('''
            INSERT INTO users (id, username, email, password_hash, created_at, api_key)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, email, password_hash, datetime.now().isoformat(), api_key))
        
        # Generate tokens
        access_token, refresh_token = generate_tokens(user_id)
        
        # Save session
        session_id = str(uuid.uuid4())
        db.execute('''
            INSERT INTO sessions (id, user_id, token, refresh_token, created_at, expires_at, ip, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, user_id, access_token, refresh_token,
            datetime.now().isoformat(),
            (datetime.now() + timedelta(hours=Config.JWT_EXPIRE_HOURS)).isoformat(),
            get_client_ip(),
            request.headers.get('User-Agent', '')
        ))
        
        response = jsonify({
            'success': True,
            'message': 'Registration successful',
            'user': {'id': user_id, 'username': username, 'api_key': api_key}
        })
        
        # Set cookie
        response.set_cookie(
            'access_token',
            access_token,
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=Config.JWT_EXPIRE_HOURS * 3600
        )
        
        return response, 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        remember = data.get('remember', False)
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'}), 400
        
        # Rate limit check
        ip = get_client_ip()
        ip_hash = hash_ip(ip)
        window_start = datetime.now() - timedelta(seconds=Config.LOGIN_RATE_WINDOW)
        
        row = db.fetchone(
            "SELECT COUNT(*) as count FROM login_attempts WHERE ip_hash = ? AND success = 0 AND timestamp > ?",
            (ip_hash, window_start.isoformat())
        )
        
        if row and row['count'] >= Config.LOGIN_RATE_LIMIT:
            return jsonify({'success': False, 'error': 'Too many failed attempts. Try again later.'}), 429
        
        # Find user
        user = db.fetchone("SELECT * FROM users WHERE username = ?", (username,))
        if not user:
            db.execute(
                "INSERT INTO login_attempts (ip_hash, username, success, timestamp) VALUES (?, ?, 0, ?)",
                (ip_hash, username, datetime.now().isoformat())
            )
            return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            db.execute(
                "INSERT INTO login_attempts (ip_hash, username, success, timestamp) VALUES (?, ?, 0, ?)",
                (ip_hash, username, datetime.now().isoformat())
            )
            return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
        
        # Login successful
        db.execute(
            "INSERT INTO login_attempts (ip_hash, username, success, timestamp) VALUES (?, ?, 1, ?)",
            (ip_hash, username, datetime.now().isoformat())
        )
        
        # Update last login
        db.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.now().isoformat(), user['id'])
        )
        
        # Generate tokens
        if remember:
            Config.JWT_EXPIRE_HOURS = 168  # 7 days
        
        access_token, refresh_token = generate_tokens(user['id'])
        
        # Save session
        session_id = str(uuid.uuid4())
        db.execute('''
            INSERT INTO sessions (id, user_id, token, refresh_token, created_at, expires_at, ip, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, user['id'], access_token, refresh_token,
            datetime.now().isoformat(),
            (datetime.now() + timedelta(hours=Config.JWT_EXPIRE_HOURS)).isoformat(),
            ip,
            request.headers.get('User-Agent', '')
        ))
        
        response = jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'api_key': user['api_key']
            }
        })
        
        response.set_cookie(
            'access_token',
            access_token,
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=Config.JWT_EXPIRE_HOURS * 3600
        )
        
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """Logout user"""
    token = request.cookies.get('access_token')
    if token:
        db.execute("DELETE FROM sessions WHERE token = ?", (token,))
    
    response = jsonify({'success': True, 'message': 'Logged out'})
    response.delete_cookie('access_token')
    return response

@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current user info"""
    user = db.fetchone(
        "SELECT id, username, email, created_at, last_login, api_key FROM users WHERE id = ?",
        (g.user_id,)
    )
    
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    return jsonify({
        'success': True,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'created_at': user['created_at'],
            'last_login': user['last_login'],
            'api_key': user['api_key']
        }
    })

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """Refresh access token"""
    refresh_token = request.json.get('refresh_token')
    if not refresh_token:
        return jsonify({'success': False, 'error': 'Refresh token required'}), 400
    
    valid, payload = verify_token(refresh_token, 'refresh')
    if not valid:
        return jsonify({'success': False, 'error': payload}), 401
    
    # Generate new access token
    access_payload = {
        'user_id': payload['user_id'],
        'type': 'access',
        'exp': datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRE_HOURS),
        'iat': datetime.utcnow()
    }
    new_access_token = jwt.encode(access_payload, Config.JWT_SECRET, algorithm='HS256')
    
    return jsonify({'success': True, 'access_token': new_access_token})
