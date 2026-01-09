# Feature: Docker One-Click Deployment & Zero-Configuration Startup

## Overview

**Goal**: Enable non-technical users to deploy and run the Personal Investment System with a single command (`docker-compose up -d`), eliminating all environment configuration barriers.

**Pain Point Addressed**: Python dependencies, database migrations, Excel path configuration, and environment setup currently prevent 90%+ of users from successfully deploying the system.

**Success Criteria**:

- User runs `docker-compose up -d` → System is accessible at `http://localhost:5000`
- No prior Python, database, or configuration knowledge required
- System auto-detects empty state and provides guided onboarding
- Demo mode available for exploration without real data

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    docker-compose.yml                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐    ┌─────────────────────────────────┐ │
│  │   pis-web (Flask)   │    │        Volumes                  │ │
│  │   Port: 5000        │◄──►│  - ./data:/app/data             │ │
│  │   Python 3.11       │    │  - ./config:/app/config         │ │
│  │   Auto-init DB      │    │  - ./output:/app/output         │ │
│  └─────────────────────┘    │  - ./logs:/app/logs             │ │
│                             └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  First-Run Flow │
                    ├─────────────────┤
                    │ 1. Check data   │
                    │ 2. Demo mode?   │
                    │ 3. CSV upload?  │
                    │ 4. Init DB      │
                    └─────────────────┘
