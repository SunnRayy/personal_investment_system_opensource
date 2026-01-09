import pandas as pd
import numpy as np
import logging
import yaml # <-- Import YAML library
import os
from collections import defaultdict

# Configure logging for this module
logger = logging.getLogger(__name__)

# --- Helper function to load asset taxonomy (unchanged) ---
def _load_asset_taxonomy(config_dir: str) -> dict:
    """
    Loads asset taxonomy configuration from the YAML file.
    (Code remains the same as previous version)
    """
    taxonomy_path = os.path.join(config_dir, 'asset_taxonomy.yaml')
    logger.info(f"Attempting to load asset taxonomy from: {taxonomy_path}")
    if not os.path.exists(taxonomy_path):
        logger.error(f"Asset taxonomy file not found at: {taxonomy_path}")
        return {}

    try:
        with open(taxonomy_path, 'r', encoding='utf-8') as f:
            taxonomy_data = yaml.safe_load(f)
        logger.info("Asset taxonomy loaded successfully.")

        # Basic validation (check if key sections exist)
        required_keys = ['top_level_classes', 'sub_classes', 'asset_mapping', 'special_categories']
        if not all(key in taxonomy_data for key in required_keys):
             logger.warning(f"Asset taxonomy YAML seems incomplete. Missing one of: {required_keys}")
             # Continue anyway, but analysis might fail later

        # Build the sub_to_top_level mapping dynamically
        sub_to_top_level = {}
        if 'sub_classes' in taxonomy_data and isinstance(taxonomy_data['sub_classes'], dict):
             for top_level, sub_list in taxonomy_data['sub_classes'].items():
                  if isinstance(sub_list, list):
                       for sub_class in sub_list:
                            sub_to_top_level[sub_class] = top_level
        taxonomy_data['_sub_to_top_level'] = sub_to_top_level # Store mapping for internal use

        return taxonomy_data
    except yaml.YAMLError as e:
        logger.error(f"Error parsing asset taxonomy YAML file: {e}", exc_info=True)
        return {}
    except Exception as e:
        logger.error(f"Error loading asset taxonomy file: {e}", exc_info=True)
        return {}


