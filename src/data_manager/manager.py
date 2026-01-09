# File path: src/data_manager/manager.py
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from typing import Dict, Optional, Any, Tuple, List
import os

# Import functions from other modules within the package
# Use relative imports for intra-package dependencies
from . import readers
from . import cleaners
from . import calculators

# --- Asset ID Generation Logic ---
def generate_asset_id(asset_name: Optional[str], asset_type: Optional[str] = None, code: Optional[str] = None) -> Optional[str]:
    """
    Generates a standardized Asset ID based on available info.
    Prioritizes standard codes, then uses type and name conventions.

    Args:
        asset_name: The original name of the asset.
        asset_type: The raw asset type (optional).
        code: A standard identifier like fund code or ticker (optional).

    Returns:
        A standardized string Asset ID or None if insufficient info.
    """
    # Priority 1: Standard Code (Fund Code, Ticker)
    if code and isinstance(code, str) and code.strip():
        return code.strip()

    # Need a name if no code is provided
    if not asset_name or pd.isna(asset_name):
        return None

    name = str(asset_name).strip()
    name_normalized = name.replace(' ', '_') # Basic normalization for ID generation

    # Simple convention based on type and name
    # Use lower case for type comparison for robustness
    asset_type_lower = str(asset_type).lower() if asset_type else ''
    name_lower = name.lower()

    if '保险' in asset_type_lower or 'ins_' in name_lower or '保单' in name_lower or '平安福' in name_lower or '亚马逊加保' in name_lower:
        return f"Ins_{name_normalized}" # e.g., Ins_平安福
    elif '黄金' in asset_type_lower or 'gold_' in name_lower or '黄金' in name_lower:
         if '纸黄金' in name_lower: return 'Paper_Gold'
         if 'etf' in name_lower: return 'Gold_ETF'
         return f"Gold_{name_normalized}" # e.g., Gold_招行纸黄金
    elif 'rsu' in asset_type_lower or 'rsu_' in name_lower or 'employer' in name_lower:
        # Assuming only one RSU type for now, link to taxonomy key
        return 'Employer_Stock_A'
    elif '银行理财' in name_lower or 'wealth' in asset_type_lower:
         # Use Name directly? Or add bank identifier? Needs careful thought for uniqueness.
         return f"BankWealth_{name_normalized}" # e.g., BankWealth_招行XXX
    elif '养老金' in name_lower or 'pension' in asset_type_lower:
         return 'Pension_Personal'
    elif '房产' in name_lower or 'property' in asset_type_lower:
         return f"Property_{name_normalized}" # e.g., Property_Residential_A
    elif 'Private_Equity_Investment_A' in name_lower or '公司股份' in name_lower or 'pe_' in name_lower or '创业投资' in asset_type_lower:
         return 'PE_Private_Equity_Investment_A' # Private Equity
    elif '基金' in name_lower and '美股' in name_lower: # Handle US Fund from Balance Sheet name
         return 'Fund_US_Placeholder' # Placeholder ID if no code available

    # Fallback for types not needing detailed investment tracking
    if asset_type_lower in ['现金', '活期存款', '定期存款']:
         # Usually not tracked with Asset IDs unless specific accounts are investments
         return None # Or generate IDs like Cash_CNY, Bank_Account_A if needed

    # Default fallback - might indicate unhandled asset type or name
    # print(f"Warning: Could not generate specific Asset ID for '{name}' (Type: {asset_type}). Using normalized name.")
    return name_normalized # Use normalized name as last resort ID

# --- Transaction Type Standardization ---
# Mapping from source transaction types (keys) to standard English types (values)
TRANSACTION_TYPE_MAP = {
    # Fund Types (from 操作类型)
    '申购': 'Buy',
    '认购': 'Buy',
    '买入': 'Buy', # General Buy, also used for Gold
    '赎回': 'Sell',
    '卖出': 'Sell', # General Sell, also used for Gold, RSU
    # --- **新增**: Alipay Fund Platform Transaction Types (Oct 2025) ---
    # Buy actions
    '活期宝即充即用': 'Buy',           # Alipay money fund instant purchase
    '买基金': 'Buy',                   # Direct fund purchase
    '活期宝即充即用轧差充值': 'Buy',   # Alipay money fund net deposit
    '份额调增': 'Buy',                 # Share increase (treated as purchase for XIRR)
    '超级转换份额调增': 'Buy',         # Super conversion share increase (money market fund)
    '超级转换-转入': 'Buy',            # Super conversion - transfer in (treated as buy for XIRR)
    # Sell actions  
    '卖基金': 'Sell',                  # Direct fund sale
    '买基金取现': 'Sell',              # Fund withdrawal to cash (money market redemption)
    '快速取现': 'Sell',                # Fast withdrawal (money market quick redemption)
    '超级转换-转出': 'Sell',           # Super conversion - transfer out (treated as sell for XIRR)
    '份额调减': 'Sell',                # Share decrease (treated as redemption for XIRR)
    # Other actions (ignored for XIRR)
    '修改分红方式': 'Dividend_Setting_Change',  # Change dividend distribution method (informational only)
    # CN Fund Dividend Types
    '红利再投资': 'Dividend_Reinvest',  # Dividend reinvestment (fund shares added)
    '现金分红': 'Dividend_Cash',        # Cash dividend (cash payout)
    # Gold Types (from 交易类型)
    '结息': 'Interest',
    # RSU Types (from user's new Excel 交易类型)
    '归属': 'RSU_Vest',
    'RSU Grant': 'RSU_Grant',
    'RSU Vest': 'RSU_Vest',
    # Insurance Type (Generated during transform)
    'Premium_Payment': 'Premium_Payment',
    # --- **新增**: Schwab 交易类型映射 (基于您提供的 Action 列) ---
    'Buy': 'Buy', # Assuming Schwab 'Action' column uses these exact English terms
    'Sell': 'Sell',
    'Dividend': 'Dividend_Cash', # Or 'Dividend' if you prefer a general one
    'Reinvest Dividend': 'Dividend_Reinvest',
    'Reinvest Shares': 'Dividend_Reinvest', # Alternative dividend reinvestment naming
    'Cash Dividend': 'Dividend_Cash', # Alternative cash dividend naming
    'Qualified Dividend': 'Dividend_Cash', # Tax classification for cash dividend
    'Stock Split': 'Stock_Split',
    'Spin-off': 'Spinoff',
    'Transfer': 'Transfer',
    'Deposit': 'Cash_Deposit',
    'Withdrawal': 'Cash_Withdrawal',
    'Wire Received': 'Cash_Deposit',
    'Wire Sent': 'Cash_Withdrawal',
    'Fee': 'Fee',
    'Interest': 'Interest',
    'Credit Interest': 'Interest',  # Schwab credit interest (same as regular interest)
    'NRA Tax Adj': 'Tax_Adjustment',  # Non-Resident Alien tax adjustment
    'MoneyLink Transfer': 'Transfer',  # Schwab money transfer
    # Add others like 'Tax Withheld', 'Fee' if Schwab provides them
    # Add other source types as needed
}

def standardize_transaction_type(row: pd.Series) -> Optional[str]:
    """
    Standardizes transaction type based on source columns (操作类型, 交易原因, etc.).
    Handles special fund dividend cases first.

    Args:
        row: A Pandas Series representing a transaction row.

    Returns:
        The standardized transaction type string or None if undetermined.
    """
    # --- Priority 0: Explicit RSU Handling (Robust Fix) ---
    # This is a high-priority rule to ensure RSU transactions are always handled correctly,
    # bypassing potential issues in the generic mapping logic.
    asset_id = row.get('Asset_ID')
    raw_type_rsu = row.get('Transaction_Type_Raw')
    if asset_id == 'Employer_Stock_A' and raw_type_rsu and isinstance(raw_type_rsu, str):
        rsu_map = {
            '归属': 'RSU_Vest',
            '卖出': 'Sell'
        }
        standard_type = rsu_map.get(raw_type_rsu.strip())
        if standard_type:
            return standard_type

    # Define constants for fund dividend reasons (match user's analysis code)
    TRADE_REASON_DIVIDEND_CASH = '现金分红'
    TRADE_REASON_DIVIDEND_REINVEST = '红利再投资'

    # Priority 1: Fund Dividend Reasons (requires Memo and Raw Type)
    memo = row.get('Memo')
    raw_type_fund = row.get('Transaction_Type_Raw') # Specific name from fund cleaning

    if isinstance(memo, str):
         memo = memo.strip()
         
         # Robust Dividend Handling: Check Memo first, ignore Raw Type if Memo is explicit
         if TRADE_REASON_DIVIDEND_CASH in memo:
              return 'Dividend_Cash'
         if TRADE_REASON_DIVIDEND_REINVEST in memo:
              return 'Dividend_Reinvest'
              
         # Legacy check (keep as fallback if needed, but redundant with above)
         if isinstance(raw_type_fund, str):
              raw_type_fund = raw_type_fund.strip()
              if memo == TRADE_REASON_DIVIDEND_CASH and raw_type_fund == '赎回':
                   return 'Dividend_Cash'
              if memo == TRADE_REASON_DIVIDEND_REINVEST and raw_type_fund == '申购':
                   return 'Dividend_Reinvest'

    # Priority 2: Standard Mapping based on Raw Type
    # Check multiple possible raw type column names
    raw_type = row.get('Transaction_Type_Raw') # From Fund/Gold/RSU cleaning
    if not raw_type or pd.isna(raw_type):
        raw_type = row.get('交易类型') # Fallback to original Gold/RSU name if needed
    if not raw_type or pd.isna(raw_type):
        raw_type = row.get('操作类型') # Fallback to original Fund name if needed

    if raw_type and isinstance(raw_type, str):
        standard_type = TRANSACTION_TYPE_MAP.get(raw_type.strip())
        if standard_type:
            return standard_type
        else:
            # Log unrecognized transaction types to help identify missing mappings
            import logging
            logger = logging.getLogger(__name__)
            asset_name = row.get('Asset_Name', 'Unknown')
            txn_date = row.get('Transaction_Date', 'Unknown date')
            logger.warning(
                f"⚠️  UNRECOGNIZED TRANSACTION TYPE: '{raw_type}' "
                f"for asset '{asset_name}' on {txn_date}"
            )
            logger.warning(
                f"   → Add this type to TRANSACTION_TYPE_MAP in src/data_manager/manager.py"
            )
            return None

    # Priority 3: Generated Type (e.g., Premiums)
    generated_type = row.get('Transaction_Type') # Check if type was already assigned
    if generated_type and isinstance(generated_type, str):
        # Validate if it's one of our known standard types (optional but good)
        if generated_type in ['Buy', 'Sell', 'Dividend_Cash', 'Dividend_Reinvest', 'Interest', 'Premium_Payment', 'RSU_Vest', 'Fee']:
             return generated_type

    # If no type determined, log a warning (optional)
    # print(f"Warning: Could not determine standard transaction type for row: {row.get('Asset_Name', 'Unknown')}, Raw Type: {raw_type}")
    return None


