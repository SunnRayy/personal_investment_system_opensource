# Personal Investment System - Development Log

## Documentation Philosophy

This file serves as the single source of truth for the project's development history, current status, and future plans. It contains high-level summaries of completed work. Detailed logs and plans for completed projects are moved to `docs/archive/` to preserve history without cluttering the main documentation. Active project plans are stored in `docs/` and linked from the "Next Development Phase" section.

---

# 整体项目背景和架构介绍

#### 整体项目背景 (Project Background)

本系统旨在开发一个全面的个人财务与投资优化平台。该平台能够读取并整合存储在本地 Excel 文件中的月度现金流数据（收入、支出）、投资组合详情及交易记录。系统的核心目标是：提供个性化的现金流管理支持；生成从资产大类到具体投资产品层级的投资分析与再平衡建议；通过可视化图表辅助用户进行分析与决策；最终实现对个人整体资产增长的分析、追踪与预测。系统将采用模块化架构设计，以确保其可维护性和未来的可扩展性。 (This system aims to develop a comprehensive personal finance and investment optimization platform. The platform will read and integrate monthly cash flow data (income, expenses), investment portfolio details, and transaction records stored in local Excel files. The core objectives are: to provide personalized cash flow management support; generate investment analysis and rebalancing recommendations spanning from broad asset classes down to specific investment products; assist user analysis and decision-making through visual charts; and ultimately enable the analysis, tracking, and forecasting of overall personal asset growth. The system will be designed with a modular architecture to ensure maintainability and future scalability.)

---

#### 整体系统架构 (System Architecture)

系统采用模块化架构，分为以下相互协作的核心模块：
(The system adopts a modular architecture with the following collaborative core modules:)

##### 数据管理模块 (Data Management Module)

* 导入和处理 Excel 数据（资产负债表、投资详情、现金流、交易记录）(Import and process Excel data - Balance Sheet, Investment Holdings, Cash Flow, Transaction Records)
* 数据清洗、验证和结构化转换 (Data cleaning, validation, and structural transformation)
* 历史数据追踪与管理，支持60个月完整历史数据处理 (Historical data tracking and management with 60-month complete data processing capability)
* 可选：对接外部市场数据接口 (Optional: Interface with external market data sources)

##### 财务分析模块 (Financial Analysis Module)

* 生成和分析资产负债表 (Generate and analyze Balance Sheet)
* 分析收入、支出，生成现金流量报告 (Analyze income and expenses, generate Cash Flow reports)
* 计算关键财务比率（储蓄率、负债率等）(Calculate key financial ratios - savings rate, debt ratio, etc.)
* 历史绩效分析与月度回报率计算 (Historical performance analysis with monthly returns calculation)
* 现金流追踪与SARIMA预测模型 (Cash flow tracking with SARIMA forecasting models)

##### 投资优化模块 (Investment Optimization Module)

* 资产映射与分类系统 (Asset mapping and categorization system)
* 基于MPT的资产大类配置优化 (Asset class allocation optimization based on Modern Portfolio Theory)
* 投资组合漂移分析与再平衡建议 (Portfolio drift analysis and rebalancing recommendations)
* 有效前沿、夏普比率与风险指标分析 (Efficient Frontier, Sharpe Ratio, and risk metrics analysis)
* 市场状态检测与动态资产配置 (Market regime detection with dynamic asset allocation)

##### 绩效归因模块 (Performance Attribution Module)

* 多期Brinson-Fachler归因分析 (Multi-period Brinson-Fachler attribution analysis)
* 基准比较与绩效分解 (Benchmark comparison and performance decomposition)
* 专业可视化图表与报告 (Professional visualization charts and reports)
* 税收优化分析与建议 (Tax optimization analysis and recommendations)

##### 目标规划与模拟模块 (Goal Planning & Simulation Module)

* 投资目标设置与参数定义 (Investment goal setting and parameter definition)
* Monte Carlo资产增长模拟 (Monte Carlo asset growth simulation)
* 目标达成可能性分析与进度跟踪 (Goal achievement probability analysis and progress tracking)
* 多情景模拟分析 (Multi-scenario simulation analysis)

##### 推荐引擎与行动建议模块 (Recommendation Engine & Actionable Advice Module)

* 智能投资建议生成 (Intelligent investment recommendation generation)
* 税收优化策略建议 (Tax-optimization strategy recommendations)
* 再平衡执行方案 (Rebalancing execution plans)
* 应急资金管理建议 (Emergency fund management recommendations)

##### 可视化与整合报告模块 (Visualization & Integrated Reporting Module)

* 生成整合性报告，汇总各模块关键分析结果 (Generate integrated reports summarizing key results from all modules)
* 交互式图表与仪表板 (Interactive charts and dashboards)
* 绩效与目标对比可视化 (Performance versus goals visualization)
* Web应用界面与实时数据展示 (Web application interface with real-time data display)

### 核心开发方法 (Development Core Approach)

* **模块化库设计 (Library Modularization)**: 核心逻辑封装在 `.py`文件中作为Python包 (Core logic encapsulated in `.py` files as Python package)
* **Jupyter笔记本驱动 (Notebooks as Drivers)**: 使用Jupyter Notebook进行编排、交互和可视化 (Use Jupyter Notebooks for orchestration, interaction, and visualization)
* **VS Code管理 (VS Code Management)**: 利用VS Code进行开发、调试和版本控制 (Leverage VS Code for development, debugging, and version control)

