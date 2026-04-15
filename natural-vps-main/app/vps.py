"""
Natural VPS - VPS Management Routes
API Endpoint: http://34.10.118.99:5000
"""

import uuid
import threading
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g
from app.database import db
from app.utils import (
    get_client_ip, hash_ip, generate_id,
    generate_username, generate_password, validate_github_token,
    retry_with_backoff
)
from app.decorators import rate_limit, require_auth
from app.health import monitor_workflow, check_workflow_status
from app.config import Config
from app.spam_detector import SpamDetector
import requests
import base64

vps_bp = Blueprint('vps', __name__)

github_session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=30, pool_maxsize=30)
github_session.mount('https://', adapter)

creation_progress = {}
progress_lock = threading.Lock()

def update_progress(vm_id, step, percent, message, status='active', error=None):
    with progress_lock:
        creation_progress[vm_id] = {
            'step': step, 'percent': percent, 'message': message,
            'status': status, 'error': error, 'updated_at': datetime.now().isoformat()
        }

def create_github_repo(token, repo_name):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'NaturalVPS/3.0'
    }
    
    try:
        resp = github_session.post(
            f"{Config.GITHUB_API_BASE}/user/repos",
            headers=headers,
            json={'name': repo_name, 'private': False, 'auto_init': True},
            timeout=Config.GITHUB_TIMEOUT
        )
        
        if resp.status_code not in [200, 201]:
            return None, f"GitHub API error: {resp.status_code}"
        
        data = resp.json()
        return {
            'name': data['name'],
            'url': data['html_url'],
            'owner': data['owner']['login']
        }, None
    except Exception as e:
        return None, str(e)

def create_workflow_file(token, owner, repo, vm_config):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'NaturalVPS/3.0'
    }
    
    workflow_content = f'''name: Natural VPS - {vm_config['name']}

on:
  workflow_dispatch:
  push:
    branches: [main, master]

jobs:
  vps:
    runs-on: ubuntu-latest
    timeout-minutes: 360
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup VPS
      run: |
        sudo apt update -qq
        sudo apt install -y curl wget openssh-server xfce4 tightvncserver novnc websockify
        
        sudo useradd -m -s /bin/bash {vm_config['username']}
        echo "{vm_config['username']}:{vm_config['password']}" | sudo chpasswd
        sudo usermod -aG sudo {vm_config['username']}
        
        sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
        sudo service ssh start
        
        curl -fsSL https://tailscale.com/install.sh | sh
        sudo tailscale up --authkey={vm_config['tailscale_key']} --hostname={vm_config['name']}
        
        sudo -u {vm_config['username']} mkdir -p ~/.vnc
        echo "{vm_config['password']}" | sudo -u {vm_config['username']} vncpasswd -f > /home/{vm_config['username']}/.vnc/passwd
        sudo -u {vm_config['username']} chmod 600 /home/{vm_config['username']}/.vnc/passwd
        sudo -u {vm_config['username']} vncserver :1 -geometry 1280x800 -depth 24
        websockify --web /usr/share/novnc 6080 localhost:5901 &
        
        curl -L https://github.com/kamipublic/KamiTunnel/releases/latest/download/kami-linux-amd64 -o kami
        chmod +x kami
        ./kami tunnel --url http://localhost:6080 > /tmp/kami.log 2>&1 &
        sleep 8
        
        KAMI_URL=$(grep -o "https://[a-z0-9.-]*\\.kami\\.dev" /tmp/kami.log | head -1)
        TAILSCALE_IP=$(tailscale ip -4)
        echo "KAMI_URL=$KAMI_URL" >> /tmp/vm_info
        echo "TAILSCALE_IP=$TAILSCALE_IP" >> /tmp/vm_info
        
    - name: Keep Alive
      run: |
        for i in $(seq 1 360); do sleep 60; done
'''
    
    content_b64 = base64.b64encode(workflow_content.encode()).decode()
    path = '.github/workflows/natural-vps.yml'
    
    try:
        check_url = f"{Config.GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}"
        check_resp = github_session.get(check_url, headers=headers)
        
        data = {'message': 'Create workflow', 'content': content_b64}
        if check_resp.status_code == 200:
            data['sha'] = check_resp.json()['sha']
        
        resp = github_session.put(check_url, headers=headers, json=data, timeout=Config.GITHUB_TIMEOUT)
        
        if resp.status_code not in [200, 201]:
            return None, f"Workflow creation failed: {resp.status_code}"
        
        return f"https://github.com/{owner}/{repo}/actions", None
    except Exception as e:
        return None, str(e)

def trigger_workflow(token, owner, repo):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'NaturalVPS/3.0'
    }
    
    try:
        url = f"{Config.GITHUB_API_BASE}/repos/{owner}/{repo}/actions/workflows"
        resp = github_session.get(url, headers=headers, timeout=Config.GITHUB_TIMEOUT)
        
        if resp.status_code != 200:
            return False
        
        workflows = resp.json().get('workflows', [])
        if not workflows:
            return False
        
        workflow_id = workflows[0]['id']
        trigger_url = f"{Config.GITHUB_API_BASE}/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches"
        resp = github_session.post(trigger_url, headers=headers, json={'ref': 'main'}, timeout=Config.GITHUB_TIMEOUT)
        
        return resp.status_code in [200, 204]
    except:
        return False

