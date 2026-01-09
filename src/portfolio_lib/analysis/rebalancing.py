# portfolio_lib/analysis/rebalancing.py
"""
Module for generating portfolio rebalancing recommendations (at sub-category level)
and analyzing scenarios. Respects non-rebalanceable top-level classes.
Scenario analysis is adjusted for the rebalanceable portion of the portfolio.
Roadmap now reflects the adjusted scenario amounts.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional, Set

# Import functions/variables from other modules if needed
try:
    from ..core.asset_mapper import _get_taxonomy
except ImportError:
    print("Error: Could not import _get_taxonomy from core.asset_mapper. Ensure structure is correct.")
    def _get_taxonomy(): return {}

# Define a basic fallback currency formatter at the module level
def _fallback_currency_formatter(x, pos=None):
    """Basic fallback currency formatter."""
    if pd.isna(x): return "N/A"
    try: num_x = float(x); return f"{num_x:,.0f}"
    except (ValueError, TypeError): return str(x)

# Attempt to import the preferred formatter from utils
try:
    from ..utils.helpers import currency_formatter
    print("Using currency_formatter from utils.helpers")
except ImportError:
    print("Warning (rebalancing.py): Could not import currency_formatter from utils. Using basic fallback.")
    currency_formatter = _fallback_currency_formatter


# --- generate_rebalancing_recommendations (Keep as is - ID: rebalancing_py_final_review) ---
def generate_rebalancing_recommendations(
    current_allocation_sub_pct: Dict[str, float],
    target_allocation_sub: Dict[str, float],
    settings: Dict[str, Any]
) -> Dict[str, Any]:
    # (Code remains the same as previous version - ID: rebalancing_py_final_review)
    print("\nGenerating Rebalancing Recommendations (Sub-Category Level)...")
    taxonomy = _get_taxonomy(); analysis_params = settings.get('analysis_params', {}); threshold = analysis_params.get('rebalancing_threshold', 0.05)
    non_rebalanceable_top_classes: Set[str] = set(taxonomy.get('non_rebalanceable_classes', [])); sub_classes_map: Dict[str, List[str]] = taxonomy.get('sub_classes', {})
    sub_to_top_map: Dict[str, str] = {};
    for top, subs in sub_classes_map.items():
        for sub in subs: sub_to_top_map[sub] = top
    recommendations: Dict[str, Any] = {'actions': [], 'actions_needed': False}; all_sub_categories = set(current_allocation_sub_pct.keys()) | set(target_allocation_sub.keys())
    print(f"  - Drift Threshold: {threshold:.1%}"); print(f"  - Non-Rebalanceable Top-Level Classes: {non_rebalanceable_top_classes or 'None'}")
    for sub_category in sorted(list(all_sub_categories)):
        parent_top_class = sub_to_top_map.get(sub_category)
        if parent_top_class in non_rebalanceable_top_classes: continue
        elif parent_top_class is None: print(f"  - Skipping '{sub_category}': Could not determine parent top-level class from taxonomy."); continue
        current_pct = current_allocation_sub_pct.get(sub_category, 0.0); target_pct = target_allocation_sub.get(sub_category, 0.0); drift = current_pct - target_pct
        if abs(drift) > threshold:
            recommendations['actions_needed'] = True; action_type = "卖出 (Sell)" if drift > 0 else "买入 (Buy)"; amount_pct = abs(drift)
            action_details = {'category': sub_category, 'parent_category': parent_top_class, 'action': action_type, 'current_pct': current_pct, 'target_pct': target_pct, 'drift': drift, 'amount_pct': amount_pct }
            recommendations['actions'].append(action_details); current_str = f"{current_pct:.1%}"; target_str = f"{target_pct:.1%}"; drift_indicator = "+" if drift > 0 else ""
            print(f"  - Action for '{sub_category}' (in '{parent_top_class}'): {action_type} {amount_pct:.1%}"); print(f"    (Current: {current_str} vs Target: {target_str}, Drift: {drift_indicator}{drift:.1%})")
    if not recommendations['actions_needed']: print("  No rebalancing actions needed based on the current threshold.")
    else: recommendations['actions'].sort(key=lambda x: x['amount_pct'], reverse=True)
    print("Rebalancing recommendation generation complete.")
    return recommendations

# --- IMPROVED analyze_rebalancing_scenarios ---
def analyze_rebalancing_scenarios(
    current_holdings_values: Dict[str, float],
    target_allocation: Dict[str, float],
    settings: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyzes rebalancing scenarios while respecting non-rebalanceable classes.

    Args:
        current_holdings_values: Dictionary of current holdings values by asset class
        target_allocation: Dictionary of target allocations by asset class (percentages)
        settings: The loaded configuration dictionary

    Returns:
        A dictionary containing scenario analysis results
    """
    # Initialize results with defaults to prevent None return
    results = {
        'summary': {
            'current_total': 0,
            'new_investment': 0,
            'total_rebalanceable': 0, 
            'total_non_rebalanceable': 0,
            'tax_rate': 0,
            'transaction_cost_rate': 0
        },
        'full_rebalancing_adjusted': {
            'sell_actions': {},
            'buy_actions': {},
            'total_sell_value': 0,
            'total_buy_value': 0,
            'funds_available': 0,
            'funding_shortfall': 0,
            'estimated_transaction_costs': 0,
            'estimated_tax_impact': 0
        },
        'new_money_only_adjusted': {
            'allocations': {},
            'remaining_buy_gaps': {},
            'estimated_transaction_costs': 0,
            'total_underweight_needed': 0,
            'coverage_ratio': 0
        },
        'gaps_details_rebal': {}
    }
    
    try:
        print("\nAnalyzing Rebalancing Scenarios (Adjusted for Rebalanceable Portion)...")
        
        if not current_holdings_values:
            print("Error: Empty current holdings values provided")
            return results
            
        if not target_allocation:
            print("Error: Empty target allocation provided")
            return results
            
        # Get parameters from settings
        analysis_params = settings.get('analysis_params', {})
        new_investment = analysis_params.get('new_investment', 0.0)
        tax_rate = analysis_params.get('tax_rate', 0.0)
        transaction_cost_rate = analysis_params.get('transaction_cost_rate', 0.001)
        
        # Get taxonomy and non-rebalanceable classes
        taxonomy = _get_taxonomy()
        non_rebalanceable = set(taxonomy.get('non_rebalanceable_classes', []))
        curr_fmt = currency_formatter
        
        # Split holdings into rebalanceable and non-rebalanceable
        rebalanceable_holdings = {k: v for k, v in current_holdings_values.items() if k not in non_rebalanceable}
        non_rebalanceable_holdings = {k: v for k, v in current_holdings_values.items() if k in non_rebalanceable}
        
        # Calculate totals
        total_current = sum(current_holdings_values.values())
        total_rebalanceable = sum(rebalanceable_holdings.values())
        total_non_rebalanceable = sum(non_rebalanceable_holdings.values())
        pct_non_rebalanceable = (total_non_rebalanceable / total_current) if total_current > 0 else 0.0
        
        # Print summary info
        print(f"  - Current Total: {curr_fmt(total_current)}")
        print(f"  -   Rebalanceable Portion: {curr_fmt(total_rebalanceable)} ({1.0 - pct_non_rebalanceable:.1%})")
        print(f"  -   Non-Rebalanceable Portion ({non_rebalanceable or 'None'}): {curr_fmt(total_non_rebalanceable)} ({pct_non_rebalanceable:.1%})")
        print(f"  - New Investment: {curr_fmt(new_investment)}")
        print(f"  - Tax Rate: {tax_rate:.1%}, Transaction Cost Rate: {transaction_cost_rate:.3%}")
        
        # Calculate adjusted target allocation for rebalanceable portion
        target_rebalanceable_sum = sum(v for k, v in target_allocation.items() if k not in non_rebalanceable)
        adjusted_target_allocation = {}
        
        # Handle case where target allocation for rebalanceable assets sums to zero
        if abs(target_rebalanceable_sum) < 1e-6:
            print("Warning: Target allocation for rebalanceable assets sums to zero or is negligible. Using equal weights.")
            rebalanceable_keys = list(rebalanceable_holdings.keys())
            count = len(rebalanceable_keys)
            if count > 0:
                equal_weight = 1.0 / count
                adjusted_target_allocation = {k: equal_weight for k in rebalanceable_keys}
            else:
                print("Error: No rebalanceable assets found.")
                return results
        else:
            # Calculate adjusted target allocation
            all_rebal_keys = set(rebalanceable_holdings.keys()) | {k for k, v in target_allocation.items() 
                                                                if k not in non_rebalanceable and v > 1e-6}
            for k in all_rebal_keys:
                if k not in non_rebalanceable:
                    adjusted_target_allocation[k] = target_allocation.get(k, 0.0) / target_rebalanceable_sum
        
        print("\n  Adjusted Target Allocation (for Rebalanceable Portion):")
        print(f"    { {k: f'{v:.1%}' for k, v in sorted(adjusted_target_allocation.items())} }")
        
        # Calculate target values and gaps
        target_total_rebalanceable_value = total_rebalanceable + new_investment
        gaps_rebal: Dict[str, Dict[str, Any]] = {}
        
        for asset in adjusted_target_allocation.keys():
            current_rebal_value = rebalanceable_holdings.get(asset, 0.0)
            target_rebal_pct = adjusted_target_allocation.get(asset, 0.0)
            target_rebal_value_ideal = target_total_rebalanceable_value * target_rebal_pct
            gap_rebal_value = target_rebal_value_ideal - current_rebal_value
            
            gaps_rebal[asset] = {
                'current_value': current_rebal_value,
                'target_value_ideal': target_rebal_value_ideal,
                'gap_value': gap_rebal_value
            }
        
        # Scenario 1: Full Rebalancing within Rebalanceable Portion
        print("\n  Scenario 1: Full Rebalancing (within Rebalanceable Portion)")
        sell_actions_rebal: Dict[str, float] = {}
        buy_actions_rebal: Dict[str, float] = {}
        total_sell_value_rebal = 0.0
        total_buy_value_rebal = 0.0
        full_rebal_trans_costs_rebal = 0.0
        
        for asset, details in gaps_rebal.items():
            gap = details['gap_value']
            if gap < -1e-6:  # Need to sell
                amount_to_sell = abs(gap)
                sell_actions_rebal[asset] = amount_to_sell
                total_sell_value_rebal += amount_to_sell
                full_rebal_trans_costs_rebal += amount_to_sell * transaction_cost_rate
            elif gap > 1e-6:  # Need to buy
                amount_to_buy = gap
                buy_actions_rebal[asset] = amount_to_buy
                total_buy_value_rebal += amount_to_buy
                full_rebal_trans_costs_rebal += amount_to_buy * transaction_cost_rate
        
        estimated_tax_rebal = total_sell_value_rebal * tax_rate
        funds_available_rebal = total_sell_value_rebal + new_investment
        funding_shortfall_rebal = max(0, total_buy_value_rebal - funds_available_rebal)
        
        print(f"    - Total to Sell (Rebalanceable Assets): {curr_fmt(total_sell_value_rebal)}")
        print(f"    - Total to Buy (Rebalanceable Assets): {curr_fmt(total_buy_value_rebal)}")
        print(f"    - Funds from Sells + New Investment: {curr_fmt(funds_available_rebal)}")
        
        if funding_shortfall_rebal > 1e-2:
            print(f"    - **Funding Shortfall:** {curr_fmt(funding_shortfall_rebal)} **(Required Buy > Available Funds)**")
        else:
            print(f"    - Funding Status: Sufficient")
            
        print(f"    - Estimated Transaction Costs: {curr_fmt(full_rebal_trans_costs_rebal)}")
        print(f"    - Estimated Tax Impact (Simplified): {curr_fmt(estimated_tax_rebal)}")
        
        # Scenario 2: New Money Only Rebalancing
        print("\n  Scenario 2: New Money Only Rebalancing (within Rebalanceable Portion)")
        new_money_allocations_rebal: Dict[str, float] = {}
        remaining_buy_gaps_rebal: Dict[str, float] = {}
        new_money_trans_costs_rebal = 0.0
        allocation_ratio_rebal = 0.0
        
        total_underweight_needed_rebal = sum(details['gap_value'] 
                                            for asset, details in gaps_rebal.items() 
                                            if details['gap_value'] > 1e-6)
        
        if new_investment > 0 and total_underweight_needed_rebal > 0:
            allocation_ratio_rebal = min(1.0, new_investment / total_underweight_needed_rebal)
            print(f"    - New money ({curr_fmt(new_investment)}) can cover {allocation_ratio_rebal:.1%} of the rebalanceable buy gap ({curr_fmt(total_underweight_needed_rebal)}).")
            
            for asset, details in gaps_rebal.items():
                if details['gap_value'] > 1e-6:
                    allocate_amount = details['gap_value'] * allocation_ratio_rebal
                    new_money_allocations_rebal[asset] = allocate_amount
                    remaining_buy_gaps_rebal[asset] = details['gap_value'] - allocate_amount
                    new_money_trans_costs_rebal += allocate_amount * transaction_cost_rate
            
            print(f"    - Allocations using new money: { {k: f'{curr_fmt(v)}' for k, v in new_money_allocations_rebal.items()} }")
            print(f"    - Estimated Transaction Costs: {curr_fmt(new_money_trans_costs_rebal)}")
            print(f"    - Remaining Buy Gaps after new money: { {k: f'{curr_fmt(v)}' for k, v in remaining_buy_gaps_rebal.items() if v > 1e-6} }")
        elif new_investment <= 0:
            print("    - No new investment provided. Cannot perform this scenario.")
        else:
            print("    - No rebalanceable assets are significantly underweight. New money cannot be allocated to rebalance.")
        
        # Prepare final results
        results = {
            'summary': {
                'current_total': total_current,
                'new_investment': new_investment,
                'total_rebalanceable': total_rebalanceable,
                'total_non_rebalanceable': total_non_rebalanceable,
                'tax_rate': tax_rate,
                'transaction_cost_rate': transaction_cost_rate
            },
            'full_rebalancing_adjusted': {
                'sell_actions': sell_actions_rebal,
                'buy_actions': buy_actions_rebal,
                'total_sell_value': total_sell_value_rebal,
                'total_buy_value': total_buy_value_rebal,
                'funds_available': funds_available_rebal,
                'funding_shortfall': funding_shortfall_rebal,
                'estimated_transaction_costs': full_rebal_trans_costs_rebal,
                'estimated_tax_impact': estimated_tax_rebal
            },
            'new_money_only_adjusted': {
                'allocations': new_money_allocations_rebal,
                'remaining_buy_gaps': remaining_buy_gaps_rebal,
                'estimated_transaction_costs': new_money_trans_costs_rebal,
                'total_underweight_needed': total_underweight_needed_rebal,
                'coverage_ratio': allocation_ratio_rebal
            },
            'gaps_details_rebal': gaps_rebal
        }
        
        print("Adjusted rebalancing scenario analysis complete.")
        return results
        
    except Exception as e:
        import traceback
        print(f"Error in analyze_rebalancing_scenarios: {e}")
        print(traceback.format_exc())
        # Still return the partially populated results rather than None
        return results

