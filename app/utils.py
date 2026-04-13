"""
Natural VPS - Utility Functions
"""

import re
import uuid
import secrets
import string
import hashlib
import bcrypt
import jwt
from datetime import datetime, timedelta
from flask import request, g
from functools import wraps
from app.config import Config
from app.database import db

def get_client_ip():
    """Get client IP address"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or '0.0.0.0'

def hash_ip(ip):
    """Hash IP address for privacy"""
    return hashlib.sha256(f"{ip}_{Config.SECRET_KEY}".encode()).hexdigest()[:32]

def generate_id(length=8):
    """Generate random ID"""
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_username():
    """Generate random username"""
    prefixes = ['forest', 'leaf', 'river', 'stone', 'wind', 'sun', 'moss', 'pine']
    return f"{secrets.choice(prefixes)}_{generate_id(6)}"

def generate_password(length=16):
    """Generate random password"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(chars) for _ in range(length))

def hash_password(password):
    """Hash password with bcrypt"""
    salt = bcrypt.gensalt(rounds=Config.BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password, hashed):
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except:
        return False

def generate_tokens(user_id):
    """Generate JWT access and refresh tokens"""
    access_payload = {
        'user_id': user_id,
        'type': 'access',
        'exp': datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRE_HOURS),
        'iat': datetime.utcnow()
    }
    refresh_payload = {
        'user_id': user_id,
        'type': 'refresh',
        'exp': datetime.utcnow() + timedelta(days=Config.JWT_REFRESH_EXPIRE_DAYS),
        'iat': datetime.utcnow()
    }
    access_token = jwt.encode(access_payload, Config.JWT_SECRET, algorithm='HS256')
    refresh_token = jwt.encode(refresh_payload, Config.JWT_SECRET, algorithm='HS256')
    return access_token, refresh_token

def verify_token(token, token_type='access'):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
        if payload.get('type') != token_type:
            return False, "Invalid token type"
        return True, payload
    except jwt.ExpiredSignatureError:
        return False, "Token expired"
    except jwt.InvalidTokenError:
        return False, "Invalid token"

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
        
        # Check cookie
        if not token:
            token = request.cookies.get('access_token')
        
        if not token:
            return {'success': False, 'error': 'Authentication required'}, 401
        
        valid, payload = verify_token(token, 'access')
        if not valid:
            return {'success': False, 'error': payload}, 401
        
        g.user_id = payload['user_id']
        return f(*args, **kwargs)
    return decorated

def validate_username(username):
    """Validate username format"""
    if not username or len(username) < 3 or len(username) > 30:
        return False, "Username must be 3-30 characters"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    return True, None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain number"
    return True, None

def validate_email(email):
    """Validate email format"""
    if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return False, "Invalid email format"
    return True, None