### 整体项目文件结构 (Project File Structure) - 更新至## 2026-01-07

### Localization Implemented

* **Framework**: Integrated Flask-Babel.

* **Features**:
  * Language switching (Session/URL/Header based).
  * Backend string extraction and translation.
  * Template localization (Portfolio Report).
  * Frontend JS localization (Chart labels).
* **Verification**: Passed `scripts/verify_flask_i18n.py` verifying locale switching and translation rendering.
* **Coverage**: Initial coverage for Portfolio Report and key navigation items.

### 2026-01-07月5日

核心项目结构与模块映射关系：
(Core project structure with module mapping relationships:)

```text
personal_investment_system/
├── development_log.md           # 项目开发总日志 (Main development log)
├── main.py                     # 统一CLI入口 (Unified CLI entry point)
├── requirements.txt            # Python依赖包 (Python dependencies)
├── SCRIPTS_README.md           # 用户脚本指南 (User scripts guide)
├── GEMINI.md                   # AI协作指南 (AI collaboration guide)
│
├── config/                     # 系统配置文件 (System configuration files)
│   ├── settings.yaml          # 主配置文件 (Main configuration)
│   ├── asset_taxonomy.yaml    # 资产分类映射 (Asset classification mapping)
│   ├── benchmark.yaml         # 基准数据配置 (Benchmark data configuration)
│   ├── market_regimes.yaml    # 市场状态配置 (Market regime configuration)
│   ├── goals.yaml             # 目标规划配置 (Goal planning configuration) [UPDATED]
│   └── goal_config.yaml       # 蒙特卡洛配置 (Monte Carlo config)
│
├── src/                       # 核心源代码模块 (Core source code modules)
│   │
│   ├── database/              # 🗄️ 数据库层 (Database Layer)
│   │   ├── base.py           # → SQLAlchemy引擎与会话 (Engine & session)
│   │   ├── connector.py      # → 数据库连接器 (Database connector)
│   │   ├── models.py         # → ORM模型 (Asset, Transaction, Holding)
│   │   ├── logic_models.py   # → 逻辑层模型 (Taxonomy, Tag, RiskProfile)
│   │   └── migrator.py       # → 数据迁移工具 (Data migration tool)
│   │
│   ├── logic_layer/           # 🧠 逻辑层 (Logic Layer)
│   │   └── auto_tagger.py    # → 自动分类引擎 (Auto-classification engine)
│   │
│   ├── data_manager/          # 📊 数据管理模块 (Data Management Module)
│   │   ├── manager.py         # → 主数据管理器 (Primary data manager)
│   │   ├── db_sync.py        # → 文件到DB同步 (File-to-DB sync)
│   │   ├── historical_manager.py # → 历史数据管理 (Historical data management)
│   │   ├── currency_converter.py # → 外汇转换服务 (Currency conversion service)
│   │   ├── readers.py         # → Excel数据读取 (Excel data reading)
│   │   ├── calculators.py     # → 数据计算逻辑 (Data calculation logic)
│   │   └── snapshot_generator.py # → 快照生成工具 (Snapshot generation tool)
│   │
│   ├── portfolio_lib/         # 📈 投资组合库 (Portfolio Library)
│   │   ├── holdings_calculator.py # → 持仓计算器 (Holdings calculator)
│   │   ├── price_service.py  # → 价格服务 (Price service)
│   │   ├── data_integration.py # → 数据集成管理 (Data integration management)
│   │   ├── taxonomy_manager.py # → 资产分类管理 (Asset taxonomy management)
│   │   ├── optimization.py    # → MPT优化算法 (MPT optimization algorithms)
│   │   └── risk_analytics.py  # → 风险分析工具 (Risk analytics tools)
│   │
│   ├── financial_analysis/    # 💰 财务分析模块 (Financial Analysis)
│   │   ├── analyzer.py       # → 综合分析器 (Comprehensive analyzer)
│   │   ├── cash_flow_forecaster.py # → 现金流预测 (Cash flow forecaster) [ENHANCED]
│   │   └── cost_basis.py     # → 成本基础计算 (Cost basis calculation)
│   │
│   ├── goal_planning/         # 🎯 目标规划模块 (Goal Planning)
│   │   ├── simulation.py     # → 蒙特卡洛引擎 (Monte Carlo engine)
│   │   └── goal_manager.py   # → 目标管理逻辑 (Goal management logic) [UPDATED]
│   │
│   ├── scripts/              # 🔧 开发与运维工具 (Development & Operations Tools)
│   │   ├── reconcile_transactions.py # → 交易对账脚本 (Transaction reconciliation)
│   │   ├── cleanup_adjustments.py    # → 调整交易清理 (Adjustment cleanup)
│   │   ├── migrate_allocations.py    # → 配置迁移工具 (Allocation migration)
│   │   └── populate_db_history.py    # → 历史数据填充 (Historical data population) [NEW]
│   │
│   ├── web_app/              # 🌐 Web界面模块 (Web Interface Module)
│   │   ├── app.py            # → Flask应用入口 (Flask application entry)
│   │   ├── blueprints/       # → 蓝图模块 (Blueprints)
│   │   │   ├── api/          # → API接口 (API endpoints)
│   │   │   ├── assets/       # → 资产管理 (Asset management)
│   │   │   ├── dashboard/    # → 仪表板 (Dashboard)
│   │   │   ├── logic_studio/ # → 逻辑工作室 (Logic Studio)
│   │   │   ├── reports/      # → 报告视图 (Report views)
│   │   │   ├── simulation/   # → 模拟分析 (Simulation Analysis) [NEW]
│   │   │   └── transactions/ # → 交易管理 (Transaction management)
│   │   ├── services/         # → 业务逻辑服务 (Business services)
│   │   │   ├── report_service.py # → 报告服务 (Report service)
│   │   │   ├── simulation_service.py # → 模拟服务 (Simulation service) [NEW]
│   │   │   └── correlation_service.py # → 相关性服务 (Correlation service) [NEW]
│   │   ├── templates/        # → HTML模板 (HTML templates)
│   │   └── static/           # → 静态资源 (Static resources)
│   │
│   ├── report_builders/       # 📋 报告构建器 (Report Builders)
│   │   ├── attribution_builder.py # → 归因分析 (Attribution analysis)
│   │   ├── rebalancing_builder.py # → 再平衡分析 (Rebalancing analysis)
│   │   ├── kpi_builders.py   # → KPI指标构建 (KPI metrics)
│   │   └── table_builder.py  # → 持仓表格构建 (Holdings table)
│   │
│   └── [其他模块保持不变...]  # (Other modules unchanged...)
│
├── data/                     # 💾 数据存储 (Data Storage)
│   ├── investment_system.db  # → 主数据库 (Main database)
│   ├── historical_snapshots/ # → 历史快照数据 (Historical snapshot data)
│   └── Financial Summary_*.xlsx # → 用户Excel数据文件 (User Excel data files)

```

