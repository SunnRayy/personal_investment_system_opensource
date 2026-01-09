# =============================================================================
# Personal Investment System - Docker Image
# Multi-stage build for optimized image size
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies and compile wheels
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS builder

# Install build dependencies for scipy, numpy, and other compiled packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    pkg-config \
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
    sqlite3 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1000 appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories with correct permissions
RUN mkdir -p /app/data/user_uploads \
             /app/data/cache \
             /app/data/cost_basis_lots \
             /app/data/historical_snapshots \
             /app/logs \
             /app/output && \
    chown -R appuser:appuser /app/data /app/logs /app/output

# Copy and set up entrypoint script
COPY --chown=appuser:appuser docker/entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Switch to non-root user
USER appuser

# Environment variables
ENV FLASK_HOST=0.0.0.0 \
    FLASK_PORT=5000 \
    APP_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATA_DIR=/app/data \
    DB_PATH=/app/data/investment_system.db

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]

# Default command
CMD ["python", "main.py", "run-web", "--host", "0.0.0.0", "--port", "5000"]
