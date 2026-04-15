"""
Natural VPS - Security & Anti-DDoS System
Implements rate limiting, IP blocking, and security headers
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask import request, jsonify, g
from datetime import datetime, timedelta
from app.database import db
from app.utils import hash_ip
import json

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Blocked IPs (anti-DDoS)
blocked_ips = {}
suspicious_ips = {}

class SecurityManager:
    """Manages security policies and threat detection"""
    
    @staticmethod
    def init_security(app):
        """Initialize security features on Flask app"""
        
        # Add security headers
        Talisman(
            app,
            force_https=True,
            strict_transport_security=True,
            strict_transport_security_max_age=31536000,
            content_security_policy={
                'default-src': "'self'",
                'script-src': ["'self'", "'unsafe-inline'", "cdnjs.cloudflare.com", "fonts.googleapis.com"],
                'style-src': ["'self'", "'unsafe-inline'", "cdnjs.cloudflare.com", "fonts.googleapis.com"],
                'font-src': ["'self'", "fonts.gstatic.com", "cdnjs.cloudflare.com"],
                'img-src': ["'self'", "data:", "https:"],
                'connect-src': ["'self'"],
            },
            content_security_policy_nonce_in='script-src',
            referrer_policy='strict-origin-when-cross-origin'
        )
        
        # Register before_request handler
        app.before_request(SecurityManager.check_request)
        
        # Register after_request handler
        app.after_request(SecurityManager.add_security_headers)
        
        print("[OK] Security system initialized")
    
    @staticmethod
    def check_request():
        """Check incoming requests for threats"""
        ip = get_remote_address()
        ip_hash = hash_ip(ip)
        
        # Check if IP is blocked
        if ip in blocked_ips:
            if datetime.now() < blocked_ips[ip]:
                return jsonify({'error': 'IP blocked - DDoS detected'}), 403
            else:
                del blocked_ips[ip]
        
        # Check for suspicious patterns
        SecurityManager.detect_suspicious_activity(ip, ip_hash)
    
    @staticmethod
    def detect_suspicious_activity(ip, ip_hash):
        """Detect and log suspicious patterns"""
        
        if ip not in suspicious_ips:
            suspicious_ips[ip] = {'requests': 0, 'last_request': datetime.now(), 'patterns': []}
        
        now = datetime.now()
        data = suspicious_ips[ip]
        
        # Reset if outside window
        if now - data['last_request'] > timedelta(minutes=1):
            suspicious_ips[ip] = {'requests': 0, 'last_request': now, 'patterns': []}
            return
        
        # Count requests in window
        data['requests'] += 1
        data['last_request'] = now
        
        # Block if too many requests in short time (DDoS pattern)
        if data['requests'] > 100:  # 100 requests per minute
            blocked_ips[ip] = datetime.now() + timedelta(hours=1)
            print(f"[ALERT] DDOS BLOCKED: {ip} - {data['requests']} requests/min")
            db.execute(
                "INSERT INTO login_attempts (ip_hash, username, success, timestamp) VALUES (?, ?, ?, ?)",
                (ip_hash, "DDOS_BLOCK", 0, datetime.now().isoformat())
            )
        
        # Watch for brute force
        elif data['requests'] > 30:
            data['patterns'].append({
                'type': 'high_frequency',
                'time': now.isoformat(),
                'count': data['requests']
            })
    
    @staticmethod
    def add_security_headers(response):
        """Add security headers to response"""
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Prevent MIME sniffing
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'"
        
        # No caching for sensitive endpoints
        if request.path.startswith('/api/auth') or request.path.startswith('/api/vps'):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
        
        return response
    
    @staticmethod
    def rate_limit_by_endpoint(endpoint_type, limit="5 per hour"):
        """Apply rate limiting to specific endpoints"""
        return limiter.limit(limit)
    
    @staticmethod
    def get_suspicious_ips():
        """Get list of suspicious IPs"""
        return suspicious_ips
    
    @staticmethod
    def get_blocked_ips():
        """Get list of blocked IPs"""
        return {ip: str(exp_time) for ip, exp_time in blocked_ips.items()}

# IP Blacklist/Whitelist Management
class IPManager:
    """Manage IP blacklist and whitelist"""
    
    @staticmethod
    def is_ip_whitelisted(ip):
        """Check if IP is in whitelist"""
        whitelist = db.fetchone("SELECT * FROM ip_whitelist WHERE ip = ?", (ip,))
        return whitelist is not None
    
    @staticmethod
    def is_ip_blacklisted(ip):
        """Check if IP is in blacklist"""
        blacklist = db.fetchone("SELECT * FROM ip_blacklist WHERE ip = ? AND expires_at > ?", 
                               (ip, datetime.now().isoformat()))
        return blacklist is not None
    
    @staticmethod
    def add_to_blacklist(ip, reason, hours=24):
        """Add IP to blacklist"""
        expires = (datetime.now() + timedelta(hours=hours)).isoformat()
        db.execute(
            "INSERT OR REPLACE INTO ip_blacklist (ip, reason, added_at, expires_at) VALUES (?, ?, ?, ?)",
            (ip, reason, datetime.now().isoformat(), expires)
        )
    
    @staticmethod
    def add_to_whitelist(ip, reason):
        """Add IP to whitelist"""
        db.execute(
            "INSERT OR IGNORE INTO ip_whitelist (ip, reason, added_at) VALUES (?, ?, ?)",
            (ip, reason, datetime.now().isoformat())
        )

# Request logging for monitoring
class RequestLogger:
    """Log requests for monitoring and analysis"""
    
    @staticmethod
    def log_request(ip, method, path, status_code, user_id=None):
        """Log HTTP request"""
        try:
            db.execute(
                """INSERT INTO request_logs (ip, method, path, status_code, user_id, timestamp) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (ip, method, path, status_code, user_id, datetime.now().isoformat())
            )
        except:
            pass
    
    @staticmethod
    def get_request_stats(hours=24):
        """Get request statistics for the last N hours"""
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        stats = db.fetchone(
            """SELECT 
               COUNT(*) as total_requests,
               SUM(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 ELSE 0 END) as successful,
               SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as errors,
               COUNT(DISTINCT ip) as unique_ips
            FROM request_logs WHERE timestamp > ?""",
            (since,)
        )
        
        return dict(stats) if stats else {}
