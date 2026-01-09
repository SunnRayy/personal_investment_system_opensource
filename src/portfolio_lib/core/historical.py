# portfolio_lib/core/historical.py
"""
Module for extracting historical asset returns and assessing data quality.
Filters out future dates before processing.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
from pandas.tseries.offsets import MonthEnd

# Import the mapper functions - assumes taxonomy is initialized externally
from .asset_mapper import create_asset_class_mapper, _get_taxonomy # Use internal getter

def extract_historical_returns_with_assessment(
    balance_df: Optional[pd.DataFrame],
    monthly_df: Optional[pd.DataFrame], # monthly_df is not used in this version, but kept for signature consistency
    settings: Dict[str, Any]
) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
    """
    Extracts historical returns for top-level asset classes from balance sheet data,
    filtering out future dates, and assesses the quality of the data for MPT analysis.

    Args:
        balance_df: Cleaned DataFrame containing time series balance sheet data.
        monthly_df: Cleaned DataFrame containing monthly income/expense data (currently unused).
        settings: The loaded configuration dictionary.

    Returns:
        A tuple containing:
        - DataFrame: Monthly returns aggregated by top-level asset class (or None if failed).
        - Dict: Data quality assessment results.
    """
    print("\nSTEP 2: Extracting Historical Returns & Assessing Quality...")
    debug_mode = settings.get('general', {}).get('debug_mode', True) # Default debug to True for this step
    taxonomy = _get_taxonomy() # Get initialized taxonomy

    # Initialize data quality assessment dictionary
    data_quality = {
        'sufficient_for_mpt': False,
        'quality_score': 0.0,
        'reason': '',
        'asset_coverage': 0.0,
        'time_span_months': 0,
        'completeness': 0.0,
        'original_end_date': None,
        'filtered_end_date': None
    }

    if balance_df is None or balance_df.empty:
        data_quality['reason'] = '资产负债表数据为空 (Balance sheet data is empty)'
        print(f"Error: {data_quality['reason']}")
        return None, data_quality

    if not isinstance(balance_df.index, pd.DatetimeIndex):
         data_quality['reason'] = '资产负债表索引不是日期类型 (Balance sheet index is not DatetimeIndex)'
         print(f"Error: {data_quality['reason']}")
         return None, data_quality

    # --- Filter out future dates ---
    original_end_date = balance_df.index.max()
    data_quality['original_end_date'] = original_end_date.strftime('%Y-%m-%d') if pd.notna(original_end_date) else None

    # Determine the cutoff date (end of the previous month relative to today)
    # Use server time or a fixed date for consistency if needed
    # today = pd.Timestamp(datetime.now())
    # For consistency with previous context, let's assume 'today' is around April 26, 2025
    today = pd.Timestamp('2025-04-26') # Use context date
    cutoff_date = today.replace(day=1) - pd.Timedelta(days=1) # End of previous month (2025-03-31)
    data_quality['analysis_cutoff_date'] = cutoff_date.strftime('%Y-%m-%d')

    print(f"Filtering balance sheet data up to: {cutoff_date.strftime('%Y-%m-%d')}")
    balance_df_filtered = balance_df.loc[balance_df.index <= cutoff_date].copy() # Use .copy()

    if balance_df_filtered.empty:
        data_quality['reason'] = f'过滤未来日期后无数据 (No data left after filtering future dates up to {cutoff_date.strftime("%Y-%m-%d")})'
        print(f"Error: {data_quality['reason']}")
        return None, data_quality

    filtered_end_date = balance_df_filtered.index.max()
    data_quality['filtered_end_date'] = filtered_end_date.strftime('%Y-%m-%d') if pd.notna(filtered_end_date) else None
    print(f"Data filtered. Original end date: {data_quality['original_end_date']}, Filtered end date: {data_quality['filtered_end_date']}")


    # --- Extract potential asset columns from the FILTERED data ---
    asset_keywords: list[str] = taxonomy.get('asset_identification_keywords',
        ['投资资产', '固定资产', 'RMB', '美元', '存款', '现金', 'Private_Equity_Investment_A', '股票', '基金', '理财', '黄金', '保险', '房产']
    )
    asset_columns = [
        col for col in balance_df_filtered.columns # Use filtered columns
        if any(keyword in col for keyword in asset_keywords)
    ]

    if not asset_columns:
        data_quality['reason'] = '过滤后的资产负债表中未找到可识别的资产列 (No identifiable asset columns found in filtered data)'
        print(f"Error: {data_quality['reason']}")
        return None, data_quality

    if debug_mode:
        print(f"- Identified {len(asset_columns)} potential asset columns in filtered data.")

    # --- Calculate Raw Monthly Returns using FILTERED data ---
    # Resample the *filtered* data
    monthly_values = balance_df_filtered[asset_columns].ffill().resample('ME').last()
    raw_returns_df = monthly_values.pct_change()
    raw_returns_df = raw_returns_df.iloc[1:] # Remove first NaN row

    if raw_returns_df.empty:
        data_quality['reason'] = '无法从过滤后的数据计算原始月度收益率 (Could not calculate raw monthly returns from filtered data)'
        print(f"Error: {data_quality['reason']}")
        return None, data_quality

    # --- Map and Aggregate Returns by Top-Level Class ---
    map_to_sub_class, map_to_top_class = create_asset_class_mapper()
    special_categories = set(taxonomy.get('special_categories', []))
    top_level_classes = taxonomy.get('top_level_classes', [])

    aggregated_returns_df = pd.DataFrame(index=raw_returns_df.index)
    processed_assets = set()

    # Get latest values for weighting (use the last row of the FILTERED balance_df)
    latest_values = balance_df_filtered.iloc[-1]

    for top_class in top_level_classes:
        # Skip special categories early
        if top_class in special_categories:
            if debug_mode: print(f"- Skipping aggregation for special category: '{top_class}'")
            continue

        class_assets_returns = []
        class_weights = {}
        total_weight_for_class = 0

        for asset_col in raw_returns_df.columns:
            mapped_top_class = map_to_top_class(asset_col)
            if mapped_top_class == top_class: # No need to check special_categories again
                # Defensive check: ensure we have valid data before checking for non-null values
                try:
                    asset_series = raw_returns_df[asset_col]
                    has_valid_data = bool(asset_series.notna().sum() > 0)
                except Exception as e:
                    if debug_mode: print(f"    - Warning: Could not check validity for '{asset_col}': {e}")
                    has_valid_data = False
                
                if has_valid_data:
                    class_assets_returns.append(raw_returns_df[asset_col])
                    asset_value = latest_values.get(asset_col, 0)
                    if pd.notna(asset_value) and asset_value > 0:
                         class_weights[asset_col] = asset_value
                         total_weight_for_class += asset_value
                    processed_assets.add(asset_col)

        if class_assets_returns:
            if len(class_assets_returns) == 1:
                aggregated_returns_df[top_class] = class_assets_returns[0]
                if debug_mode: print(f"- Aggregated '{top_class}': Using direct returns from '{class_assets_returns[0].name}'")
            elif total_weight_for_class > 0:
                weighted_returns = pd.Series(0.0, index=raw_returns_df.index)
                asset_details = []
                for asset_return_series in class_assets_returns:
                    asset_name = asset_return_series.name
                    weight = class_weights.get(asset_name, 0) / total_weight_for_class
                    weighted_returns += asset_return_series.fillna(0) * weight
                    asset_details.append(f"'{asset_name}' ({weight:.1%})")
                aggregated_returns_df[top_class] = weighted_returns
                if debug_mode: print(f"- Aggregated '{top_class}': Weighted avg of {', '.join(asset_details)}")
            else:
                print(f"Warning: No valid weights for assets in '{top_class}'. Using simple average.")
                combined_df = pd.concat(class_assets_returns, axis=1)
                aggregated_returns_df[top_class] = combined_df.mean(axis=1)
                if debug_mode: print(f"- Aggregated '{top_class}': Simple avg of {[s.name for s in class_assets_returns]}")

    # Drop columns with all NaNs
    aggregated_returns_df = aggregated_returns_df.dropna(axis=1, how='all')

    if aggregated_returns_df.empty:
        data_quality['reason'] = '聚合后的收益率数据为空 (Aggregated returns data is empty after processing)'
        print(f"Error: {data_quality['reason']}")
        return None, data_quality

    # --- Assess Data Quality based on the AGGREGATED historical data ---
    dq_thresholds = settings.get('data_quality_thresholds', {})
    min_required_months = dq_thresholds.get('min_required_months', 24)
    min_required_assets = dq_thresholds.get('min_required_assets', 3)
    min_completeness_threshold = dq_thresholds.get('min_completeness', 0.7)

    # Use the length of the *aggregated* returns df for time span
    time_span_months = len(aggregated_returns_df)
    asset_types_count = len(aggregated_returns_df.columns)
    completeness = aggregated_returns_df.notna().mean().mean()

    covered_assets_set = set(aggregated_returns_df.columns)
    # Compare against top-level classes EXCLUDING special categories
    all_analyzable_assets_set = set(tlc for tlc in top_level_classes if tlc not in special_categories)
    asset_coverage = len(covered_assets_set) / len(all_analyzable_assets_set) if all_analyzable_assets_set else 0

    time_score = min(time_span_months / min_required_months, 1.0) * 4
    assets_score = min(asset_types_count / min_required_assets, 1.0) * 4
    completeness_score = min(completeness / min_completeness_threshold, 1.0) * 2
    quality_score = max(0, min(10, time_score + assets_score + completeness_score))

    data_quality['time_span_months'] = time_span_months
    data_quality['asset_coverage'] = asset_coverage
    data_quality['completeness'] = completeness
    data_quality['quality_score'] = quality_score
    data_quality['covered_asset_classes'] = list(covered_assets_set)

    reasons = []
    if time_span_months < min_required_months:
        reasons.append(f'历史太短 ({time_span_months}月 < {min_required_months}月)')
    if asset_types_count < min_required_assets:
        reasons.append(f'资产类别太少 ({asset_types_count}种 < {min_required_assets}种)')
    if completeness < min_completeness_threshold:
        reasons.append(f'数据不完整 ({completeness:.1%} < {min_completeness_threshold:.1%})')

    data_quality['sufficient_for_mpt'] = not reasons
    data_quality['reason'] = '; '.join(reasons) if reasons else '数据质量足够 (Data quality sufficient)'

    # Print summary
    print(f"\n历史数据质量评估 (基于 {time_span_months} 个月过滤后数据):") # Clarify based on filtered data
    print(f"  - 时间跨度 (Months): {time_span_months} (需要 {min_required_months})")
    print(f"  - 资产类别覆盖 (Classes Covered): {asset_types_count}/{len(all_analyzable_assets_set)} ({asset_coverage:.0%}) (需要 {min_required_assets})")
    print(f"  - 数据完整性 (Completeness): {completeness:.1%} (需要 {min_completeness_threshold:.1%})")
    print(f"  - 综合质量评分 (Quality Score): {quality_score:.1f}/10")
    print(f"  - 是否足够用于MPT (Sufficient for MPT): {'是 (Yes)' if data_quality['sufficient_for_mpt'] else '否 (No)'}")
    if not data_quality['sufficient_for_mpt']:
        print(f"  - 原因 (Reason): {data_quality['reason']}")

    print("Finished extracting historical returns.")
    return aggregated_returns_df, data_quality


def generate_default_returns_data(settings: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """
    Generates simulated monthly returns data based on default expectations
    defined in the asset taxonomy configuration.

    Used when historical data is insufficient or missing.

    Args:
        settings: The loaded configuration dictionary.

    Returns:
        DataFrame containing simulated monthly returns, or None if generation fails.
    """
    # --- This function remains the same as before ---
    print("\nGenerating Default Returns Data based on Taxonomy Expectations...")
    debug_mode = settings.get('general', {}).get('debug_mode', False)
    taxonomy = _get_taxonomy()
    mpt_params = settings.get('mpt_params', {})
    simulation_months = mpt_params.get('default_simulation_months', 60)

    default_expectations = taxonomy.get('default_expectations')
    top_level_classes = taxonomy.get('top_level_classes', [])
    sub_classes_map = taxonomy.get('sub_classes', {})
    special_categories = set(taxonomy.get('special_categories', []))

    if not default_expectations:
        print("Error: 'default_expectations' not found in taxonomy configuration.")
        return None

    top_level_expectations: Dict[str, Dict[str, float]] = {}
    analyzable_classes = []

    for top_class in top_level_classes:
        if top_class in special_categories: continue

        sub_classes = sub_classes_map.get(top_class, [])
        class_returns = []
        class_risks = []

        if sub_classes:
            for sub in sub_classes:
                if sub in default_expectations:
                    class_returns.append(default_expectations[sub]['return'])
                    class_risks.append(default_expectations[sub]['risk'])
            if class_returns and class_risks:
                top_level_expectations[top_class] = {
                    'return': np.mean(class_returns),
                    'risk': np.mean(class_risks)
                }
                analyzable_classes.append(top_class)
            else:
                 print(f"Warning: No default expectations found for sub-classes of '{top_class}'. Skipping.")
        elif top_class in default_expectations:
             top_level_expectations[top_class] = default_expectations[top_class]
             analyzable_classes.append(top_class)
        else:
            print(f"Warning: No sub-classes or direct defaults found for top-level class '{top_class}'. Skipping.")

    if not analyzable_classes:
         print("Error: Could not determine default expectations for any analyzable top-level class.")
         return None

    correlation_matrix = pd.DataFrame(1.0, index=analyzable_classes, columns=analyzable_classes)
    default_correlations = {
        ('股票', '固定收益'): -0.1, ('股票', '房地产'): 0.4, ('股票', '商品'): 0.1, ('股票', '现金'): 0.0, ('股票', '另类投资'): 0.3,
        ('固定收益', '房地产'): 0.1, ('固定收益', '商品'): -0.2, ('固定收益', '现金'): 0.1, ('固定收益', '另类投资'): 0.1,
        ('房地产', '商品'): 0.1, ('房地产', '现金'): 0.0, ('房地产', '另类投资'): 0.5,
        ('商品', '现金'): -0.1, ('商品', '另类投资'): 0.2,
        ('现金', '另类投资'): 0.0
    }
    for i, asset1 in enumerate(analyzable_classes):
        for j, asset2 in enumerate(analyzable_classes):
            if i < j:
                corr = default_correlations.get((asset1, asset2), default_correlations.get((asset2, asset1), 0.0))
                correlation_matrix.loc[asset1, asset2] = corr
                correlation_matrix.loc[asset2, asset1] = corr

    np.random.seed(42)
    monthly_returns = np.array([top_level_expectations[a]['return']/12 for a in analyzable_classes])
    monthly_stds = np.array([top_level_expectations[a]['risk']/np.sqrt(12) for a in analyzable_classes])
    diag_std = np.diag(monthly_stds)
    try:
        corr_values = correlation_matrix.astype(float).values
        cov_matrix = diag_std @ corr_values @ diag_std
    except Exception as e:
        print(f"Error calculating covariance matrix: {e}")
        return None

    try:
        simulated_returns = np.random.multivariate_normal(monthly_returns, cov_matrix, simulation_months)
    except ValueError as e:
         print(f"Error generating multivariate normal returns: {e}")
         jitter = 1e-6
         cov_matrix_adjusted = cov_matrix + np.eye(cov_matrix.shape[0]) * jitter
         print("Attempting generation with jitter added to covariance matrix diagonal.")
         try:
              simulated_returns = np.random.multivariate_normal(monthly_returns, cov_matrix_adjusted, simulation_months)
              print("Successfully generated returns with jitter.")
         except ValueError as e_jitter:
              print(f"Still failed with jitter: {e_jitter}")
              return None
         if 'simulated_returns' not in locals(): return None

    end_date = pd.Timestamp.today().normalize()
    date_index = pd.date_range(end=end_date, periods=simulation_months, freq='ME')
    returns_df = pd.DataFrame(simulated_returns, index=date_index, columns=analyzable_classes)

    if debug_mode:
        print(f"\nGenerated {simulation_months} months of simulated returns for {len(analyzable_classes)} classes.")
        print("Target Annual Expectations Used:")
        for asset in analyzable_classes:
            print(f"  {asset}: Return={top_level_expectations[asset]['return']:.1%}, Risk={top_level_expectations[asset]['risk']:.1%}")

    print("Finished generating default returns data.")
    return returns_df