# --- analyze_balance_sheet_trends function (unchanged) ---
def analyze_balance_sheet_trends(balance_sheet_df: pd.DataFrame) -> dict:
    """
    Analyzes trends in Total Assets, Liabilities, and Net Worth using standardized columns.
    (Code remains the same as previous version)
    """
    logger.info("Analyzing balance sheet trends (Assets, Liabilities, Net Worth)...")

    # Define the columns expected from DataManager for this analysis
    required_cols = ['Total_Assets_Calc_CNY', 'Total_Liabilities_Calc_CNY', 'Net_Worth_Calc_CNY']

    # Input validation
    if balance_sheet_df is None or balance_sheet_df.empty:
        logger.warning("Input balance_sheet_df is None or empty. Skipping trend analysis.")
        return {}
    if not all(col in balance_sheet_df.columns for col in required_cols):
        logger.warning(f"Input DataFrame is missing one or more required trend columns: {required_cols}. Found: {balance_sheet_df.columns.tolist()}. Skipping trend analysis.")
        return {}
    if not isinstance(balance_sheet_df.index, pd.DatetimeIndex):
         logger.warning("Input DataFrame index is not a DatetimeIndex. Skipping trend analysis.")
         return {}

    # Ensure dataframe is sorted by date (important for start/end values)
    df = balance_sheet_df.sort_index()

    # Select only the necessary columns for trend analysis
    trend_df = df[required_cols].copy()

    # Handle potential NaN values that might have slipped through DataManager
    # Or if calculations resulted in NaN (e.g., initial data points missing)
    trend_df.fillna(0, inplace=True)

    # Need at least two data points for trend calculation
    if len(trend_df) < 2:
        logger.warning(f"Insufficient data points ({len(trend_df)} < 2) for trend analysis.")
        # Return the limited data, but no growth metrics
        return {'trend_data': trend_df}

    # Get start and end data points
    start_date = trend_df.index.min()
    end_date = trend_df.index.max()
    start_row_slice = trend_df.loc[start_date]
    end_row_slice = trend_df.loc[end_date]

    # Handle potential duplicate index for start/end row selection
    start_row = start_row_slice.iloc[-1] if isinstance(start_row_slice, pd.DataFrame) else start_row_slice
    end_row = end_row_slice.iloc[-1] if isinstance(end_row_slice, pd.DataFrame) else end_row_slice

    # Log if duplicates were handled
    if isinstance(start_row_slice, pd.DataFrame):
        logger.warning(f"Duplicate index found for start_date {start_date}. Using the last entry.")
    if isinstance(end_row_slice, pd.DataFrame):
        logger.warning(f"Duplicate index found for end_date {end_date}. Using the last entry.")

    # Ensure start_row and end_row are Series before accessing values
    if not isinstance(start_row, pd.Series) or not isinstance(end_row, pd.Series):
        logger.error(f"Failed to extract start/end rows as Series. Types: {type(start_row)}, {type(end_row)}")
        return {'trend_data': trend_df} # Return partial data

    start_assets = start_row.get('Total_Assets_Calc_CNY', 0)
    end_assets = end_row.get('Total_Assets_Calc_CNY', 0)
    start_liabilities = start_row.get('Total_Liabilities_Calc_CNY', 0)
    end_liabilities = end_row.get('Total_Liabilities_Calc_CNY', 0)
    start_net_worth = start_row.get('Net_Worth_Calc_CNY', 0)
    end_net_worth = end_row.get('Net_Worth_Calc_CNY', 0)


    # Initialize results dictionary
    results = {
        'start_date': start_date,
        'end_date': end_date,
        'start_assets': start_assets,
        'end_assets': end_assets,
        'start_liabilities': start_liabilities,
        'end_liabilities': end_liabilities,
        'start_net_worth': start_net_worth,
        'end_net_worth': end_net_worth,
        'trend_data': trend_df # Include the trend data itself for plotting later
    }

    # Calculate growth metrics only if start_net_worth is valid and non-zero
    if pd.notna(start_net_worth) and start_net_worth != 0:
        # Calculate number of months between start and end dates using pandas Period
        if start_date == end_date:
            total_months = 0 # No time passed for growth calculation
        else:
            # Calculate number of monthly periods between the dates
            # .n gives the integer difference
            total_months = (pd.Timestamp(end_date).to_period('M') - pd.Timestamp(start_date).to_period('M')).n

        # Store the calculated number of months
        results['total_months'] = total_months

        # Calculate absolute total growth
        total_growth = end_net_worth - start_net_worth
        # Calculate overall percentage growth
        total_growth_pct = (end_net_worth / start_net_worth - 1) * 100

        # Calculate compounded monthly growth rate
        # Formula: (End Value / Start Value)^(1 / Number of Periods) - 1
        monthly_growth_rate = np.nan
        # Ensure we have time passage and avoid division by zero
        if total_months > 0:
             # Ensure base is non-negative for fractional power calculation
             # Check if start_net_worth is positive before division
             if start_net_worth > 0:
                 base = end_net_worth / start_net_worth
                 if base >= 0:
                      monthly_growth_rate = (base ** (1 / total_months)) - 1
                 else:
                      # Handle cases where net worth crosses zero
                      logger.warning(f"Net worth crossed zero between {start_date} and {end_date}. Compounded growth rate is less meaningful.")
                      monthly_growth_rate = np.nan
             elif end_net_worth > 0: # Started negative/zero, ended positive
                  logger.warning(f"Net worth started at or below zero and ended positive ({start_net_worth} -> {end_net_worth}). Cannot calculate meaningful geometric growth rate.")
                  monthly_growth_rate = np.nan
             # else: started negative/zero, ended negative/zero -> growth rate is NaN or 0

        monthly_growth_pct = monthly_growth_rate * 100 if pd.notna(monthly_growth_rate) else np.nan

        # Calculate compounded annualized growth rate
        # Formula: (1 + Monthly Rate)^12 - 1
        annualized_growth_rate = ((1 + monthly_growth_rate) ** 12 - 1) if pd.notna(monthly_growth_rate) else np.nan
        annualized_growth_pct = annualized_growth_rate * 100 if pd.notna(annualized_growth_rate) else np.nan

        # Update results dictionary with calculated growth metrics
        results.update({
            'net_worth_growth_total': total_growth,
            'net_worth_growth_pct': total_growth_pct,
            'net_worth_monthly_growth_pct': monthly_growth_pct,
            'net_worth_annualized_growth_pct': annualized_growth_pct
        })
        # Log the calculated annualized growth if valid
        if pd.notna(annualized_growth_pct):
            logger.info(f"Net worth growth calculated: Annualized {annualized_growth_pct:.2f}% over {total_months} months.")
        else:
             logger.info(f"Net worth growth calculated but rates are NaN (likely due to zero crossing or insufficient time). Total growth: {total_growth:.2f}")

    else:
        # Handle cases where start_net_worth is NaN or zero
        logger.warning("Could not calculate net worth growth rates due to invalid or zero starting net worth.")
        results.update({
            'total_months': 0, # Set months to 0 if no growth calculable
            'net_worth_growth_total': None,
            'net_worth_growth_pct': None,
            'net_worth_monthly_growth_pct': None,
            'net_worth_annualized_growth_pct': None
        })

    # Return the dictionary containing all results
    return results


