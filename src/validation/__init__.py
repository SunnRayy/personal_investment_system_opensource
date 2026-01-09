"""
Data Validation Module

This module provides automated data quality validation for the Personal Investment System.
It implements the "Sentinel" framework from Project Cornerstone.
"""

from .reporter import ValidationIssue, generate_report
from .engine import ValidationEngine

__all__ = ['ValidationIssue', 'generate_report', 'ValidationEngine']
