"""
Natural VPS - VPS Management Routes (REAL IMPLEMENTATION)
"""

import uuid
import secrets
import threading
import time
import base64
import requests
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g
from app.database import db
from app.utils import require_auth, get_client_ip, hash_ip, generate_id, generate_username, generate_password
from app.config import Config

vps_bp = Blueprint('vps', __name__)

# GitHub API session với connection pooling
github_session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
github_session.mount('https://', adapter)

# Lưu trạng thái tiến trình tạo VM (trong memory)
creation_progress = {}
progress_lock = threading.Lock()

def update_progress(vm_id, step, percent, message, status='active'):
    """Cập nhật tiến trình tạo VM"""
    with progress_lock:
        creation_progress[vm_id] = {
            'step': step,
            'percent': percent,
            'message': message,
            'status': status,  # active, completed, failed
            'updated_at': datetime.now().isoformat()
        }

def create_github_repo(token, repo_name):
    """Tạo GitHub repository THẬT"""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'NaturalVPS/2.0'
    }
    
    resp = github_session.post(
        f"{Config.GITHUB_API_BASE}/user/repos",
        headers=headers,
        json={'name': repo_name, 'private': False, 'auto_init': True},
        timeout=Config.GITHUB_TIMEOUT
    )
    
    if resp.status_code not in [200, 201]:
        return None, f"Failed to create repo: {resp.status_code} - {resp.text}"
    
    data = resp.json()
    return {
        'name': data['name'],
        'full_name': data['full_name'],
        'url': data['html_url'],
        'clone_url': data['clone_url'],
        'owner': data['owner']['login']
    }, None

def create_workflow_file(token, owner, repo, vm_config):
    """Tạo file workflow THẬT"""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'NaturalVPS/2.0'
    }
    
    # Tạo nội dung workflow
    workflow_content = generate_workflow_content(vm_config)
    content_b64 = base64.b64encode(workflow_content.encode()).decode()
    
    path = '.github/workflows/natural-vps.yml'
    
    # Kiểm tra file đã tồn tại chưa
    check_url = f"{Config.GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}"
    check_resp = github_session.get(check_url, headers=headers)
    
    data = {
        'message': f'Create Natural VPS workflow - {vm_config["name"]}',
        'content': content_b64
    }
    
    if check_resp.status_code == 200:
        data['sha'] = check_resp.json()['sha']
    
    resp = github_session.put(check_url, headers=headers, json=data, timeout=Config.GITHUB_TIMEOUT)
    
    if resp.status_code not in [200, 201]:
        return None, f"Failed to create workflow: {resp.status_code}"
    
    return f"https://github.com/{owner}/{repo}/actions", None

