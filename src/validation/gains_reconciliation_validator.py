#!/usr/bin/env python3
"""
Gains Reconciliation Validator

This module validates that realized + unrealized gains from the gains analysis
match the total profit/loss from lifetime asset performance across all calculation paths.

Key Validation:
    Realized Gains + Unrealized Gains (from cost_basis.get_gains_analysis)
    = 
    Sum of Total_Profit_Loss (from cost_basis.get_lifetime_asset_performance)

This ensures consistency across different calculation paths and identifies
potential issues with currency conversion, transaction inclusion, or cost basis methods.
"""

import logging
from typing import Dict, List, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class GainsReconciliationResult:
    """Results from gains reconciliation validation."""
    
    def __init__(self,
                 lifetime_total: float,
                 analysis_total: float,
                 discrepancy: float,
                 discrepancy_pct: float,
                 status: str,
                 asset_breakdown: Optional[List[Dict]] = None):
        self.lifetime_total = lifetime_total
        self.analysis_total = analysis_total
        self.discrepancy = discrepancy
        self.discrepancy_pct = discrepancy_pct
        self.status = status
        self.asset_breakdown = asset_breakdown or []
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'lifetime_total': self.lifetime_total,
            'analysis_total': self.analysis_total,
            'discrepancy': self.discrepancy,
            'discrepancy_pct': self.discrepancy_pct,
            'status': self.status,
            'asset_breakdown': self.asset_breakdown
        }


