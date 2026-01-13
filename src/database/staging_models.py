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


class ImportSession(Base):
    """
    Tracks multi-step import wizard sessions.
    
    Persists wizard state across HTTP requests, storing uploaded file data,
    column mappings, and validation results as the user progresses through steps.
    """
    __tablename__ = 'import_sessions'
    
    # Primary key (UUID)
    id = Column(String(36), primary_key=True, comment="UUID session identifier")
    
    # Wizard State
    import_type = Column(String(50), nullable=False, 
                        comment="transactions, holdings, or accounts")
    current_step = Column(Integer, default=1, 
                         comment="Current wizard step (1-5)")
    status = Column(String(20), default='pending', index=True,
                   comment="pending, processing, completed, abandoned")
    
    # Step 2: Upload Data
    filename = Column(String(500), comment="Original uploaded filename")
    file_path = Column(String(1000), comment="Server path to uploaded file")
    detected_headers = Column(JSON, comment="Column headers from file")
    preview_data = Column(JSON, comment="First N rows for preview")
    total_rows = Column(Integer, comment="Total rows in uploaded file")
    
    # Step 3: Configuration
    column_mapping = Column(JSON, comment="User-confirmed column mapping")
    date_format = Column(String(50), comment="e.g., MM/DD/YYYY, YYYY-MM-DD")
    number_format = Column(String(20), comment="us (1,234.56) or eu (1.234,56)")
    
    # Step 4: Validation Results
    valid_rows = Column(Integer, default=0)
    error_rows = Column(Integer, default=0)
    validation_errors = Column(JSON, comment="List of row errors")
    
    # Step 5: Publish Results
    batch_id = Column(String(50), comment="Batch ID after publish")
    imported_count = Column(Integer, comment="Records successfully imported")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, comment="When import was completed")
    
    def __repr__(self):
        return f"<ImportSession(id={self.id}, type={self.import_type}, step={self.current_step})>"
