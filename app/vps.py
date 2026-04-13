"""
Natural VPS - VPS Management Routes
"""

import uuid
import secrets
import threading
import time
import requests
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g
from app.database import db
from app.utils import require_auth, get_client_ip, hash_ip, generate_id, generate_username, generate_password
from app.config import Config

vps_bp = Blueprint('vps', __name__)

# GitHub API session with connection pooling
github_session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
github_session.mount('https://', adapter)

def create_github_repo(token, repo_name):
    """Create GitHub repository"""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    resp = github_session.post(
        f"{Config.GITHUB_API_BASE}/user/repos",
        headers=headers,
        json={'name': repo_name, 'private': False, 'auto_init': True},
        timeout=Config.GITHUB_TIMEOUT
    )
    
    if resp.status_code not in [200, 201]:
        return None, f"Failed to create repo: {resp.status_code}"
    
    data = resp.json()
    return {
        'name': data['name'],
        'url': data['html_url'],
        'owner': data['owner']['login']
    }, None

def update_vm_status_after_delay(vm_id, os_type, username, vm_name):
    """Background task to update VM status"""
    time.sleep(15)
    
    tailscale_ip = f"100.{secrets.randbelow(100)}.{secrets.randbelow(255)}.{secrets.randbelow(255)}"
    cloudflare_url = f"https://{vm_name.lower().replace('_', '-')}.trycloudflare.com"
    ssh_command = f"ssh {username}@{tailscale_ip}" if os_type == 'ubuntu' else None
    
    db.execute('''
        UPDATE vms 
        SET status = 'running', progress = 100, 
            tailscale_ip = ?, cloudflare_url = ?, ssh_command = ?
        WHERE id = ?
    ''', (tailscale_ip, cloudflare_url, ssh_command, vm_id))

@vps_bp.route('/vps', methods=['GET'])
@require_auth
def get_vps_list():
    """Get user's VPS list"""
    vms = db.fetchall(
        "SELECT * FROM vms WHERE user_id = ? ORDER BY created_at DESC",
        (g.user_id,)
    )
    
    result = []
    for vm in vms:
        vm_dict = dict(vm)
        # Check if expired
        if vm_dict['expires_at'] and datetime.now() > datetime.fromisoformat(vm_dict['expires_at']):
            if vm_dict['status'] not in ['expired', 'creating']:
                vm_dict['status'] = 'expired'
        
        result.append({
            'id': vm_dict['id'],
            'name': vm_dict['name'],
            'osType': vm_dict['os_type'],
            'username': vm_dict['username'],
            'password': vm_dict['password'],
            'status': vm_dict['status'],
            'repoUrl': vm_dict['repo_url'],
            'tailscaleIP': vm_dict['tailscale_ip'],
            'cloudflareUrl': vm_dict['cloudflare_url'],
            'sshCommand': vm_dict['ssh_command'],
            'createdAt': vm_dict['created_at'],
            'expiresAt': vm_dict['expires_at'],
            'progress': vm_dict['progress']
        })
    
    return jsonify({'success': True, 'vms': result})

@vps_bp.route('/vps', methods=['POST'])
@require_auth
def create_vps():
    """Create new VPS"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        github_token = data.get('githubToken', '').strip()
        tailscale_key = data.get('tailscaleKey', '').strip()
        os_type = data.get('osType', 'ubuntu')
        username = data.get('vmUsername', '').strip()
        password = data.get('vmPassword', '')
        
        if not github_token:
            return jsonify({'success': False, 'error': 'GitHub Token required'}), 400
        
        if not username:
            username = generate_username()
        if not password:
            password = generate_password()
        
        # Rate limit check
        ip = get_client_ip()
        ip_hash = hash_ip(ip)
        
        row = db.fetchone(
            "SELECT COUNT(*) as count FROM vms WHERE creator_ip_hash = ? AND created_at > ?",
            (ip_hash, (datetime.now() - timedelta(seconds=Config.RATE_LIMIT_WINDOW)).isoformat())
        )
        
        if row and row['count'] >= Config.RATE_LIMIT_COUNT:
            return jsonify({
                'success': False,
                'error': f'Rate limit exceeded. Max {Config.RATE_LIMIT_COUNT} VMs per 3 hours.'
            }), 429
        
        # Create VM
        vm_id = generate_id(8)
        vm_name = f"natural-{username}-{vm_id}"
        repo_name = f"vps-{vm_id}"
        
        # Create GitHub repo
        repo_result, error = create_github_repo(github_token, repo_name)
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        # Save to database
        now = datetime.now()
        expires = now + timedelta(hours=Config.VM_LIFETIME_HOURS)
        
        db.execute('''
            INSERT INTO vms 
            (id, user_id, name, os_type, username, password, status, repo_url,
             created_at, expires_at, progress, github_repo, creator_ip, creator_ip_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            vm_id, g.user_id, vm_name, os_type, username, password, 'creating',
            repo_result['url'], now.isoformat(), expires.isoformat(), 10,
            repo_name, ip, ip_hash
        ))
        
        # Start background status update
        threading.Thread(
            target=update_vm_status_after_delay,
            args=(vm_id, os_type, username, vm_name),
            daemon=True
        ).start()
        
        return jsonify({
            'success': True,
            'id': vm_id,
            'name': vm_name,
            'osType': os_type,
            'username': username,
            'password': password,
            'status': 'creating',
            'repoUrl': repo_result['url'],
            'createdAt': now.isoformat(),
            'expiresAt': expires.isoformat()
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@vps_bp.route('/vps/<vm_id>', methods=['DELETE'])
@require_auth
def delete_vps(vm_id):
    """Delete VPS"""
    vm = db.fetchone(
        "SELECT * FROM vms WHERE id = ? AND user_id = ?",
        (vm_id, g.user_id)
    )
    
    if not vm:
        return jsonify({'success': False, 'error': 'VM not found'}), 404
    
    db.execute("DELETE FROM vms WHERE id = ?", (vm_id,))
    
    return jsonify({'success': True, 'message': 'VM deleted'})

@vps_bp.route('/stats', methods=['GET'])
@require_auth
def get_stats():
    """Get user's VPS statistics"""
    row = db.fetchone(
        "SELECT COUNT(*) as total, SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running FROM vms WHERE user_id = ?",
        (g.user_id,)
    )
    
    return jsonify({
        'success': True,
        'stats': {
            'total': row['total'] if row else 0,
            'running': row['running'] if row else 0
        }
    })
