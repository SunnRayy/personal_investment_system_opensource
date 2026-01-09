import pandas as pd
import numpy as np
import logging
from collections import defaultdict

# Configure logging for this module
logger = logging.getLogger(__name__)

# --- Income Analysis Functions ---

# --- analyze_income_trends function (UPDATED) ---
def analyze_income_trends(monthly_df: pd.DataFrame) -> dict:
    """
    Analyzes trends in total, active, and passive income over time.
    Handles potential outliers and reimbursements based on predefined column patterns.
    Dynamically calculates passive income total for ratio analysis.

    Args:
        monthly_df: DataFrame containing monthly income/expense data with a
                    DatetimeIndex and standardized columns like 'Total_Income_Calc_CNY',
                    'Income_Active_...', 'Income_Passive_...', etc.

    Returns:
        A dictionary containing income trend analysis results.
    """
    logger.info("Analyzing income trends...")

    # Define required and optional columns based on expected DataManager output
    total_col = 'Total_Income_Calc_CNY'
    # active_col = 'Income_Active_Total_CNY' # We will calculate this dynamically if needed
    # passive_col = 'Income_Passive_Total_CNY' # We will calculate this dynamically
    required_cols = [total_col] # At least total income is required

    # Use Correct reimbursement column name based on mapping
    reimbursement_col = 'Income_Reimbursement_CNY'
    # Anomaly column based on mapping for '收入_主动收入_其他偶然'
    anomaly_col = 'Income_Other_CNY' # This corresponds to the 880k income outlier

    if monthly_df is None or monthly_df.empty or not all(col in monthly_df.columns for col in required_cols):
        logger.warning(f"Input monthly_df is empty or missing required columns ({required_cols}). Skipping income trend analysis.")
        return {}

    df_analysis = monthly_df.copy()
    outlier_adjusted = False # Flag specific to income outlier
    reimbursement_adjusted = False # Flag specific to income reimbursement

    # --- Handle Reimbursements ---
    if reimbursement_col in df_analysis.columns:
        if pd.api.types.is_numeric_dtype(df_analysis[reimbursement_col]):
            reimbursement_total = df_analysis[reimbursement_col].fillna(0).sum()
            if reimbursement_total > 0:
                logger.info(f"Identified reimbursement income (Column: {reimbursement_col}). Adjusting totals.")
                reimbursement_adjusted = True
                if total_col in df_analysis.columns and pd.api.types.is_numeric_dtype(df_analysis[total_col]):
                     df_analysis[total_col] = df_analysis[total_col] - df_analysis[reimbursement_col].fillna(0)
                # We don't have a reliable active_col total, so we cannot adjust it here easily.
                # else:
                #      logger.warning(f"Cannot adjust non-numeric total income column '{total_col}' for reimbursement.")
                # df_analysis[reimbursement_col] = 0 # Optional: zero out for clarity
            else:
                 logger.debug(f"Reimbursement column '{reimbursement_col}' found but contains no positive values.")
        else:
             logger.warning(f"Reimbursement column '{reimbursement_col}' is not numeric. Skipping adjustment.")
    else:
        logger.debug(f"Reimbursement column '{reimbursement_col}' not found in DataFrame.")


    # --- Handle Specific Anomaly (e.g., Aug 2020 Income) ---
    anomaly_date = pd.Timestamp('2020-08-31') # Assuming month-end index
    # Check the specific anomaly column 'Income_Other_CNY' for the 880k income
    if anomaly_col in df_analysis.columns and anomaly_date in df_analysis.index:
        anomaly_value_raw = df_analysis.loc[anomaly_date, anomaly_col]
        if isinstance(anomaly_value_raw, (int, float, np.number)) and pd.notna(anomaly_value_raw):
            anomaly_value = anomaly_value_raw
            # Use a high threshold appropriate for this specific income outlier (e.g., > 500k)
            if anomaly_value > 500000:
                 logger.info(f"Identified specific anomaly income at {anomaly_date} (Column: {anomaly_col}, Value: {anomaly_value:.0f}). Adjusting totals for analysis.")
                 outlier_adjusted = True # Set the flag for income outlier
                 # Subtract anomaly from total income in the analysis copy
                 if total_col in df_analysis.columns and pd.api.types.is_numeric_dtype(df_analysis[total_col]):
                      df_analysis.loc[anomaly_date, total_col] -= anomaly_value
                 # We cannot easily adjust active total here as it's not pre-calculated
                 # df_analysis.loc[anomaly_date, anomaly_col] = 0 # Optional
            else:
                 logger.debug(f"Anomaly column '{anomaly_col}' found for {anomaly_date}, but value ({anomaly_value}) is not above income outlier threshold.")
        else:
             logger.debug(f"Anomaly column '{anomaly_col}' found for {anomaly_date}, but value is non-numeric or NaN. Raw value: {anomaly_value_raw}")
    else:
         logger.debug(f"Anomaly column '{anomaly_col}' or date '{anomaly_date}' not found. Skipping income anomaly check.")

    # --- *** Dynamically Calculate Passive Income Total *** ---
    passive_income_cols_list = [
        'Income_Passive_FundRedemption_CNY',
        'Income_Passive_BankWealth_CNY',
        'Income_Passive_GoldSale_CNY',
        'Income_Passive_Unknown_CNY' # Include if exists
    ]
    passive_cols_present = [col for col in passive_income_cols_list if col in df_analysis.columns]
    if passive_cols_present:
        logger.debug(f"Calculating passive income using columns: {passive_cols_present}")
        df_analysis['Passive_Income_Calc'] = df_analysis[passive_cols_present].fillna(0).sum(axis=1)
        passive_col_calc = 'Passive_Income_Calc'
    else:
        logger.warning("No passive income columns found to calculate total.")
        df_analysis['Passive_Income_Calc'] = 0.0 # Add column with zeros if none found
        passive_col_calc = 'Passive_Income_Calc'
    # --- *** END DYNAMIC CALCULATION *** ---

    # --- Calculate Trend Data and Metrics ---
    trend_cols = [total_col, passive_col_calc] # Use calculated passive total
    # We don't add active total here as we don't reliably have it

    trend_cols = [col for col in trend_cols if col in df_analysis.columns]
    if not trend_cols:
        logger.error("No valid trend columns found after adjustments. Cannot proceed with trend analysis.")
        return {}
    trend_data = df_analysis[trend_cols].copy()

    # Calculate basic stats on the adjusted total income
    income_series = trend_data[total_col].dropna()
    avg_income = income_series.mean() if not income_series.empty else 0
    median_income = income_series.median() if not income_series.empty else 0
    income_std_dev = income_series.std() if not income_series.empty else 0
    income_cv = (income_std_dev / avg_income) if avg_income > 0 else np.nan

    # Calculate average passive income ratio using calculated passive total
    avg_passive_ratio = np.nan
    denominator = trend_data[total_col].replace(0, np.nan).dropna()
    if passive_col_calc in trend_data.columns and not denominator.empty:
         numerator = trend_data[passive_col_calc].reindex(denominator.index)
         passive_ratio_monthly = numerator.div(denominator)
         avg_passive_ratio = passive_ratio_monthly.mean()
         logger.info(f"Calculated average passive income ratio: {avg_passive_ratio:.2%}")
    else:
         logger.warning(f"Cannot calculate passive income ratio. Missing columns or zero total income. PassiveCol='{passive_col_calc}', TotalCol='{total_col}'")


    results = {
        'trend_data': trend_data, # Now includes 'Passive_Income_Calc'
        'average_income': avg_income,
        'median_income': median_income,
        'income_std_dev': income_std_dev,
        'income_cv': income_cv,
        'income_outlier_adjusted': outlier_adjusted, # Use specific flag name
        'income_reimbursement_adjusted': reimbursement_adjusted, # Use specific flag name
        'average_passive_income_ratio': avg_passive_ratio # Now calculated
    }
    logger.info("Income trend analysis complete.")
    return results

