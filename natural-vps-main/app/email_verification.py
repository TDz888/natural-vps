"""
Natural VPS - Email Verification System
Professional email-based verification and anti-spam measures
"""

from datetime import datetime, timedelta
import secrets
import re
import json
from typing import Tuple, Optional
from app.database import db

class EmailVerificationSystem:
    """Manages email verification and validation"""
    
    # Email validation patterns
    EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Blacklisted email domains (free/temp services)
    BLACKLISTED_DOMAINS = {
        'temp-mail.io', 'tempmail.com', '10minutemail.com',
        'mailinator.com', 'throwaway.email', 'guerrillamail.com',
        'maildrop.cc', 'fakeinbox.com', 'trashmail.com',
        'yopmail.com', 'getnada.com', 'mailnesia.com'
    }
    
    # Code configuration
    VERIFICATION_CODE_LENGTH = 6
    VERIFICATION_CODE_EXPIRY_MINUTES = 15
    MAX_ATTEMPTS = 3

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email format and domain"""
        
        # Basic format validation
        if not re.match(EmailVerificationSystem.EMAIL_REGEX, email):
            return False, "Invalid email format"
        
        # Too long
        if len(email) > 254:
            return False, "Email too long"
        
        # Check for blacklisted domains
        domain = email.split('@')[1].lower()
        if domain in EmailVerificationSystem.BLACKLISTED_DOMAINS:
            return False, f"Email domain '{domain}' is not allowed (temporary/disposable service)"
        
        # Check for obvious spam patterns
        if email.count('.') > 3:
            return False, "Suspicious email format (too many dots)"
        
        # Check for consecutive special characters
        if '..' in email or '__' in email or '--' in email:
            return False, "Invalid email format"
        
        return True, ""

    @staticmethod
    def generate_verification_code(email: str) -> str:
        """Generate a 6-digit verification code"""
        code = ''.join([str(secrets.randbelow(10)) for _ in range(EmailVerificationSystem.VERIFICATION_CODE_LENGTH)])
        
        # Store in database
        db.execute(
            """INSERT INTO email_verifications (email, code, created_at, expires_at, verified)
               VALUES (?, ?, ?, ?, 0)""",
            (
                email,
                code,
                datetime.now().isoformat(),
                (datetime.now() + timedelta(minutes=EmailVerificationSystem.VERIFICATION_CODE_EXPIRY_MINUTES)).isoformat()
            )
        )
        
        return code

    @staticmethod
    def verify_email_code(email: str, code: str) -> Tuple[bool, str]:
        """Verify email with code"""
        
        # Clean code input
        code = code.strip().replace(' ', '')
        
        # Check if code matches
        record = db.fetchone(
            """SELECT id, code, attempts, expires_at, verified FROM email_verifications
               WHERE email = ? ORDER BY created_at DESC LIMIT 1""",
            (email,)
        )
        
        if not record:
            return False, "No verification code found for this email"
        
        # Check if already verified
        if record['verified']:
            return False, "Email already verified"
        
        # Check expiry
        expiry = datetime.fromisoformat(record['expires_at'])
        if datetime.now() > expiry:
            return False, "Verification code expired"
        
        # Check attempts
        if record['attempts'] >= EmailVerificationSystem.MAX_ATTEMPTS:
            return False, "Too many incorrect attempts. Please request a new code."
        
        # Verify code
        if code == record['code']:
            # Mark as verified
            db.execute(
                "UPDATE email_verifications SET verified = 1, verified_at = ? WHERE id = ?",
                (datetime.now().isoformat(), record['id'])
            )
            return True, ""
        else:
            # Increment attempts
            db.execute(
                "UPDATE email_verifications SET attempts = attempts + 1 WHERE id = ?",
                (record['id'],)
            )
            remaining = EmailVerificationSystem.MAX_ATTEMPTS - record['attempts'] - 1
            return False, f"Invalid code. {remaining} attempts remaining."

    @staticmethod
    def is_email_verified(email: str) -> bool:
        """Check if email is verified"""
        record = db.fetchone(
            "SELECT verified FROM email_verifications WHERE email = ? ORDER BY created_at DESC LIMIT 1",
            (email,)
        )
        return record and record['verified'] == 1

    @staticmethod
    def get_verification_status(email: str) -> dict:
        """Get email verification status"""
        record = db.fetchone(
            """SELECT verified, attempts, expires_at FROM email_verifications 
               WHERE email = ? ORDER BY created_at DESC LIMIT 1""",
            (email,)
        )
        
        if not record:
            return {'status': 'no_code', 'message': 'No verification initiated'}
        
        if record['verified']:
            return {'status': 'verified', 'message': 'Email is verified'}
        
        expiry = datetime.fromisoformat(record['expires_at'])
        if datetime.now() > expiry:
            return {'status': 'expired', 'message': 'Code expired'}
        
        remaining_time = expiry - datetime.now()
        remaining_attempts = EmailVerificationSystem.MAX_ATTEMPTS - record['attempts']
        
        return {
            'status': 'pending',
            'remaining_attempts': remaining_attempts,
            'expires_in_minutes': remaining_time.total_seconds() / 60 + 1
        }

    @staticmethod
    def cleanup_old_codes(days: int = 7):
        """Clean up old verification codes"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        db.execute(
            "DELETE FROM email_verifications WHERE created_at < ? AND verified = 0",
            (cutoff,)
        )

    @staticmethod
    def get_email_reputation(email: str) -> dict:
        """Get reputation score for an email"""
        reputation_score = 100  # Start at 100 (good)
        reasons = []
        
        # Check blacklist
        domain = email.split('@')[1].lower()
        if domain in EmailVerificationSystem.BLACKLISTED_DOMAINS:
            reputation_score -= 50
            reasons.append("Domain is temporary/disposable service")
        
        # Check for failed verifications
        failed_attempts = db.fetchone(
            """SELECT COUNT(*) as count FROM email_verifications 
               WHERE email = ? AND verified = 0""",
            (email,)
        )
        
        if failed_attempts and failed_attempts['count'] > 3:
            reputation_score -= 20
            reasons.append(f"Multiple failed verification attempts ({failed_attempts['count']})")
        
        # Check for associated spam users
        spam_users = db.fetchone(
            """SELECT COUNT(*) as count FROM users 
               WHERE email = ? AND (is_active = 0 OR created_at > datetime('now', '-1 day'))""",
            (email,)
        )
        
        if spam_users and spam_users['count'] > 0:
            reputation_score -= 15
            reasons.append("Email linked to suspended accounts")
        
        return {
            'score': max(0, reputation_score),
            'status': 'good' if reputation_score >= 80 else 'suspicious' if reputation_score >= 60 else 'bad',
            'reasons': reasons
        }

    @staticmethod
    def should_block_registration(email: str) -> Tuple[bool, str]:
        """Check if email registration should be blocked"""
        is_valid, error = EmailVerificationSystem.validate_email(email)
        if not is_valid:
            return True, error
        
        # Check reputation
        reputation = EmailVerificationSystem.get_email_reputation(email)
        if reputation['score'] < 30:
            reasons = ', '.join(reputation['reasons']) or 'Low email reputation score'
            return True, f"Email verification failed: {reasons}"
        
        # Check for too many accounts with same email
        account_count = db.fetchone(
            "SELECT COUNT(*) as count FROM users WHERE email = ?",
            (email,)
        )
        
        if account_count and account_count['count'] >= 3:
            return True, "Too many accounts with this email"
        
        return False, ""

    @staticmethod
    def send_verification_code(email: str, code: str) -> Tuple[bool, str]:
        """Send verification code (placeholder - implement with actual email service)"""
        
        # TODO: Integrate with email service (SendGrid, AWS SES, etc.)
        # For now, this is a placeholder that logs to database
        
        db.execute(
            """INSERT INTO email_logs (email, code, status, sent_at)
               VALUES (?, ?, ?, ?)""",
            (email, code, 'sent', datetime.now().isoformat())
        )
        
        # In production, implement actual email sending:
        # import sendgrid
        # sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        # message = Mail(
        #     from_email='noreply@natural-vps.com',
        #     to_emails=email,
        #     subject='Your Email Verification Code',
        #     html_content=f'Your verification code is: <strong>{code}</strong>'
        # )
        # try:
        #     sg.send(message)
        #     return True, ""
        # except Exception as e:
        #     return False, str(e)
        
        return True, ""
