"""
Investment Optimization Module

This module provides advanced portfolio optimization and time-series analysis capabilities
for the personal investment system. It integrates with the existing DataManager and
portfolio_lib modules to provide comprehensive optimization workflows.

Key Components:
- TimeSeriesAnalyzer: Analyzes portfolio performance and risk over time
- PortfolioOptimizer: Provides multiple optimization strategies and rebalancing recommendations
"""

from .time_series_analyzer import TimeSeriesAnalyzer
from .portfolio_optimizer import PortfolioOptimizer

__all__ = ['TimeSeriesAnalyzer', 'PortfolioOptimizer']