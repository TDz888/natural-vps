"""
Natural VPS - Enhanced Validation System
Comprehensive input validation, sanitization, and error handling
"""

import re
from typing import Tuple, Any, Dict, List
import bleach
from datetime import datetime

class ValidationError(Exception):
    """Custom validation exception"""
    pass

class InputValidator:
    """Comprehensive input validation"""
    
    # Regex patterns
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,30}$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    GITHUB_TOKEN_PATTERN = re.compile(r'^ghp_[a-zA-Z0-9]{36}$')
    TAILSCALE_KEY_PATTERN = re.compile(r'^tskey-[a-zA-Z0-9]{47}$')
    IPV4_PATTERN = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
    URL_PATTERN = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$',
        re.IGNORECASE
    )
    
    # Safe HTML tags
    ALLOWED_TAGS = ['b', 'i', 'em', 'strong', 'p', 'br', 'a']
    ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}
    
    @staticmethod
    def validate_username(username: str, min_length: int = 3, max_length: int = 30) -> Tuple[bool, str]:
        """Validate username format"""
        if not username:
            return False, "Username is required"
        
        if len(username) < min_length or len(username) > max_length:
            return False, f"Username must be {min_length}-{max_length} characters"
        
        if not InputValidator.USERNAME_PATTERN.match(username):
            return False, "Username can only contain letters, numbers, and underscores"
        
        # Check for reserved usernames
        reserved = ['admin', 'root', 'system', 'test', 'guest', 'api']
        if username.lower() in reserved:
            return False, "This username is reserved"
        
        return True, ""
    
    @staticmethod
    def validate_password(password: str, min_length: int = 8) -> Tuple[bool, str]:
        """Validate password strength"""
        if not password:
            return False, "Password is required"
        
        if len(password) < min_length:
            return False, f"Password must be at least {min_length} characters"
        
        if len(password) > 128:
            return False, "Password is too long (max 128 characters)"
        
        # Require diverse character types
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*_\-=+]', password))
        
        requirements_met = sum([has_upper, has_lower, has_digit, has_special])
        if requirements_met < 3:
            return False, "Password must contain uppercase, lowercase, number, and special character"
        
        return True, ""
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email format"""
        if not email:
            return False, "Email is required"
        
        if len(email) > 254:
            return False, "Email address is too long"
        
        if not InputValidator.EMAIL_PATTERN.match(email):
            return False, "Invalid email format"
        
        # Check for common typos
        common_typos = {
            'gmial.com': 'gmail.com',
            'gmai.com': 'gmail.com',
            'yahooo.com': 'yahoo.com',
            'hotmial.com': 'hotmail.com'
        }
        
        domain = email.split('@')[1].lower()
        if domain in common_typos:
            return False, f"Did you mean {email.split('@')[0]}@{common_typos[domain]}?"
        
        return True, ""
    
    @staticmethod
    def validate_github_token(token: str) -> Tuple[bool, str]:
        """Validate GitHub token format"""
        if not token:
            return False, "GitHub token is required"
        
        token = token.strip()
        
        if not token.startswith('ghp_'):
            return False, "Invalid token format (must start with 'ghp_')"
        
        if len(token) != 40:
            return False, "Invalid token length"
        
        return True, ""
    
    @staticmethod
    def validate_tailscale_key(key: str) -> Tuple[bool, str]:
        """Validate Tailscale key format"""
        if not key:
            return False, "Tailscale key is required"
        
        key = key.strip()
        
        if not key.startswith('tskey-'):
            return False, "Invalid key format (must start with 'tskey-')"
        
        if len(key) != 53:
            return False, "Invalid key length"
        
        return True, ""
    
    @staticmethod
    def validate_vm_name(name: str) -> Tuple[bool, str]:
        """Validate VM name"""
        if not name:
            return False, "VM name is required"
        
        if len(name) < 1 or len(name) > 50:
            return False, "VM name must be 1-50 characters"
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            return False, "VM name can only contain letters, numbers, dashes, and underscores"
        
        return True, ""
    
    @staticmethod
    def validate_ipaddress(ip: str) -> Tuple[bool, str]:
        """Validate IPv4 address"""
        if not ip:
            return False, "IP address is required"
        
        if not InputValidator.IPV4_PATTERN.match(ip):
            return False, "Invalid IP address format"
        
        # Validate octets
        octets = ip.split('.')
        for octet in octets:
            try:
                num = int(octet)
                if num < 0 or num > 255:
                    return False, "IP octets must be between 0 and 255"
            except ValueError:
                return False, "Invalid IP address format"
        
        return True, ""
    
    @staticmethod
    def validate_url(url: str) -> Tuple[bool, str]:
        """Validate URL format"""
        if not url:
            return False, "URL is required"
        
        if len(url) > 2048:
            return False, "URL is too long"
        
        if not InputValidator.URL_PATTERN.match(url):
            return False, "Invalid URL format"
        
        return True, ""
    
    @staticmethod
    def sanitize_html(html_content: str) -> str:
        """Sanitize HTML content"""
        if not html_content:
            return ""
        
        return bleach.clean(
            html_content,
            tags=InputValidator.ALLOWED_TAGS,
            attributes=InputValidator.ALLOWED_ATTRIBUTES,
            strip=True
        )
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 500) -> str:
        """Sanitize string input"""
        if not text:
            return ""
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Truncate if needed
        if len(text) > max_length:
            text = text[:max_length]
        
        # Remove dangerous characters
        text = re.sub(r'[<>"\']', '', text)
        
        return text.strip()
    
    @staticmethod
    def validate_request_body(data: Dict, required_fields: List[str], field_types: Dict[str, type] = None) -> Tuple[bool, str]:
        """Validate request body"""
        if not data:
            return False, "Request body is empty"
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                return False, f"Missing required field: {field}"
            
            if data[field] is None:
                return False, f"Field '{field}' cannot be null"
        
        # Check field types if specified
        if field_types:
            for field, expected_type in field_types.items():
                if field in data:
                    if not isinstance(data[field], expected_type):
                        return False, f"Field '{field}' must be {expected_type.__name__}"
        
        return True, ""


class SecurityValidator:
    """Security-specific validation"""
    
    @staticmethod
    def validate_session_token(token: str) -> Tuple[bool, str]:
        """Validate session token format"""
        if not token:
            return False, "Token is required"
        
        if len(token) < 20:
            return False, "Invalid token"
        
        if len(token) > 1000:
            return False, "Token too long"
        
        return True, ""
    
    @staticmethod
    def validate_csrf_token(token: str) -> Tuple[bool, str]:
        """Validate CSRF token"""
        if not token:
            return False, "CSRF token missing"
        
        if len(token) != 64:
            return False, "Invalid CSRF token"
        
        if not re.match(r'^[a-f0-9]{64}$', token):
            return False, "Invalid CSRF token format"
        
        return True, ""
    
    @staticmethod
    def check_rate_limit(ip: str, endpoint: str, max_requests: int = 5, window_seconds: int = 3600) -> Tuple[bool, str]:
        """Check if IP exceeds rate limit"""
        # This would typically use Redis in production
        from datetime import datetime, timedelta
        
        current_time = datetime.now()
        # Implementation would depend on your storage backend
        
        return True, ""
    
    @staticmethod
    def validate_no_sql_injection(text: str) -> Tuple[bool, str]:
        """Check for NoSQL injection patterns"""
        dangerous_patterns = ['$where', '$regex', '$or', '$and', '$nor', '$not', '$elemMatch']
        
        for pattern in dangerous_patterns:
            if pattern in text.lower():
                return False, f"Detected potentially malicious pattern: {pattern}"
        
        return True, ""
    
    @staticmethod
    def validate_no_xss_payload(text: str) -> Tuple[bool, str]:
        """Check for XSS payload patterns"""
        xss_patterns = [
            r'<script[^>]*>',
            r'onerror\s*=',
            r'onclick\s*=',
            r'javascript:',
            r'eval\s*\(',
            r'expression\s*\('
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False, "Detected potentially malicious content"
        
        return True, ""


# Exceptions for specific validation scenarios
class InvalidUsernameError(ValidationError):
    pass

class InvalidPasswordError(ValidationError):
    pass

class InvalidEmailError(ValidationError):
    pass

class InvalidTokenError(ValidationError):
    pass
