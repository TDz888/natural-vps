"""
Natural VPS - Monitoring & Admin Routes
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from app.database import db
from app.security import SecurityManager, limiter, IPManager, RequestLogger
from app.decorators import require_auth
from app.config import Config
import json

monitor_bp = Blueprint('monitor', __name__)

@monitor_bp.route('/health', methods=['GET'])
def system_health():
    """Get overall system health"""
    stats = RequestLogger.get_request_stats(hours=1)
    blocked = SecurityManager.get_blocked_ips()
    suspicious = SecurityManager.get_suspicious_ips()
    
    return jsonify({
        'success': True,
        'health': {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'requests_1h': stats.get('total_requests', 0),
            'success_rate': f"{(stats.get('successful', 0) / max(stats.get('total_requests', 1), 1)) * 100:.1f}%",
            'unique_ips_1h': stats.get('unique_ips', 0),
            'blocked_ips': len(blocked),
            'suspicious_ips': len(suspicious)
        }
    })

@monitor_bp.route('/stats/security', methods=['GET'])
@require_auth
def get_security_stats():
    """Get security statistics"""
    blocked = SecurityManager.get_blocked_ips()
    suspicious = SecurityManager.get_suspicious_ips()
    
    return jsonify({
        'success': True,
        'security': {
            'blocked_ips': len(blocked),
            'suspicious_ips': len(suspicious),
            'top_suspicious_ips': list(suspicious.keys())[:10]
        }
    })

@monitor_bp.route('/stats/requests', methods=['GET'])
@require_auth
def get_request_stats():
    """Get request statistics"""
    hours = request.args.get('hours', 24, type=int)
    stats = RequestLogger.get_request_stats(hours=hours)
    
    return jsonify({
        'success': True,
        'stats': stats
    })

@monitor_bp.route('/ip/block', methods=['POST'])
@require_auth
def block_ip():
    """Block an IP address"""
    data = request.get_json()
    ip = data.get('ip')
    reason = data.get('reason', 'Manual block')
    hours = data.get('hours', 24)
    
    if not ip:
        return jsonify({'success': False, 'error': 'IP required'}), 400
    
    IPManager.add_to_blacklist(ip, reason, hours)
    return jsonify({'success': True, 'message': f'IP {ip} blocked for {hours} hours'})

@monitor_bp.route('/ip/whitelist', methods=['POST'])
@require_auth
def whitelist_ip():
    """Add IP to whitelist"""
    data = request.get_json()
    ip = data.get('ip')
    reason = data.get('reason', 'Manual whitelist')
    
    if not ip:
        return jsonify({'success': False, 'error': 'IP required'}), 400
    
    IPManager.add_to_whitelist(ip, reason)
    return jsonify({'success': True, 'message': f'IP {ip} whitelisted'})

@monitor_bp.route('/cache/clear', methods=['POST'])
@require_auth
def clear_cache():
    """Clear application cache"""
    from app.cache import invalidate_cache
    pattern = request.get_json().get('pattern')
    
    if pattern:
        invalidate_cache(pattern)
        return jsonify({'success': True, 'message': f'Cache cleared for pattern: {pattern}'})
    else:
        invalidate_cache()
        return jsonify({'success': True, 'message': 'All cache cleared'})

@monitor_bp.route('/info', methods=['GET'])
def get_app_info():
    """Get application information"""
    return jsonify({
        'success': True,
        'app': {
            'name': 'Natural VPS',
            'version': Config.VERSION,
            'environment': 'production' if not Config.DEBUG else 'development',
            'api_endpoint': f"{request.host}",
            'timestamp': datetime.now().isoformat()
        }
    })
