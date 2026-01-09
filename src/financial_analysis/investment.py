import pandas as pd
import numpy as np
import logging
# --- Import utils ---
from . import utils # Assuming utils.py is in the same directory
from .performance_calculator import PerformanceCalculator  # Import the new unified calculator

# Configure logging for this module
logger = logging.getLogger(__name__)


# --- analyze_asset_performance function ---
def analyze_asset_performance(holdings_df_mapped: pd.DataFrame, # Expect df with Asset_Class
                             transactions_df: pd.DataFrame,
                             taxonomy_data: dict, # Pass taxonomy for additional context
                             risk_free_rate: float = 0.02) -> dict: # Pass risk-free rate directly
    """
    Analyze performance of assets based on holdings (with Asset_Class) and transactions.
    Prepares cash flows including final market value for XIRR calculation.
    
    Args:
        holdings_df_mapped: DataFrame with holdings data including Asset_Class column
        transactions_df: DataFrame with transaction data  
        taxonomy_data: Asset taxonomy data for additional context
        risk_free_rate: Risk-free rate for Sharpe ratio calculations
    """
    logger.info("Analyzing asset performance (using mapped holdings)...")

    # Validate inputs
    if holdings_df_mapped is None or holdings_df_mapped.empty:
        logger.warning("Mapped Holdings DataFrame is empty. Cannot analyze asset performance.")
        return {'status': 'error', 'reason': 'No mapped holdings data available'}
    if 'Asset_Class' not in holdings_df_mapped.columns:
         logger.error("'Asset_Class' column missing from input holdings_df_mapped.")
         return {'status': 'error', 'reason': "'Asset_Class' column missing"}
    if not isinstance(holdings_df_mapped.index, pd.MultiIndex) or holdings_df_mapped.index.nlevels < 2:
         logger.error("Mapped Holdings DataFrame index is not a valid MultiIndex with at least 2 levels.")
         return {'status': 'error', 'reason': 'Invalid mapped Holdings index'}

    # --- Get latest date and holdings ---
    try:
        date_level_values = holdings_df_mapped.index.get_level_values(0)
        latest_date = date_level_values.max()
        logger.debug(f"Latest holdings date (from index level 0): {latest_date}")
        current_holdings_slice = holdings_df_mapped.xs(latest_date, level=0) # Access by level 0
        current_holdings = current_holdings_slice if isinstance(current_holdings_slice, pd.DataFrame) else current_holdings_slice.to_frame().T
    except Exception as e:
         logger.error(f"Error getting latest holdings from mapped df: {e}", exc_info=True)
         return {'status': 'error', 'reason': f'Error getting latest holdings: {e}'}

    # Check if Market_Value_CNY exists
    if 'Market_Value_CNY' not in current_holdings.columns:
        logger.error("'Market_Value_CNY' column not found in mapped holdings_df.")
        return {'status': 'error', 'reason': 'Missing Market_Value_CNY column'}

    # Calculate total portfolio value
    total_portfolio_value = current_holdings['Market_Value_CNY'].sum()
    if total_portfolio_value == 0:
         logger.warning("Total portfolio value is zero on the latest date.")

    # Calculate asset allocation - Use .loc on a copy
    current_holdings_analysis = current_holdings.copy()
    current_holdings_analysis.loc[:, 'Allocation_Pct'] = (current_holdings_analysis['Market_Value_CNY'] / total_portfolio_value * 100) if total_portfolio_value else 0

    # Calculate asset class allocation (now using the mapped 'Asset_Class')
    asset_class_allocation = {}
    if 'Asset_Class' in current_holdings_analysis.columns:
        asset_class_allocation = current_holdings_analysis.groupby('Asset_Class')['Market_Value_CNY'].sum().to_dict()
        asset_class_allocation = {k: (v / total_portfolio_value * 100) if total_portfolio_value else 0 for k, v in asset_class_allocation.items()}
        logger.info("Class-level allocation calculated.")
    else:
        logger.error("'Asset_Class' column unexpectedly missing after mapping attempt.")


    # --- Prepare for XIRR calculation using PerformanceCalculator ---
    performance_calc = PerformanceCalculator(risk_free_rate=risk_free_rate)
    asset_performances = {}
    portfolio_transaction_dates = [] # Separate lists for transactions only
    portfolio_transaction_flows = [] # Will add the final market value separately
    relevant_txns = pd.DataFrame() # Initialize

    if transactions_df is not None and not transactions_df.empty:
        if not isinstance(transactions_df.index, pd.DatetimeIndex):
             logger.error("Transactions DataFrame index is not DatetimeIndex. Skipping XIRR.")
             transactions_df = None
        else:
             invest_types = ['Buy', 'Sell', 'Dividend', 'Interest']
             relevant_txns = transactions_df[transactions_df['Transaction_Type'].isin(invest_types)].copy()
             if 'Amount_Net' not in relevant_txns.columns:
                  logger.error("'Amount_Net' column missing in transactions. Cannot calculate XIRR.")
                  transactions_df = None # Mark as unusable for XIRR

    # Get unique asset IDs from current holdings index
    try:
        asset_ids = current_holdings_analysis.index.unique().tolist()
    except AttributeError:
         logger.error("Could not get unique asset IDs from current_holdings index.")
         asset_ids = []

    # First, collect all transaction cash flows for the portfolio (without adding market values yet)
    # EXCLUDE Property/Real Estate from XIRR calculation as it distorts liquid portfolio performance
    if transactions_df is not None and not relevant_txns.empty and 'Amount_Net' in relevant_txns.columns:
        # Filter out Property/Real Estate transactions
        non_property_mask = True
        if 'Asset_Class' in relevant_txns.columns:
            non_property_mask = ~relevant_txns['Asset_Class'].isin(['房地产', 'Real_Estate'])
            excluded_count = (~non_property_mask).sum()
            if excluded_count > 0:
                logger.info(f"Excluding {excluded_count} Property/Real Estate transactions from XIRR calculation")
        
        liquid_txns = relevant_txns[non_property_mask]
        
        # Add liquid transactions to portfolio calculation
        portfolio_transaction_dates.extend(liquid_txns.index.tolist())
        portfolio_transaction_flows.extend(liquid_txns['Amount_Net'].tolist())

    # Now process each individual asset using PerformanceCalculator
    for asset_id in asset_ids:
        # Retrieve data for the asset (already includes Asset_Class)
        asset_data = current_holdings_analysis.loc[asset_id]
        if isinstance(asset_data, pd.DataFrame):
            market_value = asset_data['Market_Value_CNY'].sum()
            asset_name = asset_data.iloc[0].get('Asset_Name', asset_id)
            asset_class = asset_data.iloc[0].get('Asset_Class', 'Unknown')
            allocation_pct = asset_data['Allocation_Pct'].sum()
        else:  # It's a Series
            market_value = asset_data.get('Market_Value_CNY', 0)
            asset_name = asset_data.get('Asset_Name', asset_id)
            asset_class = asset_data.get('Asset_Class', 'Unknown')
            allocation_pct = asset_data.get('Allocation_Pct', 0)

        # Use PerformanceCalculator to build cash flows and calculate XIRR
        cash_flow_result = performance_calc.build_cash_flows_for_asset(
            asset_id=asset_id,
            holdings_df=holdings_df_mapped,
            transactions_df=transactions_df,
            latest_date=latest_date
        )
        
        # Extract cash flow data
        total_outflows = cash_flow_result.get('total_outflows', 0.0)
        total_inflows_ex_mv = cash_flow_result.get('total_inflows_ex_mv', 0.0)
        
        # Calculate XIRR using the unified calculator
        if cash_flow_result['status'] in ['success', 'warning'] and cash_flow_result['dates']:
            xirr_result = performance_calc.calculate_xirr(
                dates=cash_flow_result['dates'],
                cash_flows=cash_flow_result['cash_flows'],
                context_id=str(asset_id)
            )
        else:
            xirr_result = {
                'xirr': None, 
                'status': 'skipped', 
                'reason': cash_flow_result.get('reason', 'No cash flow data'),
                'method': None
            }

        # Calculate additional metrics (keeping existing logic for dividends/sells breakdown)
        total_dividends_interest = 0.0
        total_sell_proceeds = 0.0
        
        if transactions_df is not None and not relevant_txns.empty:
            asset_txns = relevant_txns[relevant_txns['Asset_ID'] == asset_id] if 'Asset_ID' in relevant_txns.columns else pd.DataFrame()
            if not asset_txns.empty and 'Transaction_Type' in asset_txns.columns:
                div_mask = asset_txns['Transaction_Type'].isin(['Dividend_Cash', 'Interest']) & (asset_txns['Amount_Net'] > 0)
                sell_mask = asset_txns['Transaction_Type'].isin(['Sell']) & (asset_txns['Amount_Net'] > 0)
                total_dividends_interest = asset_txns.loc[div_mask, 'Amount_Net'].sum() if div_mask.any() else 0.0
                total_sell_proceeds = asset_txns.loc[sell_mask, 'Amount_Net'].sum() if sell_mask.any() else 0.0

        # Store performance data
        # Profit & return metrics
        net_invested = max(total_outflows - total_sell_proceeds - total_dividends_interest, 0)
        unrealized_gain = market_value + total_sell_proceeds + total_dividends_interest - total_outflows
        total_return_pct = (unrealized_gain / total_outflows * 100.0) if total_outflows > 1e-9 else None

        asset_performances[asset_id] = {
            'Asset_Name': asset_name,
            'Asset_Class': asset_class,  # Use the mapped class
            'Market_Value_CNY': market_value,
            'Allocation_Pct': allocation_pct,
            'XIRR': xirr_result.get('xirr'),
            'XIRR_Status': xirr_result.get('status'),
            'XIRR_Method': xirr_result.get('method'),
            'XIRR_Reason': xirr_result.get('reason'),
            'Excess_Return': (xirr_result.get('xirr', 0) - risk_free_rate * 100) if xirr_result.get('xirr') is not None else None,
            'Total_Outflows': total_outflows,
            'Total_Inflows_Ex_MV': total_inflows_ex_mv,
            'Total_Dividends_Interest': total_dividends_interest,
            'Total_Sell_Proceeds': total_sell_proceeds,
            'Net_Invested': net_invested,
            'Unrealized_Gain': unrealized_gain,
            'Total_Return_Pct': total_return_pct
        }

    # Calculate overall portfolio XIRR by:
    # 1. Using all transactions collected earlier
    # 2. Adding the TOTAL portfolio market value as one final cash flow
    portfolio_xirr_result = {'xirr': None, 'status': 'skipped', 'reason': 'No cash flows generated for portfolio'}

    # --- Post-process: Cap extreme approximate XIRR values (early-stage unrealized positions) ---
    # Business Rule: If XIRR status == 'approx' and value exceeds cap_threshold, nullify XIRR and record reason
    cap_threshold = 500.0  # percent annualized; adjustable via future config if needed
    for aid, perf in asset_performances.items():
        xirr_val = perf.get('XIRR')
        status_val = perf.get('XIRR_Status')
        if xirr_val is not None and status_val in ('approx',) and xirr_val > cap_threshold:
            perf['XIRR_Capped'] = True
            perf['XIRR_Cap_Reason'] = (
                f"Approximate XIRR {xirr_val:.2f}% exceeds {cap_threshold:.0f}% cap; likely early unrealized position with insufficient mixed cash flows. "
                "Use Total_Return_Pct for current unrealized performance until a realized inflow occurs."
            )
            perf['XIRR_Original'] = xirr_val
            perf['XIRR'] = None  # Hide impractically large approximation
        else:
            perf['XIRR_Capped'] = False
            perf['XIRR_Cap_Reason'] = None
    
    if portfolio_transaction_dates and portfolio_transaction_flows:
        # Sort transactions by date (important for correct XIRR calculation)
        sorted_portfolio_flows = sorted(zip(portfolio_transaction_dates, portfolio_transaction_flows))
        portfolio_dates_sorted = [item[0] for item in sorted_portfolio_flows]
        portfolio_flows_sorted = [item[1] for item in sorted_portfolio_flows]
        
        # Aggregate transactions by date (sum amounts for same date)
        portfolio_cf_series = pd.Series(portfolio_flows_sorted, index=pd.DatetimeIndex(portfolio_dates_sorted))
        portfolio_cf_agg = portfolio_cf_series.groupby(portfolio_cf_series.index).sum()
        
        # Add the final market value as a single cash flow at the latest date
        # Calculate LIQUID portfolio value (excluding Property/Real Estate)
        liquid_portfolio_value = total_portfolio_value
        if 'Asset_Class' in current_holdings_analysis.columns:
            property_mask = current_holdings_analysis['Asset_Class'].isin(['房地产', 'Real_Estate'])
            property_value = current_holdings_analysis.loc[property_mask, 'Market_Value_CNY'].sum()
            liquid_portfolio_value = total_portfolio_value - property_value
            if property_value > 0:
                logger.info(f"Excluding Property value ¥{property_value:,.0f} from XIRR market value. Liquid: ¥{liquid_portfolio_value:,.0f}")
        
        if liquid_portfolio_value > 1e-6:  # Only add if positive
            # Create combined dates and flows lists for XIRR calculation
            final_dates = portfolio_cf_agg.index.tolist()
            final_flows = portfolio_cf_agg.tolist()
            
            # Check if latest_date is already in the dates (avoid duplicates)
            if latest_date not in final_dates:
                final_dates.append(latest_date)
                final_flows.append(liquid_portfolio_value)
            else:
                # Find the index of the latest date and add the market value to any existing value
                idx = final_dates.index(latest_date)
                final_flows[idx] += liquid_portfolio_value
                
            # Calculate portfolio XIRR with combined transactions and final market value
            logger.debug(f"Calculating portfolio XIRR with {len(final_dates)} data points, ending with market value {liquid_portfolio_value:,.2f}")
            portfolio_xirr_result = performance_calc.calculate_xirr(final_dates, final_flows, context_id="Portfolio (Liquid)")
        else:
            logger.warning("Portfolio market value is zero, cannot calculate meaningful XIRR")
            portfolio_xirr_result = {'xirr': None, 'status': 'error', 'reason': 'Portfolio market value is zero or negative'}
    else:
        logger.warning("No transaction data available for portfolio XIRR calculation")
        portfolio_xirr_result = {'xirr': None, 'status': 'skipped', 'reason': 'No transaction data available'}

    # --- Calculate historical allocation ---
    historical_allocation = {}
    try:
        all_dates_ts = pd.to_datetime(holdings_df_mapped.index.get_level_values(0).unique())
        all_dates = sorted(all_dates_ts)
    except Exception as e:
         logger.error(f"Failed to get unique dates from mapped holdings index level 0: {e}")
         all_dates = []

    if len(all_dates) > 1:
        quarterly_dates = pd.date_range(start=all_dates[0], end=all_dates[-1], freq='Q')
        sampled_dates = set()
        for q_date in quarterly_dates:
            closest_dates = [d for d in all_dates if d <= q_date]
            if closest_dates:
                sampled_dates.add(closest_dates[-1])
        if latest_date not in sampled_dates:
            sampled_dates.add(latest_date)
        if all_dates[0] not in sampled_dates:
            sampled_dates.add(all_dates[0])

        for date in sorted(list(sampled_dates)):
            try:
                date_holdings = holdings_df_mapped.xs(date, level=0)  # Access by level 0
            except KeyError:
                continue
            date_total = date_holdings['Market_Value_CNY'].sum()
            if date_total > 0:
                if 'Asset_Class' in date_holdings.columns:
                    class_alloc = date_holdings.groupby('Asset_Class')['Market_Value_CNY'].sum().to_dict()
                    class_alloc = {k: (v / date_total * 100) if date_total else 0 for k, v in class_alloc.items()}
                else:
                    class_alloc = {}
                historical_allocation[date] = {'Total_Value': date_total, 'Class_Allocation': class_alloc}
            else:
                historical_allocation[date] = {'Total_Value': 0, 'Class_Allocation': {}}


    # Return comprehensive results
    results = {
        'latest_date': latest_date,
        'total_portfolio_value': total_portfolio_value,
        'asset_class_allocation': asset_class_allocation, # Now calculated using mapped class
        'asset_performances': asset_performances,
        'portfolio_xirr': portfolio_xirr_result.get('xirr'),  # Just return the XIRR value
        'portfolio_xirr_details': portfolio_xirr_result,      # Store full result dict for debugging
        'historical_allocation': historical_allocation,
        'risk_free_rate': risk_free_rate,
        'status': 'success'
    }

    logger.info("Asset performance analysis complete.")
    return results