│
├── notebooks/                # 🔬 测试与验证笔记本 (Testing & Validation Notebooks)
│   ├── 01_data_manager_test.ipynb     # → 数据管理器测试 (Data manager testing)
│   ├── 06_unified_analysis_test_clean.ipynb # → 统一分析测试 (Unified analysis testing)
│   ├── 07_goal_planning_test.ipynb    # → 目标规划测试 (Goal planning testing)
│   ├── 09_cash_flow_forecasting_test.ipynb # → 现金流预测测试 (Cash flow forecasting testing)
│   ├── 12_investment_compass_hub_development.ipynb # → Investment Compass开发 (Investment Compass development)
│   └── 13_performance_reconciliation_test.ipynb # → 性能对账测试 (Performance reconciliation testing)
│
├── docs/                     # 📚 技术文档 (Technical Documentation)
│   ├── _active_projects/     # → 进行中的项目计划 (Active project plans)
│   ├── archive/              # → 已完成项目归档 (Archived completed projects)
│   ├── data_manager/         # → 数据管理器文档 (Data manager documentation)
│   ├── financial_analysis/   # → 财务分析文档 (Financial analysis documentation)
│   ├── html_reporter/        # → HTML报告系统文档 (HTML reporter documentation)
│   ├── investment_compass/   # → Investment Compass文档 (Investment Compass documentation)
│   ├── investment_optimization/ # → 投资优化模块文档 (Investment optimization documentation)
│   ├── performance_attribution/ # → 绩效归因文档 (Performance attribution documentation)
│   └── system_improvement_development_log.md # → 系统改进日志 (System improvement log)
│
├── test/                     # 🧪 单元测试 (Unit Tests)
│   ├── test_performance_calculator.py # → 性能计算器测试 (Performance calculator testing)
│   ├── test_cost_basis_unit.py # → 成本基础测试 (Cost basis testing)
│   ├── test_tax_advisor.py   # → 税收优化测试 (Tax optimization testing)
│   ├── test_investment_compass_api.py # → Investment Compass API测试
│   ├── test_macro_analyzer.py # → 宏观市场指标测试 (Macro market indicators testing)
│   └── run_tests.py          # → 测试运行器 (Test runner)
│
└── data/                     # 💾 数据存储 (Data Storage)
    ├── market_data.db        # → 市场数据与交易数据库 (Market data & transactions DB)
    ├── historical_snapshots/ # → 历史快照数据 (Historical snapshot data)
    └── Financial Summary_*.xlsx # → 用户Excel数据文件 (User Excel data files)

