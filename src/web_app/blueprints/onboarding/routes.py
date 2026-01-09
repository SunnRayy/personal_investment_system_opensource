"""
Onboarding routes for first-run experience.

Handles the complete onboarding flow:
1. Welcome page with mode selection
2. Demo mode activation
3. File upload for user data
4. Column mapping for imports
5. Onboarding completion
"""

import os
from pathlib import Path
from flask import (
    render_template, redirect, url_for, request,
    flash, current_app, session, jsonify, send_from_directory
)
from werkzeug.utils import secure_filename
from flask_babel import _

from src.web_app.blueprints.onboarding import bp
from src.web_app.system_state import (
    get_state_manager, SystemState, is_first_run, is_demo_mode
)


# Allowed file extensions for upload
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

# Maximum file size (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/')
def index():
    """
    Onboarding landing page.
    
    Shows options: Try Demo, Upload Data, or Skip.
    Redirects to dashboard if user already has data.
    """
    # Skip if already has data (not first run)
    if not is_first_run() and not is_demo_mode():
        return redirect(url_for('dashboard.index'))

    # Check if demo data is available
    state_manager = get_state_manager()
    has_demo = state_manager.has_demo_data()

    return render_template(
        'onboarding/welcome.html',
        has_demo_data=has_demo
    )


from flask_login import login_user
from src.web_app.auth_manager import User

@bp.route('/demo', methods=['POST'])
def enable_demo():
    """
    Enable demo mode and redirect to dashboard.
    
    Sets DEMO_MODE environment variable and updates system state.
    Auto-logs in as 'demo' user to bypass authentication checks.
    """
    state_manager = get_state_manager()
    state_manager.enable_demo_mode()
    
    # Auto-login demo user
    user = User('demo')
    login_user(user)

    flash(_('Demo mode enabled! Explore with sample data.'), 'success')
    return redirect(url_for('main.index'))


@bp.route('/upload')
def upload():
    """
    CSV/Excel upload page.
    
    Provides drag-and-drop file upload interface with template downloads.
    """
    return render_template('onboarding/upload.html')


@bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Handle file upload.
    
    Validates file type and size, saves to user_uploads directory.
    """
    if 'file' not in request.files:
        flash(_('No file selected'), 'error')
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        flash(_('No file selected'), 'error')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        # Get upload directory from environment or default
        data_dir = Path(os.environ.get('DATA_DIR', 'data'))
        upload_dir = data_dir / 'user_uploads'
        upload_dir.mkdir(parents=True, exist_ok=True)

        filepath = upload_dir / filename
        file.save(str(filepath))

        # Store in session for mapping step
        session['uploaded_file'] = str(filepath)
        session['original_filename'] = file.filename

        current_app.logger.info(f"File uploaded: {filename}")
        flash(_('File uploaded: %(filename)s', filename=filename), 'success')
        return redirect(url_for('onboarding.mapping'))

    flash(_('Invalid file type. Please upload CSV or Excel files.'), 'error')
    return redirect(request.url)


@bp.route('/mapping')
def mapping():
    """
    Column mapping page.
    
    Shows uploaded file preview and allows column assignment.
    """
    filepath = session.get('uploaded_file')

    if not filepath or not Path(filepath).exists():
        flash(_('Please upload a file first'), 'error')
        return redirect(url_for('onboarding.upload'))

    # Read file preview
    import pandas as pd

    try:
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath, nrows=5)
        else:
            df = pd.read_excel(filepath, nrows=5)

        columns = list(df.columns)
        preview = df.head().to_dict('records')

    except Exception as e:
        current_app.logger.error(f"Error reading file: {e}")
        flash(_('Error reading file: %(error)s', error=str(e)), 'error')
        return redirect(url_for('onboarding.upload'))

    return render_template(
        'onboarding/mapping.html',
        columns=columns,
        preview=preview,
        filename=session.get('original_filename')
    )


@bp.route('/complete', methods=['POST'])
def complete():
    """
    Complete onboarding and process imported data.
    
    Applies column mappings and imports data to system.
    """
    filepath = session.get('uploaded_file')

    if not filepath:
        flash(_('Session expired. Please upload again.'), 'error')
        return redirect(url_for('onboarding.upload'))

    # Get column mappings from form
    mappings = {
        'date': request.form.get('date_column'),
        'description': request.form.get('description_column'),
        'amount': request.form.get('amount_column'),
        'category': request.form.get('category_column'),
    }

    current_app.logger.info(f"Import mappings: {mappings}")

    # TODO: In Phase 5, implement actual import logic
    # from src.data_import.csv_importer import import_transactions
    # result = import_transactions(filepath, mappings)

    # Clear session data
    session.pop('uploaded_file', None)
    session.pop('original_filename', None)

    # Update system state to user_data
    state_manager = get_state_manager()
    state_manager._cached_state = SystemState.USER_DATA

    flash(_('Data imported successfully! You can now explore your portfolio.'), 'success')
    return redirect(url_for('dashboard.index'))


@bp.route('/skip')
def skip():
    """
    Skip onboarding and go to empty dashboard.
    
    Allows users to explore the system without data.
    """
    # Clear first-run state to prevent redirect loop
    session['onboarding_skipped'] = True
    return redirect(url_for('dashboard.index'))


@bp.route('/templates/<template_type>')
def download_template(template_type: str):
    """
    Download CSV template for data import.
    
    Args:
        template_type: Type of template (transactions, holdings, balance_sheet)
    """
    # Templates directory at project root
    project_root = Path(current_app.root_path).parent.parent
    templates_dir = project_root / 'templates' / 'csv_templates'

    template_files = {
        'transactions': 'transactions_template.csv',
        'holdings': 'holdings_template.csv',
        'balance_sheet': 'balance_sheet_template.csv',
    }

    filename = template_files.get(template_type)
    if not filename:
        flash(_('Template not found'), 'error')
        return redirect(url_for('onboarding.upload'))

    if not (templates_dir / filename).exists():
        flash(_('Template file not available'), 'error')
        return redirect(url_for('onboarding.upload'))

    return send_from_directory(
        str(templates_dir),
        filename,
        as_attachment=True
    )


@bp.route('/api/validate-file', methods=['POST'])
def validate_file():
    """
    API endpoint to validate uploaded file.
    
    Returns JSON with validation results for real-time feedback.
    """
    if 'file' not in request.files:
        return jsonify({'valid': False, 'error': 'No file provided'}), 400

    file = request.files['file']
    
    if not file.filename:
        return jsonify({'valid': False, 'error': 'No filename'}), 400

    if not allowed_file(file.filename):
        return jsonify({
            'valid': False, 
            'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400

    # Check file size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset position
    
    if size > MAX_FILE_SIZE:
        return jsonify({
            'valid': False,
            'error': f'File too large. Maximum: {MAX_FILE_SIZE // (1024*1024)}MB'
        }), 400

    return jsonify({
        'valid': True,
        'filename': file.filename,
        'size': size
    })
