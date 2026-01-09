# Implementation Guide: Docker Zero-Friction Setup

This document provides detailed, step-by-step implementation instructions for developers.

---

## Phase 1: Docker Infrastructure Setup

### 1.1 Create Dockerfile

**File**: `/Dockerfile`

```dockerfile
# =============================================================================
# Personal Investment System - Docker Image
# Multi-stage build for optimized image size
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies and compile wheels
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Runtime - Slim production image
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS runtime

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopenblas0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories with correct permissions
RUN mkdir -p /app/data /app/logs /app/output /app/data/user_uploads /app/data/cache && \
    chown -R appuser:appuser /app/data /app/logs /app/output

# Copy and set up entrypoint script
COPY --chown=appuser:appuser docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Switch to non-root user
USER appuser

# Environment variables
ENV FLASK_HOST=0.0.0.0 \
    FLASK_PORT=5000 \
    APP_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]

# Default command
CMD ["python", "main.py", "run-web", "--host", "0.0.0.0", "--port", "5000"]
```

**Implementation Notes**:

- Multi-stage build reduces image from ~1.5GB to ~500MB
- Non-root user `appuser` for security
- Pre-created directories ensure write permissions
- Health check endpoint must be implemented (see Phase 2)

---

### 1.2 Create docker-compose.yml

**File**: `/docker-compose.yml`

```yaml
# =============================================================================
# Personal Investment System - Docker Compose Configuration
# One-command deployment: docker-compose up -d
# =============================================================================

version: '3.8'

services:
  pis-web:
    build:
      context: .
      dockerfile: Dockerfile
    image: personal-investment-system:latest
    container_name: pis-web
    restart: unless-stopped

    ports:
      - "${PIS_PORT:-5000}:5000"

    volumes:
      # Persistent data - user uploads, database, cache
      - pis-data:/app/data
      # Configuration - mount for customization
      - ./config:/app/config:ro
      # Logs - accessible from host
      - ./logs:/app/logs
      # Reports - accessible from host
      - ./output:/app/output

    environment:
      # Application
      - APP_ENV=${APP_ENV:-production}
      - SECRET_KEY=${SECRET_KEY:-}
      - FLASK_HOST=0.0.0.0
      - FLASK_PORT=5000

      # Database
      - DB_PATH=/app/data/investment_system.db
      - DATA_DIR=/app/data

      # Logging
      - LOG_LEVEL=${LOG_LEVEL:-INFO}

      # Demo mode (set to 'true' to force demo mode)
      - DEMO_MODE=${DEMO_MODE:-false}

      # Timezone
      - TZ=${TZ:-UTC}

      # Optional: External API keys
      - FRED_API_KEY=${FRED_API_KEY:-}

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

# Named volume for data persistence
volumes:
  pis-data:
    name: pis-investment-data

# Network configuration (optional, for future services)
networks:
  default:
    name: pis-network
```

**Usage Instructions**:

```bash
# Basic startup
docker-compose up -d

# With custom port
PIS_PORT=8080 docker-compose up -d

# Force demo mode
DEMO_MODE=true docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Stop and remove data (CAUTION)
docker-compose down -v
```

---

### 1.3 Create .dockerignore

**File**: `/.dockerignore`

```
# =============================================================================
# Docker Build Ignore File
# =============================================================================

# Git
.git
.gitignore

# Python
__pycache__
*.py[cod]
*$py.class
*.so
.Python
.env
.venv
env/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Build artifacts
build/
dist/
*.egg-info/
*.egg

# Logs and output (regenerated at runtime)
logs/*
!logs/.gitkeep
output/*
!output/.gitkeep

# Data files (user-specific, mounted via volume)
data/user_uploads/*
data/cache/*
data/*.db
data/*.db-wal
data/*.db-shm
!data/demo_source/

# Development files
*.md
!README.md
!DOCKER_QUICKSTART.md
docs/
tests/
notebooks/

# Docker files (no recursion needed)
Dockerfile
docker-compose*.yml
.dockerignore
```

---

### 1.4 Create docker-entrypoint.sh

