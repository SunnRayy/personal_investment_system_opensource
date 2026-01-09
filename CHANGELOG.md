# Changelog

All notable changes to the Personal Investment System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Docker One-Click Deployment**: Zero-friction setup for non-technical users
  - Multi-stage Dockerfile with optimized image size (~500MB)
  - `docker-compose.yml` for single-command deployment
  - `docker-entrypoint.sh` with auto-initialization and first-run detection
  - Environment variable configuration (SECRET_KEY, FLASK_HOST, FLASK_PORT, etc.)
  - Health check endpoints (`/health`, `/api/health`) for container orchestration
  - `DOCKER_QUICKSTART.md` with usage instructions
  - Development plan documentation in `docs/docker-deployment/`
  - **Phase 2**: System state detection module (`src/web_app/system_state.py`)
    - `SystemState` enum (FIRST_RUN, DEMO_MODE, USER_DATA, MIXED_MODE)
    - `SystemStateManager` class for detecting system state
    - Context processor for template access (`system_state`, `is_demo_mode`, `is_first_run`)
    - First-run redirect middleware
  - **Phase 3-4**: Onboarding flow for first-run experience
    - Welcome page with Demo/Upload/Skip options
    - Drag-and-drop file upload interface
    - Column mapping for CSV/Excel imports
    - CSV templates for transactions, holdings, and balance sheet
  - **Phase 5**: Data import engine (`src/data_import/csv_importer.py`)
  - **Phase 8**: Verification & Fixes
    - Fixed first-run redirect logic to prioritize onboarding
    - Implemented auto-login for Demo Mode
    - Resolved system state detection conflict in entrypoint script
    - Auto-detection of encoding and delimiter
    - Flexible column mapping with auto-detection
    - Data validation and error reporting
  - **Phase 6**: UX polish
    - Demo mode banner with dismiss functionality
    - Custom 404 and 500 error pages
  - **Phase 7**: Documentation (`docs/csv-formats.md`)

- **Internationalization (I18n)**: Implemented full localization support using Flask-Babel.
  - Added language switcher (English/Chinese) in navigation bar.
  - Localized "Portfolio Report" template and key backend report builders.
  - Implemented locale-aware configuration loading (e.g., `asset_taxonomy_zh.yaml`).
  - Added `scripts/extract_messages.py` for managing translation workflows.
  - Added Chinese translations for key terms.
  - **Phase 8**: Localized Data Workbench template (~45 strings).
  - **Phase 8**: Localized Logic Studio template (~80+ strings).
  - **Phase 8**: Message catalog now contains 300+ translation entries.

### Fixed

- **Portfolio Report 500 Error**: Resolved a template rendering error caused by `%` characters in translation strings (`XIRR (%)`, `Portfolio Growth (%)`). Moved the `(%)` suffix outside of `_()` translation calls.
- **Report Cache Serialization**: Fixed `Object of type Timestamp is not JSON serializable` error by extending `NumpyEncoder` to handle `pandas.Timestamp` and `datetime` objects.
- **Recommendation Engine Robustness**: Added defensive check for `XIRR` column in `_generate_profit_rebalancing_recommendation` to prevent `KeyError` when the column is missing.

- `CLAUDE.md` - Consolidated AI coding assistant guide
- `CHANGELOG.md` - Version history for open source users
- `config/column_mapping.yaml` - Configurable column mappings for data ingestion
- `scripts/generate_demo_data.py` - Generate mock financial data for testing
- Environment-based web authentication (WEB_ADMIN_USER, WEB_ADMIN_PASS)
- Support for multiple mapping profiles (default, schwab_csv, chinese_excel)
- Quick Start guide in README for demo data
- New ETFs in demo data: VEA (Developed Markets), IEMG (Emerging Markets), VNQ (Real Estate)

### Changed

- **Flask App Docker Compatibility**:
  - `run-web` command now accepts `--host` parameter for Docker binding
  - SECRET_KEY configurable via environment variable (auto-generated if not set)
  - Environment variable fallbacks for FLASK_HOST, FLASK_PORT, FLASK_DEBUG
- **Demo Data Generator Overhaul**: Complete rewrite for chart compatibility and global appeal
  - Balance sheet columns now use `Asset_*`/`Liability_*` prefixes for calculator compatibility
  - Cash flow columns now use `Income_*`/`Expense_*`/`Outflow_Invest_*` prefixes
  - Expanded from 7 to 10 US ETFs (added VEA, IEMG, VNQ for diversification)
  - Scaled all values to USD (~$300K portfolio, $8K/month income)
  - Gold and insurance data now in USD
