"""
Natural VPS - Flask Application Factory
Version: 4.0.0
"""

import os
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from flask_compress import Compress
from werkzeug.exceptions import BadRequest
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(base_dir, 'app', 'templates')
    static_dir = os.path.join(base_dir, 'static')
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir, static_url_path='/static')
    
    from app.config import Config
    app.config.from_object(Config)
    
    # Ensure SECRET_KEY is set
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.urandom(32).hex()
    
    logger.info(f"🔧 Initializing Natural VPS v{Config.VERSION}")
    
    # Initialize caching
    from app.cache import cache
    cache.init_app(app)
    logger.info("✅ Cache initialized")
    
    # Initialize enhanced security
    try:
        from app.security_enhanced import SecurityManager, limiter
    except ImportError:
        from app.security import SecurityManager, limiter
    
    limiter.init_app(app)
    SecurityManager.init_security(app)
    logger.info("✅ Security & Rate limiting initialized")
    
    # CORS configuration
    CORS(app, 
        origins=['*'],
        supports_credentials=True,
        allow_headers=['Content-Type', 'Authorization', 'X-CSRF-Token', 'X-Requested-With'],
        methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
        expose_headers=['Content-Length', 'X-CSRF-Token'],
        max_age=3600
    )
    logger.info("✅ CORS configured")
    
    # Compression
    Compress(app)
    app.config['COMPRESS_LEVEL'] = app.config.get('COMPRESS_LEVEL', 6)
    
    # Protocol mismatch handler
    @app.before_request
    def check_protocol():
        """Handle TLS/HTTP protocol mismatches gracefully"""
        try:
            if request.content_length and request.content_length > 0:
                raw_data = request.get_data(as_text=False)
                if raw_data and raw_data[0:1] == b'\x16':  # TLS handshake
                    return jsonify({
                        'error': 'Protocol Mismatch',
                        'message': 'HTTPS client connecting to HTTP server',
                        'solution': 'Use http:// instead of https://',
                        'endpoint': f'http://{request.host}'
                    }), 400
        except:
            pass
    
    # Register blueprints
    logger.info("📚 Registering API routes...")
    
    # Try to register auth_new_v5 first (with lifetime management), fall back to auth_new
    try:
        from app.auth_new_v5 import auth_bp as auth_new_v5_bp
        app.register_blueprint(auth_new_v5_bp, url_prefix='/api/auth')
        logger.info("✅ Auth v5 routes registered (with lifetime management)")
    except ImportError:
        try:
            from app.auth_new import auth_bp as auth_new_bp
            app.register_blueprint(auth_new_bp, url_prefix='/api/auth')
            logger.info("✅ Auth v4 routes registered")
        except ImportError:
            logger.warning("⚠️  New auth not found, falling back to old auth")
            from app.auth import auth_bp
            app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    # Try to register admin_v5, fall back to old admin
    try:
        from app.admin_v5 import admin_bp as admin_v5_bp
        app.register_blueprint(admin_v5_bp, url_prefix='/api/admin_v5')
        logger.info("✅ Admin v5 routes registered (with user management)")
    except ImportError:
        logger.warning("⚠️  Admin v5 not found")
    
    from app.vps import vps_bp
    from app.health import health_bp
    from app.monitor import monitor_bp
    from app.admin import init_admin_system
    
    app.register_blueprint(vps_bp, url_prefix='/api')
    logger.info("✅ VPS routes registered")
    
    app.register_blueprint(health_bp, url_prefix='/api')
    logger.info("✅ Health routes registered")
    
    app.register_blueprint(monitor_bp, url_prefix='/api/monitor')
    logger.info("✅ Monitor routes registered")
    
    # Initialize admin system
    init_admin_system(app)
    logger.info("✅ Admin system initialized")
    
    # Static routes
    @app.route('/')
    def index():
        """Main landing/auth page"""
        try:
            return send_from_directory(app.template_folder, 'auth_v5.html')
        except:
            try:
                return send_from_directory(app.template_folder, 'auth.html')
            except:
                return """
                <html>
                    <head><title>🌿 Natural VPS</title></head>
                    <body style="background:#1a3a2a;color:#e8e4d9;font-family:Arial;text-align:center;padding-top:100px;">
                        <h1>🌿 Natural VPS</h1>
                        <p>Server is running!</p>
                        <p><a href="/api/health">Check health</a></p>
                    </body>
                </html>"""
    
    @app.route('/auth')
    def auth():
        """Authentication page"""
        try:
            return send_from_directory(app.template_folder, 'auth_v5.html')
        except:
            try:
                return send_from_directory(app.template_folder, 'auth.html')
            except:
                return "<h1>Auth Page Not Found</h1>", 404
    
    @app.route('/dashboard')
    def dashboard():
        """User dashboard"""
        try:
            return send_from_directory(app.template_folder, 'dashboard_v5.html')
        except:
            try:
                return send_from_directory(app.template_folder, 'dashboard.html')
            except Exception as e:
                return f"<h1>Dashboard Error</h1><p>{str(e)}</p>", 500
    
    @app.route('/admin')
    def admin_panel():
        """Admin control panel"""
        try:
            return send_from_directory(app.template_folder, 'admin_v5.html')
        except:
            try:
                return send_from_directory(app.template_folder, 'admin.html')
            except Exception as e:
                return f"<h1>Admin Panel Error</h1><p>{str(e)}</p>", 500
    
    @app.route('/api/health')
    def health():
        """Health check endpoint"""
        return {
            'status': 'healthy',
            'version': app.config.get('VERSION', '4.0.0'),
            'endpoint': '34.10.118.99:5000',
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'features': ['auth', 'vps', 'admin', 'kami-tunnel', 'notifications']
        }
    
    logger.info(f"🎉 Natural VPS v{Config.VERSION} initialized successfully!")
    
    return app