# --- calculate_portfolio_metrics function (UPDATED) ---
def calculate_portfolio_metrics(holdings_df: pd.DataFrame, window: str = '1Y', balance_sheet_df: pd.DataFrame = None) -> dict:
    """
    Calculate portfolio risk/return metrics.
    Now supports fallback to balance sheet data when holdings don't have proper time series.
    """
    logger.info(f"Calculating portfolio metrics for {window} window...")
    
    if holdings_df is None or holdings_df.empty:
        logger.warning("Holdings DataFrame is empty. Cannot calculate portfolio metrics.")
        return {'status': 'error', 'reason': 'No holdings data available'}
    
    # Debug the structure of the DataFrame to understand what we're working with
    logger.debug(f"Holdings DataFrame shape: {holdings_df.shape}")
    logger.debug(f"Holdings DataFrame index type: {type(holdings_df.index)}")
    logger.debug(f"Holdings DataFrame columns: {holdings_df.columns.tolist()}")
    
    # Check if we have a date column in the index or as a regular column
    date_column_found = False
    all_dates = []
    
    # Try multiple approaches to find dates in the holdings data
    
    # Approach 1: MultiIndex with Date at level 0
    if isinstance(holdings_df.index, pd.MultiIndex):
        logger.debug(f"MultiIndex levels: {holdings_df.index.names}")
        try:
            if 'Date' in holdings_df.index.names:
                date_level = holdings_df.index.names.index('Date')
                all_dates = sorted(pd.to_datetime(holdings_df.index.get_level_values(date_level).unique()))
                date_column_found = True
                logger.debug(f"Found dates in MultiIndex level '{date_level}' (named 'Date')")
            else:
                # If Date isn't named but is at level 0, try level 0
                try:
                    dates_from_level0 = pd.to_datetime(holdings_df.index.get_level_values(0).unique())
                    # Check if these look like dates (no errors and reasonable range)
                    min_date = dates_from_level0.min()
                    max_date = dates_from_level0.max()
                    if pd.notna(min_date) and pd.notna(max_date) and min_date.year > 1900 and max_date.year < 2100:
                        all_dates = sorted(dates_from_level0)
                        date_column_found = True
                        logger.debug(f"Found dates in MultiIndex level 0 (date range: {min_date} to {max_date})")
                except (TypeError, ValueError) as e:
                    logger.debug(f"Level 0 values don't appear to be dates: {e}")
        except Exception as e:
            logger.warning(f"Error trying to extract dates from MultiIndex: {e}")
    
    # Approach 2: DatetimeIndex
    if not date_column_found and isinstance(holdings_df.index, pd.DatetimeIndex):
        all_dates = sorted(holdings_df.index.unique())
        date_column_found = True
        logger.debug(f"Found dates in DatetimeIndex: {len(all_dates)} unique dates")
    
    # Approach 3: Regular 'Date' column
    if not date_column_found and 'Date' in holdings_df.columns:
        all_dates = sorted(pd.to_datetime(holdings_df['Date'].unique()))
        date_column_found = True
        logger.debug(f"Found dates in 'Date' column: {len(all_dates)} unique dates")
    
    # If we still don't have dates, check some common date column variations
    if not date_column_found:
        for date_col in ['date', 'DATE', 'Time', 'time', 'Timestamp', 'timestamp']:
            if date_col in holdings_df.columns:
                try:
                    all_dates = sorted(pd.to_datetime(holdings_df[date_col].unique()))
                    date_column_found = True
                    logger.debug(f"Found dates in '{date_col}' column: {len(all_dates)} unique dates")
                    break
                except Exception:
                    pass
    
    # If we still couldn't find dates, check for balance sheet fallback
    if not date_column_found or not all_dates:
        logger.warning("Could not identify date column in holdings DataFrame. Attempting balance sheet fallback...")
        
        # Try using balance sheet data for portfolio metrics
        if balance_sheet_df is not None and not balance_sheet_df.empty:
            logger.info("Using balance sheet data for portfolio metrics calculation")
            
            # Look for total assets column
            asset_columns = [col for col in balance_sheet_df.columns 
                           if 'Total_Assets' in col or 'Net_Worth' in col]
            
            if asset_columns:
                asset_col = asset_columns[0]  # Use first available column
                portfolio_series = balance_sheet_df[asset_col].dropna()
                
                if len(portfolio_series) >= 2:
                    # Inline calculation for balance sheet metrics
                    logger.info(f"Calculating metrics from balance sheet using {asset_col}")
                    
                    # Filter to window if needed
                    if window != 'All':
                        end_date = portfolio_series.index.max()
                        if window == 'YTD':
                            start_date = pd.Timestamp(year=end_date.year, month=1, day=1)
                        else:
                            try:
                                offset = pd.tseries.frequencies.to_offset(window.replace('M', 'ME').replace('Y','YE'))
                                start_date = end_date - offset
                            except Exception:
                                start_date = end_date - pd.DateOffset(years=1)  # Default to 1 year
                        
                        portfolio_series = portfolio_series[portfolio_series.index >= start_date]
                    
                    if len(portfolio_series) >= 2:
                        # Calculate basic metrics
                        returns = portfolio_series.pct_change().dropna()
                        if len(returns) >= 2:
                            mean_return = returns.mean()
                            std_return = returns.std()
                            
                            # Annualize assuming monthly data
                            annual_return = (1 + mean_return) ** 12 - 1
                            annual_vol = std_return * (12 ** 0.5)
                            risk_free_rate = 0.035
                            sharpe = (annual_return - risk_free_rate) / annual_vol if annual_vol > 0 else 0
                            
                            # Calculate max drawdown
                            cumulative = (1 + returns).cumprod()
                            running_max = cumulative.cummax()
                            drawdown = (cumulative / running_max) - 1
                            max_dd = drawdown.min()
                            
                            return {
                                'start_date': portfolio_series.index.min(),
                                'end_date': portfolio_series.index.max(),
                                'start_value': portfolio_series.iloc[0],
                                'end_value': portfolio_series.iloc[-1],
                                'total_return_pct': ((portfolio_series.iloc[-1] / portfolio_series.iloc[0]) - 1) * 100,
                                'annualized_return_pct': annual_return * 100,
                                'volatility_pct': annual_vol * 100,
                                'sharpe_ratio': sharpe,
                                'max_drawdown_pct': max_dd * 100,
                                'num_data_points': len(portfolio_series),
                                'status': 'success',
                                'data_source': 'balance_sheet'
                            }
                    
                    logger.error("Insufficient balance sheet data after filtering")
                    return {'status': 'error', 'reason': 'Insufficient balance sheet data after window filtering'}
                else:
                    logger.error("Insufficient balance sheet data points for metrics calculation")
                    return {'status': 'error', 'reason': 'Insufficient balance sheet data points'}
            else:
                logger.error("No asset total columns found in balance sheet")
                return {'status': 'error', 'reason': 'No asset total columns in balance sheet'}
        else:
            logger.error("No balance sheet data available for fallback")
            return {'status': 'error', 'reason': 'Date column not found and no balance sheet fallback available'}
    
    # Log the found dates for debugging
    logger.debug(f"Found {len(all_dates)} unique dates from {all_dates[0]} to {all_dates[-1]}")
    
    if len(all_dates) < 2:
        logger.warning("Insufficient time points in holdings data for calculating metrics.")
        
        # Try balance sheet fallback for insufficient holdings data
        if balance_sheet_df is not None and not balance_sheet_df.empty:
            logger.info("Using balance sheet fallback due to insufficient holdings time points")
            asset_columns = [col for col in balance_sheet_df.columns 
                           if 'Total_Assets' in col or 'Net_Worth' in col]
            
            if asset_columns:
                asset_col = asset_columns[0]
                portfolio_series = balance_sheet_df[asset_col].dropna()
                
                if len(portfolio_series) >= 2:
                    # Inline balance sheet calculation for insufficient holdings fallback
                    returns = portfolio_series.pct_change().dropna()
                    if len(returns) >= 2:
                        annual_return = (1 + returns.mean()) ** 12 - 1
                        annual_vol = returns.std() * (12 ** 0.5)
                        sharpe = (annual_return - 0.035) / annual_vol if annual_vol > 0 else 0
                        return {
                            'sharpe_ratio': sharpe,
                            'annualized_return_pct': annual_return * 100,
                            'volatility_pct': annual_vol * 100,
                            'status': 'success',
                            'data_source': 'balance_sheet_fallback'
                        }
                    else:
                        return {'status': 'error', 'reason': 'Insufficient balance sheet returns data'}
        
        return {'status': 'error', 'reason': 'Insufficient time points (found only 1 date)'}

    latest_date = all_dates[-1]
    
    # Determine start date based on window
    start_date = None # Initialize
    if window == 'All':
        start_date = all_dates[0]
    elif window == 'YTD':
        # Year to date - start from beginning of current year
        start_of_year = pd.Timestamp(year=latest_date.year, month=1, day=1)
        # Find the first date in the data that is on or after the start of the year
        dates_in_year = [d for d in all_dates if d >= start_of_year]
        if dates_in_year:
             start_date = min(dates_in_year)
        else: # No data in the current year yet
             logger.warning(f"No holdings data found for YTD calculation (Year {latest_date.year}). Using 'All'.")
             start_date = all_dates[0] # Fallback to 'All'
    else:
        # Handle '1M', '3M', '6M', '1Y', '3Y' etc.
        try:
            offset = pd.tseries.frequencies.to_offset(window.replace('M', 'ME').replace('Y','YE')) # Use MonthEnd/YearEnd
            target_start = latest_date - offset
            # Find the latest date that is still before or equal to the target start date
            potential_starts = [d for d in all_dates if d <= target_start]
            if potential_starts:
                start_date = max(potential_starts)
            else: # If no date is old enough, use the earliest date
                start_date = all_dates[0]
                logger.warning(f"No data points found before target start date for window '{window}'. Using earliest available date: {start_date.date()}")
        except ValueError:
             logger.warning(f"Unrecognized window offset: {window}. Using '1Y' as default.")
             offset = pd.DateOffset(years=1)
             target_start = latest_date - offset
             potential_starts = [d for d in all_dates if d <= target_start]
             start_date = max(potential_starts) if potential_starts else all_dates[0]


    # Filter dates within the selected window
    dates_in_window = [d for d in all_dates if start_date <= d <= latest_date]
    if len(dates_in_window) < 2:
        logger.warning(f"Insufficient data points ({len(dates_in_window)}) in selected window ({start_date.date()} to {latest_date.date()}). Cannot calculate metrics accurately.")
        return {'status': 'error', 'reason': f'Insufficient data points in window {window}'}

    # Calculate portfolio value at each date in the window
    portfolio_values = {}
    for date in dates_in_window:
        try:
            # Handle different DataFrame structures
            if isinstance(holdings_df.index, pd.MultiIndex) and 'Date' in holdings_df.index.names:
                date_level = holdings_df.index.names.index('Date')
                date_holdings = holdings_df.xs(date, level=date_level)
            elif isinstance(holdings_df.index, pd.MultiIndex):
                # Try level 0 if it contains dates but not named 'Date'
                try:
                    date_holdings = holdings_df.xs(date, level=0)
                except Exception as e:
                    logger.debug(f"Could not access date {date} at level 0, trying other approaches: {e}")
                    raise KeyError("Date not at level 0")
            elif isinstance(holdings_df.index, pd.DatetimeIndex):
                date_holdings = holdings_df.loc[date]
                # If only one row is returned, it might be a Series; convert to DataFrame
                if isinstance(date_holdings, pd.Series):
                    date_holdings = pd.DataFrame([date_holdings])
            elif 'Date' in holdings_df.columns:
                date_holdings = holdings_df[holdings_df['Date'] == date]
            else:
                # Try other date columns we might have found earlier
                for date_col in ['date', 'DATE', 'Time', 'time', 'Timestamp', 'timestamp']:
                    if date_col in holdings_df.columns:
                        date_holdings = holdings_df[holdings_df[date_col] == date]
                        break
                else:
                    raise KeyError(f"Cannot find matching rows for date {date}")
            
            # Check if we actually found rows for this date
            if len(date_holdings) == 0:
                logger.warning(f"No holdings found for date {date}")
                continue
            
            # Calculate total market value for this date
            if 'Market_Value_CNY' in date_holdings.columns:
                portfolio_values[date] = date_holdings['Market_Value_CNY'].sum()
                logger.debug(f"Date {date}: Market value = {portfolio_values[date]}")
            else:
                logger.warning(f"'Market_Value_CNY' column not found in holdings for date {date}")
        except Exception as e:
            logger.warning(f"Error calculating portfolio value for date {date}: {e}")
            # Skip this date if we had an error
    
    # Convert to Series for easier calculations
    portfolio_series = pd.Series(portfolio_values).sort_index()
    
    # Check if we have enough valid data points
    if len(portfolio_series) < 2:
        logger.warning(f"Insufficient valid data points for return calculation after filtering. Found {len(portfolio_series)} valid dates.")
        return {'status': 'error', 'reason': f'Insufficient valid data points (found {len(portfolio_series)} dates with valid market values)'}
    
    # Log the actual dates we'll be using for calculations
    logger.info(f"Calculating metrics using {len(portfolio_series)} dates from {portfolio_series.index.min()} to {portfolio_series.index.max()}")
    
    # Calculate period-to-period returns (handle non-uniform time steps)
    # Calculate time difference between points in years
    time_diff_years = portfolio_series.index.to_series().diff().dt.days / 365.25
    # Calculate simple return between points
    point_returns = portfolio_series.pct_change()
    # Drop first NaN value
    point_returns = point_returns.iloc[1:]
    time_diff_years = time_diff_years.iloc[1:]

    # Handle empty returns (happens if all values are identical)
    if point_returns.empty or (point_returns == 0).all():
        logger.warning("No meaningful returns to analyze (all identical values or only one point).")
        return {
            'start_date': start_date, 'end_date': latest_date,
            'start_value': portfolio_series.iloc[0], 'end_value': portfolio_series.iloc[-1],
            'total_return_pct': 0.0, 'annualized_return_pct': 0.0,
            'volatility_pct': 0.0, 'sharpe_ratio': 0.0, 'max_drawdown_pct': 0.0,
            'status': 'warning', 'reason': 'No price changes detected'
        }

    # Calculate metrics
    total_return = (portfolio_series.iloc[-1] / portfolio_series.iloc[0]) - 1

    # Calculate time period in years for annualizing
    actual_start_date = portfolio_series.index.min() # Use actual start date of series
    actual_end_date = portfolio_series.index.max()   # Use actual end date of series
    years = (actual_end_date - actual_start_date).days / 365.25
    if years <= 0:
        years = 1 / 365.25  # Avoid division by zero, represent as 1 day

    # Annualized return (geometric mean)
    annualized_return = (1 + total_return) ** (1 / years) - 1

    # Volatility (standard deviation of period returns, annualized)
    # Need to annualize based on the *average* period length if dates are irregular
    avg_period_years = time_diff_years.mean()
    if avg_period_years > 0:
        annualization_factor = np.sqrt(1 / avg_period_years) # e.g., sqrt(12) for monthly, sqrt(252) for daily approx
    else:
        annualization_factor = 1 # Cannot annualize if no time difference
    volatility = point_returns.std() * annualization_factor

    # Sharpe ratio (assuming risk-free rate of 3.5% unless specified otherwise)
    risk_free_rate = 0.035 # Load from config if available later
    sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility > 0 else np.nan # Use NaN if no volatility

    # Maximum drawdown
    # cumulative_returns = (1 + point_returns).cumprod()  # Unused currently; retain for potential expansion
    # Add initial point for drawdown calculation
    start_nav = pd.Series([1.0], index=[actual_start_date - pd.Timedelta(days=1)]) # Add point before start
    cumulative_nav = pd.concat([start_nav, portfolio_series / portfolio_series.iloc[0]])

    running_max = cumulative_nav.cummax()
    drawdown = (cumulative_nav / running_max) - 1
    max_drawdown = drawdown.min()

    # Return all calculated metrics
    results = {
        'start_date': actual_start_date,
        'end_date': actual_end_date,
        'start_value': portfolio_series.iloc[0],
        'end_value': portfolio_series.iloc[-1],
        'total_return_pct': total_return * 100,
        'annualized_return_pct': annualized_return * 100,
        'volatility_pct': volatility * 100 if pd.notna(volatility) else np.nan,
        'sharpe_ratio': sharpe_ratio if pd.notna(sharpe_ratio) else np.nan,
        'max_drawdown_pct': max_drawdown * 100 if pd.notna(max_drawdown) else np.nan,
        'period_years': years,
        'num_data_points': len(portfolio_series),
        'status': 'success'
    }

    logger.info(f"Portfolio metrics calculation complete for {window} window.")
    return results