# --- analyze_income_sources function (UPDATED) ---
def analyze_income_sources(monthly_df: pd.DataFrame, num_months: int = 12) -> dict:
    """
    Analyzes income sources based on the most recent period, using final CNY columns.
    Adjusts for known anomaly value if the period includes it.

    Args:
        monthly_df: DataFrame containing monthly income/expense data.
        num_months: The number of recent months to consider for the analysis.

    Returns:
        A dictionary where keys are income source column names (cleaned) and
        values are dictionaries containing {'value': float, 'percentage': float}.
        Returns an empty dict if input is invalid.
    """
    logger.info(f"Analyzing income sources for the last {num_months} months...")

    if monthly_df is None or monthly_df.empty or len(monthly_df) < 1:
        logger.warning("Input monthly_df is empty. Skipping income source analysis.")
        return {}

    # Select recent data
    recent_df = monthly_df.iloc[-num_months:].copy()

    # Identify specific final CNY income columns based on mapping
    income_cols_to_use = [
        'Income_Salary_CNY',
        'Income_RSU_CNY', # Use the CNY version calculated by DataManager
        'Income_Benefit_CNY',
        'Income_HousingFund_CNY',
        'Income_Other_CNY', # Include the anomaly column initially
        'Income_Passive_Unknown_CNY', # If this exists
        'Income_Passive_FundRedemption_CNY',
        'Income_Passive_BankWealth_CNY',
        'Income_Passive_GoldSale_CNY'
        # DO NOT include Income_Reimbursement_CNY here as it's not 'real' income
    ]
    # Filter to only include columns that actually exist in the DataFrame
    income_cols = [col for col in income_cols_to_use if col in recent_df.columns]

    if not income_cols:
        logger.warning("No detailed final CNY income columns found. Skipping source analysis.")
        return {}

    # Calculate total income for each source over the period
    numeric_income_cols = [col for col in income_cols if pd.api.types.is_numeric_dtype(recent_df[col])]
    if len(numeric_income_cols) < len(income_cols):
        logger.warning(f"Non-numeric income columns found and ignored: {[col for col in income_cols if col not in numeric_income_cols]}")
    if not numeric_income_cols:
         logger.warning("No numeric detailed income columns found.")
         return {}

    source_totals = recent_df[numeric_income_cols].sum()

    # --- *** ADJUSTMENT: Subtract known income outlier from 'Income_Other_CNY' total *** ---
    income_anomaly_col = 'Income_Other_CNY'
    anomaly_date = pd.Timestamp('2020-08-31')
    income_anomaly_value = 880000 # Known income outlier value

    # Check if the anomaly column was summed and if the analysis period includes the anomaly date
    if income_anomaly_col in source_totals.index and anomaly_date in recent_df.index:
        # Check the original value for that date to confirm it was the outlier
        original_anomaly_value = recent_df.loc[anomaly_date, income_anomaly_col]
        if isinstance(original_anomaly_value, (int, float, np.number)) and pd.notna(original_anomaly_value) and original_anomaly_value > 500000: # Check threshold
             logger.info(f"Adjusting '{income_anomaly_col}' total for source analysis by subtracting outlier value {income_anomaly_value:.0f} from calculated sum {source_totals[income_anomaly_col]:.0f}")
             source_totals[income_anomaly_col] -= income_anomaly_value
             # Ensure it doesn't go below zero if other values were negative
             if source_totals[income_anomaly_col] < 0 and original_anomaly_value > 0:
                  logger.warning(f"Adjustment made '{income_anomaly_col}' negative. Setting to 0.")
                  source_totals[income_anomaly_col] = 0
        else:
             logger.debug(f"Anomaly date {anomaly_date} is within period, but value in '{income_anomaly_col}' ({original_anomaly_value}) doesn't match expected outlier criteria for source adjustment.")
    # --- ********************************************************************************** ---


    # Filter out zero-value sources AFTER potential adjustment
    source_totals = source_totals[source_totals != 0]

    # Exclude reimbursement column AFTER summing (if it exists in the original df)
    # We already excluded it from income_cols_to_use, but this is safer if definition changes
    cols_to_exclude = ['Income_Reimbursement_CNY']
    source_totals = source_totals.drop(labels=cols_to_exclude, errors='ignore')


    if source_totals.empty:
        logger.warning("No income sources found after filtering and adjustments. Skipping source analysis.")
        return {}

    # Calculate total income for percentage calculation (use the filtered & adjusted sources)
    total_period_income = source_totals.sum()

    source_analysis = {}
    if total_period_income != 0: # Check if total is non-zero
        for source_col, value in source_totals.items():
            # Clean up column name for reporting
            clean_name = source_col.replace('Income_', '').replace('_CNY', '').replace('_', ' ') # Cleaner name
            percentage = (value / total_period_income) * 100
            source_analysis[clean_name] = {'value': value, 'percentage': percentage}
            logger.debug(f" - Source: {clean_name}, Value: {value:.2f}, Percentage: {percentage:.2f}%")
    else:
        logger.warning("Total income over the period is zero or sums to zero after filtering. Cannot calculate percentages.")
        for source_col, value in source_totals.items():
             clean_name = source_col.replace('Income_', '').replace('_CNY', '').replace('_', ' ')
             source_analysis[clean_name] = {'value': value, 'percentage': 0.0}


    logger.info("Income source analysis complete.")
    # Sort by absolute value descending before returning
    sorted_source_analysis = dict(sorted(source_analysis.items(), key=lambda item: abs(item[1]['value']), reverse=True))
    return sorted_source_analysis