def background_create_vm(vm_id, github_token, tailscale_key, os_type, username, password, user_id, creator_ip):
    try:
        update_progress(vm_id, 0, 5, 'Validating GitHub token...')
        valid, result = validate_github_token(github_token)
        if not valid:
            update_progress(vm_id, 0, 0, f'Failed: {result}', 'failed', result)
            db.execute("UPDATE vms SET status = 'failed', error_message = ? WHERE id = ?", (result, vm_id))
            return
        
        github_user = result['username']
        update_progress(vm_id, 0, 15, f'Token valid (User: {github_user})', 'completed')
        
        update_progress(vm_id, 1, 25, 'Creating GitHub repository...')
        repo_name = f"natural-vps-{generate_id(8)}"
        repo_result, error = retry_with_backoff(lambda: create_github_repo(github_token, repo_name))
        
        if error:
            update_progress(vm_id, 1, 25, f'Failed: {error}', 'failed', error)
            db.execute("UPDATE vms SET status = 'failed', error_message = ? WHERE id = ?", (error, vm_id))
            return
        
        db.execute("UPDATE vms SET repo_url = ?, github_repo = ?, github_user = ? WHERE id = ?",
                   (repo_result['url'], repo_name, github_user, vm_id))
        update_progress(vm_id, 1, 40, 'Repository created', 'completed')
        
        update_progress(vm_id, 2, 55, 'Generating workflow...')
        vm_name = f"natural-{username}-{vm_id[:6]}"
        vm_config = {'name': vm_name, 'os_type': os_type, 'username': username, 'password': password, 'tailscale_key': tailscale_key}
        
        workflow_url, error = create_workflow_file(github_token, repo_result['owner'], repo_name, vm_config)
        if error:
            update_progress(vm_id, 2, 55, f'Failed: {error}', 'failed', error)
            db.execute("UPDATE vms SET status = 'failed', error_message = ? WHERE id = ?", (error, vm_id))
            return
        
        db.execute("UPDATE vms SET workflow_url = ?, name = ? WHERE id = ?", (workflow_url, vm_name, vm_id))
        update_progress(vm_id, 2, 70, 'Workflow created', 'completed')
        
        update_progress(vm_id, 3, 80, 'Triggering workflow...')
        trigger_workflow(github_token, repo_result['owner'], repo_name)
        update_progress(vm_id, 3, 85, 'Workflow triggered', 'completed')
        
        update_progress(vm_id, 4, 90, 'Waiting for VM to boot...')
        
        threading.Thread(target=monitor_workflow, args=(vm_id, github_token, repo_result['owner'], repo_name), daemon=True).start()
        
    except Exception as e:
        update_progress(vm_id, 0, 0, f'Error: {str(e)}', 'failed', str(e))
        db.execute("UPDATE vms SET status = 'failed', error_message = ? WHERE id = ?", (str(e), vm_id))

@vps_bp.route('/vps', methods=['GET'])
@require_auth
def get_vps_list():
    vms = db.fetchall("SELECT * FROM vms WHERE user_id = ? ORDER BY created_at DESC", (g.user_id,))
    result = []
    for vm in vms:
        vm_dict = dict(vm)
        if vm_dict['expires_at'] and datetime.now() > datetime.fromisoformat(vm_dict['expires_at']):
            if vm_dict['status'] not in ['expired', 'failed']:
                vm_dict['status'] = 'expired'
        
        result.append({
            'id': vm_dict['id'], 'name': vm_dict['name'], 'osType': vm_dict['os_type'],
            'username': vm_dict['username'], 'password': vm_dict['password'],
            'status': vm_dict['status'], 'repoUrl': vm_dict['repo_url'],
            'tailscaleIP': vm_dict['tailscale_ip'], 'kamiUrl': vm_dict['kami_url'],
            'kamiIP': vm_dict['kami_ip'], 'kamiPort': vm_dict['kami_port'],
            'sshCommand': vm_dict['ssh_command'], 'createdAt': vm_dict['created_at'],
            'expiresAt': vm_dict['expires_at'], 'progress': vm_dict['progress'],
            'errorMessage': vm_dict['error_message']
        })
    return jsonify({'success': True, 'vms': result})

