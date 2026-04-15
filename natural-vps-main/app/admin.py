"""
Natural VPS - Admin Management System
Professional admin panel with user management, analytics, and controls
"""

from flask import Blueprint, jsonify, request, g
from datetime import datetime, timedelta
from app.database import db
from app.utils import hash_password, verify_password, generate_tokens, hash_ip
from app.decorators import require_auth
import uuid

admin_bp = Blueprint('admin', __name__)

# Admin users (can be extended to database)
ADMIN_USERS = {
    'superdzan': {
        'email': 'thienantran1268@gmail.com',
        'password_hash': None,  # Will be set on init
        'created_at': datetime.now().isoformat(),
        'permissions': ['all']
    }
}

def init_admin_user():
    """Initialize admin user on startup"""
    # Hash the admin password
    admin_pass = hash_password('ThienAn_88')
    ADMIN_USERS['superdzan']['password_hash'] = admin_pass

@admin_bp.route('/login', methods=['POST'])
def admin_login():
    """Admin login endpoint"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'}), 400
        
        # Check admin credentials
        if username not in ADMIN_USERS:
            return jsonify({'success': False, 'error': 'Invalid admin credentials'}), 401
        
        admin_user = ADMIN_USERS[username]
        if not verify_password(password, admin_user['password_hash']):
            return jsonify({'success': False, 'error': 'Invalid admin credentials'}), 401
        
        # Generate admin token with extended expiration
        access_token, refresh_token = generate_tokens(f"admin_{username}")
        
        return jsonify({
            'success': True,
            'message': 'Admin login successful',
            'admin': {
                'username': username,
                'email': admin_user['email'],
                'role': 'admin'
            },
            'token': access_token
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/dashboard', methods=['GET'])
@require_auth
def admin_dashboard():
    """Admin dashboard overview"""
    try:
        # Check if user is admin
        if not g.user_id.startswith('admin_'):
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Get statistics
        users_count = db.fetchone("SELECT COUNT(*) as count FROM users")
        vms_count = db.fetchone("SELECT COUNT(*) as count FROM vms")
        
        running_vms = db.fetchone(
            "SELECT COUNT(*) as count FROM vms WHERE status = 'running'"
        )
        
        creating_vms = db.fetchone(
            "SELECT COUNT(*) as count FROM vms WHERE status = 'creating'"
        )
        
        failed_vms = db.fetchone(
            "SELECT COUNT(*) as count FROM vms WHERE status = 'failed'"
        )
        
        # Get recent suspicious activities
        recent_blocks = db.fetchall(
            """SELECT ip_hash, reason, added_at FROM ip_blacklist 
               ORDER BY added_at DESC LIMIT 10"""
        )
        
        # Get requests statistics
        requests_1h = db.fetchone(
            """SELECT COUNT(*) as count FROM request_logs 
               WHERE timestamp > datetime('now', '-1 hour')"""
        )
        
        return jsonify({
            'success': True,
            'dashboard': {
                'users': {
                    'total': users_count['count'],
                    'active': users_count['count']  # Could be refined
                },
                'vms': {
                    'total': vms_count['count'],
                    'running': running_vms['count'],
                    'creating': creating_vms['count'],
                    'failed': failed_vms['count']
                },
                'activity': {
                    'requests_1h': requests_1h['count'],
                    'recent_blocks': len(recent_blocks),
                    'threats_blocked': len(recent_blocks)
                },
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/users', methods=['GET'])
@require_auth
def get_all_users():
    """Get all users list"""
    try:
        if not g.user_id.startswith('admin_'):
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        offset = (page - 1) * per_page
        
        users = db.fetchall(
            """SELECT id, username, email, created_at, last_login 
               FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (per_page, offset)
        )
        
        total_count = db.fetchone("SELECT COUNT(*) as count FROM users")
        
        return jsonify({
            'success': True,
            'users': [dict(u) for u in users],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count['count']
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/user/<user_id>/suspend', methods=['POST'])
@require_auth
def suspend_user(user_id):
    """Suspend a user account"""
    try:
        if not g.user_id.startswith('admin_'):
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        reason = data.get('reason', 'Admin suspension')
        
        db.execute(
            "UPDATE users SET is_active = 0 WHERE id = ?",
            (user_id,)
        )
        
        db.execute(
            """INSERT INTO admin_actions (admin_id, action, target_id, details, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (g.user_id, 'user_suspend', user_id, reason, datetime.now().isoformat())
        )
        
        return jsonify({'success': True, 'message': f'User {user_id} suspended'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/user/<user_id>/unsuspend', methods=['POST'])
@require_auth
def unsuspend_user(user_id):
    """Unsuspend a user account"""
    try:
        if not g.user_id.startswith('admin_'):
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        db.execute(
            "UPDATE users SET is_active = 1 WHERE id = ?",
            (user_id,)
        )
        
        db.execute(
            """INSERT INTO admin_actions (admin_id, action, target_id, timestamp)
               VALUES (?, ?, ?, ?)""",
            (g.user_id, 'user_unsuspend', user_id, datetime.now().isoformat())
        )
        
        return jsonify({'success': True, 'message': f'User {user_id} unsuspended'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/vms', methods=['GET'])
@require_auth
def get_all_vms():
    """Get all VMs"""
    try:
        if not g.user_id.startswith('admin_'):
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        offset = (page - 1) * per_page
        
        if status:
            vms = db.fetchall(
                """SELECT * FROM vms WHERE status = ? 
                   ORDER BY created_at DESC LIMIT ? OFFSET ?""",
                (status, per_page, offset)
            )
        else:
            vms = db.fetchall(
                """SELECT * FROM vms ORDER BY created_at DESC LIMIT ? OFFSET ?""",
                (per_page, offset)
            )
        
        return jsonify({
            'success': True,
            'vms': [dict(vm) for vm in vms],
            'pagination': {'page': page, 'per_page': per_page}
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/spam-stats', methods=['GET'])
@require_auth
def get_spam_stats():
    """Get spam detection statistics"""
    try:
        if not g.user_id.startswith('admin_'):
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Get spam attempts in last 24 hours
        spam_attempts = db.fetchall(
            """SELECT ip_hash, username, success, timestamp FROM login_attempts 
               WHERE success = 0 AND timestamp > datetime('now', '-1 day')
               ORDER BY timestamp DESC LIMIT 100"""
        )
        
        # Get registration rate
        registrations_24h = db.fetchone(
            "SELECT COUNT(*) as count FROM users WHERE created_at > datetime('now', '-1 day')"
        )
        
        # Get VM creation rate
        vms_24h = db.fetchone(
            "SELECT COUNT(*) as count FROM vms WHERE created_at > datetime('now', '-1 day')"
        )
        
        return jsonify({
            'success': True,
            'spam_stats': {
                'failed_logins_24h': len(spam_attempts),
                'registrations_24h': registrations_24h['count'],
                'vms_created_24h': vms_24h['count'],
                'recent_spam_attempts': [dict(s) for s in spam_attempts]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/threats', methods=['GET'])
@require_auth
def get_threats():
    """Get active threats and blocked IPs"""
    try:
        if not g.user_id.startswith('admin_'):
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Get blocked IPs
        blocked = db.fetchall(
            """SELECT ip, reason, added_at, expires_at FROM ip_blacklist 
               ORDER BY added_at DESC LIMIT 100"""
        )
        
        # Get suspicious IPs
        suspicious = db.fetchall(
            """SELECT ip, method, path, status_code, COUNT(*) as count 
               FROM request_logs 
               WHERE timestamp > datetime('now', '-1 hour')
               AND status_code >= 400
               GROUP BY ip
               ORDER BY count DESC LIMIT 20"""
        )
        
        return jsonify({
            'success': True,
            'threats': {
                'blocked': [dict(b) for b in blocked],
                'suspicious': [dict(s) for s in suspicious]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/logs', methods=['GET'])
@require_auth  
def get_system_logs():
    """Get system activity logs"""
    try:
        if not g.user_id.startswith('admin_'):
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        log_type = request.args.get('type', 'all')
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        if log_type == 'api':
            logs = db.fetchall(
                """SELECT method, path, status_code, user_id, timestamp 
                   FROM request_logs 
                   WHERE timestamp > datetime('now', ? || ' hours')
                   ORDER BY timestamp DESC LIMIT ?""",
                (f'-{hours}', limit)
            )
        elif log_type == 'admin':
            logs = db.fetchall(
                """SELECT admin_id, action, target_id, details, timestamp 
                   FROM admin_actions 
                   ORDER BY timestamp DESC LIMIT ?""",
                (limit,)
            )
        else:
            logs = db.fetchall(
                """SELECT * FROM request_logs 
                   WHERE timestamp > datetime('now', ? || ' hours')
                   ORDER BY timestamp DESC LIMIT ?""",
                (f'-{hours}', limit)
            )
        
        return jsonify({
            'success': True,
            'logs': [dict(log) for log in logs],
            'type': log_type,
            'hours': hours
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/config', methods=['GET'])
@require_auth
def get_configuration():
    """Get system configuration"""
    try:
        if not g.user_id.startswith('admin_'):
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        from app.config import Config
        
        return jsonify({
            'success': True,
            'config': {
                'rate_limit_count': Config.RATE_LIMIT_COUNT,
                'rate_limit_window': Config.RATE_LIMIT_WINDOW,
                'login_rate_limit': Config.LOGIN_RATE_LIMIT,
                'login_rate_window': Config.LOGIN_RATE_WINDOW,
                'vm_lifetime_hours': Config.VM_LIFETIME_HOURS,
                'cache_ttl': Config.CACHE_TTL,
                'debug': Config.DEBUG
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Initialize admin on app startup
def init_admin_system(app):
    """Initialize admin system on app startup"""
    init_admin_user()
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    print("[OK] Admin system initialized")
