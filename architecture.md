# Personal Investment System - Architecture

## Overview

A comprehensive Python system for tracking, analyzing, and optimizing personal investments. The system follows a **layered, modular architecture** with a central data hub pattern.

```
Excel/CSV Data → Data Manager → Analysis Modules → Unified Engine → Reports
                                                          ↓
                                              Recommendation Engine
```

## System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ENTRY POINTS                                    │
│  main.py CLI: run-all | generate-report | update-global-data | run-web      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CONFIGURATION LAYER                                  │
│  settings.yaml | asset_taxonomy.yaml | benchmark.yaml | goals.yaml          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DATA LAYER (Central Hub)                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     src/data_manager/                                │    │
│  │  manager.py ─── historical_manager.py ─── currency_converter.py     │    │
│  │  readers.py ─── cleaners.py ─── calculators.py ─── validators.py    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│              ┌───────────────┼───────────────┐                              │
│              ▼               ▼               ▼                              │
│     Excel/CSV Files    Database (SQLite)   APIs (FX rates)                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ANALYSIS LAYER                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐   │
│  │ financial_       │  │ portfolio_lib/   │  │ investment_optimization/ │   │
│  │ analysis/        │  │                  │  │                          │   │
│  │ - balance_sheet  │  │ - taxonomy_mgr   │  │ - market_regime_detector │   │
│  │ - cash_flow      │  │ - data_integr.   │  │ - portfolio_optimizer    │   │
│  │ - performance    │  │ - mpt optimizer  │  │ - macro_analyzer         │   │
│  │ - cost_basis     │  │ - risk analytics │  │                          │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐   │
│  │ performance_     │  │ goal_planning/   │  │ risk_management/         │   │
│  │ attribution/     │  │                  │  │                          │   │
│  │ - brinson_fachler│  │ - monte_carlo    │  │ - rsu_concentration      │   │
│  │ - benchmarks     │  │ - goal_tracker   │  │                          │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATION LAYER                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │              src/unified_analysis/engine.py                          │    │
│  │              FinancialAnalysisEngine (Main Orchestrator)             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INTELLIGENCE LAYER                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │              src/recommendation_engine/                              │    │
│  │  comprehensive_engine.py ─ financial_advisor.py ─ portfolio_advisor │    │
│  │  risk_advisor.py ─ tax_advisor.py ─ action_prioritizer.py           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OUTPUT LAYER                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │ html_reporter/  │  │ report_builders/│  │ web_app/ (Flask)            │  │
│  │ - reporter.py   │  │ - table_builder │  │ - blueprints (routes)       │  │
│  │ - templates/    │  │ - chart_builders│  │ - services (business logic) │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Module Responsibilities

### Core Data Layer

| Module | Purpose | Key Files |
|--------|---------|-----------|
| `data_manager/` | Central data hub - ALL modules depend on this | `manager.py`, `historical_manager.py` |
| `database/` | SQLAlchemy ORM persistence layer | `models.py`, `migrator.py` |
| `data_quality/` | Data validation and health checks | `health_checker.py` |

### Analysis Layer

| Module | Purpose | Key Files |
|--------|---------|-----------|
| `financial_analysis/` | Balance sheet, cash flow, XIRR | `performance_calculator.py` (canonical XIRR) |
| `portfolio_lib/` | Asset taxonomy, MPT, risk analytics | `taxonomy_manager.py`, `data_integration.py` |
| `investment_optimization/` | Market regime detection, optimization | `market_regime_detector.py` |
| `performance_attribution/` | Brinson-Fachler attribution | `attribution.py` |
| `goal_planning/` | Monte Carlo simulation, goal tracking | `monte_carlo.py`, `goal_tracker.py` |

### Intelligence Layer

| Module | Purpose | Key Files |
|--------|---------|-----------|
| `recommendation_engine/` | Intelligent advice generation | `comprehensive_engine.py`, `action_prioritizer.py` |

### Output Layer

| Module | Purpose | Key Files |
|--------|---------|-----------|
| `html_reporter/` | HTML report generation | `reporter.py`, `templates/` |
| `report_builders/` | Report component builders | `table_builder.py`, `chart_builders.py` |
| `report_generators/` | Report orchestration | `real_report.py` |
| `web_app/` | Flask web application | `__init__.py`, `blueprints/` |