**File**: `/docker-entrypoint.sh`

```bash
#!/bin/bash
# =============================================================================
# Personal Investment System - Docker Entrypoint
# Handles initialization, database setup, and first-run detection
# =============================================================================

set -e

echo "=========================================="
echo "Personal Investment System - Starting Up"
echo "=========================================="

# -----------------------------------------------------------------------------
# Environment Setup
# -----------------------------------------------------------------------------

# Set defaults
export APP_ENV="${APP_ENV:-production}"
export DB_PATH="${DB_PATH:-/app/data/investment_system.db}"
export DATA_DIR="${DATA_DIR:-/app/data}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"

echo "[INFO] Environment: $APP_ENV"
echo "[INFO] Database: $DB_PATH"
echo "[INFO] Data Directory: $DATA_DIR"

# -----------------------------------------------------------------------------
# Directory Setup
# -----------------------------------------------------------------------------

echo "[INFO] Ensuring directories exist..."

# Create directories if they don't exist
mkdir -p "$DATA_DIR/user_uploads"
mkdir -p "$DATA_DIR/cache"
mkdir -p "$DATA_DIR/cost_basis_lots"
mkdir -p "$DATA_DIR/historical_snapshots"
mkdir -p /app/logs
mkdir -p /app/output

# -----------------------------------------------------------------------------
# Secret Key Generation
# -----------------------------------------------------------------------------

if [ -z "$SECRET_KEY" ]; then
    if [ "$APP_ENV" = "production" ]; then
        echo "[WARN] SECRET_KEY not set in production!"
        echo "[WARN] Generating random key (will change on restart)"
    fi
    export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
fi

# -----------------------------------------------------------------------------
# Database Initialization
# -----------------------------------------------------------------------------

echo "[INFO] Checking database..."

if [ ! -f "$DB_PATH" ]; then
    echo "[INFO] Database not found. Initializing..."
    python main.py init-database || {
        echo "[ERROR] Database initialization failed"
        # Continue anyway - the app will create it
    }
    echo "[INFO] Database initialized at $DB_PATH"
else
    echo "[INFO] Database found at $DB_PATH"
fi

# -----------------------------------------------------------------------------
# First-Run Detection
# -----------------------------------------------------------------------------

echo "[INFO] Checking system state..."

# Check if user has uploaded any data
USER_DATA_COUNT=$(find "$DATA_DIR/user_uploads" -type f \( -name "*.csv" -o -name "*.xlsx" -o -name "*.xls" \) 2>/dev/null | wc -l)

# Check database has transactions
if [ -f "$DB_PATH" ]; then
    DB_TABLES=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='table';" 2>/dev/null || echo "0")
else
    DB_TABLES="0"
fi

if [ "$DEMO_MODE" = "true" ]; then
    echo "[INFO] Demo mode enabled via environment"
    export SYSTEM_STATE="demo_mode"
elif [ "$USER_DATA_COUNT" -gt 0 ] || [ "$DB_TABLES" -gt 5 ]; then
    echo "[INFO] User data detected"
    export SYSTEM_STATE="user_data"
else
    echo "[INFO] No user data found - First run detected"
    export SYSTEM_STATE="first_run"
fi

echo "[INFO] System state: $SYSTEM_STATE"

# -----------------------------------------------------------------------------
# Demo Data Setup (if needed)
# -----------------------------------------------------------------------------

if [ "$SYSTEM_STATE" = "first_run" ] || [ "$SYSTEM_STATE" = "demo_mode" ]; then
    if [ -d "/app/data/demo_source" ]; then
        echo "[INFO] Demo data available at /app/data/demo_source"
    else
        echo "[WARN] Demo data directory not found"
    fi
fi

# -----------------------------------------------------------------------------
# Health Check Endpoint Setup
# -----------------------------------------------------------------------------

# Create health check file to indicate startup complete
touch /app/data/.startup_complete

# -----------------------------------------------------------------------------
# Launch Application
# -----------------------------------------------------------------------------

echo "=========================================="
echo "[INFO] Starting application..."
echo "=========================================="

# Execute the CMD passed to the container
exec "$@"
```

