import os
import logging
import time
from datetime import datetime
from flask import render_template, jsonify, Response, current_app, session, redirect, request, url_for
from flask_login import login_required
from . import main_bp

logger = logging.getLogger(__name__)

@main_bp.route('/set_language/<lang_code>')
def set_language(lang_code):
    """Set the session language."""
    if lang_code in ['en', 'zh']:
        session['lang'] = lang_code
    return redirect(request.referrer or url_for('main.index'))


@main_bp.route('/')
def index():
    """Main dashboard page - redirects to onboarding for first-run users"""
    from flask_login import current_user
    from src.web_app.system_state import is_first_run
    
    # Check first-run BEFORE login check to allow unauthenticated onboarding
    if is_first_run():
        return redirect(url_for('onboarding.index'))
    
    # For non-first-run, require authentication
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login', next=request.url))
    
    return render_template('dashboard/index.html')

@main_bp.route('/compass')
@login_required
def compass():
    """Investment Compass dashboard page"""
    try:
        # Serve the compass dashboard HTML file directly
        compass_html_path = os.path.join(current_app.root_path, 'compass_dashboard', 'index.html')
        
        if os.path.exists(compass_html_path):
            with open(compass_html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Fix relative paths to absolute paths for static files
            html_content = html_content.replace('href="style.css"', 'href="/compass/static/style.css"')
            html_content = html_content.replace('src="app.js"', 'src="/compass/static/app.js"')
            
            return html_content
        else:
            logger.error(f"Compass dashboard HTML not found at: {compass_html_path}")
            return jsonify({
                'error': 'Compass dashboard not found',
                'message': 'The Investment Compass dashboard HTML file is missing'
            }), 404
            
    except Exception as e:
        logger.error(f"Error serving compass dashboard: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to load Investment Compass dashboard'
        }), 500

@main_bp.route('/compass/static/<filename>')
@login_required
def compass_static(filename):
    """Serve static files for compass dashboard"""
    try:
        static_dir = os.path.join(current_app.root_path, 'compass_dashboard')
        file_path = os.path.join(static_dir, filename)
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Set appropriate content type
            if filename.endswith('.css'):
                return Response(content, mimetype='text/css')
            elif filename.endswith('.js'):
                return Response(content, mimetype='application/javascript')
            else:
                return content
        else:
            return "File not found", 404
            
    except Exception as e:
        logger.error(f"Error serving compass static file {filename}: {str(e)}")
        return f"Error loading {filename}", 500

@main_bp.route('/health')
def health_check():
    """System health monitoring endpoint"""
    # Simplified health check for now
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@main_bp.route('/test-components')
def test_components():
    """Route to verify UI components"""
    return render_template('test_components.html')
