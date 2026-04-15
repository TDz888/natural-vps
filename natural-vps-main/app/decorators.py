"""
Natural VPS - Decorators
"""

from functools import wraps
from flask import request, jsonify, g
from datetime import datetime, timedelta
from app.utils import verify_token, get_client_ip, hash_ip
from app.database import db
from app.config import Config

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
        if not token:
            token = request.cookies.get('access_token')
        if not token:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        valid, payload = verify_token(token, 'access')
        if not valid:
            return jsonify({'success': False, 'error': payload}), 401
        
        g.user_id = payload['user_id']
        return f(*args, **kwargs)
    return decorated

def rate_limit(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == 'POST':
            ip = get_client_ip()
            ip_hash = hash_ip(ip)
            
            row = db.fetchone(
                "SELECT count, window_start FROM rate_limits WHERE ip_hash = ?",
                (ip_hash,)
            )
            
            now = datetime.now()
            
            if row:
                window_start = datetime.fromisoformat(row['window_start'])
                if now < window_start + timedelta(seconds=Config.RATE_LIMIT_WINDOW):
                    if row['count'] >= Config.RATE_LIMIT_COUNT:
                        return jsonify({
                            'success': False,
                            'error': f'Rate limit exceeded. Max {Config.RATE_LIMIT_COUNT} requests per {Config.RATE_LIMIT_WINDOW // 3600} hours.'
                        }), 429
                    db.execute("UPDATE rate_limits SET count = count + 1 WHERE ip_hash = ?", (ip_hash,))
                else:
                    db.execute(
                        "UPDATE rate_limits SET count = 1, window_start = ? WHERE ip_hash = ?",
                        (now.isoformat(), ip_hash)
                    )
            else:
                db.execute(
                    "INSERT INTO rate_limits (ip_hash, count, window_start) VALUES (?, 1, ?)",
                    (ip_hash, now.isoformat())
                )
        
        return f(*args, **kwargs)
    return decorated
