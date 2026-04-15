"""
Natural VPS - Database Migration Utilities
Handles schema updates and migrations
"""

import sqlite3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseMigration:
    """Handles database schema migrations"""
    
    @staticmethod
    def add_notification_system(db_connection):
        """Add notification system tables and columns"""
        cursor = db_connection.cursor()
        
        try:
            # Add new columns to users table
            columns_to_add = [
                ('vps_email', 'TEXT UNIQUE'),
                ('real_email', 'TEXT'),
                ('web_username', 'TEXT UNIQUE'),
                ('notification_preferences', 'TEXT'),
                ('display_name', 'TEXT'),
                ('avatar_url', 'TEXT'),
                ('bio', 'TEXT'),
                ('timezone', 'TEXT DEFAULT "UTC"'),
                ('two_fa_enabled', 'INTEGER DEFAULT 0'),
            ]
            
            for col_name, col_def in columns_to_add:
                try:
                    cursor.execute(f'ALTER TABLE users ADD COLUMN {col_name} {col_def}')
                    logger.info(f'Added column {col_name} to users table')
                except sqlite3.OperationalError as e:
                    if 'duplicate column' in str(e):
                        logger.info(f'Column {col_name} already exists')
                    else:
                        raise
            
            # Create notifications table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT,
                    data TEXT,
                    read_at TIMESTAMP,
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            logger.info('Created notifications table')
            
            # Create notification preferences table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notification_preferences (
                    user_id TEXT PRIMARY KEY,
                    vm_created_email INTEGER DEFAULT 1,
                    vm_created_web INTEGER DEFAULT 1,
                    vm_error_email INTEGER DEFAULT 1,
                    vm_error_web INTEGER DEFAULT 1,
                    vm_expiring_email INTEGER DEFAULT 1,
                    vm_expiring_web INTEGER DEFAULT 1,
                    vm_expired_email INTEGER DEFAULT 1,
                    vm_expired_web INTEGER DEFAULT 0,
                    security_alert_email INTEGER DEFAULT 1,
                    security_alert_web INTEGER DEFAULT 1,
                    system_update_email INTEGER DEFAULT 0,
                    system_update_web INTEGER DEFAULT 1,
                    account_activity_email INTEGER DEFAULT 0,
                    account_activity_web INTEGER DEFAULT 1,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            logger.info('Created notification_preferences table')
            
            # Create user activity log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    resource_type TEXT,
                    resource_id TEXT,
                    details TEXT,
                    ip_address TEXT,
                    timestamp TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            logger.info('Created user_activity_logs table')
            
            # Create indices
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_activity_user ON user_activity_logs(user_id)')
            
            db_connection.commit()
            logger.info('Notification system migration completed successfully')
            return True, "Notification system migrated successfully"
        
        except Exception as e:
            logger.error(f'Migration failed: {str(e)}')
            db_connection.rollback()
            return False, f"Migration failed: {str(e)}"
    
    @staticmethod
    def add_tunnel_fields(db_connection):
        """Add Kami tunnel and public IP fields to VMs"""
        cursor = db_connection.cursor()
        
        try:
            columns_to_add = [
                ('kami_tunnel_url', 'TEXT'),
                ('kami_public_ip', 'TEXT'),
                ('kami_status', 'TEXT DEFAULT "pending"'),
                ('public_url', 'TEXT'),
                ('tunnel_enabled', 'INTEGER DEFAULT 1'),
            ]
            
            for col_name, col_def in columns_to_add:
                try:
                    cursor.execute(f'ALTER TABLE vms ADD COLUMN {col_name} {col_def}')
                    logger.info(f'Added column {col_name} to vms table')
                except sqlite3.OperationalError as e:
                    if 'duplicate column' in str(e):
                        logger.info(f'Column {col_name} already exists')
                    else:
                        raise
            
            db_connection.commit()
            logger.info('Tunnel fields migration completed successfully')
            return True, "Tunnel fields migrated successfully"
        
        except Exception as e:
            logger.error(f'Migration failed: {str(e)}')
            db_connection.rollback()
            return False, f"Migration failed: {str(e)}"
    
    @staticmethod
    def run_all_migrations(db_connection):
        """Run all pending migrations"""
        logger.info('Starting database migrations...')
        
        migrations = [
            ('notification_system', DatabaseMigration.add_notification_system),
            ('tunnel_fields', DatabaseMigration.add_tunnel_fields),
        ]
        
        results = []
        for name, migration_func in migrations:
            success, message = migration_func(db_connection)
            results.append((name, success, message))
            if not success:
                logger.warning(f'Migration {name} had issues: {message}')
        
        return results