## Data Flow Pipeline

```
1. LOAD CONFIGURATION
   settings.yaml → file paths, API settings
   asset_taxonomy.yaml → classification rules (SINGLE SOURCE OF TRUTH)
   benchmark.yaml → performance benchmarks

2. INGEST DATA (DataManager)
   Excel/CSV files → readers.py → cleaners.py → validators.py
   ├── Standardize transaction types (Chinese→English)
   ├── Generate Asset IDs using taxonomy rules
   └── Currency conversion with API fallback

3. FINANCIAL ANALYSIS (FinancialAnalyzer)
   ├── Balance sheet snapshots
   ├── Cash flow analysis
   ├── Investment performance (XIRR)
   └── Historical trend analysis

4. PORTFOLIO ANALYSIS (PortfolioAnalysisManager)
   ├── Holdings classification via TaxonomyManager
   ├── Modern Portfolio Theory optimization
   ├── Risk metrics calculation
   └── Performance attribution

5. ADVANCED ANALYSIS
   ├── Market regime detection (HMM)
   ├── Goal projections (Monte Carlo)
   └── Rebalancing optimization

6. RECOMMENDATIONS (ComprehensiveRecommendationEngine)
   ├── Financial health advice
   ├── Portfolio rebalancing
   ├── Risk management
   └── Tax optimization
   └→ Prioritized action plan

7. OUTPUT GENERATION
   ├── HTML reports (Jinja2 templates)
   ├── Web dashboard (Flask)
   └── Markdown context (LLM-ready)
```

## Configuration Files

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `config/settings.yaml` | Data file paths, API keys, parameters | Per environment |
| `config/asset_taxonomy.yaml` | Asset classification hierarchy | When adding asset types |
| `config/benchmark.yaml` | Performance benchmark definitions | Quarterly |
| `config/goals.yaml` | Financial goal definitions | When goals change |
| `config/column_mapping.yaml` | Excel column name mappings | When data sources change |

## Key Design Patterns

1. **Hub-and-Spoke**: DataManager as central hub, analysis modules as spokes
2. **Factory Pattern**: `create_app()` for Flask application
3. **Strategy Pattern**: Multiple data source adapters
4. **Integration Hub**: PortfolioAnalysisManager bridges data and analysis
5. **Pipeline Pattern**: Unified analysis engine orchestrates sequential processing
6. **Configuration-Driven**: Taxonomy and settings drive behavior

## Critical Implementation Notes

### XIRR Calculations
```python
# ALWAYS use the canonical implementation
from src.financial_analysis.performance_calculator import PerformanceCalculator

calculator = PerformanceCalculator()
result = calculator.calculate_xirr(dates, cash_flows, context_id="portfolio")
```

### Standard Integration Pattern
```python
from src.data_manager.manager import DataManager
from src.unified_analysis.engine import FinancialAnalysisEngine

# DataManager MUST be initialized first
data_manager = DataManager(config_path='config/settings.yaml')
engine = FinancialAnalysisEngine(config_path='config/settings.yaml')
results = engine.run_complete_analysis()
```

### Asset Classification
- `config/asset_taxonomy.yaml` is the **SINGLE SOURCE OF TRUTH**
- `investment_config.yaml` is deprecated
- TaxonomyManager handles all classification logic

## Directory Structure

```
personal_investment_system/
├── main.py                 # CLI entry point
├── config/                 # Configuration files
│   ├── settings.yaml       # Runtime settings
│   ├── asset_taxonomy.yaml # Asset classification (PRIMARY)
│   └── ...
├── src/                    # Core source code
│   ├── data_manager/       # Central data hub
│   ├── financial_analysis/ # Financial calculations
│   ├── portfolio_lib/      # Portfolio analytics
│   ├── unified_analysis/   # Main orchestrator
│   ├── recommendation_engine/ # Advice generation
│   ├── html_reporter/      # Report generation
│   └── web_app/           # Flask application
├── data/                   # Data files
│   ├── demo_source/        # Demo data
│   └── backups/           # Automated backups
├── output/                 # Generated reports
├── tests/                  # Test suite
└── docs/                   # Documentation
```

## Version History

| Date | Change | Author |
|------|--------|--------|
| 2026-01-08 | Initial architecture documentation | Claude |