```

---

## Implementation Phases

### Phase 1: Docker Infrastructure Setup ✅ COMPLETED

**Priority**: Critical | **Estimated Complexity**: Medium

- [x] **1.1** Create `Dockerfile` with multi-stage build
  - Base: Python 3.11-slim
  - Install system dependencies (build-essential for scipy/numpy)
  - Copy and install requirements.txt
  - Copy application code
  - Set working directory and entrypoint

- [x] **1.2** Create `docker-compose.yml`
  - Single service: `pis-web`
  - Volume mounts for persistent data
  - Environment variable configuration
  - Health check configuration
  - Restart policy

- [x] **1.3** Create `.dockerignore`
  - Exclude: `.git`, `__pycache__`, `*.pyc`, `.env`, `logs/*`, `output/*`
  - Include only necessary runtime files

- [x] **1.4** Create `docker-entrypoint.sh`
  - Initialize database if not exists
  - Run migrations if needed
  - Check data state and set mode
  - Launch Flask application

**Deliverables**:

- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- `docker-entrypoint.sh`

---

### Phase 2: Application Modifications for Docker Compatibility ✅ COMPLETED

**Priority**: Critical | **Estimated Complexity**: Medium

- [x] **2.1** Modify Flask host binding
  - File: `src/web_app/__init__.py` and `main.py`
  - Change default host from `127.0.0.1` to `0.0.0.0`
  - Make configurable via `FLASK_HOST` environment variable

- [x] **2.2** Environment-based configuration
  - Create `config/settings.docker.yaml` template
  - Support `CONFIG_PATH` environment variable override
  - Document all environment variables

- [x] **2.3** Database path containerization
  - Ensure `DB_PATH` environment variable is respected
  - Default to `/app/data/investment_system.db` in container
  - Auto-create database directory if not exists

- [x] **2.4** Logging configuration for containers
  - Support `LOG_LEVEL` environment variable
  - Option to log to stdout (Docker best practice)
  - Retain file logging option for debugging

- [x] **2.5** Secret key management
  - Remove hardcoded `'dev-secret-key-change-in-production'`
  - Require `SECRET_KEY` environment variable in production
  - Auto-generate if not provided (with warning)

- [x] **2.6** System state detection module (NEW)
  - Created `src/web_app/system_state.py`
  - `SystemState` enum (FIRST_RUN, DEMO_MODE, USER_DATA, MIXED_MODE)
  - `SystemStateManager` class with detection logic
  - Context processor integration in Flask app factory
  - First-run redirect middleware (prepared for Phase 3)

**Files Modified**:

- `src/web_app/__init__.py`
- `main.py`
- `src/web_app/system_state.py` (NEW)

---

### Phase 3: First-Run Detection & Demo Mode ✅ COMPLETED

**Priority**: Critical | **Estimated Complexity**: High

- [x] **3.1** System state detection (implemented in Phase 2 as `system_state.py`)
- [x] **3.2** Onboarding blueprint created
  - Routes: `/onboarding/`, `/onboarding/demo`, `/onboarding/upload`, `/onboarding/mapping`, `/onboarding/complete`
  - First-run redirect middleware active
- [x] **3.3** First-run detection logic
  - Environment variable override (`DEMO_MODE`)
  - User uploads directory check
  - Database transaction check
- [x] **3.4** Demo data management
  - Demo data served from `data/demo_source/`
  - User uploads to `data/user_uploads/`

**New Files Created**:

- `src/web_app/blueprints/onboarding/__init__.py`
- `src/web_app/blueprints/onboarding/routes.py`
- `src/web_app/templates/onboarding/welcome.html`
- `src/web_app/templates/onboarding/upload.html`
- `src/web_app/templates/onboarding/mapping.html`

---

### Phase 4: Onboarding UI & CSV Upload Flow ✅ COMPLETED

**Priority**: High | **Estimated Complexity**: High

- [x] **4.1** Onboarding blueprint with first-run redirect
- [x] **4.2** Welcome page with Demo/Upload/Skip options
- [x] **4.3** File upload with drag-and-drop interface
- [x] **4.4** Column mapping with data preview
- [x] **4.5** Import completion flow
- [x] **4.6** CSV templates created

**Files Created**:

- `templates/csv_templates/transactions_template.csv`
- `templates/csv_templates/holdings_template.csv`
- `templates/csv_templates/balance_sheet_template.csv`

---

### Phase 5: Data Import Engine Enhancement ✅ COMPLETED

**Priority**: High | **Estimated Complexity**: Medium

- [x] **5.1** Created unified import interface
  - File: `src/data_import/csv_importer.py`
  - Auto-detect delimiter and encoding
  - Auto-detect column mappings
- [x] **5.2** Data validation and transformation
  - Validate dates and amounts
  - Clean currency symbols and formatting
- [x] **5.3** ImportResult dataclass for error reporting

**New Files Created**:

- `src/data_import/__init__.py`
- `src/data_import/csv_importer.py`

---

### Phase 6: User Experience Polish ✅ COMPLETED

**Priority**: Medium | **Estimated Complexity**: Low

- [x] **6.1** Demo mode banner
  - Added to `base.html`
  - Dismissible with session storage
  - CTA to upload user data
- [x] **6.2** Custom error pages
  - Created `errors/404.html`
  - Created `errors/500.html`
- [x] **6.3** Error handlers registered in Flask app

**Files Modified**:

- `src/web_app/templates/base.html`
- `src/web_app/__init__.py`

**Files Created**:

- `src/web_app/templates/errors/404.html`

---

### Phase 7: Documentation & User Guides ✅ COMPLETED

**Priority**: Medium | **Estimated Complexity**: Low

- [x] **7.1** `DOCKER_QUICKSTART.md` already comprehensive
- [x] **7.2** Created `docs/csv-formats.md`
- [x] **7.3** Task plan and implementation docs updated

**Documentation Files**:

- `DOCKER_QUICKSTART.md`
- `docs/csv-formats.md`
- `docs/docker-deployment/task_plan.md`
- `docs/docker-deployment/implementation.md`

---

### Phase 8: Testing & Validation ✅ COMPLETED

**Priority**: High | **Estimated Complexity**: Medium

- [x] **8.1** Docker build testing
  - Test on clean Docker environment
  - Verify image size optimization
  - Test multi-architecture build (amd64, arm64)

- [x] **8.2** First-run flow testing
  - Test fresh install → demo mode
  - Test fresh install → CSV upload
  - Test data persistence across restarts

- [x] **8.3** CSV import testing
  - Various CSV formats
  - Large file handling (>10MB)
  - Error scenarios

- [x] **8.4** Integration testing
  - End-to-end onboarding flow
  - Demo mode to user data transition
  - Data integrity after import

- [x] **8.5** Performance testing
  - Container startup time (target: <30s)
  - Memory usage under load
  - Database performance

**Test Files**:

- `tests/docker/`
- `tests/integration/test_onboarding.py`
- `tests/integration/test_csv_import.py`

---

## Progress Log

| Date | Phase | Progress | Next Steps |
|------|-------|----------|------------|
| 2026-01-09 | 1 | ✅ Completed: Dockerfile, docker-compose.yml, .dockerignore, docker-entrypoint.sh | Start Phase 2 |
| 2026-01-09 | 2 | ✅ Completed: Flask host binding, secret key, system_state.py, context processors | Start Phase 3 |
| 2026-01-09 | 3 | ✅ Completed: Onboarding blueprint, first-run redirect, templates | Start Phase 4 |
| 2026-01-09 | 4 | ✅ Completed: Welcome/Upload/Mapping pages, CSV templates | Start Phase 5 |
| 2026-01-09 | 5 | ✅ Completed: CSVImporter with auto-detection and validation | Start Phase 6 |
| 2026-01-09 | 6 | ✅ Completed: Demo mode banner, custom error pages | Start Phase 7 |
| 2026-01-09 | 7 | ✅ Completed: csv-formats.md documentation | Phase 8 (Testing) |
| 2026-01-09 | 8 | ✅ Completed: End-to-end verification, entrypoint fix, auto-login | Feature Complete |

---

## Technical Specifications

### Dockerfile Specifications

```dockerfile
# Target image size: <500MB
# Base image: python:3.11-slim-bookworm
# Build stages: 2 (builder + runtime)
# Health check: HTTP GET /health
# Default port: 5000
# User: non-root (appuser)
```

### docker-compose.yml Specifications

```yaml
# Version: 3.8+
# Services: 1 (pis-web)
# Volumes: 4 (data, config, logs, output)
# Networks: 1 (default bridge)
# Restart policy: unless-stopped
# Health check: enabled
# Resource limits: optional
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Prod | auto-gen | Flask secret key |
| `FLASK_HOST` | No | 0.0.0.0 | Host binding |
| `FLASK_PORT` | No | 5000 | Port number |
| `DB_PATH` | No | /app/data/investment_system.db | Database path |
| `DATA_DIR` | No | /app/data | Data directory |
| `LOG_LEVEL` | No | INFO | Logging level |
| `DEMO_MODE` | No | false | Force demo mode |
| `APP_ENV` | No | production | Environment |
| `TZ` | No | UTC | Timezone |

### Volume Mounts

| Container Path | Host Path | Purpose |
|----------------|-----------|---------|
| `/app/data` | `./data` | User data, database, cache |
| `/app/config` | `./config` | Configuration files |
| `/app/logs` | `./logs` | Application logs |
| `/app/output` | `./output` | Generated reports |

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large image size | Slow download | Multi-stage build, slim base |
| scipy/numpy build time | Long CI/CD | Pre-built wheels, caching |
| Data loss on container rebuild | High | Named volumes, backup script |
| Port conflicts | Medium | Configurable port, documentation |
| ARM64 compatibility | Medium | Multi-arch build |
| File permission issues | High | Proper chmod in Dockerfile |

---

## Dependencies & Prerequisites

### External Dependencies (to be installed in Docker)

- Python 3.11+
- pip packages from `requirements.txt`
- System packages: `build-essential`, `libpq-dev` (for future PostgreSQL)

### User Prerequisites

- Docker Engine 20.10+
- Docker Compose v2.0+
- 4GB RAM minimum
- 2GB disk space

---

## Success Metrics

1. **Time to first dashboard**: < 2 minutes from `docker-compose up`
2. **Zero manual configuration**: No file editing required
3. **Successful import rate**: > 95% for standard CSV formats
4. **User retention**: > 50% complete onboarding
5. **Support tickets**: < 5% need manual intervention

---

## Open Questions

1. Should we support PostgreSQL in docker-compose for production deployments?
2. Should demo data be included in the image or downloaded on first run?
3. What's the maximum supported file size for CSV upload?
4. Should we add authentication by default or make it optional?
5. Multi-language support for onboarding (EN/ZH)?

---

## References

- Flask Docker deployment: <https://flask.palletsprojects.com/en/2.3.x/deploying/>
- Docker multi-stage builds: <https://docs.docker.com/build/building/multi-stage/>
- Docker Compose best practices: <https://docs.docker.com/compose/compose-file/>
