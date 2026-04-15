"""
Natural VPS - Email Generation & Notification Service
Generates @naturalvps email addresses and manages user notifications
"""

import string
import random
from typing import Tuple
import re

class EmailService:
    """Manages @naturalvps email addresses and notifications"""
    
    VPS_DOMAIN = "naturalvps.local"  # Internal domain, can be configured
    
    @staticmethod
    def generate_vpn_email() -> str:
        """Generate a random @naturalvps email address"""
        # Format: nv_<random_chars>@naturalvps
        prefix = "nv_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"{prefix}@naturalvps"
    
    @staticmethod
    def generate_web_username() -> str:
        """Generate a random web-only username"""
        # Format: user_<random_chars>
        adjectives = ['swift', 'swift', 'bright', 'calm', 'fresh', 'wild', 'brave', 'keen']
        animals = ['eagle', 'falcon', 'wolf', 'deer', 'bear', 'fox', 'lynx', 'crane']
        
        adj = random.choice(adjectives)
        animal = random.choice(animals)
        num = random.randint(100, 999)
        
        return f"{adj}_{animal}{num}"
    
    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """Generate a secure random password"""
        # Include uppercase, lowercase, numbers, and special chars
        chars = string.ascii_letters + string.digits + "!@#$%^&*-_=+"
        password = ''.join(random.choices(chars, k=length))
        
        # Ensure we have at least one of each type
        password = list(password)
        random.shuffle(password)
        
        # Replace some random chars to ensure variety
        password[0] = random.choice(string.ascii_uppercase)
        password[1] = random.choice(string.digits)
        password[2] = random.choice("!@#$%^&*-_=+")
        
        return ''.join(password)
    
    @staticmethod
    def validate_real_email(email: str) -> Tuple[bool, str]:
        """Validate a real email address"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not email or len(email) > 254:
            return False, "Email too long or empty"
        
        if not re.match(pattern, email):
            return False, "Invalid email format"
        
        # Block disposable email domains
        disposable_domains = ['tempmail', 'throwaway', '10minutemail', 'guerrillamail', 
                             'mailinator', 'maildrop', 'mintemail', 'temp-mail']
        domain = email.split('@')[1].lower()
        
        if any(blocked in domain for blocked in disposable_domains):
            return False, "Disposable email addresses are not allowed"
        
        return True, "Valid"


class NotificationService:
    """Manages user notifications and preferences"""
    
    # Notification types
    NOTIFICATION_TYPES = {
        'vm_created': 'VM Created Successfully',
        'vm_error': 'VM Creation Failed',
        'vm_expiring': 'VM Expiring Soon',
        'vm_expired': 'VM Expired',
        'security_alert': 'Security Alert',
        'system_update': 'System Update',
        'account_activity': 'Account Activity'
    }
    
    @staticmethod
    def get_default_preferences() -> dict:
        """Get default notification preferences"""
        return {
            'vm_created': {'email': True, 'web': True},
            'vm_error': {'email': True, 'web': True},
            'vm_expiring': {'email': True, 'web': True},
            'vm_expired': {'email': True, 'web': False},
            'security_alert': {'email': True, 'web': True},
            'system_update': {'email': False, 'web': True},
            'account_activity': {'email': False, 'web': True},
        }
    
    @staticmethod
    def format_notification(event_type: str, data: dict) -> dict:
        """Format a notification message"""
        templates = {
            'vm_created': {
                'title': 'VM Created Successfully',
                'template': 'Your VM "{vm_name}" has been created and is ready to use.',
                'icon': 'success'
            },
            'vm_error': {
                'title': 'VM Creation Failed',
                'template': 'Failed to create VM "{vm_name}": {error_message}',
                'icon': 'error'
            },
            'vm_expiring': {
                'title': 'VM Expiring Soon',
                'template': 'Your VM "{vm_name}" will expire in {hours} hours.',
                'icon': 'warning'
            },
            'vm_expired': {
                'title': 'VM Expired',
                'template': 'Your VM "{vm_name}" has expired and been removed.',
                'icon': 'info'
            },
            'security_alert': {
                'title': 'Security Alert',
                'template': 'Suspicious activity detected: {alert_details}',
                'icon': 'alert'
            }
        }
        
        if event_type not in templates:
            return {'title': 'Notification', 'message': str(data), 'icon': 'info'}
        
        template = templates[event_type]
        message = template['template'].format(**data)
        
        return {
            'type': event_type,
            'title': template['title'],
            'message': message,
            'icon': template['icon'],
            'data': data
        }


# Credentials template for initial email to user
CREDENTIALS_EMAIL_TEMPLATE = """
Dear User,

Welcome to Natural VPS! 🌿

Your account has been successfully created. Here are your login credentials:

═══════════════════════════════════════════════════════════════
  ACCOUNT CREDENTIALS
═══════════════════════════════════════════════════════════════

Web-Only Email:  {vps_email}
Username:        {web_username}
Password:        {web_password}
Real Email:      {real_email}

═══════════════════════════════════════════════════════════════

IMPORTANT: Please save these credentials in a secure location.

Next Steps:
1. Go to https://naturalvps.example.com
2. Log in with your username and password
3. Create your first Virtual Machine
4. Configure notification preferences

Support:
- Documentation: https://docs.naturalvps.example.com
- Issues: support@naturalvps.example.com

Welcome to the Natural VPS Community!

Best regards,
The Natural VPS Team
"""
