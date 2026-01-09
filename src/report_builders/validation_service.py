"""
Validation Service for HTML Report Data Consistency

This module provides validation checkpoints to ensure data consistency
across Portfolio, Action Compass, and Market Thermometer tabs.

Author: Personal Investment System
Date: October 20, 2025
"""

import logging
import hashlib
import json
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ValidationService:
    """
    Validate data consistency across report modules.
    
    This service performs cross-module validation to detect data
    inconsistencies, calculation errors, and ensure that Portfolio
    and Action Compass tabs display consistent information.
    """
    
    def __init__(self):
        """Initialize validation service."""
        self.logger = logging.getLogger(__name__)
        self.validation_checks = []
    
    def validate_consistency(
        self,
        portfolio_values: Dict[str, float],
        rebalancing_data: Dict[str, Any],
        recommendations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Cross-validate data consistency across modules.
        
        Args:
            portfolio_values: Dict with total_portfolio_value, rebalanceable_value, etc.
            rebalancing_data: Dict from build_rebalancing_analysis()
            recommendations: List of recommendation dicts
            
        Returns:
            Validation report with checks, summary, and overall status
        """
        self.validation_checks = []
        
        # Check 1: Rebalanceable value consistency
        self._check_rebalanceable_value_match(portfolio_values, rebalancing_data)
        
        # Check 2: Financial impacts use rebalanceable value
        self._check_financial_impacts(recommendations, portfolio_values)
        
        # Check 3: Asset allocations sum to 100%
        self._check_allocation_sum(rebalancing_data)
        
        # Check 4: Non-rebalanceable assets correctly marked
        self._check_non_rebalanceable_marking(rebalancing_data)
        
        # Check 5: Target values calculated correctly
        self._check_target_values(rebalancing_data, portfolio_values)
        
        # Generate summary
        summary = self._generate_summary()
        
        return {
            'checks': self.validation_checks,
            'summary': summary,
            'overall_status': self._determine_overall_status(summary),
            'timestamp': datetime.now().isoformat()
        }
    
    def _check_rebalanceable_value_match(
        self,
        portfolio_values: Dict[str, float],
        rebalancing_data: Dict[str, Any]
    ):
        """Verify rebalanceable values match between portfolio and rebalancing."""
        rebal_from_portfolio = portfolio_values.get('rebalanceable_value', 0)
        rebal_from_analysis = rebalancing_data.get('rebalanceable_value', 0)
        
        tolerance = 1  # Allow ¥1 rounding difference
        diff = abs(rebal_from_portfolio - rebal_from_analysis)
        
        if diff > tolerance:
            self.validation_checks.append({
                'check': 'rebalanceable_value_match',
                'status': 'FAIL',
                'message': (
                    f'Rebalanceable value mismatch: '
                    f'portfolio=¥{rebal_from_portfolio:,.0f} vs '
                    f'rebalancing=¥{rebal_from_analysis:,.0f} '
                    f'(diff: ¥{diff:,.0f})'
                ),
                'severity': 'CRITICAL'
            })
        else:
            self.validation_checks.append({
                'check': 'rebalanceable_value_match',
                'status': 'PASS',
                'message': f'Rebalanceable values consistent: ¥{rebal_from_portfolio:,.0f}',
                'severity': 'INFO'
            })
    
    def _check_financial_impacts(
        self,
        recommendations: List[Dict[str, Any]],
        portfolio_values: Dict[str, float]
    ):
        """Verify financial impacts don't exceed rebalanceable value."""
        rebalanceable_value = portfolio_values.get('rebalanceable_value', 0)
        
        if not recommendations:
            self.validation_checks.append({
                'check': 'financial_impact_reasonable',
                'status': 'SKIP',
                'message': 'No recommendations to validate',
                'severity': 'INFO'
            })
            return
        
        issues_found = 0
        for rec in recommendations:
            impact = rec.get('impact', {})
            dollar_value = impact.get('dollar_value', 0)
            
            # Financial impact should not exceed rebalanceable value by more than 10%
            max_reasonable = rebalanceable_value * 1.1
            
            if dollar_value > max_reasonable:
                self.validation_checks.append({
                    'check': 'financial_impact_reasonable',
                    'status': 'WARN',
                    'message': (
                        f"Recommendation '{rec.get('title', 'Unknown')}' has "
                        f"impact ¥{dollar_value:,.0f} which exceeds rebalanceable "
                        f"value ¥{rebalanceable_value:,.0f}"
                    ),
                    'severity': 'MEDIUM'
                })
                issues_found += 1
        
        if issues_found == 0:
            self.validation_checks.append({
                'check': 'financial_impact_reasonable',
                'status': 'PASS',
                'message': f'All {len(recommendations)} recommendations have reasonable financial impacts',
                'severity': 'INFO'
            })
    
    def _check_allocation_sum(self, rebalancing_data: Dict[str, Any]):
        """Verify rebalanceable allocations sum to 100%."""
        top_level_table = rebalancing_data.get('top_level_table', [])
        
        if not top_level_table:
            self.validation_checks.append({
                'check': 'allocation_sum_100',
                'status': 'SKIP',
                'message': 'No allocation data to validate',
                'severity': 'INFO'
            })
            return
        
        # Sum current_pct for rebalanceable assets only
        rebalanceable_items = [
            item for item in top_level_table
            if item.get('is_rebalanceable', False)
        ]
        
        if not rebalanceable_items:
            self.validation_checks.append({
                'check': 'allocation_sum_100',
                'status': 'WARN',
                'message': 'No rebalanceable assets found in allocation data',
                'severity': 'LOW'
            })
            return
        
        # CRITICAL FIX: Sum target_pct (Strategy) instead of current_pct (Actual Allocation)
        # current_pct is relative to Total Portfolio and will naturally be <100% if non-rebalanceable assets exist (like House).
        # target_pct comes from the Risk Profile and should sum to 100% for the Investable Portfolio.
        total_pct = sum(item.get('target_pct', 0) for item in rebalanceable_items)
        tolerance = 1.0  # Allow 1% rounding error
        
        if abs(total_pct - 100) > tolerance:
            self.validation_checks.append({
                'check': 'allocation_sum_100',
                'status': 'FAIL',
                'message': (
                    f'Rebalanceable allocations sum to {total_pct:.1f}% '
                    f'instead of 100% (diff: {total_pct - 100:+.1f}%)'
                ),
                'severity': 'HIGH'
            })
        else:
            self.validation_checks.append({
                'check': 'allocation_sum_100',
                'status': 'PASS',
                'message': f'Allocations sum to {total_pct:.1f}% (within tolerance)',
                'severity': 'INFO'
            })
    
    def _check_non_rebalanceable_marking(self, rebalancing_data: Dict[str, Any]):
        """Verify non-rebalanceable assets are correctly marked."""
        top_level_table = rebalancing_data.get('top_level_table', [])
        
        # Expected non-rebalanceable classes (Chinese names)
        expected_non_rebalanceable = ['房地产', '保险']
        
        issues = []
        for item in top_level_table:
            asset_class = item.get('asset_class', '')
            is_rebalanceable = item.get('is_rebalanceable', True)
            
            # Check if expected non-rebalanceable classes are marked correctly
            if asset_class in expected_non_rebalanceable:
                if is_rebalanceable:
                    issues.append(
                        f"{asset_class} is marked as rebalanceable but should not be"
                    )
                # Check if target_pct is 0
                target_pct = item.get('target_pct', 0)
                if target_pct != 0:
                    issues.append(
                        f"{asset_class} has target_pct={target_pct} but should be 0"
                    )
        
        if issues:
            self.validation_checks.append({
                'check': 'non_rebalanceable_marking',
                'status': 'FAIL',
                'message': '; '.join(issues),
                'severity': 'HIGH'
            })
        else:
            self.validation_checks.append({
                'check': 'non_rebalanceable_marking',
                'status': 'PASS',
                'message': 'Non-rebalanceable assets correctly marked',
                'severity': 'INFO'
            })
    
    def _check_target_values(
        self,
        rebalancing_data: Dict[str, Any],
        portfolio_values: Dict[str, float]
    ):
        """Verify target values are calculated using rebalanceable_value."""
        top_level_table = rebalancing_data.get('top_level_table', [])
        rebalanceable_value = portfolio_values.get('rebalanceable_value', 0)
        
        if rebalanceable_value == 0:
            self.validation_checks.append({
                'check': 'target_value_calculation',
                'status': 'SKIP',
                'message': 'Rebalanceable value is zero',
                'severity': 'INFO'
            })
            return
        
        issues = []
        for item in top_level_table:
            if not item.get('is_rebalanceable', False):
                continue
            
            asset_class = item.get('asset_class', '')
            target_pct = item.get('target_pct', 0)
            target_value = item.get('target_value', 0)
            
            # Calculate expected target value
            expected_target = (target_pct / 100) * rebalanceable_value
            
            # Allow 1% tolerance for rounding
            tolerance = expected_target * 0.01 if expected_target > 0 else 1
            diff = abs(target_value - expected_target)
            
            if diff > tolerance:
                issues.append(
                    f"{asset_class}: target_value=¥{target_value:,.0f} "
                    f"but expected ¥{expected_target:,.0f} "
                    f"(target_pct={target_pct:.1f}%)"
                )
        
        if issues:
            self.validation_checks.append({
                'check': 'target_value_calculation',
                'status': 'FAIL',
                'message': '; '.join(issues),
                'severity': 'HIGH'
            })
        else:
            self.validation_checks.append({
                'check': 'target_value_calculation',
                'status': 'PASS',
                'message': 'Target values calculated correctly using rebalanceable_value',
                'severity': 'INFO'
            })
    
    def _generate_summary(self) -> Dict[str, int]:
        """Generate summary statistics of validation checks."""
        total = len(self.validation_checks)
        passed = sum(1 for c in self.validation_checks if c['status'] == 'PASS')
        warnings = sum(1 for c in self.validation_checks if c['status'] == 'WARN')
        failures = sum(1 for c in self.validation_checks if c['status'] == 'FAIL')
        skipped = sum(1 for c in self.validation_checks if c['status'] == 'SKIP')
        
        return {
            'total_checks': total,
            'passed': passed,
            'warnings': warnings,
            'failures': failures,
            'skipped': skipped
        }
    
    def _determine_overall_status(self, summary: Dict[str, int]) -> str:
        """Determine overall validation status."""
        if summary['failures'] > 0:
            return 'FAIL'
        elif summary['warnings'] > 0:
            return 'WARN'
        else:
            return 'PASS'
    
    def generate_checksums(
        self,
        holdings_df,
        portfolio_values: Dict[str, float],
        rebalancing_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate checksums for data integrity verification.
        
        Args:
            holdings_df: Holdings DataFrame
            portfolio_values: Portfolio value breakdown
            rebalancing_data: Rebalancing analysis data
            
        Returns:
            Dict with checksums and key metrics
        """
        checksums = {
            'total_portfolio_value': portfolio_values.get('total_portfolio_value', 0),
            'rebalanceable_value': portfolio_values.get('rebalanceable_value', 0),
            'non_rebalanceable_value': portfolio_values.get('non_rebalanceable_value', 0),
            'holdings_count': len(holdings_df) if holdings_df is not None else 0,
            'rebalanceable_holdings_count': self._count_rebalanceable_holdings(holdings_df),
            'generation_timestamp': datetime.now().isoformat()
        }
        
        # Generate data hash for change detection
        checksums['data_hash'] = self._generate_data_hash(checksums)
        
        return checksums
    
    def _count_rebalanceable_holdings(self, holdings_df) -> int:
        """Count holdings that are rebalanceable."""
        if holdings_df is None or holdings_df.empty:
            return 0
        
        # Assets are rebalanceable if their top-level class is not in non-rebalanceable list
        non_rebalanceable_classes = ['房地产', '保险', 'Real Estate', 'Insurance']
        
        rebalanceable_count = 0
        for _, row in holdings_df.iterrows():
            level_1 = row.get('Level_1', '')
            if level_1 not in non_rebalanceable_classes:
                rebalanceable_count += 1
        
        return rebalanceable_count
    
    def _generate_data_hash(self, checksums: Dict[str, Any]) -> str:
        """Generate hash for data change detection."""
        # Create stable JSON representation
        data_str = json.dumps({
            'total': checksums.get('total_portfolio_value', 0),
            'rebalanceable': checksums.get('rebalanceable_value', 0),
            'holdings': checksums.get('holdings_count', 0)
        }, sort_keys=True)
        
        # Generate SHA256 hash
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