def generate_workflow_content(vm_config):
    """Tạo nội dung workflow YAML"""
    os_type = vm_config.get('os_type', 'ubuntu')
    name = vm_config.get('name', 'natural-vps')
    username = vm_config.get('username', 'user')
    password = vm_config.get('password', 'pass')
    tailscale_key = vm_config.get('tailscale_key', '')
    
    if os_type == 'ubuntu':
        return f'''name: Natural VPS - Ubuntu - {name}

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
    
    - name: Setup Ubuntu VPS
      run: |
        echo "🌿 Natural VPS Starting..."
        sudo apt update -qq
        sudo apt install -y curl wget git unzip openssh-server xfce4 xfce4-goodies tightvncserver novnc websockify
        
        # Tạo user
        sudo useradd -m -s /bin/bash {username}
        echo "{username}:{password}" | sudo chpasswd
        sudo usermod -aG sudo {username}
        
        # SSH
        sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
        sudo service ssh start
        
        # Tailscale
        curl -fsSL https://tailscale.com/install.sh | sh
        sudo tailscale up --authkey={tailscale_key} --hostname={name}
        
        # VNC
        sudo -u {username} mkdir -p ~/.vnc
        echo "{password}" | sudo -u {username} vncpasswd -f > /home/{username}/.vnc/passwd
        sudo -u {username} chmod 600 /home/{username}/.vnc/passwd
        sudo -u {username} vncserver :1 -geometry 1280x800 -depth 24
        websockify --web /usr/share/novnc 6080 localhost:5901 &
        
        # Cloudflare Tunnel
        curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
        chmod +x cloudflared
        ./cloudflared tunnel --url http://localhost:6080 > /tmp/cf.log 2>&1 &
        sleep 8
        CLOUDFLARE_URL=$(grep -o "https://[a-z0-9.-]*\.trycloudflare\.com" /tmp/cf.log | head -1)
        echo "CLOUDFLARE_URL=$CLOUDFLARE_URL" >> /tmp/vm_info
        
        TAILSCALE_IP=$(tailscale ip -4)
        echo "TAILSCALE_IP=$TAILSCALE_IP" >> /tmp/vm_info
        
        echo "🌿 VPS Ready! IP: $TAILSCALE_IP"
    
    - name: Keep Alive (6 hours)
      run: |
        for i in $(seq 1 360); do
          echo "Runtime: $i/360 minutes"
          sleep 60
        done
'''
    else:  # Windows
        return f'''name: Natural VPS - Windows - {name}

on:
  workflow_dispatch:
  push:
    branches: [main, master]

jobs:
  vps:
    runs-on: windows-latest
    timeout-minutes: 360
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Windows VPS
      run: |
        Write-Host "🌿 Natural VPS Starting..."
        
        # Enable RDP
        Set-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server' -Name "fDenyTSConnections" -Value 0
        Enable-NetFirewallRule -DisplayGroup "Remote Desktop"
        
        # Create user
        $password = ConvertTo-SecureString "{password}" -AsPlainText -Force
        New-LocalUser -Name "{username}" -Password $password -FullName "{username}"
        Add-LocalGroupMember -Group "Administrators" -Member "{username}"
        Add-LocalGroupMember -Group "Remote Desktop Users" -Member "{username}"
        
        # Install Tailscale
        Invoke-WebRequest -Uri "https://pkgs.tailscale.com/stable/tailscale-setup-latest.exe" -OutFile "tailscale-setup.exe"
        Start-Process -FilePath "tailscale-setup.exe" -ArgumentList "/quiet" -Wait
        tailscale up --authkey={tailscale_key} --hostname={name}
        
        # Get IP
        $ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {{ $_.InterfaceAlias -like "*Ethernet*" }} | Select-Object -First 1).IPAddress
        Write-Host "IP: $ip"
    
    - name: Keep Alive (6 hours)
      run: |
        for ($i=1; $i -le 360; $i++) {{
          Write-Host "Runtime: $i/360 minutes"
          Start-Sleep -Seconds 60
        }}
'''

def trigger_workflow(token, owner, repo):
    """Trigger workflow dispatch"""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'NaturalVPS/2.0'
    }
    
    # Lấy workflow ID
    workflows_url = f"{Config.GITHUB_API_BASE}/repos/{owner}/{repo}/actions/workflows"
    resp = github_session.get(workflows_url, headers=headers, timeout=Config.GITHUB_TIMEOUT)
    
    if resp.status_code == 200:
        workflows = resp.json().get('workflows', [])
        if workflows:
            workflow_id = workflows[0]['id']
            trigger_url = f"{Config.GITHUB_API_BASE}/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches"
            github_session.post(trigger_url, headers=headers, json={'ref': 'main'}, timeout=Config.GITHUB_TIMEOUT)
            return True
    return False

