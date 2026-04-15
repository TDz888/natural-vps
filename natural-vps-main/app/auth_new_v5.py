"""
Natural VPS - Updated Authentication Routes v5
With Account Lifetime & VM Quota Management
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
from app.spam_detector import SpamDetector
from app.email_service import EmailService, NotificationService, CREDENTIALS_EMAIL_TEMPLATE
from app.email_verification import EmailVerificationSystem
from app.account_lifetime_manager import AccountLifetimeManager
import json
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register_auto_credentials():
    """
    Register new user with auto-generated credentials and 3-hour lifetime
    
    Request JSON:
    {
        "real_email": "user@gmail.com"  # For notifications
    }
    
    Response includes @naturalvps email, auto-generated username and password
    Auto expiration: 3 hours from now
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        real_email = data.get('real_email', '').strip()
        client_ip = get_client_ip()
        
        # Validate real email
        if not real_email:
            return jsonify({'success': False, 'error': 'Real email address is required'}), 400
        
        is_valid, error = EmailService.validate_real_email(real_email)
        if not is_valid:
            return jsonify({'success': False, 'error': f'Invalid email: {error}'}), 400
        
        # Check if email already registered and not expired
        existing_by_real_email = db.fetchone(
            "SELECT id, is_active FROM users WHERE real_email = ? AND is_active = 1",
            (real_email,)
        )
        if existing_by_real_email:
            return jsonify({
                'success': False,
                'error': 'This email is already registered',
                'help': 'Try logging in or use a different email address'
            }), 400
        
        # Check for spam
        is_spam, spam_reason = SpamDetector.check_registration_spam(client_ip, real_email)
        if is_spam:
            return jsonify({'success': False, 'error': f'Registration blocked: {spam_reason}'}), 429
        
        # Generate credentials
        vps_email = EmailService.generate_vpn_email()
        web_username = EmailService.generate_web_username()
        web_password = EmailService.generate_secure_password()
        
        # Ensure uniqueness
        max_retries = 5
        retries = 0
        while db.fetchone("SELECT id FROM users WHERE vps_email = ?", (vps_email,)) and retries < max_retries:
            vps_email = EmailService.generate_vpn_email()
            retries += 1
        
        retries = 0
        while db.fetchone("SELECT id FROM users WHERE web_username = ?", (web_username,)) and retries < max_retries:
            web_username = EmailService.generate_web_username()
            retries += 1
        
        if retries >= max_retries:
            return jsonify({'success': False, 'error': 'Failed to generate unique credentials'}), 500
        
        # Create user
        user_id = str(uuid.uuid4())
        password_hash = hash_password(web_password)
        api_key = f"nv_{generate_id(16)}"
        
        # Create default notification preferences
        default_prefs = NotificationService.get_default_preferences()
        
        # Account lifetime (3 hours from now)
        now = datetime.now()
        expires_at = now + timedelta(hours=Config.ACCOUNT_LIFETIME_HOURS)
        
        db.execute('''
            INSERT INTO users (
                id, username, vps_email, real_email, web_username,
                email, password_hash, created_at, api_key,
                notification_preferences, email_verified,
                account_created_at, account_expires_at, account_lifetime_hours,
                is_active, vm_quota, is_unlimited
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            web_username,
            vps_email,
            real_email,
            web_username,
            vps_email,
            password_hash,
            now.isoformat(),
            api_key,
            json.dumps(default_prefs),
            0,
            now.isoformat(),
            expires_at.isoformat(),
            Config.ACCOUNT_LIFETIME_HOURS,
            1,  # is_active
            Config.USER_VM_QUOTA,  # 3 VMs
            0  # not unlimited
        ))
        
        # Create notification preferences record
        db.execute('''
            INSERT INTO notification_preferences (user_id, updated_at)
            VALUES (?, ?)
        ''', (user_id, now.isoformat()))
        
        # Generate tokens
        access_token, refresh_token = generate_tokens(user_id)
        
        # Create session
        session_id = str(uuid.uuid4())
        db.execute('''
            INSERT INTO sessions (
                id, user_id, token, refresh_token, created_at,
                expires_at, ip, user_agent
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, user_id, access_token, refresh_token,
            now.isoformat(),
            (now + timedelta(hours=Config.JWT_EXPIRE_HOURS)).isoformat(),
            client_ip,
            request.headers.get('User-Agent', '')
        ))
        
        # Log activity
        db.execute('''
            INSERT INTO user_activity_logs (
                user_id, action, resource_type, details, ip_address, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            'account_created',
            'user',
            f'New account registration (expires in {Config.ACCOUNT_LIFETIME_HOURS}h)',
            client_ip,
            now.isoformat()
        ))
        
        logger.info(f"✓ User {web_username} registered from {client_ip}")
        
        return jsonify({
            'success': True,
            'message': f'Account created successfully! Your account will expire in {Config.ACCOUNT_LIFETIME_HOURS} hours.',
            'user': {
                'id': user_id,
                'vps_email': vps_email,
                'web_username': web_username,
                'real_email': real_email,
                'api_key': api_key
            },
            'lifetime': {
                'account_lifetime_hours': Config.ACCOUNT_LIFETIME_HOURS,
                'expires_at': expires_at.isoformat(),
                'vm_quota': Config.USER_VM_QUOTA
            },
            'token': access_token,
            'refresh_token': refresh_token,
            'credentials_sent': False
        }), 201
    
    except Exception as e:
        logger.error(f"✗ Registration failed: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login with username or vps_email and password
    Checks if account is expired
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        username_or_email = data.get('username', '').strip()
        password = data.get('password', '')
        client_ip = get_client_ip()
        
        if not username_or_email or not password:
            return jsonify({'success': False, 'error': 'Username/email and password required'}), 400
        
        # Find user by username or vps_email
        user = db.fetchone(
            "SELECT * FROM users WHERE (web_username = ? OR vps_email = ? OR username = ?) AND is_active = 1",
            (username_or_email, username_or_email, username_or_email)
        )
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        # Check if account is expired
        is_expired, remaining = AccountLifetimeManager.check_account_expired(db, user['id'])
        if is_expired:
            db.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user['id'],))
            return jsonify({
                'success': False,
                'error': 'Account has expired',
                'expired': True
            }), 401
        
        if not verify_password(password, user['password_hash']):
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        # Update last login
        db.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.now().isoformat(), user['id'])
        )
        
        # Generate tokens
        access_token, refresh_token = generate_tokens(user['id'])
        
        # Create session
        session_id = str(uuid.uuid4())
        db.execute('''
            INSERT INTO sessions (
                id, user_id, token, refresh_token, created_at,
                expires_at, ip, user_agent
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, user['id'], access_token, refresh_token,
            datetime.now().isoformat(),
            (datetime.now() + timedelta(hours=Config.JWT_EXPIRE_HOURS)).isoformat(),
            client_ip,
            request.headers.get('User-Agent', '')
        ))
        
        # Log activity
        db.execute('''
            INSERT INTO user_activity_logs (
                user_id, action, resource_type, details,
                ip_address, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user['id'],
            'login',
            'auth',
            'User login',
            client_ip,
            datetime.now().isoformat()
        ))
        
        logger.info(f"✓ User {user['web_username']} logged in from {client_ip}")
        
        # Get account status
        status = AccountLifetimeManager.get_account_status(db, user['id'])
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'web_username': user['web_username'],
                'vps_email': user['vps_email'],
                'real_email': user['real_email'],
                'display_name': user.get('display_name') or user['web_username'],
                'is_admin': bool(user.get('is_admin', 0))
            },
            'account_status': status,
            'token': access_token,
            'refresh_token': refresh_token
        }), 200
    
    except Exception as e:
        logger.error(f"✗ Login failed: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """Logout user"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        db.execute("DELETE FROM sessions WHERE token = ?", (token,))
        
        db.execute('''
            INSERT INTO user_activity_logs (
                user_id, action, resource_type, details, ip_address, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            g.user_id,
            'logout',
            'auth',
            'User logout',
            get_client_ip(),
            datetime.now().isoformat()
        ))
        
        logger.info(f"✓ User {g.user_id} logged out")
        
        return jsonify({'success': True, 'message': 'Logged out successfully'}), 200
    
    except Exception as e:
        logger.error(f"✗ Logout failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get user profile with account status"""
    try:
        user = db.fetchone("SELECT * FROM users WHERE id = ?", (g.user_id,))
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get account status
        status = AccountLifetimeManager.get_account_status(db, g.user_id)
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'web_username': user['web_username'],
                'vps_email': user['vps_email'],
                'real_email': user['real_email'],
                'display_name': user.get('display_name') or user['web_username'],
                'is_admin': bool(user.get('is_admin', 0))
            },
            'account_status': status
        }), 200
    
    except Exception as e:
        logger.error(f"✗ Failed to get profile: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/profile', methods=['PUT'])
@require_auth
def update_profile():
    """Update user profile"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        updates = {}
        
        if 'display_name' in data:
            updates['display_name'] = data['display_name'][:100]
        if 'bio' in data:
            updates['bio'] = data['bio'][:500]
        if 'timezone' in data:
            updates['timezone'] = data['timezone']
        
        if updates:
            set_clause = ",".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [g.user_id]
            
            db.execute(
                f"UPDATE users SET {set_clause} WHERE id = ?",
                values
            )
            
            logger.info(f"✓ Profile updated for {g.user_id}")
        
        return jsonify({'success': True, 'message': 'Profile updated'}), 200
    
    except Exception as e:
        logger.error(f"✗ Failed to update profile: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/account-status', methods=['GET'])
@require_auth
def get_account_status():
    """Get detailed account status including lifetime and VM quota"""
    try:
        status = AccountLifetimeManager.get_account_status(db, g.user_id)
        
        if not status:
            return jsonify({'success': False, 'error': 'Account not found'}), 404
        
        return jsonify({
            'success': True,
            'account_status': status
        }), 200
    
    except Exception as e:
        logger.error(f"✗ Failed to get account status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
