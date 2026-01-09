"""
Smart column mapper and data cleaner for Data Workbench.

Handles multiple data sources with different column names, formats, and languages.
"""

import re
from datetime import datetime
import pandas as pd
from typing import Dict, Any, Optional, List

# Column name mappings (flexible matching)
COLUMN_MAPPINGS = {
    'date': [
        'Date', '日期', '交易日期', '确认日期', '净值日期', 'date',
        'transaction_date', 'Date'
    ],
    'asset_id': [
        'Asset_ID', 'Symbol', '基金代码', '股票代码', '标的名称',
        'asset_id', 'symbol', 'ticker'
    ],
    'asset_name': [
        'Asset_Name', 'Description', '基金名称', '基金简称', '资产名称',
        '股票名称', '产品名称', '标的名称', 'asset_name', 'name'
    ],
    'transaction_type': [
        'Transaction_Type', 'Action', '操作类型', '业务类型', '交易类型',
        'transaction_type', 'type', 'action'
    ],
    'amount': [
        'Amount', 'Amount_Net', '交易金额', '确认金额', '金额', '总金额_USD',
        'amount', 'net_amount'
    ],
    'shares': [
        'Quantity', 'Qty', '数量', '交易份额', '持有份额', '确认份额',
        'quantity', 'shares', 'Shares'
    ],
    'price': [
        'Price', '价格', '单位净值', '确认净值', '交易时基金单位净值', '单价',
        '单位价格_USD', 'price', 'unit_price'
    ],
    'fees': [
        'Fees \u0026 Comm', 'Fees & Comm', '手续费', 'Fee', 'fees', 'commission'
    ]
}

# Transaction type normalization
TRANSACTION_TYPE_MAPPING = {
    # English
    'Buy': 'Buy',
    'Sell': 'Sell',
    'Cash Dividend': 'Dividend',
    'Reinvest Dividend': 'Dividend_Reinvest',
    'NRA Tax Adj': 'Tax',
    'MoneyLink Transfer': 'Transfer',
    'RSU Vest': 'RSU_Vest',
    'Reinvest Shares': 'Dividend_Reinvest',
    
    # Chinese - Fund
    '申购': 'Buy',
    '赎回': 'Sell',
    '买基金': 'Buy',
    '卖基金': 'Sell',
    '现金分红': 'Dividend',
    '红利再投资': 'Dividend_Reinvest',
    
    # Chinese - General
    '买入': 'Buy',
    '卖出': 'Sell',
    '结息': 'Interest',
    
    # Variations
    'buy': 'Buy',
    'sell': 'Sell',
}

# Transaction types to SKIP (not actual investment transactions)
SKIP_TRANSACTION_TYPES = ['Transfer', 'MoneyLink Transfer', 'Wire Funds', 'Journal']

def clean_currency_value(value: Any) -> Optional[float]:
    """
    Clean currency values: strip symbols, commas, convert to float.
    
    Examples:
        '$1,234.56' -> 1234.56
        '¥1,234.56' -> 1234.56
        '1234.56 USD' -> 1234.56
        '($1,234.56)' -> -1234.56  # Accounting format
    """
    if pd.isna(value) or value == '' or value is None:
        return None
    
    # Convert to string
    value_str = str(value).strip()
    
    # Handle accounting format for negative numbers: ($1,234.56) -> -1234.56
    is_negative = False
    if value_str.startswith('(') and value_str.endswith(')'):
        is_negative = True
        value_str = value_str[1:-1]  # Remove parentheses
    
    # Remove currency symbols and text
    value_str = re.sub(r'[\$¥€£,CNY USD EUR]', '', value_str)
    value_str = value_str.strip()
    
    # Handle empty or non-numeric
    if not value_str or value_str == '-':
        return None
    
    try:
        result = float(value_str)
        return -result if is_negative else result
    except (ValueError, TypeError):
        return None

