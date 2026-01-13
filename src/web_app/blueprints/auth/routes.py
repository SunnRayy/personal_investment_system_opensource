from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from . import auth_bp
from src.web_app.auth_manager import User, verify_user


# =============================================================================
# JSON API Endpoints (for React SPA)
# =============================================================================

@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    """JSON API login endpoint for SPA."""
    data = request.get_json() or {}
    username = data.get('username', '')
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({
            'status': 'error',
            'message': 'Username and password are required'
        }), 400
    
    if verify_user(username, password):
        user = User(username)
        login_user(user)
        return jsonify({
            'status': 'success',
            'user': {'username': username}
        })
    
    return jsonify({
        'status': 'error',
        'message': 'Invalid username or password'
    }), 401


@auth_bp.route('/api/status')
def api_status():
    """Check current authentication status."""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': {'username': current_user.id}
        })
    return jsonify({
        'authenticated': False,
        'user': None
    })


@auth_bp.route('/api/logout', methods=['POST'])
def api_logout():
    """JSON API logout endpoint."""
    logout_user()
    return jsonify({'status': 'success'})


# =============================================================================
# Template-based Endpoints (legacy, for Flask templates)
# =============================================================================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if verify_user(username, password):
            user = User(username)
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        else:
            flash('Invalid username or password', 'error')
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