**Permissions**:

```bash
chmod +x docker-entrypoint.sh
```

---

## Phase 2: Application Modifications

### 2.1 Add Health Check Endpoint

**File**: `src/web_app/blueprints/api/routes.py`

Add this route to the existing API blueprint:

```python
@bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for Docker/Kubernetes.
    Returns 200 if application is healthy.
    """
    import os
    from flask import jsonify

    health_status = {
        'status': 'healthy',
        'app': 'Personal Investment System',
        'environment': os.environ.get('APP_ENV', 'development'),
        'system_state': os.environ.get('SYSTEM_STATE', 'unknown'),
    }

    # Check database connectivity
    try:
        from src.database.connector import DatabaseConnector
        connector = DatabaseConnector()
        connector.test_connection()
        health_status['database'] = 'connected'
    except Exception as e:
        health_status['database'] = f'error: {str(e)}'
        health_status['status'] = 'degraded'

    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code
```

**Also add root-level health endpoint** in `src/web_app/__init__.py`:

```python
# Inside create_app() function, after registering blueprints:

@app.route('/health')
def root_health():
    """Root-level health check for Docker."""
    return {'status': 'healthy'}, 200
```

---

### 2.2 Modify Flask Host Binding

**File**: `main.py`

Find the `run_web` command and modify:

```python
@cli.command()
@click.option('--host', default=None, help='Host to bind to')
@click.option('--port', default=5000, help='Port to run on')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def run_web(host, port, debug):
    """Launch the Flask web interface."""
    import os
    from src.web_app import create_app

    # Use environment variable if host not specified
    if host is None:
        host = os.environ.get('FLASK_HOST', '127.0.0.1')

    # Use environment variable for port if available
    port = int(os.environ.get('FLASK_PORT', port))

    app = create_app()

    # Set debug from environment if not specified
    if not debug:
        debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

    click.echo(f"Starting web server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
```

---

### 2.3 Environment-Based Secret Key

**File**: `src/web_app/__init__.py`

Modify the `create_app()` function:

```python
import os
import secrets

def create_app():
    app = Flask(__name__)

    # Secret key configuration
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        if os.environ.get('APP_ENV') == 'production':
            app.logger.warning(
                "SECRET_KEY not set in production! "
                "Sessions will not persist across restarts."
            )
        secret_key = secrets.token_hex(32)

    app.config['SECRET_KEY'] = secret_key

    # ... rest of the function
```

---

### 2.4 Create System State Module

**File**: `src/web_app/system_state.py` (NEW FILE)

