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
        
        valid, error = validate_username_format(username)
        if not valid:
            return jsonify({'success': False, 'error': error}), 400
        
        valid, error = validate_password_strength(password)
        if not valid:
            return jsonify({'success': False, 'error': error}), 400
        
        existing = db.fetchone("SELECT id FROM users WHERE username = ?", (username,))
        if existing:
            return jsonify({'success': False, 'error': 'Username already taken'}), 400
        
        user_id = str(uuid.uuid4())
        password_hash = hash_password(password)
        api_key = f"nv_{generate_id(16)}"
        
        db.execute('''
            INSERT INTO users (id, username, email, password_hash, created_at, api_key)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, email, password_hash, datetime.now().isoformat(), api_key))
        
        access_token, refresh_token = generate_tokens(user_id)
        
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
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'}), 400
        
        user = db.fetchone("SELECT * FROM users WHERE username = ?", (username,))
        if not user:
            return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
        
        if not verify_password(password, user['password_hash']):
            return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
        
        db.execute("UPDATE users SET last_login = ? WHERE id = ?", (datetime.now().isoformat(), user['id']))
        
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
