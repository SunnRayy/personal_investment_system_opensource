"""
Dual-Timeframe Metrics Calculator

This module provides functions to calculate portfolio metrics for both
lifetime and trailing 12-month timeframes.

Created: November 5, 2025
Purpose: Support dual-timeframe metrics display in portfolio reports
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional

from .performance_calculator import PerformanceCalculator

logger = logging.getLogger(__name__)


def calculate_12month_xirr(holdings_df: pd.DataFrame,
                           transactions_df: pd.DataFrame,
                           config_dir: str = 'config') -> Dict[str, Any]:
    """
    Calculate portfolio XIRR for trailing 12-month period.
    
    Uses the existing investment analysis infrastructure with date filtering
    to ensure consistent calculation logic.
    
    Args:
        holdings_df: Holdings DataFrame with MultiIndex
        transactions_df: All transactions with DatetimeIndex
        config_dir: Configuration directory path
        
    Returns:
        Dictionary with xirr, status, reason, method keys
    """
    logger.info("Calculating 12-month XIRR...")
    
    if transactions_df is None or transactions_df.empty:
        logger.warning("No transaction data provided for 12-month XIRR")
        return {
            'xirr': None,
            'status': 'warning',
            'reason': 'No transaction data',
            'method': None
        }
    
    # Ensure index is datetime
    if not isinstance(transactions_df.index, pd.DatetimeIndex):
        logger.error("Transactions index is not DatetimeIndex")
        return {
            'xirr': None,
            'status': 'error',
            'reason': 'Invalid transaction index type',
            'method': None
        }
    
    # Calculate 12-month cutoff
    today = datetime.now()
    twelve_months_ago = today - timedelta(days=365)
    start_date = pd.Timestamp(twelve_months_ago)
    
    # Filter to 12-month period
    transactions_12m = transactions_df[transactions_df.index >= start_date]
    
    if transactions_12m.empty:
        logger.warning("No transactions in last 12 months")
        return {
            'xirr': None,
            'status': 'warning',
            'reason': 'No transactions in 12-month period',
            'method': None
        }
    
    logger.info(f"Found {len(transactions_12m)} transactions in last 12 months "
               f"({len(transactions_12m) / len(transactions_df) * 100:.1f}% of total)")
    
    # Use the existing investment analysis with start_date filter
    # This ensures we use the same tested cash flow aggregation logic
    try:
        from . import investment
        
        # Run analysis with date filtering
        results_12m = investment.run_investment_analysis(
            holdings_df=holdings_df,
            transactions_df=transactions_df,  # Pass full dataframe, filtering happens inside
            balance_sheet_df=None,
            config_dir=config_dir,
            start_date=start_date  # This parameter triggers 12-month filtering
        )
        
        # Extract portfolio XIRR from results
        asset_performance = results_12m.get('asset_performance', {})
        portfolio_xirr = asset_performance.get('portfolio_xirr')
        portfolio_xirr_details = asset_performance.get('portfolio_xirr_details', {})
        
        if portfolio_xirr is not None:
            logger.info(f"✓ 12-Month XIRR calculated: {portfolio_xirr:.2f}%")
            return {
                'xirr': portfolio_xirr,
                'status': portfolio_xirr_details.get('status', 'success'),
                'reason': portfolio_xirr_details.get('reason'),
                'method': portfolio_xirr_details.get('method')
            }
        else:
            logger.warning(f"12-Month XIRR calculation returned None: {portfolio_xirr_details.get('reason')}")
            return {
                'xirr': None,
                'status': portfolio_xirr_details.get('status', 'warning'),
                'reason': portfolio_xirr_details.get('reason', 'XIRR calculation returned None'),
                'method': portfolio_xirr_details.get('method')
            }
            
    except Exception as e:
        logger.error(f"Error calculating 12-month XIRR: {e}", exc_info=True)
        return {
            'xirr': None,
            'status': 'error',
            'reason': f'Exception during calculation: {str(e)}',
            'method': None
        }


def calculate_12month_sharpe_ratio(balance_sheet_df: pd.DataFrame,
                                   risk_free_rate: float = 0.02) -> Optional[float]:
    """
    Calculate Sharpe ratio for trailing 12-month period.
    
    Args:
        balance_sheet_df: Balance sheet with Total_Assets_Calc_CNY column
        risk_free_rate: Annual risk-free rate (default: 2%)
        
    Returns:
        Annualized Sharpe ratio or None if calculation fails
    """
    logger.info("Calculating 12-month Sharpe ratio...")
    
    if balance_sheet_df is None or balance_sheet_df.empty:
        logger.warning("No balance sheet data for Sharpe calculation")
        return None
    
    if 'Total_Assets_Calc_CNY' not in balance_sheet_df.columns:
        logger.warning("Total_Assets_Calc_CNY not found in balance sheet")
        return None
    
    # Calculate 12-month cutoff
    today = datetime.now()
    twelve_months_ago = today - timedelta(days=365)
    
    # Filter balance sheet to 12-month period
    balance_12m = balance_sheet_df[balance_sheet_df.index >= twelve_months_ago].copy()
    
    if balance_12m.empty or len(balance_12m) < 2:
        logger.warning(f"Insufficient balance sheet data in 12-month period: {len(balance_12m)} months")
        return None
    
    # Calculate monthly returns
    monthly_returns = balance_12m['Total_Assets_Calc_CNY'].pct_change().dropna()
    
    if len(monthly_returns) < 2:
        logger.warning(f"Insufficient return data points: {len(monthly_returns)}")
        return None
    
    # Annualize returns and volatility
    avg_monthly_return = monthly_returns.mean()
    monthly_std = monthly_returns.std()
    
    if monthly_std == 0:
        logger.warning("Zero volatility in 12-month period")
        return None
    
    # Calculate annualized Sharpe ratio
    annual_return = (1 + avg_monthly_return) ** 12 - 1
    annual_std = monthly_std * np.sqrt(12)
    
    sharpe_ratio = (annual_return - risk_free_rate) / annual_std
    
    logger.info(f"✓ 12-Month Sharpe Ratio calculated: {sharpe_ratio:.2f}")
    logger.info(f"   Data points: {len(monthly_returns)} months")
    logger.info(f"   Annualized return: {annual_return*100:.2f}%")
    logger.info(f"   Annualized volatility: {annual_std*100:.2f}%")
    
    return sharpe_ratio


def calculate_12month_twr(balance_sheet_df: pd.DataFrame, transactions_df: pd.DataFrame = None,
                          holdings_df: pd.DataFrame = None) -> Optional[float]:
    """
    Calculate Time-Weighted Return (TWR) for trailing 12-month period.
    Uses TRANSACTION-BASED calculation for more accurate returns that include
    realized gains from sold/redeemed assets.
    
    Args:
        balance_sheet_df: Balance sheet (used for fallback only)
        transactions_df: All transactions for TWR calculation
        holdings_df: Historical holdings snapshots (required for transaction-based)
        
    Returns:
        12-month TWR percentage or None if calculation fails
    """
    logger.info("Calculating 12-month TWR (transaction-based)...")
    
    # Try transaction-based calculation first (most accurate)
    if transactions_df is not None and holdings_df is not None:
        try:
            from ..portfolio_lib.core.transaction_analyzer import calculate_returns_from_transactions
            
            returns_df, quality = calculate_returns_from_transactions(
                transactions_df, holdings_df, debug=False
            )
            
            if returns_df is not None and '股票' in returns_df.columns:
                # Get last 12 months of equity returns
                last_12m = returns_df['股票'].tail(12).dropna()
                if len(last_12m) >= 6:  # Need at least 6 months
                    # Compound monthly returns to get cumulative
                    cumulative_return = ((1 + last_12m).prod() - 1) * 100
                    logger.info(f"✓ 12-Month TWR (transaction-based, 股票): {cumulative_return:.2f}%")
                    return cumulative_return
                else:
                    logger.warning(f"Insufficient monthly data: only {len(last_12m)} months")
            else:
                logger.warning("Transaction-based calculation returned no 股票 data")
        except Exception as e:
            logger.warning(f"Transaction-based TWR failed: {e}")
    
    # Fallback to Balance Sheet simple return (less accurate)
    logger.info("Falling back to Balance Sheet simple return...")
    if balance_sheet_df is None or balance_sheet_df.empty:
        return None
    
    if 'Asset_Invest_FundA_Value' not in balance_sheet_df.columns:
        return None
    
    from datetime import datetime, timedelta
    today = datetime.now()
    twelve_months_ago = today - timedelta(days=365)
    balance_12m = balance_sheet_df[balance_sheet_df.index >= twelve_months_ago]
    
    if len(balance_12m) < 2:
        return None
    
    start_value = balance_12m['Asset_Invest_FundA_Value'].iloc[0]
    end_value = balance_12m['Asset_Invest_FundA_Value'].iloc[-1]
    
    if start_value > 0:
        simple_twr = ((end_value - start_value) / start_value) * 100
        logger.info(f"✓ 12-Month TWR (fallback, FundA only): {simple_twr:.2f}%")
        return simple_twr
    
    return None
    
    # With transaction data, calculate TWR properly accounting for cash flows
    # Get cash flows in 12-month period
    mask = transactions_df.index >= pd.Timestamp(twelve_months_ago)
    txn_12m = transactions_df[mask].copy()
    
    if txn_12m.empty:
        # No transactions in period, use simple return
        start_value = balance_12m['Total_Assets_Calc_CNY'].iloc[0]
        end_value = balance_12m['Total_Assets_Calc_CNY'].iloc[-1]
        if start_value > 0:
            simple_twr = ((end_value - start_value) / start_value) * 100
            logger.info(f"✓ 12-Month TWR calculated (no txns): {simple_twr:.2f}%")
            return simple_twr
        return None
    
    # For now, use modified Dietz approximation
    # TWR ≈ (Return - (CF * (Days_CF / Total_Days)) / Starting_Value
    start_value = balance_12m['Total_Assets_Calc_CNY'].iloc[0]
    end_value = balance_12m['Total_Assets_Calc_CNY'].iloc[-1]
    
    if start_value <= 0:
        logger.warning("Starting portfolio value is zero or negative")
        return None
    
    total_days = (balance_12m.index[-1] - balance_12m.index[0]).days
    if total_days == 0:
        logger.warning("Zero days in 12-month period")
        return None
    
    # Calculate net cash flows
    net_cf = 0
    # Check for Amount column - could be 'Amount', 'Amount_Net', or 'Amount_Gross'
    amount_col = None
    if 'Amount_Net' in txn_12m.columns:
        amount_col = 'Amount_Net'
    elif 'Amount' in txn_12m.columns:
        amount_col = 'Amount'
    elif 'Amount_Gross' in txn_12m.columns:
        amount_col = 'Amount_Gross'
    
    if amount_col:
        for idx, row in txn_12m.iterrows():
            amount = row.get(amount_col, 0)
            txn_type = row.get('Transaction_Type', '')
            
            # Classify as inflow or outflow
            # Inflows (negative in cash flow convention): Buy, Premium_Payment, RSU_Vest, Interest, Dividend_Cash
            # Outflows (positive in cash flow convention): Sell
            if txn_type in ['Buy', 'Premium_Payment', 'RSU_Vest']:
                net_cf -= amount  # Negative: money added to portfolio
            elif txn_type in ['Sell']:
                net_cf += amount  # Positive: money taken from portfolio
    
    # Modified Dietz: TWR = (Ending - Beginning - Net CF) / (Beginning + weighted CF)
    # Simplified: assume CF at midpoint
    weighted_cf = net_cf * 0.5  # 50% weight (midpoint approximation)
    
    twr_numerator = end_value - start_value - net_cf
    twr_denominator = start_value + weighted_cf
    
    if twr_denominator <= 0:
        logger.warning(f"Invalid denominator for TWR: {twr_denominator}")
        # Fallback to simple return
        twr = ((end_value - start_value) / start_value) * 100
    else:
        twr = (twr_numerator / twr_denominator) * 100
    
    logger.info(f"✓ 12-Month TWR calculated: {twr:.2f}%")
    logger.info(f"   Period: {balance_12m.index[0]} to {balance_12m.index[-1]} ({total_days} days)")
    logger.info(f"   Start value: ¥{start_value:,.2f}, End value: ¥{end_value:,.2f}")
    logger.info(f"   Net cash flows: ¥{net_cf:,.2f}")
    
    return twr


def calculate_12month_twr_by_class(balance_sheet_df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate Time-Weighted Return (TWR) for each asset class over trailing 12 months.
    Uses simple return (no cash flow adjustment) from Balance Sheet columns.
    
    Excludes: Cash, Real Estate, Insurance (non-rebalanceable/non-liquid)
    
    Args:
        balance_sheet_df: Balance sheet with asset value columns
        
    Returns:
        Dictionary of asset class -> TWR percentage
    """
    logger.info("Calculating 12-month TWR by asset class...")
    
    if balance_sheet_df is None or balance_sheet_df.empty:
        logger.warning("No balance sheet data")
        return {}
    
    # Define asset class -> Balance Sheet column mapping
    # Only include true investment assets where returns aren't distorted by deposits:
    # - Equity (CN/HK/US): Market-traded, no regular deposits
    # - Bonds: Part of Schwab holdings (AGG, IEF) - tracked in USFund
    # - Gold: Commodity, minimal new purchases
    # - Crypto: Part of Schwab holdings (FBTC, IBIT, ETHA) - tracked in USFund
    # EXCLUDED: 银行理财, 个人养老金, RSU (returns distorted by deposits/vesting)
    # Note: US Equity includes Bonds and Crypto ETFs in Balance Sheet aggregation
    class_column_map = {
        # Equity
        'CN_Equity': 'Asset_Invest_FundA_Value',               # A股基金
        'US_Securities': 'Asset_Invest_USFund_Value_CNY_FromUSD',  # 美股证券+债券+加密ETF (USD converted)
        # Commodities
        'Gold': 'Asset_Invest_Gold_Value',                     # 黄金
    }
    
    # Calculate 12-month cutoff
    today = datetime.now()
    twelve_months_ago = today - timedelta(days=365)
    
    # Filter to 12-month period
    balance_12m = balance_sheet_df[balance_sheet_df.index >= twelve_months_ago].copy()
    
    if balance_12m.empty or len(balance_12m) < 2:
        logger.warning(f"Insufficient data: {len(balance_12m)} months")
        return {}
    
    results = {}
    total_start = 0
    total_end = 0
    
    for class_name, col_name in class_column_map.items():
        if col_name not in balance_12m.columns:
            logger.debug(f"Column {col_name} not found, skipping {class_name}")
            continue
            
        start_val = balance_12m[col_name].iloc[0]
        end_val = balance_12m[col_name].iloc[-1]
        
        # Skip if no meaningful value
        if pd.isna(start_val) or pd.isna(end_val):
            continue
        if start_val <= 0:
            # Asset didn't exist at start
            if end_val > 0:
                results[class_name] = None  # Can't calculate return
            continue
            
        # Simple return (no cash flow adjustment for now)
        twr = ((end_val - start_val) / start_val) * 100
        results[class_name] = round(twr, 2)
        
        total_start += start_val
        total_end += end_val
        
        logger.info(f"   {class_name}: {twr:+.2f}% (¥{start_val:,.0f} → ¥{end_val:,.0f})")
    
    # Calculate weighted aggregate
    if total_start > 0:
        aggregate_twr = ((total_end - total_start) / total_start) * 100
        results['_aggregate'] = round(aggregate_twr, 2)
        logger.info(f"   Aggregate (liquid assets): {aggregate_twr:+.2f}%")
    
    return results


