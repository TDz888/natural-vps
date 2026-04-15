"""
Natural VPS - Configuration
"""

import os
import secrets

class Config:
    VERSION = "4.0.0"
    APP_NAME = "Natural VPS - Auto-Kami Edition"
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.environ.get('DATA_DIR', os.path.join(BASE_DIR, 'data'))
    LOG_DIR = os.environ.get('LOG_DIR', os.path.join(BASE_DIR, 'logs'))
    DB_PATH = os.environ.get('DB_PATH', os.path.join(DATA_DIR, 'vps.db'))
    
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    JWT_SECRET = os.environ.get('JWT_SECRET', secrets.token_hex(32))
    JWT_EXPIRE_HOURS = int(os.environ.get('JWT_EXPIRE_HOURS', '24'))
    JWT_REFRESH_EXPIRE_DAYS = int(os.environ.get('JWT_REFRESH_EXPIRE_DAYS', '7'))
    BCRYPT_ROUNDS = int(os.environ.get('BCRYPT_ROUNDS', '12'))
    
    RATE_LIMIT_COUNT = int(os.environ.get('RATE_LIMIT_COUNT', '5'))
    RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', '10800'))
    LOGIN_RATE_LIMIT = int(os.environ.get('LOGIN_RATE_LIMIT', '5'))
    LOGIN_RATE_WINDOW = int(os.environ.get('LOGIN_RATE_WINDOW', '900'))
    
    # VM & Account Lifetime Management (v5)
    ACCOUNT_LIFETIME_HOURS = int(os.environ.get('ACCOUNT_LIFETIME_HOURS', '3'))
    VM_LIFETIME_HOURS = int(os.environ.get('VM_LIFETIME_HOURS', '3'))
    USER_VM_QUOTA = int(os.environ.get('USER_VM_QUOTA', '3'))
    ADMIN_CLEANUP_INTERVAL = int(os.environ.get('ADMIN_CLEANUP_INTERVAL', '300'))
    CLEANUP_INTERVAL = int(os.environ.get('CLEANUP_INTERVAL', '300'))
    
    GITHUB_API_BASE = os.environ.get('GITHUB_API_BASE', 'https://api.github.com')
    GITHUB_TIMEOUT = int(os.environ.get('GITHUB_TIMEOUT', '15'))
    GITHUB_RETRY_COUNT = int(os.environ.get('GITHUB_RETRY_COUNT', '3'))
    GITHUB_POOL_SIZE = int(os.environ.get('GITHUB_POOL_SIZE', '20'))
    
    CACHE_TTL = int(os.environ.get('CACHE_TTL', '5'))
    MAX_WORKERS = int(os.environ.get('MAX_WORKERS', '10'))
    COMPRESS_LEVEL = int(os.environ.get('COMPRESS_LEVEL', '6'))
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
    
    # API Endpoint
    API_ENDPOINT = os.environ.get('API_ENDPOINT', '34.10.118.99')
    API_PORT = int(os.environ.get('PORT', '5000'))
