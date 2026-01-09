"""
Unified Data Preparer for HTML Reports

This module centralizes all data preparation for HTML reports, ensuring
consistency across Portfolio, Action Compass, and Market Thermometer tabs.

Author: Personal Investment System
Date: October 20, 2025
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
import pandas as pd

from src.report_builders.validation_service import ValidationService

logger = logging.getLogger(__name__)


class UnifiedDataPreparer:
    """
    Central data preparation for HTML reports with cross-validation.
    
    This class ensures Portfolio tab and Action Compass use identical data,
    preventing inconsistencies and calculation errors across report sections.
    
    Key Principles:
    1. Single source of truth for all calculations
    2. Consistent asset filtering throughout
    3. Clear denominator usage (total vs rebalanceable)
    4. Cross-module validation with detailed reporting
    """
    
    def __init__(self, data_manager, portfolio_manager, taxonomy_manager, financial_analyzer):
        """
        Initialize unified data preparer.
        
        Args:
            data_manager: DataManager instance for raw data
            portfolio_manager: PortfolioAnalysisManager for classifications
            taxonomy_manager: TaxonomyManager for asset taxonomy
            financial_analyzer: FinancialAnalyzer for performance metrics
        """
        self.data_manager = data_manager
        self.portfolio_manager = portfolio_manager
        self.taxonomy_manager = taxonomy_manager
        self.financial_analyzer = financial_analyzer
        self.validation_service = ValidationService()
        self.logger = logging.getLogger(__name__)
    
    def prepare_all_report_data(self) -> Dict[str, Any]:
        """
        Prepare all data for HTML reports in one unified pass with validation.
        
        This is the SINGLE ENTRY POINT for report data preparation.
        All report builders should use data from this function.
        
        Returns:
            {
                'portfolio_values': {...},      # Total, rebalanceable, breakdown
                'performance_data': {...},      # XIRR, returns, performance metrics
                'rebalancing_data': {...},      # Rebalancing analysis with correct denominators
                'recommendations': [...],       # Recommendations using rebalanceable_value
                'validation_report': {...},     # Cross-module validation results
                'checksums': {...},             # Data integrity checksums
                'generation_timestamp': str     # ISO timestamp
            }
        """
        self.logger.info("=" * 80)
        self.logger.info("Starting Unified Data Preparation for HTML Reports")
        self.logger.info("=" * 80)
        
        try:
            # Step 1: Get validated holdings with consistent filtering
            self.logger.info("Step 1/8: Getting validated holdings...")
            holdings_df = self._get_validated_holdings()
            
            # Step 2: Calculate portfolio values with CLEAR denominators
            self.logger.info("Step 2/8: Calculating portfolio values...")
            portfolio_values = self._calculate_portfolio_values(holdings_df)
            self._log_portfolio_values(portfolio_values)
            
            # Step 3: Calculate performance metrics (placeholder for now)
            self.logger.info("Step 3/8: Calculating performance metrics...")
            performance_data = self._calculate_performance_metrics(holdings_df)
            holdings_df = self._merge_performance_into_holdings(holdings_df, performance_data)
            
            # Step 4: Build rebalancing analysis using rebalanceable_value
            self.logger.info("Step 4/8: Building rebalancing analysis...")
            rebalancing_data = self._build_rebalancing_analysis(
                holdings_df,
                rebalanceable_value=portfolio_values['rebalanceable_value']
            )
            
            # Step 5: Build tier-level allocation analysis
            self.logger.info("Step 5/8: Building tier allocation analysis...")
            tier_analysis = self._build_tier_analysis(
                holdings_df, 
                rebalanceable_value=portfolio_values['rebalanceable_value']
            )
            
            # Step 6: Generate recommendations using SAME rebalancing_data
            self.logger.info("Step 6/8: Generating recommendations...")
            recommendations = self._generate_recommendations(
                holdings_df,
                rebalancing_data,
                performance_data,
                rebalanceable_value=portfolio_values['rebalanceable_value']
            )
            
            # Step 7: VALIDATE cross-module consistency
            self.logger.info("Step 7/8: Validating cross-module consistency...")
            validation_report = self.validation_service.validate_consistency(
                portfolio_values,
                rebalancing_data,
                recommendations
            )
            self._log_validation_results(validation_report)
            
            # Step 8: Generate checksums for debugging
            self.logger.info("Step 8/8: Generating checksums...")
            checksums = self.validation_service.generate_checksums(
                holdings_df,
                portfolio_values,
                rebalancing_data
            )
            
            self.logger.info("=" * 80)
            self.logger.info("✅ Unified Data Preparation Complete")
            self.logger.info(f"   Validation Status: {validation_report['overall_status']}")
            self.logger.info(f"   Total Portfolio: ¥{portfolio_values['total_portfolio_value']:,.0f}")
            self.logger.info(f"   Rebalanceable: ¥{portfolio_values['rebalanceable_value']:,.0f}")
            self.logger.info(f"   Holdings: {checksums['holdings_count']}")
            self.logger.info("=" * 80)
            
            return {
                'portfolio_values': portfolio_values,
                'performance_data': performance_data,
                'rebalancing_data': rebalancing_data,
                'tier_analysis': tier_analysis,
                'recommendations': recommendations,
                'validation_report': validation_report,
                'checksums': checksums,
                'generation_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in unified data preparation: {e}", exc_info=True)
            raise
    
    def _get_validated_holdings(self) -> pd.DataFrame:
        """
        Get holdings with consistent taxonomy classification applied.
        
        This ensures all downstream calculations use classified holdings
        with Level_1, Level_2, Level_3 columns available.
        
        Returns:
            Classified holdings DataFrame with taxonomy columns
        """
        # Get holdings from DataManager first
        holdings_df = self.data_manager.get_holdings()
        
        if holdings_df is None or holdings_df.empty:
            self.logger.warning("No holdings data available")
            return pd.DataFrame()
        
        self.logger.info(f"Loaded {len(holdings_df)} raw holdings from DataManager")

        # Step 1.1: Enrich with Lifetime Performance Data (Realized/Unrealized P&L) from CostBasis
        # This is critical for Tier Analysis to show profit splits.
        try:
            self.logger.info("   Enriching holdings with lifetime performance data...")
            from src.financial_analysis.cost_basis import get_lifetime_asset_performance
            
            # We need transactions for lifetime performance
            transactions_df = self.data_manager.get_transactions()
            
            # Calculate lifetime performance
            lifetime_perf = get_lifetime_asset_performance(transactions_df, holdings_df)
            with open("debug_log.txt", "a") as f:
                f.write(f"\n[DEBUG] Lifetime Perf generated {len(lifetime_perf)} records\n")
            
            # Create lookup dictionary
            perf_lookup = {str(item['asset_id']): item for item in lifetime_perf}
            with open("debug_log.txt", "a") as f:
                if len(perf_lookup) > 0:
                    f.write(f"[DEBUG] Sample Perf Keys: {list(perf_lookup.keys())[:5]}\n")
            
            # Merge into holdings_df
            enriched_holdings = holdings_df.copy()
            # Ensure Asset_ID is string for matching
            enriched_holdings['Asset_ID'] = enriched_holdings['Asset_ID'].astype(str)
            
            # Initialize columns
            for col in ['Realized_PnL', 'Unrealized_PnL', 'Total_PnL', 'Lifetime_XIRR']:
                enriched_holdings[col] = 0.0
            
            match_count = 0
            # Map metrics
            for idx, row in enriched_holdings.iterrows():
                asset_id = str(row.get('Asset_ID'))
                if asset_id in perf_lookup:
                    match_count += 1
                    perf = perf_lookup[asset_id]
                    enriched_holdings.at[idx, 'Realized_PnL'] = perf.get('realized_pnl', 0.0)
                    enriched_holdings.at[idx, 'Unrealized_PnL'] = perf.get('unrealized_pnl', 0.0)
                    enriched_holdings.at[idx, 'Total_PnL'] = perf.get('total_pnl', 0.0)
                    enriched_holdings.at[idx, 'Lifetime_XIRR'] = perf.get('xirr_pct') if perf.get('xirr_pct') is not None else 0.0
            
            with open("debug_log.txt", "a") as f:
                f.write(f"[DEBUG] Matched {match_count} assets with performance data out of {len(enriched_holdings)}\n")
            
            holdings_df = enriched_holdings
            with open("debug_log.txt", "a") as f:
                f.write(f"[DEBUG] Successfully enriched {len(holdings_df)} holdings with P&L data\n")
            
        except Exception as e:
            self.logger.warning(f"   Could not enrich holdings with lifetime performance: {e}")
        
        # ✅ CRITICAL FIX: Apply taxonomy classification BEFORE any calculations
        self.logger.info("   Applying taxonomy classification to holdings...")
        try:
            # Import the classification function from real_report
            from src.report_generators.real_report import classify_asset_using_taxonomy
            
            # Apply classification row by row
            classifications = []
            for _, row in holdings_df.iterrows():
                asset_name = row.get('Asset_Name', '')
                asset_type = row.get('Asset_Type_Raw', row.get('Asset_Type', ''))
                
                # Get taxonomy classification
                top_level, sub_class = classify_asset_using_taxonomy(
                    asset_name, 
                    asset_type, 
                    self.taxonomy_manager
                )
                
                classifications.append({
                    'Level_1': top_level,
                    'Level_2': sub_class,
                    'Level_3': asset_type  # Use raw asset type as Level_3
                })
            
            # Convert to DataFrame and merge with holdings
            classification_df = pd.DataFrame(classifications)
            classified_holdings = pd.concat([holdings_df.reset_index(drop=True), classification_df], axis=1)
            
            # Verify Level_1 column exists
            if 'Level_1' not in classified_holdings.columns:
                self.logger.error("   Level_1 column missing after classification!")
                self.logger.warning("   Falling back to unclassified holdings")
                return holdings_df
            
            self.logger.info(f"   ✅ Successfully classified {len(classified_holdings)} holdings with taxonomy")
            self.logger.info(f"   Level_1 classes found: {sorted(classified_holdings['Level_1'].unique().tolist())}")
            
            return classified_holdings
            
        except Exception as e:
            self.logger.error(f"   Error during taxonomy classification: {e}", exc_info=True)
            self.logger.warning("   Falling back to unclassified holdings")
            return holdings_df
    
    def _calculate_portfolio_values(self, holdings_df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate portfolio values with CLEAR denominators.
        
        This function establishes the THREE key values used throughout reporting:
        1. total_portfolio_value - ALL assets
        2. rebalanceable_value - Excludes Real Estate, Insurance
        3. non_rebalanceable_value - Real Estate + Insurance
        
        Args:
            holdings_df: Holdings DataFrame
            
        Returns:
            {
                'total_portfolio_value': float,
                'rebalanceable_value': float,
                'non_rebalanceable_value': float,
                'breakdown': {
                    'rebalanceable': {...},
                    'non_rebalanceable': {...}
                }
            }
        """
        if holdings_df is None or holdings_df.empty:
            self.logger.warning("   No holdings data for portfolio value calculation")
            return {
                'total_portfolio_value': 0,
                'rebalanceable_value': 0,
                'non_rebalanceable_value': 0,
                'breakdown': {'rebalanceable': {}, 'non_rebalanceable': {}}
            }
        
        # Calculate total portfolio value
        total_value = holdings_df['Market_Value_CNY'].sum()
        self.logger.debug(f"   DEBUG: Total portfolio value from {len(holdings_df)} holdings: ¥{total_value:,.0f}")
        
        # ✅ CRITICAL CHECK: Verify Level_1 column exists
        if 'Level_1' not in holdings_df.columns:
            self.logger.error("   ❌ ERROR: Level_1 column missing! Cannot classify rebalanceable assets.")
            self.logger.error("   All assets will be treated as rebalanceable (INCORRECT!).")
            self.logger.error("   This will cause validation failures.")
            # Fallback: treat everything as rebalanceable
            return {
                'total_portfolio_value': total_value,
                'rebalanceable_value': total_value,
                'non_rebalanceable_value': 0,
                'breakdown': {'rebalanceable': {'Unknown': total_value}, 'non_rebalanceable': {}}
            }
        
        # Identify non-rebalanceable assets (use ENGLISH names matching classify_asset_using_taxonomy output)
        non_rebalanceable_classes = ['Real Estate', 'Insurance']  # English names from taxonomy
        
        rebalanceable_value = 0
        non_rebalanceable_value = 0
        breakdown = {'rebalanceable': {}, 'non_rebalanceable': {}}
        
        for _, row in holdings_df.iterrows():
            market_value = row.get('Market_Value_CNY', 0) or 0
            level_1 = row.get('Level_1', 'Unknown')
            asset_name = row.get('Asset_Name', 'Unknown')
            
            if level_1 in non_rebalanceable_classes:
                non_rebalanceable_value += market_value
                if level_1 not in breakdown['non_rebalanceable']:
                    breakdown['non_rebalanceable'][level_1] = 0
                breakdown['non_rebalanceable'][level_1] += market_value
                self.logger.debug(f"   DEBUG: Non-rebalanceable: {asset_name} ({level_1}) = ¥{market_value:,.0f}")
            else:
                rebalanceable_value += market_value
                if level_1 not in breakdown['rebalanceable']:
                    breakdown['rebalanceable'][level_1] = 0
                breakdown['rebalanceable'][level_1] += market_value
        
        self.logger.debug(f"   DEBUG: Rebalanceable value: ¥{rebalanceable_value:,.0f}")
        self.logger.debug(f"   DEBUG: Non-rebalanceable value: ¥{non_rebalanceable_value:,.0f}")
        self.logger.debug(f"   DEBUG: Verification: {rebalanceable_value + non_rebalanceable_value:,.0f} == {total_value:,.0f}? {abs((rebalanceable_value + non_rebalanceable_value) - total_value) < 1}")
        
        # ✅ ADD: Comprehensive validation logging
        self.logger.info("=" * 60)
        self.logger.info("PORTFOLIO VALUE CALCULATION SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Total Portfolio Value:       ¥{total_value:>12,.0f}")
        self.logger.info(f"Rebalanceable Value:         ¥{rebalanceable_value:>12,.0f} ({rebalanceable_value/total_value*100 if total_value > 0 else 0:.1f}%)")
        self.logger.info(f"Non-Rebalanceable Value:     ¥{non_rebalanceable_value:>12,.0f} ({non_rebalanceable_value/total_value*100 if total_value > 0 else 0:.1f}%)")
        self.logger.info("-" * 60)
        if breakdown['non_rebalanceable']:
            self.logger.info("Non-Rebalanceable Breakdown:")
            for asset_class, value in breakdown['non_rebalanceable'].items():
                self.logger.info(f"  {asset_class:20s}: ¥{value:>12,.0f}")
        else:
            self.logger.info("Non-Rebalanceable Breakdown: (none)")
        self.logger.info("=" * 60)
        
        # Verification check
        sum_check = rebalanceable_value + non_rebalanceable_value
        if abs(sum_check - total_value) > 1:
            self.logger.error(f"❌ CALCULATION ERROR: Sum mismatch! {sum_check:,.0f} != {total_value:,.0f}")
        else:
            self.logger.info("✅ Verification passed: Rebalanceable + Non-rebalanceable = Total")
        
        return {
            'total_portfolio_value': total_value,
            'rebalanceable_value': rebalanceable_value,
            'non_rebalanceable_value': non_rebalanceable_value,
            'breakdown': breakdown
        }
    
    def _calculate_performance_metrics(self, holdings_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate performance metrics with consistent XIRR.
        
        Uses financial_analyzer to calculate real performance metrics.
        
        Args:
            holdings_df: Holdings DataFrame
            
        Returns:
            Performance metrics dictionary
        """
        asset_xirr_by_name: Dict[str, float] = {}
        asset_unrealized_by_name: Dict[str, float] = {}
        asset_performance_details: Dict[str, Any] = {}
        try:
            self.logger.info("   Calculating real XIRR and performance metrics...")
            investment_results = self.financial_analyzer.analyze_investments('config')
            
            # Extract portfolio XIRR
            portfolio_xirr = investment_results.get('asset_performance', {}).get('portfolio_xirr')
            portfolio_xirr_metadata = investment_results.get('asset_performance', {}).get('portfolio_xirr_metadata', {})

            # Build asset-level lookup tables for downstream modules
            asset_performance_details = investment_results.get('asset_performance', {}).get('asset_performances', {}) or {}
            for perf in asset_performance_details.values():
                asset_name = perf.get('Asset_Name')
                if not asset_name:
                    continue
                xirr_value = perf.get('XIRR')
                if xirr_value is not None:
                    asset_xirr_by_name[asset_name] = xirr_value
                unrealized_value = perf.get('Unrealized_Gain')
                if unrealized_value is not None:
                    asset_unrealized_by_name[asset_name] = unrealized_value
            
            if portfolio_xirr is not None and pd.notna(portfolio_xirr):
                overall_xirr_str = f"{portfolio_xirr:.2f}"
                self.logger.info(f"   ✅ Portfolio XIRR: {overall_xirr_str}%")
            else:
                overall_xirr_str = "N/A"
                self.logger.warning("   ⚠️  Portfolio XIRR calculation returned None")
            
            return {
                'portfolio_xirr': portfolio_xirr,
                'overall_xirr_str': overall_xirr_str,
                'portfolio_xirr_metadata': portfolio_xirr_metadata,
                'sharpe_ratio': None,  # TODO: Calculate in future
                'asset_xirr_by_name': asset_xirr_by_name,
                'asset_unrealized_by_name': asset_unrealized_by_name,
                'asset_performance_details': asset_performance_details
            }
        except Exception as e:
            self.logger.warning(f"   Could not calculate performance metrics: {e}")
            return {
                'portfolio_xirr': None,
                'overall_xirr_str': 'N/A',
                'sharpe_ratio': None,
                'asset_xirr_by_name': asset_xirr_by_name,
                'asset_unrealized_by_name': asset_unrealized_by_name,
                'asset_performance_details': asset_performance_details
            }
    
    def _build_rebalancing_analysis(
        self,
        holdings_df: pd.DataFrame,
        rebalanceable_value: float
    ) -> Dict[str, Any]:
        """
        Build rebalancing analysis using rebalanceable_value.
        
        Calls build_rebalancing_analysis from rebalancing_builder.py.
        
        Args:
            holdings_df: Holdings DataFrame
            rebalanceable_value: Value of rebalanceable assets only
            
        Returns:
            Rebalancing data dictionary with rebalanceable_value embedded
        """
        try:
            from src.report_builders.rebalancing_builder import build_rebalancing_analysis
            
            # Call existing rebalancing builder
            rebalancing_data = build_rebalancing_analysis(holdings_df, market_regime=None)
            
            # Verify rebalanceable_value matches
            if abs(rebalancing_data.get('rebalanceable_value', 0) - rebalanceable_value) > 1:
                self.logger.warning(
                    f"   ⚠️  Rebalanceable value mismatch: "
                    f"calculated=¥{rebalanceable_value:,.0f} vs "
                    f"from rebalancing=¥{rebalancing_data.get('rebalanceable_value', 0):,.0f}"
                )
            
            return rebalancing_data
            
        except Exception as e:
            self.logger.error(f"   Error building rebalancing analysis: {e}")
            return {
                'rebalanceable_value': rebalanceable_value,
                'top_level_table': [],
                'sub_category_table': []
            }
    
    def _generate_recommendations(
        self,
        holdings_df: pd.DataFrame,
        rebalancing_data: Dict[str, Any],
        performance_data: Dict[str, Any],
        rebalanceable_value: float
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations using SAME rebalancing_data.
        
        Calls RecommendationEngine with correct rebalanceable_value.
        
        Args:
            holdings_df: Holdings DataFrame
            rebalancing_data: From _build_rebalancing_analysis
            performance_data: Performance metrics
            rebalanceable_value: Value of rebalanceable assets
            
        Returns:
            List of recommendation dictionaries
        """
        try:
            from src.recommendation_engine.recommendation_engine import RecommendationEngine
            
            rec_engine = RecommendationEngine()
            
            # Generate recommendations (passing total portfolio value for reference)
            # Note: RecommendationEngine should use rebalanceable_value from rebalancing_data
            total_portfolio_value = rebalancing_data.get('total_portfolio_value', 0)
            
            # ACTION COMPASS V2.0 PHASE 1: Handle new dict return format
            result = rec_engine.generate_all_recommendations(
                rebalancing_data=rebalancing_data,
                holdings_df=holdings_df,
                performance_data=performance_data,
                portfolio_value=total_portfolio_value,
                market_regime=None  # Can be added later
            )
            
            # Extract recommendations list (maintain backward compatibility)
            recommendations = result.get('recommendations', []) if isinstance(result, dict) else result
            
            self.logger.info(f"   Generated {len(recommendations)} recommendations")
            return recommendations
            
        except Exception as e:
            self.logger.warning(f"   Could not generate recommendations: {e}")
            return []
    
    def _build_tier_analysis(self, holdings_df: pd.DataFrame, rebalanceable_value: float = None) -> Dict[str, Any]:
        """
        Build tier-level allocation analysis.
        
        Calls build_tier_analysis from tier_analysis_builder.py.
        
        Args:
            holdings_df: Holdings DataFrame
            rebalanceable_value: Denominator for percentage calculations (Rebalanceable Assets)
            
        Returns:
            Tier analysis data dictionary
        """
        try:
            from src.report_builders.tier_analysis_builder import build_tier_analysis
            
            # Pass rebalanceable_value as Total Denominator
            tier_data = build_tier_analysis(
                holdings_df, 
                self.taxonomy_manager,
                total_portfolio_value=rebalanceable_value
            )
            
            # Log summary
            tier_table = tier_data.get('tier_table', [])

            unclassified_count = tier_data.get('unclassified_count', 0)
            
            self.logger.info(f"   ✅ Tier analysis complete: {len(tier_table)} tiers, {unclassified_count} unclassified")
            
            for tier in tier_table:
                if tier['tier_key'] != 'unclassified':
                    self.logger.info(
                        f"      {tier['tier_name']}: "
                        f"¥{tier['current_value']:,.0f} ({tier['current_pct']:.1f}%) | "
                        f"Target: {tier['target_pct']:.1f}% | Drift: {tier['drift']:+.1f}%"
                    )
            
            return tier_data
            
        except Exception as e:
            self.logger.warning(f"   Could not build tier analysis: {e}")
            return {
                'total_value': 0,
                'tier_table': [],
                'tier_details': {},
                'unclassified_count': 0
            }

    
    def _log_portfolio_values(self, portfolio_values: Dict[str, float]):
        """Log portfolio value breakdown."""
        total = portfolio_values['total_portfolio_value']
        rebalanceable = portfolio_values['rebalanceable_value']
        non_rebalanceable = portfolio_values['non_rebalanceable_value']
        
        self.logger.info(f"   Total Portfolio: ¥{total:,.0f}")
        self.logger.info(f"   Rebalanceable: ¥{rebalanceable:,.0f} ({rebalanceable/total*100:.1f}%)")
        self.logger.info(f"   Non-Rebalanceable: ¥{non_rebalanceable:,.0f} ({non_rebalanceable/total*100:.1f}%)")
        
        # Log breakdown
        breakdown = portfolio_values['breakdown']
        if breakdown['non_rebalanceable']:
            self.logger.info("   Non-Rebalanceable Breakdown:")
            for asset_class, value in breakdown['non_rebalanceable'].items():
                self.logger.info(f"     - {asset_class}: ¥{value:,.0f}")
    
    def _log_validation_results(self, validation_report: Dict[str, Any]):
        """Log validation results."""
        summary = validation_report['summary']
        status = validation_report['overall_status']
        
        if status == 'PASS':
            self.logger.info(f"   ✅ All {summary['total_checks']} validation checks passed")
        elif status == 'WARN':
            self.logger.warning(
                f"   ⚠️  Validation completed with {summary['warnings']} warning(s), "
                f"{summary['passed']} passed"
            )
        else:
            self.logger.error(
                f"   ❌ Validation FAILED: {summary['failures']} failure(s), "
                f"{summary['warnings']} warning(s), {summary['passed']} passed"
            )
        
        # Log failures and warnings
        for check in validation_report['checks']:
            if check['status'] in ['FAIL', 'WARN']:
                self.logger.warning(f"   [{check['status']}] {check['check']}: {check['message']}")

    def _merge_performance_into_holdings(self, holdings_df: pd.DataFrame, performance_data: Dict[str, Any]) -> pd.DataFrame:
        """Attach asset-level performance metrics (XIRR, gains) to holdings DataFrame."""
        if holdings_df is None or holdings_df.empty:
            return holdings_df

        xirr_map = performance_data.get('asset_xirr_by_name') or {}
        gains_map = performance_data.get('asset_unrealized_by_name') or {}

        if not xirr_map and not gains_map:
            return holdings_df

        if 'Asset_Name' not in holdings_df.columns:
            self.logger.warning("   Asset_Name column missing, cannot merge performance metrics into holdings")
            return holdings_df

        enriched_df = holdings_df.copy()
        if xirr_map:
            enriched_df['XIRR'] = enriched_df['Asset_Name'].map(xirr_map)
            self.logger.info(f"   Added XIRR data to {enriched_df['XIRR'].notna().sum()} holdings")
        if gains_map:
            enriched_df['Unrealized_Gains'] = enriched_df['Asset_Name'].map(gains_map)
        return enriched_df
