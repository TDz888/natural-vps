"""
Natural VPS - Database Manager
"""

import sqlite3
import threading
import os
from datetime import datetime
from app.config import Config

class Database:
    """Thread-safe SQLite database manager"""
    
    def __init__(self):
        self.db_path = Config.DB_PATH
        self._local = threading.local()
        self._init_db()
    
    def _get_connection(self):
        """Get thread-local database connection"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA synchronous=NORMAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
            self._local.conn.execute("PRAGMA cache_size=-64000")
        return self._local.conn
    
    def _init_db(self):
        """Initialize database tables"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Users table
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
        
        # Sessions table
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
        
        # VMs table
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
                cloudflare_url TEXT,
                ssh_command TEXT,
                created_at TIMESTAMP,
                expires_at TIMESTAMP,
                progress INTEGER DEFAULT 0,
                github_repo TEXT,
                github_user TEXT,
                creator_ip TEXT,
                creator_ip_hash TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Rate limits table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rate_limits (
                ip_hash TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0,
                window_start TIMESTAMP,
                last_request TIMESTAMP
            )
        ''')
        
        # Login attempts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_hash TEXT,
                username TEXT,
                success INTEGER DEFAULT 0,
                timestamp TIMESTAMP
            )
        ''')
        
        # Indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_vms_user_id ON vms(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_vms_status ON vms(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_vms_expires ON vms(expires_at)')
        
        conn.commit()
    
    def execute(self, query, params=()):
        """Execute query and commit"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor
    
    def fetchone(self, query, params=()):
        """Fetch single row"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()
    
    def fetchall(self, query, params=()):
        """Fetch all rows"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

# Global database instance
db = Database()
