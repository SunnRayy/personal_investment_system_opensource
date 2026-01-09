"""
Sub-Class Analyzer

Breaks down top-level asset class allocation recommendations into specific
sub-class guidance, providing detailed recommendations for where to deploy
capital within a broad asset category.

Author: Personal Investment System
Date: October 14, 2025
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class SubClassAnalyzer:
    """
    Breaks down top-level allocation recommendations into sub-class guidance.
    
    Provides specific sub-class recommendations with priority rankings based on
    drift magnitude and alignment with portfolio targets.
    """
    
    def __init__(self):
        """Initialize the analyzer."""
        self.logger = logging.getLogger(__name__)
        
        # Priority thresholds
        self.HIGH_PRIORITY_THRESHOLD = 3.0  # drift > 3%
        self.MEDIUM_PRIORITY_THRESHOLD = 1.0  # 1% < drift <= 3%
    
    def generate_sub_class_breakdown(
        self,
        target_asset_class: str,
        allocation_amount: float,
        rebalancing_data: Dict
    ) -> Dict:
        """
        Generate sub-class allocation breakdown for a top-level asset class.
        
        Args:
            target_asset_class: Top-level class (e.g., "固定收益", "股票")
            allocation_amount: Total amount to allocate to this class
            rebalancing_data: Dictionary from build_rebalancing_analysis()
            
        Returns:
            {
                'asset_class': '固定收益',
                'total_amount': 55000,
                'sub_allocations': [
                    {
                        'sub_class': 'US Government Bonds',
                        'sub_class_cn': '美国政府债券',
                        'amount': 35000,
                        'percentage': 63.6,
                        'priority': 'HIGH',
                        'current_pct': 0.5,
                        'target_pct': 6.0,
                        'drift': -5.5,
                        'new_pct': 3.2,
                        'new_drift': -2.8,
                        'rationale': 'Largest gap within Fixed Income category'
                    },
                    ...
                ],
                'num_sub_classes': 3
            }
        """
        self.logger.info(
            f"Generating sub-class breakdown for {target_asset_class}, "
            f"allocation: ¥{allocation_amount:,.0f}"
        )
        
        # Extract sub-level data for target class
        sub_level_table = rebalancing_data.get('sub_level_table', [])
        target_sub_classes = [
            item for item in sub_level_table
            if item.get('asset_class') == target_asset_class
        ]
        
        if not target_sub_classes:
            self.logger.warning(f"No sub-classes found for {target_asset_class}")
            return self._empty_result(target_asset_class, allocation_amount)
        
        # Filter for under-allocated sub-classes
        under_allocated_subs = [
            item for item in target_sub_classes
            if item.get('drift', 0) < 0
        ]
        
        if not under_allocated_subs:
            self.logger.info(f"No under-allocated sub-classes in {target_asset_class}")
            # If no under-allocated, distribute equally among all
            under_allocated_subs = target_sub_classes
        
        self.logger.debug(f"Found {len(under_allocated_subs)} sub-classes to allocate")
        
        # Calculate proportional allocation
        sub_allocations = self._calculate_sub_allocations(
            under_allocated_subs, allocation_amount, rebalancing_data
        )
        
        result = {
            'asset_class': target_asset_class,
            'total_amount': allocation_amount,
            'sub_allocations': sub_allocations,
            'num_sub_classes': len(sub_allocations)
        }
        
        self.logger.info(f"Generated {len(sub_allocations)} sub-class recommendations")
        
        return result
    
    def _calculate_sub_allocations(
        self,
        sub_classes: List[Dict],
        total_allocation: float,
        rebalancing_data: Dict
    ) -> List[Dict]:
        """
        Calculate allocation amounts for each sub-class.
        
        Uses drift-weighted allocation similar to top-level logic.
        """
        # Calculate total absolute drift
        total_abs_drift = sum(abs(item.get('drift', 0)) for item in sub_classes)
        
        if total_abs_drift == 0:
            # Equal weighting if no drift data
            self.logger.debug("No drift data, using equal weighting for sub-classes")
            weights = {item['sub_category']: 1.0 / len(sub_classes) for item in sub_classes}
        else:
            # Drift-weighted allocation
            weights = {
                item['sub_category']: abs(item.get('drift', 0)) / total_abs_drift
                for item in sub_classes
            }
        
        # Get rebalanceable value for impact calculation
        rebalanceable_value = rebalancing_data.get('rebalanceable_value', 1)
        
        sub_allocations = []
        
        for item in sub_classes:
            sub_class = item['sub_category']
            weight = weights[sub_class]
            allocation_amount = total_allocation * weight
            allocation_pct = (allocation_amount / total_allocation) * 100
            
            # Skip very small allocations (< 5%)
            if allocation_pct < 5.0 and len(sub_classes) > 3:
                continue
            
            # Calculate new metrics after allocation
            current_pct = item.get('current_pct', 0)
            target_pct = item.get('target_pct', 0)
            drift = item.get('drift', 0)
            
            # Impact on drift
            capital_impact = (allocation_amount / rebalanceable_value) * 100
            new_drift = drift + capital_impact
            
            # New percentage
            current_value = item.get('current_value', 0)
            new_value = current_value + allocation_amount
            new_pct = (new_value / (rebalanceable_value + total_allocation)) * 100
            
            # Determine priority
            priority = self._determine_priority(abs(drift))
            
            # Generate rationale
            rationale = self._generate_rationale(
                sub_class, drift, target_pct, current_pct
            )
            
            # Language mapping for common sub-classes
            sub_class_cn = self._get_chinese_name(sub_class)
            
            sub_allocations.append({
                'sub_class': sub_class,
                'sub_class_cn': sub_class_cn,
                'amount': round(allocation_amount, 2),
                'percentage': round(allocation_pct, 2),
                'priority': priority,
                'current_pct': round(current_pct, 2),
                'target_pct': round(target_pct, 2),
                'drift': round(drift, 2),
                'new_pct': round(new_pct, 2),
                'new_drift': round(new_drift, 2),
                'rationale': rationale
            })
        
        # Sort by priority and amount
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        sub_allocations.sort(
            key=lambda x: (priority_order.get(x['priority'], 3), -x['amount'])
        )
        
        # Normalize to ensure sum equals total_allocation
        total_allocated = sum(a['amount'] for a in sub_allocations)
        if total_allocated > 0 and abs(total_allocated - total_allocation) > 0.01:
            adjustment_factor = total_allocation / total_allocated
            for allocation in sub_allocations:
                allocation['amount'] = round(allocation['amount'] * adjustment_factor, 2)
                allocation['percentage'] = round((allocation['amount'] / total_allocation) * 100, 2)
        
        return sub_allocations
    
    def _determine_priority(self, abs_drift: float) -> str:
        """Determine priority level based on drift magnitude."""
        if abs_drift >= self.HIGH_PRIORITY_THRESHOLD:
            return 'HIGH'
        elif abs_drift >= self.MEDIUM_PRIORITY_THRESHOLD:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_rationale(
        self,
        sub_class: str,
        drift: float,
        target_pct: float,
        current_pct: float
    ) -> str:
        """Generate human-readable rationale for recommendation."""
        abs_drift = abs(drift)
        
        if abs_drift >= self.HIGH_PRIORITY_THRESHOLD:
            return f"Largest gap (current: {current_pct:.1f}%, target: {target_pct:.1f}%)"
        elif abs_drift >= self.MEDIUM_PRIORITY_THRESHOLD:
            return f"Moderate gap requiring attention ({abs_drift:.1f}% below target)"
        else:
            return "Minor adjustment to optimize allocation"
    
    def _get_chinese_name(self, sub_class: str) -> str:
        """Map English sub-class names to Chinese."""
        mapping = {
            'Domestic Equity ETF': '国内股票ETF',
            'US Equity ETF': '美国股票ETF',
            'US Stock RSU': '公司美股RSU',
            'Emerging Market Equity': '新兴市场股票',
            'Domestic Government Bonds': '国内政府债券',
            'US Government Bonds': '美国政府债券',
            'Corporate Bonds': '企业债券',
            'Money Market': '货币市场',
            'Bank Wealth Management': '银行理财',
            'Residential Real Estate': '住宅地产',
            'Commercial Real Estate': '商业地产',
            'REITs': '房地产信托',
            'Gold': '黄金',
            'Other Precious Metals': '其他贵金属',
            'Energy': '能源',
            'Agricultural Products': '农产品',
            'Cash': '现金',
            'Time Deposits': '定期存款',
            'Cryptocurrency': '加密货币',
            'Venture Capital': '创业投资',
            'Private Equity': '风险投资'
        }
        return mapping.get(sub_class, sub_class)
    
    def _empty_result(self, asset_class: str, allocation_amount: float) -> Dict:
        """Return empty result structure."""
        return {
            'asset_class': asset_class,
            'total_amount': allocation_amount,
            'sub_allocations': [],
            'num_sub_classes': 0
        }
