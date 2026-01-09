"""
Proportional Allocation Optimizer

Generates intelligent capital allocation recommendations that minimize overall
portfolio drift by distributing new capital across multiple under-allocated
asset classes proportionally to their drift magnitude.

Author: Personal Investment System
Date: October 14, 2025
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ProportionalAllocationOptimizer:
    """
    Generates proportional allocation recommendations to minimize total portfolio drift.
    
    Strategy:
    1. Identify all under-allocated rebalanceable asset classes
    2. Calculate normalized allocation weights based on drift magnitude
    3. Distribute new capital proportionally to close multiple gaps
    4. Calculate before/after portfolio drift metrics
    """
    
    def __init__(self):
        """Initialize the optimizer."""
        self.logger = logging.getLogger(__name__)
    
    def calculate_proportional_allocation(
        self, 
        new_capital: float,
        rebalancing_data: Dict,
        strategy: str = "drift_weighted",
        min_allocation_pct: float = 10.0
    ) -> Dict:
        """
        Calculate proportional allocation across under-allocated classes.
        
        Args:
            new_capital: Amount of new capital to allocate (CNY)
            rebalancing_data: Dictionary from build_rebalancing_analysis()
            strategy: Allocation strategy ("drift_weighted", "equal_weighted")
            min_allocation_pct: Minimum allocation percentage per class (default: 10%)
            
        Returns:
            {
                'allocations': [
                    {
                        'asset_class': '固定收益',
                        'asset_class_en': 'Fixed Income',
                        'amount': 55000,
                        'percentage': 55.0,
                        'current_drift': -8.38,
                        'new_drift': -3.21,
                        'gap_closed': 5.17,
                        'current_pct': 1.62,
                        'target_pct': 10.00,
                        'new_pct': 6.79
                    },
                    ...
                ],
                'total_impact': {
                    'current_total_drift': 15.1,
                    'new_total_drift': 7.8,
                    'drift_reduction': 7.3,
                    'drift_reduction_pct': 48.3
                },
                'strategy_used': 'drift_weighted',
                'num_classes': 3
            }
        """
        self.logger.info(f"Calculating proportional allocation for ¥{new_capital:,.0f} using '{strategy}' strategy")
        
        # Extract rebalanceable portfolio value
        rebalanceable_value = rebalancing_data.get('rebalanceable_value', 0)
        top_level_table = rebalancing_data.get('top_level_table', [])
        
        if rebalanceable_value == 0:
            self.logger.warning("Rebalanceable value is zero, cannot calculate allocation")
            return self._empty_result(strategy)
        
        # Filter for under-allocated, rebalanceable classes
        under_allocated = [
            item for item in top_level_table
            if item.get('is_rebalanceable', False) and item.get('drift', 0) < 0
        ]
        
        if not under_allocated:
            self.logger.info("No under-allocated rebalanceable classes found")
            return self._empty_result(strategy)
        
        self.logger.debug(f"Found {len(under_allocated)} under-allocated classes")
        
        # Calculate allocation weights based on strategy
        if strategy == "drift_weighted":
            allocations = self._calculate_drift_weighted_allocation(
                under_allocated, new_capital, rebalanceable_value, min_allocation_pct
            )
        elif strategy == "equal_weighted":
            allocations = self._calculate_equal_weighted_allocation(
                under_allocated, new_capital, rebalanceable_value
            )
        else:
            self.logger.error(f"Unknown strategy: {strategy}")
            return self._empty_result(strategy)
        
        # Calculate portfolio-wide impact
        total_impact = self._calculate_total_impact(
            top_level_table, allocations, rebalanceable_value
        )
        
        result = {
            'allocations': allocations,
            'total_impact': total_impact,
            'strategy_used': strategy,
            'num_classes': len(allocations)
        }
        
        self.logger.info(
            f"Generated {len(allocations)} allocations, "
            f"drift reduction: {total_impact['drift_reduction']:.1f}%"
        )
        
        return result
    
    def _calculate_drift_weighted_allocation(
        self,
        under_allocated: List[Dict],
        new_capital: float,
        rebalanceable_value: float,
        min_allocation_pct: float
    ) -> List[Dict]:
        """
        Calculate allocations weighted by drift magnitude.
        
        Larger drifts receive more capital to maximize drift reduction.
        """
        # Calculate total absolute drift
        total_abs_drift = sum(abs(item['drift']) for item in under_allocated)
        
        if total_abs_drift == 0:
            self.logger.warning("Total drift is zero, falling back to equal weighting")
            return self._calculate_equal_weighted_allocation(
                under_allocated, new_capital, rebalanceable_value
            )
        
        allocations = []
        
        for item in under_allocated:
            # Calculate weight proportional to drift magnitude
            weight = abs(item['drift']) / total_abs_drift
            allocation_amount = new_capital * weight
            allocation_pct = (allocation_amount / new_capital) * 100
            
            # Skip if below minimum threshold (unless it's the only class)
            if allocation_pct < min_allocation_pct and len(under_allocated) > 1:
                continue
            
            # Calculate new drift after allocation
            capital_impact_on_drift = (allocation_amount / rebalanceable_value) * 100
            new_drift = item['drift'] + capital_impact_on_drift
            gap_closed = abs(item['drift']) - abs(new_drift)
            
            # Calculate new percentage allocation
            current_value = item.get('current_value', 0)
            new_value = current_value + allocation_amount
            new_pct = (new_value / (rebalanceable_value + new_capital)) * 100
            
            allocations.append({
                'asset_class': item['asset_class'],
                'asset_class_en': item.get('asset_class_en', item['asset_class']),
                'amount': round(allocation_amount, 2),
                'percentage': round(allocation_pct, 2),
                'current_drift': round(item['drift'], 2),
                'new_drift': round(new_drift, 2),
                'gap_closed': round(gap_closed, 2),
                'current_pct': round(item.get('current_pct', 0), 2),
                'target_pct': round(item.get('target_pct', 0), 2),
                'new_pct': round(new_pct, 2)
            })
        
        # Normalize allocations to ensure they sum to new_capital
        total_allocated = sum(a['amount'] for a in allocations)
        if total_allocated > 0 and abs(total_allocated - new_capital) > 0.01:
            adjustment_factor = new_capital / total_allocated
            for allocation in allocations:
                allocation['amount'] = round(allocation['amount'] * adjustment_factor, 2)
                allocation['percentage'] = round((allocation['amount'] / new_capital) * 100, 2)
        
        return sorted(allocations, key=lambda x: x['amount'], reverse=True)
    
    def _calculate_equal_weighted_allocation(
        self,
        under_allocated: List[Dict],
        new_capital: float,
        rebalanceable_value: float
    ) -> List[Dict]:
        """
        Calculate allocations with equal weights across all under-allocated classes.
        """
        num_classes = len(under_allocated)
        allocation_per_class = new_capital / num_classes
        
        allocations = []
        
        for item in under_allocated:
            # Calculate new drift after allocation
            capital_impact_on_drift = (allocation_per_class / rebalanceable_value) * 100
            new_drift = item['drift'] + capital_impact_on_drift
            gap_closed = abs(item['drift']) - abs(new_drift)
            
            # Calculate new percentage allocation
            current_value = item.get('current_value', 0)
            new_value = current_value + allocation_per_class
            new_pct = (new_value / (rebalanceable_value + new_capital)) * 100
            
            allocations.append({
                'asset_class': item['asset_class'],
                'asset_class_en': item.get('asset_class_en', item['asset_class']),
                'amount': round(allocation_per_class, 2),
                'percentage': round((allocation_per_class / new_capital) * 100, 2),
                'current_drift': round(item['drift'], 2),
                'new_drift': round(new_drift, 2),
                'gap_closed': round(gap_closed, 2),
                'current_pct': round(item.get('current_pct', 0), 2),
                'target_pct': round(item.get('target_pct', 0), 2),
                'new_pct': round(new_pct, 2)
            })
        
        return sorted(allocations, key=lambda x: x['amount'], reverse=True)
    
    def _calculate_total_impact(
        self,
        top_level_table: List[Dict],
        allocations: List[Dict],
        rebalanceable_value: float
    ) -> Dict:
        """
        Calculate portfolio-wide impact of allocations.
        """
        # Calculate current total drift (sum of absolute drifts for rebalanceable classes)
        current_total_drift = sum(
            abs(item['drift']) for item in top_level_table
            if item.get('is_rebalanceable', False)
        )
        
        # Calculate new total drift after allocations
        # Create lookup for allocated amounts by class
        allocation_lookup = {a['asset_class']: a['amount'] for a in allocations}
        
        new_total_drift = 0
        for item in top_level_table:
            if not item.get('is_rebalanceable', False):
                continue
            
            allocated_amount = allocation_lookup.get(item['asset_class'], 0)
            if allocated_amount > 0:
                # Use new drift from allocations
                allocation_rec = next(a for a in allocations if a['asset_class'] == item['asset_class'])
                new_total_drift += abs(allocation_rec['new_drift'])
            else:
                # No allocation, drift unchanged
                new_total_drift += abs(item['drift'])
        
        drift_reduction = current_total_drift - new_total_drift
        drift_reduction_pct = (drift_reduction / current_total_drift * 100) if current_total_drift > 0 else 0
        
        return {
            'current_total_drift': round(current_total_drift, 2),
            'new_total_drift': round(new_total_drift, 2),
            'drift_reduction': round(drift_reduction, 2),
            'drift_reduction_pct': round(drift_reduction_pct, 1)
        }
    
    def _empty_result(self, strategy: str) -> Dict:
        """Return empty result structure."""
        return {
            'allocations': [],
            'total_impact': {
                'current_total_drift': 0,
                'new_total_drift': 0,
                'drift_reduction': 0,
                'drift_reduction_pct': 0
            },
            'strategy_used': strategy,
            'num_classes': 0
        }
