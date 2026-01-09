# File path: src/database/staging_models.py
"""
Staging models for the Data Workbench.

These models are used for temporary storage of imported data before it is
validated and promoted to the production tables. They have looser constraints
and include fields for validation status and error tracking.
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Numeric, Date, DateTime, Boolean, Text,
    JSON, Index
)
from .base import Base

class StagingTransaction(Base):
    """
    Staging area for raw transaction imports.
    
    Allows importing "messy" data without strict foreign key constraints.
    Used by the Data Workbench to clean and validate data before promotion.
    """
    __tablename__ = 'staging_transactions'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Import Batch Tracking
    batch_id = Column(String(50), index=True, comment="ID of the upload batch")
    row_number = Column(Integer, comment="Row number in original file")
    
    # Status
    status = Column(String(20), default='PENDING', index=True, 
                   comment="PENDING, VALID, ERROR, IGNORED, PROMOTED")
    validation_errors = Column(JSON, comment="List of validation error messages")
    
    # Raw Data (As imported)
    raw_data = Column(JSON, comment="Original row data as JSON")
    
    # Mapped Fields (To be promoted to Transaction)
    # Note: No Foreign Keys here to allow "dirty" data
    transaction_id = Column(String(100), index=True, comment="Generated hash")
    date = Column(Date, index=True)
    asset_id = Column(String(100), index=True)
    asset_name = Column(String(200))
    transaction_type = Column(String(50))
    
    shares = Column(Numeric(18, 6))
    price = Column(Numeric(18, 6))
    amount = Column(Numeric(18, 2))
    
    currency = Column(String(10), default='CNY')
    exchange_rate = Column(Numeric(10, 6))
    source = Column(String(50))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<StagingTransaction(id={self.id}, status={self.status}, asset={self.asset_name})>"


class ImportHistory(Base):
    """
    Tracks all data imports for audit trail and troubleshooting.
    
    Records metadata about each upload batch including file details,
    row counts, and processing status.
    """
    __tablename__ = 'import_history'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Batch Information
    batch_id = Column(String(50), nullable=False, index=True, unique=True,
                     comment="Unique identifier for this import batch")
    
    # File Information
    filename = Column(String(500), comment="Original uploaded filename")
    file_size = Column(Integer, comment="File size in bytes")
    
    # Row Counts
    total_rows = Column(Integer, default=0, comment="Total rows imported")
    valid_rows = Column(Integer, default=0, comment="Rows that passed validation")
    error_rows = Column(Integer, default=0, comment="Rows with validation errors")
    promoted_rows = Column(Integer, default=0, comment="Rows promoted to production")
    
    # Status
    status = Column(String(50), default='uploaded', index=True,
                   comment="uploaded, promoted, cleared, partial")
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    promoted_at = Column(DateTime, comment="When records were promoted")
    cleared_at = Column(DateTime, comment="When staging was cleared")
    
    # Additional metadata
    notes = Column(Text, comment="Optional notes or error details")
    
    def __repr__(self):
        return f"<ImportHistory(batch={self.batch_id}, file={self.filename}, status={self.status})>"