# --- analyze_asset_liability_allocation function (unchanged) ---
def analyze_asset_liability_allocation(balance_sheet_df: pd.DataFrame, taxonomy_data: dict) -> dict:
    """
    Analyzes the allocation of assets and liabilities based on the latest balance sheet data,
    using categories defined in the loaded asset taxonomy data.
    (Code remains the same as previous version)
    """
    logger.info("Analyzing latest asset and liability allocation using loaded taxonomy...")

    if balance_sheet_df is None or balance_sheet_df.empty:
        logger.warning("Input DataFrame is empty. Skipping allocation analysis.")
        return {}
    if not taxonomy_data or '_sub_to_top_level' not in taxonomy_data:
         logger.error("Asset taxonomy data is missing or invalid. Skipping allocation analysis.")
         return {}

    # Extract taxonomy components
    asset_mapping = taxonomy_data.get('asset_mapping', {})
    sub_to_top_level = taxonomy_data.get('_sub_to_top_level', {})
    special_categories = set(taxonomy_data.get('special_categories', []))

    # Get the latest data row - Ensure it's a Series
    latest_date = balance_sheet_df.index.max()
    latest_data_slice = balance_sheet_df.loc[latest_date]
    if isinstance(latest_data_slice, pd.DataFrame):
        logger.warning(f"Duplicate index found for latest_date {latest_date}. Using the last available entry.")
        latest_data = latest_data_slice.iloc[-1] # Get last row as Series
    elif isinstance(latest_data_slice, pd.Series):
        latest_data = latest_data_slice
    else:
        logger.error(f"Could not extract latest data for date {latest_date}. Type received: {type(latest_data_slice)}")
        return {} # Cannot proceed

    logger.debug(f"Columns available in latest_data (index): {latest_data.index.tolist()}")

    total_assets = latest_data.get('Total_Assets_Calc_CNY', 0)
    total_liabilities = latest_data.get('Total_Liabilities_Calc_CNY', 0)

    # Initialize dictionaries
    asset_allocation_values = defaultdict(float)
    liability_allocation_values = defaultdict(float)

    # --- Asset Categorization using Mapping ---
    logger.debug("Categorizing assets based on loaded mapping:")
    processed_asset_cols = set()
    if isinstance(asset_mapping, dict):
        for col, sub_class in asset_mapping.items():
            if col in latest_data.index: # Check if column from mapping exists in the Series
                value_to_add = latest_data.get(col) # Retrieve the single value
                # **REFINED CHECK**: Ensure it's a number AND not NaN AND not zero
                if isinstance(value_to_add, (int, float, np.number)) and pd.notna(value_to_add) and value_to_add != 0:
                    top_level_class = sub_to_top_level.get(sub_class)
                    if top_level_class and top_level_class not in special_categories:
                        asset_allocation_values[top_level_class] += value_to_add
                        logger.debug(f" - Mapped '{col}' ({value_to_add:.2f}) to Top-Level '{top_level_class}'")
                    elif top_level_class in special_categories:
                        logger.debug(f" - Skipping '{col}': Belongs to special category '{top_level_class}'")
                    else:
                        logger.warning(f" - Column '{col}' mapped to sub-class '{sub_class}', but no top-level class found.")
                        asset_allocation_values['其他资产_未分类子类'] += value_to_add
                elif not isinstance(value_to_add, (int, float, np.number)):
                     # FIX HERE: Explicitly check for Series before using pd.notna
                     if isinstance(value_to_add, pd.Series):
                         if value_to_add.notna().any():  # Use Series.notna() method
                             logger.error(f" - Column '{col}' has Series type with values: {value_to_add}. Cannot add to allocation sum.")
                     elif pd.notna(value_to_add):  # Only use pd.notna on non-Series values
                          logger.error(f" - Column '{col}' has unexpected non-numeric type {type(value_to_add)}. Value: {value_to_add}. Cannot add to allocation sum.")
                # Mark as processed regardless of value (0, NaN, or error)
                processed_asset_cols.add(col)
            # else: column from mapping not found in data - will be logged later

    # Log columns from mapping that weren't found in the data
    for col in asset_mapping.keys():
        if col not in latest_data.index:
            logger.debug(f" - Column '{col}' from asset_mapping not found in latest balance sheet data.")


    # --- Handle Unmapped Assets ---
    logger.debug("Checking for unmapped asset columns:")
    for col in latest_data.index:
        if col.startswith('Asset_') and col not in processed_asset_cols and 'Total' not in col and 'Calc' not in col:
            value_to_add = latest_data.get(col)
            # **REFINED CHECK**: Ensure it's a number AND not NaN AND not zero
            if isinstance(value_to_add, (int, float, np.number)) and pd.notna(value_to_add) and value_to_add != 0:
                logger.warning(f" - Unmapped asset column found: '{col}' with value {value_to_add:.2f}. Adding to '其他资产_未映射'. Consider adding it to asset_mapping in YAML.")
                asset_allocation_values['其他资产_未映射'] += value_to_add
            elif not isinstance(value_to_add, (int, float, np.number)):
                 # FIX HERE: Explicitly check for Series before using pd.notna
                 if isinstance(value_to_add, pd.Series):
                     if value_to_add.notna().any():  # Use Series.notna() method
                         logger.error(f" - Unmapped Column '{col}' has Series type with values: {value_to_add}. Cannot add to allocation sum.")
                 elif pd.notna(value_to_add):  # Only use pd.notna on non-Series values
                      logger.error(f" - Unmapped Column '{col}' has unexpected non-numeric type {type(value_to_add)}. Value: {value_to_add}. Cannot add to allocation sum.")


    # --- Liability Categorization (Simplified Prefix-based) ---
    logger.debug("Categorizing liabilities based on prefixes:")
    for col in latest_data.index:
        value_to_add = latest_data.get(col)
        # **REFINED CHECK**: Ensure it's a number AND not NaN AND not zero
        if isinstance(value_to_add, (int, float, np.number)) and pd.notna(value_to_add) and value_to_add != 0:
             if col.startswith('Liability_ShortTerm_') or col.startswith('Liability_CC_'): # <-- Include CC prefix
                 liability_allocation_values['短期负债'] += value_to_add
                 logger.debug(f" - Mapped '{col}' ({value_to_add:.2f}) to '短期负债'")
             elif col.startswith('Liability_LongTerm_'):
                  liability_allocation_values['长期负债'] += value_to_add
                  logger.debug(f" - Mapped '{col}' ({value_to_add:.2f}) to '长期负债'")
             elif col.startswith('Liability_') and 'Total' not in col and 'Calc' not in col:
                  liability_allocation_values['其他负债'] += value_to_add
                  logger.debug(f" - Mapped '{col}' ({value_to_add:.2f}) to '其他负债'")
        elif not isinstance(value_to_add, (int, float, np.number)):
             # FIX HERE: Explicitly check for Series before using pd.notna
             if isinstance(value_to_add, pd.Series):
                 if value_to_add.notna().any() and (value_to_add != 0).any():  # Use Series methods
                     logger.error(f" - Liability Column '{col}' has Series type with values: {value_to_add}. Cannot add to allocation sum.")
             elif pd.notna(value_to_add) and value_to_add != 0:  # For scalar values
                  logger.error(f" - Liability Column '{col}' has unexpected non-numeric type {type(value_to_add)}. Value: {value_to_add}. Cannot add to allocation sum.")


    # --- Final Results Calculation ---
    # The values in asset_allocation_values and liability_allocation_values
    # should now be guaranteed floats due to defaultdict(float) and the checks above.
    # The previous loops iterating over these dicts should be safe now.
    final_asset_allocation = {}
    valid_total_assets = total_assets if total_assets != 0 else 1
    logger.debug("--- Calculating Final Asset Allocation ---")
    for category, value in asset_allocation_values.items():
        logger.debug(f"Final Processing Asset Category: '{category}', Value: {value}, Type: {type(value)}")
        # FIX HERE: Check for Series type before using pd.notna
        if isinstance(value, pd.Series):
            if value.notna().any() and (value != 0).any():
                processed_value = value.sum() if len(value) > 1 else value.iloc[0]
                percentage = (processed_value / valid_total_assets) * 100
                final_asset_allocation[category] = {'value': processed_value, 'percentage': percentage}
                logger.debug(f"Processed Series value for category '{category}': {processed_value}")
        elif pd.notna(value) and value != 0:  # For scalar values
            percentage = (value / valid_total_assets) * 100
            final_asset_allocation[category] = {'value': value, 'percentage': percentage}
        else:
             logger.debug(f"Skipping final asset category '{category}' due to zero or NaN value.")


    final_liability_allocation = {}
    valid_total_liabilities = total_liabilities if total_liabilities != 0 else 1
    logger.debug("--- Calculating Final Liability Allocation ---")
    for category, value in liability_allocation_values.items():
        logger.debug(f"Final Processing Liability Category: '{category}', Value: {value}, Type: {type(value)}")
        # FIX HERE: Check for Series type before using pd.notna
        if isinstance(value, pd.Series):
            if value.notna().any() and (value != 0).any():
                processed_value = value.sum() if len(value) > 1 else value.iloc[0]
                percentage = (processed_value / valid_total_liabilities) * 100
                final_liability_allocation[category] = {'value': processed_value, 'percentage': percentage}
                logger.debug(f"Processed Series value for category '{category}': {processed_value}")
        elif pd.notna(value) and value != 0:  # For scalar values
            percentage = (value / valid_total_liabilities) * 100
            final_liability_allocation[category] = {'value': value, 'percentage': percentage}
        else:
             logger.debug(f"Skipping final liability category '{category}' due to zero or NaN value.")


    # Construct the final results dictionary
    allocation_results = {
        'latest_date': latest_date,
        'total_assets': total_assets,
        'total_liabilities': total_liabilities,
        'asset_allocation': final_asset_allocation,
        'liability_allocation': final_liability_allocation
    }

    logger.info("Asset and liability allocation analysis complete.")
    return allocation_results