# --- analyze_rebalance_needs function (UPDATED to use mapped holdings) ---
def analyze_rebalance_needs(holdings_df_mapped: pd.DataFrame, # Expect df with Asset_Class
                           allocation_thresholds: dict = None) -> dict:
    """Analyze portfolio for rebalancing needs using mapped asset classes.

    Parameters:
        holdings_df_mapped: DataFrame containing latest holdings with an 'Asset_Class' column (MultiIndex with Date, Asset_ID).
        allocation_thresholds: Optional dict with keys 'high_concentration', 'cash_reserve_min', 'cash_reserve_max'.

    Returns:
        Dict summarizing class and asset imbalance information and cash position status.
    """
    logger.info("Analyzing portfolio rebalancing needs (using mapped holdings)...")

    if holdings_df_mapped is None or holdings_df_mapped.empty:
        logger.warning("Mapped Holdings DataFrame is empty. Cannot analyze rebalancing needs.")
        return {'status': 'error', 'reason': 'No mapped holdings data available'}
    if 'Asset_Class' not in holdings_df_mapped.columns:
         logger.error("'Asset_Class' column missing from input holdings_df_mapped for rebalancing.")
         return {'status': 'error', 'reason': "'Asset_Class' column missing"}
    if not isinstance(holdings_df_mapped.index, pd.MultiIndex) or holdings_df_mapped.index.nlevels < 2:
         logger.error("Mapped Holdings DataFrame index is not a valid MultiIndex with at least 2 levels.")
         return {'status': 'error', 'reason': 'Invalid mapped Holdings index'}

    # Use provided thresholds or defaults
    thresholds = allocation_thresholds or {
        'high_concentration': 0.25,
        'cash_reserve_min': 0.05,
        'cash_reserve_max': 0.20
    }

    # Get current holdings
    try:
        date_level_values = holdings_df_mapped.index.get_level_values(0)
        latest_date = date_level_values.max()
        current_holdings_slice = holdings_df_mapped.xs(latest_date, level=0) # Access by level 0
        current_holdings_orig = current_holdings_slice if isinstance(current_holdings_slice, pd.DataFrame) else current_holdings_slice.to_frame().T
    except Exception as e:
         logger.error(f"Error getting latest holdings from mapped df: {e}", exc_info=True)
         return {'status': 'error', 'reason': f'Error getting latest holdings: {e}'}


    total_value = current_holdings_orig['Market_Value_CNY'].sum()
    if total_value == 0:
         logger.warning("Total portfolio value is zero. Cannot analyze rebalancing.")
         return {'status': 'warning', 'reason': 'Total portfolio value is zero'}


    # Calculate current allocation - Use .loc on a copy
    current_holdings = current_holdings_orig.copy()
    current_holdings.loc[:, 'allocation_pct'] = current_holdings['Market_Value_CNY'] / total_value # Use .loc

    # Identify asset classes (using the pre-mapped 'Asset_Class' column)
    class_imbalances = []
    cash_allocation = 0.0 # Default cash allocation
    if 'Asset_Class' in current_holdings.columns:
        class_allocation_series = current_holdings.groupby('Asset_Class')['Market_Value_CNY'].sum() / total_value

    # Check each class allocation (target allocation placeholder removed as unused)

        for asset_class, alloc in class_allocation_series.items():
            # Normalize class name for cash check
            normalized_class = asset_class.lower() if isinstance(asset_class, str) else ''
            if 'cash' in normalized_class or '现金' in normalized_class: # Check for cash-like classes
                cash_allocation = alloc # Store cash allocation percentage
                if alloc < thresholds['cash_reserve_min']:
                    class_imbalances.append({
                        'asset_class': asset_class,
                        'current_allocation': alloc * 100,
                        'target_min': thresholds['cash_reserve_min'] * 100,
                        'recommendation': 'Increase cash position',
                        'adjustment_needed': (thresholds['cash_reserve_min'] - alloc) * total_value
                    })
                elif alloc > thresholds['cash_reserve_max']:
                    class_imbalances.append({
                        'asset_class': asset_class,
                        'current_allocation': alloc * 100,
                        'target_max': thresholds['cash_reserve_max'] * 100,
                        'recommendation': 'Reduce cash position',
                        'adjustment_needed': (alloc - thresholds['cash_reserve_max']) * total_value
                    })
            # Check high concentration for non-cash classes
            elif alloc > thresholds['high_concentration']:
                class_imbalances.append({
                    'asset_class': asset_class,
                    'current_allocation': alloc * 100,
                    'threshold': thresholds['high_concentration'] * 100,
                    'recommendation': 'Consider diversifying',
                    'note': f'Allocation exceeds high concentration threshold ({thresholds["high_concentration"]*100}%)'
                })
    else:
         # This should not happen if mapping worked, but log defensively
         logger.error("'Asset_Class' column missing, cannot perform class-level rebalancing analysis.")


    # Identify individual asset concentration issues
    asset_imbalances = []
    # Iterate through rows safely
    for asset_id, data in current_holdings.iterrows(): # Use the copy with 'allocation_pct'
        allocation = data['allocation_pct']
        if allocation > thresholds['high_concentration']:
            asset_name = data.get('Asset_Name', asset_id)
            asset_imbalances.append({
                'asset_id': asset_id,
                'asset_name': asset_name,
                'current_allocation': allocation * 100,
                'threshold': thresholds['high_concentration'] * 100,
                'recommendation': 'Consider reducing position',
                'note': f'Allocation exceeds high concentration threshold ({thresholds["high_concentration"]*100}%)'
            })

    # Determine cash status based on calculated allocation
    cash_status = 'Adequate'
    if cash_allocation < thresholds['cash_reserve_min']:
        cash_status = 'Low'
    elif cash_allocation > thresholds['cash_reserve_max']:
        cash_status = 'High'

    # Get cash value explicitly for reporting
    cash_value = cash_allocation * total_value

    return {
        'date': latest_date,
        'total_portfolio_value': total_value,
        'cash_value': cash_value,
        'cash_allocation_pct': cash_allocation * 100,
        'cash_status': cash_status,
        'class_imbalances': class_imbalances,
        'asset_imbalances': asset_imbalances,
        'thresholds': thresholds,
        'status': 'success'
    }


