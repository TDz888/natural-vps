"""
Natural VPS - Flask Application Factory
"""

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_compress import Compress
import os

def create_app():
    """Create and configure Flask application"""
    
    app = Flask(__name__, 
                static_folder='../static',
                template_folder='templates')
    
    # Load configuration
    from app.config import Config
    app.config.from_object(Config)
    
    # Initialize extensions
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['*']))
    Compress(app)
    app.config['COMPRESS_LEVEL'] = app.config.get('COMPRESS_LEVEL', 6)
    
    # Register blueprints
    from app.auth import auth_bp
    from app.vps import vps_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(vps_bp, url_prefix='/api')
    
    # Serve static files
    @app.route('/')
    def index():
        return send_from_directory(app.template_folder, 'index.html')
    
    @app.route('/<path:path>')
    def static_files(path):
        return send_from_directory(app.static_folder, path)
    
    # Health check
    @app.route('/api/health')
    def health():
        return {'status': 'healthy', 'version': app.config['VERSION']}
    
    return app