```python
"""
System state detection for first-run and demo mode handling.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Optional
import sqlite3


class SystemState(Enum):
    """Possible system states."""
    FIRST_RUN = "first_run"      # No data, fresh installation
    DEMO_MODE = "demo_mode"      # Running with demo data
    USER_DATA = "user_data"      # Real user data loaded
    MIXED_MODE = "mixed_mode"    # Demo data + some user data


class SystemStateManager:
    """Manages system state detection and transitions."""

    def __init__(self, data_dir: Optional[str] = None, db_path: Optional[str] = None):
        self.data_dir = Path(data_dir or os.environ.get('DATA_DIR', 'data'))
        self.db_path = Path(db_path or os.environ.get('DB_PATH', 'data/investment_system.db'))
        self.user_uploads_dir = self.data_dir / 'user_uploads'
        self.demo_data_dir = self.data_dir / 'demo_source'

        # Cache state
        self._cached_state: Optional[SystemState] = None

    def detect_state(self, force_refresh: bool = False) -> SystemState:
        """
        Detect current system state.

        Returns:
            SystemState enum value
        """
        # Check environment override
        env_state = os.environ.get('SYSTEM_STATE')
        if env_state:
            try:
                return SystemState(env_state)
            except ValueError:
                pass

        # Check demo mode flag
        if os.environ.get('DEMO_MODE', 'false').lower() == 'true':
            return SystemState.DEMO_MODE

        # Return cached if available
        if self._cached_state and not force_refresh:
            return self._cached_state

        # Detect based on data
        has_user_data = self._has_user_data()
        has_db_data = self._has_database_data()

        if has_user_data or has_db_data:
            self._cached_state = SystemState.USER_DATA
        else:
            self._cached_state = SystemState.FIRST_RUN

        return self._cached_state

    def _has_user_data(self) -> bool:
        """Check if user has uploaded any data files."""
        if not self.user_uploads_dir.exists():
            return False

        data_files = list(self.user_uploads_dir.glob('*.csv')) + \
                     list(self.user_uploads_dir.glob('*.xlsx')) + \
                     list(self.user_uploads_dir.glob('*.xls'))

        return len(data_files) > 0

    def _has_database_data(self) -> bool:
        """Check if database has user transactions."""
        if not self.db_path.exists():
            return False

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Check if transactions table exists and has data
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master
                WHERE type='table' AND name='transactions'
            """)
            has_table = cursor.fetchone()[0] > 0

            if has_table:
                cursor.execute("SELECT COUNT(*) FROM transactions LIMIT 1")
                has_data = cursor.fetchone()[0] > 0
            else:
                has_data = False

            conn.close()
            return has_data

        except Exception:
            return False

    def is_first_run(self) -> bool:
        """Check if this is the first run."""
        return self.detect_state() == SystemState.FIRST_RUN

    def is_demo_mode(self) -> bool:
        """Check if running in demo mode."""
        return self.detect_state() == SystemState.DEMO_MODE

    def enable_demo_mode(self):
        """Enable demo mode."""
        os.environ['DEMO_MODE'] = 'true'
        self._cached_state = SystemState.DEMO_MODE

    def disable_demo_mode(self):
        """Disable demo mode."""
        os.environ['DEMO_MODE'] = 'false'
        self._cached_state = None  # Force re-detection


# Global instance
_state_manager: Optional[SystemStateManager] = None


def get_state_manager() -> SystemStateManager:
    """Get or create the global state manager."""
    global _state_manager
    if _state_manager is None:
        _state_manager = SystemStateManager()
    return _state_manager


def get_system_state() -> SystemState:
    """Get current system state."""
    return get_state_manager().detect_state()


def is_first_run() -> bool:
    """Check if this is first run."""
    return get_state_manager().is_first_run()


def is_demo_mode() -> bool:
    """Check if in demo mode."""
    return get_state_manager().is_demo_mode()
```

---

### 2.5 Integrate State Detection in App Factory

**File**: `src/web_app/__init__.py`

Add to `create_app()`:

```python
from src.web_app.system_state import get_system_state, SystemState

def create_app():
    # ... existing setup ...

    # Add system state to app config
    with app.app_context():
        state = get_system_state()
        app.config['SYSTEM_STATE'] = state
        app.logger.info(f"System state: {state.value}")

    # Add state to template context
    @app.context_processor
    def inject_system_state():
        from src.web_app.system_state import get_system_state, is_demo_mode
        return {
            'system_state': get_system_state().value,
            'is_demo_mode': is_demo_mode(),
        }

    # ... rest of the function ...
```

---

## Phase 3: First-Run Onboarding

### 3.1 Create Onboarding Blueprint

**Directory Structure**:

```
src/web_app/blueprints/onboarding/
├── __init__.py
├── routes.py
└── forms.py
```

**File**: `src/web_app/blueprints/onboarding/__init__.py`

```python
from flask import Blueprint

bp = Blueprint('onboarding', __name__, url_prefix='/onboarding')

from src.web_app.blueprints.onboarding import routes
```

**File**: `src/web_app/blueprints/onboarding/routes.py`

