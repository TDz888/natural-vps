"""
Admin Management Panel API - v5
Handles admin account creation, user management, VM management
"""

import uuid
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g
from app.database import db
from app.utils import get_client_ip, generate_id, hash_password, generate_tokens
from app.decorators import require_auth
from app.config import Config
from app.account_lifetime_manager import AccountLifetimeManager
from app.email_service import EmailService
import json
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin_v5', __name__)


def check_admin(user_id):
    """Check if user is admin"""
    user = db.fetchone("SELECT is_admin FROM users WHERE id = ?", (user_id,))
    return user and user['is_admin']


@admin_bp.before_request
@require_auth
def admin_auth():
    """Check admin privileges before each request"""
    if not check_admin(g.user_id):
        return jsonify({'success': False, 'error': 'Admin access required'}), 403


@admin_bp.route('/users', methods=['GET'])
def list_users():
    """List all users with their status"""
    try:
        users = db.fetch_all('''
            SELECT id, web_username, vps_email, real_email, 
                   account_created_at, account_expires_at, 
                   is_active, is_admin, is_unlimited, vm_quota,
                   (SELECT COUNT(*) FROM vms WHERE user_id = users.id AND status != 'deleted') as vm_count
            FROM users
            ORDER BY created_at DESC
        ''')
        
        user_list = []
        for user in users:
            status = AccountLifetimeManager.get_account_status(db, user['id'])
            user_list.append({
                'id': user['id'],
                'username': user['web_username'],
                'email': user['vps_email'],
                'real_email': user['real_email'],
                'is_active': bool(user['is_active']),
                'is_admin': bool(user['is_admin']),
                'is_unlimited': bool(user['is_unlimited']),
                'vm_count': user['vm_count'],
                'vm_quota': user['vm_quota'],
                'account_status': status
            })
        
        return jsonify({
            'success': True,
            'users': user_list,
            'total': len(user_list)
        }), 200
    
    except Exception as e:
        logger.error(f"✗ Failed to list users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get specific user details"""
    try:
        user = db.fetchone('''
            SELECT * FROM users WHERE id = ?
        ''', (user_id,))
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        status = AccountLifetimeManager.get_account_status(db, user_id)
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['web_username'],
                'email': user['vps_email'],
                'real_email': user['real_email'],
                'is_active': bool(user['is_active']),
                'is_admin': bool(user['is_admin']),
                'is_unlimited': bool(user['is_unlimited']),
                'created_at': user['created_at'],
                'last_login': user['last_login']
            },
            'account_status': status
        }), 200
    
    except Exception as e:
        logger.error(f"✗ Failed to get user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users/create', methods=['POST'])
def create_user_account():
    """
    Admin creates account for user
    
    Request JSON:
    {
        "real_email": "user@example.com",
        "lifetime_hours": 3,  # 3, 5, or null for lifetime
        "is_admin": false,
        "is_unlimited": false
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        real_email = data.get('real_email', '').strip()
        lifetime_hours = data.get('lifetime_hours', Config.ACCOUNT_LIFETIME_HOURS)
        is_admin = data.get('is_admin', False)
        is_unlimited = data.get('is_unlimited', False)
        client_ip = get_client_ip()
        
        # Validate email
        if not real_email:
            return jsonify({'success': False, 'error': 'Real email is required'}), 400
        
        is_valid, error = EmailService.validate_real_email(real_email)
        if not is_valid:
            return jsonify({'success': False, 'error': f'Invalid email: {error}'}), 400
        
        # Check if email already exists
        existing = db.fetchone(
            "SELECT id FROM users WHERE real_email = ? AND is_active = 1",
            (real_email,)
        )
        if existing:
            return jsonify({'success': False, 'error': 'Email already registered'}), 400
        
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
        
        # Create user
        user_id = str(uuid.uuid4())
        password_hash = hash_password(web_password)
        api_key = f"nv_{generate_id(16)}"
        
        now = datetime.now()
        
        # Calculate expiration
        if lifetime_hours == float('inf') or lifetime_hours is None:
            expires_at = None
            lifetime = float('inf')
        else:
            expires_at = now + timedelta(hours=lifetime_hours)
            lifetime = lifetime_hours
        
        db.execute('''
            INSERT INTO users (
                id, username, vps_email, real_email, web_username,
                email, password_hash, created_at, api_key,
                account_created_at, account_expires_at, account_lifetime_hours,
                is_active, is_admin, is_unlimited, vm_quota,
                admin_created_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, web_username, vps_email, real_email, web_username,
            vps_email, password_hash, now.isoformat(), api_key,
            now.isoformat(),
            expires_at.isoformat() if expires_at else None,
            lifetime if lifetime != float('inf') else None,
            1, 1 if is_admin else 0, 1 if (is_admin or is_unlimited) else 0,
            None if (is_admin or is_unlimited) else Config.USER_VM_QUOTA,
            g.user_id
        ))
        
        # Log admin action
        db.execute('''
            INSERT INTO admin_actions (
                admin_id, action, target_user_id, details, ip_address, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            g.user_id,
            'create_account',
            user_id,
            f'Created account for {real_email}',
            client_ip,
            now.isoformat()
        ))
        
        logger.info(f"✓ Admin {g.user_id} created account for {real_email}")
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'user': {
                'id': user_id,
                'username': web_username,
                'vps_email': vps_email,
                'real_email': real_email,
                'password': web_password,
                'api_key': api_key,
                'is_admin': is_admin,
                'is_unlimited': is_unlimited
            },
            'lifetime': {
                'hours': lifetime if lifetime != float('inf') else 'unlimited',
                'expires_at': expires_at.isoformat() if expires_at else None
            }
        }), 201
    
    except Exception as e:
        logger.error(f"✗ Failed to create user account: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users/<user_id>/extend-lifetime', methods=['POST'])
def extend_user_lifetime(user_id):
    """
    Extend user account lifetime
    
    Request JSON:
    {
        "additional_hours": 5,
        "make_unlimited": false
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        additional_hours = data.get('additional_hours')
        make_unlimited = data.get('make_unlimited', False)
        
        user = db.fetchone("SELECT account_expires_at FROM users WHERE id = ?", (user_id,))
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        now = datetime.now()
        
        if make_unlimited:
            db.execute(
                "UPDATE users SET account_expires_at = NULL, is_unlimited = 1 WHERE id = ?",
                (user_id,)
            )
            new_expires = None
        else:
            if additional_hours:
                if user['account_expires_at']:
                    expires_dt = datetime.fromisoformat(user['account_expires_at'])
                    new_expires = expires_dt + timedelta(hours=additional_hours)
                else:
                    new_expires = now + timedelta(hours=additional_hours)
                
                db.execute(
                    "UPDATE users SET account_expires_at = ? WHERE id = ?",
                    (new_expires.isoformat(), user_id)
                )
            else:
                return jsonify({'success': False, 'error': 'Additional hours or make_unlimited required'}), 400
        
        # Log admin action
        db.execute('''
            INSERT INTO admin_actions (
                admin_id, action, target_user_id, details, ip_address, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            g.user_id,
            'extend_lifetime',
            user_id,
            f'Extended lifetime by {additional_hours}h' if additional_hours else 'Made unlimited',
            get_client_ip(),
            now.isoformat()
        ))
        
        logger.info(f"✓ Admin {g.user_id} extended lifetime for {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Account lifetime extended',
            'expires_at': new_expires.isoformat() if new_expires else None
        }), 200
    
    except Exception as e:
        logger.error(f"✗ Failed to extend lifetime: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users/<user_id>/suspend', methods=['POST'])
def suspend_user(user_id):
    """Suspend user account"""
    try:
        db.execute(
            "UPDATE users SET is_active = 0 WHERE id = ?",
            (user_id,)
        )
        
        # Log admin action
        db.execute('''
            INSERT INTO admin_actions (
                admin_id, action, target_user_id, details, ip_address, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            g.user_id, 'suspend_user', user_id,
            'User suspended',
            get_client_ip(),
            datetime.now().isoformat()
        ))
        
        logger.info(f"✓ Admin {g.user_id} suspended user {user_id}")
        
        return jsonify({'success': True, 'message': 'User suspended'}), 200
    
    except Exception as e:
        logger.error(f"✗ Failed to suspend user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users/<user_id>/activate', methods=['POST'])
def activate_user(user_id):
    """Activate suspended user"""
    try:
        db.execute(
            "UPDATE users SET is_active = 1 WHERE id = ?",
            (user_id,)
        )
        
        # Log admin action
        db.execute('''
            INSERT INTO admin_actions (
                admin_id, action, target_user_id, details, ip_address, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            g.user_id, 'activate_user', user_id,
            'User activated',
            get_client_ip(),
            datetime.now().isoformat()
        ))
        
        logger.info(f"✓ Admin {g.user_id} activated user {user_id}")
        
        return jsonify({'success': True, 'message': 'User activated'}), 200
    
    except Exception as e:
        logger.error(f"✗ Failed to activate user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/vms', methods=['GET'])
def list_all_vms():
    """List all VMs"""
    try:
        vms = db.fetch_all('''
            SELECT id, user_id, name, status, os_type, 
                   created_at, expires_at, vm_lifetime_hours
            FROM vms
            WHERE status != 'deleted'
            ORDER BY created_at DESC
        ''')
        
        return jsonify({
            'success': True,
            'vms': [dict(vm) for vm in vms],
            'total': len(vms)
        }), 200
    
    except Exception as e:
        logger.error(f"✗ Failed to list VMs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/vms/<vm_id>/update-lifetime', methods=['POST'])
def update_vm_lifetime(vm_id):
    """Update VM lifetime"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        lifetime_hours = data.get('lifetime_hours')
        if not lifetime_hours:
            return jsonify({'success': False, 'error': 'Lifetime hours required'}), 400
        
        vm = db.fetchone("SELECT user_id FROM vms WHERE id = ?", (vm_id,))
        if not vm:
            return jsonify({'success': False, 'error': 'VM not found'}), 404
        
        AccountLifetimeManager.update_vm_lifetime(
            db, vm_id, lifetime_hours,
            created_by_admin=True,
            admin_id=g.user_id
        )
        
        # Log admin action
        db.execute('''
            INSERT INTO admin_actions (
                admin_id, action, target_vm_id, details, ip_address, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            g.user_id, 'update_vm_lifetime', vm_id,
            f'Updated VM lifetime to {lifetime_hours}h',
            get_client_ip(),
            datetime.now().isoformat()
        ))
        
        logger.info(f"✓ Admin {g.user_id} updated VM {vm_id} lifetime")
        
        return jsonify({
            'success': True,
            'message': 'VM lifetime updated'
        }), 200
    
    except Exception as e:
        logger.error(f"✗ Failed to update VM lifetime: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/vms/<vm_id>/delete', methods=['POST'])
def delete_vm(vm_id):
    """Delete VM"""
    try:
        vm = db.fetchone("SELECT user_id FROM vms WHERE id = ?", (vm_id,))
        if not vm:
            return jsonify({'success': False, 'error': 'VM not found'}), 404
        
        AccountLifetimeManager.schedule_deletion(
            db, 'vm', vm_id, vm['user_id'],
            'Admin deletion'
        )
        
        # Log admin action
        db.execute('''
            INSERT INTO admin_actions (
                admin_id, action, target_vm_id, details, ip_address, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            g.user_id, 'delete_vm', vm_id,
            'VM scheduled for deletion',
            get_client_ip(),
            datetime.now().isoformat()
        ))
        
        logger.info(f"✓ Admin {g.user_id} deleted VM {vm_id}")
        
        return jsonify({
            'success': True,
            'message': 'VM scheduled for deletion'
        }), 200
    
    except Exception as e:
        logger.error(f"✗ Failed to delete VM: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/stats', methods=['GET'])
def admin_stats():
    """Get admin dashboard stats"""
    try:
        total_users = db.fetchone("SELECT COUNT(*) FROM users WHERE is_active = 1")[0]
        total_vms = db.fetchone("SELECT COUNT(*) FROM vms WHERE status != 'deleted'")[0]
        active_vms = db.fetchone("SELECT COUNT(*) FROM vms WHERE status = 'running'")[0]
        admin_users = db.fetchone("SELECT COUNT(*) FROM users WHERE is_admin = 1")[0]
        
        return jsonify({
            'success': True,
            'stats': {
                'total_users': total_users,
                'total_vms': total_vms,
                'active_vms': active_vms,
                'admin_users': admin_users
            }
        }), 200
    
    except Exception as e:
        logger.error(f"✗ Failed to get admin stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/audit-logs', methods=['GET'])
def get_audit_logs():
    """Get admin action audit logs"""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        logs = db.fetch_all('''
            SELECT id, admin_id, action, target_user_id, target_vm_id,
                   details, ip_address, timestamp
            FROM admin_actions
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        return jsonify({
            'success': True,
            'logs': [dict(log) for log in logs],
            'limit': limit,
            'offset': offset
        }), 200
    
    except Exception as e:
        logger.error(f"✗ Failed to get audit logs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
