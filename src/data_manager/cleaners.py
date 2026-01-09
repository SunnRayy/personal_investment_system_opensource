# src/data_manager/cleaners.py
"""
Data cleaning and column mapping for financial data ingestion.

This module handles:
- Column renaming from raw Excel/CSV headers to internal schema
- Data type cleaning (dates, monetary values, etc.)
- Transaction type standardization

Column mappings are loaded from config/column_mapping.yaml for flexibility.
Users can customize mappings by editing the YAML file or creating new profiles.
"""

import os
import logging
import pandas as pd
import numpy as np
import yaml
from typing import Dict, List, Optional, Any
from functools import lru_cache

# Set up module logger
logger = logging.getLogger(__name__)


# --- Standalone Config Loading (avoids circular imports) ---

def _get_project_root() -> str:
    """Get project root directory from this file's location."""
    # This file is in src/data_manager/
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.dirname(current_dir)
    return os.path.dirname(src_dir)


def _get_config_path(filename: str) -> str:
    """Get absolute path to a config file."""
    return os.path.join(_get_project_root(), 'config', filename)


def _load_yaml_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Load a YAML file safely with error handling.

    Args:
        file_path: Absolute path to YAML file.

    Returns:
        Dictionary from YAML or None if loading fails.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if not isinstance(data, dict):
                logger.warning(f"YAML file did not load as dictionary: {file_path}")
                return None
            return data
    except FileNotFoundError:
        logger.debug(f"Config file not found: {file_path}")
        return None
    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error in {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading {file_path}: {e}")
        return None


# --- Configuration Loading ---

# Default fallback mappings when YAML is not available
# These ensure the system doesn't crash even without config
_DEFAULT_FALLBACK_MAPPINGS = {
    'holdings': {
        'Symbol': 'Asset_ID',
        'Ticker': 'Asset_ID',
        'Name': 'Asset_Name',
        'Description': 'Asset_Name',
        'Type': 'Asset_Type_Raw',
        'Date': 'Snapshot_Date',
        'Price': 'Market_Price_Unit',
        'Quantity': 'Quantity',
        'Shares': 'Quantity',
        'Value': 'Market_Value_Raw',
        'Market Value': 'Market_Value_Raw',
    },
    'transactions': {
        'Date': 'Transaction_Date',
        'Transaction Date': 'Transaction_Date',
        'Symbol': 'Asset_ID',
        'Ticker': 'Asset_ID',
        'Name': 'Asset_Name',
        'Description': 'Asset_Name',
        'Action': 'Transaction_Type_Raw',
        'Type': 'Transaction_Type_Raw',
        'Quantity': 'Quantity',
        'Shares': 'Quantity',
        'Price': 'Price_Unit',
        'Amount': 'Amount_Gross',
        'Fees': 'Commission_Fee',
        'Commission': 'Commission_Fee',
    },
    'transaction_types': {
        'Buy': 'Buy',
        'Sell': 'Sell',
        'Dividend': 'Dividend_Cash',
        'Interest': 'Interest',
    }
}


@lru_cache(maxsize=1)
def load_column_mappings(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load column mappings from YAML configuration file.

    Falls back to built-in defaults if the config file is missing or invalid.

    Args:
        config_path: Path to column_mapping.yaml. If None, uses default location.

    Returns:
        Dictionary with mapping configuration including active profile and all profiles.
    """
    if config_path is None:
        config_path = _get_config_path('column_mapping.yaml')

    config = _load_yaml_file(config_path)

    if config is None:
        logger.warning(
            f"Column mapping config not found at {config_path}. "
            "Using built-in fallback mappings. "
            "To customize, create config/column_mapping.yaml"
        )
        return {
            'active_profile': 'fallback',
            'profiles': {'fallback': _DEFAULT_FALLBACK_MAPPINGS},
            'asset_type_overrides': {}
        }

    # Validate config structure
    if 'profiles' not in config:
        logger.warning(
            "Column mapping config missing 'profiles' section. "
            "Using built-in fallback mappings."
        )
        config['profiles'] = {'fallback': _DEFAULT_FALLBACK_MAPPINGS}

    if 'active_profile' not in config:
        logger.info("No active_profile set, defaulting to 'default'")
        config['active_profile'] = 'default'

    logger.debug(f"Loaded column mappings from {config_path}")
    return config


def get_mapping(data_type: str, profile: Optional[str] = None) -> Dict[str, str]:
    """
    Get column mapping for a specific data type with fallback handling.

    Args:
        data_type: Type of data (holdings, transactions, balance_sheet, etc.)
        profile: Profile name. If None, uses active_profile from config.

    Returns:
        Dictionary mapping raw column names to internal keys.
        Returns empty dict if no mapping found (with warning logged).
    """
    config = load_column_mappings()

    if profile is None:
        profile = config.get('active_profile', 'default')

    profiles = config.get('profiles', {})

    # Try requested profile
    if profile in profiles:
        profile_config = profiles[profile]
        mapping = profile_config.get(data_type, {})
        if mapping:
            return mapping
        logger.debug(f"No '{data_type}' mapping in profile '{profile}'")

    # Fallback chain: requested profile -> default -> fallback -> empty
    fallback_chain = ['default', 'fallback']
    for fallback_profile in fallback_chain:
        if fallback_profile != profile and fallback_profile in profiles:
            fallback_config = profiles[fallback_profile]
            mapping = fallback_config.get(data_type, {})
            if mapping:
                logger.info(
                    f"Using '{fallback_profile}' profile mapping for {data_type} "
                    f"('{profile}' profile didn't have it)"
                )
                return mapping

    # Check built-in fallback
    if data_type in _DEFAULT_FALLBACK_MAPPINGS:
        logger.warning(
            f"No '{data_type}' mapping found in any profile. "
            f"Using built-in fallback. Consider adding to column_mapping.yaml"
        )
        return _DEFAULT_FALLBACK_MAPPINGS[data_type]

    # No mapping available
    logger.warning(
        f"No column mapping found for '{data_type}'. "
        f"Data will use original column names. "
        f"Add mapping to config/column_mapping.yaml if needed."
    )
    return {}


def get_transaction_type_mapping(profile: Optional[str] = None) -> Dict[str, str]:
    """
    Get transaction type standardization mapping with fallback.

    Args:
        profile: Profile name. If None, uses active_profile from config.

    Returns:
        Dictionary mapping raw transaction types to standard types.
    """
    mapping = get_mapping('transaction_types', profile)

    if not mapping:
        logger.warning(
            "No transaction type mapping found. "
            "Transaction types will not be standardized."
        )
        return {}

    return mapping


def get_asset_type_overrides() -> Dict[str, str]:
    """
    Get asset type override mappings (ticker -> correct type).

    Returns:
        Dictionary mapping ticker symbols to corrected asset types.
        Returns empty dict if not configured (with info logged).
    """
    config = load_column_mappings()
    overrides = config.get('asset_type_overrides', {})

    if not overrides:
        logger.debug(
            "No asset_type_overrides configured. "
            "Asset types will use source data values."
        )

    return overrides


def clear_mapping_cache() -> None:
    """
    Clear the mapping configuration cache.

    Call this if you've modified column_mapping.yaml and want to reload.
    """
    load_column_mappings.cache_clear()
    logger.info("Column mapping cache cleared")


# --- Lazy-loaded Legacy Constants ---
# These provide backward compatibility for code that imports constants directly.
# They're loaded on first access to avoid import-time YAML loading.

class _LazyMapping:
    """Lazy loader for mapping constants to defer YAML loading."""

    def __init__(self, data_type: str, profile: str):
        self._data_type = data_type
        self._profile = profile
        self._mapping = None

    def _load(self):
        if self._mapping is None:
            self._mapping = get_mapping(self._data_type, self._profile)
        return self._mapping

    def __getitem__(self, key):
        return self._load()[key]

    def __contains__(self, key):
        return key in self._load()

    def __iter__(self):
        return iter(self._load())

    def __len__(self):
        return len(self._load())

    def get(self, key, default=None):
        return self._load().get(key, default)

    def keys(self):
        return self._load().keys()

    def values(self):
        return self._load().values()

    def items(self):
        return self._load().items()

    def __repr__(self):
        return repr(self._load())


# Legacy constants - lazy-loaded from YAML for backward compatibility
BALANCE_SHEET_COL_MAP = _LazyMapping('balance_sheet', 'chinese_excel')
MONTHLY_COL_MAP = _LazyMapping('monthly_cashflow', 'chinese_excel')
FUND_HOLDINGS_COL_MAP = _LazyMapping('holdings', 'chinese_excel')
FUND_TRANSACTIONS_COL_MAP = _LazyMapping('transactions', 'chinese_excel')
GOLD_HOLDINGS_COL_MAP = _LazyMapping('gold_holdings', 'chinese_excel')
GOLD_TRANSACTIONS_COL_MAP = _LazyMapping('gold_transactions', 'chinese_excel')
INSURANCE_SUMMARY_COL_MAP = _LazyMapping('insurance_summary', 'chinese_excel')
RSU_TRANSACTIONS_COL_MAP = _LazyMapping('rsu_transactions', 'chinese_excel')
SCHWAB_HOLDINGS_COL_MAP = _LazyMapping('holdings', 'schwab_csv')
SCHWAB_TRANSACTIONS_COL_MAP = _LazyMapping('transactions', 'schwab_csv')


# --- Helper Functions ---

def clean_monetary_value(value: Any) -> Optional[float]:
    """
    Cleans a monetary value string (removes ¥, ,, handles -, handles parentheses for negatives)
    and converts to float.
    """
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned_value = value.replace('¥', '').replace(',', '').strip()
        if not cleaned_value or cleaned_value == '-': # Handle empty string or just hyphen as zero
            return 0.0
        
        # Handle parentheses for negative numbers, e.g., (984.72) -> -984.72
        is_negative = False
        if cleaned_value.startswith('(') and cleaned_value.endswith(')'):
            is_negative = True
            cleaned_value = cleaned_value[1:-1] # Remove parentheses
        
        try:
            numeric_value = float(cleaned_value)
            return -numeric_value if is_negative else numeric_value
        except ValueError:
            # print(f"Warning: Could not convert monetary value '{value}' to float. Returning 0.") # Reduce noise
            return 0.0
    # print(f"Warning: Unexpected type '{type(value)}' for monetary value '{value}'. Returning 0.") # Reduce noise
    return 0.0



def standardize_date_index(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Assumes the first column is the date column.
    Parses it, sets it as index, standardizes to month-end,
    and handles duplicates by keeping the last entry per month.
    Returns None if date processing fails or results in an empty DataFrame.
    """
    if df.empty or len(df.columns) == 0:
        print("  - DataFrame is empty or has no columns. Skipping date standardization.")
        return df

    df = df.copy()
    date_col_name = df.columns[0] # Assume first column is the date column
    print(f"  - Assuming first column '{date_col_name}' is the date column.")

    # Convert to datetime, coercing errors will result in NaT
    df[date_col_name] = pd.to_datetime(df[date_col_name], errors='coerce')

    # Drop rows where date conversion failed
    original_rows = len(df)
    df = df.dropna(subset=[date_col_name])
    if len(df) < original_rows:
        print(f"  - Removed {original_rows - len(df)} rows with invalid dates.")

    if df.empty:
        print("  - DataFrame is empty after removing invalid dates.")
        return None # Return None if no valid dates

    # Standardize to month-end
    try:
        if pd.api.types.is_datetime64_any_dtype(df[date_col_name]) and df[date_col_name].dt.tz is not None:
             df[date_col_name] = df[date_col_name].dt.tz_localize(None)
        df[date_col_name] = df[date_col_name] + pd.offsets.MonthEnd(0)
    except Exception as e:
        print(f"  - Warning: Could not apply MonthEnd offset: {e}. Using normalized dates.")
        try:
             df[date_col_name] = df[date_col_name].dt.normalize()
        except Exception as e_norm:
             print(f"  - Error normalizing dates: {e_norm}. Date column might be incorrect.")
             return None


    # Handle duplicates: Sort by the original date value first, then keep last per month-end
    df = df.sort_values(by=date_col_name, ascending=True)
    num_duplicates = df.duplicated(subset=[date_col_name], keep=False).sum()
    if num_duplicates > 0:
         print(f"  - Found {num_duplicates} duplicate date entries for the same month-end.")
    df = df.drop_duplicates(subset=[date_col_name], keep='last')

    # Set the standardized date column as index
    df = df.set_index(date_col_name)
    df.index.name = 'Date' # Rename index

    print(f"  - Standardized date index to month-end, handled duplicates (keep last). Final rows: {len(df)}")
    return df


# --- Cleaning Functions for Each DataFrame ---
# Note: Column mappings are now loaded from config/column_mapping.yaml
# The legacy constants (BALANCE_SHEET_COL_MAP, etc.) are populated at module load
# from the YAML file for backward compatibility.

# --- Updated clean_dataframe_core function ---
def clean_dataframe_core(
    df_raw: Optional[pd.DataFrame],
    name: str,
    date_index: bool = False,
    rename_map: Optional[Dict] = None,
    final_schema_cols: Optional[List] = None
    ) -> Optional[pd.DataFrame]:
    """
    Core cleaning logic for DataFrames with improved type handling.

    This function is the heart of data cleaning. It handles:
    - Column renaming using provided mapping
    - Date standardization to month-end
    - Numeric type conversion with fallback
    - Final column selection

    Data types produced (compatible with calculators.py):
    - Date columns: pd.Timestamp (DatetimeIndex for index)
    - Monetary columns: float64 (Amount_*, Price_*, Value_*, *_CNY, *_USD)
    - Quantity columns: float64
    - ID/Name columns: str
    - Type columns: str

    Args:
        df_raw: Raw DataFrame to clean
        name: Name for logging purposes
        date_index: If True, set first column as DatetimeIndex
        rename_map: Column name mapping (raw -> internal)
        final_schema_cols: Optional list of columns to keep

    Returns:
        Cleaned DataFrame or None if input is invalid/empty
    """
    logger.info(f"Cleaning {name} data...")

    if df_raw is None:
        logger.warning(f"{name}: Input DataFrame is None")
        return None
    if df_raw.empty:
        logger.warning(f"{name}: Input DataFrame is empty")
        return df_raw

    df = df_raw.copy()

    # Clean column names (strip whitespace)
    try:
        df.columns = [str(col).strip() for col in df.columns]
    except Exception as e:
        logger.warning(f"{name}: Could not clean column names: {e}")

    # --- 1. Handle Date Index ---
    if date_index:
        df = standardize_date_index(df)
        if df is None or df.empty:
            logger.warning(f"{name}: DataFrame became empty after date processing")
            return None

    # --- 2. Rename Columns ---
    if rename_map:
        original_cols = df.columns.tolist()

        # Handle both dict and _LazyMapping objects
        if hasattr(rename_map, 'items'):
            rename_items = list(rename_map.items())
        else:
            rename_items = [(k, rename_map.get(k)) for k in rename_map]

        cols_to_rename = {k: v for k, v in rename_items if k in original_cols and v is not None}
        cols_to_drop = [k for k, v in rename_items if k in original_cols and v is None]

        # If target column already exists, drop source to prevent duplicates
        for src_col, target_col in list(cols_to_rename.items()):
            if target_col in df.columns and src_col in df.columns:
                cols_to_drop.append(src_col)
                del cols_to_rename[src_col]

        # Drop noise columns (Unnamed, etc.)
        noise_cols = [col for col in df.columns if 'Unnamed:' in str(col)]
        cols_to_drop.extend([nc for nc in noise_cols if nc in df.columns and nc not in cols_to_drop])

        if cols_to_drop:
            cols_to_drop_existing = [c for c in cols_to_drop if c in df.columns]
            if cols_to_drop_existing:
                df = df.drop(columns=cols_to_drop_existing)
                logger.debug(f"{name}: Dropped columns: {cols_to_drop_existing}")

        if cols_to_rename:
            df = df.rename(columns=cols_to_rename)
            logger.debug(f"{name}: Renamed {len(cols_to_rename)} columns")

        # Check for missing expected columns (warning only, not error)
        expected_cols = [v for v in (rename_map.values() if hasattr(rename_map, 'values') else []) if v is not None]
        missing_cols = [col for col in expected_cols if col not in df.columns]
        if missing_cols:
            logger.info(
                f"{name}: Some expected columns not found in source data: {missing_cols[:5]}..."
                if len(missing_cols) > 5 else f"{name}: Some expected columns not found: {missing_cols}"
            )


    # --- 3. Basic Type Cleaning ---
    # Ensures data types are compatible with calculators.py expectations
    logger.debug(f"{name}: Starting type cleaning for {len(df.columns)} columns")

    # Define patterns for numeric columns (compatible with calculators.py)
    NUMERIC_PATTERNS = {
        'prefixes': ['Amount', 'Value', 'Price', 'Fee', 'Premium', 'Insured', 'Cost', 'Total'],
        'suffixes': ['_CNY', '_USD', '_Raw'],
        'exact': ['Quantity', 'Commission_Fee', 'Price_Unit', 'Amount_Gross', 'Amount_Net',
                  'Cost_Price_Unit', 'Sum_Insured', 'Annual_Premium', 'Market_Price_Unit',
                  'Market_Value_Raw', 'Ref_USD_FX_Rate', 'Ref_Gold_Price_Gram_CNY']
    }

    def is_numeric_column(col_name: str) -> bool:
        """Check if column should be treated as numeric based on name patterns."""
        for prefix in NUMERIC_PATTERNS['prefixes']:
            if prefix in col_name:
                return True
        for suffix in NUMERIC_PATTERNS['suffixes']:
            if col_name.endswith(suffix):
                return True
        return col_name in NUMERIC_PATTERNS['exact']

    for col in df.columns:
        try:
            # Skip datetime columns - they're already correctly typed
            if 'Date' in col and pd.api.types.is_datetime64_any_dtype(df.dtypes[col]):
                continue

            if is_numeric_column(col):
                # Already numeric - ensure float type for consistency
                if pd.api.types.is_numeric_dtype(df.dtypes[col]):
                    if not pd.api.types.is_float_dtype(df.dtypes[col]):
                        df[col] = df[col].astype(float)

                    # Special case: Schwab Amount_Gross should be absolute
                    if name == "Schwab Transactions" and col == "Amount_Gross":
                        df[col] = df[col].abs()

                # Object type - clean and convert to numeric
                elif pd.api.types.is_object_dtype(df.dtypes[col]):
                    cleaned_col = df[col].apply(clean_monetary_value)
                    numeric_col = pd.to_numeric(cleaned_col, errors='coerce')

                    # Only convert if majority of values are valid numbers
                    valid_ratio = numeric_col.notna().sum() / max(len(numeric_col), 1)
                    if valid_ratio > 0.5:
                        df[col] = numeric_col.fillna(0.0)

                        # Schwab Amount_Gross absolute value
                        if name == "Schwab Transactions" and col == "Amount_Gross":
                            df[col] = df[col].abs()
                    else:
                        # Mostly non-numeric - treat as string
                        logger.debug(
                            f"{name}: Column '{col}' expected numeric but only "
                            f"{valid_ratio:.0%} valid. Keeping as string."
                        )
                        df[col] = df[col].astype(str).str.strip()

            # Non-numeric object columns - clean as strings
            elif pd.api.types.is_object_dtype(df.dtypes[col]):
                df[col] = df[col].astype(str).str.strip()

        except Exception as e:
            logger.warning(
                f"{name}: Error processing column '{col}': {e}. "
                "Column will retain original type."
            )
            continue

    # --- 4. Final Column Selection (Optional) ---
    if final_schema_cols:
        missing_final_cols = [c for c in final_schema_cols if c not in df.columns]
        if missing_final_cols:
            logger.info(f"{name}: Expected columns not in data: {missing_final_cols}")
        cols_to_keep = [c for c in final_schema_cols if c in df.columns]
        df = df[cols_to_keep]
        logger.debug(f"{name}: Selected {len(cols_to_keep)} columns from schema")

    logger.info(f"{name}: Cleaning complete. Shape: {df.shape}")
    return df


# --- Updated Cleaning Functions using core logic ---

def clean_balance_sheet(df_raw: pd.DataFrame, config: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Cleans the raw Balance Sheet DataFrame including renaming."""
    # Potentially define final_cols based on schema if strict selection is needed
    # final_cols = [...]
    return clean_dataframe_core(df_raw, "Balance Sheet", date_index=True, rename_map=BALANCE_SHEET_COL_MAP)

def clean_monthly_income_expense(df_raw: pd.DataFrame, config: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Cleans the raw Monthly Income/Expense DataFrame including renaming."""
    df = clean_dataframe_core(df_raw, "Monthly Income/Expense", date_index=True, rename_map=MONTHLY_COL_MAP)
    # Specific type handling after general cleaning if needed
    if df is not None and 'Ref_USD_FX_Rate' in df.columns: # Example specific check
        df['Ref_USD_FX_Rate'] = pd.to_numeric(df['Ref_USD_FX_Rate'], errors='coerce').fillna(0.0)
    return df

def clean_fund_holdings(df_raw: pd.DataFrame, config: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Cleans the raw Fund Holdings DataFrame including renaming."""
    df = clean_dataframe_core(df_raw, "Fund Holdings", date_index=False, rename_map=FUND_HOLDINGS_COL_MAP)
    if df is not None:
         if 'Snapshot_Date' in df.columns:
             # Only convert if not already datetime (avoid duplicate keys error)
             if not pd.api.types.is_datetime64_any_dtype(df['Snapshot_Date']):
                 df['Snapshot_Date'] = pd.to_datetime(df['Snapshot_Date'], errors='coerce')
         if 'Asset_ID' in df.columns:
             # Remove .0 suffix from float IDs (e.g. 311.0 -> 311)
             def clean_id(val):
                 try:
                     if pd.isna(val): return val
                     return str(int(float(val)))
                 except (ValueError, TypeError):
                     return str(val)
             df['Asset_ID'] = df['Asset_ID'].apply(clean_id)
    return df

def clean_fund_transactions(df_raw: pd.DataFrame, config: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Cleans the raw Fund Transactions DataFrame including renaming."""
    df = clean_dataframe_core(df_raw, "Fund Transactions", date_index=False, rename_map=FUND_TRANSACTIONS_COL_MAP)
    if df is not None:
        if 'Transaction_Date' in df.columns:
            df['Transaction_Date'] = pd.to_datetime(df['Transaction_Date'], errors='coerce')
            df = df.sort_values(by='Transaction_Date').reset_index(drop=True)
        if 'Asset_ID' in df.columns:
             # Remove .0 suffix from float IDs (e.g. 311.0 -> 311)
             def clean_id(val):
                 try:
                     if pd.isna(val): return val
                     return str(int(float(val)))
                 except (ValueError, TypeError):
                     return str(val)
             df['Asset_ID'] = df['Asset_ID'].apply(clean_id)
        # Transaction_Type_Raw is kept for standardization later
    return df

def clean_gold_holdings(df_raw: pd.DataFrame, config: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Cleans the raw Gold Holdings DataFrame including renaming."""
    df = clean_dataframe_core(df_raw, "Gold Holdings", date_index=False, rename_map=GOLD_HOLDINGS_COL_MAP)
    # Specific type handling if needed
    if df is not None and 'Unit' in df.columns:
        df['Unit'] = df['Unit'].astype(str) # Ensure unit is string
    return df

def clean_gold_transactions(df_raw: pd.DataFrame, config: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Cleans the raw Gold Transactions DataFrame including renaming."""
    df = clean_dataframe_core(df_raw, "Gold Transactions", date_index=False, rename_map=GOLD_TRANSACTIONS_COL_MAP)
    if df is not None:
         if 'Transaction_Date' in df.columns:
             df['Transaction_Date'] = pd.to_datetime(df['Transaction_Date'], errors='coerce')
             df = df.sort_values(by='Transaction_Date').reset_index(drop=True)
         # Transaction_Type_Raw is kept for standardization later
    return df

def clean_insurance_summary(df_raw: pd.DataFrame, config: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Cleans the raw Insurance Summary DataFrame including renaming."""
    df = clean_dataframe_core(df_raw, "Insurance Summary", date_index=False, rename_map=INSURANCE_SUMMARY_COL_MAP)
    if df is not None:
         if 'Policy_Start_Date' in df.columns:
             df['Policy_Start_Date'] = pd.to_datetime(df['Policy_Start_Date'], errors='coerce')
         # Raw terms kept as strings for now
    return df

def clean_rsu_transactions(df_raw: pd.DataFrame, config: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Cleans the raw RSU Transactions DataFrame including renaming."""
    # Ensure the RSU_TRANSACTIONS_COL_MAP uses the exact headers from the user's new Excel
    df = clean_dataframe_core(df_raw, "RSU Transactions", date_index=False, rename_map=RSU_TRANSACTIONS_COL_MAP)
    if df is not None:
        if 'Transaction_Date' in df.columns:
            df['Transaction_Date'] = pd.to_datetime(df['Transaction_Date'], errors='coerce')
            df = df.sort_values(by='Transaction_Date').reset_index(drop=True)
        
        # Generate Asset_ID from Asset_Name if not present (RSU Excel doesn't have Asset_ID column)
        if 'Asset_ID' not in df.columns and 'Asset_Name' in df.columns:
            # Map known RSU names to Asset_IDs
            def generate_rsu_asset_id(asset_name):
                if pd.isna(asset_name):
                    return 'RSU_Unknown'
                asset_name_lower = str(asset_name).lower()
                if 'employer' in asset_name_lower or 'employer_stock' in asset_name_lower:
                    return 'Employer_Stock_A'
                # Add more mappings as needed
                return f"RSU_{asset_name.replace(' ', '_')}"
            
            df['Asset_ID'] = df['Asset_Name'].apply(generate_rsu_asset_id)
        
        # Set Account to default if not present (RSU Excel doesn't have Account column)
        if 'Account' not in df.columns:
            df['Account'] = 'Schwab'  # Default RSU account
        
        if 'Asset_ID' in df.columns:
             df['Asset_ID'] = df['Asset_ID'].astype(str)
        
        # Assume numeric columns were handled by core cleaner based on name patterns
        # Explicitly mark currency
        if 'Price_Unit' in df.columns:
            df['Currency'] = 'USD'  # Assuming Price is USD
        if 'Amount_Gross' in df.columns:
            df['Currency'] = 'USD'  # Assuming Gross is USD
        if 'Commission_Fee' in df.columns:
            df['Currency'] = 'USD'  # Assuming Fee is USD
    return df

# --- **新增**: Schwab 清洗函数 ---
def clean_schwab_holdings(df_raw: pd.DataFrame, config: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Cleans the raw Schwab Holdings DataFrame."""
    df = clean_dataframe_core(df_raw, "Schwab Holdings", date_index=False, rename_map=SCHWAB_HOLDINGS_COL_MAP)
    if df is not None:
         if 'Snapshot_Date' in df.columns:
             df['Snapshot_Date'] = pd.to_datetime(df['Snapshot_Date'], errors='coerce')
         if 'Asset_ID' in df.columns: # Asset_ID is Ticker
             df['Asset_ID'] = df['Asset_ID'].astype(str)
             
             # Fix incorrect Asset_Type_Raw values based on known ticker symbols
             # Load corrections from YAML configuration
             asset_type_corrections = get_asset_type_overrides()

             if asset_type_corrections and 'Asset_Type_Raw' in df.columns:
                 # Apply corrections where ticker symbol is known
                 for ticker, correct_type in asset_type_corrections.items():
                     mask = df['Asset_ID'] == ticker
                     if mask.any():
                         original_type = df.loc[mask, 'Asset_Type_Raw'].iloc[0] if not df.loc[mask, 'Asset_Type_Raw'].empty else 'Unknown'
                         df.loc[mask, 'Asset_Type_Raw'] = correct_type
                         print(f"      - Corrected {ticker} type: '{original_type}' -> '{correct_type}'")
                         
         # Currency is inferred from column names like Market_Price_Unit_USD -> Market_Price_Unit
         # The core cleaner handles monetary conversion.
         # If an explicit 'Currency' column existed and was mapped, it would be used.
    return df

def clean_schwab_transactions(df_raw: pd.DataFrame, config: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Cleans the raw Schwab Transactions DataFrame."""
    df = clean_dataframe_core(df_raw, "Schwab Transactions", date_index=False, rename_map=SCHWAB_TRANSACTIONS_COL_MAP)
    if df is not None:
        if 'Transaction_Date' in df.columns:
            df['Transaction_Date'] = pd.to_datetime(df['Transaction_Date'], errors='coerce')
            df = df.sort_values(by='Transaction_Date').reset_index(drop=True)
        if 'Asset_ID' in df.columns: # Asset_ID is Ticker
            df['Asset_ID'] = df['Asset_ID'].astype(str)
        # Amount_Gross needs to be absolute as per our schema agreement
        # This is now handled in clean_dataframe_core for this specific case
        if 'Currency' not in df.columns: # If no explicit currency column from Excel
             df['Currency'] = 'USD' # Default for Schwab transactions
    return df
# --- **新增结束** ---

# --- **新增**: Schwab CSV 清洗函数 ---
def clean_schwab_holdings_csv(df: pd.DataFrame, settings: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """
    Cleans Schwab holdings CSV data with proper column mapping and data type conversion.
    
    Args:
        df: Raw DataFrame from Schwab holdings CSV
        settings: Configuration settings (unused but kept for consistency)
    
    Returns:
        Cleaned DataFrame with standardized columns, or None if error occurs
    """
    if df is None or df.empty:
        print("  - Schwab holdings CSV DataFrame is empty.")
        return None
    
    print(f"  - Processing Schwab holdings CSV with {len(df)} rows and columns: {list(df.columns)}")
    
    # Create a copy to avoid modifying original
    cleaned_df = df.copy()
    
    # Column mapping: CSV column names -> standardized names
    # Supports both real Schwab exports and demo data formats
    column_mapping = {
        'Symbol': 'Asset_ID',
        'Description': 'Asset_Name', 
        'Qty (Quantity)': 'Quantity',  # Real Schwab format
        'Quantity': 'Quantity',  # Demo/simple format
        'Price': 'Market_Price_Unit',
        'Mkt Val (Market Value)': 'Market_Value_Raw',  # Real Schwab format
        'Market Value': 'Market_Value_Raw',  # Demo/simple format
        'Security Type': 'Asset_Type_Raw',
        'Cost Basis': 'Cost_Total'
    }
    
    # Rename columns
    for csv_col, std_col in column_mapping.items():
        if csv_col in cleaned_df.columns and std_col not in cleaned_df.columns:
            cleaned_df = cleaned_df.rename(columns={csv_col: std_col})
        elif csv_col in cleaned_df.columns and std_col in cleaned_df.columns and csv_col != std_col:
            # Column already exists with standard name, skip
            pass
        elif csv_col not in cleaned_df.columns and std_col not in cleaned_df.columns:
            print(f"    - Warning: Expected column '{csv_col}' not found in CSV")
    
    # Clean and convert Quantity column
    if 'Quantity' in cleaned_df.columns:
        cleaned_df['Quantity'] = pd.to_numeric(
            cleaned_df['Quantity'].astype(str).str.replace(',', ''), 
            errors='coerce'
        )
    
    # Clean and convert Market_Value_Raw column (remove commas, convert to numeric)
    if 'Market_Value_Raw' in cleaned_df.columns:
        cleaned_df['Market_Value_Raw'] = pd.to_numeric(
            cleaned_df['Market_Value_Raw'].astype(str).str.replace(',', '').str.replace('$', ''), 
            errors='coerce'
        )
    
    # Clean and convert Market_Price_Unit column
    if 'Market_Price_Unit' in cleaned_df.columns:
        cleaned_df['Market_Price_Unit'] = pd.to_numeric(
            cleaned_df['Market_Price_Unit'].astype(str).str.replace(',', '').str.replace('$', ''), 
            errors='coerce'
        )
    
    # Clean and convert Market_Value_Raw column
    if 'Market_Value_Raw' in cleaned_df.columns:
        cleaned_df['Market_Value_Raw'] = pd.to_numeric(
            cleaned_df['Market_Value_Raw'].astype(str).str.replace(',', '').str.replace('$', ''), 
            errors='coerce'
        )
    
    # Clean and convert Quantity column
    if 'Quantity' in cleaned_df.columns:
        cleaned_df['Quantity'] = pd.to_numeric(
            cleaned_df['Quantity'].astype(str).str.replace(',', ''), 
            errors='coerce'
        )
    
    # Set standard fields
    cleaned_df['Currency'] = 'USD'
    cleaned_df['Unit'] = 'Shares'  # Default unit for stocks/ETFs
    
    # Clean Asset_ID (remove any whitespace)
    if 'Asset_ID' in cleaned_df.columns:
        cleaned_df['Asset_ID'] = cleaned_df['Asset_ID'].astype(str).str.strip()
    
    print(f"  - Schwab holdings CSV cleaned successfully. Final shape: {cleaned_df.shape}")
    return cleaned_df

def clean_schwab_transactions_csv(df: pd.DataFrame, settings: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """
    Cleans Schwab transactions CSV data with proper column mapping and data type conversion.
    
    Args:
        df: Raw DataFrame from Schwab transactions CSV  
        settings: Configuration settings (unused but kept for consistency)
    
    Returns:
        Cleaned DataFrame with standardized columns, or None if error occurs
    """
    if df is None or df.empty:
        print("  - Schwab transactions CSV DataFrame is empty.")
        return None
    
    print(f"  - Processing Schwab transactions CSV with {len(df)} rows and columns: {list(df.columns)}")
    
    # Create a copy to avoid modifying original
    cleaned_df = df.copy()
    
    # Column mapping: CSV column names -> standardized names
    column_mapping = {
        'Date': 'Transaction_Date',
        'Action': 'Transaction_Type_Raw',
        'Symbol': 'Asset_ID', 
        'Description': 'Asset_Name',
        'Price': 'Price_Unit',  # CRITICAL FIX: Map Price to Price_Unit for cost basis calculation
        'Quantity': 'Quantity',
        'Fees & Comm': 'Commission_Fee',
        'Amount': 'Amount_Net'
    }
    
    # Rename columns
    for csv_col, std_col in column_mapping.items():
        if csv_col in cleaned_df.columns:
            cleaned_df = cleaned_df.rename(columns={csv_col: std_col})
        else:
            print(f"    - Warning: Expected column '{csv_col}' not found in CSV")
    
    # Convert Transaction_Date to datetime
    if 'Transaction_Date' in cleaned_df.columns:
        cleaned_df['Transaction_Date'] = pd.to_datetime(cleaned_df['Transaction_Date'], errors='coerce')
        # Sort by date
        cleaned_df = cleaned_df.sort_values('Transaction_Date').reset_index(drop=True)
    
    # Clean numeric columns
    numeric_columns = ['Quantity', 'Price_Unit', 'Commission_Fee', 'Amount_Net']
    for col in numeric_columns:
        if col in cleaned_df.columns:
            # Remove commas, dollar signs, and convert to numeric
            cleaned_df[col] = pd.to_numeric(
                cleaned_df[col].astype(str).str.replace(',', '').str.replace('$', '').str.replace('(', '-').str.replace(')', ''), 
                errors='coerce'
            )
    
    # Set standard fields
    cleaned_df['Currency'] = 'USD'
    
    # Clean Asset_ID (remove any whitespace)
    if 'Asset_ID' in cleaned_df.columns:
        cleaned_df['Asset_ID'] = cleaned_df['Asset_ID'].astype(str).str.strip()
    
    # --- Filter out non-security transactions (Interest, Tax, etc. with no Symbol) ---
    # Records like "SCHWAB1 INT 03/28-04/28" (interest/tax adjustments) have empty Symbol/Asset_ID
    # These are summary records and should be excluded from holdings/transaction analysis
    if 'Asset_ID' in cleaned_df.columns:
        # Filter out rows where Asset_ID is empty, 'nan', or 'None'
        before_count = len(cleaned_df)
        cleaned_df = cleaned_df[
            (cleaned_df['Asset_ID'].notna()) & 
            (cleaned_df['Asset_ID'] != '') & 
            (cleaned_df['Asset_ID'] != 'nan') &
            (cleaned_df['Asset_ID'] != 'None')
        ].copy()
        after_count = len(cleaned_df)
        if before_count > after_count:
            print(f"    - Filtered out {before_count - after_count} non-security transactions (interest, tax adjustments, etc.)")
    # --- End filtering ---

    # --- Map Schwab Action field to standardized internal transaction types ---
    # Load transaction type mapping from YAML configuration (schwab_csv profile)
    if 'Transaction_Type_Raw' in cleaned_df.columns:
        action_map = get_transaction_type_mapping('schwab_csv')

        def map_action(val: Any) -> str:
            if pd.isna(val):
                return 'Unknown'
            raw_val = str(val).strip()
            # Try exact match first, then case-insensitive
            if raw_val in action_map:
                return action_map[raw_val]
            # Try lowercase match
            lower_map = {k.lower(): v for k, v in action_map.items()}
            return lower_map.get(raw_val.lower(), raw_val)  # Keep original if not mapped

        cleaned_df['Transaction_Type'] = cleaned_df['Transaction_Type_Raw'].apply(map_action)
    else:
        cleaned_df['Transaction_Type'] = 'Unknown'

    # If Amount_Net not yet present (some older logic relies on later integration step), ensure column exists
    if 'Amount_Net' not in cleaned_df.columns:
        cleaned_df['Amount_Net'] = pd.NA
    # Populate Amount_Gross for downstream sign logic if absent (Schwab CSV only provides net Amount)
    if 'Amount_Net' in cleaned_df.columns and 'Amount_Gross' not in cleaned_df.columns:
        try:
            cleaned_df['Amount_Gross'] = cleaned_df['Amount_Net'].abs()
        except Exception:
            cleaned_df['Amount_Gross'] = pd.NA
    if 'Commission_Fee' not in cleaned_df.columns:
        cleaned_df['Commission_Fee'] = 0.0
    
    print(f"  - Schwab transactions CSV cleaned successfully. Final shape: {cleaned_df.shape}")
    return cleaned_df
# --- **CSV清洗函数结束** ---

# --- Transformer Function (Insurance Premiums) ---

def transform_insurance_premiums(df_raw: pd.DataFrame, config: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Transforms the wide-format Insurance Premiums DataFrame to long format."""
    print("\nTransforming Insurance Premiums data (Wide to Long)...")
    if df_raw is None:
        return None
    if df_raw.empty:
        return df_raw

    df = df_raw.copy()
    df.columns = [str(col).strip() for col in df.columns]

    # Assume first column is date
    if len(df.columns) < 2:
        print("  - Error: Insurance Premiums sheet needs at least a date column and one product column.")
        return None
    date_col = df.columns[0] # Get the name of the date column

    # Ensure date column is datetime
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col])
    if df.empty:
        print("  - No valid dates found in Insurance Premiums data.")
        return None

    # Melt the DataFrame
    try:
        df_long = df.melt(
            id_vars=[date_col],
            var_name='Asset_Name_Raw', # Raw product name from column header
            value_name='Source_Amount' # Raw amount read from cell
        )
    except Exception as e:
        print(f"  - Error during melting: {e}")
        return None

    # Rename date column to standard Transaction_Date
    df_long = df_long.rename(columns={date_col: 'Transaction_Date'})

    # Clean the amount
    df_long['Amount_Gross'] = df_long['Source_Amount'].apply(clean_monetary_value)

    # Filter out zero amount records
    original_rows = len(df_long)
    df_long = df_long[df_long['Amount_Gross'] > 0].copy() # Keep only actual payments > 0
    if len(df_long) < original_rows:
         print(f"  - Removed {original_rows - len(df_long)} zero or invalid premium records.")

    if df_long.empty:
         print("  - No valid premium payments found after filtering.")
         return None

    # Add standard transaction columns needed later
    df_long['Transaction_Type'] = 'Premium_Payment' # Standard type
    df_long['Asset_ID'] = 'Ins_' + df_long['Asset_Name_Raw'] # Generate Asset ID
    df_long['Quantity'] = np.nan # No quantity for premiums
    df_long['Unit'] = 'CNY' # Assume premium paid in CNY, adjust if needed
    df_long['Price_Unit'] = np.nan # No unit price
    df_long['Commission_Fee'] = 0.0 # Assume no fee
    df_long['Amount_Net'] = -df_long['Amount_Gross'] # Cash outflow
    df_long['Currency'] = 'CNY' # Assume CNY
    df_long['Account'] = None
    df_long['Memo'] = '保费支付' # Add a default memo

    # Select and reorder columns to match transaction schema closely
    # Note: 'Asset_Name_Raw' kept for potential downstream use, could drop later
    final_cols = [
        'Transaction_Date', 'Asset_ID', 'Asset_Name_Raw', 'Transaction_Type',
        'Quantity', 'Unit', 'Price_Unit', 'Amount_Gross', 'Commission_Fee',
        'Amount_Net', 'Currency', 'Account', 'Memo'
    ]
    # Ensure all columns exist, add missing ones as NaN or default
    for col in final_cols:
        if col not in df_long.columns:
             df_long[col] = np.nan if col not in ['Commission_Fee'] else 0.0

    df_long = df_long[final_cols]


    print(f"  - Insurance Premiums transformed to long format. {len(df_long)} valid premium payments found.")
    if 'Transaction_Date' in df_long.columns:
        df_long = df_long.sort_values(by='Transaction_Date').reset_index(drop=True)
    return df_long

def process_raw_holdings(raw_df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Processes raw holdings data from raw_holdings_paste sheet.
    
    Input: Raw holdings DataFrame with Chinese column names
    Output: Cleaned, aggregated DataFrame matching 基金持仓汇总 schema
    
    Performs:
    - Column renaming (基金代码 -> Asset_ID, etc.)
    - Data type cleaning with robust error handling
    - Aggregation by grouping same funds and summing quantities/values
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    if raw_df is None or raw_df.empty:
        logger.warning("Raw holdings DataFrame is None or empty")
        return None
    
    try:
        # Create a copy to avoid modifying original data
        df = raw_df.copy()
        
        # Remove any completely empty rows
        df = df.dropna(how='all')
        
        if df.empty:
            logger.warning("All rows in raw holdings data are empty after cleaning")
            return None
        
        # Column mapping
        column_mapping = {
            '基金代码': 'Asset_ID',
            '基金简称': 'Asset_Name', 
            '基金类型': 'Asset_Type_Raw',
            '净值日期': 'Snapshot_Date',
            '单位净值': 'Market_Price_Unit',
            '持有份额': 'Quantity',
            '参考市值': 'Market_Value_Raw'
        }
        
        # Rename columns with robust error handling
        available_cols = set(df.columns)
        missing_cols = set(column_mapping.keys()) - available_cols
        if missing_cols:
            logger.warning(f"Missing expected columns in raw holdings: {missing_cols}")
        
        # Only rename columns that exist
        rename_map = {k: v for k, v in column_mapping.items() if k in available_cols}
        df = df.rename(columns=rename_map)
        
        # Clean Asset_ID (remove .0 suffix)
        if 'Asset_ID' in df.columns:
            def clean_id(val):
                try:
                    if pd.isna(val): return val
                    return str(int(float(val)))
                except (ValueError, TypeError):
                    return str(val)
            df['Asset_ID'] = df['Asset_ID'].apply(clean_id)
        
        # Clean and convert data types
        logger.info("Cleaning data types for holdings...")
        
        # Clean date column
        if 'Snapshot_Date' in df.columns:
            try:
                df['Snapshot_Date'] = pd.to_datetime(df['Snapshot_Date'], errors='coerce')
                invalid_dates = df['Snapshot_Date'].isna().sum()
                if invalid_dates > 0:
                    logger.warning(f"Found {invalid_dates} invalid dates in holdings data")
            except Exception as e:
                logger.error(f"Error converting Snapshot_Date: {e}")
        
        # Clean numeric columns with robust error handling
        numeric_cols = ['Market_Price_Unit', 'Quantity', 'Market_Value_Raw']
        for col in numeric_cols:
            if col in df.columns:
                try:
                    # Handle various formats and clean monetary values
                    df[col] = df[col].apply(lambda x: clean_monetary_value(x) if pd.notna(x) else 0.0)
                    invalid_count = (df[col] == 0.0).sum()
                    if invalid_count > 0:
                        # Use INFO for Commission_Fee since zero fees are normal
                        if col == 'Commission_Fee':
                            logger.info(f"Found {invalid_count} zero values in {col} (zero commission fees are expected)")
                        else:
                            logger.warning(f"Found {invalid_count} zero/invalid values in {col}")
                except Exception as e:
                    logger.error(f"Error cleaning numeric column {col}: {e}")
                    df[col] = 0.0
        
        # Remove rows with invalid or zero quantities and market values
        initial_rows = len(df)
        if 'Quantity' in df.columns and 'Market_Value_Raw' in df.columns:
            df = df[(df['Quantity'] > 0) & (df['Market_Value_Raw'] > 0)]
            removed_rows = initial_rows - len(df)
            if removed_rows > 0:
                logger.info(f"Removed {removed_rows} rows with zero/invalid quantities or market values")
        
        if df.empty:
            logger.warning("No valid holdings data remaining after cleaning")
            return None
        
        # Aggregate data by grouping
        group_cols = ['Asset_ID', 'Asset_Name', 'Asset_Type_Raw', 'Snapshot_Date', 'Market_Price_Unit']
        sum_cols = ['Quantity', 'Market_Value_Raw']
        
        # Only group by columns that exist
        available_group_cols = [col for col in group_cols if col in df.columns]
        available_sum_cols = [col for col in sum_cols if col in df.columns]
        
        if not available_group_cols or not available_sum_cols:
            logger.error("Required columns for grouping/summing not available")
            return None
        
        try:
            # Perform aggregation
            aggregated_df = df.groupby(available_group_cols)[available_sum_cols].sum().reset_index()
            logger.info(f"Successfully aggregated holdings: {len(df)} raw rows -> {len(aggregated_df)} aggregated rows")
            
            # Ensure final schema matches expected format
            expected_cols = ['Asset_ID', 'Asset_Name', 'Asset_Type_Raw', 'Snapshot_Date', 'Market_Price_Unit', 'Quantity', 'Market_Value_Raw']
            for col in expected_cols:
                if col not in aggregated_df.columns:
                    if col in ['Quantity', 'Market_Value_Raw']:
                        aggregated_df[col] = 0.0
                    else:
                        aggregated_df[col] = None
            
            # Reorder columns to match expected schema
            aggregated_df = aggregated_df[expected_cols]
            
            return aggregated_df
            
        except Exception as e:
            logger.error(f"Error during aggregation: {e}")
            return None
            
    except Exception as e:
        logger.error(f"Critical error processing raw holdings: {e}")
        return None

def process_raw_transactions(raw_df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Processes raw transactions data from raw_transactions_paste sheet.
    
    Input: Raw transactions DataFrame with Chinese column names  
    Output: Cleaned DataFrame matching 基金交易记录 schema
    
    Performs:
    - Filtering for successful transactions (确认状态 == "成功")
    - Column renaming (确认日期 -> Transaction_Date, etc.)
    - Data type cleaning with robust error handling
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    if raw_df is None or raw_df.empty:
        logger.warning("Raw transactions DataFrame is None or empty")
        return None
    
    try:
        # Create a copy to avoid modifying original data
        df = raw_df.copy()
        
        # Remove any completely empty rows
        df = df.dropna(how='all')
        
        if df.empty:
            logger.warning("All rows in raw transactions data are empty after cleaning")
            return None
        
        # Filter for successful transactions first
        if '确认状态' in df.columns:
            initial_rows = len(df)
            df = df[df['确认状态'] == '成功']
            filtered_rows = initial_rows - len(df)
            logger.info(f"Filtered transactions: {initial_rows} total -> {len(df)} successful (removed {filtered_rows} non-successful)")
        else:
            logger.warning("确认状态 column not found, processing all transactions")
        
        if df.empty:
            logger.warning("No successful transactions found after filtering")
            return None
        
        # Column mapping
        column_mapping = {
            '确认日期': 'Transaction_Date',
            '基金代码': 'Asset_ID',
            '基金简称': 'Asset_Name',
            '业务类型': 'Transaction_Type_Raw',
            '确认份额': 'Quantity',
            '确认金额': 'Amount_Gross',
            '手续费': 'Commission_Fee',
            '确认净值': 'Price_Unit'
        }
        
        # Rename columns with robust error handling
        available_cols = set(df.columns)
        missing_cols = set(column_mapping.keys()) - available_cols
        if missing_cols:
            logger.warning(f"Missing expected columns in raw transactions: {missing_cols}")
        
        # Only rename columns that exist
        rename_map = {k: v for k, v in column_mapping.items() if k in available_cols}
        df = df.rename(columns=rename_map)
        
        # Clean Asset_ID (remove .0 suffix)
        if 'Asset_ID' in df.columns:
            def clean_id(val):
                try:
                    if pd.isna(val): return val
                    return str(int(float(val)))
                except (ValueError, TypeError):
                    return str(val)
            df['Asset_ID'] = df['Asset_ID'].apply(clean_id)
        
        # Clean and convert data types
        logger.info("Cleaning data types for transactions...")
        
        # Clean date column
        if 'Transaction_Date' in df.columns:
            try:
                df['Transaction_Date'] = pd.to_datetime(df['Transaction_Date'], errors='coerce')
                invalid_dates = df['Transaction_Date'].isna().sum()
                if invalid_dates > 0:
                    logger.warning(f"Found {invalid_dates} invalid dates in transactions data")
                    # Remove rows with invalid dates
                    df = df.dropna(subset=['Transaction_Date'])
            except Exception as e:
                logger.error(f"Error converting Transaction_Date: {e}")
        
        # Clean numeric columns with robust error handling
        numeric_cols = ['Quantity', 'Amount_Gross', 'Commission_Fee', 'Price_Unit']
        for col in numeric_cols:
            if col in df.columns:
                try:
                    # Handle various formats and clean monetary values
                    df[col] = df[col].apply(lambda x: clean_monetary_value(x) if pd.notna(x) else 0.0)
                    invalid_count = (df[col] == 0.0).sum()
                    if invalid_count > 0:
                        # Use INFO for Commission_Fee since zero fees are normal
                        if col == 'Commission_Fee':
                            logger.info(f"Found {invalid_count} zero values in {col} (zero commission fees are expected)")
                        else:
                            logger.warning(f"Found {invalid_count} zero/invalid values in {col}")
                except Exception as e:
                    logger.error(f"Error cleaning numeric column {col}: {e}")
                    df[col] = 0.0
        
        # Standardize transaction types using YAML configuration
        # Raw paste data may use different terms than historical data
        if 'Transaction_Type_Raw' in df.columns:
            # Get transaction type mapping from chinese_excel profile
            type_mapping = get_transaction_type_mapping('chinese_excel')

            # Also add Chinese-specific standardization (paste format -> standard format)
            paste_to_standard = {
                '买基金': '申购',
                '卖基金': '赎回',
            }

            original_types = df['Transaction_Type_Raw'].value_counts()
            logger.info(f"Original transaction types: {original_types.to_dict()}")

            def standardize_type(x):
                if pd.isna(x):
                    return x
                # First apply paste-to-standard mapping
                result = paste_to_standard.get(x, x)
                # Then apply YAML-based mapping if available
                if type_mapping:
                    result = type_mapping.get(result, result)
                return result

            df['Transaction_Type_Raw'] = df['Transaction_Type_Raw'].map(standardize_type)

            standardized_types = df['Transaction_Type_Raw'].value_counts()
            logger.info(f"Standardized transaction types: {standardized_types.to_dict()}")
        
        if df.empty:
            logger.warning("No valid transactions data remaining after cleaning")
            return None
        
        # Ensure final schema matches expected format
        expected_cols = ['Transaction_Date', 'Asset_ID', 'Asset_Name', 'Transaction_Type_Raw', 'Quantity', 'Amount_Gross', 'Commission_Fee', 'Price_Unit']
        for col in expected_cols:
            if col not in df.columns:
                if col in ['Quantity', 'Amount_Gross', 'Commission_Fee', 'Price_Unit']:
                    df[col] = 0.0
                else:
                    df[col] = None
        
        # Reorder columns to match expected schema
        df = df[expected_cols]
        
        # Sort by transaction date
        if 'Transaction_Date' in df.columns:
            df = df.sort_values(by='Transaction_Date').reset_index(drop=True)
        
        logger.info(f"Successfully processed {len(df)} transactions")
        return df
        
    except Exception as e:
        logger.error(f"Critical error processing raw transactions: {e}")
        return None