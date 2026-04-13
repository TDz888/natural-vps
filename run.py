#!/usr/bin/env python3
"""
Natural VPS - Entry Point
"""

import os
from app import create_app

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Create app instance
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🌿 Natural VPS - Cinematic Nature 4K                       ║
║                                                              ║
║   Server: http://0.0.0.0:{port:<5}                              ║
║   Debug:  {str(debug):<5}                                         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