```python
"""
Onboarding routes for first-run experience.
"""

import os
from pathlib import Path
from flask import (
    render_template, redirect, url_for, request,
    flash, current_app, session, jsonify
)
from werkzeug.utils import secure_filename

from src.web_app.blueprints.onboarding import bp
from src.web_app.system_state import (
    get_state_manager, SystemState, is_first_run
)


ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/')
def index():
    """Onboarding landing page."""
    # Skip if already has data
    if not is_first_run():
        return redirect(url_for('dashboard.index'))

    return render_template('onboarding/welcome.html')


@bp.route('/demo', methods=['POST'])
def enable_demo():
    """Enable demo mode and redirect to dashboard."""
    state_manager = get_state_manager()
    state_manager.enable_demo_mode()

    flash('Demo mode enabled! Explore with sample data.', 'success')
    return redirect(url_for('dashboard.index'))


@bp.route('/upload')
def upload():
    """CSV upload page."""
    return render_template('onboarding/upload.html')


@bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload."""
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        # Get upload directory
        data_dir = Path(os.environ.get('DATA_DIR', 'data'))
        upload_dir = data_dir / 'user_uploads'
        upload_dir.mkdir(parents=True, exist_ok=True)

        filepath = upload_dir / filename
        file.save(str(filepath))

        # Store in session for mapping step
        session['uploaded_file'] = str(filepath)
        session['original_filename'] = file.filename

        flash(f'File uploaded: {filename}', 'success')
        return redirect(url_for('onboarding.mapping'))

    flash('Invalid file type. Please upload CSV or Excel files.', 'error')
    return redirect(request.url)


@bp.route('/mapping')
def mapping():
    """Column mapping page."""
    filepath = session.get('uploaded_file')

    if not filepath or not Path(filepath).exists():
        flash('Please upload a file first', 'error')
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
        flash(f'Error reading file: {str(e)}', 'error')
        return redirect(url_for('onboarding.upload'))

    return render_template(
        'onboarding/mapping.html',
        columns=columns,
        preview=preview,
        filename=session.get('original_filename')
    )


@bp.route('/complete', methods=['POST'])
def complete():
    """Complete onboarding and import data."""
    filepath = session.get('uploaded_file')

    if not filepath:
        flash('Session expired. Please upload again.', 'error')
        return redirect(url_for('onboarding.upload'))

    # Get column mappings from form
    mappings = {
        'date': request.form.get('date_column'),
        'description': request.form.get('description_column'),
        'amount': request.form.get('amount_column'),
        'category': request.form.get('category_column'),
    }

    # TODO: Implement actual import logic
    # from src.data_import.csv_importer import import_transactions
    # result = import_transactions(filepath, mappings)

    # Clear session
    session.pop('uploaded_file', None)
    session.pop('original_filename', None)

    # Update system state
    state_manager = get_state_manager()
    state_manager._cached_state = SystemState.USER_DATA

    flash('Data imported successfully!', 'success')
    return redirect(url_for('dashboard.index'))


@bp.route('/skip')
def skip():
    """Skip onboarding and go to empty dashboard."""
    return redirect(url_for('dashboard.index'))


@bp.route('/templates/<template_type>')
def download_template(template_type):
    """Download CSV template."""
    from flask import send_from_directory

    templates_dir = Path(current_app.root_path).parent.parent / 'templates' / 'csv_templates'

    template_files = {
        'transactions': 'transactions_template.csv',
        'holdings': 'holdings_template.csv',
        'balance_sheet': 'balance_sheet_template.csv',
    }

    filename = template_files.get(template_type)
    if not filename:
        flash('Template not found', 'error')
        return redirect(url_for('onboarding.upload'))

    return send_from_directory(
        str(templates_dir),
        filename,
        as_attachment=True
    )
```

---

### 3.2 Register Onboarding Blueprint

**File**: `src/web_app/__init__.py`

Add to blueprint registration:

```python
# Add import
from src.web_app.blueprints.onboarding import bp as onboarding_bp

# In create_app(), add:
app.register_blueprint(onboarding_bp)
```

---

### 3.3 Add First-Run Redirect Middleware

**File**: `src/web_app/__init__.py`

Add before request handler:

```python
@app.before_request
def check_first_run():
    """Redirect to onboarding if first run."""
    from src.web_app.system_state import is_first_run
    from flask import request

    # Skip for certain endpoints
    exempt_prefixes = [
        '/onboarding',
        '/static',
        '/health',
        '/api/health',
    ]

    if any(request.path.startswith(prefix) for prefix in exempt_prefixes):
        return None

    # Redirect to onboarding if first run
    if is_first_run():
        return redirect(url_for('onboarding.index'))

    return None
```

---

### 3.4 Create Onboarding Templates

**File**: `src/web_app/templates/onboarding/welcome.html`

```html
{% extends "base.html" %}

{% block title %}Welcome - Personal Investment System{% endblock %}

{% block content %}
<div class="onboarding-container">
    <div class="onboarding-hero">
        <h1>Welcome to Personal Investment System</h1>
        <p class="lead">
            Track, analyze, and optimize your investments with powerful analytics.
        </p>
    </div>

    <div class="onboarding-options">
        <div class="option-card">
            <h3>Try Demo Mode</h3>
            <p>Explore the system with sample data. No upload required.</p>
            <form action="{{ url_for('onboarding.enable_demo') }}" method="POST">
                <button type="submit" class="btn btn-primary btn-lg">
                    Start Demo
                </button>
            </form>
        </div>

        <div class="option-card">
            <h3>Upload Your Data</h3>
            <p>Import your transactions and holdings from CSV or Excel.</p>
            <a href="{{ url_for('onboarding.upload') }}" class="btn btn-secondary btn-lg">
                Upload Data
            </a>
        </div>

        <div class="option-card option-skip">
            <p>
                <a href="{{ url_for('onboarding.skip') }}">
                    Skip for now →
                </a>
            </p>
        </div>
    </div>
</div>

<style>
.onboarding-container {
    max-width: 800px;
    margin: 4rem auto;
    padding: 2rem;
    text-align: center;
}

.onboarding-hero {
    margin-bottom: 3rem;
}

.onboarding-hero h1 {
    font-size: 2.5rem;
    margin-bottom: 1rem;
}

.onboarding-options {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
    margin-bottom: 2rem;
}

.option-card {
    background: var(--card-bg, #f8f9fa);
    border-radius: 8px;
    padding: 2rem;
    text-align: center;
}

.option-card h3 {
    margin-bottom: 1rem;
}

.option-skip {
    grid-column: span 2;
    background: none;
    padding: 1rem;
}

@media (max-width: 600px) {
    .onboarding-options {
        grid-template-columns: 1fr;
    }
    .option-skip {
        grid-column: span 1;
    }
}
</style>
{% endblock %}
```

**File**: `src/web_app/templates/onboarding/upload.html`

```html
{% extends "base.html" %}

{% block title %}Upload Data - Personal Investment System{% endblock %}

{% block content %}
<div class="upload-container">
    <h1>Upload Your Data</h1>
    <p class="lead">Import transactions from CSV or Excel files.</p>

    <div class="templates-section">
        <h3>Download Templates</h3>
        <p>Not sure about the format? Download our templates:</p>
        <div class="template-buttons">
            <a href="{{ url_for('onboarding.download_template', template_type='transactions') }}"
               class="btn btn-outline">
                Transactions Template
            </a>
            <a href="{{ url_for('onboarding.download_template', template_type='holdings') }}"
               class="btn btn-outline">
                Holdings Template
            </a>
        </div>
    </div>

    <div class="upload-section">
        <form action="{{ url_for('onboarding.upload_file') }}"
              method="POST"
              enctype="multipart/form-data"
              class="upload-form">

            <div class="dropzone" id="dropzone">
                <input type="file"
                       name="file"
                       id="file-input"
                       accept=".csv,.xlsx,.xls"
                       required>
                <div class="dropzone-content">
                    <p class="dropzone-icon">📁</p>
                    <p>Drag and drop your file here</p>
                    <p>or <strong>click to browse</strong></p>
                    <p class="file-types">Supported: CSV, Excel (.xlsx, .xls)</p>
                </div>
            </div>

            <button type="submit" class="btn btn-primary btn-lg">
                Upload and Continue
            </button>
        </form>
    </div>

    <div class="back-link">
        <a href="{{ url_for('onboarding.index') }}">← Back to options</a>
    </div>
</div>

<style>
.upload-container {
    max-width: 600px;
    margin: 2rem auto;
    padding: 2rem;
}

.templates-section {
    background: var(--card-bg, #f8f9fa);
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 2rem;
}

.template-buttons {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
}

.dropzone {
    border: 2px dashed #ccc;
    border-radius: 8px;
    padding: 3rem 2rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
    margin-bottom: 1.5rem;
}

.dropzone:hover, .dropzone.dragover {
    border-color: var(--primary-color, #007bff);
    background: rgba(0, 123, 255, 0.05);
}

.dropzone input[type="file"] {
    display: none;
}

.dropzone-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.file-types {
    font-size: 0.875rem;
    color: #666;
    margin-top: 1rem;
}

.back-link {
    margin-top: 2rem;
    text-align: center;
}
</style>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');

    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            // Update UI to show selected file
            dropzone.querySelector('.dropzone-content').innerHTML = `
                <p class="dropzone-icon">✓</p>
                <p><strong>${files[0].name}</strong></p>
                <p>Ready to upload</p>
            `;
        }
    });
});
</script>
{% endblock %}
```