```

### 当前开发状态总览 (Current Development Status & Priority)

### ➡️ 当前阶段：WealthOS 全数据库模式 (Current Phase: WealthOS Full Database Mode)

**状态更新 (Status Update)**: Jan 5, 2026

**状态更新 (Status Update)**: Jan 7, 2026

**最新完成 (Latest Completed)**:

## [Unreleased]

### Added
- **Internationalization (I18n)**: Implemented full localization support using Flask-Babel.
  - Added language switcher (English/Chinese) in navigation bar.
  - Localized "Portfolio Report" template and key backend report builders.
  - Implemented locale-aware configuration loading (e.g., `asset_taxonomy_zh.yaml`).
  - Added `scripts/extract_messages.py` for managing translation workflows.
  - Added Chinese translations for key terms.

* **Portfolio Report 500 Error Fix** (Completed: Jan 8, 2026):
  * **Root Cause**: A `ValueError: unsupported format character ')' (0x29) at index 7` was triggered by `XIRR (%)` and `Portfolio Growth (%)` strings within `_()` translation calls. Python's `%`-formatting rules conflicted with the `%` character.
  * **Template Fix**: Moved `(%)` suffix outside of `_()` calls in `portfolio.html` (lines 816, 848, 882) to separate the translatable text from the literal `%` symbol.
  * **Cache Fix**: Extended `NumpyEncoder` in `report_service.py` to handle `pandas.Timestamp` and `datetime.datetime` objects, resolving a `TypeError` that prevented cache saving.
  * **Recommendation Engine**: Added a defensive check for the `XIRR` column in `recommendation_engine.py` to prevent a `KeyError` during profit rebalancing recommendation generation.

* **Terminology Refactor \u0026 Documentation Cleanup** (Completed: Jan 7, 2026):
  * **Global Markets**: Renamed "CN Funds" to "Global Markets" across the entire system (CLI commands, logging, README, configuration comments) to align with professional terminology.
  * **Documentation**: Cleaned up `docs/` folder, preserving only `MAPPING_GUIDE.md` and removing obsolete dev logs. Updated `.gitignore` to track the clean `docs/` folder.
  * **CLI Update**: Renamed `update-funds` command to `update-global-data`.

* **Asset Tier Interactive Management & Priority-Based Rules** (Completed: Jan 6, 2026):
  * **Interactive Tier Management**: Implemented full lifecycle UI for Asset Tiers in Logic Studio, including summary cards, a classification audit table with quick-action shortcuts, and a target allocation editor.
  * **Rule Priority Support**: Enhanced the classification rule engine with a `priority` field. New rules now default to higher priority (e.g., 200), allowing user-defined rules to safely override seeded or legacy rules (typically priority 107).
  * **Taxonomy Isolation**: Fixed classification interference where Tier tags were appearing in Asset Class reports. Tiers and Asset Classes now operate as parallel, isolated taxonomies.
  * **Rule Management**: Added a dedicated Tier Rules section to the UI with delete functionality, ensuring full CRUD control over classification logic.
  * **Data Integrity**: Enforced taxonomy-specific filtering in `TaxonomyManager` to prevent data leakage between classification layers.

* **Interactive Goal Management & Advanced Risk Simulation** (Completed: Jan 5, 2026):
  * **Goal Management**: Implemented interactive CRUD UI for investment goals (Add/Edit/Delete). Goals are persisted to `config/goals.yaml` with auto-reload resilience.
  * **Simulation Engine**: Integrated Monte Carlo simulation into the Web App (`/simulation`). Dynamic analysis of portfolio growth vs. multiple weighted goals.
  * **Success Metrics**: Implemented "Aggregate Success Rate" metric to track the probability of meeting all defined financial goals simultaneously.
  * **Correlation Insights**: Enhanced the correlation heatmap in Action Compass. Sub-class level view by default; collapsible asset-level view with friendly names (mapping IDs to symbols).
  * **Data Consistency**: Fixed critical "stale asset" duplicates in Database mode by enforcing a global latest-date filter. Resolved TaxonomyManager method name mismatch.

* **Asset Tier Reporting & Analysis** (Completed: Jan 4, 2026):
  * **Tier Analysis**: Implemented Granular Tier Analysis with Profit/Loss (Realized/Unrealized) and XIRR metrics per tier.
  * **Web App**: Integrated Strategic Tier Allocation into Action Compass report for better alignment with strategic decision making.
  * **Reporting**: Enhanced Markdown context report with detailed tier performance table.
  * **Refinement**: Clarified "Unclassified" assets and reviewed ETF taxonomy.
* **System Optimization & Cleanup** (Completed: Jan 4, 2026):
  * **Legacy Removal**: Deleted `src/web_app/legacy_app.py` (71KB dead code from pre-Blueprint architecture).
  * **Script Organization**: Archived 25+ one-off migration/debug scripts to `scripts/archive/`.
  * **Demo Cleanup**: Removed outdated `demos/` directory.
  * **Runtime Optimization**: Re-enabled 5-minute caching in `ReportDataService` (was disabled, causing redundant API calls). Reduced log verbosity.
  * **Stats**: -3361 lines of legacy code removed.
* **Annual Report Web Page & Navigation Updates** (Completed: Jan 4, 2026):
  * **Annual Report**: Implemented interactive annual summary report at `/reports/annual` with Sankey chart visualization for income/expense/savings flow, 9 KPI cards (Income, Expense, Savings, Investment, Savings Rate, Investment Rate, Passive Income %, NW Growth %, Market Gain), and year selector (2020-2025).
  * **Metric Calculations**: Added extended metrics including Net New Investment, Investment Rate %, and corrected Market Gain formula (NW Change - Net New Investment).
  * **Hover Tooltips**: All KPI cards display calculation formulas on hover for transparency.
  * **Navigation**: Added "Annual Report" to Reports dropdown; converted Health Check into a dropdown with "Data Quality" and "Parity Check" sub-items.
  * **Cash Flow Year Selector**: Added year selector dropdown to Cash Flow report header with dynamic YTD metrics recalculation per selected year.

* **Dividend Reinvestment Cost Basis Fix** (Completed: Dec 27, 2025):

  * **Root Cause**: `Dividend_Reinvest` transactions were incorrectly creating purchase lots at NAV cost, inflating total cost basis and suppressing reported profits.
  * **Fix Applied in `cost_basis.py`**: Reinvested dividend shares now have **zero cost basis** (profit returned as shares, not new investment); dividend value recorded as **realized profit**.
  * **Validation**: Cross-validated CN fund profits; HTML reports and Web App now show accurate lifetime profits including historical dividend income.
  * **Debug Tooling**: Created `scripts/debug/validate_cn_fund_profits.py` for systematic profit validation.

* **Cash Flow Dashboard V4 & Data Processing Updates** (Completed: Dec 22, 2025):
  * **Cash Flow Report**: Complete interactive dashboard with period comparisons, expense analytics, and 12-month financial forecasting.
  * **Multi-Account Gold Holdings**: Aggregated paper gold from multiple bank accounts into unified reporting entry.
  * **Expense Column Mapping**: Updated expense column mapping for "Family and Temp expenses" category.
  * **Routes & Templates**: New `/reports/cashflow` route with full visualization and parity checking.

* **Market Thermometer Separation & Regime Logic Enhancement** (Completed: Dec 24, 2025):
  * **Architectural Change**: Separated Action Compass (Risk Profile-driven) from Market Thermometer (Market Regime-driven).
  * **Regime Logic**: Added "Elevated Valuation Risk" regime to cover high PE (30+) + neutral F&G scenarios.
  * **Functional Separation**: Removed dynamic target overrides from Action Compass; rebalancing now strictly follows Logic Studio profiles.
  * **Advisory UI**: Added "Suggested Allocation Adjustments" section to Market Thermometer for advisory guidance.
  * **Fixes**: Fixed risk profile not found error, incorrect template endpoint, and gold/crypto caching issues.

* **Attribution Report & Portfolio Performance Improvements** (Completed: Dec 24, 2025):
  * **Attribution Report**: Implemented Brinson-Fachler attribution analysis with asset class breakdown and return contribution visualization.
  * **TWR Calculation Fix**: Replaced Balance Sheet-based TWR with transaction-based calculation using `calculate_returns_from_transactions` for improved accuracy.
  * **XIRR Property Exclusion**: Excluded Real Estate/Property from overall XIRR calculation to focus on liquid portfolio performance.
  * **Display Fixes**: Fixed 12-Month XIRR formatting to 2 decimal places; added "Excl. Real Estate" notes to XIRR cards.
  * **Bug Fixes**: Fixed attribution endpoint 500 errors, transaction_analyzer taxonomy initialization, dividend reinvestment handling.
* **WealthOS Phase 10: Full DB Mode & Reconciliation** (Completed: Dec 20, 2025):
  * **Transaction Reconciliation**: Implemented `reconcile_transactions.py` to auto-generate adjustment transactions bridging gaps between incomplete transaction history and authoritative holdings snapshots.
  * **Dynamic FX Rate**: 3-tier fetch (Google Finance → Excel → Hardcoded fallback) for USD/CNY conversion.
  * **Parity Dashboard**: `/dashboard/parity` shows 0.00% gap between `HoldingsCalculator` and `DataManager`.
  * **HoldingsCalculator Promotion**: Now the single source of truth for all reports.

* **WealthOS Phase 8-9: Automated Pipeline** (Completed: Dec 16, 2025):
  * **Automated Flow**: `python main.py run-all` executes: Files → DB Sync → Auto-Classify → Reconcile → Validate → Report.
  * **DB Sync**: `db_sync.py` upserts assets from Schwab CSV/Funding Excel into SQLite.
  * **Holdings Snapshot Sync**: Monthly CN fund holdings synced to `Holding` table for accuracy.
  * **AutoTagger**: Regex-based rule engine classifies assets and backfills `Asset.asset_class`.

* **Logic Studio Phase 7.5: Active Risk & Asset Intelligence** (Completed: Dec 2, 2025):
  * **Active Risk Profile**: Implemented UI to switch active risk profiles, persisted in DB.
  * **Market Regime Refinement**: Relative modifiers (+/-) adjust the active profile based on market conditions (e.g., Inflation Regime).
  * **Logic Studio**: Full UI control over asset taxonomy (Tag Manager, Audit View) replacing YAML configuration.
  * **Rebalancing**: Implemented "Constrained Target Value" to ensure trade recommendations are realistic and based on liquid assets only.

* **Logic Studio Phase 6: Logic Layer Foundation** (Completed: Nov 25, 2025):
  * **Logic Layer**: Introduced `Taxonomy`, `Tag`, and `ClassificationRule` database models to replace hardcoded logic.
  * **Taxonomy Editor**: Web interface to manage asset hierarchies and tags.
  * **Auto-Tagger**: Regex-based rule engine to automatically classify assets from transaction descriptions.

* **Web App Phase 5: Data Quality & Report Parity** (Completed: Nov 22, 2025):
  * **Feature Parity**: Web App now matches static reports 100% (Portfolio, Compass, Thermometer).
  * **Data Quality**: Fixed Dashboard history count and Action Compass badges.
  * **UX**: Added auto-complete dropdown for Transaction Form.
  * **Performance**: Implemented 24h persistent caching.

**系统状态 (System Status)**: 🟢 生产就绪，WealthOS 全数据库模式已实现 (Production-ready, WealthOS Full Database Mode Achieved)

**当前系统架构概览 (System Status Summary)**:

* **Data Sources (Unified Mode)**:
    1. **SQLite Database**: **Primary source of truth** for holdings, transactions, and asset metadata.
    2. **Excel/CSV**: Secondary input (Schwab CSV, Funding Excel), synced to DB via `db_sync.py`.
* **Reporting Engines (Unified)**:
    1. **Web App HTML**: Primary interactive Flask-based reports (powered by `HoldingsCalculator`).
    2. **Static HTML**: Legacy report generator (still available for backup/audit).
    3. **Markdown**: LLM-optimized context output for AI analysis.

**下一阶段建议 (Next Phase Suggestions)**:

1. **Scheduler/CRON**: Automate `run-all` on a daily schedule.
2. **Advanced Analytics**: Bring Monte Carlo simulations and goal planning into the web interface.
3. **Mobile-Friendly UI**: Responsive design for mobile access.

### **详细项目文档 (Detailed Project Documentation)**

完成项目的详细实施文档、技术架构、测试结果已归档至 `docs/archive/completed_projects/` 和各模块文档目录。

主要归档文档包括：

* Action Compass V2.0: `docs/ACTION_COMPASS_V2_REDESIGNED_PLAN.md`
* Market Thermometer: `docs/investment_optimization/market_thermometer_*.md`
* Modular HTML Report System: `docs/archive/completed_projects/modular_html_report_system/`
* Crypto & Alternative Assets: `docs/archive/completed_projects/crypto_alt_assets_system_completion.md`

(Detailed implementation documentation, technical architecture, and test results for completed projects are archived in `docs/archive/completed_projects/` and module documentation directories.)

---

#### ✅ 已实现系统能力 (System Capabilities Achieved)

**核心平台功能 (Core Platform Features):**

* ✅ **统一工作流 (Unified Workflow)**: 从Excel到Web仪表板的单命令分析，**August 19验证**: 端到端系统100%运行成功 (Single-command analysis from Excel to web dashboard, August 19 validation: end-to-end system 100% operational)
* ✅ **专业输出 (Professional Output)**: 顾问级质量报告和综合分析，**技术能力**: 完整投资组合分析功能 (Advisor-quality reports and comprehensive analysis, technical capability: complete portfolio analysis functions)
* ✅ **智能分析 (Intelligent Analysis)**: 数据驱动的建议与质量验证，**数据处理**: 完整交易记录处理能力 (Data-driven recommendations with quality validation, data processing: complete transaction record processing capability)
* ✅ **高级规划 (Advanced Planning)**: 目标规划与仿真能力 (Goal planning and simulation capabilities)
* ✅ **历史分析 (Historical Analytics)**: 完整的多年投资组合分析与风险指标，**验证完成**: 完整历史记录成功加载 (Complete multi-year portfolio analysis and risk metrics, validation completed: complete historical records successfully loaded)
* ✅ **高级归因 (Advanced Attribution)**: 多期归因分析与税收优化 (Multi-period attribution analysis with tax optimization)
* ✅ **预测分析 (Predictive Analytics)**: 机器学习预测框架 (SARIMA, ETS, 集成方法)，**验证状态**: 12个月预测能力完全运行 (Machine learning forecasting framework - SARIMA, ETS, ensemble methods, validation status: 12-month forecasting fully operational)

**待解决问题 (Outstanding Issues):**

* � **Web界面稳定性 (Web Interface Stability)**: 稳定性管理框架已实施，继续优化中 (Stability management framework implemented, ongoing optimization)
* 🚧 **自动化优化 (Automated Optimization)**: 智能再平衡和税收高效策略 (第6阶段规划) (Smart rebalancing and tax-efficient strategies - Phase 6 Planning)

---

## ✅ 之前完成的主要项目 (Previously Completed Major Projects)

This section provides a high-level overview of major completed projects, ranked from latest to oldest.

* **Web App Phase 5: Data Quality & Report Parity** (Completed: Nov 22, 2025):
  * **Feature Parity**: Web App now matches static reports 100% (Portfolio, Compass, Thermometer).
  * **Data Quality**: Fixed Dashboard history count and Action Compass badges.
  * **UX**: Added auto-complete dropdown for Transaction Form.
  * **Performance**: Implemented 24h persistent caching.
* **Web App Phase 4: Interactive Reporting & Visualization** (Completed: Nov 22, 2025):
  * **Interactive Reports**: Implemented `ReportGenerator` to create dynamic HTML reports with Jinja2 templates.
  * **Investment Compass**: Integrated "Investment Compass" into the web interface with dynamic market regime detection.
  * **Visualizations**: Added interactive charts using Chart.js for portfolio performance and asset allocation.
  * **Drift Analysis**: Fixed drift calculation in Compass report to correctly display allocation deviations.
* **Web App Phase 3: Security & Database Integration** (Completed: Nov 22, 2025):
  * **Security**: Implemented CSRF protection (WTForms), secure headers (Talisman), and rate limiting (Limiter).
  * **Database**: Integrated SQLAlchemy ORM for `FundNAV` and `MacroIndicator`, replacing direct SQL/Excel access.
  * **API**: Created RESTful API endpoints for fund data and macro indicators with proper error handling.
  * **Testing**: Added comprehensive test suite for security features and database models.
* **CN Fund Data Persistence & Management** (Completed: Nov 18, 2025):
  * **Database Migration**: Successfully migrated from Excel-based `fund_nav_history.xlsx` to SQLite database (`data/market_data.db`).
  * **Data Integrity**: Implemented `FundNAVManager` with robust validation, duplicate prevention, and atomic transactions.
  * **Performance**: Reduced data loading time and improved reliability for historical NAV data.
  * **Recovery**: Successfully recovered from a critical data loss incident (2206 records) using backup restoration protocols.
* **Cost Basis Calculation Fix** (Completed: Nov 18, 2025):
  * **Issue Resolution**: Fixed critical bug in `cost_basis.py` where `calculate_realized_gains` was failing due to missing `date` column in merged DataFrame.
  * **Validation**: Added comprehensive unit test `test_realized_gains_calculation` to verify fix and prevent regression.
  * **Impact**: Restored accurate realized gain/loss reporting for tax and performance analysis.
* **Data Accuracy Fixes Phase 2** (Completed: Nov 17, 2025):
  * **Insurance Asset Classification**: Enhanced pattern matching for insurance products.
  * **BOC Dual-Currency Handling**: Fixed USD conversion overwriting CNY values.
  * **Duplicate Deposits Removal**: Standardized deposit holdings.
  * **Asset Classification**: Completed asset taxonomy for BOC Deposit (USD).
* **Historical Fixes Restoration & System Verification** (Completed: Nov 17, 2025):
  * **Restoration**: Restored Nov 4-5 fixes lost during branch sync.
  * **Verification**: Verified Sharpe ratio, TWR formula, and Markdown aggregate metrics.
* **Data Quality Fixes** (Completed: Nov 16-17, 2025):
  * **Bank Wealth Categorization**: Corrected mapping to Money Market.
  * **US Bonds XIRR**: Added transaction amount filter.
  * **Priority Actions**: Enforced validated data sources.
  * **BOC Deposit Deduplication**: Added column filters.
  * **Cash Flow Forecast**: Prioritized validated columns.
* **Report Data Consistency Fixes** (Completed: Nov 5, 2025):
  * **Markdown Context**: Enhanced asset matching.
  * **System Status**: Integrated real-time Google Finance API.
  * **Holdings Table**: Unified formatting and asset matching.
  * **XIRR Diagnostics**: Restored data display.
* **Data Consolidation Migration** (Completed: Nov 4, 2025):
  * **Migration**: Moved from static balance sheet to transaction-driven architecture.
  * **Validation**: Zero duplicate holdings, stable performance metrics.
* **Data Validation & Accuracy Fixes** (Completed: Nov 2-3, 2025):
  * **Production Deployment**: 4 critical data accuracy fixes - Fund 310398 dividend distribution handling (cost basis tracking bug fix), Sharpe ratio calculation (removed -1 multiplier), TWR formula standardization (unified ±1 formula), Markdown context generator aggregate metrics (added asset class total P/L and return %).
  * **Validation**: All fixes validated and deployed, system data accuracy meets production standards.
  * **Documentation**: `docs/comprehensive_data_validation_plan.md`, `docs/xirr_calculation_analysis.md`
* **Action Compass V2.0 - LLM-Powered Intelligence System** (Completed: Nov 2, 2025):
  * **Dual-Track Output**: HTML Action Compass + Markdown Context Generator, 4-day completion (planned 5-7 days).
  * **CLI Integration**: `generate-context` command for standalone markdown generation, user-validated for production deployment.
  * **Complete Phases**: Strategic Directive Engine, Portfolio Alignment Analysis, HTML Integration, Markdown Context Generator, CLI Integration, User Validation (100% complete).
  * **Technical Metrics**: HTML 192KB/Markdown 19KB, generation time <4s (target <8s).
  * **Documentation**: `docs/ACTION_COMPASS_V2_REDESIGNED_PLAN.md`
* **Market Thermometer V2.0 - Alternative Assets Intelligence System** (Completed: Oct 30, 2025):
  * **Scoring System**: -10 to +10 weighted scoring with Gold/Crypto intelligent recommendation engine.
  * **Asset Intelligence**: BTC/ETH asset differentiation, 3 crypto sentiment indicators (BTC/QQQ ratio, Fear & Greed Index, Overall Market Sentiment).
  * **Testing**: 45/45 unit tests passing, Google Finance fallback implementation, BTC/QQQ dual-source reliability.
  * **Integration**: Action Compass layout reorganization.
* **Crypto & Alternative Assets Volatility System** (Completed: Oct 29, 2025):
  * **Recommendation Engine**: Volatility-based crypto (BTC/ETH) and gold recommendation system.
  * **Market Integration**: 7 market indicators integrated into Market Thermometer.
  * **Analysis**: Contrarian volatility signals with relative value analysis.
  * **Performance**: 66/66 unit tests passing, 24-hour caching optimization.
* **Modular HTML Report System** (Completed: Oct 19-20, 2025):
  * **Report Split**: 850 KB monolithic report split into 4 independent pages (Index/Portfolio/Market Thermometer/Action Compass).
  * **Size Reduction**: 403.4 KB total (52.5% reduction), Jinja2 parent-child template architecture implementing DRY principles.
  * **Optimization**: Typography system optimization (12.5% reduction), Capital Injection calculator, XIRR diagnostics data transformation.
  * **Validation**: 100% data integrity validation after fixing 9 issues in 2 debug sessions.
* **Market Thermometer - Macro Market Indicators System** (Completed: Oct 18, 2025):
  * **Indicators**: 7 indicators real-time fetching (Shiller P/E, VIX, High Yield Spread, 4 Buffett Indicators).
  * **Classification**: 5-level system (Extreme Cold/Cold/Normal/Hot/Extreme Hot).
  * **Data Sources**: GuruFocus web scraping replacing FRED's 2-5 year old data, manual input system for user override.
  * **Testing**: 23/23 unit tests passing, HTML report integration with Market Thermometer tab.
* **Action Compass V2.0 - Intelligent Recommendation Engine Enhancement** (Completed: Oct 14, 2025):
  * **Upgrade**: From informational tips to multi-dimensional intelligent recommendation engine.
  * **Generators**: 4 recommendation generators (rebalancing optimization, tax optimization, cash flow management, emergency fund).
  * **Recommendations**: Product-level intelligent recommendations (5-7 items) with financial impact and execution steps.
  * **Performance**: 3-day completion (57% ahead of 7-10 day schedule), report generation 4.89s (well below 8s target).
* **Data Consistency Fixes** (Completed: Oct 14, 2025):
  * **XIRR Unification**: Unified XIRR data source to `lifetime_performance_data`.
  * **Consistency**: Eliminated cost basis approximation errors, 88% discrepancy eliminated between Dashboard and Action Compass.
  * **Validation**: 100% cross-module data consistency achieved.
* **USD Assets Currency Conversion Bug Fixes** (Completed: Oct 12, 2025):
  * **Bug Fix**: Double currency conversion bug affecting all USD assets (RSU, US ETF).
  * **Implementation**: 8 critical fixes (cost_basis.py 6 fixes, kpi_builders.py 2 fixes), single conversion point principle.
  * **Result**: RSU and US ETF now display reasonable returns and XIRR values.
* **Currency Converter Performance Optimization** (Completed: Oct 7, 2025):
  * **Strategy**: Excel-first strategy, API disabled by default.
  * **Performance**: 200x improvement (10 min→4.5 sec), thread-based timeout protection.
* **Project: Command Center - Unified CLI System** (Completed: Oct 2, 2025):
  * **CLI System**: Single entry point consolidating all runner scripts (`run-all`, `generate-report`, `update-funds`, `create-snapshots`).
  * **Implementation**: 1,034-line self-contained implementation, report generator modularized.
  * **Validation**: Production validation complete, automated data processing and report generation workflow.
* **Project Unify - Unified Performance Engine** (Completed: Sep 30, 2025):
  * **Consolidation**: Eliminated XIRR duplication across modules.
  * **Features**: Multi-currency support, 23 tests passing.
* **Static HTML Report Generation System** (Completed: Sep 21, 2025):
  * **Enhancement**: 10 professional-grade enhancement tasks completed.
  * **Quality**: Production-level financial reporting system.
* **Investment Compass Decision Support System** (Completed: Sep 7, 2025):
  * **Development**: Comprehensive investment decision support system development.
  * **Features**: 6-category asset allocation analysis, rebalancing recommendation engine.
* **System Validation & Integration Testing** (Completed: Aug 19, 2025):
  * **Validation**: 5/5 core modules 100% operational validation.
  * **Analysis**: Portfolio technical analysis completed.
* **Advanced Attribution & Tax Optimization** (Completed: Aug 17, 2025):
  * **Phase 5.1**: Multi-period attribution analysis with production-ready tax optimization.
* **Machine Learning & Predictive Analytics** (Completed: Aug 17, 2025):
  * **Phase 5.3**: SARIMA/ETS forecasting with ensemble methods.
* **Historical Data Infrastructure** (Completed: Aug 16, 2025):
  * **Phase 5.5**: 60-month analysis capability unlocked.
* **Goal Planning & Simulation** (Phase 5.2):
  * **Capability**: Monte Carlo modeling and scenario analysis.

* **Web App Phase 2: Modular Architecture & Management Platform** (Completed: Nov 21, 2025):
  * **Refactoring**: Converted monolithic `app.py` into a modular Flask Blueprint architecture (`main`, `api`, `transactions`, `assets`, `dashboard`).
  * **Transaction Management**: Implemented full CRUD functionality for transactions with TailwindCSS UI.
  * **Asset Taxonomy**: Added UI for managing asset mappings and taxonomy configuration (`asset_taxonomy.yaml`).
  * **Dashboard**: Created a visual dashboard with Chart.js integration for portfolio overview.
  * **Final Polish**: Connected Dashboard charts to real API data, fixed Compass integration, and improved Asset list UI.
  * **Validation**: Verified with end-to-end tests covering all new routes and API endpoints.
* **Action Compass V2.0 - Phase 1: Strategic Directive Engine** (Completed: Oct 30, 2025): Implemented pyramid-logic recommendation system with Strategic Command Card UI. Built `StrategicDirectiveBuilder` to extract market regime strategy into user-friendly directives with core objectives, prioritized action steps, and allocation adjustments. 23 unit tests (100% pass rate), full HTML integration, and 2 critical bug fixes during integration testing.