class GainsReconciliationValidator:
    """
    Validator for reconciling realized/unrealized gains across calculation paths.
    
    This ensures data consistency and identifies potential calculation discrepancies.
    """
    
    def __init__(self, tolerance_cny: float = 100.0, tolerance_pct: float = 0.1):
        """
        Initialize the validator.
        
        Args:
            tolerance_cny: Absolute tolerance in CNY (default: ¥100)
            tolerance_pct: Percentage tolerance (default: 0.1%)
        """
        self.tolerance_cny = tolerance_cny
        self.tolerance_pct = tolerance_pct
        self.logger = logging.getLogger(__name__)
        
    def validate_gains_consistency(self,
                                   gains_analysis: Dict[str, float],
                                   lifetime_performance: List[Dict[str, Any]]) -> GainsReconciliationResult:
        """
        Validate that gains analysis totals match lifetime performance totals.
        
        Args:
            gains_analysis: Dictionary from get_realized_unrealized_gains()
                Contains: realized_gains, unrealized_gains, total_gains
            lifetime_performance: List from get_lifetime_asset_performance()
                Each item contains: Asset_ID, Total_Profit_Loss, etc.
                
        Returns:
            GainsReconciliationResult with validation details
        """
        self.logger.info("=" * 70)
        self.logger.info("GAINS RECONCILIATION VALIDATION")
        self.logger.info("=" * 70)
        
        # Extract totals from gains analysis
        realized_gains = gains_analysis.get('realized_gains', 0.0)
        unrealized_gains = gains_analysis.get('unrealized_gains', 0.0)
        analysis_total = gains_analysis.get('total_gains', realized_gains + unrealized_gains)
        
        self.logger.info("\n📊 Gains Analysis Breakdown:")
        self.logger.info(f"   Realized Gains:   ¥{realized_gains:>15,.2f}")
        self.logger.info(f"   Unrealized Gains: ¥{unrealized_gains:>15,.2f}")
        self.logger.info(f"   Total (Analysis): ¥{analysis_total:>15,.2f}")
        
        # Sum Total_Profit_Loss from lifetime performance
        # Note: The field is 'total_pnl' in cost_basis module output
        lifetime_total = sum(
            asset.get('total_pnl', asset.get('Total_Profit_Loss', 0.0))
            for asset in lifetime_performance
            if asset.get('total_pnl', asset.get('Total_Profit_Loss')) is not None
        )
        
        self.logger.info(f"\n📈 Lifetime Performance Total:")
        self.logger.info(f"   Total Profit/Loss: ¥{lifetime_total:>14,.2f}")
        
        # Calculate discrepancy
        discrepancy = lifetime_total - analysis_total
        discrepancy_pct = (discrepancy / analysis_total * 100) if analysis_total != 0 else 0.0
        
        self.logger.info(f"\n🔍 Reconciliation Results:")
        self.logger.info(f"   Discrepancy:      ¥{discrepancy:>15,.2f}")
        self.logger.info(f"   Discrepancy %:    {discrepancy_pct:>16.4f}%")
        self.logger.info(f"   Tolerance (CNY):  ¥{self.tolerance_cny:>15,.2f}")
        self.logger.info(f"   Tolerance (%):    {self.tolerance_pct:>16.2f}%")
        
        # Determine status
        status = self._determine_status(discrepancy, discrepancy_pct)
        
        # Get asset-level breakdown if there's a significant discrepancy
        asset_breakdown = []
        if status != 'PASS':
            asset_breakdown = self._analyze_asset_level_discrepancies(
                lifetime_performance,
                gains_analysis
            )
        
        # Log final status
        self.logger.info(f"\n{'✅' if status == 'PASS' else '❌' if status == 'FAIL' else '⚠️'} Status: {status}")
        self.logger.info("=" * 70)
        
        return GainsReconciliationResult(
            lifetime_total=lifetime_total,
            analysis_total=analysis_total,
            discrepancy=discrepancy,
            discrepancy_pct=discrepancy_pct,
            status=status,
            asset_breakdown=asset_breakdown
        )
    
    def _determine_status(self, discrepancy: float, discrepancy_pct: float) -> str:
        """
        Determine validation status based on discrepancy.
        
        Args:
            discrepancy: Absolute discrepancy in CNY
            discrepancy_pct: Percentage discrepancy
            
        Returns:
            Status string: 'PASS', 'WARNING', or 'FAIL'
        """
        abs_discrepancy = abs(discrepancy)
        abs_discrepancy_pct = abs(discrepancy_pct)
        
        if abs_discrepancy <= self.tolerance_cny and abs_discrepancy_pct <= self.tolerance_pct:
            return 'PASS'
        elif abs_discrepancy <= self.tolerance_cny * 2 and abs_discrepancy_pct <= self.tolerance_pct * 2:
            return 'WARNING'
        else:
            return 'FAIL'
    
    def _analyze_asset_level_discrepancies(self,
                                          lifetime_performance: List[Dict[str, Any]],
                                          gains_analysis: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Analyze asset-level discrepancies to identify problematic assets.
        
        Args:
            lifetime_performance: Lifetime asset performance data
            gains_analysis: Gains analysis data
            
        Returns:
            List of assets with potential issues
        """
        self.logger.info("\n🔬 Asset-Level Analysis:")
        self.logger.info("-" * 70)
        
        problematic_assets = []
        
        # Get subclass breakdown if available
        subclass_breakdown = gains_analysis.get('subclass_breakdown', {})
        
        # Analyze each asset
        for asset in lifetime_performance:
            asset_id = asset.get('Asset_ID', 'Unknown')
            total_pl = asset.get('Total_Profit_Loss', 0.0)
            currency = asset.get('Currency', 'CNY')
            
            # Flag assets with extreme values or potential currency issues
            if total_pl is None:
                problematic_assets.append({
                    'asset_id': asset_id,
                    'issue': 'NULL_PROFIT_LOSS',
                    'description': 'Total_Profit_Loss is None'
                })
                self.logger.warning(f"   ⚠️  {asset_id}: Total_Profit_Loss is None")
                
            elif abs(total_pl) > 1_000_000:  # Very large profit/loss
                problematic_assets.append({
                    'asset_id': asset_id,
                    'issue': 'EXTREME_VALUE',
                    'total_pl': total_pl,
                    'description': f'Unusually large profit/loss: ¥{total_pl:,.2f}'
                })
                self.logger.warning(f"   ⚠️  {asset_id}: Extreme value ¥{total_pl:,.2f}")
                
            elif currency == 'USD' and abs(total_pl) > 100_000:  # USD asset with high CNY value
                problematic_assets.append({
                    'asset_id': asset_id,
                    'issue': 'POTENTIAL_CURRENCY_ISSUE',
                    'total_pl': total_pl,
                    'currency': currency,
                    'description': f'USD asset with high CNY value: ¥{total_pl:,.2f}'
                })
                self.logger.warning(f"   ⚠️  {asset_id}: Potential currency conversion issue")
        
        if not problematic_assets:
            self.logger.info("   ✅ No significant asset-level issues detected")
        else:
            self.logger.info(f"   Found {len(problematic_assets)} assets with potential issues")
        
        return problematic_assets
    
    def generate_detailed_report(self, result: GainsReconciliationResult) -> str:
        """
        Generate a detailed human-readable report.
        
        Args:
            result: GainsReconciliationResult from validation
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 80)
        report.append("GAINS RECONCILIATION VALIDATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Status summary
        status_emoji = {
            'PASS': '✅',
            'WARNING': '⚠️',
            'FAIL': '❌'
        }
        report.append(f"{status_emoji.get(result.status, '❓')} Overall Status: {result.status}")
        report.append("")
        
        # Financial totals
        report.append("Financial Totals:")
        report.append(f"  Lifetime Performance Total: ¥{result.lifetime_total:>18,.2f}")
        report.append(f"  Gains Analysis Total:       ¥{result.analysis_total:>18,.2f}")
        report.append(f"  Discrepancy:                ¥{result.discrepancy:>18,.2f}")
        report.append(f"  Discrepancy %:              {result.discrepancy_pct:>19.4f}%")
        report.append("")
        
        # Tolerance thresholds
        report.append("Tolerance Thresholds:")
        report.append(f"  Absolute: ±¥{self.tolerance_cny:,.2f}")
        report.append(f"  Percentage: ±{self.tolerance_pct:.2f}%")
        report.append("")
        
        # Asset-level issues
        if result.asset_breakdown:
            report.append("Asset-Level Issues Detected:")
            for i, issue in enumerate(result.asset_breakdown, 1):
                report.append(f"  {i}. {issue['asset_id']}")
                report.append(f"     Issue: {issue['issue']}")
                report.append(f"     Description: {issue['description']}")
                report.append("")
        else:
            report.append("No asset-level issues detected")
            report.append("")
        
        # Recommendations
        report.append("Recommendations:")
        if result.status == 'PASS':
            report.append("  ✅ Gains reconciliation passed - no action needed")
        elif result.status == 'WARNING':
            report.append("  ⚠️  Minor discrepancy detected:")
            report.append("     1. Review asset-level breakdown above")
            report.append("     2. Check for currency conversion timing differences")
            report.append("     3. Verify transaction completeness")
        else:  # FAIL
            report.append("  ❌ Significant discrepancy detected - investigation required:")
            report.append("     1. Review problematic assets listed above")
            report.append("     2. Validate currency conversion consistency")
            report.append("     3. Check for missing transactions")
            report.append("     4. Verify cost basis calculation methods")
            report.append("     5. Compare transaction inclusion logic between paths")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


def validate_gains_from_analyzer(analyzer) -> GainsReconciliationResult:
    """
    Convenience function to validate gains using FinancialAnalyzer instance.
    
    Args:
        analyzer: FinancialAnalyzer instance
        
    Returns:
        GainsReconciliationResult
    """
    validator = GainsReconciliationValidator()
    
    gains_analysis = analyzer.get_realized_unrealized_gains()
    lifetime_performance = analyzer.get_lifetime_asset_performance()
    
    return validator.validate_gains_consistency(gains_analysis, lifetime_performance)


if __name__ == '__main__':
    # Test the validator with real data
    import sys
    import os
    
    # Add project root to path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)
    
    from src.data_manager.manager import DataManager
    from src.financial_analysis.analyzer import FinancialAnalyzer
    
    print("\n" + "=" * 80)
    print("GAINS RECONCILIATION VALIDATOR - TEST RUN")
    print("=" * 80 + "\n")
    
    # Initialize system
    print("Initializing DataManager and FinancialAnalyzer...")
    analyzer = FinancialAnalyzer(config_dir='config')
    
    # Run validation
    print("\nRunning gains reconciliation validation...\n")
    result = validate_gains_from_analyzer(analyzer)
    
    # Generate detailed report
    validator = GainsReconciliationValidator()
    report = validator.generate_detailed_report(result)
    print("\n" + report)
    
    # Exit with appropriate code
    sys.exit(0 if result.status == 'PASS' else 1)