---

### 3.5 Create CSV Templates

**Directory**: `templates/csv_templates/`

**File**: `templates/csv_templates/transactions_template.csv`

```csv
Date,Description,Amount,Category,Account,Notes
2024-01-15,Stock Purchase - AAPL,-1500.00,Investment,Brokerage,Buy 10 shares
2024-01-20,Dividend - VTI,45.23,Income,Brokerage,Quarterly dividend
2024-02-01,401k Contribution,-500.00,Retirement,401k,Monthly contribution
2024-02-15,Salary Deposit,5000.00,Income,Checking,Monthly salary
```

**File**: `templates/csv_templates/holdings_template.csv`

```csv
Symbol,Name,Quantity,Cost Basis,Current Price,Account,Asset Type
AAPL,Apple Inc,50,7500.00,185.50,Brokerage,US Stock
VTI,Vanguard Total Stock Market,100,20000.00,225.30,IRA,ETF
BTC,Bitcoin,0.5,15000.00,42000.00,Crypto Wallet,Cryptocurrency
```

---

## Phase 4: Demo Mode Banner

### 4.1 Add Demo Mode Banner Component

**File**: `src/web_app/templates/base.html`

Add after `<body>` tag:

```html
{% if is_demo_mode %}
<div class="demo-banner" id="demo-banner">
    <div class="demo-banner-content">
        <span class="demo-badge">DEMO MODE</span>
        <span class="demo-text">You're exploring with sample data.</span>
        <a href="{{ url_for('onboarding.upload') }}" class="demo-cta">
            Upload Your Data
        </a>
        <button class="demo-dismiss" onclick="dismissDemoBanner()">×</button>
    </div>
</div>

<style>
.demo-banner {
    background: linear-gradient(90deg, #ffc107, #ff9800);
    color: #000;
    padding: 0.5rem 1rem;
    text-align: center;
    position: sticky;
    top: 0;
    z-index: 1000;
}

.demo-banner-content {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    flex-wrap: wrap;
}

.demo-badge {
    background: #000;
    color: #ffc107;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-weight: bold;
    font-size: 0.75rem;
}

.demo-cta {
    background: #000;
    color: #fff;
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    text-decoration: none;
}

.demo-cta:hover {
    background: #333;
}

.demo-dismiss {
    background: none;
    border: none;
    font-size: 1.25rem;
    cursor: pointer;
    padding: 0 0.5rem;
}
</style>

<script>
function dismissDemoBanner() {
    document.getElementById('demo-banner').style.display = 'none';
    sessionStorage.setItem('demoBannerDismissed', 'true');
}

if (sessionStorage.getItem('demoBannerDismissed') === 'true') {
    document.getElementById('demo-banner').style.display = 'none';
}
</script>
{% endif %}
```

---

## Testing Checklist

### Docker Build Tests

