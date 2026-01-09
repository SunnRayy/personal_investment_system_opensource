"""
Performance Builders Module - Aggregation functions for asset performance data.

This module contains functions for aggregating individual asset performance metrics
into top-level and sub-class summaries for reporting.
"""

from typing import List, Dict, Any


def aggregate_performance_by_top_level(individual_assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate individual asset performance data into top-level class summaries.
    Only aggregates assets with real XIRR data; shows "N/A" if no real data available.
    
    Args:
        individual_assets: List of dictionaries with asset performance data
        
    Returns:
        List of dictionaries with top-level class performance summaries
    """
    top_level_groups = {}
    
    for asset in individual_assets:
        top_level = asset.get('top_level', 'Unknown')
        
        if top_level not in top_level_groups:
            top_level_groups[top_level] = {
                'class_name': top_level,
                'total_market_value': 0,
                'weighted_xirr_sum': 0,
                'total_weight_with_xirr': 0,  # Only count assets with real XIRR
                'has_any_real_xirr': False,
                'approximated_count': 0,
                'total_count': 0
            }
        
        market_value = asset.get('market_value', 0)
        xirr = asset.get('xirr')
        has_real_xirr = asset.get('has_real_xirr', False)
        xirr_metadata = asset.get('xirr_metadata', {})
        
        group = top_level_groups[top_level]
        group['total_market_value'] += market_value
        group['total_count'] += 1
        
        # Track approximation metadata
        if xirr_metadata.get('is_approximated', True):
            group['approximated_count'] += 1
        
        # Only include in XIRR calculation if real data is available
        if has_real_xirr and xirr is not None:
            group['weighted_xirr_sum'] += xirr * market_value
            group['total_weight_with_xirr'] += market_value
            group['has_any_real_xirr'] = True
    
    # Calculate total portfolio value for percentage calculations
    total_portfolio_value = sum(group['total_market_value'] for group in top_level_groups.values())
    
    # Calculate weighted average XIRR and portfolio percentage for each group
    result = []
    for group in top_level_groups.values():
        # Only calculate XIRR if we have real data
        if group['has_any_real_xirr'] and group['total_weight_with_xirr'] > 0:
            weighted_avg_xirr = group['weighted_xirr_sum'] / group['total_weight_with_xirr']
        else:
            weighted_avg_xirr = None  # Will display as "N/A"
            
        portfolio_percentage = (group['total_market_value'] / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
        
        # Calculate approximation percentage
        approximation_percentage = (group['approximated_count'] / group['total_count'] * 100) if group['total_count'] > 0 else 100
        
        result.append({
            'class_name': group['class_name'],
            'market_value': group['total_market_value'],
            'xirr': weighted_avg_xirr,
            'portfolio_percentage': portfolio_percentage,
            'metadata': {
                'approximated_count': group['approximated_count'],
                'total_count': group['total_count'],
                'approximation_percentage': approximation_percentage,
                'show_warning': approximation_percentage > 50 or weighted_avg_xirr is None
            }
        })
    
    return sorted(result, key=lambda x: x['xirr'] if x['xirr'] is not None else -999, reverse=True)


def aggregate_performance_by_sub_class(individual_assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate individual asset performance data into sub-class summaries.
    Only aggregates assets with real XIRR data; shows "N/A" if no real data available.
    
    Args:
        individual_assets: List of dictionaries with asset performance data
        
    Returns:
        List of dictionaries with sub-class performance summaries
    """
    sub_class_groups = {}
    
    for asset in individual_assets:
        sub_class = asset.get('sub_class', 'Unknown')
        
        if sub_class not in sub_class_groups:
            sub_class_groups[sub_class] = {
                'class_name': sub_class,
                'total_market_value': 0,
                'weighted_xirr_sum': 0,
                'total_weight_with_xirr': 0,
                'has_any_real_xirr': False,
                'approximated_count': 0,
                'total_count': 0
            }
        
        market_value = asset.get('market_value', 0)
        xirr = asset.get('xirr')
        has_real_xirr = asset.get('has_real_xirr', False)
        xirr_metadata = asset.get('xirr_metadata', {})
        
        group = sub_class_groups[sub_class]
        group['total_market_value'] += market_value
        group['total_count'] += 1
        
        # Track approximation metadata
        if xirr_metadata.get('is_approximated', True):
            group['approximated_count'] += 1
        
        # Only include in XIRR calculation if real data is available
        if has_real_xirr and xirr is not None:
            group['weighted_xirr_sum'] += xirr * market_value
            group['total_weight_with_xirr'] += market_value
            group['has_any_real_xirr'] = True
    
    # Calculate total portfolio value for percentage calculations
    total_portfolio_value = sum(group['total_market_value'] for group in sub_class_groups.values())
    
    # Calculate weighted average XIRR and portfolio percentage for each group
    result = []
    for group in sub_class_groups.values():
        # Only calculate XIRR if we have real data
        if group['has_any_real_xirr'] and group['total_weight_with_xirr'] > 0:
            weighted_avg_xirr = group['weighted_xirr_sum'] / group['total_weight_with_xirr']
        else:
            weighted_avg_xirr = None  # Will display as "N/A"
            
        portfolio_percentage = (group['total_market_value'] / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
        
        # Calculate approximation percentage
        approximation_percentage = (group['approximated_count'] / group['total_count'] * 100) if group['total_count'] > 0 else 100
        
        result.append({
            'class_name': group['class_name'],
            'market_value': group['total_market_value'],
            'xirr': weighted_avg_xirr,
            'portfolio_percentage': portfolio_percentage,
            'metadata': {
                'approximated_count': group['approximated_count'],
                'total_count': group['total_count'],
                'approximation_percentage': approximation_percentage,
                'show_warning': approximation_percentage > 50 or weighted_avg_xirr is None
            }
        })
    
    return sorted(result, key=lambda x: x['xirr'] if x['xirr'] is not None else -999, reverse=True)
