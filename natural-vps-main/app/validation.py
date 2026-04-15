"""
Natural VPS - Advanced Input Validation & Data Sanitization
Comprehensive validation to prevent security vulnerabilities
"""

import re
import json
from functools import wraps
from flask import request, jsonify, g

class InputValidator:
    """Advanced input validation"""
    
    # Validation patterns
    USERNAME_PATTERN = r'^[a-zA-Z0-9_-]{3,30}$'
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    URL_PATTERN = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}.*$'
    IP_PATTERN = r'^(\d{1,3}\.){3}\d{1,3}$'
    
    @staticmethod
    def validate_username(username):
        """Validate username"""
        if not username or len(username) < 3 or len(username) > 30:
            return False, 'Username must be 3-30 characters'
        if not re.match(InputValidator.USERNAME_PATTERN, username):
            return False, 'Username can only contain letters, numbers, underscore, hyphen'
        return True, None
    
    @staticmethod
    def validate_email(email):
        """Validate email"""
        if not email or not re.match(InputValidator.EMAIL_PATTERN, email):
            return False, 'Invalid email format'
        if len(email) > 254:
            return False, 'Email too long'
        return True, None
    
    @staticmethod
    def validate_password(password):
        """Validate password strength"""
        if len(password) < 8:
            return False, 'Password must be at least 8 characters'
        if not re.search(r'[A-Z]', password):
            return False, 'Password must contain uppercase letter'
        if not re.search(r'[a-z]', password):
            return False, 'Password must contain lowercase letter'
        if not re.search(r'[0-9]', password):
            return False, 'Password must contain number'
        if re.search(r'[<>"\'\;&#]', password):
            return False, 'Password contains invalid characters'
        return True, None
    
    @staticmethod
    def validate_url(url):
        """Validate URL"""
        if not url or not re.match(InputValidator.URL_PATTERN, url):
            return False, 'Invalid URL format'
        return True, None
    
    @staticmethod
    def validate_ip(ip):
        """Validate IP address"""
        if not re.match(InputValidator.IP_PATTERN, ip):
            return False, 'Invalid IP address'
        
        # Check octets
        octets = ip.split('.')
        for octet in octets:
            if int(octet) > 255:
                return False, 'Invalid IP address'
        return True, None
    
    @staticmethod
    def sanitize_string(value):
        """Remove potentially dangerous characters"""
        # Remove SQL injection attempts
        dangerous_patterns = ['--', ';', '/*', '*/', 'xp_', 'sp_', 'DROP', 'DELETE', 'INSERT']
        for pattern in dangerous_patterns:
            value = value.replace(pattern, '')
        return value
    
    @staticmethod
    def sanitize_json(data):
        """Sanitize JSON data"""
        if isinstance(data, dict):
            return {k: InputValidator.sanitize_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [InputValidator.sanitize_json(item) for item in data]
        elif isinstance(data, str):
            return InputValidator.sanitize_string(data)
        return data

def require_valid_input(*required_fields):
    """Decorator to validate required input fields"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if request.method in ['POST', 'PUT', 'PATCH']:
                data = request.get_json()
                if not data:
                    return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
                
                # Check required fields
                for field in required_fields:
                    if field not in data or data[field] is None:
                        return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
                
                # Sanitize input
                g.validated_data = InputValidator.sanitize_json(data)
            else:
                g.validated_data = {}
            
            return f(*args, **kwargs)
        return decorated
    return decorator

class DataSanitizer:
    """Comprehensive data sanitization"""
    
    @staticmethod
    def sanitize_for_html(value):
        """Escape HTML special characters"""
        if not isinstance(value, str):
            return value
        
        replacements = {
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;',
            '&': '&amp;'
        }
        
        for char, escape in replacements.items():
            value = value.replace(char, escape)
        return value
    
    @staticmethod
    def sanitize_for_sql(value):
        """Escape SQL special characters"""
        if not isinstance(value, str):
            return value
        return value.replace("'", "''")
    
    @staticmethod
    def sanitize_file_path(path):
        """Prevent directory traversal"""
        if '..' in path or path.startswith('/'):
            raise ValueError('Invalid file path')
        return path
    
    @staticmethod
    def sanitize_api_key(key):
        """Validate and sanitize API key"""
        if not re.match(r'^nv_[a-zA-Z0-9]{32,}$', key):
            raise ValueError('Invalid API key format')
        return key

class RateLimitValidator:
    """Validate against rate limiting"""
    
    @staticmethod
    def check_rate_limit(identifier, max_requests=10, window_seconds=60):
        """Check if identifier exceeds rate limit"""
        from app.database import db
        from datetime import datetime, timedelta
        
        now = datetime.now()
        window_start = now - timedelta(seconds=window_seconds)
        
        # Count requests in window
        count = db.fetchone("""
            SELECT COUNT(*) as count FROM request_logs 
            WHERE ip = ? AND timestamp > ?
        """, (identifier, window_start.isoformat()))
        
        return (count['count'] if count else 0) < max_requests

class TypeValidator:
    """Validate data types"""
    
    @staticmethod
    def validate_string(value, max_length=255):
        """Validate string"""
        if not isinstance(value, str):
            return False, 'Not a string'
        if len(value) > max_length:
            return False, f'String exceeds max length of {max_length}'
        return True, None
    
    @staticmethod
    def validate_integer(value, min_val=0, max_val=None):
        """Validate integer"""
        if not isinstance(value, int):
            return False, 'Not an integer'
        if value < min_val:
            return False, f'Value below minimum of {min_val}'
        if max_val and value > max_val:
            return False, f'Value exceeds maximum of {max_val}'
        return True, None
    
    @staticmethod
    def validate_boolean(value):
        """Validate boolean"""
        if not isinstance(value, bool):
            return False, 'Not a boolean'
        return True, None
    
    @staticmethod
    def validate_json_object(value):
        """Validate JSON object"""
        if not isinstance(value, dict):
            return False, 'Not a valid JSON object'
        return True, None

# Validation for common fields
FIELD_VALIDATORS = {
    'username': InputValidator.validate_username,
    'email': InputValidator.validate_email,
    'password': InputValidator.validate_password,
    'url': InputValidator.validate_url,
    'ip': InputValidator.validate_ip
}
