import os
import sys

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.web_app import create_app

app = create_app()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Run the web application')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the application on')
    args = parser.parse_args()
    
    app.run(debug=True, port=args.port)
