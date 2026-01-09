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

### Phase 1: Docker Infrastructure Setup
**Priority**: Critical | **Estimated Complexity**: Medium

- [ ] **1.1** Create `Dockerfile` with multi-stage build
  - Base: Python 3.11-slim
  - Install system dependencies (build-essential for scipy/numpy)
  - Copy and install requirements.txt
  - Copy application code
  - Set working directory and entrypoint

- [ ] **1.2** Create `docker-compose.yml`
  - Single service: `pis-web`
  - Volume mounts for persistent data
  - Environment variable configuration
  - Health check configuration
  - Restart policy

- [ ] **1.3** Create `.dockerignore`
  - Exclude: `.git`, `__pycache__`, `*.pyc`, `.env`, `logs/*`, `output/*`
  - Include only necessary runtime files

- [ ] **1.4** Create `docker-entrypoint.sh`
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

### Phase 2: Application Modifications for Docker Compatibility
**Priority**: Critical | **Estimated Complexity**: Medium

- [ ] **2.1** Modify Flask host binding
  - File: `src/web_app/__init__.py` and `main.py`
  - Change default host from `127.0.0.1` to `0.0.0.0`
  - Make configurable via `FLASK_HOST` environment variable

- [ ] **2.2** Environment-based configuration
  - Create `config/settings.docker.yaml` template
  - Support `CONFIG_PATH` environment variable override
  - Document all environment variables

- [ ] **2.3** Database path containerization
  - Ensure `DB_PATH` environment variable is respected
  - Default to `/app/data/investment_system.db` in container
  - Auto-create database directory if not exists

- [ ] **2.4** Logging configuration for containers
  - Support `LOG_LEVEL` environment variable
  - Option to log to stdout (Docker best practice)
  - Retain file logging option for debugging

- [ ] **2.5** Secret key management
  - Remove hardcoded `'dev-secret-key-change-in-production'`
  - Require `SECRET_KEY` environment variable in production
  - Auto-generate if not provided (with warning)

**Files to Modify**:
- `src/web_app/__init__.py`
- `main.py`
- `src/data_manager/manager.py`

---

### Phase 3: First-Run Detection & Demo Mode
**Priority**: Critical | **Estimated Complexity**: High

- [ ] **3.1** Create `src/web_app/first_run.py` module
  - `detect_first_run()`: Check if system has user data
  - `is_demo_mode()`: Check if running in demo mode
  - `get_system_state()`: Return current state enum

- [ ] **3.2** Define system states
  ```python
  class SystemState(Enum):
      FIRST_RUN = "first_run"       # No data, no demo
      DEMO_MODE = "demo_mode"       # Using demo data
      USER_DATA = "user_data"       # Real user data loaded
      MIXED_MODE = "mixed_mode"     # Demo + some user data
  ```

- [ ] **3.3** First-run detection logic
  - Check: `data/investment_system.db` exists and has transactions?
  - Check: Any CSV/Excel files in `data/user_uploads/`?
  - Check: `DEMO_MODE` environment variable set?
  - Store state in session/application context

- [ ] **3.4** Demo data management
  - Keep `data/demo_source/` as read-only demo data
  - Create `data/user_uploads/` for user CSV files
  - Flag to easily switch between demo and user data

**New Files**:
- `src/web_app/first_run.py`
- `src/web_app/system_state.py`

---

### Phase 4: Onboarding UI & CSV Upload Flow
**Priority**: High | **Estimated Complexity**: High

- [ ] **4.1** Create onboarding blueprint
  - Route: `/onboarding/` or `/setup/`
  - Redirect from root if `FIRST_RUN` state
  - Multi-step wizard interface

- [ ] **4.2** Onboarding Step 1: Welcome & Mode Selection
  - Option A: "Try Demo Mode" - Load demo data
  - Option B: "Upload My Data" - Go to CSV upload
  - Option C: "I'll configure later" - Skip to empty dashboard

- [ ] **4.3** Onboarding Step 2: CSV Upload Interface
  - Drag-and-drop file upload
  - Supported formats: CSV, Excel (.xlsx, .xls)
  - Template downloads for each data type
  - Real-time validation preview

- [ ] **4.4** Onboarding Step 3: Data Mapping
  - Auto-detect column mappings
  - Allow manual column assignment
  - Preview imported data
  - Validate required fields

- [ ] **4.5** Onboarding Step 4: Confirmation
  - Summary of imported data
  - Run initial analysis
  - Redirect to dashboard