# --- Expense Analysis Functions ---

# --- analyze_expense_trends function (unchanged) ---
def analyze_expense_trends(monthly_df: pd.DataFrame) -> dict:
    """
    Analyzes trends in total and categorized expenses over time.
    Handles potential outliers and reimbursements.
    Dynamically calculates essential/non-essential totals.
    (Code remains the same as previous version)
    """
    logger.info("Analyzing expense trends...")

    # Define required and optional columns
    total_col = 'Total_Expense_Calc_CNY'
    required_cols = [total_col]

    # Use Correct reimbursement column name based on mapping
    reimbursable_expense_col = 'Expense_WorkRelated_CNY'
    # Define the column containing the large temporary/housing expense
    expense_anomaly_col = 'Expense_FamilyTemp_CNY' # Correct column for the 928k outlier

    if monthly_df is None or monthly_df.empty or not all(col in monthly_df.columns for col in required_cols):
        logger.warning(f"Input monthly_df is empty or missing required columns ({required_cols}). Skipping expense trend analysis.")
        return {}

    df_analysis = monthly_df.copy()
    outlier_adjusted = False # Flag specific to expense outlier
    reimbursement_adjusted = False # Flag specific to expense reimbursement

    # --- Handle Reimbursable Expenses ---
    # (Logic remains the same, using correct column name)
    if reimbursable_expense_col in df_analysis.columns:
        if pd.api.types.is_numeric_dtype(df_analysis[reimbursable_expense_col]):
            reimbursement_total = df_analysis[reimbursable_expense_col].fillna(0).sum()
            if reimbursement_total > 0:
                logger.info(f"Identified potentially reimbursable expenses (Column: {reimbursable_expense_col}). Adjusting total expense.")
                reimbursement_adjusted = True
                if total_col in df_analysis.columns and pd.api.types.is_numeric_dtype(df_analysis[total_col]):
                     df_analysis[total_col] = df_analysis[total_col] - df_analysis[reimbursable_expense_col].fillna(0)
                else:
                     logger.warning(f"Cannot adjust non-numeric total expense column '{total_col}' for reimbursement.")
                # df_analysis[reimbursable_expense_col] = 0 # Optional
            else:
                 logger.debug(f"Potentially reimbursable expense column '{reimbursable_expense_col}' found but contains no positive values.")
        else:
             logger.warning(f"Potentially reimbursable expense column '{reimbursable_expense_col}' is not numeric. Skipping adjustment.")
    else:
         logger.debug(f"Potentially reimbursable expense column '{reimbursable_expense_col}' not found.")


    # --- Handle Specific Outliers (e.g., Aug 2020 Expense in Temporary Col) ---
    anomaly_date = pd.Timestamp('2020-08-31') # Assuming month-end index
    expense_outlier_threshold = 500000 # Define threshold for large expense

    # Check the SPECIFIC anomaly column 'Expense_FamilyTemp_CNY' for the outlier date
    if expense_anomaly_col in df_analysis.columns and anomaly_date in df_analysis.index:
        anomaly_value_raw = df_analysis.loc[anomaly_date, expense_anomaly_col]

        # Check if it's numeric and above threshold
        if isinstance(anomaly_value_raw, (int, float, np.number)) and pd.notna(anomaly_value_raw) and anomaly_value_raw > expense_outlier_threshold:
            anomaly_value = anomaly_value_raw # This is the 928k value
            logger.info(f"Identified potential large expense outlier at {anomaly_date} (Column: {expense_anomaly_col}, Value: {anomaly_value:.0f}). Adjusting total expense for analysis.")
            outlier_adjusted = True # Set the flag for expense outlier

            # Subtract the specific anomaly value from the total expense for that date
            # in the analysis copy (df_analysis)
            if total_col in df_analysis.columns and pd.api.types.is_numeric_dtype(df_analysis[total_col]):
                 current_total = df_analysis.loc[anomaly_date, total_col]
                 if isinstance(current_total, (int, float, np.number)) and pd.notna(current_total):
                      # Subtract the temporary expense amount from the total for this date
                      df_analysis.loc[anomaly_date, total_col] -= anomaly_value
                      logger.debug(f"Adjusted {total_col} at {anomaly_date} by {-anomaly_value:.0f}. New value: {df_analysis.loc[anomaly_date, total_col]:.0f}")
                 else:
                      logger.warning(f"Could not subtract outlier from non-numeric total expense on {anomaly_date}")
            else:
                 logger.warning(f"Total expense column '{total_col}' not found or not numeric, cannot adjust for outlier.")

            # Also adjust the specific anomaly column in the analysis copy to avoid double counting if used later
            df_analysis.loc[anomaly_date, expense_anomaly_col] = 0 # Set the source of outlier to 0 in analysis df

        else:
            logger.debug(f"Expense anomaly column '{expense_anomaly_col}' on {anomaly_date} ({anomaly_value_raw}) is not above threshold {expense_outlier_threshold} or is non-numeric/NaN.")
    else:
         logger.debug(f"Expense anomaly column '{expense_anomaly_col}' or date '{anomaly_date}' not found. Skipping expense outlier check.")
    # --- END OUTLIER UPDATE ---

    # --- Dynamically Calculate Essential/Non-Essential Totals ---
    # Define lists of columns based on the provided mapping
    essential_cols_list = [
        'Expense_Food_CNY', 'Expense_Housing_CNY', 'Expense_Transport_CNY',
        'Expense_FamilyTemp_CNY', # Include family/temporary initially, outlier adjusted above in df_analysis
        'Outflow_Insurance_Pingan_CNY', 'Outflow_Insurance_Amazon_CNY',
        'Outflow_Insurance_Alipay_CNY', 'Outflow_Loan_Mortgage_CNY'
    ]
    nonessential_cols_list = [
        'Expense_Travel_CNY', 'Expense_Apparel_CNY', 'Expense_Electronics_CNY',
        'Expense_HealthFitness_CNY', 'Expense_Entertainment_CNY'
    ]

    # Filter lists to include only columns present in the DataFrame
    essential_cols_present = [col for col in essential_cols_list if col in df_analysis.columns]
    nonessential_cols_present = [col for col in nonessential_cols_list if col in df_analysis.columns]

    # Calculate totals only if columns are present
    essential_col_calc = None
    if essential_cols_present:
        # Use the df_analysis copy where the anomaly in Expense_FamilyTemp_CNY was zeroed out
        df_analysis['Essential_Expense_Calc'] = df_analysis[essential_cols_present].fillna(0).sum(axis=1)
        essential_col_calc = 'Essential_Expense_Calc' # Use calculated column name
        logger.debug(f"Calculated essential expenses using columns: {essential_cols_present}")
    else:
        logger.warning("No essential expense columns found to calculate total.")

    nonessential_col_calc = None
    if nonessential_cols_present:
        df_analysis['NonEssential_Expense_Calc'] = df_analysis[nonessential_cols_present].fillna(0).sum(axis=1)
        nonessential_col_calc = 'NonEssential_Expense_Calc'
        logger.debug(f"Calculated non-essential expenses using columns: {nonessential_cols_present}")
    else:
        logger.warning("No non-essential expense columns found to calculate total.")
    # --- END DYNAMIC CALCULATION ---


    # --- Calculate Trend Data and Metrics ---
    trend_cols = [total_col]
    # Use the dynamically calculated column names if available
    if essential_col_calc: trend_cols.append(essential_col_calc)
    if nonessential_col_calc: trend_cols.append(nonessential_col_calc)

    # Ensure trend columns exist before selecting (redundant check, but safe)
    trend_cols = [col for col in trend_cols if col in df_analysis.columns]
    if not trend_cols:
        logger.error("No valid trend columns found after adjustments. Cannot proceed with expense trend analysis.")
        return {}
    # Use the df_analysis which has the outlier adjusted AND calculated category totals
    trend_data = df_analysis[trend_cols].copy()

    # Calculate basic stats on the adjusted total expense
    expense_series = trend_data[total_col].dropna()
    avg_expense = expense_series.mean() if not expense_series.empty else 0
    median_expense = expense_series.median() if not expense_series.empty else 0
    expense_std_dev = expense_series.std() if not expense_series.empty else 0
    expense_cv = (expense_std_dev / avg_expense) if avg_expense > 0 else np.nan

    # Calculate average non-essential ratio (using calculated totals)
    avg_nonessential_ratio = np.nan
    # Check if both calculated non-essential and adjusted total columns are available
    if nonessential_col_calc and total_col in trend_data.columns:
        denominator = trend_data[total_col].replace(0, np.nan).dropna()
        if not denominator.empty:
            # Use the calculated non-essential total
            numerator = trend_data[nonessential_col_calc].reindex(denominator.index)
            nonessential_ratio_monthly = numerator.div(denominator)
            avg_nonessential_ratio = nonessential_ratio_monthly.mean()
            logger.info(f"Calculated average non-essential ratio: {avg_nonessential_ratio:.2%}")
        else:
            logger.warning("Cannot calculate non-essential ratio because adjusted total expense is zero or NaN.")
    else:
        logger.warning(f"Cannot calculate non-essential ratio. Missing calculated columns: NonEssential='{nonessential_col_calc}', Total='{total_col}'")


    results = {
        'trend_data': trend_data, # Includes calculated essential/non-essential if available
        'average_expense': avg_expense, # Calculated excluding outlier impact
        'median_expense': median_expense, # Calculated excluding outlier impact
        'expense_std_dev': expense_std_dev, # Calculated excluding outlier impact
        'expense_cv': expense_cv,
        'expense_outlier_adjusted': outlier_adjusted, # Use specific flag name
        'expense_reimbursement_adjusted': reimbursement_adjusted, # Use specific flag name
        'average_nonessential_ratio': avg_nonessential_ratio # Now calculated dynamically
    }
    logger.info("Expense trend analysis complete.")
    return results

