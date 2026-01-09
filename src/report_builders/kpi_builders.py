"""
KPI Builders Module - Key Performance Indicator calculations for reports.

This module contains functions for calculating top-level KPIs, individual asset
performance metrics, and gains analysis data.
"""

import logging
import pandas as pd
from typing import Dict, List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.data_manager.manager import DataManager
    from src.portfolio_lib.taxonomy_manager import TaxonomyManager

logger = logging.getLogger(__name__)


def build_gains_analysis_data(
    data_manager: 'DataManager',
    current_holdings: Any
) -> Dict[str, Any]:
    """
    Build asset-level gains breakdown for enhanced tables.
    
    Phase 5 Task 5.1: Enhanced with cost_basis and gain_percentage fields.
    
    Args:
        data_manager: DataManager instance
        current_holdings: Current holdings DataFrame
        
    Returns:
        Dictionary mapping asset names to their gains data including:
        - realized_gains: Gains from sold assets
        - unrealized_gains: Paper gains on held assets
        - total_gains: Sum of realized + unrealized
        - cost_basis: Total amount invested (NEW)
        - gain_percentage: Return percentage (NEW)
        - is_currently_held: Whether asset is in current portfolio
    """
    asset_gains_data = {}
    try:
        from src.financial_analysis.cost_basis import calculate_cost_basis_for_portfolio
        
        # Build current prices dictionary using Asset_ID (same logic as portfolio-level)
        current_prices = {}
        if current_holdings is not None and not current_holdings.empty:
            for idx, holding in current_holdings.iterrows():
                # Extract Asset_ID from MultiIndex
                if hasattr(idx, '__len__') and len(idx) >= 2:
                    asset_id = idx[1]  # Asset_ID from MultiIndex
                else:
                    asset_id = holding.get('Asset_ID')
                
                # Use Asset_ID directly without stripping .0 suffix
                # The cost basis calculation should handle ID types consistently.
                
                quantity = holding.get('Quantity', 0)
                
                # FIXED: Use Market_Value_CNY since transactions are now converted to CNY
                # at transaction processing level in cost_basis._process_single_transaction
                market_value_cny = holding.get('Market_Value_CNY', 0)
                
                if asset_id and quantity > 0 and market_value_cny > 0:
                    # Use Asset_ID as key for consistency with cost basis calculation
                    # Price is in CNY (converted from USD if necessary)
                    # Normalize ID for current_prices lookup consistency
                    h_id_str = str(asset_id)
                    if h_id_str.endswith('.0'):
                        h_id_str = h_id_str[:-2]
                    
                    if h_id_str.isdigit():
                        h_id_norm = str(int(h_id_str))
                    else:
                        h_id_norm = h_id_str
                    
                    current_prices[h_id_norm] = market_value_cny / quantity
                    # Robustness: also set integer key if applicable
                    if h_id_norm.isdigit():
                         current_prices[int(h_id_norm)] = current_prices[h_id_norm]
        
        # Get transactions and calculate cost basis for each asset
        transactions = data_manager.get_transactions()
        if transactions is not None and not transactions.empty:
            # FIX: Ensure DatetimeIndex for cost basis calculation
            if 'Transaction_Date' in transactions.columns and not isinstance(transactions.index, pd.DatetimeIndex):
                try:
                     transactions = transactions.copy()
                     transactions['Transaction_Date'] = pd.to_datetime(transactions['Transaction_Date'])
                     transactions.set_index('Transaction_Date', inplace=True)
                except Exception as e:
                     logger.warning(f"Could not set Transaction_Date index in kpi_builders: {e}")

            # Calculate cost basis for all assets
            cost_basis_results = calculate_cost_basis_for_portfolio(transactions, current_prices)
            
            # Build asset gains mapping using Asset_Name as key
            for asset_id, cb_data in cost_basis_results.items():
                # Skip insurance assets
                if 'Ins_' in str(asset_id):
                    continue
                    
                # Get asset name and currency from transactions/holdings
                # FIX: Use string matching for Asset ID
                str_asset_id = str(asset_id)
                if 'Asset_ID' in transactions.columns:
                     asset_mask = transactions['Asset_ID'].astype(str) == str_asset_id
                     asset_transactions = transactions[asset_mask]
                else:
                     asset_transactions = pd.DataFrame()

                if not asset_transactions.empty:
                    asset_name = asset_transactions.iloc[0].get('Asset_Name', str(asset_id))
                    
                    # Determine if currently held by checking Asset_ID in holdings
                    is_held = False
                    if current_holdings is not None:
                        # Get all held asset IDs
                        if hasattr(current_holdings.index, 'levels'):
                            held_ids = set(current_holdings.index.get_level_values('Asset_ID'))
                        else:
                            held_ids = set(current_holdings['Asset_ID'].values if 'Asset_ID' in current_holdings.columns else [])
                        
                        # Create a map for quick lookup of holdings by asset_id
                        holdings_map = {}
                        for idx, holding in current_holdings.iterrows():
                            if hasattr(idx, '__len__') and len(idx) >= 2:
                                h_asset_id = idx[1]
                            else:
                                h_asset_id = holding.get('Asset_ID')
                            
                            # Normalize holding ID for comparison
                            # 1. Convert to string
                            # 2. Strip .0 suffix
                            # 3. If digit, convert to int then string to remove leading zeros (001856 -> 1856)
                            h_id_str = str(h_asset_id)
                            if h_id_str.endswith('.0'):
                                h_id_str = h_id_str[:-2]
                            
                            if h_id_str.isdigit():
                                h_id_norm = str(int(h_id_str))
                            else:
                                h_id_norm = h_id_str
                            
                            holdings_map[h_id_norm] = {
                                'quantity': holding.get('Quantity', 0),
                                'market_value': holding.get('Market_Value_CNY', 0)
                            }
                            
                        # Normalize target asset ID
                        target_id_str = str(asset_id)
                        if target_id_str.endswith('.0'):
                           target_id_str = target_id_str[:-2]
                        if target_id_str.isdigit():
                           target_id_norm = str(int(target_id_str))
                        else:
                           target_id_norm = target_id_str

                        # Check if currently held (quantity > 0)
                        if target_id_norm in holdings_map:
                            is_held = holdings_map[target_id_norm]['quantity'] > 0
                    
                    # Extract realized and unrealized gains (already in CNY)
                    realized_gain = cb_data.get('realized_pnl', 0.0)
                    unrealized_gain = cb_data.get('unrealized_pnl', 0.0) if is_held else 0.0
                    
                    # Phase 5 Task 5.1: Extract cost basis and calculate gain percentage
                    cost_basis = cb_data.get('total_cost_basis', 0.0)
                    if cost_basis == 0.0:
                         cost_basis = cb_data.get('cost_basis', 0.0) # Fallback
                    
                    total_gain = realized_gain + unrealized_gain
                    
                    # Calculate gain percentage: (total_gain / cost_basis) * 100
                    # Avoid division by zero
                    if cost_basis > 0:
                        gain_percentage = (total_gain / cost_basis) * 100.0
                    else:
                        gain_percentage = 0.0
                    
                    # FIXED: Gains are already in CNY (transactions converted at processing level)
                    # No need to convert again based on currency
                    
                    asset_gains_data[asset_name] = {
                        'realized_gains': realized_gain,
                        'unrealized_gains': unrealized_gain,
                        'total_gains': total_gain,
                        'cost_basis': cost_basis,  # Phase 5 Task 5.1: NEW field
                        'gain_percentage': gain_percentage,  # Phase 5 Task 5.1: NEW field
                        'is_currently_held': is_held
                    }
                    
    except Exception as e:
        logger.warning(f"⚠️  Error calculating asset-level gains: {e}")
        asset_gains_data = {}
    
    return asset_gains_data


