# Changelog

All notable changes to the Personal Investment System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **E2E Testing with Playwright** (Phase 13 of UX/UI redesign):
  - Playwright test framework with 24 comprehensive tests
  - Test suites: Authentication, Dashboard, Navigation, Reports, Settings
  - Auto-start configuration for Flask backend and Vite dev server
  - npm scripts: `test:e2e`, `test:e2e:headed`, `test:e2e:ui`

- **API Integration Layer** (Phase 1 of revised UX/UI plan):
  - `src/api/client.ts`: Type-safe fetch wrapper with error handling, timeout support, and dev logging.
  - `src/api/endpoints.ts`: Centralized endpoint constants for all Flask backend routes.
  - `src/api/types/`: TypeScript interfaces mirroring Flask API response structures.
  - `src/hooks/usePortfolio.ts`: React Query hooks for portfolio data (`usePortfolioOverview`, `useAssetsList`, `useDataQuality`).
  - `src/hooks/useReports.ts`: React Query hooks for reports (`useUnifiedAnalysis`, `useWealthSummary`, `useCashFlow`, `useCorrelation`).
  - Dashboard.tsx now fetches real data from Flask `/api/portfolio_overview` endpoint.
  - Added loading states, error handling, and refresh functionality to Dashboard.
  - Integrated `@tanstack/react-query` for data fetching with caching and retry logic.

- **UX/UI Redesign (Phase 1-4, 7)**:
  - **Design System**: Created `design-tokens.css` with SunnRayy palette (Champagne Gold + Tech Blue) and Inter font.
  - **Components**: Added reusable Jinja2 macros (Buttons, Badges, Metrics, Alerts) in `src/web_app/templates/macros/components.html`.
  - **Layout**: Complete rewrite of `base.html` featuring a modern Sidebar navigation and responsive Top Bar.
  - **Verification**: Added temporary `/test-components` route to verify UI elements.
  - **Data Workbench Wizard**: Multi-step import wizard UI with 5-step flow (Select Type → Upload → Map → Validate → Publish).
  - **CSS Utilities**: Added 140+ utility classes to `style.css` for SunnRayy design system (colors, borders, spacing, responsive grid).
  - **SPA Architecture (Phase 7)**: React/Vite-based Single Page Application structure.
    - Project setup with `vite.config.ts`, TypeScript, and `react-router-dom`.
    - Unified types in `src/types/index.ts`.
    - Migrated pages: `Dashboard.tsx`, `DataWorkbench.tsx`, `Portfolio.tsx`.
    - Reusable `Layout.tsx` with sidebar navigation.

- **Reports Migration (Phase 10-11)**:
  - **Portfolio Report** (`/portfolio`): Interactive stacked area charts for asset allocation and performance history.
  - **Cash Flow Analysis** (`/cashflow`): Sankey-like capital flow diagram and income/expense trends.
  - **Investment Compass** (`/compass`): Market regime indicators, fear/greed gauge, and rebalancing drift analysis.
  - **Monte Carlo Simulation** (`/simulation`): Forward-looking wealth projection with confidence intervals and success probability.
  - **Lifetime Performance** (`/performance`): New report featuring "Gains Analysis" (Realized vs Unrealized) and detailed "Asset Performance Table" (Scorecard).
  - **Logic Studio** (`/logic-studio`): React SPA implementation with tabbed interface for Classification Rules, Strategy Tiers, and Risk Profiles. Includes Add Rule modal, tier descriptions, and allocation sliders with 100% validation.
  - **Design System Enforcement**: Strict adherence to SunnRayy palette (Gray scale, Blue primary, Gold for Equity/Gains).

- **Wealth Dashboard** (`/wealth`): Complete wealth overview with 3-tab navigation.
  - Net Worth & Health tab: Net worth trend chart, asset allocation pie, financial health ratios.
  - Cash Flow tab: Income vs expenses bar charts, net cash flow trend.
  - Expenses tab: Expense breakdown pie chart, efficiency analysis with progress bars.
  - YTD KPI cards with Year-over-Year comparison.
  - **Smart Fallback**: YTD metrics now fallback to Last 12 Months (L12M) when current year has no data, with dynamic label indicator.
  - New hooks: `useWealthDashboard()`, `useWealthParity()`.
  - TypeScript types for wealth API responses.

- **Phase 14 Upstream Fixes** (from legacy real-data testing):
  - **Market Thermometer API**: New `/api/market_thermometer` endpoint for Fear & Greed Index and Buffett Indicator.
  - **Compass API Binding**: `useMarketThermometer` hook with real macro data, demo fallback.
  - **TimePeriodSelector**: Reusable period filter component (1M/3M/6M/YTD/1Y/ALL) wired to Portfolio, CashFlow, Compass.
  - **GlassTooltip**: Glassmorphism-styled chart tooltip component with frosted glass effect.
  - **Export Buttons**: CSV download functionality on all report pages (Portfolio, CashFlow, Compass).
  - **Data Workbench**: Functional file upload with drag/drop, click-to-browse, Copy & Paste tab.
  - **CashFlow Sankey**: Improved visualization with SVG flow connectors, gradient styling, hover effects.

