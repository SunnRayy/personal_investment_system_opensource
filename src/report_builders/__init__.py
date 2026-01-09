"""
Report Builders - Modular data builders for HTML report generation.

This package contains specialized builder modules for different report sections:
- chart_builders: Chart data generation for visualizations
- performance_builders: Performance metrics aggregation
- kpi_builders: KPI calculations and gains analysis
- rebalancing_builder: Rebalancing analysis and trade recommendations
- table_builder: Holdings table generation with hierarchical structure
- unified_data_preparer: Unified data preparation with validation (Phase 2)
- validation_service: Cross-module data validation (Phase 2)
"""

from .chart_builders import (
    build_portfolio_growth_data,
    build_cash_flow_data,
    build_forecast_data,
    build_twr_data,
    build_drawdown_data,
    build_allocation_from_holdings
)

from .performance_builders import (
    aggregate_performance_by_top_level,
    aggregate_performance_by_sub_class
)

from .kpi_builders import (
    build_gains_analysis_data,
    build_kpi_metrics,
    build_individual_asset_performance
)

from .rebalancing_builder import (
    build_rebalancing_analysis,
    build_hierarchical_recommendations
)

from .table_builder import (
    build_holdings_table_direct
)

from .unified_data_preparer import UnifiedDataPreparer
from .validation_service import ValidationService

__all__ = [
    'build_portfolio_growth_data',
    'build_cash_flow_data',
    'build_forecast_data',
    'build_twr_data',
    'build_drawdown_data',
    'build_allocation_from_holdings',
    'aggregate_performance_by_top_level',
    'aggregate_performance_by_sub_class',
    'build_gains_analysis_data',
    'build_kpi_metrics',
    'build_individual_asset_performance',
    'build_rebalancing_analysis',
    'build_hierarchical_recommendations',
    'build_holdings_table_direct',
    'UnifiedDataPreparer',
    'ValidationService'
]