# --- IMPROVED generate_roadmap_text ---
def generate_roadmap_text(
    scenario_results: Optional[Dict[str, Any]], # Changed input: Can now handle None
    settings: Dict[str, Any]
    ) -> str:
    """
    Generates a text-based implementation roadmap based on the calculated
    buy/sell amounts from the 'full_rebalancing_adjusted' scenario.

    Args:
        scenario_results: The dictionary returned by analyze_rebalancing_scenarios.
                          It must contain the 'full_rebalancing_adjusted' key.
                          Can handle None or missing keys.
        settings: The loaded configuration dictionary.

    Returns:
        A string containing the formatted roadmap text.
    """
    roadmap_lines = ["\n--- 再平衡实施路线图 (Rebalancing Implementation Roadmap) ---"]
    
    # Handle case where scenario_results is None
    if scenario_results is None:
        roadmap_lines.append("\n错误：未提供场景分析结果。(Error: No scenario analysis results provided.)")
        return "\n".join(roadmap_lines)
    
    # Get settings and format helpers
    analysis_params = settings.get('analysis_params', {})
    min_transaction_amount = analysis_params.get('min_transaction_amount', 0)
    summary_info = scenario_results.get('summary', {})
    full_rebal_adj = scenario_results.get('full_rebalancing_adjusted')
    
    # Display total value
    total_value = summary_info.get('current_total', 0.0)
    roadmap_lines.append(f"投资组合总值 (Portfolio Total Value): {currency_formatter(total_value)}")
    
    # Handle missing full_rebalancing_adjusted data
    if full_rebal_adj is None:
        roadmap_lines.append("\n错误：未能获取调整后的完全再平衡情景数据。(Error: Adjusted full rebalancing scenario data not found.)")
        return "\n".join(roadmap_lines)
    
    # Get buy/sell actions directly from the adjusted scenario results
    sell_actions_dict = full_rebal_adj.get('sell_actions', {})  # {asset: amount}
    buy_actions_dict = full_rebal_adj.get('buy_actions', {})    # {asset: amount}
    
    # Verify we have valid data
    if not isinstance(sell_actions_dict, dict) or not isinstance(buy_actions_dict, dict):
        roadmap_lines.append("\n错误：买入/卖出行动数据格式无效。(Error: Buy/sell actions data has invalid format.)")
        return "\n".join(roadmap_lines)
    
    # Filter actions by minimum transaction amount
    sell_actions_filtered = {k: v for k, v in sell_actions_dict.items() if v >= min_transaction_amount}
    buy_actions_filtered = {k: v for k, v in buy_actions_dict.items() if v >= min_transaction_amount}
    skipped_sell = {k: v for k, v in sell_actions_dict.items() if v < min_transaction_amount}
    skipped_buy = {k: v for k, v in buy_actions_dict.items() if v < min_transaction_amount}
    skipped_actions_count = len(skipped_sell) + len(skipped_buy)
    
    # Check if any actions remain after filtering
    actions_needed = bool(sell_actions_filtered) or bool(buy_actions_filtered)
    
    if not actions_needed:
        roadmap_lines.append("\n根据最低交易额过滤后，无需立即进行交易。(No trades needed after applying minimum transaction amount.)")
        # Optionally list skipped actions here if desired
        if skipped_actions_count > 0:
            roadmap_lines.append(f"\n注意: 以下 {skipped_actions_count} 项调整因金额小于最低交易额 ({currency_formatter(min_transaction_amount)}) 而被跳过:")
            for cat, val in sorted(skipped_sell.items(), key=lambda item: item[1], reverse=True):
                roadmap_lines.append(f"  - 卖出 (Sell) {cat}: {currency_formatter(val)}")
            for cat, val in sorted(skipped_buy.items(), key=lambda item: item[1], reverse=True):
                roadmap_lines.append(f"  - 买入 (Buy) {cat}: {currency_formatter(val)}")
        return "\n".join(roadmap_lines)
    
    # Use the potentially imported or fallback formatter
    curr_fmt = currency_formatter
    
    # Sort actions by amount descending for display
    sell_actions_list = sorted(sell_actions_filtered.items(), key=lambda item: item[1], reverse=True)
    buy_actions_list = sorted(buy_actions_filtered.items(), key=lambda item: item[1], reverse=True)
    
    if sell_actions_list:
        roadmap_lines.append("\n第一步: 减持以下资产类别 (Step 1: Reduce Holdings - Top-Level Rebalanceable)")
        for category, amount_value in sell_actions_list:
            # Calculate percentage relative to *rebalanceable* total for context
            rebal_total = summary_info.get('total_rebalanceable', total_value)  # Use rebalanceable total if available
            pct_of_rebal = (amount_value / rebal_total) * 100 if rebal_total > 0 else 0
            roadmap_lines.append(f"  - 卖出 (Sell) {category}: 约 {curr_fmt(amount_value)} ({pct_of_rebal:.1f}% of rebalanceable part)")
    
    if buy_actions_list:
        roadmap_lines.append("\n第二步: 增持以下资产类别 (Step 2: Increase Holdings - Top-Level Rebalanceable)")
        for category, amount_value in buy_actions_list:
            rebal_total = summary_info.get('total_rebalanceable', total_value)
            pct_of_rebal = (amount_value / rebal_total) * 100 if rebal_total > 0 else 0
            roadmap_lines.append(f"  - 买入 (Buy) {category}: 约 {curr_fmt(amount_value)} ({pct_of_rebal:.1f}% of rebalanceable part)")
    
    if skipped_actions_count > 0:
        roadmap_lines.append(f"\n注意: 以下 {skipped_actions_count} 项调整因金额小于最低交易额 ({curr_fmt(min_transaction_amount)}) 而被跳过:")
        for cat, val in sorted(skipped_sell.items(), key=lambda item: item[1], reverse=True):
            roadmap_lines.append(f"  - 卖出 (Sell) {cat}: {curr_fmt(val)}")
        for cat, val in sorted(skipped_buy.items(), key=lambda item: item[1], reverse=True):
            roadmap_lines.append(f"  - 买入 (Buy) {cat}: {curr_fmt(val)}")
    
    # Implementation Advice
    roadmap_lines.append("\n实施建议 (Implementation Advice):")
    roadmap_lines.append("  - 考虑分批调整，尤其对大额交易，以降低市场时机风险。(Consider phasing large trades.)")
    roadmap_lines.append("  - 优先使用新增投资或分红直接投向目标配置，减少交易成本和税负。(Prioritize new funds/dividends for rebalancing.)")
    roadmap_lines.append("  - 仔细评估每笔交易的成本（手续费、滑点）和潜在税收影响。(Evaluate transaction costs and taxes carefully.)")
    roadmap_lines.append("  - 定期（如每季度或每年）回顾并根据需要重复此分析。(Review periodically.)")
    
    return "\n".join(roadmap_lines)