def parse_flexible_date(date_value: Any) -> Optional[datetime]:
    """
    Parse dates in multiple formats.
    
    Handles:
    - YYYY-MM-DD
    - MM/DD/YYYY
    - (MM/DD/YYYY as of MM/DD/YYYY) -> extracts first date
    - Excel datetime objects
    """
    if pd.isna(date_value) or date_value == '':
        return None
    
    # Already datetime
    if isinstance(date_value, (datetime, pd.Timestamp)):
        return date_value
    
    date_str = str(date_value).strip()
    
    # Handle "(MM/DD/YYYY as of MM/DD/YYYY)" format
    match = re.match(r'\((\d{1,2}/\d{1,2}/\d{4})', date_str)
    if match:
        date_str = match.group(1)
    
    # Try multiple formats
    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%Y/%m/%d', '%d/%m/%Y']:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # Pandas fallback
    try:
        return pd.to_datetime(date_str)
    except:
        return None

def detect_column_mapping(df_columns: List[str]) -> Dict[str, str]:
    """
    Auto-detect which columns map to which standard fields.
    
    Returns: {standard_field: actual_column_name}
    """
    mapping = {}
    
    for standard_field, possible_names in COLUMN_MAPPINGS.items():
        for col in df_columns:
            if col in possible_names:
                mapping[standard_field] = col
                break
    
    return mapping

def normalize_transaction_type(raw_type: str) -> Optional[str]:
    """
    Normalize transaction type to standard format.
    Returns None if should be skipped.
    """
    if pd.isna(raw_type) or not raw_type:
        return None
    
    raw_type_str = str(raw_type).strip()
    
    # Check if should skip
    if raw_type_str in SKIP_TRANSACTION_TYPES:
        return None
    
    # Normalize
    return TRANSACTION_TYPE_MAPPING.get(raw_type_str, raw_type_str)

def normalize_asset_id(raw_id: Any) -> Optional[str]:
    """
    Normalize asset ID: strip spaces, ensure string format.
    """
    if pd.isna(raw_id) or raw_id == '':
        return None
    
    # Convert to string and clean
    asset_id = str(raw_id).strip()
    
    # Remove any weird characters
    asset_id = re.sub(r'[^\w\-\.]', '', asset_id)
    
    return asset_id if asset_id else None

def detect_file_source(df: pd.DataFrame) -> str:
    """
    Detect the source/type of the uploaded file.
    
    Returns: 'schwab', 'chinese_fund', 'gold', 'rsu', 'insurance', 'unknown'
    """
    columns = set(df.columns)
    
    # Check for Schwab
    if 'Action' in columns and 'Symbol' in columns:
        return 'schwab'
    
    # Check for Chinese Fund (raw or processed)
    if '基金代码' in columns or ('确认日期' in columns and '业务类型' in columns):
        return 'chinese_fund'
    
    # Check for Gold
    if '资产类别' in columns and '标的名称' in columns:
        return 'gold'
    
    # Check for RSU
    if '交易类型' in columns and any('USD' in str(col) for col in columns):
        return 'rsu'
    
    return 'unknown'

def detect_currency(file_source: str, df: pd.DataFrame = None, column_map: Dict[str, str] = None) -> str:
    """
    Detect the currency based on file source and optionally column contents.
    
    Args:
        file_source: Detected file source ('schwab', 'chinese_fund', etc.)
        df: Optional DataFrame for content inspection
        column_map: Optional column mapping for checking specific columns
    
    Returns:
        Currency code: 'USD', 'CNY', etc.
    """
    # Source-based currency mapping
    SOURCE_CURRENCY_MAP = {
        'schwab': 'USD',
        'chinese_fund': 'CNY',
        'gold': 'CNY',
        'insurance': 'CNY',
        'rsu': 'USD',
    }
    
    # If we have a direct mapping, use it
    if file_source in SOURCE_CURRENCY_MAP:
        return SOURCE_CURRENCY_MAP[file_source]
    
    # If DataFrame provided, check for USD in column names
    if df is not None:
        columns_str = ' '.join(df.columns)
        if 'USD' in columns_str or '_USD' in columns_str:
            return 'USD'
        if 'CNY' in columns_str or '人民币' in columns_str or '元' in columns_str:
            return 'CNY'
    
    # If column map provided and amount column exists, inspect first few values
    if df is not None and column_map and 'amount' in column_map:
        amount_col = column_map['amount']
        if amount_col in df.columns:
            # Check first non-null value for currency symbols
            for val in df[amount_col].dropna().head(5):
                val_str = str(val)
                if '$' in val_str:
                    return 'USD'
                if '¥' in val_str or '￥' in val_str:
                    return 'CNY'
    
    # Default to CNY (since most manual sheets are CNY)
    return 'CNY'