# --- Sign Convention Logic ---
def apply_transaction_sign_convention(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies sign conventions to Quantity and Amount_Net based on standardized Transaction_Type.

    Args:
        df: DataFrame with a 'Transaction_Type' column and amount/quantity columns.

    Returns:
        DataFrame with adjusted signs for Quantity and Amount_Net.
    """
    if df.empty or 'Transaction_Type' not in df.columns:
        return df # Return early if no type column or empty

    df_signed = df.copy()

    # --- Quantity Sign Convention ---
    # + for Buy/In/Vest/Interest(if adds units like reinvest), - for Sell/Out
    buy_types = ['Buy', 'Dividend_Reinvest', 'RSU_Vest', 'RSU_Grant', 'Interest'] # Types increasing holding units
    sell_types = ['Sell'] # Types decreasing holding units
    no_quantity_types = ['Dividend_Cash', 'Premium_Payment', 'Fee'] # Types without quantity concept

    if 'Quantity' in df_signed.columns:
        # Ensure Quantity is numeric first, fill NaN with 0 for sign application
        df_signed['Quantity'] = pd.to_numeric(df_signed['Quantity'], errors='coerce').fillna(0.0)

        mask_buy = df_signed['Transaction_Type'].isin(buy_types)
        mask_sell = df_signed['Transaction_Type'].isin(sell_types)
        mask_no_qty = df_signed['Transaction_Type'].isin(no_quantity_types)

        # Make quantities positive first, then apply negative sign for sell types
        df_signed['Quantity'] = df_signed['Quantity'].abs()
        df_signed.loc[mask_sell, 'Quantity'] = -df_signed.loc[mask_sell, 'Quantity']
        # For types like Premium_Payment or Dividend_Cash, set Quantity to NaN
        df_signed.loc[mask_no_qty, 'Quantity'] = np.nan

    # --- Amount_Net Sign Convention & Calculation ---
    # + for Cash In (Sell/Dividend/Interest), - for Cash Out (Buy/Premium/Fee/Reinvest)
    # Ensure relevant amount columns are numeric and exist
    for col in ['Amount_Gross', 'Commission_Fee']:
         if col in df_signed.columns:
              df_signed[col] = pd.to_numeric(df_signed[col], errors='coerce').fillna(0.0)
         else:
              df_signed[col] = 0.0 # Add column as 0 if missing

    # Normalize gross amounts for core transactional types to avoid double negatives from upstream sources
    if 'Transaction_Type' in df_signed.columns:
       normalize_mask = df_signed['Transaction_Type'].isin(['Buy', 'Sell', 'Dividend_Cash', 'Dividend_Reinvest', 'Interest', 'Premium_Payment', 'RSU_Vest', 'RSU_Grant'])
       df_signed.loc[normalize_mask, 'Amount_Gross'] = df_signed.loc[normalize_mask, 'Amount_Gross'].abs()

    # Define calculation logic based on type
    def calculate_net(row):
        gross = row['Amount_Gross']
        fee = row['Commission_Fee']
        txn_type = row.get('Transaction_Type') # Use .get for safety

        if txn_type in ['Buy', 'Premium_Payment', 'Dividend_Reinvest']:
            # Cash outflow = Gross Amount + Fee
            return -(gross + fee)
        elif txn_type in ['Sell', 'Dividend_Cash', 'Interest']:
            # Cash inflow = Gross Amount - Fee
            return gross - fee
        elif txn_type == 'Fee': # If Fee type is added later
             return -fee
        elif txn_type in ['RSU_Vest', 'RSU_Grant']:
             # RSU Grant/Vest should record cost basis at fair market value for tax purposes
             # This is essential for accurate cost basis calculation
             return -(gross + fee)  # Treat as cash outflow (cost basis)
        else:
            # Fallback for unknown types or if Amount_Net was pre-calculated
            return row.get('Amount_Net', 0.0) # Default to 0 if column missing

    # Apply the calculation to create/overwrite Amount_Net
    df_signed['Amount_Net'] = df_signed.apply(calculate_net, axis=1)

    print("  - Applied sign conventions to Quantity and Amount_Net.")
    return df_signed


# --- Main Orchestration Logic ---

class DataManager:
    """
    Orchestrates the reading, cleaning, transforming, calculating,
    and integrating of financial data from multiple Excel sources.

    Provides access to the final, processed DataFrames.
    """
    def __init__(self, config_path: str = 'config/settings.yaml', force_mode: Optional[str] = None):
        """
        Initializes the DataManager, loads settings, and runs the full data processing pipeline.

        Args:
            config_path: Path to the main settings YAML file.
            force_mode: Optional override for operation mode ('excel' or 'database').
        """
        print("Initializing DataManager...")
        self.config_path = config_path
        self.settings = readers.load_settings(config_path) # Load config first

        # Detect database mode from settings
        database_config = self.settings.get('database', {})
        
        if force_mode:
            self.database_mode = force_mode
            print(f"⚠️  Mode forced to: {self.database_mode.upper()}")
        else:
            self.database_mode = database_config.get('mode', 'excel')  # Default to Excel mode
            
        self.db_connector = None
        
        if self.database_mode == 'database':
            # Import DatabaseConnector lazily
            from src.database.connector import DatabaseConnector
            db_path = database_config.get('path', 'data/investment_system.db')
            self.db_connector = DatabaseConnector(database_path=db_path)
            print(f"📊 DataManager operating in DATABASE mode (db: {db_path})")
        else:
            print(f"📊 DataManager operating in EXCEL mode")

        # Initialize data dictionaries (used in Excel mode)
        self.raw_data: Dict[str, Any] = {}
        self.cleaned_data: Dict[str, Optional[pd.DataFrame]] = {}
        self.calculated_data: Dict[str, Optional[pd.DataFrame]] = {}
        self.final_data: Dict[str, Optional[pd.DataFrame]] = {}
        self.fx_rates: Optional[pd.Series] = None # To store FX rates
        
        # Initialize historical data cache
        self.historical_holdings_cache: Optional[pd.DataFrame] = None

        # Execute processing steps.
        if self.database_mode == 'excel':
            self._initialize_excel_pipeline()
        else:
            load_excel_fallback = database_config.get('load_excel_fallback', True)
            if load_excel_fallback:
                print("📎 Database mode: loading Excel compatibility pipeline for legacy modules (balance sheet, monthly cash flow, etc.)")
                self._initialize_excel_pipeline()
            else:
                print("⚠️ Excel compatibility disabled in database mode. Some reports may not have historical data until database tables are populated.")

        print("DataManager initialized and data processed.")

    def _initialize_excel_pipeline(self) -> None:
        """Run the legacy Excel processing pipeline for modules still depending on it."""
        self._load_raw_data()
        self._clean_and_transform_data()
        self._calculate_data()
        self._integrate_data()

        # Load historical snapshots if enabled
        self._load_historical_data()

        # Perform cleanup of old snapshots
        self._cleanup_old_snapshots()

    def _load_raw_data(self):
        """Loads raw data from all sources defined in settings."""
        self.raw_data = readers.read_all_sources(self.config_path)

    def _clean_and_transform_data(self):
        """Applies cleaning functions and transformations to raw data."""
        print("\n--- Cleaning and Transforming Data ---")

        # Clean individual sources and store in self.cleaned_data
        fs_data = self.raw_data.get('financial_summary', {})
        self.cleaned_data['balance_sheet'] = cleaners.clean_balance_sheet(fs_data.get('balance_sheet'), self.settings)
        self.cleaned_data['monthly_income_expense'] = cleaners.clean_monthly_income_expense(fs_data.get('monthly_income_expense'), self.settings)

        fund_data = self.raw_data.get('funds', {})
        self.cleaned_data['fund_holdings'] = cleaners.clean_fund_holdings(fund_data.get('holdings'), self.settings)
        self.cleaned_data['fund_transactions'] = cleaners.clean_fund_transactions(fund_data.get('transactions'), self.settings)

        gold_data = self.raw_data.get('gold', {})
        self.cleaned_data['gold_holdings'] = cleaners.clean_gold_holdings(gold_data.get('holdings'), self.settings)
        self.cleaned_data['gold_transactions'] = cleaners.clean_gold_transactions(gold_data.get('transactions'), self.settings)

        ins_data = self.raw_data.get('insurance', {})
        self.cleaned_data['insurance_summary'] = cleaners.clean_insurance_summary(ins_data.get('summary'), self.settings)
        # Transform premiums - result is already like a transaction df
        self.cleaned_data['insurance_premiums_long'] = cleaners.transform_insurance_premiums(ins_data.get('premiums'), self.settings)

        rsu_data = self.raw_data.get('rsu', {})
        self.cleaned_data['rsu_transactions'] = cleaners.clean_rsu_transactions(rsu_data.get('transactions'), self.settings)

        # --- **新增**: 清洗 Schwab 数据 (CSV format) ---
        schwab_data = self.raw_data.get('schwab', {})
        self.cleaned_data['schwab_holdings'] = cleaners.clean_schwab_holdings_csv(schwab_data.get('holdings'), self.settings)
        self.cleaned_data['schwab_transactions'] = cleaners.clean_schwab_transactions_csv(schwab_data.get('transactions'), self.settings)
        # --- **新增结束** ---

    def _calculate_data(self):
        """Performs calculations like currency conversion and totals on cleaned data."""
        print("\n--- Calculating Data ---")

        # Get FX rates first, store as instance variable
        self.fx_rates = calculators.get_fx_rates(self.cleaned_data.get('monthly_income_expense'))
        
        # Initialize currency converter service with Excel rates for fallback
        if self.fx_rates is not None and not self.fx_rates.empty:
            from .currency_converter import initialize_currency_service
            # Use Excel-first strategy with API disabled for best performance
            initialize_currency_service(
                excel_rates=self.fx_rates, 
                use_excel_fallback=True,
                prefer_excel=True,      # Try Excel BEFORE API (instant vs 206+ seconds)
                enable_forex_api=False  # Disable slow forex-python API by default
            )
            print(f"  - Initialized currency converter with {len(self.fx_rates)} Excel exchange rates (API disabled for performance)")

        # Calculate for Balance Sheet using self.fx_rates
        self.calculated_data['balance_sheet'] = calculators.calculate_balance_sheet_totals(
            self.cleaned_data.get('balance_sheet'), self.fx_rates
        )
        # Calculate for Monthly Income/Expense using self.fx_rates
        self.calculated_data['monthly_income_expense'] = calculators.calculate_monthly_totals(
            self.cleaned_data.get('monthly_income_expense'), self.fx_rates
        )

    def _integrate_data(self): # <-- **修改此方法**
        """Integrates data from various sources into final holdings and transactions DFs."""
        print("\n--- Integrating Data ---")
        self.final_data['balance_sheet_df'] = self.calculated_data.get('balance_sheet')
        self.final_data['monthly_df'] = self.calculated_data.get('monthly_income_expense')
        print("  - Integrating Holdings...")
        all_holdings: List[pd.DataFrame] = []
        latest_bs_date = pd.Timestamp.min
        if self.final_data['balance_sheet_df'] is not None and not self.final_data['balance_sheet_df'].empty:
            latest_bs_date = self.final_data['balance_sheet_df'].index.max()
        else:
            print("    - Warning: Cannot determine latest balance sheet date.")
            latest_bs_date = pd.Timestamp.now().normalize()
        
        # 获取最新的汇率信息，优先使用最接近资产负债表日期的汇率
        fx_rate_latest = None
        if self.fx_rates is not None and not self.fx_rates.empty:
            relevant_rates = self.fx_rates.loc[self.fx_rates.index <= latest_bs_date]
            if not relevant_rates.empty:
                fx_rate_latest = relevant_rates.iloc[-1]
                print(f"    - Using USD/CNY FX rate: {fx_rate_latest} from {relevant_rates.index[-1]}")
            else:
                # 如果没有找到早于资产负债表日期的汇率，则使用最早的可用汇率
                fx_rate_latest = self.fx_rates.iloc[0]
                print(f"    - Warning: No FX rate found before {latest_bs_date}. Using earliest available: {fx_rate_latest}")
        
        # a) Fund Holdings (Update to use latest_bs_date)
        df_fund_h = self.cleaned_data.get('fund_holdings')
        if df_fund_h is not None and not df_fund_h.empty:
            print("    - Processing Fund Holdings...")
            temp_h = df_fund_h.copy()
            required_fund_cols = ['Asset_ID', 'Asset_Name', 'Asset_Type_Raw', 'Quantity', 'Market_Price_Unit', 'Market_Value_Raw']
            if all(col in temp_h.columns for col in required_fund_cols):
                # Major Fix: Filter for LATEST snapshot only before overwriting date
                # This prevents double counting if the Excel file contains multiple historical snapshots
                if 'Snapshot_Date' in temp_h.columns:
                    # Convert to datetime if not already
                    temp_h['Snapshot_Date'] = pd.to_datetime(temp_h['Snapshot_Date'], errors='coerce')
                    latest_snapshot = temp_h['Snapshot_Date'].max()
                    
                    if pd.notna(latest_snapshot):
                        original_count = len(temp_h)
                        # CRITICAL FIX: QDII funds often have T-1 or T-2 dates (e.g., 12-11 vs 12-12).
                        # Exact matching 'latest_snapshot' drops them.
                        # Use a tolerance window (e.g., 3 days) to capture the full "Latest Batch".
                        tolerance_window = pd.Timedelta(days=5) 
                        date_threshold = latest_snapshot - tolerance_window
                        
                        # Filter for rows within the latest reporting window
                        temp_h = temp_h[temp_h['Snapshot_Date'] >= date_threshold].copy()
                        
                        # Now we might have multiple dates for the same asset (if user uploaded weekly).
                        # We must distinct by Asset_ID, keeping the latest one found.
                        temp_h = temp_h.sort_values('Snapshot_Date', ascending=False)
                        temp_h = temp_h.drop_duplicates(subset=['Asset_ID'], keep='first')
                        
                        print(f"      - Filtered Fund Holdings to latest snapshot window ({date_threshold.date()} to {latest_snapshot.date()}) (Kept {len(temp_h)}/{original_count} records)")
                    else:
                        print("      - Warning: No valid Snapshot_Date found in Fund Holdings. Using all rows.")
                
                # Replace original snapshot date with latest_bs_date for unified timing
                temp_h['Snapshot_Date'] = pd.to_datetime(latest_bs_date)
                temp_h['Asset_ID'] = temp_h['Asset_ID'].astype(str)
                temp_h['Currency'] = 'CNY'
                temp_h['Unit'] = 'Shares'  # <-- **明确设置 Unit**
                for col in ['Cost_Price_Unit', 'Account', 'Insurance_CashValue_CNY']:
                    temp_h[col] = np.nan
                cols_to_keep = [
                    'Snapshot_Date', 'Asset_ID', 'Asset_Name', 'Asset_Type_Raw', 'Quantity',
                    'Unit', 'Cost_Price_Unit', 'Market_Price_Unit', 'Market_Value_Raw',
                    'Currency', 'Account', 'Insurance_CashValue_CNY'
                ]
                cols_present = [col for col in cols_to_keep if col in temp_h.columns]
                
                # Fix: Aggregate duplicates to prevent "duplicate keys" error
                # This handles cases where the same fund appears multiple times (e.g. different accounts or data error)
                agg_rules = {
                    'Asset_Name': 'first',
                    'Asset_Type_Raw': 'first',
                    'Quantity': 'sum',
                    'Unit': 'first',
                    'Cost_Price_Unit': 'mean',
                    'Market_Price_Unit': 'mean',
                    'Market_Value_Raw': 'sum',
                    'Currency': 'first',
                    'Account': 'first',
                    'Insurance_CashValue_CNY': 'sum'
                }
                # Only aggregate columns that actually exist
                final_agg = {k: v for k, v in agg_rules.items() if k in cols_present}
                
                temp_h_agg = temp_h.groupby(['Snapshot_Date', 'Asset_ID']).agg(final_agg).reset_index()
                
                all_holdings.append(temp_h_agg.set_index(['Snapshot_Date', 'Asset_ID']))
                print(f"      - Set all fund holdings to snapshot date: {latest_bs_date.strftime('%Y-%m-%d')} (Aggregated {len(temp_h)} -> {len(temp_h_agg)} records)")
            else:
                print("      - Warning: Fund holdings missing required columns. Skipping.")

        # b) Gold Holdings - Aggregate all accounts into a single entry
        df_gold_h = self.cleaned_data.get('gold_holdings')
        if df_gold_h is not None and not df_gold_h.empty:
            print("    - Processing Gold Holdings...")
            temp_h = df_gold_h.copy()
            temp_h['Snapshot_Date'] = pd.to_datetime(latest_bs_date)
            
            # Log accounts found for debugging
            if 'Account' in temp_h.columns:
                unique_accounts = temp_h['Account'].dropna().unique()
                print(f"      - Found Gold holdings from {len(unique_accounts)} account(s): {list(unique_accounts)}")
            else:
                unique_accounts = []
                print("      - No Account column found, treating as single account")
            
            # Aggregate all Gold holdings into a single entry with combined values
            # This ensures the report shows total Gold value from all accounts
            aggregated = {
                'Snapshot_Date': pd.to_datetime(latest_bs_date),
                'Asset_ID': 'Paper_Gold',  # Single unified ID
                'Asset_Name': '纸黄金',
                'Asset_Type_Raw': '黄金',
                'Quantity': temp_h['Quantity'].sum() if 'Quantity' in temp_h.columns else 0,
                'Unit': temp_h['Unit'].iloc[0] if 'Unit' in temp_h.columns else 'Gram',
                'Cost_Price_Unit': (temp_h['Cost_Price_Unit'] * temp_h['Quantity']).sum() / temp_h['Quantity'].sum() if 'Cost_Price_Unit' in temp_h.columns and temp_h['Quantity'].sum() > 0 else np.nan,
                'Market_Price_Unit': temp_h['Market_Price_Unit'].iloc[0] if 'Market_Price_Unit' in temp_h.columns else np.nan,
                'Market_Value_Raw': temp_h['Market_Value_Raw'].sum() if 'Market_Value_Raw' in temp_h.columns else 0,
                'Currency': 'CNY',
                'Account': ', '.join(unique_accounts) if len(unique_accounts) > 0 else None,  # Store all accounts
                'Insurance_CashValue_CNY': np.nan
            }
            
            # Create single-row DataFrame from aggregated data
            temp_h_agg = pd.DataFrame([aggregated])
            temp_h_agg['Snapshot_Date'] = pd.to_datetime(temp_h_agg['Snapshot_Date'])
            temp_h_agg = temp_h_agg.set_index(['Snapshot_Date', 'Asset_ID'])
            
            all_holdings.append(temp_h_agg)
            print(f"      - Aggregated Gold total: ¥{aggregated['Market_Value_Raw']:,.2f} (Qty: {aggregated['Quantity']:.4f}g)")

        # c) Insurance Holdings (Already using latest_bs_date - no change needed)
        df_ins_s = self.cleaned_data.get('insurance_summary')
        if df_ins_s is not None and not df_ins_s.empty:
            print("    - Processing Insurance Holdings (Cash Value)...")  # ... (粘贴之前的 Insurance Holdings 处理代码) ...
            temp_h = df_ins_s.copy()
            temp_h['Snapshot_Date'] = pd.to_datetime(latest_bs_date)
            temp_h['Asset_ID'] = temp_h['Asset_Name'].apply(lambda x: generate_asset_id(x, asset_type='保险'))
            temp_h['Quantity'] = 1
            temp_h['Unit'] = 'Policy'
            if 'Annual_Premium' in temp_h.columns:
                temp_h['Insurance_CashValue_CNY'] = pd.to_numeric(temp_h['Annual_Premium'], errors='coerce').fillna(0.0) * 0.5
            else:
                temp_h['Insurance_CashValue_CNY'] = 0.0
            temp_h['Market_Value_Raw'] = temp_h['Insurance_CashValue_CNY']
            temp_h['Currency'] = 'CNY'
            for col in ['Cost_Price_Unit', 'Market_Price_Unit', 'Account']:
                temp_h[col] = np.nan
            cols_to_keep = [
                'Snapshot_Date', 'Asset_ID', 'Asset_Name', 'Asset_Type_Raw', 'Quantity',
                'Unit', 'Cost_Price_Unit', 'Market_Price_Unit', 'Market_Value_Raw',
                'Currency', 'Account', 'Insurance_CashValue_CNY'
            ]
            cols_present = [col for col in cols_to_keep if col in temp_h.columns]
            if all(col in temp_h.columns for col in ['Snapshot_Date', 'Asset_ID']):
                # Fix duplicate keys: Aggregate by (Snapshot_Date, Asset_ID) if multiple sub-policies exist
                agg_cols = {
                    'Asset_Name': 'first',
                    'Asset_Type_Raw': 'first',
                    'Quantity': 'sum',
                    'Unit': 'first',
                    'Market_Value_Raw': 'sum',
                    'Currency': 'first',
                    'Insurance_CashValue_CNY': 'sum'
                }
                # Only aggregate numeric columns that exist
                for col in ['Cost_Price_Unit', 'Market_Price_Unit', 'Account']:
                    if col in cols_present:
                        agg_cols[col] = 'first'

                temp_h_indexed = temp_h[cols_present].groupby(['Snapshot_Date', 'Asset_ID']).agg(agg_cols)
                all_holdings.append(temp_h_indexed)
                print("      - Aggregated insurance holdings (resolved duplicate Asset_IDs for sub-policies)")
            else:
                print("      - Warning: Insurance holdings missing Snapshot_Date or Asset_ID after processing. Skipping.")

        # d) Holdings from Balance Sheet 
        df_bs = self.final_data.get('balance_sheet_df')
        if df_bs is not None and not df_bs.empty and not df_bs.index.empty:
            print("    - Processing Holdings from Balance Sheet...")
            latest_bs_data_row = df_bs.loc[latest_bs_date]
            
            # 处理投资资产 (维持原有逻辑)
            # Note (2025-11-04 Migration): Transaction-based assets (Schwab US funds, CN funds, Gold, RSU)
            # are NO LONGER sourced from balance sheet. See: docs/data_consolidation_migration_plan.md
            bs_holding_cols_map = {
                # Transaction-based assets - now sourced exclusively from transaction files:
                # 'Asset_Invest_RSU_Value_USD': RSU holdings from RSU_transactions.xlsx
                # 'Asset_Invest_USFund_Value_USD': Schwab holdings from Individual-Positions-*.csv
                
                # Balance sheet-only assets (no transaction files available):
                'Asset_Invest_BankWealth_Value': ('BankWealth_招行', '货币市场', 'Unit', 'CNY'),  # Fixed: Changed from '银行理财' to '货币市场' for proper categorization
                'Asset_Invest_Pension_Value': ('Pension_Personal', '养老金', 'Unit', 'CNY'),
                'Asset_Invest_Private_Equity_Investment_A': ('PE_Private_Equity_Investment_A', '创业投资', 'Unit', 'CNY'),
                'Asset_Fixed_Property_Value': ('Property_Residential_A', '住宅地产', 'Unit', 'CNY'),
            }
            monthly_df = self.final_data.get('monthly_df')
            for bs_col, (asset_id, asset_type, unit, currency) in bs_holding_cols_map.items():
                if bs_col in latest_bs_data_row.index:
                    market_value_scalar = latest_bs_data_row[bs_col]
                    # Fix: Ensure market_value_scalar is a scalar, not a Series
                    if isinstance(market_value_scalar, pd.Series):
                        market_value_scalar = market_value_scalar.iloc[0] if not market_value_scalar.empty else float('nan')
                    
                    if pd.notna(market_value_scalar):
                        try:
                            numeric_value = float(market_value_scalar)
                            if abs(numeric_value) > 1e-9:
                                qty = np.nan
                                price = np.nan
                                market_value = numeric_value  # Default to balance sheet value
                                if asset_id == 'Employer_Stock_A':
                                    # Get OLD price from Excel to establish baseline share count
                                    old_price = None
                                    if monthly_df is not None and 'Ref_Employer_Stock_Price_USD' in monthly_df.columns:
                                        if latest_bs_date in monthly_df.index:
                                            old_price = monthly_df['Ref_Employer_Stock_Price_USD'].loc[latest_bs_date]
                                            if isinstance(old_price, pd.Series):
                                                old_price = old_price.iloc[0] if not old_price.empty else float('nan')
                                    
                                    # Calculate fixed share count from balance sheet value and OLD price
                                    baseline_shares = numeric_value / old_price if old_price and pd.notna(old_price) and old_price > 0 else None
                                    
                                    # Priority 1: Try Google Finance for latest employer stock price
                                    employer_stock_price = None
                                    try:
                                        from .connectors.google_finance_connector import get_google_finance_connector
                                        connector = get_google_finance_connector()
                                        employer_stock_price = connector.get_stock_price('AMZN', 'NASDAQ')
                                        if employer_stock_price and baseline_shares:
                                            print(f"      ✓ Using Google Finance employer stock price: ${employer_stock_price:.2f}")
                                            price = employer_stock_price
                                            qty = baseline_shares  # Use FIXED share count
                                            market_value = qty * price  # Recalculate with NEW price
                                            print(f"      ✓ Recalculated RSU: {qty:.2f} shares × ${price:.2f} = ${market_value:,.2f} (was ${numeric_value:,.2f})")
                                            unit = 'Shares'
                                    except Exception as e:
                                        print(f"      - Google Finance failed for employer stock: {e}, trying Excel fallback")
                                    
                                    # Priority 2: Fall back to Excel data if Google Finance fails
                                    if employer_stock_price is None and old_price and pd.notna(old_price) and old_price > 0:
                                        print(f"      ✓ Using Excel employer stock price: ${old_price:.2f}")
                                        price = old_price
                                        qty = baseline_shares
                                        market_value = numeric_value  # Keep original value
                                        unit = 'Shares'
                                holding_entry = pd.DataFrame(
                                    {
                                        'Snapshot_Date': [latest_bs_date],
                                        'Asset_ID': [asset_id],
                                        'Asset_Name': [asset_id],
                                        'Asset_Type_Raw': [asset_type],
                                        'Quantity': [qty],
                                        'Unit': [unit],
                                        'Cost_Price_Unit': [np.nan],
                                        'Market_Price_Unit': [price],
                                        'Market_Value_Raw': [market_value],
                                        'Currency': [currency],
                                        'Account': [None],
                                        'Insurance_CashValue_CNY': [np.nan]
                                    }
                                )
                                all_holdings.append(holding_entry.set_index(['Snapshot_Date', 'Asset_ID']))
                        except (ValueError, TypeError):
                            print(f"    - Warning: Could not convert BS value '{bs_col}' to float: {market_value_scalar}. Skipping.")

            # 新增: 处理现金和存款资产
            print("    - Processing Cash and Deposit assets from Balance Sheet...")
            # 处理现金和存款列
            all_processed_cols = []
            for col in latest_bs_data_row.index:
                # CRITICAL: Skip calculated columns (_FromUSD, _FromCNY) to avoid duplicates
                # These are auto-generated by calculators.py when converting USD to CNY
                if '_FromUSD' in col or '_FromCNY' in col:
                    continue
                
                # Skip Chase/Discover CNY columns (these are duplicates from Excel - use USD only)
                # BOC has separate RMB and USD deposits, so process both BOC_CNY and BOC_USD
                if col in ['Asset_Deposit_Chase_CNY', 'Asset_Deposit_Discover_CNY']:
                    continue
                    
                # Process all remaining Cash and Deposit columns
                if ((col.startswith('Asset_Cash') or col.startswith('Asset_Deposit')) 
                    and col not in all_processed_cols):
                    
                    value = latest_bs_data_row[col]
                    # 确保value是标量值
                    if isinstance(value, pd.Series):
                        value = value.iloc[0] if not value.empty else float('nan')
                    
                    # 跳过空值或零值
                    if pd.isna(value) or abs(float(value)) < 1e-9:
                        continue
                    
                    # 处理列名，提取信息
                    parts = col.split('_')
                    asset_type = parts[1]  # Cash 或 Deposit
                    
                    # 确定银行/账户（如果适用）
                    account = None
                    if len(parts) > 2 and asset_type == 'Deposit':
                        account = parts[2]  # 如 BOC, CMB 等
                    
                    # 确定货币
                    is_usd = col.endswith('_USD')
                    currency = 'USD' if is_usd else 'CNY'
                    
                    # 添加到已处理列表 - only this column, not paired!
                    # CRITICAL FIX: Do NOT mark USD/CNY pairs as processed together
                    # Each currency variant should be added as a separate holding
                    all_processed_cols.append(col)
                    
                    # 生成资产ID和名称
                    if asset_type == 'Cash':
                        asset_id = f"Cash_{currency}"
                        asset_name = f"Cash ({currency})"
                    else:  # Deposit
                        asset_id = f"Deposit_{account}_{currency}" if account else f"Deposit_{currency}"
                        asset_name = f"{account} Deposit ({currency})" if account else f"Deposit ({currency})"
                    
                    # 创建持仓条目
                    holding_entry = pd.DataFrame({
                        'Snapshot_Date': [latest_bs_date],
                        'Asset_ID': [asset_id],
                        'Asset_Name': [asset_name],
                        'Asset_Type_Raw': [asset_type],
                        'Quantity': [1.0],  # 对于现金/存款，数量不太有意义，但设为1
                        'Unit': ['Account'],  # 对现金/存款使用'Account'作为单位
                        'Cost_Price_Unit': [np.nan],
                        'Market_Price_Unit': [np.nan],
                        'Market_Value_Raw': [value],
                        'Currency': [currency],
                        'Account': [account],
                        'Insurance_CashValue_CNY': [np.nan]
                    })
                    
                    all_holdings.append(holding_entry.set_index(['Snapshot_Date', 'Asset_ID']))
                    print(f"      - Added {asset_name} with value {value}")

        # Fixed: Removed redundant "Manual Fix for BOC Deposit Issue" section (former lines 605-641)
        # BOC deposits are now correctly processed in the main cash/deposit loop above
        # with the _FromUSD/_FromCNY filter preventing duplicate entries

        # --- **新增**: f) Schwab Holdings ---
        df_schwab_h = self.cleaned_data.get('schwab_holdings')
        if df_schwab_h is not None and not df_schwab_h.empty:
            print("    - Processing Schwab Holdings...")
            temp_h = df_schwab_h.copy()
            # Ensure Snapshot_Date is present and use it, or align to latest_bs_date
            if 'Snapshot_Date' in temp_h.columns and temp_h['Snapshot_Date'].notna().any():
                temp_h['Snapshot_Date'] = pd.to_datetime(temp_h['Snapshot_Date'], errors='coerce')
                # If you want to force all Schwab holdings to latest_bs_date:
                # temp_h['Snapshot_Date'] = pd.to_datetime(latest_bs_date)
            else:
                temp_h['Snapshot_Date'] = pd.to_datetime(latest_bs_date) # Fallback
            temp_h = temp_h.dropna(subset=['Snapshot_Date'])

            if 'Asset_ID' in temp_h.columns:  # Asset_ID is Ticker
                temp_h['Asset_ID'] = temp_h['Asset_ID'].astype(str)
                if 'Currency' not in temp_h.columns:
                    temp_h['Currency'] = 'USD'  # Default for Schwab
                if 'Unit' not in temp_h.columns:
                    temp_h['Unit'] = 'Shares'
                
                # CRITICAL FIX: Preserve Cost Data
                # cleaners.py maps 'Cost Basis' -> 'Cost_Total'
                if 'Cost_Total' in temp_h.columns:
                    temp_h['Cost_Basis_Raw'] = pd.to_numeric(temp_h['Cost_Total'], errors='coerce')
                    
                    # Calculate Cost_Price_Unit if missing
                    if 'Cost_Price_Unit' not in temp_h.columns or temp_h['Cost_Price_Unit'].isna().all():
                        # Cost per share = Total Cost / Quantity
                        temp_h['Cost_Price_Unit'] = temp_h.apply(
                            lambda row: row['Cost_Basis_Raw'] / row['Quantity'] 
                            if pd.notnull(row['Cost_Basis_Raw']) and pd.notnull(row['Quantity']) and row['Quantity'] != 0 
                            else np.nan, 
                            axis=1
                        )
                else:
                    temp_h['Cost_Basis_Raw'] = np.nan

                for col_add in ['Cost_Price_Unit', 'Account', 'Insurance_CashValue_CNY']:
                    if col_add not in temp_h.columns:
                        temp_h[col_add] = np.nan

                cols_to_keep = [
                    'Snapshot_Date', 'Asset_ID', 'Asset_Name', 'Asset_Type_Raw', 
                    'Quantity', 'Unit', 'Cost_Price_Unit', 'Market_Price_Unit', 
                    'Market_Value_Raw', 'Cost_Basis_Raw',  # Keep explicit cost basis
                    'Currency', 'Account', 'Insurance_CashValue_CNY'
                ]
                cols_present = [col for col in cols_to_keep if col in temp_h.columns]
                all_holdings.append(temp_h[cols_present].set_index(['Snapshot_Date', 'Asset_ID']))
            else:
                print("      - Warning: Schwab holdings missing Asset_ID. Skipping.")
        # --- **新增结束** ---
        
        # --- **新增**: g) RSU Holdings (calculated from transactions) ---
        # Note (2025-11-17): After Nov 4 migration, RSU no longer comes from balance sheet.
        # Calculate current RSU holdings from RSU_transactions.xlsx
        df_rsu_trans = self.cleaned_data.get('rsu_transactions')
        if df_rsu_trans is not None and not df_rsu_trans.empty:
            print("    - Processing RSU Holdings (calculated from transactions)...")
            # Calculate current shares for each RSU asset
            rsu_holdings_list = []
            
            # Group by Asset_ID (should be Employer_Stock_A or similar)
            if 'Asset_ID' in df_rsu_trans.columns and df_rsu_trans['Asset_ID'].notna().any():
                for asset_id in df_rsu_trans['Asset_ID'].unique():
                    if pd.isna(asset_id):
                        continue
                    
                    asset_trans = df_rsu_trans[df_rsu_trans['Asset_ID'] == asset_id].copy()
                    
                    # Calculate current quantity (Vest adds +, Sell subtracts -)
                    # Quantity should already have correct signs from sign conventions
                    current_qty = asset_trans['Quantity'].sum()
                    
                    if abs(current_qty) < 0.01:  # Skip if no current holdings
                        continue
                    
                    # Get asset name
                    asset_name = asset_trans['Asset_Name'].iloc[0] if 'Asset_Name' in asset_trans.columns else asset_id
                    
                    # Get latest price (try from monthly_df first, then from transactions)
                    latest_price_usd = None
                    if monthly_df is not None and 'Ref_Employer_Stock_Price_USD' in monthly_df.columns:
                        # Get price at latest_bs_date or closest before
                        price_series = monthly_df['Ref_Employer_Stock_Price_USD'].dropna()
                        if not price_series.empty:
                            dates_before = price_series.index[price_series.index <= latest_bs_date]
                            if len(dates_before) > 0:
                                latest_price_usd = price_series.loc[dates_before[-1]]
                    
                    # Fallback: use latest transaction price
                    if latest_price_usd is None or pd.isna(latest_price_usd):
                        if 'Price_Unit' in asset_trans.columns:
                            latest_price_usd = asset_trans['Price_Unit'].dropna().iloc[-1] if not asset_trans['Price_Unit'].dropna().empty else None
                    
                    if latest_price_usd is None or pd.isna(latest_price_usd):
                        print(f"      - Warning: No price found for {asset_id}, skipping RSU holdings")
                        continue
                    
                    # Create holdings entry
                    market_value_usd = current_qty * latest_price_usd
                    
                    rsu_holding = {
                        'Snapshot_Date': latest_bs_date,
                        'Asset_ID': asset_id,
                        'Asset_Name': asset_name,
                        'Asset_Type_Raw': 'RSU',
                        'Quantity': current_qty,
                        'Unit': 'Shares',
                        'Cost_Price_Unit': np.nan,  # Cost basis calculated later in cost_basis module
                        'Market_Price_Unit': latest_price_usd,
                        'Market_Value_Raw': market_value_usd,
                        'Currency': 'USD',
                        'Account': asset_trans['Account'].iloc[0] if 'Account' in asset_trans.columns else np.nan,
                        'Insurance_CashValue_CNY': np.nan
                    }
                    
                    rsu_holdings_list.append(rsu_holding)
                    print(f"      - Added {asset_id}: {current_qty:.2f} shares @ ${latest_price_usd:.2f} = ${market_value_usd:.2f}")
                
                # Add to all_holdings
                if rsu_holdings_list:
                    rsu_df = pd.DataFrame(rsu_holdings_list)
                    rsu_df['Snapshot_Date'] = pd.to_datetime(rsu_df['Snapshot_Date'])
                    all_holdings.append(rsu_df.set_index(['Snapshot_Date', 'Asset_ID']))
            else:
                print("      - Warning: RSU transactions missing Asset_ID column. Skipping RSU holdings calculation.")
        # --- **新增结束** ---


        # e) Concatenate all holdings and apply currency conversion
        if all_holdings:
            holdings_df = pd.concat(all_holdings)
            
            # 修复汇率应用的逻辑
            if self.fx_rates is not None and not self.fx_rates.empty:
                # 直接使用 latest_bs_date 对应或之前最近的汇率值，而不是尝试合并整个序列
                fx_rate_value = None
                # 尝试获取资产负债表日期的汇率
                if latest_bs_date in self.fx_rates.index:
                    fx_rate_value = self.fx_rates.loc[latest_bs_date]
                    if isinstance(fx_rate_value, pd.Series):
                        fx_rate_value = fx_rate_value.iloc[0]
                else:
                    # 如果没有精确匹配，找到小于等于资产负债表日期的最近汇率
                    earlier_dates = self.fx_rates.index[self.fx_rates.index <= latest_bs_date]
                    if not earlier_dates.empty:
                        latest_earlier_date = earlier_dates[-1]
                        fx_rate_value = self.fx_rates.loc[latest_earlier_date]
                        if isinstance(fx_rate_value, pd.Series):
                            fx_rate_value = fx_rate_value.iloc[0]
                    else:
                        # 如果没有早期日期，使用第一个可用汇率
                        fx_rate_value = self.fx_rates.iloc[0]
                        if isinstance(fx_rate_value, pd.Series):
                            fx_rate_value = fx_rate_value.iloc[0]
                
                # 检查汇率是否为有效数值（非零且非NaN）
                if pd.notna(fx_rate_value) and fx_rate_value > 0:
                    print(f"    - Applying USD/CNY FX rate {fx_rate_value} to USD assets")
                    
                    # 添加FX_Rate列到holdings_df以便于审核和调试
                    holdings_df['FX_Rate'] = fx_rate_value
                    
                    # 应用汇率转换
                    holdings_df['Market_Value_CNY'] = holdings_df.apply(
                        lambda row: row['Market_Value_Raw'] * fx_rate_value if row['Currency'] == 'USD' 
                                  else row['Market_Value_Raw'], 
                        axis=1
                    )
                    
                    # CRITICAL: Apply FX conversion to Cost Basis as well
                    if 'Cost_Basis_Raw' in holdings_df.columns:
                        holdings_df['Cost_Basis_CNY'] = holdings_df.apply(
                            lambda row: row['Cost_Basis_Raw'] * fx_rate_value if row['Currency'] == 'USD' and pd.notnull(row['Cost_Basis_Raw'])
                                      else (row['Cost_Basis_Raw'] if pd.notnull(row['Cost_Basis_Raw']) else np.nan),
                            axis=1
                        )
                else:
                    print(f"    - Warning: Invalid FX rate ({fx_rate_value}). USD assets will not be converted to CNY.")
                    holdings_df['FX_Rate'] = fx_rate_value
                    holdings_df['Market_Value_CNY'] = holdings_df['Market_Value_Raw'] # 使用USD原值（未转换）
                    if 'Cost_Basis_Raw' in holdings_df.columns:
                        holdings_df['Cost_Basis_CNY'] = holdings_df['Cost_Basis_Raw']
            else:
                # Fallback to default FX rate when no FX data available
                default_fx_rate = 7.0
                print(f"    - Warning: No FX rates available. Using fallback rate USD/CNY = {default_fx_rate}")
                holdings_df['FX_Rate'] = default_fx_rate
                
                # Apply fallback FX conversion for USD assets
                holdings_df['Market_Value_CNY'] = holdings_df.apply(
                    lambda row: row['Market_Value_Raw'] * default_fx_rate if row['Currency'] == 'USD' 
                              else row['Market_Value_Raw'], 
                    axis=1
                )
                
                # Also convert cost basis
                if 'Cost_Basis_Raw' in holdings_df.columns:
                    holdings_df['Cost_Basis_CNY'] = holdings_df.apply(
                        lambda row: row['Cost_Basis_Raw'] * default_fx_rate if row['Currency'] == 'USD' and pd.notnull(row['Cost_Basis_Raw'])
                                  else (row['Cost_Basis_Raw'] if pd.notnull(row['Cost_Basis_Raw']) else np.nan),
                        axis=1
                    )
            
            # 确保Market_Value_CNY是数值类型
            holdings_df['Market_Value_CNY'] = pd.to_numeric(holdings_df['Market_Value_CNY'], errors='coerce')
            
            # 最后处理并保存
            self.final_data['holdings_df'] = holdings_df.sort_index()
            print(f"  - Holdings data integrated. Total rows: {len(holdings_df)}")
            
            # 检查USD资产的转换是否成功
            usd_holdings = holdings_df[holdings_df['Currency'] == 'USD']
            if not usd_holdings.empty:
                print(f"    - Converted {len(usd_holdings)} USD holdings to CNY")
                for idx, row in usd_holdings.iterrows():
                    print(f"      - {idx[1]}: USD {row['Market_Value_Raw']:.2f} -> CNY {row['Market_Value_CNY']:.2f} (FX: {row['FX_Rate']})")
            
            # Add info about the snapshot date being used
            unique_dates = holdings_df.index.get_level_values('Snapshot_Date').unique()
            if len(unique_dates) == 1:
                print(f"  - All holdings using unified snapshot date: {unique_dates[0].strftime('%Y-%m-%d')}")
            else:
                print(f"  - Warning: Holdings still have {len(unique_dates)} different snapshot dates")
        else: 
            print("  - No holdings data found to integrate.")

        # --- 3. Create Consolidated Transactions DataFrame (`transactions_df`) ---
        print("  - Integrating Transactions...")
        all_transactions = []

        # Define all expected final columns for transactions_df
        all_final_trans_cols = [
            'Asset_ID', 'Asset_Name', 'Transaction_Type', 'Quantity', 'Unit',
            'Price_Unit', 'Amount_Gross', 'Commission_Fee', 'Amount_Net',
            'Currency', 'Account', 'Memo'
        ]

        # Function to prepare a transaction chunk for concatenation
        def prepare_trans_chunk(df_t, asset_type_default=None, default_unit=None):
            if df_t is None or df_t.empty:
                return None
            temp_t = df_t.copy()

            # Ensure date index exists or create from column
            if not isinstance(temp_t.index, pd.DatetimeIndex):
                if 'Transaction_Date' in temp_t.columns:
                    temp_t['Transaction_Date'] = pd.to_datetime(temp_t['Transaction_Date'], errors='coerce')
                    temp_t = temp_t.dropna(subset=['Transaction_Date'])
                    if temp_t.empty:
                        return None
                    temp_t = temp_t.set_index('Transaction_Date')
                else:
                    print("Warning: Transaction chunk missing date index/column. Skipping...")
                    return None  # Skip this chunk

            # Generate Asset_ID if missing
            if 'Asset_ID' not in temp_t.columns and 'Asset_Name' in temp_t.columns:
                 temp_t['Asset_ID'] = temp_t['Asset_Name'].apply(lambda x: generate_asset_id(x, asset_type=asset_type_default))
            elif 'Asset_ID' not in temp_t.columns:
                print("Warning: Transaction chunk missing Asset_ID and Asset_Name. Skipping...")
                return None

            # Standardize Transaction Type
            temp_t['Transaction_Type'] = temp_t.apply(standardize_transaction_type, axis=1)
            temp_t = temp_t.dropna(subset=['Transaction_Type'])  # Remove rows where type couldn't be standardized
            if temp_t.empty:
                return None

            # Ensure Unit column exists and has appropriate values
            if 'Unit' not in temp_t.columns and default_unit is not None:
                temp_t['Unit'] = default_unit
            elif 'Unit' not in temp_t.columns:
                temp_t['Unit'] = np.nan

            # Apply Sign Convention (ensure Quantity exists first)
            if 'Quantity' not in temp_t.columns:
                temp_t['Quantity'] = np.nan
            temp_t = apply_transaction_sign_convention(temp_t)

            # Ensure Currency column exists
            if 'Currency' not in temp_t.columns:
                 # Infer currency based on Asset ID, asset type, or assume CNY
                 if ('Asset_ID' in temp_t.columns and 
                     temp_t['Asset_ID'].astype(str).str.contains('RSU|USD', case=False, na=False).any()):
                      temp_t['Currency'] = 'USD'
                 elif asset_type_default == 'Schwab US Investment':  # Add this condition
                      temp_t['Currency'] = 'USD'
                 else:
                      temp_t['Currency'] = 'CNY'

            # Ensure all final columns exist, fill missing with default
            for col in all_final_trans_cols:
                if col not in temp_t.columns:
                    default_val = 0.0 if col in ['Quantity', 'Price_Unit', 'Amount_Gross', 'Commission_Fee', 'Amount_Net'] else None
                    temp_t[col] = default_val

            return temp_t[all_final_trans_cols]  # Select and order columns

        # Process each transaction source
        fund_chunk = prepare_trans_chunk(self.cleaned_data.get('fund_transactions'), asset_type_default='基金', default_unit='Shares')
        if fund_chunk is not None:
            all_transactions.append(fund_chunk)
            print("    - Processed Fund Transactions.")

        gold_chunk = prepare_trans_chunk(self.cleaned_data.get('gold_transactions'), asset_type_default='黄金', default_unit='Gram')
        if gold_chunk is not None:
            all_transactions.append(gold_chunk)
            print("    - Processed Gold Transactions.")

        # Rename insurance premium columns before preparing
        ins_p_df = self.cleaned_data.get('insurance_premiums_long')
        if ins_p_df is not None:
            ins_p_df = ins_p_df.rename(columns={'Asset_Name_Raw': 'Asset_Name'})  # Use standard name
            ins_chunk = prepare_trans_chunk(ins_p_df, asset_type_default='保险', default_unit=None)  # Already has type
            if ins_chunk is not None:
                all_transactions.append(ins_chunk)
                print("    - Processed Insurance Premiums.")

        rsu_chunk = prepare_trans_chunk(self.cleaned_data.get('rsu_transactions'), asset_type_default='RSU', default_unit='Shares')
        if rsu_chunk is not None:
            all_transactions.append(rsu_chunk)
            print("    - Processed RSU Transactions.")

        # --- **新增**: 处理 Schwab 交易 ---
        schwab_trans_chunk = prepare_trans_chunk(
            self.cleaned_data.get('schwab_transactions'),
            asset_type_default='Schwab US Investment',
            default_unit='Shares'
        )
        if schwab_trans_chunk is not None:
            all_transactions.append(schwab_trans_chunk)
            print("    - Processed Schwab Transactions.")
        # --- **新增结束** ---

        # Concatenate all valid transaction chunks
        if all_transactions:
            transactions_df = pd.concat(all_transactions)
            transactions_df = transactions_df.sort_index() # Sort by Transaction_Date index
            
            # --- Add Property Purchase Transaction (Manual/Synthetic) ---
            # Property_Residential_A was purchased in Aug 2020 for ¥2,820,000 (including ¥197,000 loan)
            # This adds a synthetic Buy transaction to enable proper XIRR calculation
            property_purchase_date = pd.to_datetime('2020-08-15')  # Mid-month estimate
            property_transaction = pd.DataFrame({
                'Asset_ID': ['Property_Residential_A'],
                'Asset_Name': ['Property_Residential_A'],
                'Asset_Type': ['住宅地产'],
                'Transaction_Type': ['Buy'],
                'Quantity': [1.0],
                'Unit': ['Unit'],
                'Price_Unit': [2820000.0],  # Total purchase price
                'Amount_Gross': [-2820000.0],  # Cash outflow (negative)
                'Commission_Fee': [0.0],
                'Amount_Net': [-2820000.0],  # Net cash outflow
                'Currency': ['CNY'],
                'Transaction_Type_Raw': ['Property_Purchase']
            }, index=[property_purchase_date])
            
            # Ensure property transaction has all required columns
            for col in transactions_df.columns:
                if col not in property_transaction.columns:
                    property_transaction[col] = None if transactions_df[col].dtype == 'object' else 0.0
            
            # Concatenate property transaction with other transactions
            transactions_df = pd.concat([transactions_df, property_transaction])
            transactions_df = transactions_df.sort_index()  # Re-sort after adding property
            print("    - Added Property_Residential_A synthetic purchase transaction (2020-08-15, ¥2,820,000)")
            # --- End Property Transaction Addition ---
            
            self.final_data['transactions_df'] = transactions_df
            print(f"  - Transactions data integrated. Total rows: {len(transactions_df)}")
        else:
            print("  - No valid transaction data found after processing.")
            self.final_data['transactions_df'] = pd.DataFrame()

    def _load_historical_data(self):
        """Load historical snapshots from storage if enabled."""
        if not self.settings.get('historical_data', {}).get('enable_snapshots', False):
            print("Historical snapshots disabled in configuration.")
            return
        
        print("\n--- Loading Historical Snapshots ---")
        self.historical_holdings_cache = self._load_all_historical_snapshots()
        
        if self.historical_holdings_cache is not None:
            snapshot_count = len(self.historical_holdings_cache.index.get_level_values(0).unique())
            print(f"Loaded {snapshot_count} historical snapshots into cache.")
        else:
            print("No historical snapshots found in storage.")

    # --- Accessor Methods ---
    def get_balance_sheet(self) -> Optional[pd.DataFrame]:
        """Returns the final, calculated Balance Sheet DataFrame."""
        return self.final_data.get('balance_sheet_df')

    def get_monthly_income_expense(self) -> Optional[pd.DataFrame]:
        """Returns the final, calculated Monthly Income/Expense DataFrame."""
        return self.final_data.get('monthly_df')

    def get_transactions(self) -> Optional[pd.DataFrame]:
        """
        Returns the final, integrated Transactions DataFrame.
        
        Routes to database or Excel based on configured mode.
        """
        print("DEBUG: get_transactions method called")
        
        if self.database_mode == 'database' and self.db_connector:
            return self.db_connector.get_transactions()
        else:
            return self.final_data.get('transactions_df')

    def get_holdings(self, latest_only: bool = True) -> Optional[pd.DataFrame]:
        """
        Enhanced method with backward compatibility for historical holdings data.
        
        Routes to database or Excel based on configured mode.
        
        Args:
            latest_only: If True (default), returns only latest snapshot
                        If False, returns all historical snapshots
        
        Returns:
            DataFrame with holdings data. Structure depends on latest_only parameter:
            - If latest_only=True: Single-level index with latest data
            - If latest_only=False: Multi-level index (Date, Asset_ID) with all historical data
        """
        if latest_only:
            return self._get_latest_holdings()

        if self.database_mode == 'database' and self.db_connector:
            return self.db_connector.get_holdings(latest_only=False)

        return self._get_all_historical_holdings()
    
    def _get_latest_holdings(self) -> Optional[pd.DataFrame]:
        """Returns the latest holdings DataFrame regardless of data source."""
        # When running in database mode, pull directly from the connector so
        # downstream modules (UnifiedDataPreparer, report builders, etc.) see
        # the same structure they expect from Excel mode.
        if self.database_mode == 'database' and self.db_connector:
            holdings_df = self.db_connector.get_holdings(latest_only=True)
        else:
            holdings_df = self.final_data.get('holdings_df')
        
        if holdings_df is None or holdings_df.empty:
            return holdings_df

        # Work on a copy so we can safely filter without mutating cached data
        holdings_df = holdings_df.copy()

        # Drop rows with missing index identifiers (e.g., NaN Asset_ID in MultiIndex)
        if isinstance(holdings_df.index, pd.MultiIndex) and 'Asset_ID' in holdings_df.index.names:
            invalid_index_mask = holdings_df.index.get_level_values('Asset_ID').isna()
            if invalid_index_mask.any():
                dropped = int(invalid_index_mask.sum())
                print(f"Warning: Dropping {dropped} holdings rows with missing Asset_ID in index")
                holdings_df = holdings_df[~invalid_index_mask]

        # Drop rows missing essential columns that would poison downstream sums
        if 'Asset_Name' in holdings_df.columns:
            missing_name_mask = holdings_df['Asset_Name'].isna()
            if missing_name_mask.any():
                dropped = int(missing_name_mask.sum())
                print(f"Warning: Dropping {dropped} holdings rows with missing Asset_Name")
                holdings_df = holdings_df[~missing_name_mask]

        if 'Market_Value_CNY' in holdings_df.columns:
            missing_value_mask = holdings_df['Market_Value_CNY'].isna()
            if missing_value_mask.any():
                dropped = int(missing_value_mask.sum())
                print(f"Warning: Dropping {dropped} holdings rows with missing Market_Value_CNY")
                holdings_df = holdings_df[~missing_value_mask]
        
        if holdings_df.empty:
            return holdings_df
        
        # Ensure taxonomy columns exist for consumers that require them
        if 'Asset_Class' not in holdings_df.columns:
            holdings_df = self._add_asset_classification(holdings_df)

        # Backward compatibility: some modules still expect Asset_Type_Raw/Asset_Sub_Class naming
        if 'Asset_Type_Raw' not in holdings_df.columns:
            source_col = None
            for candidate in ['Asset_Type', 'Asset_Type_Raw']:
                if candidate in holdings_df.columns:
                    source_col = candidate
                    break
            if source_col is not None:
                holdings_df['Asset_Type_Raw'] = holdings_df[source_col]
            else:
                holdings_df['Asset_Type_Raw'] = None

        if 'Asset_Sub_Class' not in holdings_df.columns and 'Asset_SubClass' in holdings_df.columns:
            holdings_df['Asset_Sub_Class'] = holdings_df['Asset_SubClass']
        elif 'Asset_Sub_Class' not in holdings_df.columns:
            holdings_df['Asset_Sub_Class'] = None
        
        return holdings_df
    
    def _add_asset_classification(self, holdings_df: pd.DataFrame) -> pd.DataFrame:
        """Add Asset_Class, Asset_SubClass, Asset_Type taxonomy columns using portfolio_lib."""
        try:
            from ..portfolio_lib.core.asset_mapper import (
                initialize_mapper_taxonomy,
                _map_asset_to_top_class_internal,
                _map_asset_to_sub_class_internal
            )
            import yaml
            
            # Initialize taxonomy (only once)
            if not hasattr(self, '_taxonomy_initialized'):
                taxonomy_path = self.config_path.replace('settings.yaml', 'asset_taxonomy.yaml')
                with open(taxonomy_path, 'r', encoding='utf-8') as f:
                    taxonomy = yaml.safe_load(f)
                initialize_mapper_taxonomy(taxonomy)
                self._taxonomy_initialized = True
            
            # Make a copy to avoid modifying original
            result_df = holdings_df.copy()
            
            # Map each asset to its classification
            asset_classes = []
            asset_subclasses = []
            
            # Get Asset_Name column (handle if it's in index or columns)
            if 'Asset_Name' in result_df.columns:
                asset_names = result_df['Asset_Name'].values
            elif result_df.index.name == 'Asset_Name':
                asset_names = result_df.index.values
            else:
                # Try to reset index to find Asset_Name
                temp_df = result_df.reset_index()
                if 'Asset_Name' in temp_df.columns:
                    asset_names = temp_df['Asset_Name'].values
                else:
                    print("Warning: Asset_Name column not found, cannot classify assets")
                    result_df['Asset_Class'] = 'Unknown'
                    result_df['Asset_SubClass'] = 'Unknown'
                    result_df['Asset_Type'] = result_df.get('Asset_Type_Raw', 'Unknown')
                    result_df['Risk_Level'] = None
                    return result_df
            
            for asset_name in asset_names:
                asset_class = _map_asset_to_top_class_internal(str(asset_name))
                asset_subclass = _map_asset_to_sub_class_internal(str(asset_name))
                
                asset_classes.append(asset_class if asset_class else None)
                asset_subclasses.append(asset_subclass if asset_subclass else None)
            
            # Add classification columns
            result_df['Asset_Class'] = asset_classes
            result_df['Asset_SubClass'] = asset_subclasses
            result_df['Asset_Type'] = result_df.get('Asset_Type_Raw', None)
            result_df['Risk_Level'] = None  # Risk level not provided by mapper yet
            
            return result_df
            
        except Exception as e:
            print(f"Warning: Could not add asset classification: {e}")
            import traceback
            traceback.print_exc()
            # Return original with empty classification columns
            result_df = holdings_df.copy()
            result_df['Asset_Class'] = None
            result_df['Asset_SubClass'] = None
            result_df['Asset_Type'] = result_df.get('Asset_Type_Raw', None)
            result_df['Risk_Level'] = None
            return result_df
    
    def _get_all_historical_holdings(self) -> Optional[pd.DataFrame]:
        """
        Returns all historical holdings snapshots, combining stored snapshots with current holdings.
        
        Returns:
            DataFrame with MultiIndex (Snapshot_Date, Asset_ID) containing historical holdings data.
            Returns None if no historical data is available.
        """
        all_snapshots = []
        
        # 1. Load stored historical snapshots from cache
        if self.historical_holdings_cache is not None:
            all_snapshots.append(self.historical_holdings_cache)
            print(f"Added {len(self.historical_holdings_cache.index.get_level_values(0).unique())} stored snapshots")
        
        # 2. Add current holdings as the latest snapshot
        current_holdings = self.final_data.get('holdings_df')
        if current_holdings is not None and not current_holdings.empty:
            # Get the latest balance sheet date as our snapshot date
            balance_sheet_df = self.final_data.get('balance_sheet_df')
            if balance_sheet_df is not None and not balance_sheet_df.empty:
                latest_date = balance_sheet_df.index.max()
                
                # Convert current holdings to historical format with MultiIndex
                current_snapshot = current_holdings.copy()
                
                # Reset index to make Asset_ID a column again if it's in the index
                if current_snapshot.index.name == 'Asset_ID' or 'Asset_ID' in current_snapshot.index.names:
                    current_snapshot = current_snapshot.reset_index()
                
                # Add snapshot date column
                current_snapshot['Snapshot_Date'] = latest_date
                
                # Create proper MultiIndex (Snapshot_Date, Asset_ID)
                current_snapshot = current_snapshot.set_index(['Snapshot_Date', 'Asset_ID'])
                
                # Only add if this date is not already in stored snapshots
                if (self.historical_holdings_cache is None or 
                    latest_date not in self.historical_holdings_cache.index.get_level_values(0)):
                    all_snapshots.append(current_snapshot)
                    print(f"Added current holdings as snapshot for date: {latest_date}")
                else:
                    print(f"Current holdings snapshot for {latest_date} already exists in stored data")
        
        if not all_snapshots:
            print("No historical holdings data available.")
            return None
        
        # 3. Combine all snapshots
        combined_holdings = pd.concat(all_snapshots, axis=0)
        combined_holdings = combined_holdings.sort_index()
        
        print(f"Combined historical holdings: {len(combined_holdings.index.get_level_values(0).unique())} snapshots, {len(combined_holdings)} total records")
        
        return combined_holdings
    
    def get_historical_holdings(self, 
                               start_date: Optional[pd.Timestamp] = None, 
                               end_date: Optional[pd.Timestamp] = None, 
                               frequency: str = 'monthly') -> Optional[pd.DataFrame]:
        """
        Returns historical holdings data within a specified date range.
        
        Args:
            start_date: Start date for filtering (inclusive). If None, uses earliest available.
            end_date: End date for filtering (inclusive). If None, uses latest available.
            frequency: Frequency for data points ('daily', 'weekly', 'monthly', 'quarterly')
        
        Returns:
            DataFrame with MultiIndex (Snapshot_Date, Asset_ID) containing filtered historical data.
        """
        # Get all historical holdings
        historical_holdings = self._get_all_historical_holdings()
        
        if historical_holdings is None:
            return None
        
        # Get available snapshot dates
        available_dates = historical_holdings.index.get_level_values(0).unique().sort_values()  # Use level 0 for Snapshot_Date
        
        # Apply date filtering
        if start_date is not None:
            available_dates = available_dates[available_dates >= start_date]
        
        if end_date is not None:
            available_dates = available_dates[available_dates <= end_date]
        
        if len(available_dates) == 0:
            print(f"No historical data available in date range {start_date} to {end_date}")
            return None
        
        # Filter historical holdings by selected dates
        filtered_holdings = historical_holdings.loc[available_dates]
        
        print(f"Historical holdings filtered: {len(available_dates)} snapshots, {len(filtered_holdings)} total records")
        
        return filtered_holdings
    
    def get_holdings_snapshots(self, dates_list: Optional[List[pd.Timestamp]] = None) -> Optional[pd.DataFrame]:
        """
        Returns holdings snapshots for specific dates.
        
        Args:
            dates_list: List of specific dates to retrieve. If None, returns all available snapshots.
        
        Returns:
            DataFrame with MultiIndex (Snapshot_Date, Asset_ID) for specified dates.
        """
        historical_holdings = self._get_all_historical_holdings()
        
        if historical_holdings is None:
            return None
        
        if dates_list is None:
            return historical_holdings
        
        # Convert dates to pandas Timestamps if needed
        dates_list = [pd.Timestamp(date) for date in dates_list]
        
        # Filter by specified dates
        available_dates = historical_holdings.index.get_level_values(0).unique()  # Use level 0 for Snapshot_Date
        valid_dates = [date for date in dates_list if date in available_dates]
        
        if not valid_dates:
            print("None of the requested dates are available in historical data.")
            print(f"Requested: {dates_list}")
            print(f"Available: {available_dates.tolist()}")
            return None
        
        filtered_holdings = historical_holdings.loc[valid_dates]
        
        print(f"Holdings snapshots retrieved for {len(valid_dates)} dates: {valid_dates}")
        
        return filtered_holdings
    
    def create_holdings_snapshot(self, snapshot_date: Optional[pd.Timestamp] = None) -> bool:
        """
        Creates a new holdings snapshot for the specified date and saves it to storage.
        
        Args:
            snapshot_date: Date for the snapshot. If None, uses the latest balance sheet date.
        
        Returns:
            True if snapshot was created successfully, False otherwise.
        """
        # Check if snapshots are enabled
        if not self.settings.get('historical_data', {}).get('enable_snapshots', False):
            print("Historical snapshots disabled in configuration.")
            return False
        
        current_holdings = self.final_data.get('holdings_df')
        if current_holdings is None or current_holdings.empty:
            print("No current holdings data available to create snapshot.")
            return False
        
        if snapshot_date is None:
            # Use latest balance sheet date
            balance_sheet_df = self.final_data.get('balance_sheet_df')
            if balance_sheet_df is None or balance_sheet_df.empty:
                print("No balance sheet data available to determine snapshot date.")
                return False
            snapshot_date = balance_sheet_df.index.max()
        
        # Convert snapshot_date to pandas Timestamp if needed
        snapshot_date = pd.Timestamp(snapshot_date)
        
        # Check if snapshot already exists
        existing_snapshots = self._get_all_historical_holdings()
        if (existing_snapshots is not None and 
            snapshot_date in existing_snapshots.index.get_level_values(0)):
            print(f"Snapshot for date {snapshot_date} already exists.")
            return False
        
        # Prepare holdings data for snapshot
        snapshot_holdings = current_holdings.copy()
        
        # Save snapshot to file
        success = self._save_snapshot_to_file(snapshot_holdings, snapshot_date)
        
        if success:
            # Refresh the cache to include the new snapshot
            self.historical_holdings_cache = self._load_all_historical_snapshots()
            print(f"Successfully created and saved snapshot for date: {snapshot_date}")
            print(f"Holdings records in snapshot: {len(snapshot_holdings)}")
        else:
            print(f"Failed to save snapshot for date: {snapshot_date}")
        
        return success
    
    def get_available_snapshot_dates(self) -> List[pd.Timestamp]:
        """
        Returns a list of available snapshot dates.
        
        Returns:
            List of Timestamp objects representing available snapshot dates.
        """
        historical_holdings = self._get_all_historical_holdings()
        
        if historical_holdings is None:
            print("No historical holdings data available.")
            return []
        
        available_dates = historical_holdings.index.get_level_values(0).unique().sort_values().tolist()  # Use level 0 for Snapshot_Date
        
        print(f"Available snapshot dates: {len(available_dates)} dates")
        for date in available_dates:
            print(f"  - {date.strftime('%Y-%m-%d')}")
        
        return available_dates

    # --- Historical Data Storage Helper Methods ---
    def _get_snapshots_directory(self) -> str:
        """Get the snapshots directory path from configuration."""
        base_dir = self.settings.get('historical_data', {}).get('snapshots_directory', 'data/historical_snapshots/')
        # Convert relative path to absolute path
        if not os.path.isabs(base_dir):
            # Get the project root directory (two levels up from src/data_manager)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            base_dir = os.path.join(project_root, base_dir)
        
        # Ensure directory exists
        os.makedirs(base_dir, exist_ok=True)
        return base_dir
    
    def _get_storage_format(self) -> str:
        """Get the storage format from configuration."""
        return self.settings.get('historical_data', {}).get('storage_format', 'excel')
    
    def _generate_snapshot_filename(self, snapshot_date: pd.Timestamp, storage_format: str) -> str:
        """Generate filename for a snapshot."""
        date_str = snapshot_date.strftime('%Y%m%d')
        
        if storage_format == 'excel':
            return f"holdings_snapshot_{date_str}.xlsx"
        elif storage_format == 'csv':
            return f"holdings_snapshot_{date_str}.csv"
        elif storage_format == 'parquet':
            return f"holdings_snapshot_{date_str}.parquet"
        else:
            return f"holdings_snapshot_{date_str}.xlsx"  # Default to Excel
    
    def _save_snapshot_to_file(self, holdings_df: pd.DataFrame, snapshot_date: pd.Timestamp) -> bool:
        """
        Save a holdings snapshot to file.
        
        Args:
            holdings_df: Holdings DataFrame to save
            snapshot_date: Date of the snapshot
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            storage_format = self._get_storage_format()
            snapshots_dir = self._get_snapshots_directory()
            filename = self._generate_snapshot_filename(snapshot_date, storage_format)
            filepath = os.path.join(snapshots_dir, filename)
            
            # Prepare data for saving (reset index to include Asset_ID as column)
            save_df = holdings_df.copy()
            if isinstance(save_df.index, pd.MultiIndex) and 'Asset_ID' in save_df.index.names:
                save_df = save_df.reset_index()
            elif save_df.index.name == 'Asset_ID':
                save_df = save_df.reset_index()
            
            # Add metadata columns
            save_df['Snapshot_Date'] = snapshot_date
            save_df['Created_At'] = pd.Timestamp.now()
            save_df['DataManager_Version'] = '1.2'
            
            # Save based on format
            if storage_format == 'excel':
                save_df.to_excel(filepath, index=False, sheet_name='Holdings_Snapshot')
            elif storage_format == 'csv':
                save_df.to_csv(filepath, index=False)
            elif storage_format == 'parquet':
                save_df.to_parquet(filepath, index=False)
            
            print(f"Snapshot saved successfully: {filepath}")
            return True
            
        except Exception as e:
            print(f"Error saving snapshot: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _load_snapshot_from_file(self, filepath: str) -> Optional[pd.DataFrame]:
        """
        Load a holdings snapshot from file.
        
        Args:
            filepath: Path to the snapshot file
            
        Returns:
            DataFrame with loaded snapshot data, or None if failed
        """
        try:
            if not os.path.exists(filepath):
                return None
            
            # Determine format from file extension
            if filepath.endswith('.xlsx'):
                df = pd.read_excel(filepath, sheet_name='Holdings_Snapshot')
            elif filepath.endswith('.csv'):
                df = pd.read_csv(filepath)
            elif filepath.endswith('.parquet'):
                df = pd.read_parquet(filepath)
            else:
                print(f"Unsupported file format: {filepath}")
                return None
            
            # Convert Snapshot_Date to datetime
            if 'Snapshot_Date' in df.columns:
                df['Snapshot_Date'] = pd.to_datetime(df['Snapshot_Date'])
            
            # Remove metadata columns that aren't part of holdings data
            metadata_cols = ['Created_At', 'DataManager_Version']
            df = df.drop(columns=[col for col in metadata_cols if col in df.columns])
            
            return df
            
        except Exception as e:
            print(f"Error loading snapshot from {filepath}: {e}")
            return None
    
    def _load_all_historical_snapshots(self) -> Optional[pd.DataFrame]:
        """
        Load all available historical snapshots from storage.
        
        Returns:
            DataFrame with MultiIndex (Snapshot_Date, Asset_ID) containing all historical data
        """
        snapshots_dir = self._get_snapshots_directory()
        storage_format = self._get_storage_format()
        
        # Find all snapshot files
        if storage_format == 'excel':
            pattern = 'holdings_snapshot_*.xlsx'
        elif storage_format == 'csv':
            pattern = 'holdings_snapshot_*.csv'
        elif storage_format == 'parquet':
            pattern = 'holdings_snapshot_*.parquet'
        else:
            pattern = 'holdings_snapshot_*.*'
        
        import glob
        snapshot_files = glob.glob(os.path.join(snapshots_dir, pattern))
        
        if not snapshot_files:
            print("No historical snapshot files found.")
            return None
        
        # Load all snapshots
        all_snapshots = []
        for filepath in sorted(snapshot_files):
            snapshot_df = self._load_snapshot_from_file(filepath)
            if snapshot_df is not None:
                all_snapshots.append(snapshot_df)
                print(f"Loaded snapshot: {os.path.basename(filepath)}")
        
        if not all_snapshots:
            return None
        
        # Combine all snapshots
        combined_df = pd.concat(all_snapshots, ignore_index=True)
        
        # Create MultiIndex (Snapshot_Date, Asset_ID)
        if 'Asset_ID' in combined_df.columns and 'Snapshot_Date' in combined_df.columns:
            combined_df = combined_df.set_index(['Snapshot_Date', 'Asset_ID'])
            combined_df = combined_df.sort_index()
        
        print(f"Loaded {len(all_snapshots)} historical snapshots with {len(combined_df)} total records")
        
        return combined_df
    
    def _cleanup_old_snapshots(self):
        """
        Clean up old snapshots based on retention period configuration.
        """
        if not self.settings.get('historical_data', {}).get('enable_snapshots', False):
            return
        
        try:
            retention_months = self.settings.get('historical_data', {}).get('retention_period_months', 36)
            cutoff_date = pd.Timestamp.now() - pd.DateOffset(months=retention_months)
            
            snapshots_dir = self._get_snapshots_directory()
            import glob
            snapshot_files = glob.glob(os.path.join(snapshots_dir, 'holdings_snapshot_*.*'))
            
            deleted_count = 0
            for filepath in snapshot_files:
                # Extract date from filename
                filename = os.path.basename(filepath)
                try:
                    date_str = filename.split('_')[2].split('.')[0]  # Extract YYYYMMDD
                    file_date = pd.to_datetime(date_str, format='%Y%m%d')
                    
                    if file_date < cutoff_date:
                        os.remove(filepath)
                        deleted_count += 1
                        print(f"Deleted old snapshot: {filename}")
                        
                except (ValueError, IndexError):
                    print(f"Could not parse date from filename: {filename}")
                    continue
            
            if deleted_count > 0:
                print(f"Cleaned up {deleted_count} old snapshots (older than {retention_months} months)")
            else:
                print("No old snapshots to clean up.")
            
        except Exception as e:
            print(f"Error during snapshot cleanup: {e}")

    # --- Transaction Management Methods (Database Mode Only) ---
    
    def get_transaction_by_id(self, transaction_id: int) -> Optional[dict]:
        """
        Fetch a single transaction by ID.
        Only available in database mode.
        """
        if self.database_mode != 'database' or not self.db_connector:
            raise ValueError("Transaction management requires database mode")
            
        return self.db_connector.get_transaction_by_id(transaction_id)
        
    def add_transaction(self, data: dict) -> int:
        """
        Add a new transaction.
        Only available in database mode.
        """
        if self.database_mode != 'database' or not self.db_connector:
            raise ValueError("Transaction management requires database mode")
            
        return self.db_connector.add_transaction(data)
        
    def update_transaction(self, transaction_id: int, data: dict) -> bool:
        """
        Update an existing transaction.
        Only available in database mode.
        """
        if self.database_mode != 'database' or not self.db_connector:
            raise ValueError("Transaction management requires database mode")
            
        return self.db_connector.update_transaction(transaction_id, data)
        
    def delete_transaction(self, transaction_id: int) -> bool:
        """
        Delete a transaction.
        Only available in database mode.
        """
        if self.database_mode != 'database' or not self.db_connector:
            raise ValueError("Transaction management requires database mode")
            
        return self.db_connector.delete_transaction(transaction_id)