def calculate_dual_timeframe_metrics(transactions_df: pd.DataFrame,
                                     holdings_df: pd.DataFrame,
                                     balance_sheet_df: pd.DataFrame,
                                     lifetime_xirr: float,
                                     lifetime_sharpe: float,
                                     lifetime_twr: float,
                                     risk_free_rate: float = 0.02,
                                     config_dir: str = 'config') -> Dict[str, Any]:
    """
    Calculate both lifetime and 12-month metrics for comparison.
    
    Args:
        transactions_df: All transactions
        holdings_df: Current holdings (MultiIndex expected)
        balance_sheet_df: Balance sheet history
        lifetime_xirr: Pre-calculated lifetime XIRR
        lifetime_sharpe: Pre-calculated lifetime Sharpe ratio
        lifetime_twr: Pre-calculated lifetime TWR
        risk_free_rate: Risk-free rate for Sharpe calculation
        config_dir: Configuration directory path
        
    Returns:
        Dictionary with lifetime and 12month keys containing metrics
    """
    logger.info("Calculating dual-timeframe metrics...")
    
    # Calculate 12-month metrics
    xirr_12m_result = calculate_12month_xirr(holdings_df, transactions_df, config_dir)
    sharpe_12m = calculate_12month_sharpe_ratio(balance_sheet_df, risk_free_rate)
    twr_12m = calculate_12month_twr(balance_sheet_df, transactions_df, holdings_df)
    
    # Calculate 12-month portfolio growth from balance sheet
    # Simple return: (end - start) / start
    growth_12m = None
    if balance_sheet_df is not None and not balance_sheet_df.empty and 'Total_Assets_Calc_CNY' in balance_sheet_df.columns:
        twelve_months_ago = datetime.now() - timedelta(days=365)
        balance_12m = balance_sheet_df[balance_sheet_df.index >= twelve_months_ago].copy()
        if not balance_12m.empty and len(balance_12m) >= 2:
            start_value = balance_12m['Total_Assets_Calc_CNY'].iloc[0]
            end_value = balance_12m['Total_Assets_Calc_CNY'].iloc[-1]
            if start_value > 0:
                growth_12m = ((end_value - start_value) / start_value) * 100
                logger.info(f"✓ 12-Month Growth calculated: {growth_12m:.2f}%")
    
    # Format values with proper precision
    sharpe_12m_str = f"{sharpe_12m:.2f}" if sharpe_12m is not None else 'N/A'
    twr_12m_str = f"{twr_12m:.2f}" if twr_12m is not None else 'N/A'
    growth_12m_str = f"{growth_12m:.2f}" if growth_12m is not None else 'N/A'
    
    # Compile results
    # Return results in format expected by template
    results = {
        'lifetime': {
            'xirr': str(lifetime_xirr) if lifetime_xirr is not None else 'N/A',
            'sharpe': str(lifetime_sharpe) if lifetime_sharpe is not None else 'N/A',
            'sharpe_ratio': str(lifetime_sharpe) if lifetime_sharpe is not None else 'N/A',  # Alias
            'twr': str(lifetime_twr) if lifetime_twr is not None else 'N/A',
            'portfolio_growth': 'N/A',  # Not available in this function
            'timeframe': 'Lifetime'
        },
        'trailing_12m': {
            'xirr': f"{xirr_12m_result.get('xirr'):.2f}" if isinstance(xirr_12m_result.get('xirr'), (int, float)) else 'N/A',
            'xirr_status': xirr_12m_result.get('status', 'N/A'),
            'sharpe': sharpe_12m_str,
            'sharpe_ratio': sharpe_12m_str,  # Alias
            'twr': twr_12m_str,
            'portfolio_growth': growth_12m_str,
            'timeframe': 'Trailing 12 Months'
        }
    }
    
    logger.info("✅ Dual-timeframe metrics calculated successfully")
    logger.info(f"   Lifetime XIRR: {lifetime_xirr} | 12-Month XIRR: {xirr_12m_result.get('xirr', 'N/A')}")
    logger.info(f"   Lifetime Sharpe: {lifetime_sharpe} | 12-Month Sharpe: {sharpe_12m if sharpe_12m else 'N/A'}")
    logger.info(f"   Lifetime TWR: {lifetime_twr} | 12-Month TWR: {twr_12m if twr_12m else 'N/A'}")
    
    return results
