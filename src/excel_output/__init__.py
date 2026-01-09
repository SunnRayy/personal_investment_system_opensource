"""
Excel Output System for Personal Investment Analysis

This module provides comprehensive Excel report generation capabilities
for financial analysis and investment recommendations.
"""

from .report_generator import ExcelReportGenerator
from .formatters import ExcelFormatter
from .chart_builder import ChartBuilder
from .worksheet_manager import WorksheetManager
from .template_loader import TemplateLoader

__all__ = [
    'ExcelReportGenerator',
    'ExcelFormatter', 
    'ChartBuilder',
    'WorksheetManager',
    'TemplateLoader'
]

__version__ = "1.0.0"
__author__ = "Personal Investment System"
