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
    python main.py init-database 2>/dev/null || {
        echo "[WARN] Database initialization command not available or failed"
        echo "[INFO] Database will be created on first access"
    }
    if [ -f "$DB_PATH" ]; then
        echo "[INFO] Database initialized at $DB_PATH"
    fi
else
    echo "[INFO] Database found at $DB_PATH"
fi

# -----------------------------------------------------------------------------
# First-Run Detection
# -----------------------------------------------------------------------------

echo "[INFO] Checking system state..."

# Check if user has uploaded any data
USER_DATA_COUNT=$(find "$DATA_DIR/user_uploads" -type f \( -name "*.csv" -o -name "*.xlsx" -o -name "*.xls" \) 2>/dev/null | wc -l | tr -d ' ')

# Check database has transactions
if [ -f "$DB_PATH" ]; then
    DB_TABLES=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='table';" 2>/dev/null || echo "0")
else
    DB_TABLES="0"
fi

if [ "$DEMO_MODE" = "true" ]; then
    echo "[INFO] Demo mode enabled via environment"
    STATE_LOG="demo_mode"
elif [ "$USER_DATA_COUNT" -gt 0 ] || [ "$DB_TABLES" -gt 5 ]; then
    echo "[INFO] User data/schema detected"
    STATE_LOG="user_data"
else
    echo "[INFO] Start conditions check - First run potential"
    STATE_LOG="first_run"
fi

echo "[INFO] Preliminary state check: $STATE_LOG"

# -----------------------------------------------------------------------------
# Demo Data Check
# -----------------------------------------------------------------------------

if [ "$STATE_LOG" = "first_run" ] || [ "$STATE_LOG" = "demo_mode" ]; then
    if [ -d "/app/data/demo_source" ] && [ "$(ls -A /app/data/demo_source 2>/dev/null)" ]; then
        echo "[INFO] Demo data available at /app/data/demo_source"
    else
        echo "[WARN] Demo data directory not found or empty"
    fi
fi

# -----------------------------------------------------------------------------
# Configuration Check
# -----------------------------------------------------------------------------

if [ -f "/app/config/settings.yaml" ]; then
    echo "[INFO] Configuration found at /app/config/settings.yaml"
else
    echo "[WARN] Configuration file not found - using defaults"
fi

# -----------------------------------------------------------------------------
# Launch Application
# -----------------------------------------------------------------------------

echo "=========================================="
echo "[INFO] Starting application..."
echo "[INFO] Web interface will be available at http://0.0.0.0:${FLASK_PORT:-5000}"
echo "=========================================="

# Execute the CMD passed to the container
exec "$@"
