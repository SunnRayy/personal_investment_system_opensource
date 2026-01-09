# Research Notes: Docker Zero-Friction Setup

## Key Findings

### Current System Analysis

1. **Entry Points**:
   - CLI via `main.py` with Click framework (10+ commands)
   - Web app via Flask factory pattern in `src/web_app/__init__.py`
   - Host is hardcoded to `127.0.0.1` (must change for Docker)

2. **Data Dependencies**:
   - 6+ Excel/CSV files in `data/demo_source/`
   - SQLite database at `data/investment_system.db`
   - Configuration in `config/settings.yaml`
   - Historical snapshots in `data/historical_snapshots/`

3. **Heavy Dependencies**:
   - scipy, numpy, scikit-learn (require build tools)
   - pandas, openpyxl (large packages)
   - Total ~28 Python packages

4. **Current Pain Points**:
   - Manual Python version management
   - Complex dependency installation (scipy compilation)
   - Excel path configuration in YAML
   - Database initialization steps

### Docker Image Strategy

| Strategy | Image Size | Build Time | Pros | Cons |
|----------|------------|------------|------|------|
| Full build | ~1.5GB | ~10 min | Simple | Too large |
| Multi-stage | ~500MB | ~8 min | Smaller | More complex |
| Pre-built wheels | ~450MB | ~5 min | Fastest | Need wheel repo |
| Alpine base | ~350MB | ~15 min | Smallest | Compatibility issues |

**Decision**: Multi-stage build with `python:3.11-slim-bookworm`
- Bookworm provides better compatibility than Alpine
- Multi-stage reduces size by 60%
- Acceptable build time for CI/CD

### First-Run Detection Approaches

| Approach | Reliability | Complexity | Notes |
|----------|-------------|------------|-------|
| Environment variable | High | Low | Manual, but explicit |
| Database check | High | Medium | Accurate for DB mode |
| File existence check | Medium | Low | Could have empty files |
| Session/cookie | Low | Low | Doesn't persist |

**Decision**: Combined approach
1. Environment variable override (`DEMO_MODE=true`)
2. Database transaction count check
3. User upload directory file count
4. Fallback to first-run state

### Data Storage Options

| Option | Persistence | Backup | Portability |
|--------|-------------|--------|-------------|
| Named volume | High | Manual | Low |
| Bind mount | High | Easy | High |
| Container storage | None | N/A | None |

**Decision**: Hybrid approach
- Named volume for database and user data (reliability)
- Bind mounts for config, logs, output (accessibility)

---

## Design Decisions

| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| Single container | Simplicity for personal use | Multi-container with nginx, separate DB |
| SQLite database | No external dependencies | PostgreSQL in docker-compose |
| Flask built-in server | Adequate for single-user | Gunicorn + nginx for production |
| Non-root user | Security best practice | Root (not recommended) |
| Health check endpoint | Docker/K8s compatibility | TCP check only |
| Entrypoint script | Complex initialization logic | Dockerfile CMD only |
| Demo data in image | Faster first-run | Download on demand |

### Security Decisions

1. **Secret Key**:
   - Must be set via environment variable in production
   - Auto-generate with warning if not provided
   - Never commit to source control

2. **Non-root User**:
   - Container runs as `appuser` (UID 1000)
   - Directories pre-created with correct permissions
   - Volume mounts may need `chown` on host

3. **Network Binding**:
   - Container binds to `0.0.0.0` (required for port mapping)
   - docker-compose exposes only to localhost by default
   - Production should use reverse proxy

### UX Decisions

1. **Onboarding Flow**:
   - Three options: Demo, Upload, Skip
   - Demo provides instant gratification
   - Skip allows exploration of empty system
   - No forced registration or account creation

2. **Demo Mode Banner**:
   - Persistent but dismissible
   - Clear CTA to upload real data
   - Stored in session (returns on new session)

3. **CSV Upload**:
   - Drag-and-drop interface
   - Template downloads provided
   - Real-time validation preview
   - Flexible column mapping

---

## Technical Constraints

1. **scipy/numpy**: Require BLAS/LAPACK libraries at runtime
2. **openpyxl**: Needs libxml2 for Excel parsing
3. **Flask**: Single-threaded by default (adequate for personal use)
4. **SQLite**: File-based, no concurrent write support
5. **File uploads**: Limited by container memory, should cap at 50MB

---

## Future Considerations

### PostgreSQL Support

```yaml
# Future docker-compose.prod.yml addition
services:
  db:
    image: postgres:15-alpine
    volumes:
      - postgres-data:/var/lib/postgresql/data
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
```

Would require:
- Database connector abstraction (partially exists)
- Migration scripts
- Connection pooling

### Horizontal Scaling

Current architecture doesn't support:
- Multiple container instances (SQLite limitation)
- Load balancing
- Session sharing

Would require:
- PostgreSQL database
- Redis for sessions
- Gunicorn with workers
- nginx load balancer

### Kubernetes Deployment

Would need:
- Helm chart
- PersistentVolumeClaim for data
- ConfigMap for settings
- Secret for credentials
- Ingress for routing

---

## References

### Docker Best Practices
- [Docker Python Guide](https://docs.docker.com/language/python/)
- [Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)
- [Security best practices](https://docs.docker.com/develop/security-best-practices/)

### Flask Deployment
- [Flask Deployment Options](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [Flask-Login Documentation](https://flask-login.readthedocs.io/)

### Similar Projects
- [Actual Budget Docker](https://github.com/actualbudget/actual) - Similar personal finance tool
- [Firefly III](https://github.com/firefly-iii/firefly-iii) - Reference for Docker deployment

---

## Open Questions Log

| Question | Status | Resolution |
|----------|--------|------------|
| PostgreSQL support needed? | Open | Consider for v2 |
| Demo data size impact? | Resolved | ~5MB, acceptable |
| Max upload file size? | Open | Propose 50MB limit |
| Multi-language onboarding? | Open | Leverage existing i18n |
| Authentication default? | Open | Disabled by default, enable via env |
| Automatic backups? | Open | Manual for now, future cron job |
