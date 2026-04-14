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
                api_key TEXT UNIQUE
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
