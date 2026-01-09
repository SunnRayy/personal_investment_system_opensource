# File path: src/database/models.py
"""
SQLAlchemy ORM models for the Personal Investment System database.

This module defines all database tables as SQLAlchemy models, including:
- Core data: Transactions, Holdings, Assets, Balance Sheets
- Configuration: Asset Taxonomy, Mappings, Settings, Benchmarks
- System: Audit Trail, Import Log, Backup Manifest, Config History
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Column, String, Integer, Numeric, Date, DateTime, Boolean, Text,
    ForeignKey, Index, JSON, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship
from .base import Base


# ============================================================================
# CORE DATA MODELS
# ============================================================================

class Transaction(Base):
    """
    Transaction records - replaces Excel transaction sheets.
    
    Stores all investment transactions including buys, sells, dividends,
    and other cash flows for XIRR and cost basis calculations.
    """
    __tablename__ = 'transactions'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Business key (for deduplication)
    transaction_id = Column(String(100), unique=True, nullable=False, index=True,
                           comment="Generated hash for deduplication")
    
    # Transaction details
    date = Column(Date, nullable=False, index=True, comment="Transaction date")
    asset_id = Column(String(100), ForeignKey('assets.asset_id'), nullable=False, index=True)
    asset_name = Column(String(200), nullable=False, comment="Display name")
    transaction_type = Column(String(50), nullable=False, index=True,
                            comment="Buy, Sell, Dividend_Cash, etc.")
    
    # Quantities and prices
    shares = Column(Numeric(18, 6), comment="Number of shares (NULL for cash-only transactions)")
    price = Column(Numeric(18, 6), comment="Price per share (NULL for cash-only)")
    amount = Column(Numeric(18, 2), nullable=False, comment="Total transaction amount")
    
    # Currency handling
    currency = Column(String(10), default='CNY', comment="Transaction currency")
    exchange_rate = Column(Numeric(10, 6), comment="Exchange rate to CNY if not CNY")
    
    # Metadata
    source = Column(String(50), comment="CN_Fund, Schwab, Manual_Excel, etc.")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(50), default='system', comment="User or system component")
    
    # Relationships
    asset = relationship("Asset", back_populates="transactions")
    
    # Indexes
    __table_args__ = (
        Index('idx_transactions_date_asset', 'date', 'asset_id'),
        Index('idx_transactions_type_date', 'transaction_type', 'date'),
    )
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, date={self.date}, asset={self.asset_name}, type={self.transaction_type}, amount={self.amount})>"


class Holding(Base):
    """
    Holdings snapshot - current and historical positions.
    
    Stores point-in-time snapshots of portfolio positions for
    performance tracking and historical analysis.
    """
    __tablename__ = 'holdings'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Snapshot identification
    snapshot_date = Column(Date, nullable=False, index=True, comment="Date of this snapshot")
    asset_id = Column(String(100), ForeignKey('assets.asset_id'), nullable=False, index=True)
    asset_name = Column(String(200), nullable=False, comment="Display name")
    
    # Position details
    shares = Column(Numeric(18, 6), comment="Number of shares held")
    current_price = Column(Numeric(18, 6), comment="Price per share at snapshot date")
    market_value = Column(Numeric(18, 2), comment="Total market value (shares * price)")
    cost_basis = Column(Numeric(18, 2), comment="Total cost basis (FIFO/LIFO)")
    unrealized_pnl = Column(Numeric(18, 2), comment="Unrealized profit/loss")
    
    # Currency
    currency = Column(String(10), default='CNY')
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    asset = relationship("Asset", back_populates="holdings")
    
    # Constraints: One snapshot per asset per date
    __table_args__ = (
        UniqueConstraint('snapshot_date', 'asset_id', name='uq_holding_snapshot'),
        Index('idx_holdings_date_asset', 'snapshot_date', 'asset_id'),
    )
    
    def __repr__(self):
        return f"<Holding(date={self.snapshot_date}, asset={self.asset_name}, shares={self.shares}, value={self.market_value})>"


class Asset(Base):
    """
    Assets master table - metadata for all investment assets.
    
    Stores asset definitions including funds, stocks, ETFs, RSUs, insurance, etc.
    Links to transactions and holdings.
    """
    __tablename__ = 'assets'
    
    # Primary key
    asset_id = Column(String(100), primary_key=True, comment="Standardized asset identifier")
    
    # Asset metadata
    asset_name = Column(String(200), nullable=False, comment="Display name")
    asset_type = Column(String(100), comment="Fund, ETF, Stock, RSU, Insurance, etc.")
    asset_class = Column(String(100), comment="Equity, Fixed_Income, Alternative, etc.")
    asset_subclass = Column(String(100), comment="Sub-category within asset class")
    risk_level = Column(String(20), comment="Low, Medium, High")
    
    # Status
    is_active = Column(Boolean, default=True, comment="False if asset no longer held")
    
    # Flexible metadata storage
    metadata_json = Column(JSON, comment="Asset-specific fields (fund codes, tickers, etc.)")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="asset", cascade="all, delete-orphan")
    holdings = relationship("Holding", back_populates="asset", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Asset(id={self.asset_id}, name={self.asset_name}, type={self.asset_type})>"


class BalanceSheet(Base):
    """
    Balance sheet snapshots - historical financial position.
    
    Stores monthly/daily snapshots of assets, liabilities, and equity
    for trend analysis and financial health tracking.
    """
    __tablename__ = 'balance_sheets'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Snapshot identification
    snapshot_date = Column(Date, nullable=False, index=True, comment="Date of snapshot")
    
    # Classification
    category = Column(String(100), comment="Asset, Liability, or Equity")
    subcategory = Column(String(100), comment="Cash, Investments, Debt, etc.")
    line_item = Column(String(200), comment="Specific item name")
    
    # Financial data
    amount = Column(Numeric(18, 2), comment="Amount in specified currency")
    currency = Column(String(10), default='CNY')
    
    # Additional info
    notes = Column(Text, comment="Optional notes or context")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_balance_sheet_date_category', 'snapshot_date', 'category'),
    )
    
    def __repr__(self):
        return f"<BalanceSheet(date={self.snapshot_date}, category={self.category}, item={self.line_item}, amount={self.amount})>"


# ============================================================================
# CONFIGURATION MODELS
# ============================================================================

class AssetTaxonomy(Base):
    """
    Asset taxonomy - classification hierarchy (replaces asset_taxonomy.yaml).
    
    Defines asset classes, sub-classes, target allocations, and risk profiles
    for portfolio construction and optimization.
    """
    __tablename__ = 'asset_taxonomy'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Classification hierarchy
    asset_class = Column(String(100), nullable=False, comment="Top-level class (Equity, Fixed_Income, etc.)")
    asset_subclass = Column(String(100), comment="Sub-category within class")
    display_name = Column(String(200), comment="User-friendly name")
    
    # Portfolio management
    target_allocation = Column(Numeric(5, 2), comment="Target allocation percentage (0-100)")
    risk_level = Column(String(20), comment="Low, Medium, High")
    benchmark_index = Column(String(100), comment="Benchmark for performance comparison")
    
    # Hierarchy support
    parent_class = Column(String(100), comment="Parent class for nested hierarchies")
    
    # Flexible metadata
    metadata_json = Column(JSON, comment="Additional configuration")
    
    # Versioning
    version = Column(Integer, default=1, comment="Config version for rollback")
    is_active = Column(Boolean, default=True, comment="False if deprecated")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Constraints: One taxonomy entry per class/subclass/version
    __table_args__ = (
        UniqueConstraint('asset_class', 'asset_subclass', 'version', name='uq_taxonomy_version'),
    )
    
    def __repr__(self):
        return f"<AssetTaxonomy(class={self.asset_class}, subclass={self.asset_subclass}, target={self.target_allocation}%)>"


class AssetMapping(Base):
    """
    Asset mappings - fund names to asset classes (replaces manual YAML mappings).
    
    Maps asset names or patterns to asset classes for automated categorization.
    Supports explicit mappings and fuzzy pattern matching.
    """
    __tablename__ = 'asset_mappings'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Mapping definition
    asset_id = Column(String(100), ForeignKey('assets.asset_id'), comment="Explicit asset ID")
    asset_name_pattern = Column(String(200), comment="Pattern for fuzzy matching")
    
    # Target classification
    asset_class = Column(String(100), nullable=False, comment="Target asset class")
    asset_subclass = Column(String(100), comment="Target sub-class")
    
    # Mapping metadata
    mapping_type = Column(String(50), default='Explicit', comment="Explicit, Pattern, or Manual")
    priority = Column(Integer, default=0, comment="Higher priority wins in conflicts")
    is_active = Column(Boolean, default=True, comment="False if disabled")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(50), default='system')
    
    def __repr__(self):
        return f"<AssetMapping(pattern={self.asset_name_pattern}, class={self.asset_class}, priority={self.priority})>"


class SystemSetting(Base):
    """
    System settings - configuration parameters (replaces settings.yaml).
    
    Stores all system configuration as key-value pairs with versioning
    and type metadata for validation.
    """
    __tablename__ = 'system_settings'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Setting definition
    setting_key = Column(String(100), unique=True, nullable=False, index=True, comment="Unique setting identifier")
    setting_value = Column(Text, comment="Setting value (JSON string for complex values)")
    setting_type = Column(String(50), comment="string, integer, json, boolean, etc.")
    description = Column(Text, comment="What this setting controls")
    
    # Versioning
    version = Column(Integer, default=1, comment="Setting version for rollback")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<SystemSetting(key={self.setting_key}, value={self.setting_value[:50] if self.setting_value else None})>"


class Benchmark(Base):
    """
    Benchmarks - performance comparison indices (replaces benchmark.yaml).
    
    Stores benchmark definitions for portfolio performance comparison,
    including both standard indices and custom composite benchmarks.
    """
    __tablename__ = 'benchmarks'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Benchmark definition
    benchmark_name = Column(String(100), nullable=False, unique=True, comment="Unique benchmark name")
    benchmark_type = Column(String(50), comment="Index or Custom")
    ticker_symbol = Column(String(20), comment="Ticker for standard indices")
    
    # Custom benchmark composition
    composition = Column(JSON, comment="Dict of {ticker: weight} for custom benchmarks")
    
    # Data source
    data_source = Column(String(50), comment="Yahoo, Manual, Calculated, etc.")
    is_active = Column(Boolean, default=True, comment="False if no longer used")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Benchmark(name={self.benchmark_name}, type={self.benchmark_type}, ticker={self.ticker_symbol})>"


# ============================================================================
# SYSTEM MANAGEMENT MODELS
# ============================================================================

class AuditTrail(Base):
    """
    Audit trail - tracks all data modifications.
    
    Records every change to the database for compliance, debugging,
    and rollback capabilities. Immutable log.
    """
    __tablename__ = 'audit_trail'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Event details
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    user = Column(String(50), default='system', comment="User or system component")
    action = Column(String(50), comment="INSERT, UPDATE, DELETE, IMPORT, ROLLBACK")
    
    # Target identification
    table_name = Column(String(100), index=True, comment="Table that was modified")
    record_id = Column(String(100), comment="Primary key of modified record")
    
    # Change details
    old_value = Column(JSON, comment="Record state before change")
    new_value = Column(JSON, comment="Record state after change")
    reason = Column(Text, comment="Why this change was made")
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_timestamp_table', 'timestamp', 'table_name'),
        Index('idx_audit_user_action', 'user', 'action'),
    )
    
    def __repr__(self):
        return f"<AuditTrail(timestamp={self.timestamp}, user={self.user}, action={self.action}, table={self.table_name})>"


class ImportLog(Base):
    """
    Import log - tracks file import operations.
    
    Records every data import with success/failure status and error details
    to enable rollback and troubleshooting.
    """
    __tablename__ = 'import_log'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Import details
    import_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    source_file = Column(String(200), comment="Original filename")
    source_type = Column(String(50), comment="Excel, CSV, API")
    
    # Results
    records_imported = Column(Integer, default=0, comment="Successfully imported")
    records_updated = Column(Integer, default=0, comment="Updated existing records")
    records_failed = Column(Integer, default=0, comment="Failed validation")
    error_log = Column(Text, comment="Error messages and stack traces")
    
    # Metadata
    imported_by = Column(String(50), default='system')
    status = Column(String(20), comment="Success, Partial, or Failed")
    can_rollback = Column(Boolean, default=True, comment="False if data can't be undone")
    
    def __repr__(self):
        return f"<ImportLog(date={self.import_date}, file={self.source_file}, status={self.status}, imported={self.records_imported})>"


class BackupManifest(Base):
    """
    Backup manifest - tracks database backups.
    
    Records metadata about each backup file for retention management
    and restore operations.
    """
    __tablename__ = 'backup_manifest'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Backup details
    backup_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    backup_file = Column(String(200), nullable=False, comment="Backup filename")
    backup_type = Column(String(20), comment="Full or Incremental")
    
    # File metadata
    file_size_mb = Column(Numeric(10, 2), comment="Backup file size in MB")
    checksum = Column(String(64), comment="SHA256 hash for integrity verification")
    
    # Verification
    is_verified = Column(Boolean, default=False, comment="True if restore test passed")
    
    # Retention
    retention_until = Column(Date, comment="Delete backup after this date")
    notes = Column(Text, comment="Optional backup notes")
    
    def __repr__(self):
        return f"<BackupManifest(date={self.backup_date}, file={self.backup_file}, type={self.backup_type}, size={self.file_size_mb}MB)>"


class ConfigHistory(Base):
    """
    Config history - version control for configurations.
    
    Snapshots configuration changes to enable rollback and
    audit who changed what when.
    """
    __tablename__ = 'config_history'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Change details
    config_table = Column(String(100), index=True, comment="Which config table was changed")
    config_id = Column(Integer, comment="Primary key of the config record")
    change_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    changed_by = Column(String(50), default='system')
    change_type = Column(String(20), comment="CREATE, UPDATE, or DELETE")
    
    # Snapshot
    snapshot = Column(JSON, comment="Full config state at this version")
    change_reason = Column(Text, comment="Why this change was made")
    
    # Indexes
    __table_args__ = (
        Index('idx_config_history_table_date', 'config_table', 'change_date'),
    )
    
    def __repr__(self):
        return f"<ConfigHistory(table={self.config_table}, id={self.config_id}, type={self.change_type}, date={self.change_date})>"


# ============================================================================
# PHASE 6: SYSTEM UNIFICATION - ADDITIONAL DATA MODELS
# ============================================================================

class MonthlyFinancialSnapshot(Base):
    """
    Monthly financial snapshots - replaces 月度收支 Excel sheet.
    
    Stores monthly income/expense tracking and savings rate calculations
    for financial health monitoring and cash flow analysis.
    """
    __tablename__ = 'monthly_financial_snapshots'
    
    # Primary key
    snapshot_date = Column(Date, primary_key=True, comment="Month end date (e.g., 2025-11-30)")
    
    # Income sources
    salary_income = Column(Numeric(18, 2), comment="Monthly salary/wages")
    rsu_income = Column(Numeric(18, 2), comment="RSU vesting income")
    investment_income = Column(Numeric(18, 2), comment="Dividends, interest, realized gains")
    other_income = Column(Numeric(18, 2), comment="Other income sources")
    total_income = Column(Numeric(18, 2), nullable=False, comment="Sum of all income")
    
    # Expense categories
    housing_expense = Column(Numeric(18, 2), comment="Rent/mortgage, utilities")
    living_expense = Column(Numeric(18, 2), comment="Food, transportation, daily expenses")
    healthcare_expense = Column(Numeric(18, 2), comment="Medical, insurance premiums")
    entertainment_expense = Column(Numeric(18, 2), comment="Travel, hobbies, dining out")
    investment_expense = Column(Numeric(18, 2), comment="Investment purchases (not counted in savings)")
    other_expense = Column(Numeric(18, 2), comment="Other expenses")
    total_expense = Column(Numeric(18, 2), nullable=False, comment="Sum of all expenses")
    
    # Derived metrics
    net_savings = Column(Numeric(18, 2), comment="Total income - Total expense")
    savings_rate = Column(Numeric(5, 2), comment="Savings rate percentage (0-100)")
    
    # Notes
    notes = Column(Text, comment="Month commentary or special events")
    
    # Currency
    currency = Column(String(10), default='CNY', nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(50), default='system')
    
    def __repr__(self):
        return f"<MonthlyFinancialSnapshot(date={self.snapshot_date}, income={self.total_income}, expense={self.total_expense}, savings_rate={self.savings_rate}%)>"


class InsurancePremium(Base):
    """
    Insurance premium payments - replaces 保费记录 Excel sheet.
    
    Tracks insurance premium payment history for healthcare insurance policies.
    Note: Insurance is healthcare-only, not investment products.
    """
    __tablename__ = 'insurance_premiums'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Insurance policy identification
    policy_id = Column(String(100), nullable=False, index=True, comment="Policy identifier")
    policy_name = Column(String(200), nullable=False, comment="Policy display name")
    insurer = Column(String(100), comment="Insurance company name")
    
    # Premium payment
    payment_date = Column(Date, nullable=False, index=True, comment="Date premium was paid")
    premium_amount = Column(Numeric(18, 2), nullable=False, comment="Premium payment amount")
    payment_frequency = Column(String(20), comment="Annual, Semi-Annual, Monthly, etc.")
    
    # Policy details
    coverage_start = Column(Date, comment="Policy coverage start date")
    coverage_end = Column(Date, comment="Policy coverage end date")
    insured_person = Column(String(100), comment="Name of insured person")
    
    # Notes
    notes = Column(Text, comment="Payment notes or special terms")
    
    # Currency
    currency = Column(String(10), default='CNY', nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(50), default='system')
    
    # Indexes
    __table_args__ = (
        Index('idx_insurance_premiums_date_policy', 'payment_date', 'policy_id'),
    )
    
    def __repr__(self):
        return f"<InsurancePremium(policy={self.policy_name}, date={self.payment_date}, amount={self.premium_amount})>"


class MarketDataNAV(Base):
    """
    Market data - Net Asset Values for CN funds.
    
    Stores daily NAV (Net Asset Value) data for Chinese mutual funds
    to support price fetching in PriceService.
    """
    __tablename__ = 'market_data_nav'
    
    # Composite primary key
    asset_id = Column(String(100), primary_key=True, comment="Asset identifier (fund code)")
    date = Column(Date, primary_key=True, index=True, comment="NAV date")
    
    # NAV data
    nav = Column(Numeric(18, 6), nullable=False, comment="Net Asset Value per unit")
    accumulated_nav = Column(Numeric(18, 6), comment="Accumulated NAV (includes dividends)")
    
    # Additional data
    daily_growth_rate = Column(Numeric(8, 4), comment="Daily growth rate percentage")
    
    # Data source
    source = Column(String(50), comment="Data source (API name, manual, etc.)")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_market_data_nav_asset_date', 'asset_id', 'date'),
    )
    
    def __repr__(self):
        return f"<MarketDataNAV(asset={self.asset_id}, date={self.date}, nav={self.nav})>"
