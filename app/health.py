"""
Natural VPS - Workflow Health Check
"""

import requests
import re
import time
import threading
from flask import Blueprint, jsonify
from app.database import db
from app.config import Config

health_bp = Blueprint('health', __name__)

workflow_cache = {}
cache_lock = threading.Lock()

def check_workflow_status(github_token, owner, repo):
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'NaturalVPS/3.0'
    }
    
    try:
        url = f"{Config.GITHUB_API_BASE}/repos/{owner}/{repo}/actions/runs"
        resp = requests.get(url, headers=headers, timeout=Config.GITHUB_TIMEOUT)
        
        if resp.status_code != 200:
            return {'error': f'API error: {resp.status_code}', 'status': 'unknown'}
        
        runs = resp.json().get('workflow_runs', [])
        if not runs:
            return {'status': 'not_found', 'conclusion': None}
        
        latest = runs[0]
        return {
            'id': latest['id'],
            'status': latest['status'],
            'conclusion': latest['conclusion'],
            'url': latest['html_url']
        }
    except Exception as e:
        return {'error': str(e), 'status': 'error'}

def extract_kami_info(github_token, owner, repo, run_id):
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'NaturalVPS/3.0'
    }
    
    try:
        url = f"{Config.GITHUB_API_BASE}/repos/{owner}/{repo}/actions/runs/{run_id}/logs"
        resp = requests.get(url, headers=headers, timeout=Config.GITHUB_TIMEOUT, allow_redirects=True)
        
        if resp.status_code != 200:
            return {'kami_url': None, 'tailscale_ip': None}
        
        logs = resp.text
        
        # Extract Kami URL
        kami_match = re.search(r'(https?://[a-z0-9.-]+\.kami\.dev)(?:\s|$)', logs)
        kami_url = kami_match.group(1) if kami_match else None
        
        # Extract Tailscale IP
        ip_match = re.search(r'TAILSCALE_IP=(\d+\.\d+\.\d+\.\d+)', logs)
        tailscale_ip = ip_match.group(1) if ip_match else None
        
        # Extract Kami IP:Port
        if kami_url:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(kami_url)
                kami_ip = parsed.hostname
                kami_port = parsed.port or '80'
            except:
                kami_ip = None
                kami_port = None
        else:
            kami_ip = None
            kami_port = None
        
        return {
            'kami_url': kami_url,
            'kami_ip': kami_ip,
            'kami_port': kami_port,
            'tailscale_ip': tailscale_ip
        }
    except Exception as e:
        return {'error': str(e)}

def monitor_workflow(vm_id, github_token, owner, repo):
    for i in range(60):
        time.sleep(5)
        
        status = check_workflow_status(github_token, owner, repo)
        
        if status.get('status') == 'completed':
            if status.get('conclusion') == 'success':
                # Extract Kami info
                info = extract_kami_info(github_token, owner, repo, status.get('id'))
                
                db.execute('''
                    UPDATE vms 
                    SET status = 'running', progress = 100,
                        tailscale_ip = ?, kami_url = ?, kami_ip = ?, kami_port = ?
                    WHERE id = ?
                ''', (info.get('tailscale_ip'), info.get('kami_url'), info.get('kami_ip'), info.get('kami_port'), vm_id))
                return
            else:
                db.execute("UPDATE vms SET status = 'failed', error_message = ? WHERE id = ?",
                          (f"Workflow {status.get('conclusion')}", vm_id))
                return
        
        # Update progress
        progress = min(90, 50 + i * 2)
        db.execute("UPDATE vms SET progress = ? WHERE id = ?", (progress, vm_id))
    
    db.execute("UPDATE vms SET status = 'timeout', error_message = 'Workflow timeout' WHERE id = ?", (vm_id,))

@health_bp.route('/workflow/<vm_id>', methods=['GET'])
def get_workflow_health(vm_id):
    vm = db.fetchone("SELECT * FROM vms WHERE id = ?", (vm_id,))
    if not vm:
        return jsonify({'success': False, 'error': 'VM not found'}), 404
    
    return jsonify({
        'success': True,
        'vm': {
            'id': vm['id'],
            'status': vm['status'],
            'progress': vm['progress'],
            'kami_url': vm['kami_url'],
            'kami_ip': vm['kami_ip'],
            'kami_port': vm['kami_port'],
            'tailscale_ip': vm['tailscale_ip'],
            'error_message': vm['error_message']
        }
    })
