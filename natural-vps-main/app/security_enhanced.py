"""
Natural VPS - Enhanced Security System with CSRF, CORS, and Connectivity Fixes
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask import request, jsonify, g, make_response
from datetime import datetime, timedelta
from app.database import db
from app.utils import hash_ip
import json
import secrets
import re

# Initialize rate limiter with Redis-like memory storage
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    strategy="fixed-window"
)

# In-memory stores for IPs and CSRF tokens
blocked_ips = {}
suspicious_ips = {}
csrf_tokens = {}
connection_cache = {}

class SecurityManager:
    """Enhanced Security Manager with CSRF, connectivity fixes, and improved CORS"""
    
    @staticmethod
    def init_security(app):
        """Initialize comprehensive security features on Flask app"""
        
        # 1. Configure Security Headers with Talisman
        Talisman(
            app,
            force_https=False,  # Allow HTTP for local development, change to True in production
            strict_transport_security=True,
            strict_transport_security_max_age=31536000,
            strict_transport_security_include_subdomains=True,
            strict_transport_security_preload=True,
            content_security_policy={
                'default-src': "'self'",
                'script-src': [
                    "'self'",
                    "'unsafe-inline'",
                    "'unsafe-eval'",
                    "cdnjs.cloudflare.com",
                    "fonts.googleapis.com",
                    "cdn.jsdelivr.net",
                    "unpkg.com"
                ],
                'style-src': [
                    "'self'",
                    "'unsafe-inline'",
                    "cdnjs.cloudflare.com",
                    "fonts.googleapis.com",
                    "cdn.jsdelivr.net"
                ],
                'font-src': [
                    "'self'",
                    "fonts.gstatic.com",
                    "cdnjs.cloudflare.com",
                    "fonts.googleapis.com"
                ],
                'img-src': [
                    "'self'",
                    "data:",
                    "https:",
                    "*.githubusercontent.com"
                ],
                'connect-src': [
                    "'self'",
                    "*.github.com",
                    "api.github.com",
                    "*.tailscale.com"
                ],
                'media-src': ["'self'", "data:"],
                'frame-ancestors': ["'self'"]
            },
            referrer_policy='strict-origin-when-cross-origin',
            permissions_policy={
                'accelerometer': [],
                'geolocation': [],
                'gyroscope': [],
                'magnetometer': [],
                'microphone': [],
                'payment': [],
                'usb': []
            }
        )
        
        # 2. Register security middleware
        app.before_request(SecurityManager.check_request)
        app.before_request(SecurityManager.handle_preflight)
        app.after_request(SecurityManager.add_security_headers)
        app.after_request(SecurityManager.handle_cors_response)
        
        # 3. Error handlers
        app.register_error_handler(400, lambda e: SecurityManager.handle_error(e, 400))
        app.register_error_handler(403, lambda e: SecurityManager.handle_error(e, 403))
        app.register_error_handler(404, lambda e: SecurityManager.handle_error(e, 404))
        app.register_error_handler(500, lambda e: SecurityManager.handle_error(e, 500))
        
        print("[OK] Enhanced Security System Initialized")
    
    @staticmethod
    def handle_preflight():
        """Handle CORS preflight requests"""
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRF-Token'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Max-Age'] = '3600'
            return response, 200
    
    @staticmethod
    def handle_cors_response(response):
        """Fix CORS issues by adding proper headers"""
        origin = request.headers.get('Origin')
        
        # Allow local and trusted origins
        allowed_origins = [
            'http://localhost:3000',
            'http://localhost:5000',
            'http://127.0.0.1:5000',
            'http://34.10.118.99',
            'http://34.10.118.99:5000'
        ]
        
        if origin in allowed_origins or origin is None:
            response.headers['Access-Control-Allow-Origin'] = origin or '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRF-Token, X-Requested-With'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Expose-Headers'] = 'Content-Length, X-CSRF-Token'
        
        return response
    
    @staticmethod
    def check_request():
        """Check incoming requests for threats and connectivity issues"""
        # Skip checks for health and static endpoints
        if request.path.startswith('/static') or request.path == '/api/health':
            return
        
        ip = get_remote_address()
        ip_hash = hash_ip(ip)
        
        # Store request info for later use
        g.client_ip = ip
        g.ip_hash = ip_hash
        
        # Check if IP is whitelisted (skip other checks)
        if IPManager.is_ip_whitelisted(ip):
            return
        
        # Check if IP is blacklisted
        if IPManager.is_ip_blacklisted(ip):
            return jsonify({'error': 'Your IP is temporarily blocked. Please try again later.'}), 403
        
        # Detect suspicious activity
        SecurityManager.detect_suspicious_activity(ip, ip_hash)
        
        # Log request for monitoring
        if request.method in ['POST', 'PUT', 'DELETE']:
            RequestLogger.log_request(ip, request.method, request.path)
    
    @staticmethod
    def detect_suspicious_activity(ip, ip_hash):
        """Detect and prevent DDoS attacks"""
        if ip not in suspicious_ips:
            suspicious_ips[ip] = {
                'requests': 0,
                'last_request': datetime.now(),
                'patterns': []
            }
        
        now = datetime.now()
        data = suspicious_ips[ip]
        
        # Reset if outside 1-minute window
        if now - data['last_request'] > timedelta(minutes=1):
            suspicious_ips[ip] = {
                'requests': 0,
                'last_request': now,
                'patterns': []
            }
            return
        
        data['requests'] += 1
        data['last_request'] = now
        
        # DDoS detection: Block if >150 requests per minute
        if data['requests'] > 150:
            blocked_ips[ip] = datetime.now() + timedelta(hours=1)
            print(f"[ALERT] DDoS BLOCKED: {ip} with {data['requests']} requests/min")
            db.execute(
                "INSERT INTO security_events (ip_hash, event_type, severity, details, timestamp) VALUES (?, ?, ?, ?, ?)",
                (ip_hash, "DDOS_BLOCK", "CRITICAL", json.dumps({"requests": data['requests']}), datetime.now().isoformat())
            )
    
    @staticmethod
    def add_security_headers(response):
        """Add comprehensive security headers"""
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Disable caching for auth and API endpoints
        if request.path.startswith(('/api/auth', '/api/vms', '/api/monitor')):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, private'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        else:
            response.headers['Cache-Control'] = 'public, max-age=3600'
        
        return response
    
    @staticmethod
    def handle_error(error, status_code):
        """Handle errors with improved messages"""
        error_map = {
            400: "Bad Request - Invalid input",
            403: "Access Denied - Check your credentials or IP",
            404: "Resource Not Found",
            500: "Server Error - Please try again later"
        }
        
        return jsonify({
            'success': False,
            'error': error_map.get(status_code, 'An error occurred'),
            'status': status_code
        }), status_code
    
    @staticmethod
    def generate_csrf_token():
        """Generate CSRF token"""
        token = secrets.token_hex(32)
        csrf_tokens[token] = datetime.now() + timedelta(hours=1)
        return token
    
    @staticmethod
    def verify_csrf_token(token):
        """Verify CSRF token"""
        if token not in csrf_tokens:
            return False
        if datetime.now() > csrf_tokens[token]:
            del csrf_tokens[token]
            return False
        return True
    
    @staticmethod
    def get_suspicious_ips():
        """Get list of suspicious IPs"""
        return suspicious_ips
    
    @staticmethod
    def get_blocked_ips():
        """Get list of blocked IPs"""
        return {ip: str(exp_time) for ip, exp_time in blocked_ips.items()}


class IPManager:
    """Manage IP blacklist and whitelist"""
    
    @staticmethod
    def is_ip_whitelisted(ip):
        """Check if IP is in whitelist"""
        try:
            whitelist = db.fetchone("SELECT * FROM ip_whitelist WHERE ip = ?", (ip,))
            return whitelist is not None
        except:
            return False
    
    @staticmethod
    def is_ip_blacklisted(ip):
        """Check if IP is in blacklist"""
        try:
            blacklist = db.fetchone(
                "SELECT * FROM ip_blacklist WHERE ip = ? AND expires_at > ?",
                (ip, datetime.now().isoformat())
            )
            return blacklist is not None
        except:
            return False
    
    @staticmethod
    def add_to_blacklist(ip, reason, hours=24):
        """Add IP to blacklist"""
        expires = (datetime.now() + timedelta(hours=hours)).isoformat()
        try:
            db.execute(
                "INSERT OR REPLACE INTO ip_blacklist (ip, reason, added_at, expires_at) VALUES (?, ?, ?, ?)",
                (ip, reason, datetime.now().isoformat(), expires)
            )
            print(f"[BLOCKED] Blacklisted {ip}: {reason}")
        except Exception as e:
            print(f"Error blacklisting IP: {e}")
    
    @staticmethod
    def add_to_whitelist(ip, reason):
        """Add IP to whitelist"""
        try:
            db.execute(
                "INSERT OR IGNORE INTO ip_whitelist (ip, reason, added_at) VALUES (?, ?, ?)",
                (ip, reason, datetime.now().isoformat())
            )
            print(f"[OK] Whitelisted {ip}: {reason}")
        except Exception as e:
            print(f"Error whitelisting IP: {e}")
    
    @staticmethod
    def remove_from_blacklist(ip):
        """Remove IP from blacklist"""
        try:
            db.execute("DELETE FROM ip_blacklist WHERE ip = ?", (ip,))
            print(f"[REMOVED] Removed {ip} from blacklist")
        except Exception as e:
            print(f"Error removing IP: {e}")


class RequestLogger:
    """Log requests for monitoring and analysis"""
    
    @staticmethod
    def log_request(ip, method, path, status_code=200, user_id=None):
        """Log HTTP request"""
        try:
            db.execute(
                "INSERT INTO request_logs (ip, method, path, status_code, user_id, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (ip, method, path, status_code, user_id, datetime.now().isoformat())
            )
        except Exception as e:
            print(f"Logging error: {e}")
    
    @staticmethod
    def get_request_stats(hours=24):
        """Get request statistics for the last N hours"""
        try:
            since = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            stats = db.fetchone(
                """SELECT
                    COUNT(*) as total_requests,
                    COUNT(DISTINCT ip) as unique_ips,
                    SUM(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as failed
                FROM request_logs
                WHERE timestamp > ?""",
                (since,)
            )
            
            return {
                'total_requests': stats['total_requests'] or 0,
                'unique_ips': stats['unique_ips'] or 0,
                'successful': stats['successful'] or 0,
                'failed': stats['failed'] or 0
            }
        except Exception as e:
            print(f"Stats error: {e}")
            return {'total_requests': 0, 'unique_ips': 0, 'successful': 0, 'failed': 0}


class ConnectivityManager:
    """Manage and fix connectivity issues"""
    
    @staticmethod
    def test_connection(endpoint, timeout=5):
        """Test connection to endpoint"""
        import requests
        try:
            response = requests.get(endpoint, timeout=timeout)
            return response.status_code == 200
        except:
            return False
    
    @staticmethod
    def get_api_endpoint():
        """Get corrected API endpoint"""
        from app.config import Config
        protocol = "https" if Config.DEBUG is False else "http"
        return f"{protocol}://{Config.API_ENDPOINT}:{Config.API_PORT}"
    
    @staticmethod
    def validate_url(url):
        """Validate URL format"""
        url_pattern = re.compile(
            r'^https?://'  # protocol
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None