# --- analyze_expense_categories function (UPDATED to exclude Investment Outflows) ---
def analyze_expense_categories(monthly_df: pd.DataFrame, num_months: int = 12) -> dict:
    """
    Analyzes non-investment expense categories based on the most recent period.
    Adjusts the anomaly value from the specific category total if period includes it.
    Investment outflows (Outflow_Invest_*) are excluded from this analysis.

    Args:
        monthly_df: DataFrame containing monthly income/expense data.
        num_months: The number of recent months to consider for the analysis.

    Returns:
        A dictionary where keys are non-investment expense category column names (cleaned)
        and values are dictionaries containing {'value': float, 'percentage': float}.
        Returns an empty dict if input is invalid or no non-investment expenses found.
    """
    logger.info(f"Analyzing non-investment expense categories for the last {num_months} months...")

    if monthly_df is None or monthly_df.empty or len(monthly_df) < 1:
        logger.warning("Input monthly_df is empty. Skipping expense category analysis.")
        return {}

    # Select recent data
    recent_df = monthly_df.iloc[-num_months:].copy()

    # Define columns to exclude from DIRECT category analysis
    reimbursable_expense_col = 'Expense_WorkRelated_CNY' # Exclude reimbursement column itself
    cols_to_exclude = [reimbursable_expense_col]

    # *** UPDATED: Identify ONLY non-investment expense/outflow columns ***
    expense_cols = [
        col for col in recent_df.columns
        if col.startswith('Expense_')
        and 'Total' not in col
        and 'Calc' not in col
        and col not in cols_to_exclude # Exclude specific cols like reimbursement
    ]
    # Include Outflow columns EXCEPT those starting with Outflow_Invest_
    outflow_cols = [
        col for col in recent_df.columns
        if col.startswith('Outflow_') and not col.startswith('Outflow_Invest_')
    ]
    all_expense_detail_cols = expense_cols + outflow_cols
    # *********************************************************************


    if not all_expense_detail_cols:
        logger.warning("No detailed non-investment expense or non-investment outflow columns found. Skipping category analysis.")
        return {}

    # Calculate total expense for each category over the period
    numeric_cols = [col for col in all_expense_detail_cols if pd.api.types.is_numeric_dtype(recent_df[col])]
    non_numeric_cols = [col for col in all_expense_detail_cols if not pd.api.types.is_numeric_dtype(recent_df[col])]
    if non_numeric_cols:
        logger.warning(f"Non-numeric columns found in expense details: {non_numeric_cols}. They will be ignored in sum.")

    if not numeric_cols:
        logger.warning("No numeric detailed non-investment expense/outflow columns found.")
        return {}

    category_totals = recent_df[numeric_cols].sum()

    # *** ADJUSTMENT: Subtract known outlier from 'Expense_FamilyTemp_CNY' total if applicable ***
    expense_anomaly_col = 'Expense_FamilyTemp_CNY'
    anomaly_date = pd.Timestamp('2020-08-31')
    expense_anomaly_value = 928505 # The known outlier value

    # Check if the anomaly column was summed and if the analysis period includes the anomaly date
    if expense_anomaly_col in category_totals.index and anomaly_date in recent_df.index:
        original_anomaly_value = recent_df.loc[anomaly_date, expense_anomaly_col]
        if isinstance(original_anomaly_value, (int, float, np.number)) and pd.notna(original_anomaly_value) and original_anomaly_value > 500000: # Check threshold
             logger.info(f"Adjusting '{expense_anomaly_col}' total for category analysis by subtracting outlier value {expense_anomaly_value:.0f} from calculated sum {category_totals[expense_anomaly_col]:.0f}")
             category_totals[expense_anomaly_col] -= expense_anomaly_value
             if category_totals[expense_anomaly_col] < 0 and original_anomaly_value > 0 :
                  logger.warning(f"Adjustment made '{expense_anomaly_col}' negative. Setting to 0.")
                  category_totals[expense_anomaly_col] = 0
        else:
             logger.debug(f"Anomaly date {anomaly_date} is within period, but value in '{expense_anomaly_col}' ({original_anomaly_value}) doesn't match expected outlier criteria for source adjustment.")

    # *******************************************************************************************

    # Filter out zero-value categories AFTER potential adjustment
    category_totals = category_totals[category_totals != 0]

    if category_totals.empty:
        logger.warning("No non-zero non-investment expense categories found after filtering and adjustments. Skipping category analysis.")
        return {}

    # Calculate total expense for percentage calculation (use the filtered & adjusted categories)
    # Now, category_totals already excludes investment outflows
    total_period_expense_for_pct = category_totals.sum()


    category_analysis = {}
    if total_period_expense_for_pct != 0: # Check if total is non-zero
        for category_col, value in category_totals.items():
            # Clean up column name for reporting
            clean_name = category_col.replace('Expense_', '').replace('Outflow_', '').replace('_CNY','').replace('_USD','').replace('_', ' ') # Cleaner name
            # Calculate percentage based on non-investment expenses
            percentage = (value / total_period_expense_for_pct) * 100
            category_analysis[clean_name] = {'value': value, 'percentage': percentage}
            logger.debug(f" - Category: {clean_name}, Value: {value:.2f}, Percentage: {percentage:.2f}%")
    else:
         logger.warning("Total non-investment expense over the period is zero or sums to zero after filtering. Cannot calculate percentages.")
         for category_col, value in category_totals.items():
             clean_name = category_col.replace('Expense_', '').replace('Outflow_', '').replace('_CNY','').replace('_USD','').replace('_', ' ')
             category_analysis[clean_name] = {'value': value, 'percentage': 0.0}

    logger.info("Expense category analysis complete.")
     # Sort by absolute value descending before returning
    sorted_category_analysis = dict(sorted(category_analysis.items(), key=lambda item: abs(item[1]['value']), reverse=True))
    return sorted_category_analysis

