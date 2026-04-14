#!/usr/bin/env python3
"""
Natural VPS - Entry Point
API Endpoint: http://34.10.118.99:5000
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app import create_app

def main():
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    app = create_app()
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🌿 NATURAL VPS - Cinematic Nature 4K                       ║
║   Version: 3.0.0                                             ║
║                                                              ║
║   Server: http://34.10.118.99:{port:<5}                      ║
║   Debug:  {str(debug):<5}                                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug, threaded=True)

if __name__ == '__main__':
    main()
