"""
Natural VPS - Integration Test
Tests all anti-spam and email verification systems
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.database import db
from app.spam_detector import SpamDetector
from app.email_verification import EmailVerificationSystem
from datetime import datetime, timedelta

def test_email_validation():
    """Test email validation"""
    print("\n✓ Testing Email Validation...")
    
    # Valid emails
    valid_emails = [
        'user@example.com',
        'test.user@company.co.uk',
        'name+tag@domain.com'
    ]
    
    for email in valid_emails:
        is_valid, error = EmailVerificationSystem.validate_email(email)
        assert is_valid, f"Valid email {email} flagged as invalid: {error}"
        print(f"  ✓ {email} - Valid")
    
    # Invalid emails
    invalid_emails = [
        'plainaddress',
        'user@',
        '@domain.com',
        'user@temp-mail.io',  # Blacklisted domain
        'user@tempmail.com',  # Blacklisted domain
        'user...name@example.com'  # Suspicious pattern
    ]
    
    for email in invalid_emails:
        is_valid, error = EmailVerificationSystem.validate_email(email)
        assert not is_valid, f"Invalid email {email} passed validation"
        print(f"  ✗ {email} - Correctly rejected ({error[:30]}...)")

def test_email_code_generation():
    """Test email verification code generation"""
    print("\n✓ Testing Email Code Generation...")
    
    email = 'test@example.com'
    code = EmailVerificationSystem.generate_verification_code(email)
    
    assert code, "Code generation failed"
    assert len(code) == 6, f"Code length is {len(code)}, expected 6"
    assert code.isdigit(), f"Code is not all digits: {code}"
    
    print(f"  ✓ Generated code: {code} (for {email})")
    
    # Check status
    status = EmailVerificationSystem.get_verification_status(email)
    assert status['status'] == 'pending', f"Status is {status['status']}, expected pending"
    print(f"  ✓ Status: pending (expires in {status['expires_in_minutes']:.1f} minutes)")

def test_email_code_verification():
    """Test email code verification"""
    print("\n✓ Testing Email Code Verification...")
    
    email = 'verify@example.com'
    code = EmailVerificationSystem.generate_verification_code(email)
    
    # Wrong code
    success, error = EmailVerificationSystem.verify_email_code(email, '000000')
    assert not success, "Wrong code was accepted"
    print(f"  ✓ Wrong code rejected: {error}")
    
    # Correct code
    success, error = EmailVerificationSystem.verify_email_code(email, code)
    assert success, f"Correct code rejected: {error}"
    print(f"  ✓ Correct code accepted")
    
    # Check verified status
    is_verified = EmailVerificationSystem.is_email_verified(email)
    assert is_verified, "Email still not marked as verified"
    print(f"  ✓ Email marked as verified")

def test_registration_spam_limits():
    """Test registration spam detection"""
    print("\n✓ Testing Registration Spam Detection...")
    
    ip = '192.168.1.100'
    
    # Clear any existing test data
    test_email = 'spamtest@example.com'
    test_username = 'spamtestuser'
    
    # First registration should pass
    is_spam, reason = SpamDetector.check_registration_spam(ip, test_email)
    assert not is_spam, f"First registration flagged as spam: {reason}"
    print(f"  ✓ First registration allowed")

def test_login_spam_tracking():
    """Test login spam detection"""
    print("\n✓ Testing Login Spam Detection...")
    
    username = 'testuser'
    ip = '192.168.1.101'
    
    # Should not be blocked initially
    is_spam, reason = SpamDetector.check_login_spam(username, ip)
    assert not is_spam, f"Login blocked: {reason}"
    print(f"  ✓ Login attempt not blocked")

def test_ip_reputation():
    """Test IP reputation scoring"""
    print("\n✓ Testing IP Reputation...")
    
    email = 'reputation@example.com'
    reputation = EmailVerificationSystem.get_email_reputation(email)
    
    print(f"  ✓ Email reputation score: {reputation['score']}/100")
    print(f"  ✓ Status: {reputation['status']}")

def test_user_spam_score():
    """Test user spam score calculation"""
    print("\n✓ Testing User Spam Score...")
    
    # Create a test user
    user_id = 'test-user-spam-666'
    
    # Insert test user
    from app.utils import hash_password
    db.execute('''
        INSERT OR IGNORE INTO users (id, username, email, password_hash, created_at, api_key)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, 'spamtest99', 'spamtest99@example.com', hash_password('test123'), 
          datetime.now().isoformat(), 'test_key'))
    
    score = SpamDetector.get_spam_score(user_id)
    print(f"  ✓ User spam score: {score}/100")
    assert score >= 0 and score <= 100, f"Invalid score: {score}"

def test_email_reputation():
    """Test email reputation"""
    print("\n✓ Testing Email Reputation...")
    
    # Good email
    good_email = 'good@company.com'
    reputation = EmailVerificationSystem.get_email_reputation(good_email)
    print(f"  ✓ Good email reputation: {reputation['score']}/100 ({reputation['status']})")
    
    # Suspicious email pattern
    suspicious_email = 'test@10minutemail.com'
    reputation = EmailVerificationSystem.get_email_reputation(suspicious_email)
    print(f"  ✗ Suspicious email reputation: {reputation['score']}/100 ({reputation['status']})")
    assert reputation['status'] == 'bad', "Suspicious email not marked as bad"

def main():
    print("=" * 60)
    print("Natural VPS - Anti-Spam & Email Verification Tests")
    print("=" * 60)
    
    # Initialize Flask app
    app = create_app()
    with app.app_context():
        try:
            test_email_validation()
            test_email_code_generation()
            test_email_code_verification()
            test_registration_spam_limits()
            test_login_spam_tracking()
            test_ip_reputation()
            test_user_spam_score()
            test_email_reputation()
            
            print("\n" + "=" * 60)
            print("✓ ALL TESTS PASSED!")
            print("=" * 60)
            return 0
        except AssertionError as e:
            print(f"\n✗ TEST FAILED: {e}")
            return 1
        except Exception as e:
            print(f"\n✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return 1

if __name__ == '__main__':
    sys.exit(main())