# --- Investment Flow Analysis ---

def analyze_investment_flows(monthly_df: pd.DataFrame) -> dict:
    """
    Analyzes investment flow patterns, regularity, and tracking metrics.
    Utilizes the new Total_Investment_Calc_CNY column from enhanced DataManager.

    Args:
        monthly_df: DataFrame containing monthly data with Total_Investment_Calc_CNY column

    Returns:
        A dictionary containing investment flow analysis results.
    """
    logger.info("Analyzing investment flows...")

    required_cols = ['Total_Investment_Calc_CNY']
    if monthly_df is None or monthly_df.empty or not all(col in monthly_df.columns for col in required_cols):
        logger.warning(f"Input monthly_df is empty or missing required columns ({required_cols}). Skipping investment flow analysis.")
        return {"status": "skipped", "reason": "Missing Total_Investment_Calc_CNY column"}

    df_analysis = monthly_df.copy()
    investment_col = 'Total_Investment_Calc_CNY'
    
    # Ensure investment column is numeric
    if not pd.api.types.is_numeric_dtype(df_analysis[investment_col]):
        logger.warning(f"{investment_col} is not numeric. Converting...")
        df_analysis[investment_col] = pd.to_numeric(df_analysis[investment_col], errors='coerce')
    
    # Fill NaN values with 0 for investment calculation
    df_analysis[investment_col] = df_analysis[investment_col].fillna(0)
    
    # Calculate investment flow metrics
    total_investment = df_analysis[investment_col].sum()
    avg_monthly_investment = df_analysis[investment_col].mean()
    investment_periods = (df_analysis[investment_col] > 0).sum()
    total_periods = len(df_analysis)
    investment_frequency = (investment_periods / total_periods * 100) if total_periods > 0 else 0
    
    # Investment regularity analysis
    investment_months = df_analysis[df_analysis[investment_col] > 0]
    if not investment_months.empty:
        max_investment = investment_months[investment_col].max()
        min_investment = investment_months[investment_col].min()
        investment_volatility = investment_months[investment_col].std()
        recent_6_months = df_analysis.iloc[-6:][investment_col].sum() if len(df_analysis) >= 6 else total_investment
    else:
        max_investment = min_investment = investment_volatility = recent_6_months = 0
    
    # Investment trend analysis (last 12 months vs previous 12 months)
    if len(df_analysis) >= 24:
        recent_12_months = df_analysis.iloc[-12:][investment_col].sum()
        previous_12_months = df_analysis.iloc[-24:-12][investment_col].sum()
        investment_trend = ((recent_12_months - previous_12_months) / previous_12_months * 100) if previous_12_months > 0 else 0
    else:
        recent_12_months = df_analysis.iloc[-12:][investment_col].sum() if len(df_analysis) >= 12 else total_investment
        investment_trend = 0
    
    # Investment as percentage of income (if available)
    investment_rate = 0
    if 'Total_Income_Calc_CNY' in df_analysis.columns:
        total_income = df_analysis['Total_Income_Calc_CNY'].sum()
        investment_rate = (total_investment / total_income * 100) if total_income > 0 else 0
    
    # Identify investment category breakdown (if detailed columns available)
    investment_categories = {}
    investment_detail_cols = [
        col for col in df_analysis.columns
        if col.startswith('Outflow_Invest_') and col != investment_col
    ]
    
    for col in investment_detail_cols:
        if pd.api.types.is_numeric_dtype(df_analysis[col]):
            category_total = df_analysis[col].fillna(0).sum()
            if category_total > 0:
                # Extract category name from column (e.g., 'Outflow_Invest_Fund_TT_CNY' -> 'Fund_TT')
                category_name = col.replace('Outflow_Invest_', '').replace('_CNY', '')
                investment_categories[category_name] = {
                    'total': float(category_total),
                    'percentage': (category_total / total_investment * 100) if total_investment > 0 else 0,
                    'frequency': float((df_analysis[col].fillna(0) > 0).sum())
                }
    
    results = {
        'status': 'completed',
        'total_investment': float(total_investment),
        'avg_monthly_investment': float(avg_monthly_investment),
        'investment_periods': int(investment_periods),
        'total_periods': int(total_periods),
        'investment_frequency_pct': float(investment_frequency),
        'investment_rate_pct': float(investment_rate),
        'max_monthly_investment': float(max_investment),
        'min_monthly_investment': float(min_investment),
        'investment_volatility': float(investment_volatility) if pd.notna(investment_volatility) else 0,
        'recent_6_months_investment': float(recent_6_months),
        'recent_12_months_investment': float(recent_12_months),
        'investment_trend_pct': float(investment_trend),
        'investment_categories': investment_categories,
        'insights': []
    }
    
    # Generate insights
    if investment_frequency >= 80:
        results['insights'].append("High investment consistency - investing in 80%+ of periods")
    elif investment_frequency >= 50:
        results['insights'].append("Moderate investment consistency - regular monthly investing")
    elif investment_frequency < 25:
        results['insights'].append("Low investment frequency - consider more regular investing")
    
    if investment_rate >= 20:
        results['insights'].append("Excellent investment rate - saving 20%+ of income for investments")
    elif investment_rate >= 10:
        results['insights'].append("Good investment rate - healthy portion of income going to investments")
    elif investment_rate < 5:
        results['insights'].append("Low investment rate - consider increasing investment allocation")
    
    if investment_trend > 10:
        results['insights'].append("Positive investment trend - increasing investment amounts over time")
    elif investment_trend < -10:
        results['insights'].append("Declining investment trend - investment amounts decreasing")
    
    logger.info(f"Investment flow analysis completed. Total investment: ¥{total_investment:,.0f}, Frequency: {investment_frequency:.1f}%")
    return results


