"""
Data Manager Module

Provides comprehensive data management capabilities for the personal investment system.

Core Components:
- manager.py: Main DataManager class
- historical_manager.py: Enhanced HistoricalDataManager with multi-timeframe support
- readers.py: Excel file reading utilities
- cleaners.py: Data cleaning and transformation
- calculators.py: Financial calculations and currency conversion
- snapshot_generator.py: Historical snapshot generation utilities

Enhanced Features (Phase 3):
- Multi-timeframe historical analysis
- Enhanced metadata generation
- Robust gap-filling and validation
- Production-ready historical data infrastructure
"""

from .manager import DataManager
from .historical_manager import HistoricalDataManager
from .currency_converter import initialize_currency_service, get_currency_service
from .fund_data_writer import write_processed_fund_data

__all__ = [
    'DataManager', 
    'HistoricalDataManager', 
    'initialize_currency_service', 
    'get_currency_service',
    'write_processed_fund_data'
]