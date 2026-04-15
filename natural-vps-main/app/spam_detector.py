"""
Natural VPS - Advanced Anti-Spam System
Professional spam detection with multiple strategies
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from app.database import db
from app.utils import hash_ip
import json

class SpamDetector:
    """Advanced spam detection system"""
    
    # Configuration thresholds
    REGISTRATION_LIMITS = {
        'per_ip_per_hour': 3,
        'per_ip_per_day': 10,
        'per_email_per_hour': 2,
    }
    
    VPS_CREATION_LIMITS = {
        'per_user_per_hour': 5,
        'per_user_per_day': 15,
        'per_ip_per_hour': 10,
    }
    
    LOGIN_LIMITS = {
        'failed_attempts_per_ip_per_hour': 10,
        'failed_attempts_per_user_per_hour': 5,
    }
    
    IP_SPAM_PATTERNS = {
        'high_error_rate': 0.8,  # >80% errors = suspicious
        'rapid_requests': 100,   # >100 req/min
        'multiple_failures': 50, # >50 failures/hour
    }

    @staticmethod
    def check_registration_spam(ip: str, email: str) -> Tuple[bool, str]:
        """Check if registration should be blocked for spam"""
        ip_hash = hash_ip(ip)
        
        # Check registrations per IP per hour
        ip_registrations_1h = db.fetchone(
            """SELECT COUNT(*) as count FROM users 
               WHERE creator_ip_hash = ? 
               AND created_at > datetime('now', '-1 hour')""",
            (ip_hash,)
        )
        
        if ip_registrations_1h and ip_registrations_1h['count'] >= SpamDetector.REGISTRATION_LIMITS['per_ip_per_hour']:
            return True, f"Too many registrations from IP ({ip_registrations_1h['count']}/{SpamDetector.REGISTRATION_LIMITS['per_ip_per_hour']})"
        
        # Check registrations per IP per day
        ip_registrations_24h = db.fetchone(
            """SELECT COUNT(*) as count FROM users 
               WHERE creator_ip_hash = ? 
               AND created_at > datetime('now', '-24 hours')""",
            (ip_hash,)
        )
        
        if ip_registrations_24h and ip_registrations_24h['count'] >= SpamDetector.REGISTRATION_LIMITS['per_ip_per_day']:
            return True, f"Too many registrations from IP per day ({ip_registrations_24h['count']}/{SpamDetector.REGISTRATION_LIMITS['per_ip_per_day']})"
        
        # Check email registrations per hour
        email_registrations = db.fetchone(
            """SELECT COUNT(*) as count FROM users 
               WHERE email = ? 
               AND created_at > datetime('now', '-1 hour')""",
            (email,)
        )
        
        if email_registrations and email_registrations['count'] >= SpamDetector.REGISTRATION_LIMITS['per_email_per_hour']:
            return True, f"Email already registered recently"
        
        return False, ""

    @staticmethod
    def check_vm_creation_spam(user_id: str, ip: str) -> Tuple[bool, str]:
        """Check if VM creation should be blocked for spam"""
        ip_hash = hash_ip(ip)
        
        # Check per user per hour
        user_vms_1h = db.fetchone(
            """SELECT COUNT(*) as count FROM vms 
               WHERE user_id = ? 
               AND created_at > datetime('now', '-1 hour')""",
            (user_id,)
        )
        
        if user_vms_1h and user_vms_1h['count'] >= SpamDetector.VPS_CREATION_LIMITS['per_user_per_hour']:
            return True, f"User VM creation limit per hour exceeded ({user_vms_1h['count']}/{SpamDetector.VPS_CREATION_LIMITS['per_user_per_hour']})"
        
        # Check per user per day
        user_vms_24h = db.fetchone(
            """SELECT COUNT(*) as count FROM vms 
               WHERE user_id = ? 
               AND created_at > datetime('now', '-24 hours')""",
            (user_id,)
        )
        
        if user_vms_24h and user_vms_24h['count'] >= SpamDetector.VPS_CREATION_LIMITS['per_user_per_day']:
            return True, f"User VM creation limit per day exceeded"
        
        # Check per IP per hour  
        ip_vms_1h = db.fetchone(
            """SELECT COUNT(*) as count FROM vms 
               WHERE creator_ip_hash = ? 
               AND created_at > datetime('now', '-1 hour')""",
            (ip_hash,)
        )
        
        if ip_vms_1h and ip_vms_1h['count'] >= SpamDetector.VPS_CREATION_LIMITS['per_ip_per_hour']:
            return True, f"Too many VMs created from this IP"
        
        return False, ""

    @staticmethod
    def check_login_spam(username: str, ip: str) -> Tuple[bool, str]:
        """Check if login attempts are spam"""
        ip_hash = hash_ip(ip)
        
        # Check failed attempts per IP per hour
        failed_per_ip = db.fetchone(
            """SELECT COUNT(*) as count FROM login_attempts 
               WHERE ip_hash = ? 
               AND success = 0 
               AND timestamp > datetime('now', '-1 hour')""",
            (ip_hash,)
        )
        
        if failed_per_ip and failed_per_ip['count'] >= SpamDetector.LOGIN_LIMITS['failed_attempts_per_ip_per_hour']:
            return True, f"Too many failed login attempts from IP"
        
        # Check failed attempts per user per hour
        failed_per_user = db.fetchone(
            """SELECT COUNT(*) as count FROM login_attempts 
               WHERE username = ? 
               AND success = 0 
               AND timestamp > datetime('now', '-1 hour')""",
            (username,)
        )
        
        if failed_per_user and failed_per_user['count'] >= SpamDetector.LOGIN_LIMITS['failed_attempts_per_user_per_hour']:
            return True, f"Too many failed login attempts for this user"
        
        return False, ""

    @staticmethod
    def detect_suspicious_ip(ip: str, hours: int = 1) -> Dict[str, any]:
        """Detect suspicious patterns from an IP"""
        ip_hash = hash_ip(ip)
        
        # Get request statistics
        stats = db.fetchone(
            """SELECT 
               COUNT(*) as total_requests,
               SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as errors,
               SUM(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 ELSE 0 END) as success,
               MIN(timestamp) as first_seen,
               MAX(timestamp) as last_seen
            FROM request_logs 
            WHERE ip = ? AND timestamp > datetime('now', ? || ' hours')""",
            (ip, f'-{hours}')
        )
        
        if not stats or stats['total_requests'] == 0:
            return {'suspicious': False, 'reason': 'No requests found'}
        
        # Calculate error rate
        error_rate = stats['errors'] / stats['total_requests'] if stats['total_requests'] > 0 else 0
        
        suspicious_indicators = []
        
        # Check for high error rate
        if error_rate >= SpamDetector.IP_SPAM_PATTERNS['high_error_rate']:
            suspicious_indicators.append(f"High error rate: {error_rate*100:.1f}%")
        
        # Check for rapid requests
        if stats['total_requests'] > SpamDetector.IP_SPAM_PATTERNS['rapid_requests']:
            suspicious_indicators.append(f"Rapid requests: {stats['total_requests']} in {hours} hours")
        
        # Check for multiple failures
        if stats['errors'] > SpamDetector.IP_SPAM_PATTERNS['multiple_failures']:
            suspicious_indicators.append(f"Multiple failures: {stats['errors']} errors")
        
        return {
            'suspicious': len(suspicious_indicators) > 0,
            'indicators': suspicious_indicators,
            'stats': {
                'total_requests': stats['total_requests'],
                'errors': stats['errors'],
                'error_rate': f"{error_rate*100:.1f}%",
                'success': stats['success']
            }
        }

    @staticmethod
    def get_spam_score(user_id: str) -> float:
        """Calculate spam score for a user (0-100)"""
        score = 0
        
        # Recent registration
        user_age = db.fetchone(
            "SELECT created_at FROM users WHERE id = ?",
            (user_id,)
        )
        
        if user_age:
            user_created = datetime.fromisoformat(user_age['created_at'])
            age_hours = (datetime.now() - user_created).total_seconds() / 3600
            
            if age_hours < 1:
                score += 20
            elif age_hours < 24:
                score += 10
        
        # Many VMs created quickly
        vms_24h = db.fetchone(
            """SELECT COUNT(*) as count FROM vms 
               WHERE user_id = ? AND created_at > datetime('now', '-24 hours')""",
            (user_id,)
        )
        
        if vms_24h and vms_24h['count'] > 10:
            score += 25
        elif vms_24h and vms_24h['count'] > 5:
            score += 10
        
        # Failed logins
        failed_logins = db.fetchone(
            """SELECT COUNT(*) as count FROM login_attempts 
               WHERE user_id = ? AND success = 0 
               AND timestamp > datetime('now', '-24 hours')""",
            (user_id,)
        )
        
        if failed_logins and failed_logins['count'] > 10:
            score += 15
        
        # Suspended or inactive users
        user = db.fetchone(
            "SELECT is_active FROM users WHERE id = ?",
            (user_id,)
        )
        
        if user and not user['is_active']:
            score += 40
        
        return min(score, 100)

    @staticmethod
    def should_require_email_verification(email: str) -> bool:
        """Check if email should require verification"""
        # Suspicious email patterns
        suspicious_patterns = [
            r'temp.*mail',
            r'fake.*mail',
            r'disposable',
            r'10minute',
            r'guerrillamail',
        ]
        
        for pattern in suspicious_patterns:
            import re
            if re.search(pattern, email, re.IGNORECASE):
                return True
        
        return False

    @staticmethod
    def log_spam_detection(user_id: str, spam_type: str, details: Dict):
        """Log spam detection event"""
        db.execute(
            """INSERT INTO spam_logs (user_id, spam_type, details, timestamp)
               VALUES (?, ?, ?, ?)""",
            (user_id, spam_type, json.dumps(details), datetime.now().isoformat())
        )