# --- run_cash_flow_analysis function (No changes needed here) ---
def run_cash_flow_analysis(monthly_df: pd.DataFrame) -> dict:
    """
    Runs all cash flow analysis components (income, expense, savings).

    Args:
        monthly_df: DataFrame from DataManager containing monthly data.

    Returns:
        A dictionary containing results from all cash flow analyses.
    """
    logger.info("Starting comprehensive cash flow analysis...")
    all_results = {}

    # --- 1. Income Analysis ---
    income_trends = analyze_income_trends(monthly_df)
    all_results['income_trends'] = income_trends
    income_sources = analyze_income_sources(monthly_df)
    all_results['income_sources'] = income_sources

    # --- 2. Expense Analysis ---
    expense_trends = analyze_expense_trends(monthly_df)
    all_results['expense_trends'] = expense_trends
    expense_categories = analyze_expense_categories(monthly_df) # Call the updated function
    all_results['expense_categories'] = expense_categories

    # --- 3. Investment Flow Analysis ---
    investment_flows = analyze_investment_flows(monthly_df)
    all_results['investment_flows'] = investment_flows

    # --- 4. Cash Flow Overview & Savings ---
    cash_flow_overview = analyze_cash_flow_overview(monthly_df)
    all_results['cash_flow_overview'] = cash_flow_overview

    # --- 4. YoY Comparison ---
    cash_flow_yoy = generate_cash_flow_yoy_comparison(monthly_df)
    all_results['yoy_comparison'] = cash_flow_yoy

    logger.info("Cash flow analysis finished.")
    return all_results