- [ ] **4.6** Create CSV templates
  - `templates/csv_templates/transactions_template.csv`
  - `templates/csv_templates/holdings_template.csv`
  - `templates/csv_templates/balance_sheet_template.csv`
  - Include example rows with comments

**New Files**:
- `src/web_app/blueprints/onboarding/`
  - `__init__.py`
  - `routes.py`
  - `forms.py`
  - `validators.py`
- `src/web_app/templates/onboarding/`
  - `welcome.html`
  - `upload.html`
  - `mapping.html`
  - `confirmation.html`
- `templates/csv_templates/*.csv`

---

### Phase 5: Data Import Engine Enhancement
**Priority**: High | **Estimated Complexity**: Medium

- [ ] **5.1** Create unified import interface
  - File: `src/data_import/csv_importer.py`
  - Support multiple CSV formats
  - Auto-detect delimiter, encoding
  - Handle date format variations

- [ ] **5.2** Transaction import logic
  - Map to standard transaction schema
  - Validate amounts, dates, accounts
  - Handle duplicates (skip or merge)

- [ ] **5.3** Holdings import logic
  - Map to asset holdings schema
  - Lookup/create assets as needed
  - Calculate cost basis if provided

- [ ] **5.4** Import progress tracking
  - WebSocket for real-time progress
  - Store import history in database
  - Rollback capability on errors

- [ ] **5.5** Error handling and reporting
  - Row-level validation errors
  - Batch import summary
  - Downloadable error report

**New/Modified Files**:
- `src/data_import/csv_importer.py`
- `src/data_import/validators.py`
- `src/database/models/import_log.py` (exists, enhance)

---

### Phase 6: User Experience Polish
**Priority**: Medium | **Estimated Complexity**: Low

- [ ] **6.1** Demo mode banner
  - Persistent banner when in demo mode
  - "Exit Demo" / "Upload Your Data" CTA
  - Dismissible but returns on next visit

- [ ] **6.2** Empty state designs
  - Dashboard with no data: Show helpful guidance
  - Reports with no data: Explain what's needed
  - Consistent empty state illustrations

- [ ] **6.3** Progress indicators
  - Data import progress bar
  - Analysis generation progress
  - Loading states for all operations

- [ ] **6.4** Error pages
  - Custom 404, 500 error pages
  - Helpful error messages with next steps
  - Contact/support information

- [ ] **6.5** Mobile responsiveness check
  - Ensure onboarding works on mobile
  - Test file upload on mobile browsers

**Files to Modify**:
- `src/web_app/templates/base.html`
- `src/web_app/static/css/main.css`
- Various template files

---

### Phase 7: Documentation & User Guides
**Priority**: Medium | **Estimated Complexity**: Low

- [ ] **7.1** Create `DOCKER_QUICKSTART.md`
  - Prerequisites (Docker, Docker Compose)
  - One-command installation
  - Accessing the web interface
  - Troubleshooting common issues

- [ ] **7.2** Create `docs/csv-formats.md`
  - Detailed CSV format specifications
  - Required vs optional columns
  - Date format requirements
  - Example files

- [ ] **7.3** Update `README.md`
  - Add Docker deployment section
  - Quick start with Docker badge
  - Link to detailed docs

- [ ] **7.4** In-app help
  - Tooltip explanations
  - Link to documentation
  - FAQ section

**New Files**:
- `DOCKER_QUICKSTART.md`
- `docs/csv-formats.md`
- Update `README.md`

---

### Phase 8: Testing & Validation
**Priority**: High | **Estimated Complexity**: Medium

- [ ] **8.1** Docker build testing
  - Test on clean Docker environment
  - Verify image size optimization
  - Test multi-architecture build (amd64, arm64)

- [ ] **8.2** First-run flow testing
  - Test fresh install → demo mode
  - Test fresh install → CSV upload
  - Test data persistence across restarts

- [ ] **8.3** CSV import testing
  - Various CSV formats
  - Large file handling (>10MB)
  - Error scenarios

- [ ] **8.4** Integration testing
  - End-to-end onboarding flow
  - Demo mode to user data transition
  - Data integrity after import

- [ ] **8.5** Performance testing
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
| *TBD* | 1 | Not started | Create Dockerfile |

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

- Flask Docker deployment: https://flask.palletsprojects.com/en/2.3.x/deploying/
- Docker multi-stage builds: https://docs.docker.com/build/building/multi-stage/
- Docker Compose best practices: https://docs.docker.com/compose/compose-file/