- **Terminology Refactor**: Replaced "CN Funds" with "Global Markets" across CLI, logs, and documentation for professional consistency
- **Docs Cleanup**: Consolidated documentation in `docs/` folder, removing legacy development logs
- Data ingestion now uses YAML-based column mappings instead of hardcoded dictionaries
- Web app now requires password via environment variable (no hardcoded default)
- `cleaners.py` refactored with proper logging and fallback mechanism
- Column mappings use lazy loading to avoid circular imports

### Removed

- `gemini.md` and `.github/copilot-instructions.md` (replaced by CLAUDE.md)
- `config/rsu_schedule.yaml` from git tracking (now gitignored, use template)
- Hardcoded column mapping dictionaries from cleaners.py (~200 lines)
- CN Fund data generator and CN_FUNDS dictionary (replaced with global ETFs)

---

## [1.0.0] - 2025-01-06

### Added

- **Open Source Release** - Repository sanitized and prepared for public release
- Comprehensive README with installation and usage instructions
- MIT License
- Configuration templates (`settings.yaml.example`, `rsu_schedule.yaml.example`)
- Environment variable support via `.env.example`

### Changed

- Decoupled PII and absolute paths from codebase
- All personal data now loaded from external config files

### Removed

- Jupyter notebooks containing sensitive data
- Hardcoded file paths and personal financial information

---

## [0.9.0] - 2025-01-05

### Added

- **Asset Tier Management UI** - Interactive tier classification in web dashboard
- Priority-based asset classification system
- Logic Studio rule priority support (including priority 0)

### Fixed

- Rule priority default bug in Logic Studio

---

## [0.8.0] - 2025-01-04

### Added

- **Interactive Goal Management** - Full CRUD for financial goals
- **Advanced Risk Simulation** - Enhanced Monte Carlo with scenario analysis
- Goal progress tracking and visualization

---

## [0.7.0] - 2024-12-28

### Added

- **Asset Tier Classification System** - Categorize assets by investment tier
- Annual Report web page with Sankey chart
- Extended KPIs in reporting dashboard

### Changed

- Tier percentages now calculated against rebalanceable assets only
- Improved tier reporting moved to Investment Compass module

### Fixed

- Tier allocation denominator calculation

---

## [0.6.0] - 2024-12-20

### Added

- **Attribution Report** - Brinson-Fachler performance attribution
- Portfolio performance improvements

### Fixed

- Money market fund exclusion from performance reporting
- Dividend reinvestment cost basis calculation
- Stale holdings deletion during sync
- CN fund dividend transaction type mapping

---

## [0.5.0] - 2024-12-15

### Fixed

- Holdings snapshot date bug (was using future dates)
- Fund data writer TypeError for transaction dates
- Data integrity issues with synthetic transactions
- Gold data restoration
- Cash XIRR exclusion from calculations

---

## [0.4.0] - 2024-12-01

### Added

- **System Optimization** - Runtime performance improvements
- Legacy code cleanup
- Next phase planning documentation

---

## [0.3.0] - 2024-11-15

### Added

- **Unified Analysis Engine** - Single entry point for all analysis
- HTML report generator with comprehensive visualizations
- Cash flow forecasting with SARIMA models

---

## [0.2.0] - 2024-11-01

### Added

- **Portfolio Library** - MPT optimization, efficient frontier
- Risk analytics and Sharpe ratio calculations
- Asset taxonomy system with YAML configuration

---

## [0.1.0] - 2024-10-15

### Added

- **Initial Release**
- DataManager for Excel/CSV data integration
- Multi-currency support with automatic conversion
- Transaction processing and cost basis tracking
- Basic financial analysis (balance sheet, XIRR)
- CLI interface via `main.py`

---

## Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| 1.0.0 | 2025-01-06 | Open source release |
| 0.9.0 | 2025-01-05 | Asset tier management |
| 0.8.0 | 2025-01-04 | Goal management & risk simulation |
| 0.7.0 | 2024-12-28 | Asset tier classification |
| 0.6.0 | 2024-12-20 | Attribution reporting |
| 0.5.0 | 2024-12-15 | Data integrity fixes |
| 0.4.0 | 2024-12-01 | System optimization |
| 0.3.0 | 2024-11-15 | Unified analysis engine |
| 0.2.0 | 2024-11-01 | Portfolio library |
| 0.1.0 | 2024-10-15 | Initial release |
