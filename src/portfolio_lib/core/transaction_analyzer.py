# portfolio_lib/core/transaction_analyzer.py
"""
Module for analyzing transaction data to compute historical returns.
Uses transactions_df from DataManager to calculate more precise return metrics.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional
from pandas.tseries.offsets import MonthEnd


def calculate_returns_from_transactions(
    transactions_df: pd.DataFrame,
    holdings_df: pd.DataFrame,
    debug: bool = False
) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
    """
    Calculates historical returns using transaction data and holdings snapshots.
    
    Args:
        transactions_df: DataFrame containing transaction history from DataManager.
        holdings_df: DataFrame containing holdings snapshots from DataManager.
        debug: Whether to print debugging information.
        
    Returns:
        A tuple containing:
        - DataFrame: Monthly returns aggregated by top-level asset class (or None if failed).
        - Dict: Data quality assessment results.
    """
    print("\nCalculating Historical Returns from Transactions...")
    
    # Initialize data quality assessment
    data_quality = {
        'sufficient_for_mpt': False,
        'months_of_data': 0,
        'assets_with_returns': 0,
        'data_density_pct': 0.0,
        'num_assets': 0,
        'completeness_pct': 0.0,
        'message': '',
        'details': {}
    }
    
    if transactions_df is None or transactions_df.empty:
        data_quality['message'] = "No transaction data available"
        return None, data_quality
    
    if holdings_df is None or holdings_df.empty:
        data_quality['message'] = "No holdings data available"
        return None, data_quality
    
    try:
        # Enhanced debugging - Input data validation
        if debug:
            print(f"[DEBUG] transactions_df shape: {transactions_df.shape}")
            print(f"[DEBUG] transactions_df columns: {transactions_df.columns.tolist()}")
            print(f"[DEBUG] holdings_df shape: {holdings_df.shape}")
            print(f"[DEBUG] holdings_df columns: {holdings_df.columns.tolist()}")
            if isinstance(holdings_df.index, pd.MultiIndex):
                print(f"[DEBUG] holdings_df index names: {holdings_df.index.names}")
        
        # Ensure both DataFrames have DatetimeIndex
        if not isinstance(transactions_df.index, pd.DatetimeIndex):
            if 'Transaction_Date' in transactions_df.columns:
                transactions_df = transactions_df.set_index('Transaction_Date')
                if debug:
                    print("[DEBUG] Set transactions_df index to Transaction_Date")
            else:
                data_quality['message'] = "Transaction data has no date index"
                return None, data_quality
        
        # Get all unique snapshot dates from holdings_df
        if isinstance(holdings_df.index, pd.MultiIndex):
            snapshot_dates = holdings_df.index.get_level_values('Snapshot_Date').unique()
            if len(snapshot_dates) < 2:
                data_quality['message'] = f"Insufficient holdings snapshots: {len(snapshot_dates)}"
                return None, data_quality
            if debug:
                print(f"[DEBUG] Found {len(snapshot_dates)} unique snapshot dates")
                print(f"[DEBUG] First and last snapshot dates: {min(snapshot_dates)} to {max(snapshot_dates)}")
        else:
            data_quality['message'] = "Holdings data does not have expected MultiIndex format"
            return None, data_quality
        
        # 1. Group transactions by asset and process them chronologically
        assets = set()
        if isinstance(holdings_df.index, pd.MultiIndex):
            # Extract unique Asset_IDs from holdings_df
            latest_date = max(snapshot_dates)
            try:
                latest_holdings = holdings_df.xs(latest_date, level='Snapshot_Date')
                if isinstance(latest_holdings.index, pd.Index):
                    assets.update(latest_holdings.index.tolist())
                    if debug:
                        print(f"[DEBUG] Extracted {len(latest_holdings.index)} assets from latest holdings")
            except Exception as e:
                print(f"Warning: Could not extract assets from latest holdings: {e}")
        
        # Extract unique Asset_IDs from transactions_df
        if 'Asset_ID' in transactions_df.columns:
            new_assets = set(transactions_df['Asset_ID'].unique())
            assets.update(new_assets)
            if debug:
                print(f"[DEBUG] Extracted {len(new_assets)} unique assets from transactions")
        
        if not assets:
            data_quality['message'] = "Could not identify assets from data"
            return None, data_quality
        
        if debug:
            print(f"[DEBUG] Total unique assets identified: {len(assets)}")
        
        # 2. For each asset, calculate monthly returns using holdings and transactions
        # Sort by date and process transactions
        transactions_df = transactions_df.sort_index()
        
        # Extract transaction months and holding snapshot months
        transaction_months = pd.Series(transactions_df.index).dt.to_period('M').unique()
        snapshot_months = pd.Series(snapshot_dates).dt.to_period('M').unique()
        
        # Combine all months to create a full timeline
        all_months = sorted(set(transaction_months) | set(snapshot_months))
        monthly_index = pd.PeriodIndex(all_months, freq='M').to_timestamp() + MonthEnd(0)
        
        if debug:
            print(f"[DEBUG] Timeline spans {len(all_months)} months from {all_months[0]} to {all_months[-1]}")
        
        # Prepare returns DataFrame (will be populated with monthly returns by asset)
        asset_returns = pd.DataFrame(index=monthly_index)
        asset_processing_stats = {'processed': 0, 'skipped': 0, 'returns_calculated': 0}
        
        # Process each asset
        for asset_id in assets:
            # Get transactions for this asset
            if 'Asset_ID' in transactions_df.columns:
                asset_transactions = transactions_df[transactions_df['Asset_ID'] == asset_id]
                if debug and len(asset_transactions) > 0:
                    print(f"[DEBUG] Asset {asset_id}: found {len(asset_transactions)} transactions")
            else:
                # Skip this asset if we can't identify its transactions
                asset_processing_stats['skipped'] += 1
                continue
                
            # Calculate returns for this asset
            try:
                # Extract holdings values at each snapshot
                asset_values = {}
                holdings_found = 0
                
                for snapshot_date in snapshot_dates:
                    try:
                        if isinstance(holdings_df.index, pd.MultiIndex):
                            # Try to get the asset from this snapshot
                            try:
                                asset_value = holdings_df.xs((snapshot_date, asset_id), level=['Snapshot_Date', 'Asset_ID'])['Market_Value_CNY']
                                # Check if asset_value is a Series or scalar and convert to scalar if needed
                                if isinstance(asset_value, pd.Series):
                                    if len(asset_value) > 0:
                                        asset_value = asset_value.iloc[0]  # Get the first value if it's a Series
                                    else:
                                        if debug:
                                            print(f"[DEBUG] Skipping empty Series for {asset_id} at {snapshot_date}")
                                        continue  # Skip if Series is empty
                                
                                # Ensure we have a valid numeric value
                                if pd.isna(asset_value) or not np.isfinite(asset_value):
                                    if debug:
                                        print(f"[DEBUG] Skipping non-finite value for {asset_id} at {snapshot_date}: {asset_value}")
                                    continue
                                
                                # FIX: Actually store the value in the dict!
                                asset_values[snapshot_date] = asset_value
                                holdings_found += 1
                                
                            except KeyError:
                                # Asset might not exist at this snapshot date
                                pass
                    except Exception as e:
                        print(f"Error processing holdings for {asset_id} at {snapshot_date}: {e}")
                
                if debug:
                    print(f"[DEBUG] Asset {asset_id}: found {holdings_found} holdings snapshots")
                
                # If we have enough snapshot values, calculate simple returns
                if len(asset_values) >= 2:
                    dates = sorted(asset_values.keys())
                    returns_periods = 0
                    
                    for i in range(1, len(dates)):
                        start_date = dates[i-1]
                        end_date = dates[i]
                        start_value = asset_values[start_date]
                        end_value = asset_values[end_date]
                        
                        # Get all transactions between these dates
                        period_transactions = asset_transactions[
                            (asset_transactions.index > start_date) & 
                            (asset_transactions.index <= end_date)
                        ]
                        
                        # Improved cash flow calculation
                        cash_flow = 0
                        if not period_transactions.empty and 'Amount_Net_CNY' in period_transactions.columns:
                            # Ensure numeric conversion, handle NaNs, then sum
                            try:
                                cash_flow = pd.to_numeric(
                                    period_transactions['Amount_Net_CNY'], 
                                    errors='coerce'
                                ).fillna(0).sum()
                            except Exception as e:
                                print(f"Error calculating cash flow for {asset_id}: {e}")
                                if debug:
                                    print(f"[DEBUG] Period transactions data: {period_transactions['Amount_Net_CNY'].head()}")
                                cash_flow = 0
                        
                        # Ensure all values are scalar
                        if isinstance(start_value, pd.Series):
                            if len(start_value) > 0:
                                start_value = start_value.iloc[0]
                            else:
                                if debug:
                                    print(f"[DEBUG] Empty start_value Series for {asset_id} between {start_date} and {end_date}")
                                continue
                                
                        if isinstance(end_value, pd.Series):
                            if len(end_value) > 0:
                                end_value = end_value.iloc[0]
                            else:
                                if debug:
                                    print(f"[DEBUG] Empty end_value Series for {asset_id} between {start_date} and {end_date}")
                                continue
                        
                        # Check for valid numeric values
                        if pd.isna(start_value) or pd.isna(end_value) or not np.isfinite(start_value) or not np.isfinite(end_value):
                            if debug:
                                print(f"[DEBUG] Non-finite values detected: start={start_value}, end={end_value}")
                            continue
                            
                        # Safer Modified Dietz calculation
                        if abs(start_value) > 1e-6:  # Avoid division by zero
                            # Calculate denominator first to check for very small values
                            dietz_denominator = start_value + cash_flow/2
                            
                            if abs(dietz_denominator) < 1e-9:  # Near-zero denominator
                                if debug:
                                    print(f"[DEBUG] Near-zero denominator for {asset_id} between {start_date} and {end_date}")
                                continue
                            
                            # Modified Dietz formula: (End_Value - Start_Value - Cash_Flow) / (Start_Value + Cash_Flow/2)
                            period_return = (end_value - start_value - cash_flow) / dietz_denominator
                            
                            # Convert to monthly return
                            months_between = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
                            if months_between > 0:
                                # Safer power calculation
                                base_for_power = 1 + period_return
                                
                                if base_for_power <= 0 and months_between > 1:
                                    # Can't take fractional root of negative number
                                    if debug:
                                        print(f"[DEBUG] Invalid base {base_for_power} for power calculation for {asset_id}")
                                    monthly_return = np.nan
                                else:
                                    try:
                                        monthly_return = np.power(base_for_power, 1/months_between) - 1
                                        if not np.isfinite(monthly_return):  # Check for inf/nan
                                            if debug:
                                                print(f"[DEBUG] Non-finite monthly return for {asset_id}: {monthly_return}")
                                            monthly_return = np.nan
                                    except Exception as calc_err:
                                        if debug:
                                            print(f"[DEBUG] Error in power calculation: {calc_err}")
                                        monthly_return = np.nan
                                
                                # Store the monthly return for each month in this period if it's valid
                                if np.isfinite(monthly_return):
                                    current_date = start_date + MonthEnd(1)
                                    while current_date <= end_date:
                                        return_date = pd.Timestamp(current_date.year, current_date.month, current_date.day)
                                        if return_date in asset_returns.index:
                                            asset_returns.loc[return_date, asset_id] = monthly_return
                                            returns_periods += 1
                                        current_date = current_date + MonthEnd(1)
                    
                    if returns_periods > 0:
                        asset_processing_stats['returns_calculated'] += 1
                        if debug:
                            print(f"[DEBUG] Asset {asset_id}: calculated returns for {returns_periods} periods")
                    else:
                        if debug:
                            print(f"[DEBUG] Asset {asset_id}: no valid returns calculated")
                else:
                    if debug:
                        print(f"[DEBUG] Asset {asset_id}: insufficient holdings data, need at least 2 snapshots")
                
                asset_processing_stats['processed'] += 1
            
            except Exception as e:
                print(f"Error calculating returns for asset {asset_id}: {e}")
                import traceback
                if debug:
                    print(traceback.format_exc())
                asset_processing_stats['skipped'] += 1
        
        # Print asset processing statistics
        print(f"Asset processing summary: {asset_processing_stats['processed']} processed, "
              f"{asset_processing_stats['returns_calculated']} with returns calculated, "
              f"{asset_processing_stats['skipped']} skipped")
              
        # Check if any returns were calculated
        if asset_returns.empty or asset_returns.count().sum() == 0:
            print("No valid returns were calculated for any asset")
            
            # If we have insufficient snapshot dates, explain this to the user
            if len(snapshot_dates) < 3:
                days_between = (max(snapshot_dates) - min(snapshot_dates)).days
                if days_between < 30:
                    data_quality['message'] = f"Insufficient time between snapshots: only {days_between} days between {min(snapshot_dates).date()} and {max(snapshot_dates).date()}. Need at least monthly data."
                else:
                    data_quality['message'] = f"Only {len(snapshot_dates)} holdings snapshots available. Need at least 3 for meaningful return calculations."
            else:
                data_quality['message'] = "Could not calculate returns from transaction data"
            
            # Add more details to help debugging
            data_quality['details'] = {
                'snapshot_dates': [str(d.date()) for d in sorted(snapshot_dates)],
                'num_assets_processed': asset_processing_stats['processed'],
                'assets_with_snapshots': {}
            }
            
            # Sample a few assets to show their snapshot counts
            sample_size = min(5, len(assets))
            sample_assets = list(assets)[:sample_size]
            
            for asset_id in sample_assets:
                asset_snapshots = 0
                for snapshot_date in snapshot_dates:
                    try:
                        if isinstance(holdings_df.index, pd.MultiIndex):
                            if (snapshot_date, asset_id) in holdings_df.index:
                                asset_snapshots += 1
                    except Exception:
                        pass
                data_quality['details']['assets_with_snapshots'][asset_id] = asset_snapshots
            
            return None, data_quality
        
        # Print asset returns statistics before mapping
        if debug:
            print("[DEBUG] Raw asset_returns before mapping:")
            print(f"[DEBUG] Shape: {asset_returns.shape}")
            print(f"[DEBUG] Non-NaN counts per column:\n{asset_returns.count()}")
            print(f"[DEBUG] Is entirely NaN? {asset_returns.isnull().all().all()}")
            print("[DEBUG] Average monthly returns per asset:")
            for col in asset_returns.columns:
                avg_return = asset_returns[col].mean()
                count = asset_returns[col].count()
                print(f"  {col}: {avg_return:.4f} ({count} non-null values)")
        
        # 3. Map assets to their top-level categories and aggregate returns
        from .asset_mapper import _map_asset_to_top_class_internal, initialize_mapper_taxonomy
        
        # Initialize taxonomy if not already done
        try:
            import yaml
            import os
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config', 'asset_taxonomy.yaml')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    taxonomy = yaml.safe_load(f)
                initialize_mapper_taxonomy(taxonomy)
                if debug:
                    print(f"[DEBUG] Initialized asset taxonomy from {config_path}")
        except Exception as e:
            print(f"Warning: Could not initialize taxonomy: {e}")
        
        asset_category_map = {}
        
        for asset_id in asset_returns.columns:
            try:
                category = _map_asset_to_top_class_internal(asset_id)
                asset_category_map[asset_id] = category
                if debug:
                    print(f"[DEBUG] Mapped asset {asset_id} -> category '{category}'")
            except Exception as e:
                print(f"Error mapping asset {asset_id} to category: {e}")
                # Use a default category for unmapped assets
                asset_category_map[asset_id] = '其他'
                if debug:
                    print(f"[DEBUG] Using default category '其他' for {asset_id}")
        
        # Group returns by category
        category_returns = pd.DataFrame(index=asset_returns.index)
        category_counts = {}
        
        for category in set(asset_category_map.values()):
            # Get assets in this category
            category_assets = [asset for asset, cat in asset_category_map.items() if cat == category]
            category_counts[category] = len(category_assets)
            
            if category_assets:
                # Get the subset of asset returns for this category
                category_data = asset_returns[category_assets]
                
                # Count non-NaN values per date for this category
                valid_counts = category_data.count(axis=1)
                
                if debug:
                    print(f"[DEBUG] Category '{category}' has {len(category_assets)} assets")
                    print(f"[DEBUG] Category '{category}' non-null values by date: min={valid_counts.min()}, "
                          f"max={valid_counts.max()}, mean={valid_counts.mean():.1f}")
                
                # Average returns across all assets in this category
                try:
                    category_returns[category] = category_data.mean(axis=1)
                    if debug:
                        print(f"[DEBUG] Category '{category}' avg return: "
                              f"{category_returns[category].mean():.4f} over {category_returns[category].count()} periods")
                except Exception as e:
                    print(f"Error calculating category returns for {category}: {e}")
        
        # Print category statistics
        if debug:
            print(f"[DEBUG] Category counts: {category_counts}")
            print(f"[DEBUG] Category returns shape: {category_returns.shape}")
            print(f"[DEBUG] Non-null counts per category:\n{category_returns.count()}")
        
        # 4. Fill in missing values and finalize
        # Forward fill (and then backward fill) to handle missing data
        returns_df = category_returns.ffill().bfill()
        
        if debug:
            print(f"[DEBUG] Final returns_df shape after ffill/bfill: {returns_df.shape}")
            print(f"[DEBUG] Non-null counts in final returns_df:\n{returns_df.count()}")
        
        # Calculate data quality metrics
        total_cells = returns_df.shape[0] * returns_df.shape[1]
        non_na_cells = returns_df.count().sum()
        
        data_quality['months_of_data'] = len(returns_df)
        data_quality['assets_with_returns'] = returns_df.columns.size
        data_quality['num_assets'] = returns_df.columns.size
        
        if total_cells > 0:
            data_quality['data_density_pct'] = non_na_cells / total_cells
            data_quality['completeness_pct'] = min(1.0, returns_df.count().min() / len(returns_df)) if len(returns_df) > 0 else 0
        
        # Check if data is sufficient for MPT
        min_months = 12  # Require at least 12 months of data
        min_assets = 3   # Require at least 3 asset classes
        min_density = 0.7  # Require at least 70% data density
        
        is_sufficient = (
            data_quality['months_of_data'] >= min_months and
            data_quality['assets_with_returns'] >= min_assets and
            data_quality['data_density_pct'] >= min_density
        )
        
        data_quality['sufficient_for_mpt'] = is_sufficient
        
        if is_sufficient:
            data_quality['message'] = f"Data suitable for MPT analysis: {data_quality['months_of_data']} months, {data_quality['assets_with_returns']} assets"
        else:
            data_quality['message'] = "Insufficient data quality for reliable MPT analysis"
            reasons = []
            if data_quality['months_of_data'] < min_months:
                reasons.append(f"only {data_quality['months_of_data']} months (need {min_months})")
            if data_quality['assets_with_returns'] < min_assets:
                reasons.append(f"only {data_quality['assets_with_returns']} assets (need {min_assets})")
            if data_quality['data_density_pct'] < min_density:
                reasons.append(f"only {data_quality['data_density_pct']:.1%} data density (need {min_density:.1%})")
            
            if reasons:
                data_quality['message'] += ": " + ", ".join(reasons)
        
        if debug:
            print("\nData quality assessment:")
            print(f"  Months of data: {data_quality['months_of_data']}")
            print(f"  Asset classes: {data_quality['assets_with_returns']}")
            print(f"  Data density: {data_quality['data_density_pct']:.1%}")
            print(f"  Conclusion: {'Suitable' if data_quality['sufficient_for_mpt'] else 'Insufficient'} for MPT")
        
        return returns_df, data_quality
        
    except Exception as e:
        import traceback
        print(f"Error calculating returns from transactions: {e}")
        print(traceback.format_exc())
        data_quality['message'] = f"Error: {str(e)}"
        return None, data_quality
