"""
Database Migration v5 - Account Lifetime & VM Quotas System
Handles account expiration, VM quotas, and admin account creation
"""

from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DatabaseMigrationV5:
    """Database migrations for lifetime and quota management"""
    
    @staticmethod
    def add_account_lifetime_system(db_connection):
        """Add account lifetime and quota tracking columns to users table"""
        try:
            cursor = db_connection.cursor()
            
            # Add account lifetime columns
            columns_to_add = [
                ("account_lifetime_hours", "INTEGER DEFAULT 3"),  # 3 hours default
                ("account_created_at", "TIMESTAMP"),
                ("account_expires_at", "TIMESTAMP"),
                ("is_admin", "INTEGER DEFAULT 0"),
                ("admin_created_by", "TEXT"),  # User ID of admin who created this account
                ("is_active", "INTEGER DEFAULT 1"),  # Account active flag
                ("vm_quota", "INTEGER DEFAULT 3"),  # VMs allowed for this account
                ("is_unlimited", "INTEGER DEFAULT 0"),  # Admin flag for unlimited
            ]
            
            # Check and add each column if it doesn't exist
            for col_name, col_definition in columns_to_add:
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_definition}")
                    logger.info(f"✓ Added column '{col_name}' to users table")
                except Exception as e:
                    if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                        logger.info(f"✓ Column '{col_name}' already exists")
                    else:
                        raise
            
            db_connection.commit()
            logger.info("✓ Account lifetime system migration complete")
            
        except Exception as e:
            logger.error(f"✗ Failed to add account lifetime system: {e}")
            raise
    
    @staticmethod
    def add_vm_lifecycle_columns(db_connection):
        """Add VM lifecycle tracking columns"""
        try:
            cursor = db_connection.cursor()
            
            columns_to_add = [
                ("vm_lifetime_hours", "INTEGER DEFAULT 3"),  # 3 hours default
                ("vm_created_at", "TIMESTAMP"),
                ("vm_expires_at", "TIMESTAMP"),
                ("created_by_admin", "INTEGER DEFAULT 0"),  # Created by admin flag
                ("admin_who_created", "TEXT"),  # Admin user ID
            ]
            
            for col_name, col_definition in columns_to_add:
                try:
                    cursor.execute(f"ALTER TABLE vms ADD COLUMN {col_name} {col_definition}")
                    logger.info(f"✓ Added column '{col_name}' to vms table")
                except Exception as e:
                    if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                        logger.info(f"✓ Column '{col_name}' already exists")
                    else:
                        raise
            
            db_connection.commit()
            logger.info("✓ VM lifecycle columns migration complete")
            
        except Exception as e:
            logger.error(f"✗ Failed to add VM lifecycle columns: {e}")
            raise
    
    @staticmethod
    def create_admin_audit_log_table(db_connection):
        """Create admin action audit log table"""
        try:
            cursor = db_connection.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target_user_id TEXT,
                    target_vm_id TEXT,
                    details TEXT,
                    ip_address TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE SET NULL,
                    FOREIGN KEY (target_user_id) REFERENCES users(id) ON DELETE SET NULL,
                    FOREIGN KEY (target_vm_id) REFERENCES vms(id) ON DELETE SET NULL
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_admin_actions_admin ON admin_actions(admin_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_admin_actions_timestamp ON admin_actions(timestamp)')
            
            db_connection.commit()
            logger.info("✓ Admin audit log table created")
            
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info("✓ Admin audit log table already exists")
            else:
                logger.error(f"✗ Failed to create admin audit log: {e}")
                raise
    
    @staticmethod
    def create_account_deletion_queue(db_connection):
        """Create table for tracking accounts/VMs to delete"""
        try:
            cursor = db_connection.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deletion_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    user_id TEXT,
                    deletion_reason TEXT,
                    scheduled_deletion_at TIMESTAMP NOT NULL,
                    deleted_at TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_deletion_queue_scheduled ON deletion_queue(scheduled_deletion_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_deletion_queue_status ON deletion_queue(status)')
            
            db_connection.commit()
            logger.info("✓ Deletion queue table created")
            
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info("✓ Deletion queue table already exists")
            else:
                logger.error(f"✗ Failed to create deletion queue: {e}")
                raise
    
    @staticmethod
    def run_all_migrations(db_connection):
        """Run all v5 migrations in order"""
        logger.info("=" * 60)
        logger.info("Running Database Migration v5 - Lifetime & Quotas")
        logger.info("=" * 60)
        
        try:
            DatabaseMigrationV5.add_account_lifetime_system(db_connection)
            DatabaseMigrationV5.add_vm_lifecycle_columns(db_connection)
            DatabaseMigrationV5.create_admin_audit_log_table(db_connection)
            DatabaseMigrationV5.create_account_deletion_queue(db_connection)
            
            logger.info("=" * 60)
            logger.info("✓ All v5 migrations completed successfully!")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"✗ Migration failed: {e}")
            raise