# --- Cash Flow & Savings Analysis ---

# --- analyze_cash_flow_overview function (unchanged) ---
def analyze_cash_flow_overview(monthly_df: pd.DataFrame) -> dict:
    """
    Analyzes net cash flow and calculates savings rate.
    (Code remains the same)
    """
    logger.info("Analyzing net cash flow and savings rate...")

    required_cols = ['Net_Cash_Flow_Calc_CNY', 'Total_Income_Calc_CNY']
    if monthly_df is None or monthly_df.empty or not all(col in monthly_df.columns for col in required_cols):
        logger.warning(f"Input monthly_df is empty or missing required columns ({required_cols}). Skipping cash flow overview.")
        return {}

    # Ensure adjustment for outliers/reimbursements if necessary before calculating averages
    # We will use the calculated columns directly, assuming DataManager handled adjustments
    # If not, we would need to re-apply adjustments here based on flags from trend analysis
    net_cash_flow = monthly_df['Net_Cash_Flow_Calc_CNY'].copy()
    total_income = monthly_df['Total_Income_Calc_CNY'].copy()

    # Calculate average net cash flow
    avg_net_cash_flow = net_cash_flow.mean()

    # Calculate savings rate (Net Cash Flow / Total Income)
    # Replace 0 income with NaN to avoid division by zero and infinite results
    savings_rate_monthly = net_cash_flow.div(total_income.replace(0, np.nan))
    avg_savings_rate = savings_rate_monthly.mean() # Average of monthly rates

    results = {
        'net_cash_flow_trend': net_cash_flow,
        'average_net_cash_flow': avg_net_cash_flow,
        'average_savings_rate': avg_savings_rate
    }

    logger.info(f"Cash flow overview complete. Average Savings Rate: {avg_savings_rate:.2%}")
    return results