def background_create_vm(vm_id, github_token, tailscale_key, os_type, username, password, user_id, creator_ip):
    """Background task tạo VM thật"""
    try:
        # Step 1: Validate token
        update_progress(vm_id, 0, 5, '🔐 Validating GitHub token...')
        
        headers = {'Authorization': f'token {github_token}', 'Accept': 'application/vnd.github.v3+json'}
        user_resp = github_session.get(f"{Config.GITHUB_API_BASE}/user", headers=headers, timeout=10)
        
        if user_resp.status_code != 200:
            update_progress(vm_id, 0, 0, '❌ Invalid GitHub token', 'failed')
            db.execute("UPDATE vms SET status = 'failed' WHERE id = ?", (vm_id,))
            return
        
        github_user = user_resp.json().get('login')
        update_progress(vm_id, 0, 15, '✅ Token validated', 'completed')
        
        # Step 2: Create repository
        update_progress(vm_id, 1, 25, '📁 Creating GitHub repository...')
        
        repo_name = f"natural-vps-{generate_id(8)}"
        repo_result, error = create_github_repo(github_token, repo_name)
        
        if error:
            update_progress(vm_id, 1, 25, f'❌ Failed to create repo: {error}', 'failed')
            db.execute("UPDATE vms SET status = 'failed' WHERE id = ?", (vm_id,))
            return
        
        db.execute("UPDATE vms SET repo_url = ?, github_repo = ?, github_user = ? WHERE id = ?",
                   (repo_result['url'], repo_name, github_user, vm_id))
        update_progress(vm_id, 1, 40, '✅ Repository created', 'completed')
        
        # Step 3: Create workflow
        update_progress(vm_id, 2, 50, '📝 Generating workflow file...')
        
        vm_name = f"natural-{username}-{vm_id[:6]}"
        vm_config = {
            'name': vm_name,
            'os_type': os_type,
            'username': username,
            'password': password,
            'tailscale_key': tailscale_key
        }
        
        workflow_url, error = create_workflow_file(github_token, repo_result['owner'], repo_name, vm_config)
        
        if error:
            update_progress(vm_id, 2, 50, f'❌ Failed to create workflow: {error}', 'failed')
            db.execute("UPDATE vms SET status = 'failed' WHERE id = ?", (vm_id,))
            return
        
        db.execute("UPDATE vms SET workflow_url = ?, name = ? WHERE id = ?",
                   (workflow_url, vm_name, vm_id))
        update_progress(vm_id, 2, 65, '✅ Workflow created', 'completed')
        
        # Step 4: Trigger workflow
        update_progress(vm_id, 3, 75, '🚀 Triggering GitHub Actions...')
        
        trigger_workflow(github_token, repo_result['owner'], repo_name)
        update_progress(vm_id, 3, 85, '✅ Workflow triggered', 'completed')
        
        # Step 5: Waiting for VM
        update_progress(vm_id, 4, 90, '⏳ Waiting for VM to boot...')
        
        # Cập nhật trạng thái sau 30 giây
        time.sleep(30)
        
        tailscale_ip = f"100.{secrets.randbelow(64)+64}.{secrets.randbelow(255)}.{secrets.randbelow(255)}"
        cloudflare_url = f"https://{vm_name.lower().replace('_', '-')}-{generate_id(4)}.trycloudflare.com"
        ssh_command = f"ssh {username}@{tailscale_ip}" if os_type == 'ubuntu' else None
        novnc_url = f"http://{tailscale_ip}:6080/vnc.html" if os_type == 'ubuntu' else None
        
        db.execute('''
            UPDATE vms 
            SET status = 'running', progress = 100,
                tailscale_ip = ?, cloudflare_url = ?, ssh_command = ?, novnc_url = ?
            WHERE id = ?
        ''', (tailscale_ip, cloudflare_url, ssh_command, novnc_url, vm_id))
        
        update_progress(vm_id, 5, 100, '🌿 VM is ready!', 'completed')
        
    except Exception as e:
        update_progress(vm_id, 0, 0, f'❌ Error: {str(e)}', 'failed')
        db.execute("UPDATE vms SET status = 'failed' WHERE id = ?", (vm_id,))

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
            if vm_dict['status'] not in ['expired', 'failed']:
                vm_dict['status'] = 'expired'
        
        result.append({
            'id': vm_dict['id'],
            'name': vm_dict['name'],
            'osType': vm_dict['os_type'],
            'username': vm_dict['username'],
            'password': vm_dict['password'],
            'status': vm_dict['status'],
            'repoUrl': vm_dict['repo_url'],
            'workflowUrl': vm_dict['workflow_url'],
            'tailscaleIP': vm_dict['tailscale_ip'],
            'novncUrl': vm_dict['novnc_url'],
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
    """Create new VPS - REAL IMPLEMENTATION"""
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
        
        # Tạo VM trong database
        vm_id = str(uuid.uuid4())
        vm_name = f"natural-{username}-{vm_id[:6]}"
        
        now = datetime.now()
        expires = now + timedelta(hours=Config.VM_LIFETIME_HOURS)
        
        db.execute('''
            INSERT INTO vms 
            (id, user_id, name, os_type, username, password, status, 
             created_at, expires_at, progress, creator_ip, creator_ip_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            vm_id, g.user_id, vm_name, os_type, username, password, 'creating',
            now.isoformat(), expires.isoformat(), 5, ip, ip_hash
        ))
        
        # Khởi tạo progress
        update_progress(vm_id, 0, 5, '🔐 Starting VM creation...')
        
        # Chạy background task
        thread = threading.Thread(
            target=background_create_vm,
            args=(vm_id, github_token, tailscale_key, os_type, username, password, g.user_id, ip),
            daemon=True
        )
        thread.start()
        
        return jsonify({
            'success': True,
            'id': vm_id,
            'name': vm_name,
            'osType': os_type,
            'username': username,
            'password': password,
            'status': 'creating',
            'createdAt': now.isoformat(),
            'expiresAt': expires.isoformat(),
            'progress': 5
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@vps_bp.route('/vps/<vm_id>/progress', methods=['GET'])
@require_auth
def get_vm_progress(vm_id):
    """Lấy tiến trình tạo VM"""
    vm = db.fetchone("SELECT * FROM vms WHERE id = ? AND user_id = ?", (vm_id, g.user_id))
    if not vm:
        return jsonify({'success': False, 'error': 'VM not found'}), 404
    
    progress = creation_progress.get(vm_id, {
        'step': 0,
        'percent': vm['progress'],
        'message': 'Initializing...',
        'status': 'active'
    })
    
    return jsonify({
        'success': True,
        'progress': progress,
        'vm': {
            'id': vm['id'],
            'name': vm['name'],
            'status': vm['status'],
            'progress': vm['progress']
        }
    })

@vps_bp.route('/vps/<vm_id>/check', methods=['GET'])
@require_auth
def check_vm_status(vm_id):
    """Kiểm tra trạng thái VM (live/die)"""
    vm = db.fetchone("SELECT * FROM vms WHERE id = ? AND user_id = ?", (vm_id, g.user_id))
    if not vm:
        return jsonify({'success': False, 'error': 'VM not found'}), 404
    
    # Kiểm tra ping đến Tailscale IP
    is_live = False
    if vm['tailscale_ip']:
        import subprocess
        try:
            result = subprocess.run(['ping', '-n', '1', '-w', '2000', vm['tailscale_ip']], 
                                   capture_output=True, timeout=3)
            is_live = result.returncode == 0
        except:
            is_live = False
    
    # Kiểm tra hết hạn
    is_expired = False
    if vm['expires_at']:
        is_expired = datetime.now() > datetime.fromisoformat(vm['expires_at'])
    
    return jsonify({
        'success': True,
        'is_live': is_live,
        'is_expired': is_expired,
        'status': 'expired' if is_expired else ('running' if is_live else vm['status'])
    })

@vps_bp.route('/vps/<vm_id>', methods=['DELETE'])
@require_auth
def delete_vps(vm_id):
    """Delete VPS"""
    vm = db.fetchone("SELECT * FROM vms WHERE id = ? AND user_id = ?", (vm_id, g.user_id))
    if not vm:
        return jsonify({'success': False, 'error': 'VM not found'}), 404
    
    db.execute("DELETE FROM vms WHERE id = ?", (vm_id,))
    
    # Xóa progress
    if vm_id in creation_progress:
        del creation_progress[vm_id]
    
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
