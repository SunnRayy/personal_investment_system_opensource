# File path: src/database/__init__.py
"""
Database persistence layer for the Personal Investment System.

This module provides SQLAlchemy ORM models and database management utilities
to replace Excel-based data storage with a robust, queryable database.
"""

from .base import Base, get_engine, get_session, init_database, reset_engine
from .migrator import DatabaseMigrator
from .connector import DatabaseConnector
from .models import (
    Transaction,
    Holding,
    Asset,
    BalanceSheet,
    AssetTaxonomy,
    AssetMapping,
    SystemSetting,
    Benchmark,
    AuditTrail,
    ImportLog,
    BackupManifest,
    ConfigHistory,
    MonthlyFinancialSnapshot,
    InsurancePremium,
    MarketDataNAV,
)
from .staging_models import StagingTransaction, ImportHistory, ImportSession
from .logic_models import Taxonomy, Tag, AssetTag, CalculationStrategy, ClassificationRule, RiskProfile, TargetAllocation

__all__ = [
    # Base infrastructure
    'Base',
    'get_engine',
    'get_session',
    'init_database',
    'reset_engine',
    # Migration tool
    'DatabaseMigrator',
    # Database connector
    'DatabaseConnector',
    # Core data models
    'Transaction',
    'Holding',
    'Asset',
    'BalanceSheet',
    # Configuration models
    'AssetTaxonomy',
    'AssetMapping',
    'SystemSetting',
    'Benchmark',
    # System models
    'AuditTrail',
    'ImportLog',
    'BackupManifest',
    'ConfigHistory',
    'StagingTransaction',
    'ImportHistory',
    'ImportSession',
    # Logic Layer models
    'Taxonomy',
    'Tag',
    'AssetTag',
    'CalculationStrategy',
    'ClassificationRule',
    'RiskProfile',
    'TargetAllocation'
]
