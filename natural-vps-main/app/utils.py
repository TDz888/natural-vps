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
import socket
import requests
import time
from datetime import datetime, timedelta
from flask import request, g
from functools import wraps
from app.config import Config

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or '0.0.0.0'

def hash_ip(ip):
    return hashlib.sha256(f"{ip}_{Config.SECRET_KEY}".encode()).hexdigest()[:32]

def generate_id(length=8):
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_username():
    prefixes = ['forest', 'leaf', 'river', 'stone', 'wind', 'sun', 'moss', 'pine']
    return f"{secrets.choice(prefixes)}_{generate_id(6)}"

def generate_password(length=16):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(chars) for _ in range(length))

def hash_password(password):
    salt = bcrypt.gensalt(rounds=Config.BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password, hashed):
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except:
        return False

def generate_tokens(user_id):
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
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
        if payload.get('type') != token_type:
            return False, "Invalid token type"
        return True, payload
    except jwt.ExpiredSignatureError:
        return False, "Token expired"
    except jwt.InvalidTokenError:
        return False, "Invalid token"

def validate_github_token(token):
    try:
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'NaturalVPS/3.0'
        }
        resp = requests.get('https://api.github.com/user', headers=headers, timeout=10)
        
        if resp.status_code != 200:
            if resp.status_code == 401:
                return False, "Invalid GitHub token - Unauthorized"
            return False, f"GitHub API error: {resp.status_code}"
        
        user_data = resp.json()
        scopes = resp.headers.get('X-OAuth-Scopes', '')
        
        if 'repo' not in scopes:
            return False, "Token missing 'repo' scope"
        if 'workflow' not in scopes:
            return False, "Token missing 'workflow' scope"
        
        return True, {'username': user_data.get('login'), 'scopes': scopes}
    except requests.exceptions.Timeout:
        return False, "GitHub API timeout"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def check_port_open(host, port, timeout=3):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def retry_with_backoff(func, max_retries=3, base_delay=1):
    for attempt in range(max_retries):
        try:
            result, error = func()
            if error is None:
                return result, None
            if attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt))
        except Exception as e:
            if attempt == max_retries - 1:
                return None, str(e)
            time.sleep(base_delay * (2 ** attempt))
    return None, "Max retries exceeded"

def validate_username_format(username):
    if not username or len(username) < 3 or len(username) > 30:
        return False, "Username must be 3-30 characters"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    return True, None

def validate_password_strength(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain number"
    return True, None