def build_kpi_metrics(
    data_manager: 'DataManager',
    current_holdings: Any
) -> Dict[str, str]:
    """
    Calculate top-level KPI metrics from balance sheet and holdings.
    
    Args:
        data_manager: DataManager instance
        current_holdings: Current holdings DataFrame
        
    Returns:
        Dictionary containing KPI strings (total_liability_str, total_net_assets_str, total_liquid_portfolio_str)
    """
    logger.info("💰 Calculating balance sheet metrics...")
    balance_sheet = data_manager.get_balance_sheet()
    
    if balance_sheet is not None and not balance_sheet.empty:
        latest_bs = balance_sheet.iloc[-1]  # Get most recent balance sheet data
        
        # Total Liabilities
        total_liability = latest_bs.get('Total_Liabilities_Calc_CNY', 0.0)
        total_liability_str = f"{total_liability:,.0f}" if total_liability else "0"
        
        # Total Assets = Sum of ALL holdings (includes property, insurance, investments)
        # NOTE: Balance sheet Total_Assets_Calc_CNY only includes liquid assets, not fixed assets like property
        total_assets = 0.0
        if current_holdings is not None and not current_holdings.empty:
            total_assets = current_holdings['Market_Value_CNY'].sum()
            logger.info(f"✅ Total Assets from holdings (all assets including property): ¥{total_assets:,.0f}")
        else:
            # Fallback to balance sheet if holdings not available (shouldn't happen)
            total_assets = latest_bs.get('Total_Assets_Calc_CNY', 0.0)
            logger.warning(f"⚠️ Using balance sheet Total_Assets_Calc_CNY (liquid assets only): ¥{total_assets:,.0f}")
        
        # Total Net Assets (Assets - Liabilities)
        total_net_assets = total_assets - total_liability
        total_net_assets_str = f"{total_net_assets:,.0f}" if total_net_assets else "0"
        
        # Liquid Portfolio (Holdings excluding Real Estate and Insurance)
        liquid_assets = 0.0
        real_estate_value = 0.0
        insurance_value = 0.0
        
        if current_holdings is not None and not current_holdings.empty:
            for _, holding in current_holdings.iterrows():
                asset_name = holding.get('Asset_Name', '')
                asset_id = holding.get('Asset_ID', '')
                market_value = holding.get('Market_Value_CNY', 0.0)
                
                # Identify real estate assets
                if 'Property' in str(asset_id) or '房' in str(asset_name) or '地产' in str(asset_name) or '蓝郡' in str(asset_name):
                    real_estate_value += market_value
                # Identify insurance assets - FIXED: Added more patterns to catch all insurance products
                elif ('保险' in str(asset_name) or 'Insurance' in str(asset_name) or 'Ins_' in str(asset_id) or
                      '加保' in str(asset_name) or '平安福' in str(asset_name) or 
                      '支付宝保险' in str(asset_name) or 'Pension' in str(asset_name)):
                    insurance_value += market_value
                else:
                    # Only count liquid assets (exclude real estate and insurance)
                    liquid_assets += market_value
        
        # Liquid Portfolio = Direct sum of liquid holdings (excluding real estate and insurance)
        # This approach is more accurate than subtracting from balance sheet totals
        total_liquid_portfolio = liquid_assets
        total_liquid_portfolio_str = f"{total_liquid_portfolio:,.0f}" if total_liquid_portfolio else "0"
        
        logger.info(f"✅ Balance sheet metrics: Liability=¥{total_liability_str}, Net Assets=¥{total_net_assets_str}, Liquid=¥{total_liquid_portfolio_str}")
    else:
        total_liability_str = "0"
        total_net_assets_str = "0" 
        total_liquid_portfolio_str = "0"
        logger.warning("⚠️  Balance sheet data not available")
    
    return {
        'total_liability_str': total_liability_str,
        'total_net_assets_str': total_net_assets_str,
        'total_liquid_portfolio_str': total_liquid_portfolio_str
    }


