import pandas as pd
import yaml
import os
import glob
from typing import Dict, Optional, Any

def load_settings(config_path: str = 'config/settings.yaml') -> Dict[str, Any]:
    """Loads configuration settings from a YAML file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            settings = yaml.safe_load(f)
        print(f"Configuration loaded successfully from {config_path}")
        return settings
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {config_path}")
        raise
    except Exception as e:
        print(f"Error loading configuration from {config_path}: {e}")
        raise

def read_excel_file(
    file_config: Dict[str, Any],
    sheet_name: str,
    header_row: int = 0, # Default header row is 0 (first row)
    use_cols: Optional[list] = None,
    converters: Optional[Dict] = None
) -> Optional[pd.DataFrame]:
    """
    Reads a specific sheet from an Excel file based on configuration.

    Args:
        file_config: Dictionary containing 'path' and 'sheets' mapping for the file.
        sheet_name: The specific sheet name key (e.g., 'balance_sheet', 'transactions')
                    as defined in the settings.yaml file under the file's 'sheets'.
        header_row: The 0-indexed row number to use as the header.
        use_cols: Optional list of columns to read.
        converters: Optional dictionary specifying converters for columns.

    Returns:
        A pandas DataFrame containing the data from the specified sheet,
        or None if the file/sheet doesn't exist or an error occurs.
    """
    file_path = file_config.get('path')
    actual_sheet_name = file_config.get('sheets', {}).get(sheet_name)

    if not file_path or not actual_sheet_name:
        print(f"Error: Path or sheet key '{sheet_name}' not found in file configuration.")
        return None

    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return None

    print(f"Reading sheet '{actual_sheet_name}' from {os.path.basename(file_path)} (Header row: {header_row})...")
    try:
        # Check if sheet exists before reading
        xls = pd.ExcelFile(file_path, engine='openpyxl')
        if actual_sheet_name not in xls.sheet_names:
             print(f"Error: Sheet '{actual_sheet_name}' not found in {os.path.basename(file_path)}")
             return None

        df = pd.read_excel(
            file_path,
            sheet_name=actual_sheet_name,
            header=header_row,
            engine='openpyxl', # Explicitly use openpyxl
            usecols=use_cols,
            converters=converters
        )
        print(f"  Successfully read {df.shape[0]} rows, {df.shape[1]} columns.")
        return df
    except Exception as e:
        print(f"Error reading sheet '{actual_sheet_name}' from {file_path}: {e}")
        return None

# --- Specific Reader Functions ---

def read_financial_summary_data(settings: Dict[str, Any]) -> Dict[str, Optional[pd.DataFrame]]:
    """Reads Balance Sheet and Monthly Income/Expense data."""
    fs_config = settings.get('data_files', {}).get('financial_summary')
    if not fs_config:
        print("Error: 'financial_summary' configuration not found in settings.")
        return {'balance_sheet': None, 'monthly_income_expense': None}

    # Balance Sheet: Header is on Row 4 (index 3)
    balance_df = read_excel_file(fs_config, 'balance_sheet', header_row=3)
    # Monthly Income/Expense: Header is on Row 4 (index 3)
    monthly_df = read_excel_file(fs_config, 'monthly_income_expense', header_row=3)

    return {'balance_sheet': balance_df, 'monthly_income_expense': monthly_df}

def read_fund_data(settings: Dict[str, Any]) -> Dict[str, Optional[pd.DataFrame]]:
    """Reads Fund Holdings and Transactions data."""
    fund_config = settings.get('data_files', {}).get('fund_transactions')
    if not fund_config:
        print("Error: 'fund_transactions' configuration not found in settings.")
        return {'holdings': None, 'transactions': None}

    # Specify converters for fund code
    converters = {'基金代码': str}

    holdings_df = read_excel_file(fund_config, 'holdings', header_row=0, converters=converters)
    transactions_df = read_excel_file(fund_config, 'transactions', header_row=0, converters=converters)

    return {'holdings': holdings_df, 'transactions': transactions_df}

def read_gold_data(settings: Dict[str, Any]) -> Dict[str, Optional[pd.DataFrame]]:
    """Reads Gold Holdings and Transactions data."""
    gold_config = settings.get('data_files', {}).get('gold_transactions')
    if not gold_config:
        print("Error: 'gold_transactions' configuration not found in settings.")
        return {'holdings': None, 'transactions': None}

    holdings_df = read_excel_file(gold_config, 'holdings', header_row=0)
    transactions_df = read_excel_file(gold_config, 'transactions', header_row=0)

    return {'holdings': holdings_df, 'transactions': transactions_df}

def read_insurance_data(settings: Dict[str, Any]) -> Dict[str, Optional[pd.DataFrame]]:
    """Reads Insurance Summary and Premiums data."""
    ins_config = settings.get('data_files', {}).get('insurance_portfolio')
    if not ins_config:
        print("Error: 'insurance_portfolio' configuration not found in settings.")
        return {'summary': None, 'premiums': None}

    summary_df = read_excel_file(ins_config, 'summary', header_row=0)
    premiums_df = read_excel_file(ins_config, 'premiums', header_row=0) # Premiums read in wide format initially

    return {'summary': summary_df, 'premiums': premiums_df}

def read_rsu_data(settings: Dict[str, Any]) -> Dict[str, Optional[pd.DataFrame]]:
    """Reads RSU Transactions data."""
    # Assuming RSU data path is added to settings.yaml under 'rsu_transactions' key
    rsu_config = settings.get('data_files', {}).get('rsu_transactions')
    if not rsu_config:
        print("Info: 'rsu_transactions' configuration not found in settings. Skipping RSU data.")
        return {'transactions': None} # Return None if config not found

    # Assuming the sheet name is defined as 'transactions' in settings for rsu_transactions
    # Assuming header is on the first row (index 0)
    transactions_df = read_excel_file(rsu_config, 'transactions', header_row=0)

    return {'transactions': transactions_df}

def find_latest_file_by_pattern(pattern: str) -> Optional[str]:
    """
    Finds the most recently modified file matching the given glob pattern.
    
    Args:
        pattern: Glob pattern to match files (e.g., "data/Individual-Positions-*.csv")
    
    Returns:
        Path to the most recently modified file, or None if no files match
    """
    matching_files = glob.glob(pattern)
    if not matching_files:
        print(f"Warning: No files found matching pattern '{pattern}'")
        return None
    
    # Sort by modification time (most recent first)
    latest_file = max(matching_files, key=os.path.getmtime)
    print(f"Found latest file for pattern '{pattern}': {latest_file}")
    return latest_file

def read_schwab_holdings_csv(file_path: str) -> Optional[pd.DataFrame]:
    """
    Reads Schwab holdings CSV file.
    
    Args:
        file_path: Path to the holdings CSV file
    
    Returns:
        DataFrame with holdings data, or None if error occurs
    """
    if not os.path.exists(file_path):
        print(f"Error: Schwab holdings file not found at {file_path}")
        return None
    
    try:
        # Skip first 2 metadata rows to get proper column headers
        # Row 0: Account header, Row 1: Empty, Row 2: Column names
        df = pd.read_csv(file_path, skiprows=2, skipfooter=2, engine='python')
        print(f"Successfully read Schwab holdings CSV: {file_path}")
        return df
    except Exception as e:
        print(f"Error reading Schwab holdings CSV {file_path}: {e}")
        return None

def read_schwab_transactions_csv(file_path: str) -> Optional[pd.DataFrame]:
    """
    Reads Schwab transactions CSV file.
    
    Args:
        file_path: Path to the transactions CSV file
    
    Returns:
        DataFrame with transactions data, or None if error occurs
    """
    if not os.path.exists(file_path):
        print(f"Error: Schwab transactions file not found at {file_path}")
        return None
    
    try:
        expected_cols = {"Date", "Action", "Symbol", "Description", "Quantity", "Price", "Amount"}
        # First attempt: assume header present (no skip)
        df_primary = pd.read_csv(file_path)
        cols_primary = set(df_primary.columns.astype(str))
        if expected_cols.issubset(cols_primary):
            print(f"Successfully read Schwab transactions CSV (standard header): {file_path}")
            return df_primary
        # Second attempt: maybe first row is metadata, original implementation skipped 1 row
        df_skip1 = pd.read_csv(file_path, skiprows=1)
        cols_skip1 = set(df_skip1.columns.astype(str))
        if expected_cols.issubset(cols_skip1):
            print(f"Successfully read Schwab transactions CSV (after skipping 1 metadata row): {file_path}")
            return df_skip1
        # Heuristic: if column names look like a data row (e.g. first col matches date pattern like MM/DD/YYYY)
        import re
        date_pattern = re.compile(r"\d{2}/\d{2}/\d{4}")
        suspicious_header = any(date_pattern.match(str(c)) for c in df_primary.columns[:1])
        if suspicious_header:
            # Re-read treating there is one metadata line and our current columns are actually first data row
            # Read raw lines to count columns
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            # Determine delimiter by checking first non-empty line
            sample_line = next((ln for ln in lines if ln.strip()), '')
            delimiter = ',' if sample_line.count(',') >= sample_line.count('\t') else '\t'
            # Build provisional header list sized to split count of data row
            first_data = [cell.strip() for cell in lines[0].strip().split(delimiter)]
            # Fallback header schema (order based on Schwab export typical format)
            fallback_headers = ["Date", "Action", "Symbol", "Description", "Quantity", "Price", "Fees & Comm", "Amount"]
            header_to_use = fallback_headers[:len(first_data)]
            df_reparsed = pd.read_csv(file_path, names=header_to_use, header=None)
            cols_reparsed = set(df_reparsed.columns.astype(str))
            if expected_cols.intersection(cols_reparsed):
                print(f"Successfully read Schwab transactions CSV (reparsed heuristic header recovery): {file_path}")
                return df_reparsed
        # If all attempts fail, report diagnostics
        print("Warning: Could not confidently identify Schwab transactions header. Returning first parse result (may cause downstream missing columns):")
        print(f"  - Columns detected: {list(df_primary.columns)}")
        return df_primary
    except Exception as e:
        print(f"Error reading Schwab transactions CSV {file_path}: {e}")
        return None

def read_schwab_data(settings: Dict[str, Any]) -> Dict[str, Optional[pd.DataFrame]]:
    """Reads Schwab Holdings and Transactions data from CSV files."""
    schwab_config = settings.get('data_files', {}).get('schwab_investments')
    if not schwab_config:
        print("Info: 'schwab_investments' configuration not found in settings. Skipping Schwab data.")
        return {'holdings': None, 'transactions': None}

    # Get file patterns from configuration
    holdings_pattern = schwab_config.get('holdings_path_pattern')
    transactions_pattern = schwab_config.get('transactions_path_pattern')
    
    if not holdings_pattern or not transactions_pattern:
        print("Error: holdings_path_pattern or transactions_path_pattern not found in schwab_investments config.")
        return {'holdings': None, 'transactions': None}
    
    # Find latest files
    holdings_file = find_latest_file_by_pattern(holdings_pattern)
    transactions_file = find_latest_file_by_pattern(transactions_pattern)
    
    # Read CSV files
    holdings_df = read_schwab_holdings_csv(holdings_file) if holdings_file else None
    transactions_df = read_schwab_transactions_csv(transactions_file) if transactions_file else None

    return {'holdings': holdings_df, 'transactions': transactions_df}

def read_all_sources(config_path: str = 'config/settings.yaml') -> Dict[str, Any]:
    """
    Reads all configured data sources.

    Args:
        config_path: Path to the settings YAML file.

    Returns:
        A dictionary containing DataFrames for each source type:
        {
            'financial_summary': {'balance_sheet': df, 'monthly_income_expense': df},
            'funds': {'holdings': df, 'transactions': df},
            'gold': {'holdings': df, 'transactions': df},
            'insurance': {'summary': df, 'premiums': df},
            'rsu': {'transactions': df},
            'schwab': {'holdings': df, 'transactions': df}
        }
        Returns None for sources that fail to load or are not configured.
    """
    settings = load_settings(config_path)
    all_data = {}
    
    # Check for demo mode - if primary data files don't exist, try mock data
    demo_data_path = 'data/mock_financial_data.xlsx'
    use_demo_mode = False
    
    # Check if any primary data file exists
    primary_file = settings.get('data_files', {}).get('financial_summary', {}).get('path')
    if primary_file and not os.path.exists(primary_file):
        if os.path.exists(demo_data_path):
            print(f"\n⚠️  Primary data files not found. Using demo data: {demo_data_path}")
            use_demo_mode = True
    
    if use_demo_mode:
        # Load from consolidated demo file
        return _read_demo_data(demo_data_path)

    print("\n--- Reading Financial Summary ---")
    all_data['financial_summary'] = read_financial_summary_data(settings)

    print("\n--- Reading Fund Data ---")
    all_data['funds'] = read_fund_data(settings)

    print("\n--- Reading Gold Data ---")
    all_data['gold'] = read_gold_data(settings)

    print("\n--- Reading Insurance Data ---")
    all_data['insurance'] = read_insurance_data(settings)

    print("\n--- Reading RSU Data ---")
    all_data['rsu'] = read_rsu_data(settings) # Call the new RSU reader

    print("\n--- Reading Schwab Data ---")
    all_data['schwab'] = read_schwab_data(settings) # Call the new Schwab reader

    print("\nFinished reading all sources.")
    return all_data


def _read_demo_data(demo_path: str) -> Dict[str, Any]:
    """
    Read data from consolidated demo/mock Excel file.
    
    The demo file uses English column names matching the 'default' profile
    in column_mapping.yaml.
    
    Args:
        demo_path: Path to mock_financial_data.xlsx
        
    Returns:
        Dictionary with data matching read_all_sources structure
    """
    print(f"\n📊 Loading demo data from: {demo_path}")
    all_data = {}
    
    try:
        xls = pd.ExcelFile(demo_path, engine='openpyxl')
        available_sheets = xls.sheet_names
        print(f"   Available sheets: {available_sheets}")
        
        # Map demo sheets to expected structure
        # Holdings -> fund holdings (simulated)
        if 'Holdings' in available_sheets:
            holdings_df = pd.read_excel(xls, sheet_name='Holdings')
            all_data['funds'] = {'holdings': holdings_df, 'transactions': None}
            print(f"   ✓ Loaded Holdings: {len(holdings_df)} rows")
        else:
            all_data['funds'] = {'holdings': None, 'transactions': None}
            
        # Transactions -> fund transactions
        if 'Transactions' in available_sheets:
            txn_df = pd.read_excel(xls, sheet_name='Transactions')
            if 'funds' in all_data:
                all_data['funds']['transactions'] = txn_df
            else:
                all_data['funds'] = {'holdings': None, 'transactions': txn_df}
            print(f"   ✓ Loaded Transactions: {len(txn_df)} rows")
            
        # Balance Sheet
        if 'Balance Sheet' in available_sheets:
            bs_df = pd.read_excel(xls, sheet_name='Balance Sheet')
            all_data['financial_summary'] = {
                'balance_sheet': bs_df,
                'monthly_income_expense': None
            }
            print(f"   ✓ Loaded Balance Sheet: {len(bs_df)} rows")
        else:
            all_data['financial_summary'] = {'balance_sheet': None, 'monthly_income_expense': None}
            
        # Monthly Cash Flow
        if 'Monthly Cash Flow' in available_sheets:
            cf_df = pd.read_excel(xls, sheet_name='Monthly Cash Flow')
            if 'financial_summary' in all_data:
                all_data['financial_summary']['monthly_income_expense'] = cf_df
            else:
                all_data['financial_summary'] = {'balance_sheet': None, 'monthly_income_expense': cf_df}
            print(f"   ✓ Loaded Monthly Cash Flow: {len(cf_df)} rows")
            
        # Initialize empty structures for unsupported demo data types
        all_data.setdefault('gold', {'holdings': None, 'transactions': None})
        all_data.setdefault('insurance', {'summary': None, 'premiums': None})
        all_data.setdefault('rsu', {'transactions': None})
        all_data.setdefault('schwab', {'holdings': None, 'transactions': None})
        
        print(f"\n✅ Demo data loaded successfully")
        return all_data
        
    except Exception as e:
        print(f"❌ Error loading demo data: {e}")
        # Return empty structure on error
        return {
            'financial_summary': {'balance_sheet': None, 'monthly_income_expense': None},
            'funds': {'holdings': None, 'transactions': None},
            'gold': {'holdings': None, 'transactions': None},
            'insurance': {'summary': None, 'premiums': None},
            'rsu': {'transactions': None},
            'schwab': {'holdings': None, 'transactions': None}
        }

def read_raw_fund_sheets(file_path: str) -> tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Reads raw fund data from paste sheets for automated processing.
    
    Args:
        file_path: Path to the Excel file containing raw paste sheets.
        
    Returns:
        tuple: (raw_holdings_df, raw_transactions_df)
               Returns (None, None) if file doesn't exist or sheets are empty.
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return None, None
    
    try:
        # Read raw holdings paste sheet
        raw_holdings_df = None
        try:
            raw_holdings_df = pd.read_excel(file_path, sheet_name='raw_holdings_paste')
            if raw_holdings_df.empty:
                logger.warning("raw_holdings_paste sheet is empty")
                raw_holdings_df = None
            else:
                logger.info(f"Successfully read {len(raw_holdings_df)} rows from raw_holdings_paste")
        except Exception as e:
            logger.warning(f"Error reading raw_holdings_paste sheet: {e}")
            raw_holdings_df = None
        
        # Read raw transactions paste sheet  
        raw_transactions_df = None
        try:
            raw_transactions_df = pd.read_excel(file_path, sheet_name='raw_transactions_paste')
            if raw_transactions_df.empty:
                logger.warning("raw_transactions_paste sheet is empty")
                raw_transactions_df = None
            else:
                logger.info(f"Successfully read {len(raw_transactions_df)} rows from raw_transactions_paste")
        except Exception as e:
            logger.warning(f"Error reading raw_transactions_paste sheet: {e}")
            raw_transactions_df = None
            
        return raw_holdings_df, raw_transactions_df
        
    except Exception as e:
        logger.error(f"Critical error reading raw fund sheets from {file_path}: {e}")
        return None, None