@vps_bp.route('/vps', methods=['POST'])
@require_auth
@rate_limit
def create_vps():
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
        if not tailscale_key:
            return jsonify({'success': False, 'error': 'Tailscale Key required'}), 400
        
        if not username:
            username = generate_username()
        if not password:
            password = generate_password()
        
        ip = get_client_ip()
        
        # Check for VM creation spam
        is_spam, spam_reason = SpamDetector.check_vm_creation_spam(g.user_id, ip)
        if is_spam:
            return jsonify({'success': False, 'error': f'VM creation blocked: {spam_reason}'}), 429
        
        ip_hash = hash_ip(ip)
        
        row = db.fetchone(
            "SELECT COUNT(*) as count FROM vms WHERE creator_ip_hash = ? AND created_at > ?",
            (ip_hash, (datetime.now() - timedelta(seconds=Config.RATE_LIMIT_WINDOW)).isoformat())
        )
        
        if row and row['count'] >= Config.RATE_LIMIT_COUNT:
            return jsonify({'success': False, 'error': f'Rate limit exceeded. Max {Config.RATE_LIMIT_COUNT} VMs per 3 hours.'}), 429
        
        vm_id = str(uuid.uuid4())
        vm_name = f"natural-{username}-{vm_id[:6]}"
        now = datetime.now()
        expires = now + timedelta(hours=Config.VM_LIFETIME_HOURS)
        
        db.execute('''
            INSERT INTO vms (id, user_id, name, os_type, username, password, status,
             created_at, expires_at, progress, creator_ip, creator_ip_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (vm_id, g.user_id, vm_name, os_type, username, password, 'creating',
              now.isoformat(), expires.isoformat(), 5, ip, ip_hash))
        
        update_progress(vm_id, 0, 5, 'Starting VM creation...')
        
        threading.Thread(target=background_create_vm,
                         args=(vm_id, github_token, tailscale_key, os_type, username, password, g.user_id, ip),
                         daemon=True).start()
        
        return jsonify({
            'success': True, 'id': vm_id, 'name': vm_name, 'osType': os_type,
            'username': username, 'password': password, 'status': 'creating',
            'createdAt': now.isoformat(), 'expiresAt': expires.isoformat(), 'progress': 5
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@vps_bp.route('/vps/<vm_id>/progress', methods=['GET'])
@require_auth
def get_vm_progress(vm_id):
    vm = db.fetchone("SELECT * FROM vms WHERE id = ? AND user_id = ?", (vm_id, g.user_id))
    if not vm:
        return jsonify({'success': False, 'error': 'VM not found'}), 404
    
    progress = creation_progress.get(vm_id, {
        'step': 0, 'percent': vm['progress'], 'message': 'Processing...',
        'status': 'active', 'error': None
    })
    
    return jsonify({'success': True, 'progress': progress, 'vm': {'id': vm['id'], 'name': vm['name'], 'status': vm['status'], 'progress': vm['progress']}})

@vps_bp.route('/vps/<vm_id>', methods=['DELETE'])
@require_auth
def delete_vps(vm_id):
    vm = db.fetchone("SELECT * FROM vms WHERE id = ? AND user_id = ?", (vm_id, g.user_id))
    if not vm:
        return jsonify({'success': False, 'error': 'VM not found'}), 404
    
    db.execute("DELETE FROM vms WHERE id = ?", (vm_id,))
    if vm_id in creation_progress:
        del creation_progress[vm_id]
    
    return jsonify({'success': True, 'message': 'VM deleted'})

@vps_bp.route('/stats', methods=['GET'])
@require_auth
def get_stats():
    row = db.fetchone(
        """SELECT COUNT(*) as total, SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running,
           SUM(CASE WHEN status = 'creating' THEN 1 ELSE 0 END) as creating,
           SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
        FROM vms WHERE user_id = ?""",
        (g.user_id,)
    )
    
    return jsonify({'success': True, 'stats': {
        'total': row['total'] if row else 0,
        'running': row['running'] if row else 0,
        'creating': row['creating'] if row else 0,
        'failed': row['failed'] if row else 0
    }})

@vps_bp.route('/rate-limit', methods=['GET'])
@require_auth
def get_rate_limit_status():
    """Lấy trạng thái rate limit của user hiện tại"""
    ip = get_client_ip()
    ip_hash = hash_ip(ip)
    
    row = db.fetchone(
        "SELECT count, window_start FROM rate_limits WHERE ip_hash = ?",
        (ip_hash,)
    )
    
    limit = Config.RATE_LIMIT_COUNT
    window_hours = Config.RATE_LIMIT_WINDOW // 3600
    
    if not row:
        return jsonify({
            'success': True,
            'rate_limit': {
                'used': 0,
                'limit': limit,
                'remaining': limit,
                'window_hours': window_hours,
                'reset_at': None,
                'seconds_remaining': 0
            }
        })
    
    used = row['count']
    remaining = max(0, limit - used)
    reset_at = row['window_start']
    
    seconds_remaining = 0
    if reset_at:
        reset_time = datetime.fromisoformat(reset_at) + timedelta(seconds=Config.RATE_LIMIT_WINDOW)
        now = datetime.now()
        if now < reset_time:
            seconds_remaining = (reset_time - now).seconds
        else:
            remaining = limit
            used = 0
    
    return jsonify({
        'success': True,
        'rate_limit': {
            'used': used,
            'limit': limit,
            'remaining': remaining,
            'window_hours': window_hours,
            'reset_at': reset_at,
            'seconds_remaining': seconds_remaining
        }
    })