# --- run_investment_analysis function (UPDATED) ---
def run_investment_analysis(holdings_df: pd.DataFrame, transactions_df: pd.DataFrame,
                          balance_sheet_df: pd.DataFrame = None, config: dict = None, config_dir: str = None,
                          start_date: pd.Timestamp = None) -> dict:
    """Run comprehensive investment analysis.

    Performs the following steps:
      1. Load taxonomy/config (if provided) and map asset classes.
      2. Compute per-asset performance (allocation, XIRR, profit breakdown).
      3. Calculate portfolio metrics over configured tracking periods.
      4. Assess rebalancing needs versus concentration & cash thresholds.

    Parameters:
        holdings_df: Holdings DataFrame (MultiIndex expected) without 'Asset_Class' prior to mapping.
        transactions_df: Transactions DataFrame indexed by datetime with at least 'Transaction_Type' & 'Amount_Net'.
        balance_sheet_df: Balance sheet DataFrame for Sharpe ratio calculations.
        config: Optional configuration dict (risk_free_rate, tracking_periods, allocation_thresholds).
        config_dir: Optional path to configuration directory for taxonomy loading (backward compatibility).
        start_date: Optional start date for filtering transactions (for 12-month analysis, etc.)

    Returns:
        Dict containing keys: asset_performance, portfolio_metrics, rebalancing, and status flags.
    """
    if start_date:
        logger.info(f"Starting comprehensive investment analysis (filtered from {start_date})...")
    else:
        logger.info("Starting comprehensive investment analysis...")

    results = {}
    taxonomy_data = {} # Initialize

    # --- 1. Load Configs ---
    if config_dir:
        taxonomy_data = utils.load_asset_taxonomy(config_dir)
        if not taxonomy_data:
             logger.error("Failed to load asset taxonomy. Class-level analysis will be limited.")
    
    # Use provided config or create defaults
    if config is None:
        logger.warning("No configuration provided. Using default values.")
        config = {
            'risk_free_rate': 0.02,
            'benchmark_index': 'CSI300',
            'tracking_periods': ['3M', '6M', 'YTD', '1Y', '3Y', 'All'],
            'allocation_thresholds': {
                'high_concentration': 0.25,
                'cash_reserve_min': 0.05,
                'cash_reserve_max': 0.20
            }
        }

    # --- Filter transactions by start_date if provided (for 12-month analysis, etc.) ---
    if start_date is not None and transactions_df is not None and not transactions_df.empty:
        if isinstance(transactions_df.index, pd.DatetimeIndex):
            original_count = len(transactions_df)
            transactions_df = transactions_df[transactions_df.index >= start_date].copy()
            filtered_count = len(transactions_df)
            logger.info(f"Filtered transactions: {original_count} → {filtered_count} (from {start_date})")
        else:
            logger.warning("Cannot filter transactions by start_date: index is not DatetimeIndex")

    # --- 2. Map Asset Class ---
    logger.info("Mapping asset classes to holdings...")
    holdings_df_mapped = utils.map_asset_class(holdings_df, taxonomy_data)
    # Check if mapping was successful (Asset_Class column added)
    if 'Asset_Class' not in holdings_df_mapped.columns:
         logger.error("Failed to add 'Asset_Class' column to holdings DataFrame.")
         # Add a dummy column to prevent errors, but analysis will be limited
         holdings_df_mapped = holdings_df.copy() # Avoid modifying original
         holdings_df_mapped['Asset_Class'] = 'Unknown'

    # --- 3. Asset Performance Analysis ---
    logger.info("Running asset performance analysis...")
    # Pass the mapped holdings dataframe, taxonomy, and config
    performance_results = analyze_asset_performance(
        holdings_df_mapped=holdings_df_mapped,
        transactions_df=transactions_df,
        taxonomy_data=taxonomy_data,
        risk_free_rate=config.get('risk_free_rate', 0.02)
    )
    results['asset_performance'] = performance_results

    # --- 4. Portfolio Metrics for different time periods ---
    logger.info("Calculating portfolio metrics for different time periods...")
    periods = config.get('tracking_periods', ['3M', '6M', 'YTD', '1Y', '3Y', 'All'])

    metrics_by_period = {}
    # Use the mapped holdings_df for metric calculation to ensure we have proper structure
    # This is a key change - using mapped DF which should have consistent structure
    for period in periods:
        period_metrics = calculate_portfolio_metrics(holdings_df_mapped, period, balance_sheet_df)
        metrics_by_period[period] = period_metrics

    results['portfolio_metrics'] = metrics_by_period

    # --- 5. Rebalancing Needs ---
    logger.info("Analyzing rebalancing needs...")
    # Pass the mapped holdings dataframe and allocation thresholds
    rebalance_results = analyze_rebalance_needs(
        holdings_df_mapped, 
        allocation_thresholds=config.get('allocation_thresholds')
    )
    results['rebalancing'] = rebalance_results

    logger.info("Investment analysis complete.")
    return results
