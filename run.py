#!/usr/bin/env python3
"""
FindMyDos - Protest Monitoring Application
Main entry point for the application.
"""

import os
from findmydos.web.app import create_app

def main():
    """Main application entry point."""
    app = create_app()

    # Get configuration from environment
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()