# --- generate_cash_flow_yoy_comparison function (UPDATED) ---
def generate_cash_flow_yoy_comparison(monthly_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates a Year-over-Year comparison table for key cash flow metrics,
    adjusting for known outliers before aggregation.

    Args:
        monthly_df: DataFrame with DatetimeIndex and columns like
                    'Total_Income_Calc_CNY', 'Total_Expense_Calc_CNY', 'Net_Cash_Flow_Calc_CNY',
                    'Income_Other_CNY', 'Expense_FamilyTemp_CNY'.

    Returns:
        A pandas DataFrame comparing annual totals and growth rates.
        Returns an empty DataFrame if insufficient data.
    """
    logger.info("Generating Year-over-Year cash flow comparison (with outlier adjustment)...")

    key_metrics = ['Total_Income_Calc_CNY', 'Total_Expense_Calc_CNY', 'Net_Cash_Flow_Calc_CNY']
    if monthly_df is None or monthly_df.empty or not all(col in monthly_df.columns for col in key_metrics):
        logger.warning("Input DataFrame is empty or missing key metrics for YoY cash flow comparison.")
        return pd.DataFrame()

    # --- Apply Outlier Adjustments BEFORE Resampling ---
    df_adjusted = monthly_df.copy()
    anomaly_date = pd.Timestamp('2020-08-31')
    income_anomaly_col = 'Income_Other_CNY'
    income_anomaly_value = 880000
    expense_anomaly_col = 'Expense_FamilyTemp_CNY'
    expense_anomaly_value = 928505

    if anomaly_date in df_adjusted.index:
        # Adjust Income
        if income_anomaly_col in df_adjusted.columns:
            original_income = df_adjusted.loc[anomaly_date, income_anomaly_col]
            if isinstance(original_income, (int, float, np.number)) and pd.notna(original_income) and original_income > 500000:
                 logger.debug(f"Adjusting YoY Income: Subtracting {income_anomaly_value} from {key_metrics[0]} for {anomaly_date}")
                 df_adjusted.loc[anomaly_date, key_metrics[0]] -= income_anomaly_value
                 # Also adjust Net Cash Flow
                 if key_metrics[2] in df_adjusted.columns:
                      df_adjusted.loc[anomaly_date, key_metrics[2]] -= income_anomaly_value

        # Adjust Expense
        if expense_anomaly_col in df_adjusted.columns:
             original_expense = df_adjusted.loc[anomaly_date, expense_anomaly_col]
             if isinstance(original_expense, (int, float, np.number)) and pd.notna(original_expense) and original_expense > 500000:
                  logger.debug(f"Adjusting YoY Expense: Subtracting {expense_anomaly_value} from {key_metrics[1]} for {anomaly_date}")
                  df_adjusted.loc[anomaly_date, key_metrics[1]] -= expense_anomaly_value
                  # Also adjust Net Cash Flow (add back the subtracted expense)
                  if key_metrics[2] in df_adjusted.columns:
                       df_adjusted.loc[anomaly_date, key_metrics[2]] += expense_anomaly_value # Add back because expense is outflow

    # --- END Outlier Adjustments ---


    df_calc = df_adjusted[key_metrics].copy() # Use the adjusted DataFrame
    df_calc.fillna(0, inplace=True) # Fill NaNs for calculations

    # Resample to get annual sums using the adjusted data
    annual_totals = df_calc.resample('YE').sum()

    if len(annual_totals) < 2:
        logger.warning("Not enough yearly data points (< 2) for YoY comparison.")
        # Return the totals we have, but without growth columns
        return annual_totals

    # Calculate YoY changes (Absolute and Percentage)
    yoy_comparison = annual_totals.copy()
    for metric in key_metrics:
        # Absolute Change
        yoy_comparison[f"{metric}_YoY_Change"] = yoy_comparison[metric].diff()

        # Percentage Change
        prev_year_metric = yoy_comparison[metric].shift(1)
        yoy_comparison[f"{metric}_YoY_Growth_%"] = (
            (yoy_comparison[metric] - prev_year_metric) / prev_year_metric.replace(0, np.nan)
        ) * 100

    # Replace infinite values with NaN
    yoy_comparison.replace([np.inf, -np.inf], np.nan, inplace=True)

    # Set index name and format
    yoy_comparison.index.name = 'Year'
    yoy_comparison.index = yoy_comparison.index.year

    logger.info("Year-over-Year cash flow comparison generated.")
    return yoy_comparison


