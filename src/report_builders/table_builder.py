"""Holdings Table Builder Module

This module handles the creation of hierarchical holdings tables with sub-totals,
classifications, and XIRR performance data for investment portfolios.

Author: Personal Investment System
Date: 2025-01-03
"""

import logging
from typing import Dict, List
import pandas as pd
from src.localization import _

logger = logging.getLogger(__name__)


def build_holdings_table_direct(holdings_df, individual_asset_performance=None, lifetime_performance_data=None) -> List[Dict[str, str]]:
    """
    Build holdings table with sub-totals, sorted by Top Class and Sub-class totals.
    
    Phase 5 Task 5.2: Enhanced with P/L data at all hierarchy levels.
    
    Args:
        holdings_df: DataFrame of current holdings
        individual_asset_performance: List of asset performance dictionaries
        lifetime_performance_data: List of dicts with lifetime asset performance (NEW - Phase 5)
            Expected structure: [{'asset_name': str, 'total_pnl': float, 'total_return_pct': float, ...}, ...]
    
    Returns:
        List of dictionaries representing table rows with all columns including P/L data
    """
    
    from src.portfolio_lib.taxonomy_manager import TaxonomyManager
    
    # Import helper functions from src.report_generators.real_report
    from src.report_generators.real_report import (
        classify_asset_using_taxonomy,
        is_placeholder_asset,
        format_asset_name_for_display
    )
    
    holdings_table = []
    total_value = holdings_df['Market_Value_CNY'].sum() if 'Market_Value_CNY' in holdings_df.columns else 0
    
    # Initialize taxonomy manager for classification
    taxonomy_manager = TaxonomyManager()
    
    # Create XIRR lookup from individual asset performance
    xirr_lookup = {}
    if individual_asset_performance:
        for asset_perf in individual_asset_performance:
            asset_id = asset_perf.get('asset_id', '')
            # Asset ID is now guaranteed to be normalized (no .0 suffix) from database
            asset_id_str = str(asset_id)
            
            # Only include XIRR if it's real data, not fallback
            if asset_perf.get('has_real_xirr', False) and asset_perf.get('xirr') is not None:
                xirr_lookup[asset_id_str] = asset_perf['xirr']
    
    # First pass: classify and prepare data
    classified_holdings = []
    skipped_placeholders = 0
    for idx, holding in holdings_df.iterrows():
        asset_name = holding.get('Asset_Name', 'Unknown')
        asset_type = holding.get('Asset_Type_Raw', 'Unknown')
        market_value = holding.get('Market_Value_CNY', 0) or 0
        
        # Differentiate Gold holdings by Account (招行/工行) for multi-account support
        # Note: Gold holdings are now aggregated in manager.py, so this is only for 
        # potential future use if separate display is needed
        account = holding.get('Account', None)

        asset_id = holding.name if hasattr(holding, 'name') else None
        
        # Filter out invalid asset names (NaN or 'nan')
        if pd.isna(asset_name) or str(asset_name).lower() == 'nan':
            continue

        if is_placeholder_asset(asset_id, asset_name):
            skipped_placeholders += 1
            continue
        
        # Get classification using taxonomy
        top_level_class, sub_class = classify_asset_using_taxonomy(asset_name, asset_type, taxonomy_manager)
        
        # Calculate percentage
        portfolio_percentage = (market_value / total_value * 100) if total_value > 0 else 0
        
        # Determine status - simplified logic
        # Determine status - based on successful classification
        # If we have a valid classification (not Other/Other), consider it Active/Mapped
        if top_level_class == 'Other' and sub_class == 'Other':
            status = 'Unmapped'
        else:
            status = 'Active'
        
        # Look up XIRR data for this asset
        # CRITICAL FIX: Handle MultiIndex (Timestamp, Asset_ID) tuple properly
        if isinstance(holding.name, tuple) and len(holding.name) >= 2:
            asset_id = holding.name[1]  # Extract Asset_ID from MultiIndex tuple
        elif hasattr(holding, 'name'):
            asset_id = holding.name
        else:
            asset_id = f"{asset_name}_{asset_type}"
        
        # Asset ID is now guaranteed to be normalized (no .0 suffix) from database
        asset_id_str = str(asset_id)
        
        xirr_value = xirr_lookup.get(asset_id)
        
        # Phase 5 Task 5.2: Look up P/L data for this asset from lifetime_performance_data
        # Use lifetime_performance_data (same source as markdown and dashboard)
        total_pnl = 0.0
        pnl_percentage = 0.0
        if lifetime_performance_data:
            for perf in lifetime_performance_data:
                perf_asset_name = perf.get('asset_name', '')
                perf_asset_id = perf.get('asset_id', '')
                
                # Match by exact asset_id OR by exact asset name
                if (perf_asset_id == asset_id_str or 
                    perf_asset_id == asset_id or
                    perf_asset_name == asset_name):
                    total_pnl = perf.get('total_pnl', 0.0) or 0.0
                    pnl_percentage = perf.get('total_return_pct', 0.0) or 0.0
                    break
        
        classified_holdings.append({
            'top_class': str(top_level_class),
            'sub_class': str(sub_class),
            'asset_name': format_asset_name_for_display(asset_name),
            'asset_class': str(asset_type) if pd.notna(asset_type) and asset_type != 'Unknown' else sub_class,
            'market_value_numeric': market_value,
            'market_value': f"{market_value:,.0f}" if market_value else "0",
            'portfolio_percentage_numeric': portfolio_percentage,
            'portfolio_percentage': f"{portfolio_percentage:.1f}",
            'total_pnl_numeric': total_pnl,  # Phase 5: NEW field
            'total_pnl': f"{total_pnl:,.0f}",  # Phase 5: NEW field
            'pnl_percentage_numeric': pnl_percentage,  # Phase 5: NEW field
            'pnl_percentage': f"{pnl_percentage:+.2f}%",  # Phase 5: NEW field (with + sign for positive)
            'status': status,
            'is_subtotal': False,
            'xirr': xirr_value  # Add XIRR data
        })
    
    # Second pass: calculate Top Class and Sub-class totals
    top_class_totals = {}
    sub_class_totals = {}
    # Phase 5 Task 5.2: Add P/L aggregation - sum P/L amounts for subtotals
    top_class_pnl = {}
    sub_class_pnl = {}
    
    for holding in classified_holdings:
        top_class = holding['top_class']
        sub_class = holding['sub_class']
        value = holding['market_value_numeric']
        # Phase 5 Task 5.2: Aggregate P/L data (just sum the P/L amounts)
        pnl = holding.get('total_pnl_numeric', 0.0)
        
        # Aggregate Top Class totals
        if top_class not in top_class_totals:
            top_class_totals[top_class] = 0
            top_class_pnl[top_class] = 0.0  # Phase 5
        top_class_totals[top_class] += value
        top_class_pnl[top_class] += pnl  # Phase 5
        
        # Aggregate Sub-class totals within Top Class
        sub_key = f"{top_class}|{sub_class}"
        if sub_key not in sub_class_totals:
            sub_class_totals[sub_key] = 0
            sub_class_pnl[sub_key] = 0.0  # Phase 5
        sub_class_totals[sub_key] += value
        sub_class_pnl[sub_key] += pnl  # Phase 5
    
    # Sort Top Classes by total value (descending)
    sorted_top_classes = sorted(top_class_totals.items(), key=lambda x: x[1], reverse=True)
    
    # Third pass: build the ordered table with sub-totals
    for top_class, top_class_total in sorted_top_classes:
        # Get holdings for this top class
        top_class_holdings = [h for h in classified_holdings if h['top_class'] == top_class]
        
        # Group by sub-class and sort sub-classes by total value
        sub_class_groups = {}
        for holding in top_class_holdings:
            sub_class = holding['sub_class']
            if sub_class not in sub_class_groups:
                sub_class_groups[sub_class] = []
            sub_class_groups[sub_class].append(holding)
        
        # Sort sub-classes by total value within this top class
        sorted_sub_classes = sorted(
            sub_class_groups.items(),
            key=lambda x: sum(h['market_value_numeric'] for h in x[1]),
            reverse=True
        )
        
        # Add Top Class header/subtotal
        top_class_percentage = (top_class_total / total_value * 100) if total_value > 0 else 0
        # Phase 5 Task 5.2: Calculate aggregated P/L for top class
        # Formula: cost_basis = market_value - total_pnl, then pnl_pct = (total_pnl / cost_basis) * 100
        top_pnl = top_class_pnl.get(top_class, 0.0)
        top_cost_basis = top_class_total - top_pnl  # Current value = cost + pnl, so cost = value - pnl
        top_pnl_pct = (top_pnl / top_cost_basis * 100.0) if top_cost_basis > 0 else 0.0
        
        holdings_table.append({
            'top_class': f"📊 {top_class} {_('Category Total')}",
            'sub_class': '',
            'asset_name': '',
            'asset_class': '',
            'market_value': f"{top_class_total:,.0f}",
            'portfolio_percentage': f"{top_class_percentage:.1f}",
            'total_pnl': f"{top_pnl:,.0f}",  # Phase 5: NEW field
            'pnl_percentage': f"{top_pnl_pct:+.2f}%",  # Phase 5: NEW field
            'status': '',
            'is_subtotal': True,
            'subtotal_type': 'top_class',
            'xirr': None  # No XIRR for subtotals
        })
        
        # Process each sub-class within this top class
        for sub_class, sub_holdings in sorted_sub_classes:
            sub_class_total = sum(h['market_value_numeric'] for h in sub_holdings)
            sub_class_percentage = (sub_class_total / total_value * 100) if total_value > 0 else 0
            # Phase 5 Task 5.2: Calculate aggregated P/L for sub-class
            sub_key = f"{top_class}|{sub_class}"
            sub_pnl = sub_class_pnl.get(sub_key, 0.0)
            sub_cost_basis = sub_class_total - sub_pnl  # Same formula as top class
            sub_pnl_pct = (sub_pnl / sub_cost_basis * 100.0) if sub_cost_basis > 0 else 0.0
            
            # Add Sub-class subtotal
            holdings_table.append({
                'top_class': '',
                'sub_class': f"  📈 {sub_class} {_('Subtotal')}",
                'asset_name': '',
                'asset_class': '',
                'market_value': f"{sub_class_total:,.0f}",
                'portfolio_percentage': f"{sub_class_percentage:.1f}",
                'total_pnl': f"{sub_pnl:,.0f}",  # Phase 5: NEW field
                'pnl_percentage': f"{sub_pnl_pct:+.2f}%",  # Phase 5: Fixed - added missing % sign
                'status': '',
                'is_subtotal': True,
                'subtotal_type': 'sub_class',
                'xirr': None  # No XIRR for subtotals
            })
            
            # Sort individual holdings within sub-class by market value (descending)
            sub_holdings.sort(key=lambda x: x['market_value_numeric'], reverse=True)
            
            # Add individual holdings
            for holding in sub_holdings:
                holdings_table.append({
                    'top_class': '',  # Empty for individual holdings to avoid repetition
                    'sub_class': '',  # Empty for individual holdings to avoid repetition
                    'asset_name': f"    • {holding['asset_name']}",  # Indent individual assets
                    'asset_class': holding['asset_class'],
                    'market_value': holding['market_value'],
                    'portfolio_percentage': holding['portfolio_percentage'],
                    'total_pnl': holding.get('total_pnl', '0'),  # Phase 5: NEW field
                    'pnl_percentage': holding.get('pnl_percentage', '+0.00'),  # Phase 5: NEW field
                    'status': holding['status'],
                    'is_subtotal': False,
                    'subtotal_type': '',
                    'xirr': holding['xirr']  # Include XIRR data for individual assets
                })
    
    if skipped_placeholders:
        logger.debug(f"🧹 Removed {skipped_placeholders} placeholder aggregate asset(s) from holdings table")
    return holdings_table
