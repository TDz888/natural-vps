"""
Account Lifetime Manager
Handles account expiration, auto-deletion, and VM quota enforcement
"""

from datetime import datetime, timedelta
import logging
from flask import current_app

logger = logging.getLogger(__name__)


class AccountLifetimeManager:
    """Manages account and VM lifetimes"""
    
    # Default lifetimes (in hours)
    DEFAULT_ACCOUNT_LIFETIME = 3
    DEFAULT_VM_LIFETIME = 3
    
    # Quotas
    USER_VM_QUOTA = 3  # Regular users can have 3 VMs
    ADMIN_UNLIMITED = True
    
    @staticmethod
    def create_account_with_lifetime(db, user_id, real_email, lifetime_hours=None, is_admin_created=False, 
                                      admin_id=None, made_unlimited=False):
        """
        Create account with specified lifetime
        lifetime_hours: None = 3 hours default, or specific hours, or float('inf') for lifetime
        """
        if lifetime_hours is None:
            lifetime_hours = AccountLifetimeManager.DEFAULT_ACCOUNT_LIFETIME
        
        now = datetime.now()
        expires_at = now + timedelta(hours=lifetime_hours) if lifetime_hours != float('inf') else None
        
        try:
            cursor = db._get_connection().cursor()
            
            cursor.execute('''
                UPDATE users 
                SET account_created_at = ?,
                    account_expires_at = ?,
                    account_lifetime_hours = ?,
                    is_active = 1,
                    admin_created_by = ?,
                    is_unlimited = ?
                WHERE id = ?
            ''', (
                now.isoformat(),
                expires_at.isoformat() if expires_at else None,
                lifetime_hours,
                admin_id,
                1 if made_unlimited else 0,
                user_id
            ))
            
            db._get_connection().commit()
            
            logger.info(f"✓ Account {user_id} created with {lifetime_hours}h lifetime")
            
            return True, "Account created successfully"
            
        except Exception as e:
            logger.error(f"✗ Failed to create account with lifetime: {e}")
            return False, str(e)
    
    @staticmethod
    def check_account_expired(db, user_id):
        """
        Check if account has expired
        Returns (is_expired, time_remaining_seconds)
        """
        try:
            result = db.fetchone(
                "SELECT account_expires_at, is_unlimited FROM users WHERE id = ?",
                (user_id,)
            )
            
            if not result:
                return False, 0
            
            expires_at, is_unlimited = result[0], result[1]
            
            if is_unlimited or expires_at is None:
                return False, float('inf')
            
            expires_dt = datetime.fromisoformat(expires_at)
            now = datetime.now()
            
            if now > expires_dt:
                return True, 0
            
            remaining = (expires_dt - now).total_seconds()
            return False, remaining
            
        except Exception as e:
            logger.error(f"✗ Failed to check account expiration: {e}")
            return False, 0
    
    @staticmethod
    def check_vm_quota(db, user_id):
        """
        Check if user can create more VMs
        Returns (can_create, current_count, limit)
        """
        try:
            user = db.fetchone(
                "SELECT is_unlimited, vm_quota FROM users WHERE id = ?",
                (user_id,)
            )
            
            if not user:
                return False, 0, 0
            
            is_unlimited, quota = user[0], user[1]
            
            # Admin accounts are unlimited
            if is_unlimited:
                return True, 0, float('inf')
            
            # Count active VMs
            vm_count = db.fetchone(
                "SELECT COUNT(*) FROM vms WHERE user_id = ? AND status != 'deleted'",
                (user_id,)
            )[0]
            
            can_create = vm_count < quota
            
            return can_create, vm_count, quota
            
        except Exception as e:
            logger.error(f"✗ Failed to check VM quota: {e}")
            return False, 0, 0
    
    @staticmethod
    def update_vm_lifetime(db, vm_id, lifetime_hours=None, created_by_admin=False, admin_id=None):
        """Update VM with lifetime tracking"""
        if lifetime_hours is None:
            lifetime_hours = AccountLifetimeManager.DEFAULT_VM_LIFETIME
        
        now = datetime.now()
        expires_at = now + timedelta(hours=lifetime_hours)
        
        try:
            cursor = db._get_connection().cursor()
            
            cursor.execute('''
                UPDATE vms
                SET vm_created_at = ?,
                    vm_expires_at = ?,
                    vm_lifetime_hours = ?,
                    created_by_admin = ?,
                    admin_who_created = ?
                WHERE id = ?
            ''', (
                now.isoformat(),
                expires_at.isoformat(),
                lifetime_hours,
                1 if created_by_admin else 0,
                admin_id,
                vm_id
            ))
            
            db._get_connection().commit()
            
            logger.info(f"✓ VM {vm_id} lifetime set to {lifetime_hours}h")
            return True, "VM lifetime updated"
            
        except Exception as e:
            logger.error(f"✗ Failed to update VM lifetime: {e}")
            return False, str(e)
    
    @staticmethod
    def schedule_deletion(db, resource_type, resource_id, user_id, reason="Lifetime expired"):
        """
        Schedule account or VM for deletion
        resource_type: 'account' or 'vm'
        """
        try:
            cursor = db._get_connection().cursor()
            
            # Schedule deletion for 1 hour from now (grace period)
            deletion_time = datetime.now() + timedelta(hours=1)
            
            cursor.execute('''
                INSERT INTO deletion_queue 
                (resource_type, resource_id, user_id, deletion_reason, scheduled_deletion_at, status)
                VALUES (?, ?, ?, ?, ?, 'pending')
            ''', (
                resource_type,
                resource_id,
                user_id,
                reason,
                deletion_time.isoformat()
            ))
            
            db._get_connection().commit()
            
            logger.info(f"✓ Scheduled {resource_type} {resource_id} for deletion at {deletion_time}")
            return True, "Deletion scheduled"
            
        except Exception as e:
            logger.error(f"✗ Failed to schedule deletion: {e}")
            return False, str(e)
    
    @staticmethod
    def process_expired_accounts(db):
        """
        Check and process expired accounts
        Returns count of processed accounts
        """
        try:
            cursor = db._get_connection().cursor()
            
            # Find expired accounts
            now = datetime.now()
            
            expired = cursor.execute('''
                SELECT id, vps_email 
                FROM users 
                WHERE account_expires_at IS NOT NULL 
                AND account_expires_at < ? 
                AND is_active = 1
            ''', (now.isoformat(),)).fetchall()
            
            count = 0
            for user_id, email in expired:
                # Mark as inactive and schedule deletion
                cursor.execute(
                    "UPDATE users SET is_active = 0 WHERE id = ?",
                    (user_id,)
                )
                
                AccountLifetimeManager.schedule_deletion(
                    db, 'account', user_id, user_id,
                    f"Account expired (was {email})"
                )
                
                logger.info(f"✓ Marked account {user_id} ({email}) as expired")
                count += 1
            
            db._get_connection().commit()
            
            if count > 0:
                logger.info(f"✓ Processed {count} expired accounts")
            
            return count
            
        except Exception as e:
            logger.error(f"✗ Failed to process expired accounts: {e}")
            return 0
    
    @staticmethod
    def process_expired_vms(db):
        """
        Check and process expired VMs
        Returns count of processed VMs
        """
        try:
            cursor = db._get_connection().cursor()
            
            now = datetime.now()
            
            expired = cursor.execute('''
                SELECT id, user_id, name
                FROM vms 
                WHERE vm_expires_at IS NOT NULL 
                AND vm_expires_at < ? 
                AND status != 'deleted' AND status != 'deleting'
            ''', (now.isoformat(),)).fetchall()
            
            count = 0
            for vm_id, user_id, name in expired:
                # Mark as deleting
                cursor.execute(
                    "UPDATE vms SET status = 'deleting' WHERE id = ?",
                    (vm_id,)
                )
                
                AccountLifetimeManager.schedule_deletion(
                    db, 'vm', vm_id, user_id,
                    f"VM lifetime expired: {name}"
                )
                
                logger.info(f"✓ Marked VM {vm_id} ({name}) for deletion")
                count += 1
            
            db._get_connection().commit()
            
            if count > 0:
                logger.info(f"✓ Processed {count} expired VMs")
            
            return count
            
        except Exception as e:
            logger.error(f"✗ Failed to process expired VMs: {e}")
            return 0
    
    @staticmethod
    def get_account_status(db, user_id):
        """Get detailed account status"""
        try:
            user = db.fetchone('''
                SELECT username, vps_email, account_expires_at, is_unlimited, 
                       vm_quota, is_active
                FROM users WHERE id = ?
            ''', (user_id,))
            
            if not user:
                return None
            
            username, email, expires_at, is_unlimited, quota, is_active = user
            
            is_expired, remaining = AccountLifetimeManager.check_account_expired(db, user_id)
            can_create, vm_count, limit = AccountLifetimeManager.check_vm_quota(db, user_id)
            
            expires_formatted = None
            if expires_at:
                expires_dt = datetime.fromisoformat(expires_at)
                expires_formatted = expires_dt.strftime("%Y-%m-%d %H:%M:%S")
            
            return {
                'username': username,
                'email': email,
                'is_active': bool(is_active),
                'is_expired': is_expired,
                'is_unlimited': bool(is_unlimited),
                'expires_at': expires_formatted,
                'time_remaining_hours': remaining / 3600 if remaining != float('inf') else None,
                'vms': {
                    'current': vm_count,
                    'limit': limit if limit != float('inf') else 'unlimited',
                    'can_create': can_create
                }
            }
            
        except Exception as e:
            logger.error(f"✗ Failed to get account status: {e}")
            return None
