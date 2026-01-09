"""
Unified Analysis Module

This module provides a comprehensive analysis engine that integrates all system modules
to deliver end-to-end financial analysis and portfolio optimization capabilities.

Key Components:
- FinancialAnalysisEngine: Main orchestrator for complete analysis workflow
- DataPipeline: Manages data flow between modules
- ConfigManager: Handles analysis configuration and user preferences
- Validators: Cross-module data validation and quality assurance
"""

from .engine import FinancialAnalysisEngine
from .pipeline import DataPipeline
from .config_manager import AnalysisConfig, ConfigManager
from .validators import DataValidator, IntegrationValidator

__all__ = [
    'FinancialAnalysisEngine',
    'DataPipeline', 
    'AnalysisConfig',
    'ConfigManager',
    'DataValidator',
    'IntegrationValidator'
]

__version__ = "1.0.0"
