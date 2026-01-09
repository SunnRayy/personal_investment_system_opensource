# Web Application (Deprecated)

This directory contains the Flask web application launcher, which has been **deprioritized** due to known issues.

## ⚠️ Status: Maintenance Mode

The web application (`run_webapp.py`) has known visualization defects:
- Chart.js rendering issues affecting dashboard modules
- Frontend display problems with Investment Compass

**Current Recommendation:** Use the static HTML report system instead.

## Usage (if needed)

```bash
# Launch web app on default port (5001)
python scripts/web/run_webapp.py

# Launch on custom port
python scripts/web/run_webapp.py 5000
```

## Alternative: Static HTML Reports

**Recommended approach:**
```bash
# Generate comprehensive static HTML report
python generate_real_report.py
```

The HTML report provides:
- Complete financial analysis
- Investment Compass recommendations
- XIRR diagnostics
- Historical performance charts
- No server required (open directly in browser)

## Future Plans

Web application development is on hold pending:
1. Resolution of Chart.js rendering issues
2. Completion of Phase 6 advanced optimization features
3. Frontend framework evaluation

## Documentation

For web app architecture details, see:
- `docs/web_app/web_app_development_log.md`
- `development_log.md` (Phase 4.4 status)

## Archival Note

Moved to `scripts/web/` on October 1, 2025 to reduce root directory clutter. The web app remains functional but is not actively maintained.
