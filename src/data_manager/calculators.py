import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple

def get_fx_rates(monthly_df_clean: pd.DataFrame, fx_col_name: str = 'Ref_USD_FX_Rate') -> Optional[pd.Series]:
    """Extracts the FX rate series from the cleaned monthly DataFrame."""
    if monthly_df_clean is None or fx_col_name not in monthly_df_clean.columns:
        print(f"Warning: FX rate column '{fx_col_name}' not found in monthly_df. Cannot perform currency conversion.")
        return None
    # Forward fill to handle potential missing rates, then backfill start
    fx_rates = monthly_df_clean[fx_col_name].ffill().bfill()
    # Ensure the index is DatetimeIndex for proper alignment
    if not isinstance(fx_rates.index, pd.DatetimeIndex):
         print("Warning: FX rate Series index is not DatetimeIndex.")
         try:
             fx_rates.index = pd.to_datetime(fx_rates.index)
         except Exception as e:
             print(f"Error converting FX rate index to DatetimeIndex: {e}")
             return None
    return fx_rates

def convert_usd_to_cny(
    df: pd.DataFrame,
    usd_columns: List[str],
    fx_rates: pd.Series,
    base_currency: str = 'CNY'
) -> pd.DataFrame:
    """Converts specified USD columns to base currency (CNY) using FX rates."""
    df_converted = df.copy()
    if fx_rates is None:
        print("  - Skipping currency conversion due to missing FX rates.")
        return df_converted

    # Ensure DataFrame index is DatetimeIndex for alignment
    if not isinstance(df_converted.index, pd.DatetimeIndex):
         print("  - Warning: DataFrame index is not DatetimeIndex. Currency conversion might be inaccurate.")
         # Attempt conversion if index matches somehow, otherwise skip
         if len(df_converted) != len(fx_rates) or not df_converted.index.equals(fx_rates.index):
              print("  - Skipping currency conversion due to index mismatch.")
              return df_converted # Return original if index doesn't match

    # Align FX rates to DataFrame index (using month-end dates)
    # Reindex fx_rates to match the df index, forward filling missing values
    aligned_fx = fx_rates.reindex(df_converted.index, method='ffill').bfill()

    for col in usd_columns:
        if col in df_converted.columns:
            cny_col_name = col.replace('_USD', f'_{base_currency}') # Create corresponding CNY column name
            
            # CRITICAL FIX: Do NOT overwrite existing CNY columns (e.g., Asset_Bank_Account_A)
            # Only create the CNY column if it doesn't already exist
            if cny_col_name in df_converted.columns:
                # Column already exists (e.g., original RMB deposit), use a different name
                cny_col_name = col.replace('_USD', f'_{base_currency}_FromUSD')
                print(f"  - Converted '{col}' (USD) to '{cny_col_name}' ({base_currency}) [original {cny_col_name.replace('_FromUSD', '')} preserved].")
            else:
                print(f"  - Converted '{col}' (USD) to '{cny_col_name}' ({base_currency}).")
            
            df_converted[cny_col_name] = df_converted[col] * aligned_fx
        else:
             print(f"  - Warning: USD column '{col}' not found in DataFrame during conversion.")

    return df_converted

def calculate_balance_sheet_totals(
    bs_df_clean: pd.DataFrame,
    fx_rates: Optional[pd.Series]
) -> pd.DataFrame:
    """Calculates Total Assets, Liabilities, and Net Worth in CNY."""
    print("\nCalculating Balance Sheet totals (in CNY)...")
    if bs_df_clean is None: return None
    df = bs_df_clean.copy()

    asset_cols_cny = []
    liability_cols_cny = []
    asset_cols_usd = [col for col in df.columns if col.startswith('Asset_') and col.endswith('_USD')]
    liability_cols_usd = [col for col in df.columns if col.startswith('Liability_') and col.endswith('_USD')]

    # Perform currency conversion first
    if fx_rates is not None:
        df = convert_usd_to_cny(df, asset_cols_usd + liability_cols_usd, fx_rates)
    else:
        # If no FX rates, cannot calculate CNY totals accurately if USD columns exist
        if asset_cols_usd or liability_cols_usd:
             print("  - Warning: Cannot calculate accurate CNY totals without FX rates for USD columns.")
             # Add empty columns as placeholders
             df['Total_Assets_Calc_CNY'] = np.nan
             df['Total_Liabilities_Calc_CNY'] = np.nan
             df['Net_Worth_Calc_CNY'] = np.nan
             return df

    # Identify all CNY columns (original CNY + converted USD_CNY)
    # CRITICAL FIX: Exclude _USD, _CNY_FromUSD (duplicates), and prevent double counting
    added_stems = set()
    for col in df.columns:
        if col.startswith('Asset_') and not col.endswith('_USD') and not col.endswith('_FromUSD'):
            # Check for exact duplicates in columns list itself (e.g. Private_Equity_Investment_A appearing twice)
            if col in added_stems:
                continue
            asset_cols_cny.append(col)
            added_stems.add(col)
            
        elif col.startswith('Liability_') and not col.endswith('_USD') and not col.endswith('_FromUSD'):
             if col in added_stems:
                 continue
             liability_cols_cny.append(col)
             added_stems.add(col)

    print(f"  - Summing {len(asset_cols_cny)} CNY asset columns for Total Assets.")
    print(f"  - Summing {len(liability_cols_cny)} CNY liability columns for Total Liabilities.")

    # Calculate totals using only CNY columns
    df['Total_Assets_Calc_CNY'] = df[asset_cols_cny].sum(axis=1, skipna=True)
    df['Total_Liabilities_Calc_CNY'] = df[liability_cols_cny].sum(axis=1, skipna=True)
    df['Net_Worth_Calc_CNY'] = df['Total_Assets_Calc_CNY'] - df['Total_Liabilities_Calc_CNY']

    print("  - Balance Sheet total calculations complete.")
    return df

