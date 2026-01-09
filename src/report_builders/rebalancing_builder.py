"""Rebalancing Analysis Builder Module

This module handles the creation of rebalancing analysis data for investment portfolios,
including two-level allocation analysis, drift detection, and hierarchical trade recommendations.

Author: Personal Investment System
Date: 2025-01-03
Updated: 2025-10-19 (Phase 7.4.2: Market regime dynamic target support)
"""

import logging
from typing import Dict, List, Optional
from src.localization import _

logger = logging.getLogger(__name__)


def build_rebalancing_analysis(
    holdings_df, 
    market_regime: Optional[Dict] = None, 
    taxonomy_manager=None,
    active_risk_profile: Optional[str] = None
) -> Dict:
    """Build two-level rebalancing analysis following Investment Compass logic.
    
    Args:
        holdings_df: DataFrame with current holdings data
        market_regime: Optional dict from IndicatorRegimeDetector containing:
                      - regime_name: str
                      - dynamic_targets: dict with 'top_level' asset class targets
                      If None, uses baseline targets from asset_taxonomy.yaml
        taxonomy_manager: Optional TaxonomyManager instance. If None, creates a new one.
        active_risk_profile: Optional override for risk profile name (e.g. '成长型')
    
    Returns:
        Dict containing rebalancing analysis with top_level_table, sub_level_table, etc.
    """
    
    logger.debug("🎯 Building two-level rebalancing analysis...")
    
    # Initialize TaxonomyManager if not provided
    if taxonomy_manager is None:
        from src.portfolio_lib.taxonomy_manager import TaxonomyManager
        taxonomy_manager = TaxonomyManager()
    
    # Import classification helper (from src.report_generators.real_report)
    from src.report_generators.real_report import classify_asset_using_taxonomy
    
    # Load target allocations and sub-category weights from asset taxonomy
    # Load target allocations and sub-category weights from DB (via TaxonomyManager)
    
    # Use override if provided, otherwise default to active profile from DB
    if active_risk_profile:
        active_profile = active_risk_profile
        logger.info(f"Using OVERRIDDEN risk profile: {active_profile}")
    else:
        active_profile = taxonomy_manager.get_active_risk_profile_name()
        logger.info(f"Using active risk profile: {active_profile}")
        
    target_allocations, sub_category_weights = taxonomy_manager.get_risk_profile_allocations(active_profile)
    logger.debug(f"Loaded baseline target allocations: {target_allocations}")
    logger.debug(f"Loaded sub-category weights keys: {list(sub_category_weights.keys())}")
    
    # PHASE 7.4.2: Apply market regime dynamic targets (Modifiers) if available
    if market_regime:
        target_modifiers = market_regime.get('target_modifiers')
        
        if target_modifiers:
            top_level_modifiers = target_modifiers.get('top_level', {})
            sub_category_targets = target_modifiers.get('sub_category', {}) # These are still absolute targets for rotation
            
            regime_name = market_regime.get('regime_name_cn', market_regime.get('regime_name', 'Unknown'))
            logger.info(f"📊 PHASE 7.4.2: Applying dynamic modifiers from market regime: {regime_name}")
            
            # 1. Apply Top-Level Modifiers (Deltas)
            if top_level_modifiers:
                for asset_class_cn, modifier in top_level_modifiers.items():
                    if asset_class_cn in target_allocations:
                        old_target = target_allocations[asset_class_cn]
                        # Apply modifier (e.g., 0.20 + (-0.05) = 0.15)
                        new_target = max(0.0, min(1.0, old_target + modifier))
                        target_allocations[asset_class_cn] = new_target
                        
                        sign = "+" if modifier > 0 else ""
                        logger.info(f"  ✓ {asset_class_cn}: {old_target*100:.1f}% {sign}{modifier*100:.1f}% → {new_target*100:.1f}%")
                    else:
                        # If asset class not in profile, we can optionally add it if modifier > 0
                        if modifier > 0:
                            target_allocations[asset_class_cn] = modifier
                            logger.info(f"  ✓ {asset_class_cn}: Added new target {modifier*100:.1f}%")
            
            # 2. Apply Sub-Category Targets (Absolute Proportions)
            # Note: Sub-category logic remains absolute for tactical rotation within the asset class
            if sub_category_targets:
                logger.info("📊 Applying regime sub-category proportions...")
                
                # Map Chinese sub-category names from regime config to taxonomy sub-category names
                regime_to_taxonomy_map = {
                    '国内股票ETF': '国内股票ETF',
                    '港股ETF': 'HK ETF',
                    '美国股票ETF': '美国股票ETF',
                    '公司美股RSU': '公司美股RSU',
                    # Add more mappings as needed
                }
                
                for asset_class_cn, sub_proportions in sub_category_targets.items():
                    if asset_class_cn in sub_category_weights and isinstance(sub_proportions, dict):
                        # Replace baseline proportions with regime proportions
                        regime_weights = {}
                        for sub_cat_regime, proportion in sub_proportions.items():
                            # Map regime name to taxonomy name
                            taxonomy_name = regime_to_taxonomy_map.get(sub_cat_regime, sub_cat_regime)
                            regime_weights[taxonomy_name] = proportion
                            
                            # Calculate absolute target: proportion × top_level_target
                            top_level_target = target_allocations.get(asset_class_cn, 0.0)
                            absolute_target = proportion * top_level_target * 100
                            logger.info(f"    ✓ {taxonomy_name}: {proportion*100:.1f}% of {asset_class_cn} = {absolute_target:.1f}% of rebalanceable")
                        
                        # Replace baseline weights with regime weights
                        sub_category_weights[asset_class_cn] = regime_weights
                        logger.info(f"  ✓ Updated {asset_class_cn} sub-category weights from regime")
            
            logger.info("📊 Dynamic modifiers applied successfully")
        else:
            logger.info("📊 Market regime provided but no target_modifiers found, using baseline")
    else:
        logger.info("📊 No market regime provided, using baseline targets from active profile")
    
    logger.debug(f"Final target allocations for rebalancing: {target_allocations}")
    
    # Calculate portfolio composition
    total_portfolio_value = holdings_df['Market_Value_CNY'].sum()
    
    # Get non-rebalanceable classes from taxonomy
    non_rebalanceable_classes = taxonomy_manager.config.get('non_rebalanceable_classes', [])
    non_rebalanceable_sub_classes = taxonomy_manager.config.get('non_rebalanceable_sub_classes', [])
    special_categories = taxonomy_manager.config.get('special_categories', [])
    
    # Build current allocation data structures
    top_level_allocation = {}  # Chinese category -> value
    sub_level_allocation = {}  # Chinese category -> {sub_category -> value}
    non_rebalanceable_value = 0
    
    for idx, holding in holdings_df.iterrows():
        asset_name = str(holding.get('Asset_Name', ''))
        asset_type = str(holding.get('Asset_Type_Raw', ''))
        market_value = holding.get('Market_Value_CNY', 0) or 0

        # Use taxonomy to classify
        top_level, sub_class = classify_asset_using_taxonomy(asset_name, asset_type, taxonomy_manager)
        
        # Map English back to Chinese for allocation grouping
        # Use localized top level key directly
        top_level_key = top_level
        
        # Check if asset is non-rebalanceable
        is_non_rebalanceable = (
            top_level_key in non_rebalanceable_classes or
            top_level_key in special_categories or
            sub_class in non_rebalanceable_sub_classes
        )
        
        if is_non_rebalanceable:
            non_rebalanceable_value += market_value
        
        # Add to allocation tracking (include all assets for analysis)
        top_level_allocation[top_level_key] = top_level_allocation.get(top_level_key, 0) + market_value
        
        if top_level_key not in sub_level_allocation:
            sub_level_allocation[top_level_key] = {}
        sub_level_allocation[top_level_key][sub_class] = sub_level_allocation[top_level_key].get(sub_class, 0) + market_value
    
    rebalanceable_value = total_portfolio_value - non_rebalanceable_value
    
    logger.debug(f"Total portfolio: ¥{total_portfolio_value:,.0f}")
    logger.debug(f"Non-rebalanceable: ¥{non_rebalanceable_value:,.0f}")
    logger.debug(f"Rebalanceable: ¥{rebalanceable_value:,.0f}")
    
    # Create two-level allocation analysis following Investment Compass pattern
    top_level_analysis = []
    sub_level_analysis = []
    recommended_trades = []
    
    # Calculate rebalanceable allocation separately for proper percentage calculations
    rebalanceable_allocation = {}
    category_sub_class_mapping = {}  # Track which sub-classes belong to each category
    
    # Build mapping of categories to their sub-classes and check rebalanceability
    for category, sub_categories in sub_level_allocation.items():
        category_sub_class_mapping[category] = sub_categories
        rebalanceable_value_for_category = 0
        
        for sub_class, value in sub_categories.items():
            # Check if this specific sub-class is non-rebalanceable
            is_sub_class_non_rebalanceable = sub_class in non_rebalanceable_sub_classes
            is_category_non_rebalanceable = (category in non_rebalanceable_classes or 
                                           category in special_categories)
            
            if not (is_sub_class_non_rebalanceable or is_category_non_rebalanceable):
                rebalanceable_value_for_category += value
        
        if rebalanceable_value_for_category > 0:
            rebalanceable_allocation[category] = rebalanceable_value_for_category
    
    # Process top-level categories
    for category, current_value in top_level_allocation.items():
        # Check if category is rebalanceable (considering sub-classes)
        has_non_rebalanceable_sub_classes = False
        if category in category_sub_class_mapping:
            for sub_class in category_sub_class_mapping[category]:
                if sub_class in non_rebalanceable_sub_classes:
                    has_non_rebalanceable_sub_classes = True
                    break
        
        # Category is non-rebalanceable if:
        # 1. It's in non_rebalanceable_classes
        # 2. It's in special_categories  
        # 3. All its sub-classes are non-rebalanceable
        is_category_non_rebalanceable = (category in non_rebalanceable_classes or 
                                       category in special_categories)
        
        # For mixed categories (some sub-classes rebalanceable, some not), 
        # we'll mark as rebalanceable at top level but handle individual assets separately
        is_rebalanceable = not is_category_non_rebalanceable
        
        # CRITICAL FIX: Use Total Portfolio Value as denominator for percentage comparison
        # But use Constrained Target Value for ACTUAL TARGET amounts to respect non-rebalanceable constraints.
        
        # Current % Calculation Update (2025-12-14): 
        # User requested Current % to be based on "Rebalanceable Assets" for rebalanceable categories.
        # For non-rebalanceable (e.g. Property), we continue to use Total Portfolio.
        if is_rebalanceable and rebalanceable_value > 0:
             current_pct = (current_value / rebalanceable_value * 100)
        else:
             current_pct = (current_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0.0
        
        # Target % = target allocation from profile
        target_pct = target_allocations.get(category, 0.0) * 100
        
        # Ideal Target Value (unconstrained) - Theoretical target if all assets were liquid
        ideal_target_value = (target_pct / 100) * total_portfolio_value if total_portfolio_value > 0 else 0
        
        # Drift based on the Calculated Current % (Investable for Investable, Total for Non)
        drift = current_pct - target_pct
        
        # Calculate Constrained Target Value (FEASIBLE Target)
        # This is based on the Rebalanceable Portfolio, ensuring trades are realistic.
        constrained_target_value = 0
        
        if is_rebalanceable:
            # Calculate total target allocation for all rebalanceable assets
            total_rebalanceable_target_sum = 0
            for cat, weight in target_allocations.items():
                if cat not in non_rebalanceable_classes and cat not in special_categories:
                    total_rebalanceable_target_sum += weight
            
            if total_rebalanceable_target_sum > 0:
                # Normalize this asset's target relative to the rebalanceable pool
                raw_target_weight = target_allocations.get(category, 0.0)
                normalized_weight = raw_target_weight / total_rebalanceable_target_sum
                
                # Apply to Rebalanceable Portfolio Value for the FEASIBLE target amount
                constrained_target_value = normalized_weight * rebalanceable_value
            else:
                constrained_target_value = 0
        else:
            # For non-rebalanceable, the "Target" is effectively the current value (we can't move it)
            # OR we display the Ideal Target but suppress trading. 
            # Sticking to Ideal for display, but trades are suppressed by is_rebalanceable check.
            constrained_target_value = ideal_target_value

        # PRIMARY FIX: Use Constrained Value as the main 'target_value' for the report table
        # This ensures the user sees the achievable target, not the theoretical one requiring house sale.
        final_target_value = constrained_target_value if is_rebalanceable else ideal_target_value

        top_level_analysis.append({
            'level': 'top_level',
            'asset_class': category,
            'sub_category': category,
            'current_pct': current_pct,
            'target_pct': target_pct,
            'drift': drift,
            'current_value': current_value,
            'target_value': final_target_value, # Now Feasible
            'ideal_target_value': ideal_target_value, # Kept for reference
            'constrained_target_value': constrained_target_value,
            'is_rebalanceable': is_rebalanceable
        })
        
        # Generate trade recommendations based on FEASIBLE target
        if is_rebalanceable and abs(drift) > 5: # Threshold of 5% drift
            # Recalculate trade amount based on Feasible Target
            trade_amount = final_target_value - current_value
            
            if abs(trade_amount) > 1000: # Ignore tiny trades
                if trade_amount > 0:
                    recommended_trades.append(_("Buy ¥{amount} of '{category}' assets", amount=f"{abs(trade_amount):,.0f}", category=category))
                else:
                    recommended_trades.append(_("Sell ¥{amount} of '{category}' assets", amount=f"{abs(trade_amount):,.0f}", category=category))
    
    # Process sub-level categories
    for top_category, sub_categories in sub_level_allocation.items():
        category_weights = sub_category_weights.get(top_category, {})
        top_category_target_allocation = target_allocations.get(top_category, 0.0)
        
        # Check if parent category is rebalanceable
        parent_is_rebalanceable = top_category not in non_rebalanceable_classes and top_category not in special_categories
        
        for sub_category, current_value in sub_categories.items():
            # Current % Calculation Update (2025-12-14)
            if parent_is_rebalanceable and rebalanceable_value > 0:
                current_pct = (current_value / rebalanceable_value * 100)
            else:
                current_pct = (current_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0.0
            
            # Map English sub-category names to Chinese for target lookup
            # Use localized keys directly
            sub_category_key = sub_category
            
            # Calculate target percentage: sub_weight * parent_target_allocation * 100
            # parent_target_allocation is relative to Total Portfolio
            sub_weight = category_weights.get(sub_category_key, 0.0)
            
            target_pct = sub_weight * top_category_target_allocation * 100
            
            # Ideal Target Value (unconstrained)
            ideal_target_value = (target_pct / 100) * total_portfolio_value if total_portfolio_value > 0 else 0
            
            drift = current_pct - target_pct
            
            # Calculate Constrained Target Value (FEASIBLE Target)
            constrained_target_value = 0
            
            if parent_is_rebalanceable:
                # We need the same total_rebalanceable_target_sum as calculated in the top-level loop.
                # Recalculating here for safety.
                total_rebalanceable_target_sum = 0
                for cat, weight in target_allocations.items():
                    if cat not in non_rebalanceable_classes and cat not in special_categories:
                        total_rebalanceable_target_sum += weight
                
                if total_rebalanceable_target_sum > 0:
                    # Sub-class raw target weight = sub_weight * top_category_target_allocation
                    raw_sub_target_weight = sub_weight * top_category_target_allocation
                    
                    # Normalize relative to the TOTAL rebalanceable pool
                    normalized_sub_weight = raw_sub_target_weight / total_rebalanceable_target_sum
                    
                    # Apply to Rebalanceable Portfolio Value for FEASIBLE target
                    constrained_target_value = normalized_sub_weight * rebalanceable_value
                else:
                    constrained_target_value = 0
            else:
                constrained_target_value = ideal_target_value
            
            # PRIMARY FIX: Use Constrained Value as the main 'target_value'
            final_target_value = constrained_target_value if parent_is_rebalanceable else ideal_target_value
            
            sub_level_analysis.append({
                'level': 'sub_level',
                'asset_class': top_category,
                'sub_category': sub_category,
                'current_pct': current_pct,
                'target_pct': target_pct,
                'drift': drift,
                'current_value': current_value,
                'target_value': final_target_value, # Now Feasible
                'ideal_target_value': ideal_target_value,
                'constrained_target_value': constrained_target_value,
                'is_rebalanceable': parent_is_rebalanceable
            })
    
    # Sort both analyses by absolute drift (highest first)
    top_level_analysis.sort(key=lambda x: abs(x['drift']), reverse=True)
    sub_level_analysis.sort(key=lambda x: abs(x['drift']), reverse=True)
    
    return {
        'total_portfolio_value': total_portfolio_value,
        'non_rebalanceable_value': non_rebalanceable_value,
        'rebalanceable_value': rebalanceable_value,
        'top_level_table': top_level_analysis,
        'sub_level_table': sub_level_analysis,
        'rebalancing_table': top_level_analysis,  # Keep for backward compatibility
        'recommended_trades': recommended_trades,
        'hierarchical_recommendations': build_hierarchical_recommendations(top_level_analysis, sub_level_analysis),
        'needs_rebalancing': len(recommended_trades) > 0
    }


def build_hierarchical_recommendations(top_level_analysis, sub_level_analysis) -> List[Dict]:
    """
    Build hierarchical recommendations that group sub-class actions under top-level actions.
    
    Args:
        top_level_analysis: List of top-level rebalancing analysis data
        sub_level_analysis: List of sub-level rebalancing analysis data
        
    Returns:
        List of hierarchical recommendation dictionaries with nested structure
    """
    hierarchical_recommendations = []
    
    # Group sub-level items by their top-level category
    sub_by_top_category = {}
    for sub_item in sub_level_analysis:
        if not sub_item['is_rebalanceable']:
            continue
        top_category = sub_item['asset_class']
        if top_category not in sub_by_top_category:
            sub_by_top_category[top_category] = []
        sub_by_top_category[top_category].append(sub_item)
    
    # Process each top-level category
    for top_level_item in top_level_analysis:
        if not top_level_item['is_rebalanceable']:
            continue
            
        top_category = top_level_item['asset_class']
        top_drift = top_level_item['drift']
        
        # Get all sub-categories under this top-level category
        relevant_sub_categories = sub_by_top_category.get(top_category, [])
        if not relevant_sub_categories:
            continue
        
        # Calculate individual sub-category recommendations
        sub_recommendations = []
        total_sub_amount = 0
        
        for sub_item in relevant_sub_categories:
            sub_drift = sub_item['drift']
            sub_trade_amount = sub_item['target_value'] - sub_item['current_value']
            
            # Only include sub-categories that need significant rebalancing (>1% drift)
            if abs(sub_drift) <= 1:
                continue
                
            # Determine action for this sub-category
            if sub_trade_amount > 0:
                sub_action = _("Buy")
                sub_amount = abs(sub_trade_amount)
            else:
                sub_action = _("Sell")
                sub_amount = abs(sub_trade_amount)
            
            sub_recommendations.append({
                'sub_category': sub_item['sub_category'],
                'action': sub_action,
                'amount': sub_amount,
                'drift': sub_drift,
                'current_value': sub_item['current_value']
            })
            
            # Add to total (sell = positive, buy = negative for net calculation)
            if sub_trade_amount < 0:  # selling
                total_sub_amount += abs(sub_trade_amount)
            else:  # buying
                total_sub_amount -= abs(sub_trade_amount)
        
        # Skip if no meaningful sub-recommendations
        if not sub_recommendations:
            continue
            
        # Sort sub-recommendations by absolute drift (largest first)
        sub_recommendations.sort(key=lambda x: abs(x['drift']), reverse=True)
        
        # Determine top-level action based on net sub-category movements
        if total_sub_amount > 0:
            action_type = "sell"
            action_text = _("Sell")
            icon = "📉"
            total_amount = total_sub_amount
        else:
            action_type = "buy" 
            action_text = _("Buy")
            icon = "📈"
            total_amount = abs(total_sub_amount)
        
        # Only add if total amount is significant (>1000)
        if total_amount > 1000:
            hierarchical_recommendations.append({
                'top_level_category': top_category,
                'action_type': action_type,
                'action_text': action_text,
                'icon': icon,
                'total_amount': total_amount,
                'drift': top_drift,
                'sub_recommendations': sub_recommendations
            })
    
    # Sort by total amount (largest first)
    hierarchical_recommendations.sort(key=lambda x: x['total_amount'], reverse=True)
    
    return hierarchical_recommendations
