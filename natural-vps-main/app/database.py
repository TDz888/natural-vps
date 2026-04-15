"""
Natural VPS - Database Manager
"""

import sqlite3
import threading
import os
from app.config import Config

class Database:
    def __init__(self):
        self.db_path = Config.DB_PATH
        self._local = threading.local()
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
    
    def _get_connection(self):
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA synchronous=NORMAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
        return self._local.conn
    
    def _init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP,
                last_login TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                api_key TEXT UNIQUE,
                creator_ip_hash TEXT,
                email_verified INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                refresh_token TEXT UNIQUE,
                created_at TIMESTAMP,
                expires_at TIMESTAMP,
                ip TEXT,
                user_agent TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vms (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                name TEXT NOT NULL,
                os_type TEXT DEFAULT 'ubuntu',
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                status TEXT DEFAULT 'creating',
                repo_url TEXT,
                workflow_url TEXT,
                tailscale_ip TEXT,
                novnc_url TEXT,
                kami_url TEXT,
                kami_ip TEXT,
                kami_port TEXT,
                ssh_command TEXT,
                created_at TIMESTAMP,
                expires_at TIMESTAMP,
                progress INTEGER DEFAULT 0,
                github_repo TEXT,
                github_user TEXT,
                creator_ip TEXT,
                creator_ip_hash TEXT,
                error_message TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rate_limits (
                ip_hash TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0,
                window_start TIMESTAMP,
                last_request TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_hash TEXT,
                user_id TEXT,
                username TEXT,
                success INTEGER DEFAULT 0,
                timestamp TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_vms_user_id ON vms(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_vms_status ON vms(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_vms_expires ON vms(expires_at)')
        
        # Security tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ip_whitelist (
                ip TEXT PRIMARY KEY,
                reason TEXT,
                added_at TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ip_blacklist (
                ip TEXT PRIMARY KEY,
                reason TEXT,
                added_at TIMESTAMP,
                expires_at TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS request_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT,
                method TEXT,
                path TEXT,
                status_code INTEGER,
                user_id TEXT,
                timestamp TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_request_logs_timestamp ON request_logs(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_request_logs_ip ON request_logs(ip)')
        
        # Advanced logging tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS event_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                user_id TEXT,
                data TEXT,
                severity TEXT DEFAULT 'info',
                timestamp TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_type TEXT,
                user_id TEXT,
                error_message TEXT,
                traceback TEXT,
                context TEXT,
                timestamp TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation TEXT,
                duration_ms REAL,
                status TEXT,
                details TEXT,
                timestamp TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_event_logs_timestamp ON event_logs(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_error_logs_timestamp ON error_logs(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_performance_logs_timestamp ON performance_logs(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_performance_logs_operation ON performance_logs(operation)')
        
        # Spam detection tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS spam_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                spam_type TEXT,
                details TEXT,
                timestamp TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                code TEXT NOT NULL,
                verified INTEGER DEFAULT 0,
                attempts INTEGER DEFAULT 0,
                created_at TIMESTAMP,
                verified_at TIMESTAMP,
                expires_at TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                code TEXT,
                status TEXT,
                sent_at TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id TEXT,
                action TEXT,
                target_id TEXT,
                target_type TEXT,
                details TEXT,
                timestamp TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_hash TEXT,
                event_type TEXT,
                severity TEXT,
                details TEXT,
                timestamp TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_spam_logs_timestamp ON spam_logs(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_spam_logs_user ON spam_logs(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_email_verifications_email ON email_verifications(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_admin_actions_admin ON admin_actions(admin_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_admin_actions_timestamp ON admin_actions(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_events_timestamp ON security_events(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_events_ip ON security_events(ip_hash)')
        
        conn.commit()
    
    def execute(self, query, params=()):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor
    
    def fetchone(self, query, params=()):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()
    
    def fetchall(self, query, params=()):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

db = Database()