def build_individual_asset_performance(
    current_holdings: Any,
    investment_analysis_results: Dict[str, Any],
    taxonomy_manager: 'TaxonomyManager',
    is_placeholder_asset_func,
    classify_asset_func,
    lifetime_performance_data: List[Dict[str, Any]] = None
) -> tuple[List[Dict[str, Any]], Dict[str, List]]:
    """
    Build individual asset performance list and XIRR diagnostics.
    
    CRITICAL: Uses lifetime_performance_data (cost_basis.py) as single source of truth
    for individual asset XIRRs. This ensures consistency across all report sections.
    
    Args:
        current_holdings: Current holdings DataFrame
        investment_analysis_results: Results from financial analyzer (for portfolio-level data)
        taxonomy_manager: TaxonomyManager instance
        is_placeholder_asset_func: Function to check if asset is placeholder
        classify_asset_func: Function to classify assets using taxonomy
        lifetime_performance_data: Lifetime performance data from cost_basis.py (AUTHORITATIVE SOURCE)
        
    Returns:
        Tuple of (individual_asset_performance list, xirr_diagnostics dict)
    """
    individual_asset_performance = []
    
    # Collect diagnostic status for XIRR (success/warning/error) to surface in HTML
    xirr_diagnostics = {
        'success': [],
        'warning': [],
        'error': [],
        'skipped': []
    }
    
    # Get special categories that should be excluded from performance analysis
    special_categories = taxonomy_manager.config.get('special_categories', [])
    
    # UNIFIED DATA SOURCE: Use lifetime_performance_data (cost_basis.py) as single source of truth
    # Build lookup dictionaries by asset_id AND asset_name for robust matching
    asset_performances_data = {}
    asset_performances_by_name = {}
    
    if lifetime_performance_data:
        logger.info(f"📊 Using UNIFIED XIRR data from cost_basis.py for {len(lifetime_performance_data)} assets")
        
        for perf in lifetime_performance_data:
            asset_id = perf.get('asset_id')
            asset_name = perf.get('asset_name')
            xirr_pct = perf.get('xirr_pct')  # Already in percentage form
            xirr_status = perf.get('xirr_status', 'success' if xirr_pct is not None else 'skipped')
            
            # Asset ID is now guaranteed to be normalized (no .0 suffix) from database
            
            # Build entry for diagnostics with complete metadata
            # CRITICAL FIX (Nov 5): Include cash_flows_count and period_days from performance data
            # Calculate cash flows count from total shares bought + sold (each transaction is a cash flow)
            total_bought = perf.get('total_shares_bought', 0)
            total_sold = perf.get('total_shares_sold', 0)
            # Approximate cash flows: buys + sells + (1 if currently held for final market value)
            cash_flows_count = int(total_bought + total_sold)
            if perf.get('is_currently_held', False):
                cash_flows_count += 1  # Add 1 for current market value as terminal cash flow
            
            entry = {
                'asset_id': str(asset_id),  # Use normalized ID
                'asset_name': asset_name,
                'market_value': perf.get('current_market_value', 0),
                'xirr': xirr_pct,
                'status': xirr_status,
                'reason': perf.get('xirr_metadata', {}).get('reason', ''),
                'method': xirr_pct if xirr_pct is not None else 'Unknown',  # Show "Xirr" for successful calculations
                'cash_flows_count': cash_flows_count,
                'period_days': perf.get('holding_period_days', 0)
            }
            
            # Store by asset_id for efficient lookup
            perf_data = {
                'Asset_Name': asset_name,
                'XIRR': xirr_pct,
                'Market_Value_CNY': perf.get('current_market_value', 0),
                'XIRR_Status': xirr_status,
                'XIRR_Reason': entry['reason'],
                'XIRR_metadata': perf.get('xirr_metadata', {})
            }
            
            if asset_id:
                asset_performances_data[str(asset_id)] = perf_data
            
            # Also store by name for fallback matching
            if asset_name:
                asset_performances_by_name[asset_name] = perf_data
            
            # Collect diagnostics
            if xirr_status in xirr_diagnostics:
                xirr_diagnostics[xirr_status].append(entry)
            else:
                xirr_diagnostics['skipped'].append(entry)
    else:
        logger.warning("⚠️  No lifetime performance data provided, XIRR values will be unavailable")
    
    if current_holdings is not None and not current_holdings.empty:
        for _, holding in current_holdings.iterrows():
            asset_name = holding.get('Asset_Name', 'Unknown')
            asset_type = holding.get('Asset_Type_Raw', 'Unknown')
            market_value = holding.get('Market_Value_CNY', 0) or 0
            
            # Extract Asset_ID from the index - handle both MultiIndex and simple index
            if isinstance(holding.name, tuple):
                # MultiIndex (Timestamp, Asset_ID)
                asset_id = holding.name[1]
            else:
                # Simple index
                asset_id = holding.name
            
            # Skip placeholder/aggregate assets (balance sheet level, not individual holding)
            if is_placeholder_asset_func(asset_id, asset_name):
                logger.debug(f"🚫 Skipping placeholder asset in performance build: {asset_id} / {asset_name}")
                continue
            
            # Use proper taxonomy classification instead of hardcoded logic
            top_level, sub_class = classify_asset_func(asset_name, asset_type, taxonomy_manager)
            
            # Check if this asset should be excluded from performance analysis
            # Insurance assets can be classified as either:
            # 1. Top-level: "Insurance" (if properly mapped)
            # 2. Sub-class: "Insurance Products" (current classification)
            should_exclude = False
            
            # Check top-level against special_categories (with English-to-Chinese mapping)
            english_to_chinese = {
                'Insurance': '保险',
                'Real Estate': '房地产'
            }
            chinese_top_level = english_to_chinese.get(top_level, top_level)
            if chinese_top_level in special_categories:
                should_exclude = True
            
            # Also check sub-class for insurance products
            if sub_class == 'Insurance Products':
                should_exclude = True
            
            # Skip assets that should be excluded from performance analysis
            if should_exclude:
                continue
            
            # Get real XIRR value and metadata from UNIFIED lifetime performance data (cost_basis.py)
            # Try to find matching asset by index (Asset_ID) first, then by name
            real_xirr = None
            xirr_metadata = {'is_approximated': True, 'method_used': 'unavailable', 'confidence': 'low'}

            # Try Asset_ID match first
            asset_id_str = str(asset_id)
            if asset_id_str in asset_performances_data:
                xirr_data = asset_performances_data[asset_id_str].get('XIRR')
                xirr_meta = asset_performances_data[asset_id_str].get('XIRR_metadata', {})
                if xirr_data is not None and pd.notna(xirr_data):
                    real_xirr = float(xirr_data)
                    # Extract metadata if available
                    if xirr_meta:
                        xirr_metadata = {
                            'is_approximated': xirr_meta.get('is_approximated', False),
                            'method_used': xirr_meta.get('method_used', 'calculated'),
                            'confidence': xirr_meta.get('confidence', 'high')
                        }
                    logger.debug(f"✅ Matched XIRR for {asset_id} ({asset_name}): {real_xirr}%")
            
            # If no exact match, try name-based matching using the name lookup dictionary
            if real_xirr is None and asset_name in asset_performances_by_name:
                perf_data = asset_performances_by_name[asset_name]
                xirr_data = perf_data.get('XIRR')
                xirr_meta = perf_data.get('XIRR_metadata', {})
                if xirr_data is not None and pd.notna(xirr_data):
                    real_xirr = float(xirr_data)
                    if xirr_meta:
                        xirr_metadata = {
                            'is_approximated': xirr_meta.get('is_approximated', False),
                            'method_used': xirr_meta.get('method_used', 'calculated'),
                            'confidence': xirr_meta.get('confidence', 'high')
                        }
                    logger.debug(f"✅ Matched XIRR for {asset_name} (by name): {real_xirr}%")
            
            if real_xirr is None:
                logger.debug(f"❌ No XIRR match for {asset_id} ({asset_name})")
            
            # Use real XIRR if available, otherwise mark as unavailable
            has_real_xirr = real_xirr is not None
            if has_real_xirr:
                asset_xirr = real_xirr
            else:
                asset_xirr = None  # Will be handled as "N/A" in aggregation
            
            individual_asset_performance.append({
                'asset_id': asset_id,  # Include asset_id for XIRR lookup
                'asset_name': asset_name,
                'asset_type': asset_type,
                'market_value': market_value,
                'xirr': asset_xirr,
                'has_real_xirr': has_real_xirr,
                'xirr_metadata': xirr_metadata,
                'top_level': top_level,
                'sub_class': sub_class
            })
    
    return individual_asset_performance, xirr_diagnostics
