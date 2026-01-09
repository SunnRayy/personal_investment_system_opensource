"""
CSV/Excel Importer for user data uploads.

Provides flexible import functionality with:
- Auto-detection of file format and encoding
- Column mapping support
- Data validation and error reporting
- Duplicate detection
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import chardet

logger = logging.getLogger(__name__)


@dataclass
class ImportResult:
    """Result of an import operation."""
    success: bool
    rows_imported: int = 0
    rows_skipped: int = 0
    errors: List[Dict[str, Any]] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class CSVImporter:
    """
    Unified CSV/Excel importer with flexible column mapping.
    
    Supports:
    - CSV files (auto-detect delimiter and encoding)
    - Excel files (.xlsx, .xls)
    - Column mapping for non-standard formats
    - Data validation and type conversion
    """
    
    # Standard column names expected by the system
    STANDARD_COLUMNS = {
        'date': ['date', 'transaction_date', 'trade_date', 'Date', 'DATE'],
        'description': ['description', 'desc', 'name', 'memo', 'Description', 'DESCRIPTION'],
        'amount': ['amount', 'value', 'net_amount', 'Amount', 'AMOUNT', 'Market Value'],
        'category': ['category', 'type', 'transaction_type', 'Category', 'TYPE'],
        'account': ['account', 'Account', 'account_name', 'ACCOUNT'],
        'symbol': ['symbol', 'ticker', 'Symbol', 'SYMBOL'],
        'quantity': ['quantity', 'qty', 'shares', 'Quantity', 'QUANTITY'],
        'price': ['price', 'unit_price', 'Price', 'PRICE'],
    }
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the importer.
        
        Args:
            data_dir: Directory for user uploads. Uses DATA_DIR env var or 'data' as default.
        """
        self.data_dir = Path(data_dir or os.environ.get('DATA_DIR', 'data'))
        self.upload_dir = self.data_dir / 'user_uploads'
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def detect_encoding(self, filepath: str) -> str:
        """
        Detect file encoding.
        
        Args:
            filepath: Path to file
            
        Returns:
            Detected encoding (default: utf-8)
        """
        with open(filepath, 'rb') as f:
            result = chardet.detect(f.read(10000))
        return result.get('encoding', 'utf-8')
    
    def detect_delimiter(self, filepath: str, encoding: str = 'utf-8') -> str:
        """
        Detect CSV delimiter.
        
        Args:
            filepath: Path to CSV file
            encoding: File encoding
            
        Returns:
            Detected delimiter (default: comma)
        """
        import csv
        with open(filepath, 'r', encoding=encoding) as f:
            sample = f.read(8192)
            sniffer = csv.Sniffer()
            try:
                dialect = sniffer.sniff(sample)
                return dialect.delimiter
            except csv.Error:
                return ','
    
    def read_file(self, filepath: str, nrows: Optional[int] = None) -> Tuple[pd.DataFrame, List[str]]:
        """
        Read CSV or Excel file into DataFrame.
        
        Args:
            filepath: Path to file
            nrows: Number of rows to read (None for all)
            
        Returns:
            Tuple of (DataFrame, list of warnings)
        """
        filepath = Path(filepath)
        warnings = []
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        ext = filepath.suffix.lower()
        
        if ext == '.csv':
            # Detect encoding and delimiter
            encoding = self.detect_encoding(str(filepath))
            delimiter = self.detect_delimiter(str(filepath), encoding)
            
            df = pd.read_csv(filepath, encoding=encoding, delimiter=delimiter, nrows=nrows)
            logger.info(f"Read CSV file: {filepath.name} (encoding={encoding}, delimiter='{delimiter}')")
            
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(filepath, nrows=nrows)
            logger.info(f"Read Excel file: {filepath.name}")
            
        else:
            raise ValueError(f"Unsupported file format: {ext}")
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        return df, warnings
    
    def auto_detect_mapping(self, columns: List[str]) -> Dict[str, str]:
        """
        Auto-detect column mapping based on column names.
        
        Args:
            columns: List of column names from file
            
        Returns:
            Dictionary mapping standard names to actual column names
        """
        mapping = {}
        
        for standard_name, possible_names in self.STANDARD_COLUMNS.items():
            for col in columns:
                col_lower = col.lower().strip()
                if col_lower in [n.lower() for n in possible_names]:
                    mapping[standard_name] = col
                    break
        
        return mapping
    
    def validate_data(self, df: pd.DataFrame, mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Validate data before import.
        
        Args:
            df: DataFrame to validate
            mapping: Column mapping
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check required columns
        if 'date' not in mapping or not mapping['date']:
            errors.append({
                'type': 'missing_column',
                'message': 'Date column is required',
                'column': 'date'
            })
        
        if 'amount' not in mapping or not mapping['amount']:
            errors.append({
                'type': 'missing_column', 
                'message': 'Amount column is required',
                'column': 'amount'
            })
        
        if errors:
            return errors
        
        # Validate date format
        date_col = mapping['date']
        for idx, value in df[date_col].items():
            try:
                pd.to_datetime(value)
            except (ValueError, TypeError):
                errors.append({
                    'type': 'invalid_date',
                    'row': idx + 2,  # 1-indexed + header
                    'column': date_col,
                    'value': str(value),
                    'message': f'Invalid date format at row {idx + 2}'
                })
        
        # Validate amount format
        amount_col = mapping['amount']
        for idx, value in df[amount_col].items():
            try:
                if pd.notna(value):
                    # Remove currency symbols and commas
                    clean_val = str(value).replace('$', '').replace(',', '').replace('¥', '')
                    float(clean_val)
            except (ValueError, TypeError):
                errors.append({
                    'type': 'invalid_amount',
                    'row': idx + 2,
                    'column': amount_col,
                    'value': str(value),
                    'message': f'Invalid amount format at row {idx + 2}'
                })
        
        return errors
    
    def transform_data(self, df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
        """
        Transform imported data to standard format.
        
        Args:
            df: Source DataFrame
            mapping: Column mapping
            
        Returns:
            Transformed DataFrame with standard columns
        """
        result = pd.DataFrame()
        
        # Map columns
        for standard_name, source_col in mapping.items():
            if source_col and source_col in df.columns:
                result[standard_name] = df[source_col]
        
        # Parse dates
        if 'date' in result.columns:
            result['date'] = pd.to_datetime(result['date'], errors='coerce')
        
        # Clean amounts
        if 'amount' in result.columns:
            result['amount'] = result['amount'].apply(self._clean_amount)
        
        # Clean quantities
        if 'quantity' in result.columns:
            result['quantity'] = pd.to_numeric(result['quantity'], errors='coerce')
        
        # Clean prices
        if 'price' in result.columns:
            result['price'] = result['price'].apply(self._clean_amount)
        
        # Add import metadata
        result['imported_at'] = datetime.now()
        result['source_file'] = df.attrs.get('source_file', 'unknown')
        
        return result
    
    def _clean_amount(self, value) -> Optional[float]:
        """Clean amount value by removing currency symbols and formatting."""
        if pd.isna(value):
            return None
        
        try:
            # Convert to string and clean
            clean = str(value).replace('$', '').replace('¥', '').replace(',', '').strip()
            # Handle parentheses for negative numbers
            if clean.startswith('(') and clean.endswith(')'):
                clean = '-' + clean[1:-1]
            return float(clean)
        except (ValueError, TypeError):
            return None
    
    def import_file(
        self, 
        filepath: str, 
        mapping: Optional[Dict[str, str]] = None,
        validate: bool = True
    ) -> ImportResult:
        """
        Import a file with optional column mapping.
        
        Args:
            filepath: Path to file
            mapping: Optional column mapping (auto-detected if not provided)
            validate: Whether to validate data before import
            
        Returns:
            ImportResult with status and details
        """
        try:
            # Read file
            df, warnings = self.read_file(filepath)
            df.attrs['source_file'] = Path(filepath).name
            
            # Auto-detect mapping if not provided
            if mapping is None:
                mapping = self.auto_detect_mapping(list(df.columns))
            
            # Validate if requested
            if validate:
                errors = self.validate_data(df, mapping)
                if errors:
                    return ImportResult(
                        success=False,
                        errors=errors,
                        warnings=warnings
                    )
            
            # Transform data
            transformed = self.transform_data(df, mapping)
            
            # Count results
            rows_imported = len(transformed)
            rows_skipped = len(df) - rows_imported
            
            logger.info(f"Import complete: {rows_imported} rows imported, {rows_skipped} skipped")
            
            return ImportResult(
                success=True,
                rows_imported=rows_imported,
                rows_skipped=rows_skipped,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Import failed: {e}")
            return ImportResult(
                success=False,
                errors=[{
                    'type': 'system_error',
                    'message': str(e)
                }]
            )


def import_transactions(filepath: str, mapping: Dict[str, str]) -> ImportResult:
    """
    Convenience function to import transactions.
    
    Args:
        filepath: Path to file
        mapping: Column mapping
        
    Returns:
        ImportResult
    """
    importer = CSVImporter()
    return importer.import_file(filepath, mapping)