# --- analyze_asset_category_growth function (unchanged) ---
def analyze_asset_category_growth(balance_sheet_df: pd.DataFrame, taxonomy_data: dict) -> pd.DataFrame:
    """
    Calculates the historical value of each top-level asset category over time.
    (Code remains the same as previous version)
    """
    logger.info("Analyzing asset category growth over time...")

    if balance_sheet_df is None or balance_sheet_df.empty:
        logger.warning("Input DataFrame is empty. Skipping category growth analysis.")
        return pd.DataFrame()
    if not taxonomy_data or '_sub_to_top_level' not in taxonomy_data:
         logger.error("Asset taxonomy data is missing or invalid. Skipping category growth analysis.")
         return pd.DataFrame()

    # Extract taxonomy components
    asset_mapping = taxonomy_data.get('asset_mapping', {})
    sub_to_top_level = taxonomy_data.get('_sub_to_top_level', {})
    special_categories = set(taxonomy_data.get('special_categories', []))
    top_level_classes = taxonomy_data.get('top_level_classes', []) # Get defined top-level classes

    # Initialize a DataFrame to store results, using the original index
    category_growth_df = pd.DataFrame(index=balance_sheet_df.index)

    # Create a mapping from column name directly to top-level class
    col_to_top_level = {}
    unmapped_cols = []
    other_category_cols = []

    if isinstance(asset_mapping, dict):
        for col in balance_sheet_df.columns:
            if col.startswith('Asset_') and 'Total' not in col and 'Calc' not in col:
                sub_class = asset_mapping.get(col)
                if sub_class:
                    top_level = sub_to_top_level.get(sub_class)
                    if top_level and top_level not in special_categories:
                        col_to_top_level[col] = top_level
                    elif top_level and top_level in special_categories:
                         logger.debug(f"Column '{col}' belongs to special category '{top_level}', excluding from growth analysis.")
                    else:
                         logger.warning(f"Column '{col}' mapped to sub-class '{sub_class}' but no top-level class found. Assigning to '其他资产'.")
                         col_to_top_level[col] = '其他资产' # Assign to a generic 'Other'
                         other_category_cols.append(col)
                else:
                    # Column exists in data but not in asset_mapping
                    logger.warning(f"Column '{col}' not found in asset_mapping. Assigning to '其他资产'.")
                    col_to_top_level[col] = '其他资产' # Assign unmapped to 'Other'
                    unmapped_cols.append(col)
                    other_category_cols.append(col)

    # Group columns by their assigned top-level category
    top_level_to_cols = defaultdict(list)
    for col, top_level in col_to_top_level.items():
        top_level_to_cols[top_level].append(col)

    # Calculate sum for each top-level category over time
    for top_level, cols_in_category in top_level_to_cols.items():
        if cols_in_category: # Ensure there are columns in this category
            # Sum the values of all columns belonging to this top-level category for each date
            # Fill NaN with 0 before summing to avoid propagation of NaNs
            category_growth_df[top_level] = balance_sheet_df[cols_in_category].fillna(0).sum(axis=1)

    # Ensure all defined top-level classes (excluding special) exist as columns, add if missing (with 0s)
    defined_top_levels = [cls for cls in top_level_classes if cls not in special_categories]
    for cls in defined_top_levels:
         if cls not in category_growth_df.columns:
              logger.debug(f"Adding missing defined top-level class '{cls}' to growth DataFrame with zeros.")
              category_growth_df[cls] = 0.0
    # Also add '其他资产' if it was generated
    if '其他资产' not in category_growth_df.columns and other_category_cols:
         logger.debug("Adding '其他资产' column to growth DataFrame with zeros as it was generated but might be empty.")
         category_growth_df['其他资产'] = 0.0


    # Reorder columns based on defined top_level_classes + '其他资产' if exists
    final_columns_order = defined_top_levels
    if '其他资产' in category_growth_df.columns:
         final_columns_order.append('其他资产')
    # Filter to only include columns that actually exist in the DataFrame
    final_columns_order = [col for col in final_columns_order if col in category_growth_df.columns]

    category_growth_df = category_growth_df[final_columns_order]


    logger.info("Asset category growth analysis complete.")
    return category_growth_df

