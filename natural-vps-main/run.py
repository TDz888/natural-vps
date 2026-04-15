#!/usr/bin/env python3
"""
Natural VPS - Entry Point with Kami Tunnel Auto-Setup
API Endpoint: http://34.10.118.99:5000
"""

import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app import create_app
from app.kami_service import KamiTunnelService, PublicIPService
from app.db_migration import DatabaseMigration
from app.db_migration_v5 import DatabaseMigrationV5
from app.account_lifetime_manager import AccountLifetimeManager

def setup_kami_tunnel():
    """Setup Kami tunnel for public IP access"""
    logger.info("🔧 Checking Kami tunnel setup...")
    
    if not KamiTunnelService.is_kami_installed():
        logger.info("📦 Installing Kami tunnel...")
        success, message = KamiTunnelService.install_kami()
        if success:
            logger.info(f"✅ {message}")
        else:
            logger.warning(f"⚠️  {message}")
    else:
        logger.info("✅ Kami tunnel already installed")
    
    # Detect public IP
    logger.info("🌍 Detecting public IP address...")
    success, public_ip = PublicIPService.get_public_ip()
    if success:
        logger.info(f"✅ Public IP: {public_ip}")
        return public_ip
    else:
        logger.warning("⚠️  Could not detect public IP")
        return None

def run_migrations():
    """Run database migrations v4 and v5"""
    logger.info("🗄️  Running database migrations...")
    try:
        from app.database import db
        conn = db._get_connection()
        
        # Run v4 migrations
        logger.info("📦 Running v4 migrations...")
        results = DatabaseMigration.run_all_migrations(conn)
        
        for name, success, message in results:
            if success:
                logger.info(f"✅ {name}: {message}")
            else:
                logger.warning(f"⚠️  {name}: {message}")
        
        # Run v5 migrations (Lifetime & Quotas)
        logger.info("📦 Running v5 migrations (Lifetime & Quotas)...")
        DatabaseMigrationV5.run_all_migrations(conn)
        
        logger.info("✅ All migrations completed successfully!")
        
    except Exception as e:
        logger.error(f"[ERROR] Migration error: {str(e)}")
        raise

def main():
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Create Flask app
    app = create_app()
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    enable_kami = os.environ.get('ENABLE_KAMI', 'true').lower() == 'true'
    
    # Check for SSL certificates
    ssl_context = None
    ssl_status = "🔓 HTTP only"
    if os.path.exists('cert.pem') and os.path.exists('key.pem'):
        ssl_context = ('cert.pem', 'key.pem')
        ssl_status = "[SSL] HTTPS/SSL enabled"
    
    # Run migrations
    run_migrations()
    
    # Setup Kami tunnel
    public_ip = None
    if enable_kami:
        public_ip = setup_kami_tunnel()
    
    print(f"""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║   NATURAL VPS - Ephemeral Cloud Computing                      ║
║   Version: 4.0.0 (Auto-Kami Edition)                           ║
║                                                                ║
║   Server Configuration:                                        ║
║   • Port:       {port:<5}                                      ║
║   • Debug:      {str(debug):<5}                                ║
║   • Security:   {ssl_status:<28}                          ║
║   • Kami Tunnel: {('Enabled [OK]' if enable_kami else 'Disabled'):<28} ║
║   {f'• Public IP:    {public_ip:<29}' if public_ip else ''}
║                                                                ║
║   Access URLs:                                                ║
║   • Main:       http://localhost:{port}                        ║
║   • Auth:       http://localhost:{port}/auth                   ║
║   • Dashboard:  http://localhost:{port}/dashboard              ║
║   • Admin:      http://localhost:{port}/admin                  ║
║   • API:        http://localhost:{port}/api                    ║
║   • Health:     http://localhost:{port}/api/health             ║
║                                                                ║
║   Default Endpoints:                                           ║
║   • User Registration: /api/auth/register                      ║
║   • User Login: /api/auth/login                                ║
║   • VM Creation: /api/vms/create                               ║
║   • VM List: /api/vms                                          ║
║   • Admin Dashboard: /api/admin/dashboard                      ║
║                                                                ║
║   Database: {os.path.basename(os.environ.get('DB_PATH', 'data/vps.db')):<28}
║   Data Dir: {os.path.dirname(os.environ.get('DB_PATH', 'data/vps.db')):<29}
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        logger.info(f"[INFO] Starting Natural VPS server on 0.0.0.0:{port}")
        app.run(host='0.0.0.0', port=port, debug=debug, threaded=True, ssl_context=ssl_context)
    except OSError as e:
        if "Address already in use" in str(e):
            logger.error(f"[ERROR] Port {port} is already in use!")
            logger.info(f"   Options:")
            logger.info(f"   1. Kill existing process: netstat -ano | findstr :{port}")
            logger.info(f"   2. Use different port: $env:PORT=8000; python run.py")
        else:
            raise
    except Exception as e:
        logger.error(f"[ERROR] Startup error: {str(e)}")
        raise

if __name__ == '__main__':
    main()
