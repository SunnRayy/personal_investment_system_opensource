#!/usr/bin/env python3
"""
Web Application Launcher for Personal Investment System

This script launches the Flask development server for the web interface.
"""

import os
import sys

def main():
    """Launch the Flask web application"""
    
    # Get the directory where this script is located (project root)
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Add project root to Python path
    sys.path.insert(0, project_root)
    
    print("=" * 60)
    print("Personal Investment System - Web Interface Launcher")
    print("=" * 60)
    print(f"Project Root: {project_root}")
    print()
    
    # Check if Flask is installed
    try:
        import flask
        print(f"✓ Flask {flask.__version__} is installed")
    except ImportError:
        print("✗ Flask is not installed")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)
    
    # Launch the Flask application
    try:
        # Allow custom port via command line argument
        port = 5001
        if len(sys.argv) > 1:
            try:
                port = int(sys.argv[1])
            except ValueError:
                print(f"Invalid port argument: {sys.argv[1]}. Using default port 5001.")
        print(f"\nStarting Flask development server...")
        print(f"Access the web interface at: http://127.0.0.1:{port}")
        print("Press Ctrl+C to stop the server")
        print("-" * 60)
        # Import and run the Flask app
        from src.web_app.app import app
        app.run(debug=True, host='127.0.0.1', port=port)
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
    except Exception as e:
        print(f"\n✗ Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
