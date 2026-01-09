"""
Performance Attribution Module

This module provides sophisticated performance attribution analysis using the Brinson-Fachler model
to decompose portfolio returns into allocation, selection, and interaction effects.

Components:
- AttributionModel: Core Brinson-Fachler attribution calculations
- BenchmarkManager: Handles benchmark configuration and data
- BenchmarkPerformance: Real market data integration for benchmark returns
- AttributionReporter: Generates attribution reports and visualizations

Author: Personal Investment System
Date: August 2025
"""

from .attribution_model import (
    AttributionModel, 
    AttributionResult,
    MultiPeriodAttributionModel,
    MultiPeriodAttributionResult
)
from .benchmark_manager import BenchmarkManager
from .benchmark_performance import BenchmarkPerformance
from .data_adapter import AttributionDataAdapter

__all__ = [
    'AttributionModel',
    'AttributionResult',
    'MultiPeriodAttributionModel',
    'MultiPeriodAttributionResult',
    'AttributionDataAdapter',
    'BenchmarkManager',
    'BenchmarkPerformance'
]

__version__ = '1.0.0'