# --- NEW: calculate_balance_sheet_ratios function ---
def calculate_balance_sheet_ratios(balance_sheet_df: pd.DataFrame, category_growth_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates key financial ratios based on balance sheet data over time.

    Args:
        balance_sheet_df: DataFrame with Total_Assets_Calc_CNY, Total_Liabilities_Calc_CNY.
        category_growth_df: DataFrame with top-level asset category values over time.

    Returns:
        A pandas DataFrame with DatetimeIndex and columns for each calculated ratio.
        Returns an empty DataFrame if input is invalid.
    """
    logger.info("Calculating balance sheet ratios over time...")

    if balance_sheet_df is None or balance_sheet_df.empty or \
       category_growth_df is None or category_growth_df.empty:
        logger.warning("Input DataFrames are empty or None. Skipping ratio calculation.")
        return pd.DataFrame()

    # Ensure indices match for alignment
    if not balance_sheet_df.index.equals(category_growth_df.index):
        logger.warning("Indices of balance_sheet_df and category_growth_df do not match. Attempting reindex.")
        # Align category_growth_df to balance_sheet_df's index
        category_growth_df = category_growth_df.reindex(balance_sheet_df.index, method='ffill').fillna(0)

    # One improvement: Add explicit check for required columns before accessing them
    required_cols = ['Total_Assets_Calc_CNY', 'Total_Liabilities_Calc_CNY']
    if not all(col in balance_sheet_df.columns for col in required_cols):
        logger.warning(f"Balance sheet DataFrame missing required columns: {required_cols}")
        return pd.DataFrame()

    ratios_df = pd.DataFrame(index=balance_sheet_df.index)

    # --- 1. Debt-to-Asset Ratio ---
    total_assets = balance_sheet_df['Total_Assets_Calc_CNY']
    total_liabilities = balance_sheet_df['Total_Liabilities_Calc_CNY']
    # Avoid division by zero
    ratios_df['Debt_to_Asset_Ratio'] = total_liabilities.div(total_assets.replace(0, np.nan))

    # --- 2. Liquidity Ratio (Simplified: Liquid Assets / Short-Term Liabilities) ---
    # Try to get liquid assets from '现金' category
    liquid_assets = category_growth_df.get('现金', pd.Series(0, index=ratios_df.index)).fillna(0)
    
    # Identify explicit liquid columns from balance sheet for robustness
    # (Sometimes category mapping might miss some columns)
    liquid_cols = [col for col in balance_sheet_df.columns 
                   if (col.startswith('Asset_Cash_') or col.startswith('Asset_Deposit_'))
                   and '_USD' not in col] # Use CNY columns
    
    if liquid_cols:
        logger.info(f"Merging explicit liquid columns from balance sheet: {liquid_cols}")
        bs_liquid = balance_sheet_df[liquid_cols].fillna(0).sum(axis=1)
        # Use the maximum of the two to be safe (or just bs_liquid if it's more reliable)
        liquid_assets = pd.concat([liquid_assets, bs_liquid], axis=1).max(axis=1)

    # Identify short-term liabilities (CC + ShortTerm)
    short_term_liability_cols = [col for col in balance_sheet_df.columns if col.startswith('Liability_CC_') or col.startswith('Liability_ShortTerm_')]
    if short_term_liability_cols:
        short_term_liabilities = balance_sheet_df[short_term_liability_cols].fillna(0).sum(axis=1)
        logger.info(f"Liquid Assets sum: {liquid_assets.sum():.2f}, ST Liabilities sum: {short_term_liabilities.sum():.2f}")
        # Avoid division by zero
        ratios_df['Liquidity_Ratio'] = liquid_assets.div(short_term_liabilities.replace(0, np.nan))
    else:
        logger.warning("No short-term liability columns found. Cannot calculate Liquidity Ratio.")
        ratios_df['Liquidity_Ratio'] = np.nan

    # --- 3. Investment-to-Asset Ratio ---
    # Sum all top-level categories except '现金' and '其他资产' (and implicitly '保险')
    investment_categories = [
        col for col in category_growth_df.columns
        if col not in ['现金', '其他资产', '其他资产_未映射', '其他资产_未分类子类'] # Exclude cash and other/unmapped
    ]
    if investment_categories:
        investment_assets = category_growth_df[investment_categories].fillna(0).sum(axis=1)
        # Avoid division by zero
        ratios_df['Investment_to_Asset_Ratio'] = investment_assets.div(total_assets.replace(0, np.nan))
    else:
        logger.warning("No investment categories found in category_growth_df. Cannot calculate Investment-to-Asset Ratio.")
        ratios_df['Investment_to_Asset_Ratio'] = np.nan


    # Fill potential infinite values resulting from division by zero with NaN
    ratios_df.replace([np.inf, -np.inf], np.nan, inplace=True)

    logger.info("Balance sheet ratio calculation complete.")
    return ratios_df

# --- NEW: generate_yoy_comparison function ---
def generate_yoy_comparison(balance_sheet_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates a Year-over-Year comparison table for key balance sheet metrics.

    Args:
        balance_sheet_df: DataFrame with DatetimeIndex and columns like
                          'Total_Assets_Calc_CNY', 'Total_Liabilities_Calc_CNY', 'Net_Worth_Calc_CNY'.

    Returns:
        A pandas DataFrame comparing year-end values and growth rates.
        Returns an empty DataFrame if insufficient data.
    """
    logger.info("Generating Year-over-Year balance sheet comparison...")

    key_metrics = ['Total_Assets_Calc_CNY', 'Total_Liabilities_Calc_CNY', 'Net_Worth_Calc_CNY']
    if balance_sheet_df is None or balance_sheet_df.empty or not all(col in balance_sheet_df.columns for col in key_metrics):
        logger.warning("Input DataFrame is empty or missing key metrics for YoY comparison.")
        return pd.DataFrame()

    df = balance_sheet_df[key_metrics].copy()
    df.fillna(0, inplace=True) # Fill NaNs for calculations

    # Resample to get the last available day within each year
    # Using 'YE' for Year End frequency. last() gets the last non-NA value in the period.
    year_end_snapshots = df.resample('YE').last()

    # Alternative: Group by year and take the last entry's index within that year
    # This handles cases where data might not extend to the actual year-end
    # year_end_indices = df.groupby(df.index.year).apply(lambda x: x.index.max())
    # year_end_snapshots = df.loc[year_end_indices.values].copy()
    # year_end_snapshots.index = pd.to_datetime(year_end_snapshots.index.year.astype(str)) # Set index to year start/end for clarity

    # One improvement: Handle the case where resample might return a Series
    # This is unlikely but adds an extra safety check
    if isinstance(year_end_snapshots, pd.Series):
        logger.warning("Resampling returned a Series instead of DataFrame. Converting to DataFrame.")
        year_end_snapshots = year_end_snapshots.to_frame()

    if len(year_end_snapshots) < 2:
        logger.warning("Not enough yearly data points (< 2) for YoY comparison.")
        # Return the snapshots we have, but without growth columns
        return year_end_snapshots

    # Calculate YoY changes (Absolute and Percentage)
    # Use .diff() for absolute change from the previous year
    yoy_comparison = year_end_snapshots.copy()
    for metric in key_metrics:
        # Absolute Change
        yoy_comparison[f"{metric}_YoY_Change"] = yoy_comparison[metric].diff()

        # Percentage Change - shift metric to align previous year value for calculation
        prev_year_metric = yoy_comparison[metric].shift(1)
        # Calculate percentage change, handle division by zero or NaN in previous year
        yoy_comparison[f"{metric}_YoY_Growth_%"] = (
            (yoy_comparison[metric] - prev_year_metric) / prev_year_metric.replace(0, np.nan)
        ) * 100

    # Replace infinite values with NaN just in case
    yoy_comparison.replace([np.inf, -np.inf], np.nan, inplace=True)

    # Set index name to 'Year' for clarity
    yoy_comparison.index.name = 'Year'
    # Optionally format index to show only the year
    yoy_comparison.index = yoy_comparison.index.year


    logger.info("Year-over-Year comparison generated.")
    return yoy_comparison


# --- Main function to coordinate all balance sheet analyses (UPDATED) ---
def run_balance_sheet_analysis(balance_sheet_df: pd.DataFrame, config_dir: str) -> dict:
    """
    Runs all balance sheet analysis components.

    Args:
        balance_sheet_df: DataFrame from DataManager containing balance sheet data.
        config_dir: Path to the configuration directory (needed for taxonomy).

    Returns:
        A dictionary containing results from all balance sheet analyses.
        Example: {'trends': {...}, 'allocation': {...}, 'category_growth': pd.DataFrame, ...}
    """
    logger.info("Starting comprehensive balance sheet analysis...")
    all_results = {} # Initialize dictionary to hold all results

    # --- Load Taxonomy ---
    taxonomy_data = _load_asset_taxonomy(config_dir)
    if not taxonomy_data:
         logger.error("Failed to load asset taxonomy. Some analyses may be incomplete.")
         # Decide if analysis should stop or continue with potential errors
         # For now, let's allow it to continue but allocation will likely fail/be empty

    # --- 1. Analyze Trends ---
    trend_results = analyze_balance_sheet_trends(balance_sheet_df)
    all_results['trends'] = trend_results

    # --- 2. Analyze Allocation ---
    allocation_results = analyze_asset_liability_allocation(balance_sheet_df, taxonomy_data)
    all_results['allocation'] = allocation_results

    # --- 3. Analyze Asset Category Growth ---
    logger.info("Running asset category growth analysis...")
    category_growth_df = analyze_asset_category_growth(balance_sheet_df, taxonomy_data)
    all_results['category_growth'] = category_growth_df # Store the resulting DataFrame

    # --- 4. Calculate Balance Sheet Ratios ---
    logger.info("Calculating balance sheet ratios...")
    # Pass both the main balance sheet and the category growth df
    ratios_df = calculate_balance_sheet_ratios(balance_sheet_df, category_growth_df)
    all_results['ratios'] = ratios_df # Store the ratios DataFrame

    # --- 5. Generate Year-over-Year comparison ---
    logger.info("Generating Year-over-Year comparison...")
    yoy_comparison_df = generate_yoy_comparison(balance_sheet_df)
    all_results['yoy_comparison'] = yoy_comparison_df # Store the YoY DataFrame

    logger.info("Balance sheet analysis finished.")
    # Return the dictionary containing results from all executed analyses
    return all_results
