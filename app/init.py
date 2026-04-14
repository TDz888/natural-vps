"""
Natural VPS - Flask Application Factory
"""

import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_compress import Compress

def create_app():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(base_dir, 'app', 'templates')
    static_dir = os.path.join(base_dir, 'static')
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir, static_url_path='/static')
    
    from app.config import Config
    app.config.from_object(Config)
    
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.urandom(32).hex()
    
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['*']))
    Compress(app)
    app.config['COMPRESS_LEVEL'] = app.config.get('COMPRESS_LEVEL', 6)
    
    from app.auth import auth_bp
    from app.vps import vps_bp
    from app.health import health_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(vps_bp, url_prefix='/api')
    app.register_blueprint(health_bp, url_prefix='/api')
    
    @app.route('/')
    def index():
        try:
            return send_from_directory(app.template_folder, 'index.html')
        except:
            return """
            <html><head><title>Natural VPS</title></head>
            <body style="background:#1a3a2a;color:#e8e4d9;font-family:Arial;text-align:center;padding-top:100px;">
            <h1>🌿 Natural VPS</h1><p>Server is running!</p>
            <p>API: http://34.10.118.99:5000</p>
            </body></html>"""
    
    @app.route('/api/health')
    def health():
        return {'status': 'healthy', 'version': app.config.get('VERSION', '3.0.0'), 'endpoint': '34.10.118.99:5000'}
    
    return app