def calculate_monthly_totals(
    monthly_df_clean: pd.DataFrame,
    fx_rates: Optional[pd.Series]
) -> pd.DataFrame:
    """Calculates Total Income, Expense, and Net Cash Flow in CNY."""
    print("\nCalculating Monthly totals (in CNY)...")
    if monthly_df_clean is None: return None
    df = monthly_df_clean.copy()

    income_cols_cny = []
    expense_cols_cny = []
    investment_cols_cny = []
    income_cols_usd = [col for col in df.columns if col.startswith('Income_') and col.endswith('_USD')]
    # Assuming no USD expense/outflow columns based on schema, add if needed
    expense_outflow_cols_usd = []

     # Perform currency conversion first (only for income RSU for now)
    if fx_rates is not None:
        df = convert_usd_to_cny(df, income_cols_usd, fx_rates) # Only convert USD income cols
    else:
         if income_cols_usd:
             print("  - Warning: Cannot calculate accurate CNY income total without FX rates for RSU.")
             # Add empty columns as placeholders
             df['Total_Income_Calc_CNY'] = np.nan
             df['Total_Expense_Calc_CNY'] = np.nan # Expense likely okay if no USD expense
             df['Net_Cash_Flow_Calc_CNY'] = np.nan
             # Still calculate expense if possible
             for col in df.columns:
                 # Define which prefixes count towards expense/outflow
                 if col.startswith('Expense_') and not col.endswith('_USD'):
                     expense_cols_cny.append(col)
                 elif col.startswith('Outflow_') and not col.endswith('_USD'):
                     # Enhanced categorization: separate investment vs non-investment outflows
                     if (col.startswith('Outflow_Invest_') or 
                         any(keyword in col.lower() for keyword in ['invest', 'fund', 'stock', 'portfolio', 'wealth'])):
                         investment_cols_cny.append(col)
                     else:
                         expense_cols_cny.append(col)  # Non-investment outflows (insurance, loans, etc.)
             
             if expense_cols_cny:
                 df['Total_Expense_Calc_CNY'] = df[expense_cols_cny].sum(axis=1, skipna=True)
             if investment_cols_cny:
                 df['Total_Investment_Calc_CNY'] = df[investment_cols_cny].sum(axis=1, skipna=True)
             else:
                 df['Total_Investment_Calc_CNY'] = 0.0  # No investment data available
             return df


    # Identify all CNY columns for summing with enhanced categorization
    for col in df.columns:
        # Define which prefixes count towards income
        if col.startswith('Income_') and not col.endswith('_USD'): # Includes original CNY and converted RSU_CNY
            income_cols_cny.append(col)
        # Enhanced categorization: separate expenses from investments
        elif col.startswith('Expense_') and not col.endswith('_USD'):
            expense_cols_cny.append(col)
        elif col.startswith('Outflow_') and not col.endswith('_USD'):
            # Enhanced categorization: separate investment vs non-investment outflows
            if (col.startswith('Outflow_Invest_') or 
                any(keyword in col.lower() for keyword in ['invest', 'fund', 'stock', 'portfolio', 'wealth'])):
                investment_cols_cny.append(col)
            else:
                expense_cols_cny.append(col)  # Non-investment outflows (insurance, loans, etc.)

    print(f"  - Summing {len(income_cols_cny)} CNY income columns for Total Income.")
    print(f"  - Summing {len(expense_cols_cny)} CNY expense columns for Total Expense.")
    print(f"  - Summing {len(investment_cols_cny)} CNY investment columns for Total Investment.")

    # Calculate totals using enhanced categorization
    df['Total_Income_Calc_CNY'] = df[income_cols_cny].sum(axis=1, skipna=True)
    df['Total_Expense_Calc_CNY'] = df[expense_cols_cny].sum(axis=1, skipna=True)
    df['Total_Investment_Calc_CNY'] = df[investment_cols_cny].sum(axis=1, skipna=True)
    # Updated Net Cash Flow calculation to properly account for investments
    df['Net_Cash_Flow_Calc_CNY'] = df['Total_Income_Calc_CNY'] - df['Total_Expense_Calc_CNY'] - df['Total_Investment_Calc_CNY']

    print("  - Monthly total calculations complete.")
    return df