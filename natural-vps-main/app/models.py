"""
Natural VPS - Data Models
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

@dataclass
class User:
    id: str
    username: str
    email: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_login: Optional[str] = None
    api_key: Optional[str] = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at,
            'last_login': self.last_login,
            'api_key': self.api_key
        }

@dataclass
class VM:
    id: str
    user_id: str
    name: str
    os_type: str
    username: str
    password: str
    status: str = 'creating'
    repo_url: Optional[str] = None
    workflow_url: Optional[str] = None
    tailscale_ip: Optional[str] = None
    novnc_url: Optional[str] = None
    kami_url: Optional[str] = None
    kami_ip: Optional[str] = None
    kami_port: Optional[str] = None
    ssh_command: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    expires_at: Optional[str] = None
    progress: int = 0
    github_repo: Optional[str] = None
    github_user: Optional[str] = None
    creator_ip: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'osType': self.os_type,
            'username': self.username,
            'password': self.password,
            'status': self.status,
            'repoUrl': self.repo_url,
            'workflowUrl': self.workflow_url,
            'tailscaleIP': self.tailscale_ip,
            'novncUrl': self.novnc_url,
            'kamiUrl': self.kami_url,
            'kamiIP': self.kami_ip,
            'kamiPort': self.kami_port,
            'sshCommand': self.ssh_command,
            'createdAt': self.created_at,
            'expiresAt': self.expires_at,
            'progress': self.progress,
            'errorMessage': self.error_message
        }
    
    @classmethod
    def from_row(cls, row):
        return cls(
            id=row['id'],
            user_id=row['user_id'],
            name=row['name'],
            os_type=row['os_type'],
            username=row['username'],
            password=row['password'],
            status=row['status'],
            repo_url=row['repo_url'],
            workflow_url=row['workflow_url'],
            tailscale_ip=row['tailscale_ip'],
            novnc_url=row['novnc_url'],
            kami_url=row['kami_url'],
            kami_ip=row['kami_ip'],
            kami_port=row['kami_port'],
            ssh_command=row['ssh_command'],
            created_at=row['created_at'],
            expires_at=row['expires_at'],
            progress=row['progress'],
            github_repo=row['github_repo'],
            github_user=row['github_user'],
            creator_ip=row['creator_ip'],
            error_message=row['error_message']
        )

@dataclass
class Progress:
    step: int = 0
    percent: int = 0
    message: str = ''
    status: str = 'active'  # active, completed, failed
    error: Optional[str] = None
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self):
        return asdict(self)