- **Phase 15 Data Integration** (remove hardcoded demo data):
  - **LifetimePerformance.tsx**: Removed `GAINS_BREAKDOWN`, `SUBCLASS_DATA`, `ASSET_DATA` constants; integrated `useLifetimePerformance()` API hook; added functional pagination, filter toggle, and CSV export.
  - **Portfolio.tsx**: Removed 4 `DEMO_*` constants; added `usePortfolioOverview()` hook for trend data; simplified hero chart to single area chart.
  - **CashFlow.tsx**: Removed hardcoded `forecastData`, `incomeBreakdown`, `expenseBreakdown`; added conditional rendering for null states.
  - **Compass.tsx**: Removed all `DEMO_*` fallback constants; implemented null-safe rendering with graceful error states.
  - **New Service**: `src/web_app/services/lifetime_performance_service.py` for gains/performance calculations.

- **Settings Page** (`/settings`): User preferences management with localStorage persistence.
  - Display preferences: Theme (light/dark/system), Language (en/zh), Currency (USD/CNY), Date format.
  - Analysis parameters section (read-only view of config/settings.yaml values).
  - Data integration settings with sync frequency and auto-sync toggles.
  - About section with version information.

- **Dark Mode Support**: Full dark mode implementation across React SPA.
  - PreferencesContext with theme state management and localStorage persistence.
  - Tailwind CSS `darkMode: 'class'` configuration.
  - Layout component updated with dark mode variants for sidebar, navigation, and content areas.
  - System theme preference detection and automatic switching.

- **Code Splitting**: Performance optimization with React.lazy() and Suspense.
  - All page components lazy-loaded on-demand.
  - Main JavaScript chunk reduced from 1037KB to 235KB.
  - Loading spinner fallback during chunk loading.

### Changed

- **Template Deprecation**: Moved 21 Flask Jinja2 templates to `templates/deprecated/` folder.
  - Deprecated: dashboard, data_workbench, logic_studio, reports, wealth templates.
  - Kept active: error pages (404, 500), integrations, onboarding, auth, transactions.
  - Added README.md documenting deprecation with React replacement mapping.

### Fixed

- **Portfolio Report Charts**: Resolved `Chart is not defined` error by moving chart scripts to `{% block scripts %}` (loads after Chart.js library).
- **Translation Format Error**: Fixed "incomplete format" 500 error by moving `%` outside `_()` translation calls.
- **Report Loading Performance**: Identified SARIMA forecast as performance bottleneck causing multi-minute load times. Disabled synchronous forecast generation in `wealth_service.py` to restore fast report loading.

- **Automated Data Integrations**: API-based portfolio sync replacing manual Excel/CSV workflows
  - **Base Connector Framework** (`src/data_manager/connectors/`)
    - `base_connector.py`: Abstract base class with standard interface
    - `utils.py`: Rate limiting, response caching, retry with exponential backoff
    - Standard column definitions for holdings and transactions
  - **CCXT Crypto Integration** (`ccxt_connector.py`)
    - Support for 100+ exchanges (Binance, Coinbase, Kraken, OKX, etc.)
    - Unified balance and transaction fetching
    - Automatic rate limit handling per exchange
  - **Interactive Brokers Integration** (`ibkr_connector.py`)
    - Client Portal API support with JWT authentication
    - Multi-account support (Individual, Joint, IRA, 401k)
    - Support for stocks, bonds, options, futures, forex, crypto
  - **Tiingo Market Data** (`tiingo_connector.py`)
    - Real-time and historical price data
    - Support for stocks, ETFs, crypto, forex
    - Multi-provider fallback (Tiingo → Yahoo → Alpha Vantage)
  - **Plugin System** (`src/plugins/`)
    - `base.py`: Abstract plugin class for bank integrations
    - `manager.py`: Plugin discovery, loading, and validation
    - `registry.py`: Plugin registration and capability tracking
    - Sample bank plugin with full documentation
  - **Import Orchestrator** (`src/data_manager/import_orchestrator.py`)
    - Unified data pipeline coordinating all sources
    - Deduplication and conflict resolution
    - Data quality validation
  - **Database Models**
    - `ImportJob`: Track sync operations and history
    - `PluginConfig`: Store encrypted plugin credentials
    - `DataSourceMetadata`: Track data lineage and quality
  - **Web UI** (`src/web_app/blueprints/integrations/`)
    - Dashboard for managing data sources
    - Crypto holdings view with exchange breakdown
    - Broker connection management
    - Import history and error logs
  - **Configuration** (`config/data_sources.yaml`)
    - Centralized integration configuration
    - Environment variable support for credentials
    - Rate limiting and caching settings
  - **Documentation** (`docs/automated-integrations/`)
    - `task_plan.md`: Development phases and progress tracking
    - `implementation.md`: Technical specs and code examples
    - `notes.md`: Research findings and design decisions
    - `PLUGIN_DEVELOPMENT.md`: Guide for creating plugins
    - `troubleshooting.md`: Common issues and solutions
    - Setup guides for Binance, Coinbase, IBKR, Tiingo
  - **Tests** (`tests/connectors/`)
- 100% test pass rate

### Fixed

- **Foreign Key Constraint Error**: Fixed valid demo data ingest by pre-registering synthetic assets (Cash, Deposits, Property) in `db_sync.py`.
- **Authentication**: Resolved "Silent Failure" on login by enforcing `.env` config precedence and adding `SECRET_KEY` for session stability.
- **Documentation**: Added missing default login credentials (`admin`/`admin`) to README and Docker guides.
- **Report Performance**: Fixed slow report loading (was minutes, now <5 seconds)
  - Added FX rate caching with 1-day TTL and 2-second timeout
  - Implemented timing instrumentation for performance monitoring
  - Created `/reports/api/correlation` endpoint for lazy loading support
  - Added fallback values for API failures

## [1.1.0] - 2026-01-09

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
