"""Tier Analysis Builder Module

Builds tier-level allocation analysis for portfolio holdings, categorizing assets
by strategic role (Core/底仓, Diversification/辅助, Trading/交易).

Author: Personal Investment System
Date: 2025-12-29
"""

import logging
from typing import Dict, List, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


def build_tier_analysis(
    holdings_df: pd.DataFrame,
    taxonomy_manager=None,
    total_portfolio_value: Optional[float] = None
) -> Dict[str, Any]:
    """
    Build tier-level allocation analysis.
    
    Args:
        holdings_df: DataFrame with current holdings data (must have Market_Value_CNY)
        taxonomy_manager: Optional TaxonomyManager instance. If None, creates a new one.
        total_portfolio_value: Optional override for total value (denominator). 
                              If None, sums Market_Value_CNY of all holdings.
        
    Returns:
        Dict containing:
            - total_value: Total value used for calculation
            - tier_table: List of tier analysis dicts
            - tier_details: Dict of tier_key -> list of asset details
            - unclassified_count: Number of assets without tier classification
    """
    logger.debug("🎯 Building tier-level allocation analysis...")
    
    # Initialize TaxonomyManager if not provided
    if taxonomy_manager is None:
        from src.portfolio_lib.taxonomy_manager import TaxonomyManager
        taxonomy_manager = TaxonomyManager()
    
    # Get tier configuration
    tier_config = taxonomy_manager.get_tier_config()
    tier_targets = taxonomy_manager.get_tier_targets()
    
    # Calculate sum of holdings
    holdings_sum = holdings_df['Market_Value_CNY'].sum() if 'Market_Value_CNY' in holdings_df.columns else 0.0
    
    # Filter out non-rebalanceable assets for tier analysis
    # We only want to analyze "Investment Assets" (Liquid)
    excluded_classes = ['房地产', 'Real Estate', '保险', 'Insurance', 'Pension', 'Yearly_Savings']
    
    analysis_df = holdings_df.copy()
    if 'Asset_Class' in analysis_df.columns:
        # Filter out excluded classes
        analysis_df = analysis_df[~analysis_df['Asset_Class'].isin(excluded_classes)]
        logger.info(f"Filtered out {len(holdings_df) - len(analysis_df)} non-rebalanceable assets from tier analysis")
    
    # Determine denominator
    if total_portfolio_value is not None:
        calc_total_value = total_portfolio_value
        logger.info(f"Using provided total value as denominator: ¥{calc_total_value:,.0f}")
    else:
        # Recalculate sum from filtered dataframe if no external total provided
        calc_total_value = analysis_df['Market_Value_CNY'].sum() if 'Market_Value_CNY' in analysis_df.columns else 0.0
        logger.info(f"Using sum of filtered holdings as denominator: ¥{calc_total_value:,.0f}")
    
    if calc_total_value <= 0:
        logger.warning("Total portfolio value is 0 or negative, returning empty analysis")
        return {
            'total_value': 0,
            'tier_table': [],
            'tier_details': {},
            'unclassified_count': 0
        }
    
    # Classify holdings by tier
    classified_df = taxonomy_manager.classify_holdings_by_tier(analysis_df)
    
    # Aggregate by tier
    tier_metrics = {}
    tier_details = {}
    unclassified_count = 0
    
    for _, row in classified_df.iterrows():
        tier_key = row.get('Asset_Tier', 'unclassified')
        market_value = row.get('Market_Value_CNY', 0) or 0
        asset_name = row.get('Asset_Name', 'Unknown')
        asset_id = row.get('Asset_ID', '')
        
        # P&L Metrics (Handle NaNs)
        realized_pnl = row.get('Realized_PnL', 0.0)
        if pd.isna(realized_pnl): realized_pnl = 0.0
        
        unrealized_pnl = row.get('Unrealized_PnL', 0.0)
        if pd.isna(unrealized_pnl): unrealized_pnl = 0.0
        
        total_pnl = row.get('Total_PnL', 0.0)
        if pd.isna(total_pnl): total_pnl = 0.0
        
        xirr = row.get('Lifetime_XIRR', 0.0)
        if pd.isna(xirr): xirr = 0.0
        
        if tier_key not in tier_metrics:
            tier_metrics[tier_key] = {
                'value': 0.0,
                'realized_pnl': 0.0,
                'unrealized_pnl': 0.0,
                'total_pnl': 0.0,
                'xirr_weighted_sum': 0.0,
                'xirr_weight_total': 0.0
            }
            tier_details[tier_key] = []
        
        # Aggregate Metrics
        tier_metrics[tier_key]['value'] += market_value
        tier_metrics[tier_key]['realized_pnl'] += realized_pnl
        tier_metrics[tier_key]['unrealized_pnl'] += unrealized_pnl
        tier_metrics[tier_key]['total_pnl'] += total_pnl
        
        # Weighted XIRR Calculation (only if market value > 0)
        if market_value > 0:
            tier_metrics[tier_key]['xirr_weighted_sum'] += (market_value * xirr)
            tier_metrics[tier_key]['xirr_weight_total'] += market_value
        
        tier_details[tier_key].append({
            'asset_id': asset_id,
            'asset_name': asset_name,
            'value': market_value,
            'pct': (market_value / calc_total_value * 100) if calc_total_value > 0 else 0,
            'total_pnl': total_pnl,
            'xirr': xirr
        })
        
        if tier_key == 'unclassified':
            unclassified_count += 1
    
    # Build tier table
    tier_table = []
    
    # Process configured tiers first (in order)
    tier_order = ['tier_1_core', 'tier_2_diversification', 'tier_3_trading']
    
    for tier_key in tier_order:
        metrics = tier_metrics.get(tier_key, {})
        current_value = metrics.get('value', 0.0)
        current_pct = (current_value / calc_total_value * 100) if calc_total_value > 0 else 0.0
        target_pct = tier_targets.get(tier_key, 0.0) * 100
        drift = current_pct - target_pct
        
        # Calculate Weighted XIRR
        xirr_weight_total = metrics.get('xirr_weight_total', 0.0)
        weighted_xirr = (metrics.get('xirr_weighted_sum', 0.0) / xirr_weight_total) if xirr_weight_total > 0 else 0.0
        
        tier_info = tier_config.get(tier_key, {})
        
        tier_table.append({
            'tier_key': tier_key,
            'tier_name': tier_info.get('name', tier_key),
            'description': tier_info.get('description', ''),
            'color': tier_info.get('color', 'gray'),
            'current_value': current_value,
            'current_pct': current_pct,
            'target_pct': target_pct,
            'drift': drift,
            'asset_count': len(tier_details.get(tier_key, [])),
            # New P&L Fields
            'realized_pnl': metrics.get('realized_pnl', 0.0),
            'unrealized_pnl': metrics.get('unrealized_pnl', 0.0),
            'total_pnl': metrics.get('total_pnl', 0.0),
            'weighted_xirr': weighted_xirr
        })
        
        logger.debug(
            f"  {tier_info.get('name', tier_key)}: "
            f"¥{current_value:,.0f} ({current_pct:.1f}%) | "
            f"Target: {target_pct:.1f}% | Drift: {drift:+.1f}% | "
            f"P&L: ¥{metrics.get('total_pnl', 0):,.0f} | XIRR: {weighted_xirr:.2f}%"
        )
    
    # Add unclassified if any
    if 'unclassified' in tier_metrics and tier_metrics['unclassified']['value'] > 0:
        metrics = tier_metrics['unclassified']
        unclassified_value = metrics['value']
        
        # Weighted XIRR for unclassified
        xirr_weight_total = metrics.get('xirr_weight_total', 0.0)
        weighted_xirr = (metrics.get('xirr_weighted_sum', 0.0) / xirr_weight_total) if xirr_weight_total > 0 else 0.0
        
        tier_table.append({
            'tier_key': 'unclassified',
            'tier_name': '未分类 (Unclassified)',
            'description': '未配置梯队的资产',
            'color': 'gray',
            'current_value': unclassified_value,
            'current_pct': (unclassified_value / calc_total_value * 100) if calc_total_value > 0 else 0,
            'target_pct': 0,
            'drift': (unclassified_value / calc_total_value * 100) if calc_total_value > 0 else 0,
            'asset_count': unclassified_count,
            'realized_pnl': metrics.get('realized_pnl', 0.0),
            'unrealized_pnl': metrics.get('unrealized_pnl', 0.0),
            'total_pnl': metrics.get('total_pnl', 0.0),
            'weighted_xirr': weighted_xirr
        })
        
        logger.warning(f"  ⚠️ Unclassified: ¥{unclassified_value:,.0f} ({unclassified_count} assets)")
    
    logger.info(f"Tier analysis complete. Total Denom: ¥{calc_total_value:,.0f}, {len(tier_table)} tiers")
    
    return {
        'total_value': calc_total_value,
        'tier_table': tier_table,
        'tier_details': tier_details,
        'unclassified_count': unclassified_count
    }


def format_tier_table_for_display(tier_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Format tier analysis for display in reports.
    
    Args:
        tier_data: Output from build_tier_analysis()
        
    Returns:
        List of display-ready dicts with formatted values
    """
    formatted = []
    
    for tier in tier_data.get('tier_table', []):
        formatted.append({
            'tier_name': tier['tier_name'],
            'current_value': f"¥{tier['current_value']:,.0f}",
            'current_pct': f"{tier['current_pct']:.1f}%",
            'target_pct': f"{tier['target_pct']:.1f}%",
            'drift': f"{tier['drift']:+.1f}%",
            'drift_class': 'positive' if tier['drift'] > 2 else ('negative' if tier['drift'] < -2 else 'neutral'),
            'asset_count': str(tier['asset_count'])
        })
    
    return formatted
