# portfolio_lib/data_loader/excel_loader.py
"""
Module for loading and performing initial cleaning of the main financial summary Excel file.
Reads data based on configuration provided in settings.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional

def _clean_dataframe(df: pd.DataFrame, sheet_name: str, debug: bool = False) -> pd.DataFrame:
    """
    Performs initial cleaning operations on a DataFrame loaded from Excel.

    Args:
        df: The raw DataFrame to clean.
        sheet_name: Name of the sheet for logging purposes.
        debug: If True, prints detailed cleaning steps.

    Returns:
        The cleaned DataFrame.
    """
    if df.empty:
        print(f"Warning: DataFrame for sheet '{sheet_name}' is empty, skipping cleaning.")
        return df

    if debug:
        print(f"\n--- Cleaning DataFrame: {sheet_name} ---")
        print(f"Initial shape: {df.shape}")

    # Create a copy to avoid SettingWithCopyWarning
    df_cleaned = df.copy()

    # 1. Clean column names: strip whitespace, replace spaces with underscores
    original_columns = df_cleaned.columns.tolist()
    df_cleaned.columns = [str(col).strip().replace(' ', '_') for col in df_cleaned.columns]
    new_columns = df_cleaned.columns.tolist()
    if debug and original_columns != new_columns:
        print(f"- Cleaned column names (Example: '{original_columns[1]}' -> '{new_columns[1]}')")

    # 2. Identify and set date index (assuming first column is date)
    date_col_name = df_cleaned.columns[0]
    if date_col_name:
        if debug: print(f"- Identified potential date column: '{date_col_name}'")
        # Convert to datetime, coercing errors (invalid dates become NaT)
        df_cleaned[date_col_name] = pd.to_datetime(df_cleaned[date_col_name], errors='coerce')

        # Remove rows where the date conversion failed (NaT)
        initial_rows = len(df_cleaned)
        df_cleaned = df_cleaned.dropna(subset=[date_col_name])
        rows_removed = initial_rows - len(df_cleaned)
        if rows_removed > 0 and debug:
            print(f"- Removed {rows_removed} rows with invalid date entries in '{date_col_name}'.")

        if not df_cleaned.empty:
             # Set the date column as the index
             df_cleaned = df_cleaned.set_index(date_col_name)
             if debug: print(f"- Set '{date_col_name}' as index.")
        else:
             print(f"Warning: No valid date entries found in column '{date_col_name}' for sheet '{sheet_name}'. Index not set.")
             return df_cleaned # Return early if no valid dates

    else:
        print(f"Warning: Could not identify the first column as a date column for sheet '{sheet_name}'. Index not set.")
        # Decide if you want to proceed without a date index or return/raise error

    # 3. Remove unnamed or empty columns
    unnamed_cols = [col for col in df_cleaned.columns if 'Unnamed:' in str(col) or str(col).strip() == '']
    if unnamed_cols:
        df_cleaned = df_cleaned.drop(columns=unnamed_cols)
        if debug: print(f"- Removed {len(unnamed_cols)} unnamed/empty columns.")

    # 4. Convert numeric columns (attempt conversion, keep non-numeric as is)
    numeric_cols_converted = 0
    for col in df_cleaned.columns:
        try:
            # Attempt conversion, coercing errors to NaN
            converted_col = pd.to_numeric(df_cleaned[col], errors='coerce')
            # Only replace if the original column wasn't already numeric or if conversion worked
            if not pd.api.types.is_numeric_dtype(df_cleaned[col]) or converted_col.notna().any():
                 # Check if conversion actually changed the type or values significantly
                 if not df_cleaned[col].equals(converted_col):
                      df_cleaned[col] = converted_col
                      numeric_cols_converted += 1
        except Exception as e:
            # Catch potential errors during conversion attempt
            if debug: print(f"  - Could not convert column '{col}' to numeric: {e}")
            pass # Keep original column type
    if debug and numeric_cols_converted > 0:
        print(f"- Attempted numeric conversion on columns ({numeric_cols_converted} potentially converted).")

    # 5. Handle potential duplicate monthly records (specifically for monthly sheet)
    #    Assumes index is DatetimeIndex
    if isinstance(df_cleaned.index, pd.DatetimeIndex) and sheet_name == 'monthly_income_expense': # Apply only to monthly sheet
        if debug: print("- Checking for duplicate monthly records...")
        # Create a year-month identifier
        df_cleaned['year_month'] = df_cleaned.index.to_period('M')

        # Check for months with more than one entry
        duplicate_months = df_cleaned['year_month'].value_counts()
        months_with_duplicates = duplicate_months[duplicate_months > 1].index.tolist()

        if months_with_duplicates:
            if debug: print(f"- Found {len(months_with_duplicates)} months with duplicate records. Consolidating...")
            consolidated_rows = []
            processed_months = set()

            for ym_period in df_cleaned['year_month'].unique():
                group = df_cleaned[df_cleaned['year_month'] == ym_period]
                if len(group) > 1:
                    # Consolidate duplicate rows for this month
                    consolidated_data = {}
                    for col in group.columns:
                        if col == 'year_month': continue # Skip helper column

                        # Select numeric columns for aggregation
                        if pd.api.types.is_numeric_dtype(group[col]):
                            # Get non-zero values
                            non_zero_values = group[col].dropna()[group[col] != 0]
                            if len(non_zero_values) == 0:
                                consolidated_data[col] = 0.0 # All zeros or NaN
                            elif len(non_zero_values) == 1:
                                consolidated_data[col] = non_zero_values.iloc[0] # Use the single non-zero value
                            else:
                                # If multiple non-zeros, take the maximum (as per original logic)
                                consolidated_data[col] = non_zero_values.max()
                                if debug: print(f"  - Consolidated '{col}' for {ym_period}: using max value {non_zero_values.max()}")
                        else:
                             # For non-numeric, keep the first non-null value if any
                             consolidated_data[col] = group[col].dropna().iloc[0] if not group[col].dropna().empty else None

                    # Use the first date index of the group for the consolidated row
                    consolidated_rows.append(pd.Series(consolidated_data, name=group.index[0]))
                    processed_months.add(ym_period)
                # else: # Keep single rows as they are (handled implicitly by not being in months_with_duplicates)
                #    pass

            # Get rows for months that had no duplicates
            single_month_rows = df_cleaned[~df_cleaned['year_month'].isin(processed_months)]

            # Combine consolidated rows and single rows
            df_cleaned = pd.concat([pd.DataFrame(consolidated_rows), single_month_rows.drop(columns=['year_month'])]).sort_index()
            if debug: print(f"- Consolidated duplicate months. New shape: {df_cleaned.shape}")
        else:
            # No duplicates found, just remove the helper column
            df_cleaned = df_cleaned.drop(columns=['year_month'])
            if debug: print("- No duplicate monthly records found.")

    if debug:
        print(f"Final cleaned shape: {df_cleaned.shape}")
        print(f"--- End Cleaning: {sheet_name} ---")

    return df_cleaned


def import_financial_data(settings: Dict[str, Any]) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Loads and cleans financial data (Balance Sheet, Monthly Income/Expense)
    from the main Excel file specified in the settings.

    Args:
        settings: The loaded configuration dictionary containing file paths and sheet names.

    Returns:
        A tuple containing two cleaned DataFrames: (balance_df, monthly_df).
        Returns (None, None) if loading fails.
    """
    print("\nSTEP 1: Importing Main Financial Data...")
    debug_mode = settings.get('general', {}).get('debug_mode', False)
    balance_df: Optional[pd.DataFrame] = None
    monthly_df: Optional[pd.DataFrame] = None

    # --- Get file path and sheet names from settings ---
    file_key = 'financial_summary'
    file_info = settings.get('data_files', {}).get(file_key)

    if not file_info or not isinstance(file_info, dict):
        print(f"Error: Configuration for '{file_key}' not found or invalid in settings.")
        return None, None

    file_path = file_info.get('path')
    balance_sheet_name = file_info.get('sheets', {}).get('balance_sheet')
    monthly_sheet_name = file_info.get('sheets', {}).get('monthly_income_expense')

    if not file_path:
        print(f"Error: File path for '{file_key}' not found in settings.")
        return None, None
    if not balance_sheet_name:
        print(f"Warning: Sheet name for 'balance_sheet' not found for '{file_key}' in settings.")
    if not monthly_sheet_name:
        print(f"Warning: Sheet name for 'monthly_income_expense' not found for '{file_key}' in settings.")

    print(f"Attempting to load from: {file_path}")

    # --- Load Balance Sheet ---
    if balance_sheet_name:
        try:
            print(f"Reading sheet: '{balance_sheet_name}'...")
            # Assuming header is on row 4 (index 3) as per original code
            # Consider making header row configurable in settings.yaml if it varies
            balance_df_raw = pd.read_excel(
                file_path,
                sheet_name=balance_sheet_name,
                header=3
            )
            print(f"Raw Balance Sheet loaded: {balance_df_raw.shape[0]} rows, {balance_df_raw.shape[1]} columns")
            balance_df = _clean_dataframe(balance_df_raw, 'balance_sheet', debug=debug_mode)
            if balance_df is not None and not balance_df.empty:
                 print(f"Cleaned Balance Sheet: {balance_df.shape[0]} rows, {balance_df.shape[1]} columns")
            else:
                 print("Warning: Balance sheet DataFrame is empty after cleaning.")
        except FileNotFoundError:
            print(f"Error: File not found at {file_path}")
            return None, None
        except ValueError as e: # Catches sheet not found error
            print(f"Error reading sheet '{balance_sheet_name}': {e}")
        except Exception as e:
            print(f"An unexpected error occurred loading '{balance_sheet_name}': {e}")

    # --- Load Monthly Income/Expense ---
    if monthly_sheet_name:
        try:
            print(f"Reading sheet: '{monthly_sheet_name}'...")
            # Assuming header is on row 4 (index 3)
            monthly_df_raw = pd.read_excel(
                file_path,
                sheet_name=monthly_sheet_name,
                header=3
            )
            print(f"Raw Monthly Data loaded: {monthly_df_raw.shape[0]} rows, {monthly_df_raw.shape[1]} columns")
            monthly_df = _clean_dataframe(monthly_df_raw, 'monthly_income_expense', debug=debug_mode)
            if monthly_df is not None and not monthly_df.empty:
                 print(f"Cleaned Monthly Data: {monthly_df.shape[0]} rows, {monthly_df.shape[1]} columns")
            else:
                 print("Warning: Monthly data DataFrame is empty after cleaning.")
        except FileNotFoundError: # Should be caught above, but good practice
            print(f"Error: File not found at {file_path}")
            return balance_df, None # Return balance_df if it loaded successfully
        except ValueError as e: # Catches sheet not found error
            print(f"Error reading sheet '{monthly_sheet_name}': {e}")
        except Exception as e:
            print(f"An unexpected error occurred loading '{monthly_sheet_name}': {e}")


    if balance_df is None and monthly_df is None:
        print("Failed to load any data from the financial summary file.")
        return None, None
    elif balance_df is None:
        print("Warning: Failed to load or clean balance sheet data.")
    elif monthly_df is None:
         print("Warning: Failed to load or clean monthly income/expense data.")


    print("Finished importing main financial data.")
    return balance_df, monthly_df