```bash
# Build image
docker build -t pis:test .

# Check image size (should be <500MB)
docker images pis:test

# Run container
docker run -d -p 5000:5000 --name pis-test pis:test

# Check health
curl http://localhost:5000/health

# Check logs
docker logs pis-test

# Clean up
docker rm -f pis-test
```

### First-Run Flow Tests

1. **Fresh Install → Demo Mode**
   - Remove all data volumes
   - `docker-compose up -d`
   - Access `http://localhost:5000`
   - Should redirect to onboarding
   - Click "Try Demo Mode"
   - Should show dashboard with demo data

2. **Fresh Install → CSV Upload**
   - Remove all data volumes
   - `docker-compose up -d`
   - Access `http://localhost:5000`
   - Click "Upload Your Data"
   - Upload test CSV
   - Complete mapping
   - Should show dashboard with imported data

3. **Data Persistence**
   - `docker-compose down`
   - `docker-compose up -d`
   - Data should persist

### Performance Tests

```bash
# Measure startup time
time docker-compose up -d

# Memory usage
docker stats pis-web --no-stream

# Response time
ab -n 100 -c 10 http://localhost:5000/health
```

---

## Deployment Commands

### Production Deployment

```bash
# Clone repository
git clone https://github.com/yourusername/personal-investment-system.git
cd personal-investment-system

# Create environment file
cat > .env << EOF
SECRET_KEY=$(openssl rand -hex 32)
APP_ENV=production
TZ=America/New_York
EOF

# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Update to latest
docker-compose pull
docker-compose up -d
```

### Development Mode

```bash
# Build with no cache
docker-compose build --no-cache

# Run with mounted source for live reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Port 5000 in use | Change `PIS_PORT=8080` |
| Permission denied on volumes | Check Docker volume permissions |
| Database locked | Only run one container instance |
| Import fails | Check CSV encoding (UTF-8) |
| Health check failing | Wait for startup (60s) |

### Debug Mode

```bash
# Run with debug output
docker-compose run --rm -e FLASK_DEBUG=true pis-web

# Shell into container
docker-compose exec pis-web /bin/bash

# View database
docker-compose exec pis-web sqlite3 /app/data/investment_system.db ".tables"
```

---

## Phase 8: Verification & Fixes

### 8.1 Entrypoint Logic Fix

**File**: `/docker-entrypoint.sh`

Cleaned up state detection logic to prevent false positives for "User Data" state.

```bash
# Before: Exported SYSTEM_STATE based on table count (unreliable)
# After: Only logs state for info; delegates logic to Python app
if [ "$DEMO_MODE" = "true" ]; then
    echo "[INFO] Demo mode enabled via environment"
    STATE_LOG="demo_mode"
elif [ "$USER_DATA_COUNT" -gt 0 ] || [ "$DB_TABLES" -gt 5 ]; then
    echo "[INFO] User data/schema detected"
    STATE_LOG="user_data"
else
    STATE_LOG="first_run"
fi
```

### 8.2 First-Run Redirect Fix

**File**: `src/web_app/blueprints/main/routes.py`

Modified the root index route to prioritize first-run detection over authentication.

```python
@main_bp.route('/')
def index():
    # Check first-run BEFORE login check
    if is_first_run():
        return redirect(url_for('onboarding.index'))
    
    # Then force login for normal use
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login', next=request.url))
    
    return render_template('dashboard/index.html')
```

### 8.3 Demo Mode Auto-Login

**Files**: `src/web_app/blueprints/onboarding/routes.py`, `src/web_app/auth_manager.py`

Implemented seamless transition to dashboard when enabling demo mode.

1. **Auth Manager**: Updated `load_user` to accept 'demo' user when in Demo Mode.
2. **Onboarding Route**: Auto-login 'demo' user upon activation.

```python
# src/web_app/blueprints/onboarding/routes.py
@bp.route('/demo', methods=['POST'])
def enable_demo():
    state_manager.enable_demo_mode()
    
    # Auto-login demo user
    user = User('demo')
    login_user(user) # Flask-Login integration

    return redirect(url_for('main.index'))
```
