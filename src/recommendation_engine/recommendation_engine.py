"""
Recommendation Engine - Central orchestrator for generating actionable investment recommendations.

This module provides the core RecommendationEngine class that coordinates multiple recommendation
generators to produce prioritized, actionable advice for portfolio management.

Author: Personal Investment System
Date: October 14, 2025
Updated: October 30, 2025 - Action Compass V2.0 Phase 1 Integration
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
from .product_recommender import ProductRecommender
from .strategic_directive_builder import StrategicDirectiveBuilder

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Central engine for generating multiple types of actionable recommendations.
    
    This orchestrator coordinates various recommendation generators to produce
    5-7 prioritized recommendations spanning multiple categories:
    - Capital Allocation
    - Profit Rebalancing
    - Risk Concentration
    - Market Timing
    - Tax Optimization
    
    Each recommendation includes:
    - Priority score (0-100)
    - Specific action items
    - Financial impact metrics
    - Execution guidance
    """
    
    def __init__(self):
        """Initialize the recommendation engine."""
        self.logger = logging.getLogger(__name__)
        self.recommendations = []
        self._recommendation_counter = 0
        self.product_recommender = ProductRecommender()
        
        # ACTION COMPASS V2.0 PHASE 1: Initialize Strategic Directive Builder
        self.strategic_directive_builder = StrategicDirectiveBuilder()
        
        # PHASE 6.1.3: Load asset taxonomy configuration
        self.asset_taxonomy = self._load_asset_taxonomy()
        self.non_rebalanceable_classes = self.asset_taxonomy.get('non_rebalanceable_classes', [])
        self.logger.info(f"Loaded non-rebalanceable classes: {self.non_rebalanceable_classes}")
    
    def _load_asset_taxonomy(self) -> Dict:
        """
        Load asset taxonomy configuration from YAML.
        
        Returns:
            Dictionary with asset taxonomy config or empty dict if error
        """
        try:
            import yaml
            with open('config/asset_taxonomy.yaml', 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Error loading asset_taxonomy.yaml: {e}")
            return {}
    
    def _build_class_allocation_from_table(
        self,
        top_level_table: List[Dict],
        portfolio_value: float
    ) -> Dict:
        """
        Build class_allocation dictionary from top_level_table.
        
        Args:
            top_level_table: List of top-level asset class allocation dicts
            portfolio_value: Total portfolio value
        
        Returns:
            Dict with structure: {
                'Equity': {'value': float, 'current_pct': float, 'target_pct': float, 'is_rebalanceable': bool},
                ...
            }
        """
        class_allocation = {}
        for item in top_level_table:
            asset_class = item.get('asset_class', '')
            if not asset_class:
                continue

            raw_current_pct = item.get('current_pct', item.get('current', 0)) or 0
            raw_target_pct = item.get('target_pct', item.get('target', 0)) or 0
            current_pct = raw_current_pct / 100.0 if not isinstance(raw_current_pct, str) else 0.0
            target_pct = raw_target_pct / 100.0 if not isinstance(raw_target_pct, str) else 0.0

            class_allocation[asset_class] = {
                'value': item.get('current_value', item.get('value', 0)) or 0,
                'current_pct': current_pct,
                'target_pct': target_pct,
                'is_rebalanceable': item.get('is_rebalanceable', True)
            }
        return class_allocation
    
    def _identify_asset_class_from_strategy(self, action_cn: str) -> Optional[str]:
        """
        Identify which asset class a strategy is targeting based on keywords.
        
        Args:
            action_cn: Action text from strategic recommendation
        
        Returns:
            Asset class name (English) or None if not identified
        """
        if 'Real Estate' in action_cn or 'Real Estate' in action_cn:
            return 'Real Estate'
        elif 'Insurance' in action_cn:
            return 'Insurance'
        elif 'Equity' in action_cn or 'Equity' in action_cn:
            return 'Equity'
        elif 'Fixed Income' in action_cn or 'Bond' in action_cn or 'Bond' in action_cn:
            return 'Fixed Income'
        elif 'Cash' in action_cn:
            return 'Cash'
        elif 'Gold' in action_cn or 'Commodity' in action_cn:
            return 'Commodities'
        elif 'Alternative' in action_cn or 'Crypto' in action_cn:
            return 'Alternative'
        return None
    
    def generate_all_recommendations(
        self,
        rebalancing_data: Dict,
        holdings_df: pd.DataFrame,
        performance_data: Dict,
        portfolio_value: float,
        market_regime: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Generate comprehensive list of actionable recommendations.
        
        Args:
            rebalancing_data: Dictionary from RebalancingBuilder.build_rebalancing_analysis()
            holdings_df: Current portfolio holdings with Asset_ID, Asset_Name, Market_Value_CNY, XIRR
            performance_data: Performance metrics from FinancialAnalyzer
            portfolio_value: Total portfolio value in CNY
            market_regime: Optional market regime dict from IndicatorRegimeDetector with keys:
                - regime_name: str (e.g., 'Maximum Defense')
                - regime_name_cn: str (e.g., 'Maximum Defense')
                - priority: int
                - dynamic_targets: Optional[Dict] with top_level and sub_category allocations
                - strategic_recommendations: List[Dict] with priority recommendations
                - matched_conditions: List of condition details
        
        Returns:
            Dict with keys:
                - recommendations: List of recommendation dictionaries sorted by priority (descending)
                - strategic_directive: Dict with strategic directive data (ACTION COMPASS V2.0 PHASE 1)
        """
        self.logger.info("=" * 80)
        self.logger.info("Generating comprehensive recommendations...")
        if market_regime:
            self.logger.info(f"Market Regime: {market_regime.get('regime_name_cn', 'N/A')} ({market_regime.get('regime_name', 'N/A')})")
        self.logger.info("=" * 80)
        
        self.recommendations = []
        self._recommendation_counter = 0
        
        # ACTION COMPASS V2.0 PHASE 1B: Build Portfolio-Aware Strategic Directive
        strategic_directive = None
        if market_regime:
            # Extract portfolio state for phase 1B
            portfolio_state = self._extract_portfolio_state(rebalancing_data, portfolio_value)
            
            # Build portfolio-aware directive
            directive_obj = self.strategic_directive_builder.build_directive(
                market_regime,
                portfolio_state
            )
            if directive_obj:
                strategic_directive = self.strategic_directive_builder.to_dict(directive_obj)
                self.logger.info(f"✅ Built Strategic Directive: {directive_obj.core_objective_cn}")
            else:
                self.logger.warning("⚠️ Failed to build strategic directive from market regime")
        
        # PHASE 2: Apply dynamic targets if market regime provides them
        if market_regime and market_regime.get('dynamic_targets'):
            rebalancing_data = self._apply_dynamic_targets(rebalancing_data, market_regime, portfolio_value)
        
        # PHASE 2: Inject strategic recommendations from regime first
        if market_regime and market_regime.get('strategic_recommendations'):
            self._inject_strategic_recommendations(market_regime, rebalancing_data, portfolio_value, holdings_df, strategic_directive)
        
        # Generate recommendations from each category
        self._generate_capital_allocation_recommendation(rebalancing_data, portfolio_value, holdings_df)
        self._generate_profit_rebalancing_recommendation(rebalancing_data, holdings_df, portfolio_value)
        self._generate_risk_concentration_recommendation(rebalancing_data, holdings_df, portfolio_value)
        self._generate_market_timing_recommendation(market_regime, rebalancing_data)  # Pass full regime dict
        self._generate_tax_loss_harvesting_recommendation(holdings_df, portfolio_value)
        self._generate_diversification_recommendation(rebalancing_data, holdings_df, portfolio_value)
        self._generate_correlation_risk_recommendation(rebalancing_data)
        self._generate_liquidity_stress_recommendation(rebalancing_data)
        
        # Calculate priority scores (skip if already set, like for strategic recommendations)
        for rec in self.recommendations:
            if 'priority' not in rec or rec['priority'] == 0:
                rec['priority'] = self._calculate_priority_score(rec)
        
        # Sort by priority (descending)
        self.recommendations.sort(key=lambda x: x['priority'], reverse=True)
        
        self.logger.info(f"Generated {len(self.recommendations)} recommendations")
        for i, rec in enumerate(self.recommendations[:5], 1):
            self.logger.info(f"  {i}. [{rec['priority']}] {rec['title_cn']} ({rec['type']})")
        
        # ACTION COMPASS V2.0 PHASE 1: Return both recommendations and strategic directive
        return {
            'recommendations': self.recommendations,
            'strategic_directive': strategic_directive
        }
    
    def _generate_capital_allocation_recommendation(
        self,
        rebalancing_data: Dict,
        portfolio_value: float,
        holdings_df: Optional[pd.DataFrame] = None
    ):
        """
        Generate capital allocation recommendation using Phase 1 proportional allocation.
        
        Args:
            rebalancing_data: Rebalancing analysis data
            portfolio_value: Total portfolio value
            holdings_df: Current holdings DataFrame (for product recommendations)
        """
        try:
            # Check if there are under-allocated asset classes
            top_level_table = rebalancing_data.get('top_level_table', [])
            under_allocated = [
                item for item in top_level_table
                if item.get('is_rebalanceable', False) and item.get('drift', 0) < -1.0
            ]
            
            if not under_allocated:
                self.logger.info("No significant under-allocation found (drift < -1%), skipping capital allocation recommendation")
                return
            
            # Calculate total drift and reference capital
            total_drift = sum(abs(item['drift']) for item in under_allocated)
            reference_capital = 100000  # Default reference amount
            
            # Get proportional allocation from rebalancing data
            proportional_allocation = rebalancing_data.get('proportional_allocation', [])
            
            if not proportional_allocation:
                self.logger.warning("No proportional allocation data available")
                return
            
            # Build description
            num_classes = len(proportional_allocation)
            drift_reduction = rebalancing_data.get('total_drift_reduction', 0)
            
            description = (
                f"Your portfolio has {num_classes} under-allocated asset classes with "
                f"total drift of {total_drift:.1f}%. Deploying new capital using a proportional "
                f"allocation strategy can reduce portfolio imbalance efficiently across multiple gaps."
            )
            
            # Build action items from proportional allocation
            action_items = []
            product_recommendations = []  # Store product recommendations
            current_holdings = holdings_df['Asset_Name'].tolist() if holdings_df is not None and not holdings_df.empty else []
            
            for alloc in proportional_allocation:
                action_text = f"Allocate to {alloc['asset_class']} ({alloc['asset_class_en']})"
                rationale = (
                    f"Current drift: {alloc['current_drift']:.1f}% | "
                    f"New drift after allocation: {alloc['new_drift']:.1f}% | "
                    f"Gap closed: {alloc.get('gap_closed', 0):.1f}%"
                )
                action_items.append({
                    'action': action_text,
                    'amount': alloc['amount'],
                    'percentage': alloc['percentage'],
                    'rationale': rationale
                })
                
                # Get product recommendations for this allocation
                product_rec = self.product_recommender.recommend_products(
                    asset_class=alloc['asset_class_en'],
                    allocation_amount=alloc['amount'],
                    sub_class=alloc.get('sub_class'),
                    current_holdings=current_holdings
                )
                
                if product_rec and product_rec.get('total_products', 0) > 0:
                    product_recommendations.append({
                        'asset_class': alloc['asset_class'],
                        'asset_class_en': alloc['asset_class_en'],
                        'amount': alloc['amount'],
                        'products': product_rec.get('products', []),
                        'strategy': product_rec.get('allocation_strategy', ''),
                        'sub_class_breakdown': alloc.get('sub_class_breakdown', [])
                    })
            
            # Calculate dollar impact
            total_allocation = sum(alloc['amount'] for alloc in proportional_allocation)
            
            rec = {
                'id': self._generate_recommendation_id(),
                'type': 'CAPITAL_ALLOCATION',
                'title': 'Smart Asset Allocation Strategy',
                'title_cn': 'Smart Asset Allocation Strategy',
                'description': description,
                'impact': {
                    'dollar_value': total_allocation,
                    'drift_reduction': drift_reduction,
                    'risk_reduction': 'MEDIUM'
                },
                'action_items': action_items,
                'urgency': 'MEDIUM',
                'category': 'Capital Allocation',
                'estimated_effort': 'LOW',
                'tax_implications': None,
                'product_recommendations': product_recommendations,  # Phase 3: Product recommendations
                'metadata': {
                    'reference_capital': reference_capital,
                    'num_asset_classes': num_classes,
                    'proportional_allocation': proportional_allocation
                }
            }
            
            self.recommendations.append(rec)
            self.logger.info(f"✓ Generated capital allocation recommendation (drift reduction: {drift_reduction:.1f}%)")
            
        except Exception as e:
            self.logger.error(f"Error generating capital allocation recommendation: {e}", exc_info=True)
    
    def _generate_profit_rebalancing_recommendation(
        self,
        rebalancing_data: Dict,
        holdings_df: pd.DataFrame,
        portfolio_value: float
    ):
        """
        Generate profit rebalancing recommendation for over-allocated high-gain positions.
        
        Args:
            rebalancing_data: Rebalancing analysis data
            holdings_df: Holdings with XIRR performance
            portfolio_value: Total portfolio value
        """
        try:
            # Check for over-allocated asset classes
            top_level_table = rebalancing_data.get('top_level_table', [])
            over_allocated = [
                item for item in top_level_table
                if item.get('is_rebalanceable', False) and item.get('drift', 0) > 5.0
            ]
            
            if not over_allocated:
                self.logger.info("No significant over-allocation found (drift > 5%), skipping profit rebalancing")
                return
            
            # Find high-performing assets in over-allocated classes
            if 'XIRR' not in holdings_df.columns:
                self.logger.warning("XIRR column not found in holdings_df, skipping profit rebalancing recommendation")
                return

            high_performers = holdings_df[
                (holdings_df['XIRR'].notna()) & 
                (holdings_df['XIRR'] > 10.0) &
                (holdings_df['Market_Value_CNY'] > 5000)
            ].copy()
            
            if high_performers.empty:
                self.logger.info("No high-performing positions found for rebalancing")
                return
            
            # Sort by combination of XIRR and market value (prioritize high gains + high value)
            high_performers['rebalance_score'] = (
                high_performers['XIRR'] * 0.6 + 
                (high_performers['Market_Value_CNY'] / portfolio_value * 100) * 0.4
            )
            high_performers = high_performers.sort_values('rebalance_score', ascending=False)
            
            # Take top 2-3 candidates
            top_candidates = high_performers.head(3)
            
            # Calculate total over-allocation value
            total_over_allocated_value = sum(
                item.get('rebalanceable_value', 0) * item['drift'] / 100
                for item in over_allocated
            )
            
            # Build action items
            action_items = []
            total_sell_value = 0
            
            for _, asset in top_candidates.iterrows():
                asset_name = asset.get('Asset_Name', 'Unknown')
                market_value = asset['Market_Value_CNY']
                xirr = asset['XIRR']
                
                # Get actual unrealized gain from holdings data (mapped from asset_gains_data)
                # CRITICAL FIX: Use actual unrealized gains instead of incorrect approximation formula
                unrealized_gain = asset.get('Unrealized_Gains', 0.0)
                
                # Suggest selling 30-50% of position
                sell_percentage = 40 if market_value > 50000 else 30
                sell_amount = market_value * sell_percentage / 100
                
                action_text = f"Sell {sell_percentage}% of {asset_name}"
                rationale = (
                    f"Current XIRR: {xirr:.1f}% | Market Value: ¥{market_value:,.0f} | "
                    f"Unrealized Gain: ¥{unrealized_gain:,.0f} | "
                    f"Reduces concentration and locks in profits"
                )
                
                action_items.append({
                    'action': action_text,
                    'amount': sell_amount,
                    'percentage': sell_percentage,
                    'rationale': rationale
                })
                
                total_sell_value += sell_amount
                
                if len(action_items) >= 2:  # Limit to top 2 for clarity
                    break
            
            if not action_items:
                return
            
            # Build description
            over_allocated_class = over_allocated[0]['asset_class']
            max_drift = over_allocated[0]['drift']
            
            description = (
                f"Your {over_allocated_class} allocation is {max_drift:.1f}% above target with strong "
                f"unrealized gains. Selling high-performing positions can reduce risk, lock in profits, "
                f"and free capital for under-allocated asset classes."
            )
            
            rec = {
                'id': self._generate_recommendation_id(),
                'type': 'PROFIT_REBALANCING',
                'title': 'Profit Rebalancing Opportunity',
                'title_cn': 'Profit-Taking Rebalance Opportunity',
                'description': description,
                'impact': {
                    'dollar_value': total_sell_value,
                    'drift_reduction': max_drift,
                    'risk_reduction': 'HIGH'
                },
                'action_items': action_items,
                'urgency': 'HIGH',
                'category': 'Rebalancing',
                'estimated_effort': 'LOW',
                'tax_implications': 'Capital gains tax will apply (estimate 15-25% depending on jurisdiction)',
                'metadata': {
                    'over_allocated_classes': len(over_allocated),
                    'total_over_allocation': total_over_allocated_value
                }
            }
            
            self.recommendations.append(rec)
            self.logger.info(f"✓ Generated profit rebalancing recommendation (sell value: ¥{total_sell_value:,.0f})")
            
        except Exception as e:
            self.logger.error(f"Error generating profit rebalancing recommendation: {e}", exc_info=True)
    
    def _generate_risk_concentration_recommendation(
        self,
        rebalancing_data: Dict,
        holdings_df: pd.DataFrame,
        portfolio_value: float
    ):
        """
        Generate risk concentration alert for positions exceeding threshold.
        Only analyzes rebalanceable assets (excludes Real Estate, Insurance, etc.).
        
        Args:
            rebalancing_data: Rebalancing analysis data with is_rebalanceable flags
            holdings_df: Holdings with market values
            portfolio_value: Total portfolio value
        """
        try:
            # Get rebalanceable portfolio value for accurate percentage calculation
            rebalanceable_value = rebalancing_data.get('rebalanceable_value', portfolio_value)
            
            # Better approach: Filter holdings by matching against sub-level table
            sub_level_table = rebalancing_data.get('sub_level_table', [])
            rebalanceable_subclasses = set()
            for sub_class in sub_level_table:
                if sub_class.get('is_rebalanceable', False):
                    # Use 'sub_category' field (English name) from sub_level_table
                    rebalanceable_subclasses.add(sub_class.get('sub_category', ''))
            
            # Filter holdings to only rebalanceable assets
            # Use Asset_Sub_Class or taxonomy mapping to match holdings
            holdings_df = holdings_df.copy()
            
            # Add asset class info if not present
            if 'Asset_Sub_Class' not in holdings_df.columns:
                self.logger.warning("Asset_Sub_Class column not found in holdings, cannot filter by rebalanceability")
                # Fallback: Exclude known non-rebalanceable assets by name patterns
                non_rebalanceable_patterns = ['Property_', 'Ins_', 'Insurance', 'Real Estate', 'Real Estate']
                mask = ~holdings_df['Asset_Name'].apply(
                    lambda x: any(pattern in str(x) for pattern in non_rebalanceable_patterns)
                )
                rebalanceable_holdings = holdings_df[mask].copy()
            else:
                # Filter by asset sub-class matching rebalanceable sub-classes
                rebalanceable_holdings = holdings_df[
                    holdings_df['Asset_Sub_Class'].isin(rebalanceable_subclasses)
                ].copy()
            
            if rebalanceable_holdings.empty:
                self.logger.info("No rebalanceable holdings found for concentration analysis")
                return
            
            # Calculate percentage of REBALANCEABLE portfolio for each holding
            rebalanceable_holdings['portfolio_pct'] = (
                rebalanceable_holdings['Market_Value_CNY'] / rebalanceable_value * 100
            )
            
            # Find concentrated positions (> 8% of portfolio)
            CONCENTRATION_THRESHOLD = 8.0
            concentrated = rebalanceable_holdings[rebalanceable_holdings['portfolio_pct'] > CONCENTRATION_THRESHOLD].copy()
            
            if concentrated.empty:
                self.logger.info(f"No concentration risk found (all rebalanceable positions < {CONCENTRATION_THRESHOLD}%)")
                return
            
            concentrated = concentrated.sort_values('portfolio_pct', ascending=False)
            
            # Build description
            top_asset = concentrated.iloc[0]
            top_asset_name = top_asset.get('Asset_Name', 'Unknown')
            top_asset_pct = top_asset['portfolio_pct']
            num_concentrated = len(concentrated)
            
            description = (
                f"You have {num_concentrated} rebalanceable position(s) exceeding {CONCENTRATION_THRESHOLD}% of your rebalanceable portfolio. "
                f"{top_asset_name} represents {top_asset_pct:.1f}% of rebalanceable assets (¥{rebalanceable_value:,.0f}). "
                f"High concentration increases portfolio volatility and single-asset risk. "
                f"Gradual reduction is recommended for better diversification."
            )
            
            # Build action items
            action_items = []
            
            # Load target allocations from taxonomy to use actual config targets
            from src.portfolio_lib.taxonomy_manager import TaxonomyManager
            from src.report_generators.real_report import classify_asset_using_taxonomy
            
            taxonomy_manager = TaxonomyManager()
            target_allocations = taxonomy_manager.config.get('risk_profiles', {}).get('Growth', {})
            sub_category_weights = taxonomy_manager.config.get('sub_category_weights', {})
            
            for _, asset in concentrated.head(2).iterrows():
                asset_name = asset.get('Asset_Name', 'Unknown')
                asset_type = asset.get('Asset_Type_Raw', 'Unknown')
                asset_pct = asset['portfolio_pct']
                market_value = asset['Market_Value_CNY']
                
                # Classify asset to get its target allocation from config
                top_level, sub_class = classify_asset_using_taxonomy(asset_name, asset_type, taxonomy_manager)
                
                # Map English to Chinese for lookup
                english_to_chinese = {
                    'Equity': 'Equity',
                    'Fixed Income': 'Fixed Income', 
                    'Cash': 'Cash',
                    'Commodities': 'Commodities',
                    'Alternative': 'Alternative',
                    'Real Estate': 'Real Estate',
                    'Insurance': 'Insurance'
                }
                chinese_top_level = english_to_chinese.get(top_level, top_level)
                
                # Map English sub-category to localized version (here just same English as we are moving to English-first)
                english_to_chinese_subcategory = {
                    'Domestic Equity ETF': 'Domestic Equity ETF',
                    'US Equity ETF': 'US Equity ETF', 
                    'US Stock RSU': 'US Stock RSU',
                    'Hong Kong Equity ETF': 'HK Equity ETF',
                    'Emerging Market Equity': 'Emerging Market Equity',
                    'Domestic Government Bonds': 'CN Govt Bonds',
                    'US Government Bonds': 'US Govt Bonds',
                    'Corporate Bonds': 'Corporate Bonds',
                    'Money Market': 'Money Market',
                    'Bank Wealth Management': 'Bank Products',
                    'Gold': 'Gold',
                    'Cash': 'Cash',
                    'Cryptocurrency': 'Crypto',
                    'Venture Capital': 'Venture Capital'
                }
                chinese_sub_category = english_to_chinese_subcategory.get(sub_class, sub_class)
                
                # Get target from config: sub_weight * top_category_target * 100
                top_category_target = target_allocations.get(chinese_top_level, 0.0)
                category_weights = sub_category_weights.get(chinese_top_level, {})
                sub_weight = category_weights.get(chinese_sub_category, 0.0)
                target_pct = sub_weight * top_category_target * 100
                
                # If no specific target found, use 5% as fallback
                if target_pct == 0:
                    target_pct = 5.0
                    self.logger.warning(f"No target found for {asset_name} ({chinese_sub_category}), using 5% fallback")
                
                # Only recommend reduction if OVER-ALLOCATED (current > target)
                if asset_pct <= target_pct:
                    self.logger.debug(f"Skipping {asset_name}: current {asset_pct:.1f}% <= target {target_pct:.1f}%")
                    continue
                
                reduction_needed = asset_pct - target_pct
                reduction_value = market_value * (reduction_needed / asset_pct)
                
                action_text = f"Reduce {asset_name} position"
                rationale = (
                    f"Current: {asset_pct:.1f}% of portfolio (¥{market_value:,.0f}) | "
                    f"Target: {target_pct:.1f}% | "
                    f"Suggest gradual reduction of ¥{reduction_value:,.0f} over 2-3 months"
                )
                
                action_items.append({
                    'action': action_text,
                    'amount': reduction_value,
                    'rationale': rationale
                })
            
            # If no action items (all concentrated positions are under-allocated), skip recommendation
            if not action_items:
                self.logger.info("All concentrated positions are under-allocated (below target), no reduction recommended")
                return
            
            # Calculate total concentration value (sum of reduction amounts for over-allocated assets)
            total_concentrated_value = sum(item['amount'] for item in action_items)
            
            rec = {
                'id': self._generate_recommendation_id(),
                'type': 'RISK_CONCENTRATION',
                'title': 'Concentration Risk Alert',
                'title_cn': 'Concentration Risk Alert',
                'description': description,
                'impact': {
                    'dollar_value': total_concentrated_value,
                    'drift_reduction': 0,
                    'risk_reduction': 'HIGH'
                },
                'action_items': action_items,
                'urgency': 'HIGH' if top_asset_pct > 15 else 'MEDIUM',
                'category': 'Risk Management',
                'estimated_effort': 'MEDIUM',
                'tax_implications': 'Consider tax-loss harvesting opportunities when reducing positions',
                'metadata': {
                    'num_concentrated_positions': num_concentrated,
                    'concentration_threshold': CONCENTRATION_THRESHOLD,
                    'top_concentration_pct': top_asset_pct
                }
            }
            
            self.recommendations.append(rec)
            self.logger.info(f"✓ Generated concentration risk recommendation ({num_concentrated} positions)")
            
        except Exception as e:
            self.logger.error(f"Error generating risk concentration recommendation: {e}", exc_info=True)
    
    def _generate_market_timing_recommendation(
        self,
        market_regime: Optional[Dict],
        rebalancing_data: Dict
    ):
        """
        Generate market timing insight based on current regime.
        
        Args:
            market_regime: Market regime dict from IndicatorRegimeDetector or None
            rebalancing_data: Rebalancing analysis data
        """
        try:
            # Get current equity allocation
            top_level_table = rebalancing_data.get('top_level_table', [])
            equity_data = next(
                (item for item in top_level_table if 'equity' in item.get('asset_class_en', '').lower()),
                None
            )
            
            if not equity_data:
                self.logger.warning("No equity data found for market timing recommendation")
                return
            
            current_equity_pct = equity_data.get('current_pct', 0)
            target_equity_pct = equity_data.get('target_pct', 0)
            equity_drift = equity_data.get('drift', 0)
            
            # Check if market_regime is dict (new format) or string (legacy format)
            regime_name = None
            if market_regime:
                if isinstance(market_regime, dict):
                    regime_name = market_regime.get('regime_name', '').upper()
                elif isinstance(market_regime, str):
                    regime_name = market_regime.upper()
            
            # Generate regime-specific advice or generic advice if regime unknown
            if regime_name and 'BULL' in regime_name:
                title = 'Bull Market Positioning Review'
                title_cn = 'Bull Market Allocation Review'
                description = (
                    f"Current market regime: BULL MARKET. Your equity allocation is {current_equity_pct:.1f}% "
                    f"(target: {target_equity_pct:.1f}%). In bull markets, it's wise to periodically take profits "
                    f"from high-flying positions and build defensive positions for eventual corrections."
                )
                action_items = [
                    {
                        'action': 'Review profit-taking opportunities in high-gain equity positions',
                        'rationale': 'Bull markets eventually correct; lock in gains while market is strong'
                    },
                    {
                        'action': 'Gradually increase Fixed Income allocation',
                        'rationale': 'Build defensive positions for portfolio protection during corrections'
                    }
                ]
                urgency = 'MEDIUM'
                
            elif regime_name and 'BEAR' in regime_name:
                title = 'Bear Market Positioning Review'
                title_cn = 'Bear Market Allocation Review'
                description = (
                    f"Current market regime: BEAR MARKET. Your equity allocation is {current_equity_pct:.1f}%. "
                    f"Bear markets present buying opportunities but require patience. Focus on quality assets "
                    f"and maintain adequate cash/fixed income reserves."
                )
                action_items = [
                    {
                        'action': 'Maintain or increase Fixed Income allocation for stability',
                        'rationale': 'Preserve capital during market downturns'
                    },
                    {
                        'action': 'Identify quality equity positions at discounted valuations',
                        'rationale': 'Bear markets create long-term buying opportunities'
                    }
                ]
                urgency = 'LOW'
                
            else:  # SIDEWAYS, None, or other
                title = 'Strategic Rebalancing Opportunity'
                title_cn = 'Strategic Rebalancing Opportunity'
                description = (
                    f"Your equity allocation is {current_equity_pct:.1f}% (target: {target_equity_pct:.1f}%, "
                    f"drift: {equity_drift:+.1f}%). Regular rebalancing helps maintain your risk profile and "
                    f"captures mean reversion. Consider reviewing your allocation quarterly to stay aligned with targets."
                )
                action_items = [
                    {
                        'action': 'Review and rebalance to target allocations',
                        'rationale': 'Maintain strategic risk profile through disciplined rebalancing'
                    },
                    {
                        'action': 'Assess quality of individual holdings within each asset class',
                        'rationale': 'Rebalancing is a good time to upgrade to higher quality positions'
                    }
                ]
                urgency = 'LOW' if abs(equity_drift) < 5 else 'MEDIUM'
            
            rec = {
                'id': self._generate_recommendation_id(),
                'type': 'MARKET_TIMING',
                'title': title,
                'title_cn': title_cn,
                'description': description,
                'impact': {
                    'dollar_value': 0,  # Informational
                    'drift_reduction': 0,
                    'risk_reduction': 'MEDIUM'
                },
                'action_items': action_items,
                'urgency': urgency,
                'category': 'Market Context',
                'estimated_effort': 'LOW',
                'tax_implications': None,
                'metadata': {
                    'market_regime': market_regime or 'UNKNOWN',
                    'equity_allocation': current_equity_pct,
                    'equity_drift': equity_drift
                }
            }
            
            self.recommendations.append(rec)
            regime_display = market_regime or 'generic rebalancing'
            self.logger.info(f"✓ Generated market timing recommendation (regime: {regime_display})")
            
        except Exception as e:
            self.logger.error(f"Error generating market timing recommendation: {e}", exc_info=True)
    
    def _calculate_priority_score(self, recommendation: Dict) -> int:
        """
        Calculate 0-100 priority score based on multiple factors.
        
        Scoring Factors:
        - Dollar Impact (40%): Larger $ impact = higher priority
        - Drift Magnitude (30%): Larger drift = higher priority
        - Risk Level (20%): Higher risk = higher priority
        - Urgency (10%): Time-sensitive actions = higher priority
        
        Args:
            recommendation: Recommendation dictionary
        
        Returns:
            Priority score (0-100)
        """
        score = 0
        impact = recommendation.get('impact', {})
        
        # Dollar Impact (0-40 points)
        dollar_impact = impact.get('dollar_value', 0)
        if dollar_impact > 200000:
            score += 40
        elif dollar_impact > 100000:
            score += 30
        elif dollar_impact > 50000:
            score += 20
        elif dollar_impact > 10000:
            score += 10
        else:
            score += 5
        
        # Drift Magnitude (0-30 points)
        drift = abs(impact.get('drift_reduction', 0))
        if drift > 10:
            score += 30
        elif drift > 5:
            score += 20
        elif drift > 2:
            score += 10
        else:
            score += 5
        
        # Risk Level (0-20 points)
        risk = impact.get('risk_reduction', 'LOW')
        risk_scores = {'HIGH': 20, 'MEDIUM': 12, 'LOW': 5}
        score += risk_scores.get(risk, 0)
        
        # Urgency (0-10 points)
        urgency = recommendation.get('urgency', 'LOW')
        urgency_scores = {'HIGH': 10, 'MEDIUM': 6, 'LOW': 2}
        score += urgency_scores.get(urgency, 0)
        
        return min(score, 100)  # Cap at 100
    
    def _generate_tax_loss_harvesting_recommendation(
        self,
        holdings_df: pd.DataFrame,
        portfolio_value: float
    ):
        """
        Generate tax loss harvesting recommendations for loss positions.
        
        Args:
            holdings_df: Current holdings with XIRR and unrealized gains
            portfolio_value: Total portfolio value
        """
        try:
            if holdings_df is None or holdings_df.empty:
                return
            
            # Find positions with losses (negative XIRR or negative unrealized gains)
            loss_positions = []
            
            for _, asset in holdings_df.iterrows():
                xirr = asset.get('XIRR', 0)
                unrealized_gain = asset.get('Unrealized_Gains', 0)
                market_value = asset.get('Market_Value_CNY', 0)
                asset_name = asset.get('Asset_Name', 'Unknown')
                
                # Identify loss positions
                if (xirr < -5 or unrealized_gain < -1000) and market_value > 1000:
                    loss_positions.append({
                        'asset_name': asset_name,
                        'xirr': xirr,
                        'unrealized_loss': abs(unrealized_gain) if unrealized_gain < 0 else 0,
                        'market_value': market_value
                    })
            
            if not loss_positions:
                return  # No tax harvesting opportunities
            
            # Sort by loss amount
            loss_positions.sort(key=lambda x: x['unrealized_loss'], reverse=True)
            top_losses = loss_positions[:3]  # Top 3 loss positions
            
            total_loss = sum(pos['unrealized_loss'] for pos in top_losses)
            
            if total_loss < 1000:
                return  # Too small to be worthwhile
            
            # Generate recommendation
            rec_id = self._generate_recommendation_id()
            
            action_items = []
            for i, pos in enumerate(top_losses, 1):
                action_items.append({
                    'action': f"Sell {pos['asset_name']} to harvest loss",
                    'amount': pos['market_value'],
                    'rationale': f"Unrealized loss: ¥{pos['unrealized_loss']:,.0f} | XIRR: {pos['xirr']:.1f}%"
                })
            
            self.recommendations.append({
                'id': rec_id,
                'type': 'TAX_OPTIMIZATION',
                'title': 'Tax Loss Harvesting Opportunity',
                'title_cn': 'Tax-Loss Harvesting Opportunity',
                'description': f'You have {len(top_losses)} positions with unrealized losses totaling ¥{total_loss:,.0f}. Consider harvesting these losses to offset capital gains.',
                'impact': {
                    'dollar_value': total_loss,
                    'drift_reduction': 0,
                    'risk_reduction': 'LOW'
                },
                'action_items': action_items,
                'urgency': 'MEDIUM',
                'category': 'Tax Optimization',
                'estimated_effort': 'LOW',
                'tax_implications': f'Tax benefit: Offset ¥{total_loss:,.0f} in capital gains (estimated savings ¥{total_loss * 0.2:,.0f})',
                'priority': 0  # Will be calculated later
            })
            
            self.logger.info(f"  Generated tax loss harvesting recommendation (${total_loss:,.0f} losses)")
            
        except Exception as e:
            self.logger.error(f"Error generating tax loss harvesting recommendation: {e}")
    
    def _generate_diversification_recommendation(
        self,
        rebalancing_data: Dict,
        holdings_df: pd.DataFrame,
        portfolio_value: float
    ):
        """
        Generate diversification recommendations for under-diversified portfolio segments.
        
        Args:
            rebalancing_data: Rebalancing analysis data
            holdings_df: Current holdings
            portfolio_value: Total portfolio value
        """
        try:
            # Check for US-heavy portfolio
            if holdings_df is None or holdings_df.empty:
                return
            
            # Count assets by sub-class
            us_assets_value = 0
            cn_assets_value = 0
            total_equity_value = 0
            
            for _, asset in holdings_df.iterrows():
                asset_name = asset.get('Asset_Name', '')
                market_value = asset.get('Market_Value_CNY', 0)
                
                # Simplified classification
                if any(ticker in str(asset_name) for ticker in ['Employer_Stock_A', 'QQQ', 'VOO', 'SPY']):
                    us_assets_value += market_value
                    total_equity_value += market_value
                elif 'Fund' in str(asset_name) or 'Stock' in str(asset_name) or 'Equity' in str(asset_name):
                    cn_assets_value += market_value
                    total_equity_value += market_value
            
            if total_equity_value == 0:
                return
            
            us_pct = (us_assets_value / total_equity_value) * 100
            cn_pct = (cn_assets_value / total_equity_value) * 100
            
            # If > 70% in one region, suggest diversification
            if us_pct > 70 or cn_pct > 70:
                rec_id = self._generate_recommendation_id()
                
                if us_pct > 70:
                    primary_region = 'US'
                    primary_pct = us_pct
                    suggest_region = 'China/Emerging Markets'
                else:
                    primary_region = 'China'
                    primary_pct = cn_pct
                    suggest_region = 'US/Developed Markets'
                
                action_items = [
                    {
                        'action': f"Reduce {primary_region} equity exposure",
                        'amount': total_equity_value * 0.2,  # Suggest moving 20%
                        'rationale': f"Current {primary_region} allocation: {primary_pct:.1f}% of equity portfolio"
                    },
                    {
                        'action': f"Increase {suggest_region} exposure",
                        'amount': total_equity_value * 0.2,
                        'rationale': "Target: More balanced regional allocation (50-60% max in one region)"
                    }
                ]
                
                self.recommendations.append({
                    'id': rec_id,
                    'type': 'DIVERSIFICATION',
                    'title': 'Geographic Diversification Opportunity',
                    'title_cn': 'Geographic Diversification Opportunity',
                    'description': f'Your equity portfolio is heavily concentrated in {primary_region} ({primary_pct:.1f}%). Consider diversifying across regions to reduce country-specific risk.',
                    'impact': {
                        'dollar_value': total_equity_value * 0.2,
                        'drift_reduction': 0,
                        'risk_reduction': 'MEDIUM'
                    },
                    'action_items': action_items,
                    'urgency': 'MEDIUM',
                    'category': 'Diversification',
                    'estimated_effort': 'MEDIUM',
                    'tax_implications': 'May trigger capital gains tax if selling US positions',
                    'priority': 0  # Will be calculated later
                })
                
                self.logger.info(f"  Generated geographic diversification recommendation ({primary_region} {primary_pct:.1f}%)")
                
        except Exception as e:
            self.logger.error(f"Error generating diversification recommendation: {e}")

    def _generate_correlation_risk_recommendation(self, rebalancing_data: Dict):
        """
        Generate recommendations based on asset correlation analysis.
        
        Args:
            rebalancing_data: Dictionary containing correlation_analysis
        """
        try:
            correlation_analysis = rebalancing_data.get('correlation_analysis', {})
            if not correlation_analysis:
                return

            high_corr_pairs = correlation_analysis.get('high_corr_pairs', [])
            alerts = correlation_analysis.get('alerts', [])
            
            if not high_corr_pairs and not alerts:
                return

            # Filter pairs with correlation > 0.8
            critical_pairs = [p for p in high_corr_pairs if p.get('correlation', 0) > 0.8]
            
            if critical_pairs:
                action_items = []
                for p in critical_pairs:
                    pair = p.get('pair', [])
                    corr = p.get('correlation', 0)
                    action_items.append({
                        'action': f"Review overlapping exposure between {pair[0]} and {pair[1]}",
                        'amount': 0,
                        'rationale': f"High correlation ({corr:.2f}) indicates potential concentration risk despite different names."
                    })
                
                self.recommendations.append({
                    'id': self._generate_recommendation_id(),
                    'type': 'CORRELATION_RISK',
                    'title': 'High Asset Correlation Warning',
                    'title_cn': 'High Correlation Alert',
                    'description': f'Identified {len(critical_pairs)} asset pairs with extreme correlation (>0.8), reducing diversification effectiveness.',
                    'impact': {
                        'dollar_value': 0,
                        'drift_reduction': 0,
                        'risk_reduction': 'MEDIUM'
                    },
                    'action_items': action_items,
                    'urgency': 'MEDIUM',
                    'category': 'Risk Management',
                    'estimated_effort': 'MEDIUM',
                    'tax_implications': None,
                    'priority': 0
                })
        except Exception as e:
            self.logger.error(f"Error generating correlation recommendations: {e}")

    def _generate_liquidity_stress_recommendation(self, rebalancing_data: Dict):
        """
        Generate recommendations based on liquidity stress test results.
        
        Args:
            rebalancing_data: Dictionary containing stress_test_results
        """
        try:
            # Check for liquidity issues in stress test
            # Note: This expects stress_test_data to be present in rebalancing_data
            stress_data = rebalancing_data.get('stress_test_data', {})
            if not stress_data or not stress_data.get('has_liquidity_issue', False):
                return

            self.recommendations.append({
                'id': self._generate_recommendation_id(),
                'type': 'LIQUIDITY_STRESS',
                'title': 'Liquidity Stress Warning',
                'title_cn': 'Liquidity Stress Alert',
                'description': 'Stress tests indicate potential net cash flow issues under market shock scenarios (e.g., -20% income, +20% expenses).',
                'impact': {
                    'dollar_value': 0,
                    'drift_reduction': 0,
                    'risk_reduction': 'HIGH'
                },
                'action_items': [
                    {
                        'action': "Increase cash/liquid reserves",
                        'amount': 0,
                        'rationale': "Buffer needed for potential income/expense shocks identified in stress simulation."
                    },
                    {
                        'action': "Review discretionary spending items",
                        'amount': 0,
                        'rationale': "Identify potential expense reductions to improve net cash flow resilience."
                    }
                ],
                'urgency': 'HIGH',
                'category': 'Cash Flow',
                'estimated_effort': 'LOW',
                'tax_implications': None,
                'priority': 0
            })
        except Exception as e:
            self.logger.error(f"Error generating liquidity stress recommendations: {e}")
    
    def _generate_recommendation_id(self) -> str:
        """Generate unique recommendation ID."""
        self._recommendation_counter += 1
        return f"rec_{self._recommendation_counter:03d}"
    
    def get_recommendation_summary(self) -> Dict:
        """
        Get summary statistics about generated recommendations.
        
        Returns:
            Dictionary with recommendation statistics
        """
        if not self.recommendations:
            return {
                'total_count': 0,
                'high_priority_count': 0,
                'medium_priority_count': 0,
                'low_priority_count': 0,
                'total_potential_impact': 0,
                'categories': {}
            }
        
        high_priority = len([r for r in self.recommendations if r['priority'] >= 80])
        medium_priority = len([r for r in self.recommendations if 60 <= r['priority'] < 80])
        low_priority = len([r for r in self.recommendations if r['priority'] < 60])
        
        total_impact = sum(r['impact']['dollar_value'] for r in self.recommendations)
        
        # Category breakdown
        categories = {}
        for rec in self.recommendations:
            cat = rec['category']
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1
        
        return {
            'total_count': len(self.recommendations),
            'high_priority_count': high_priority,
            'medium_priority_count': medium_priority,
            'low_priority_count': low_priority,
            'total_potential_impact': total_impact,
            'categories': categories
        }
    
    def _apply_dynamic_targets(
        self,
        rebalancing_data: Dict,
        market_regime: Dict,
        portfolio_value: float
    ) -> Dict:
        """
        Apply dynamic allocation targets from market regime to rebalancing data.
        
        This method overrides the baseline targets from asset_taxonomy.yaml with
        regime-specific targets (e.g., shift from 75% equity to 55% in Maximum Defense).
        
        Args:
            rebalancing_data: Original rebalancing data with baseline targets
            market_regime: Market regime dict with dynamic_targets
            portfolio_value: Total portfolio value
        
        Returns:
            Modified rebalancing_data with updated targets
        """
        try:
            dynamic_targets = market_regime.get('dynamic_targets', {})
            top_level_targets = dynamic_targets.get('top_level', {})
            sub_category_targets = dynamic_targets.get('sub_category', {})
            
            if not top_level_targets:
                self.logger.warning("No top_level targets in dynamic_targets, skipping application")
                return rebalancing_data
            
            self.logger.info("=" * 80)
            self.logger.info(f"Applying dynamic targets from {market_regime.get('regime_name_cn', 'N/A')} regime")
            self.logger.info("=" * 80)
            
            # CRITICAL FIX: Get rebalanceable_value for correct target_value calculation
            rebalanceable_value = rebalancing_data.get('rebalanceable_value', portfolio_value)
            self.logger.info(f"Using rebalanceable_value: ¥{rebalanceable_value:,.0f} for target calculations")
            
            # Update top-level targets in rebalancing_data
            top_level_table = rebalancing_data.get('top_level_table', [])
            
            for item in top_level_table:
                asset_class_cn = item.get('asset_class')
                
                # Find matching dynamic target
                if asset_class_cn in top_level_targets:
                    # CRITICAL FIX: Use correct key names (current_pct, target_pct, not current, target)
                    old_target_pct = item.get('target_pct', 0)
                    new_target_decimal = top_level_targets[asset_class_cn]  # Decimal form (0.70 for 70%)
                    new_target_pct = new_target_decimal * 100  # Convert to percentage
                    
                    # Update target_pct and recalculate drift
                    item['target_pct'] = new_target_pct
                    item['drift'] = item.get('current_pct', 0) - new_target_pct
                    
                    # CRITICAL FIX: Use rebalanceable_value for rebalanceable assets, not total portfolio_value
                    if item.get('is_rebalanceable', True):
                        item['target_value'] = (new_target_pct / 100) * rebalanceable_value
                    else:
                        # Non-rebalanceable assets have 0 target
                        item['target_value'] = 0
                    
                    self.logger.info(f"  {asset_class_cn}: {old_target_pct:.1f}% → {new_target_pct:.1f}% (drift: {item['drift']:+.1f}%)")
            
            # Update sub-category targets if provided
            if sub_category_targets:
                sub_category_table = rebalancing_data.get('sub_category_table', [])
                
                for parent_class, sub_targets in sub_category_targets.items():
                    for item in sub_category_table:
                        if item.get('parent_class') == parent_class:
                            sub_class_cn = item.get('sub_class')
                            
                            if sub_class_cn in sub_targets:
                                old_target_pct = item.get('target_pct', 0)
                                new_target_decimal = sub_targets[sub_class_cn]
                                new_target_pct = new_target_decimal * 100
                                
                                item['target_pct'] = new_target_pct
                                item['drift'] = item.get('current_pct', 0) - new_target_pct
                                
                                # Sub-categories also use rebalanceable_value
                                if item.get('is_rebalanceable', True):
                                    item['target_value'] = (new_target_pct / 100) * rebalanceable_value
                                else:
                                    item['target_value'] = 0
                                
                                self.logger.info(f"  {parent_class}/{sub_class_cn}: {old_target_pct:.1f}% → {new_target_pct:.1f}%")
            
            # Recalculate proportional allocation with new targets
            # This ensures capital allocation recommendations use regime-adjusted targets
            rebalancing_data = self._recalculate_proportional_allocation(rebalancing_data, portfolio_value)
            
            self.logger.info("✓ Dynamic targets applied successfully")
            return rebalancing_data
            
        except Exception as e:
            self.logger.error(f"Error applying dynamic targets: {e}", exc_info=True)
            return rebalancing_data
    
    def _recalculate_proportional_allocation(
        self,
        rebalancing_data: Dict,
        portfolio_value: float
    ) -> Dict:
        """
        Recalculate proportional allocation after target updates.
        
        CRITICAL FIX: Uses rebalanceable_value from rebalancing_data for calculations.
        
        Args:
            rebalancing_data: Rebalancing data with updated targets (must contain rebalanceable_value)
            portfolio_value: Total portfolio value (for reference only)
        
        Returns:
            Updated rebalancing_data with new proportional_allocation
        """
        try:
            top_level_table = rebalancing_data.get('top_level_table', [])
            rebalanceable_value = rebalancing_data.get('rebalanceable_value', portfolio_value) or 0.0
            
            # Find under-allocated classes
            under_allocated = [
                item for item in top_level_table
                if item.get('is_rebalanceable', False) and item.get('drift', 0) < -1.0
            ]
            
            if not under_allocated:
                rebalancing_data['proportional_allocation'] = []
                return rebalancing_data
            
            # Calculate gaps and allocations using rebalanceable_value
            reference_capital = 100000
            total_gap = 0.0
            gaps = []
            for item in under_allocated:
                drift_pct = item.get('drift', 0.0) or 0.0
                gap_amount = abs(drift_pct) / 100.0 * rebalanceable_value
                gaps.append((item, gap_amount))
                total_gap += gap_amount
            
            proportional_allocation = []
            for item, gap_amount in gaps:
                proportion = gap_amount / total_gap if total_gap > 0 else 0
                allocation_amount = reference_capital * proportion
                current_pct = item.get('current_pct', item.get('current', 0)) or 0.0
                target_pct = item.get('target_pct', item.get('target', 0)) or 0.0

                current_value = (current_pct / 100.0) * rebalanceable_value
                new_total = rebalanceable_value + reference_capital
                new_value = current_value + allocation_amount
                new_current_pct = (new_value / new_total * 100.0) if new_total > 0 else current_pct
                new_drift = new_current_pct - target_pct
                original_drift = abs(item.get('drift', 0))
                gap_closed = ((original_drift - abs(new_drift)) / original_drift) if original_drift else 0
                
                proportional_allocation.append({
                    'asset_class': item['asset_class'],
                    'asset_class_en': item.get('asset_class_en', ''),
                    'current_drift': item['drift'],
                    'gap_amount': gap_amount,
                    'proportion': proportion,
                    'amount': allocation_amount,
                    'percentage': proportion,
                    'new_drift': new_drift,
                    'gap_closed': gap_closed
                })
            
            rebalancing_data['proportional_allocation'] = proportional_allocation
            return rebalancing_data
            
        except Exception as e:
            self.logger.error(f"Error recalculating proportional allocation: {e}", exc_info=True)
            return rebalancing_data
    
    def _inject_strategic_recommendations(
        self,
        market_regime: Dict,
        rebalancing_data: Dict,
        portfolio_value: float,
        holdings_df: pd.DataFrame,
        strategic_directive: Optional[Dict] = None
    ):
        """
        Inject strategic recommendations from market regime at top priority.
        
        Generates portfolio-specific action steps based on actual holdings.
        
        CRITICAL FIX: Uses rebalanceable_value from rebalancing_data for financial impact
        calculations instead of total portfolio_value.
        
        Args:
            market_regime: Market regime dict with strategic_recommendations
            rebalancing_data: Rebalancing analysis data with current allocations and drifts
            portfolio_value: Total portfolio value (for reference only)
            holdings_df: Current portfolio holdings
            strategic_directive: Optional strategic directive with enriched action steps
        """
        try:
            strategic_recs = market_regime.get('strategic_recommendations', [])
            
            if not strategic_recs:
                return
            
            self.logger.info(f"Injecting {len(strategic_recs)} strategic recommendations from regime")
            
            # CRITICAL FIX: Extract rebalanceable_value for correct financial impact calculation
            rebalanceable_value = rebalancing_data.get('rebalanceable_value', portfolio_value)
            self.logger.info(f"Using rebalanceable_value: ¥{rebalanceable_value:,.0f} (vs total: ¥{portfolio_value:,.0f})")
            
            # PHASE 6.1.1: Validate and reconstruct class_allocation if incomplete
            class_allocation = rebalancing_data.get('class_allocation', {})
            if not class_allocation or not isinstance(class_allocation, dict):
                self.logger.warning("class_allocation missing or invalid, reconstructing from top_level_table")
                class_allocation = self._build_class_allocation_from_table(
                    rebalancing_data.get('top_level_table', []),
                    portfolio_value
                )
                self.logger.info(f"Reconstructed class_allocation with {len(class_allocation)} classes")
            
            # Log class allocation for debugging
            self.logger.info(f"DEBUG: class_allocation keys: {list(class_allocation.keys())}")
            for cls, data in class_allocation.items():
                self.logger.info(f"  {cls}: value={data.get('value', 0):,.0f}, current_pct={data.get('current_pct', 0):.2%}, is_rebalanceable={data.get('is_rebalanceable', True)}")
            
            dynamic_targets = market_regime.get('dynamic_targets', {}).get('top_level', {})
            
            # PHASE 1B: Get strategic directive action steps for enriched gap data
            action_steps_with_gaps = {}
            if strategic_directive:
                action_steps_with_gaps = {
                    step.get('action_cn'): step 
                    for step in strategic_directive.get('action_steps', [])
                    if step.get('action_cn')
                }
                self.logger.info(f"Found {len(action_steps_with_gaps)} action steps with gap data from strategic directive")
            else:
                self.logger.info("No strategic directive provided, strategic recommendations will use base rationale")
            
            for idx, strategy in enumerate(strategic_recs):
                rec_id = self._generate_recommendation_id()
                
                # Extract action content from YAML
                action_text = strategy.get('action', '')
                action_text_cn = strategy.get('action_cn', '')
                rationale_text = strategy.get('rationale', '')
                rationale_text_cn = strategy.get('rationale_cn', '')
                
                # PHASE 1B: Enrich description with gap data if available
                if action_text_cn in action_steps_with_gaps:
                    enriched_step = action_steps_with_gaps[action_text_cn]
                    # Use enriched rationale with gap data
                    rationale_text = enriched_step.get('rationale', rationale_text)
                    rationale_text_cn = enriched_step.get('rationale_cn', rationale_text_cn)
                    self.logger.info(f"✅ Enriched '{action_text_cn[:40]}...' with gap data")
                
                # Generate portfolio-specific action items
                action_items = self._generate_portfolio_specific_actions(
                    strategy, class_allocation, dynamic_targets, holdings_df, rebalanceable_value
                )
                
                # Calculate financial impact based on strategy priority and actual portfolio changes
                # CRITICAL FIX: Use rebalanceable_value instead of total portfolio_value
                strategy_priority = strategy.get('priority', 50)
                estimated_impact = self._estimate_strategic_impact(
                    strategy, class_allocation, dynamic_targets, rebalanceable_value
                )
                
                rec = {
                    'id': rec_id,
                    'type': 'STRATEGIC_REGIME',
                    'title': action_text,
                    'title_cn': action_text_cn if action_text_cn else f"Strategic Action {idx+1}",
                    'description': rationale_text,
                    'description_cn': rationale_text_cn,
                    'impact': {
                        'dollar_value': estimated_impact,
                        'drift_reduction': 0,
                        'risk_reduction': 'HIGH'
                    },
                    'action_items': action_items,
                    'urgency': 'HIGH',
                    'category': 'Market Regime Strategy',
                    'estimated_effort': 'MEDIUM',
                    'tax_implications': None,
                    'priority': 90 + (len(strategic_recs) - idx),
                    'metadata': {
                        'regime_name': market_regime.get('regime_name'),
                        'regime_name_cn': market_regime.get('regime_name_cn'),
                        'regime_priority': market_regime.get('priority'),
                        'strategy_priority': strategy_priority
                    }
                }
                
                self.recommendations.append(rec)
                self.logger.info(f"  ✓ Injected strategic recommendation: {rec['title_cn']}")
            
        except Exception as e:
            self.logger.error(f"Error injecting strategic recommendations: {e}", exc_info=True)
    
    def _generate_portfolio_specific_actions(
        self,
        strategy: Dict,
        class_allocation: Dict,
        dynamic_targets: Dict,
        holdings_df: pd.DataFrame,
        rebalanceable_value: float
    ) -> List[Dict]:
        """
        Generate portfolio-specific action steps based on strategy and holdings.
        
        CRITICAL FIX: Uses rebalanceable_value for calculations instead of total portfolio value.
        
        Args:
            strategy: Strategy dict with action details
            class_allocation: Current asset class allocations
            dynamic_targets: Target allocations
            holdings_df: Current holdings
            rebalanceable_value: Rebalanceable portfolio value (excludes Real Estate, Insurance)
        
        Returns:
            List of action item dicts
        """
        action_items = []
        action_cn = strategy.get('action_cn', '')
        
        try:
            # PHASE 6.1.3: Check if asset class is non-rebalanceable
            asset_class_in_strategy = self._identify_asset_class_from_strategy(action_cn)
            if asset_class_in_strategy in self.non_rebalanceable_classes:
                self.logger.info(f"Skipping action generation for non-rebalanceable class: {asset_class_in_strategy}")
                action_items.append({
                    'action': f"{asset_class_in_strategy} is non-rebalanceable - maintain current holdings",
                    'amount': 0,
                    'rationale': "This asset class is excluded from rebalancing per asset_taxonomy.yaml configuration"
                })
                return action_items
            
            # Analyze strategy keywords to generate specific actions
            if '轮动' in action_cn or 'rotate' in strategy.get('action', '').lower():
                # PHASE 6.1.2: Rotation strategy with improved filtering
                us_holdings = pd.DataFrame()
                cn_holdings = pd.DataFrame()
                
                if 'Asset_Name' in holdings_df.columns:
                    try:
                        us_holdings = holdings_df[
                            holdings_df['Asset_Name'].fillna('').str.contains(
                                'VOO|QQQ|SPY|US Stock|AMZN', case=False, regex=True
                            )
                        ]
                        cn_holdings = holdings_df[
                            holdings_df['Asset_Name'].fillna('').str.contains(
                                '中国|国内|沪深|港股|A股|景顺|易方达|广发|汇添富|博时', case=False, regex=True
                            )
                        ]
                        self.logger.info(f"DEBUG: US holdings count: {len(us_holdings)}, CN holdings count: {len(cn_holdings)}")
                    except Exception as e:
                        self.logger.warning(f"Error filtering holdings: {e}")
                else:
                    self.logger.warning("Asset_Name column missing in holdings_df")
                
                us_total = us_holdings['Market_Value_CNY'].sum() if not us_holdings.empty else 0
                cn_total = cn_holdings['Market_Value_CNY'].sum() if not cn_holdings.empty else 0
                
                self.logger.info(f"DEBUG: US total value: ¥{us_total:,.0f}, CN total value: ¥{cn_total:,.0f}")
                
                # PHASE 6.1.4: Calculate rotation based on dynamic_targets instead of hardcoded percentages
                sub_category_targets = dynamic_targets.get('sub_category', {}).get('Equity', {}) if isinstance(dynamic_targets, dict) else {}
                us_target_pct = sub_category_targets.get('US Equity', 0.30) if sub_category_targets else 0.30
                cn_target_pct = sub_category_targets.get('CN Equity', 0.50) if sub_category_targets else 0.50
                
                self.logger.info(f"DEBUG: Sub-category targets - US: {us_target_pct*100:.0f}%, CN: {cn_target_pct*100:.0f}%")
                
                equity_total = us_total + cn_total
                if equity_total > 0:
                    us_should_be = equity_total * us_target_pct
                    cn_should_be = equity_total * cn_target_pct
                    
                    if us_total > us_should_be:
                        rotation_amount = us_total - us_should_be
                        action_items.append({
                            'action': f"Sell ¥{rotation_amount:,.0f} of US equities (VOO, QQQ, SPY) to rotate to Chinese assets",
                            'amount': rotation_amount,
                            'rationale': f"Target US allocation: {us_target_pct*100:.0f}% of equity (¥{us_should_be:,.0f}), Current: ¥{us_total:,.0f}"
                        })
                    
                    if cn_total < cn_should_be:
                        increase_amount = cn_should_be - cn_total
                        action_items.append({
                            'action': f"Increase Chinese equity allocation to ¥{cn_should_be:,.0f}",
                            'amount': increase_amount,
                            'rationale': f"Target {cn_target_pct*100:.0f}% of equity in Chinese assets (¥{cn_should_be:,.0f}), Current: ¥{cn_total:,.0f}"
                        })
            
            elif 'Reduce' in action_cn and 'Equity' in action_cn:
                # Reduce equity exposure
                equity_class = class_allocation.get('Equity', {})
                current_value = equity_class.get('value', 0)
                current_pct = equity_class.get('current_pct', 0)
                target_pct = dynamic_targets.get('Equity', 0.75)
                
                reduction_amount = current_value - (rebalanceable_value * target_pct)
                if reduction_amount > 0:
                    action_items.append({
                        'action': f"Reduce equity holdings by ¥{reduction_amount:,.0f}",
                        'amount': reduction_amount,
                        'rationale': f"Current: {current_pct:.1f}% (¥{current_value:,.0f}) → Target: {target_pct*100:.0f}%"
                    })
                    
                    # Identify specific high-value holdings to reduce
                    equity_holdings = holdings_df[holdings_df['Market_Value_CNY'] > rebalanceable_value * 0.05].nlargest(3, 'Market_Value_CNY')
                    for _, holding in equity_holdings.iterrows():
                        asset_name = holding['Asset_Name']
                        asset_value = holding['Market_Value_CNY']
                        action_items.append({
                            'action': f"Consider reducing {asset_name}",
                            'amount': asset_value * 0.2,  # Suggest 20% reduction
                            'rationale': f"Current position: ¥{asset_value:,.0f} ({asset_value/rebalanceable_value*100:.1f}% of rebalanceable portfolio)"
                        })
            
            elif 'Fixed Income' in action_cn or 'Bond' in action_cn:
                # Increase fixed income
                bond_class = class_allocation.get('Fixed Income', {})
                current_value = bond_class.get('value', 0)
                target_pct = dynamic_targets.get('Fixed Income', 0.15)
                increase_amount = (rebalanceable_value * target_pct) - current_value
                
                if increase_amount > 0:
                    action_items.append({
                        'action': f"Increase fixed income allocation by ¥{increase_amount:,.0f}",
                        'amount': increase_amount,
                        'rationale': f"Target: {target_pct*100:.0f}% (¥{rebalanceable_value * target_pct:,.0f}), Current: ¥{current_value:,.0f}"
                    })
                    action_items.append({
                        'action': "Consider: BND, AGG, or Chinese bond funds",
                        'amount': increase_amount,
                        'rationale': "Increase defensive positioning with high-quality bonds"
                    })
            
            # If no specific actions generated, fall back to generic action
            if not action_items:
                action_items.append({
                    'action': strategy.get('action', ''),
                    'amount': 0,
                    'rationale': strategy.get('rationale', '')
                })
        
        except Exception as e:
            self.logger.warning(f"Error generating portfolio-specific actions: {e}")
            # Fallback to generic action
            action_items.append({
                'action': strategy.get('action', ''),
                'amount': 0,
                'rationale': strategy.get('rationale', '')
            })
        
        # PHASE 6: Log generated actions for debugging
        self.logger.info(f"DEBUG: Generated {len(action_items)} action items for strategy: {strategy.get('action_cn', 'N/A')[:50]}...")
        for idx, item in enumerate(action_items, 1):
            self.logger.info(f"  Action {idx}: {item.get('action', 'N/A')[:80]}...")
        
        return action_items
    
    def _estimate_strategic_impact(
        self,
        strategy: Dict,
        class_allocation: Dict,
        dynamic_targets: Dict,
        rebalanceable_value: float
    ) -> float:
        """
        Estimate financial impact of strategic action based on portfolio changes.
        
        CRITICAL: Uses rebalanceable_value (excludes Real Estate, Insurance) instead of
        total portfolio value to avoid inflating impact numbers.
        
        Args:
            strategy: Strategy dict with action details
            class_allocation: Current asset class allocations
            dynamic_targets: Target allocations from market regime
            rebalanceable_value: Rebalanceable portfolio value (excludes non-rebalanceable assets)
        
        Returns:
            Financial impact in CNY
        """
        try:
            strategy_priority = strategy.get('priority', 50)
            action_cn = strategy.get('action_cn', '')
            
            # Try to calculate actual impact based on target changes
            if 'Equity' in action_cn:
                equity_class = class_allocation.get('Equity', {})
                current_value = equity_class.get('value', 0)
                target_pct = dynamic_targets.get('Equity', 0.75)
                target_value = rebalanceable_value * target_pct
                return abs(target_value - current_value)
            
            elif 'Fixed Income' in action_cn:
                bond_class = class_allocation.get('Fixed Income', {})
                current_value = bond_class.get('value', 0)
                target_pct = dynamic_targets.get('Fixed Income', 0.15)
                target_value = rebalanceable_value * target_pct
                return abs(target_value - current_value)
            
            # Fallback to priority-based estimation (use rebalanceable value)
            if strategy_priority >= 95:
                return rebalanceable_value * 0.15
            elif strategy_priority >= 90:
                return rebalanceable_value * 0.10
            elif strategy_priority >= 85:
                return rebalanceable_value * 0.08
            else:
                return rebalanceable_value * 0.05
        except Exception as e:
            self.logger.error(f"Error calculating strategy impact: {e}")
            return 0
    
    def _extract_portfolio_state(self, rebalancing_data: Dict, portfolio_value: float) -> Dict:
        """
        Extract portfolio state for portfolio-aware strategic directive (Phase 1B).
        
        Args:
            rebalancing_data: Rebalancing analysis data
            portfolio_value: Total portfolio value
        
        Returns:
            Dict with:
                - current_allocation: {asset_class_cn: percentage, ...}
                - total_value: total portfolio value in CNY
                - rebalanceable_value: rebalanceable portfolio value (excludes insurance, real estate)
                - non_rebalanceable_classes: list of non-rebalanceable asset classes
        """
        portfolio_state = {
            'current_allocation': {},
            'total_value': portfolio_value,
            'rebalanceable_value': portfolio_value,  # Will be updated below
            'non_rebalanceable_classes': self.non_rebalanceable_classes,  # From asset_taxonomy.yaml
            'sub_level_table': []  # Sub-category allocation data for regional rotation
        }
        
        try:
            # Extract current allocations from rebalancing data
            class_allocation = rebalancing_data.get('class_allocation', {})
            
            # Fallback: if class_allocation is empty, try to reconstruct from top_level_table
            if not class_allocation:
                top_level_table = rebalancing_data.get('top_level_table', [])
                if top_level_table:
                    self.logger.info("class_allocation empty, reconstructing from top_level_table")
                    class_allocation = {}
                    for item in top_level_table:
                        asset_class = item.get('asset_class')
                        if asset_class:
                            class_allocation[asset_class] = {
                                'value': item.get('current_value', 0),
                                'percentage': item.get('current', 0),
                                'target': item.get('target', 0)
                            }
            
            # Get rebalanceable value (excludes insurance, real estate)
            rebalanceable_value = rebalancing_data.get('rebalanceable_value', portfolio_value)
            portfolio_state['rebalanceable_value'] = rebalanceable_value
            
            # Add sub-category allocation data for regional rotation calculation
            sub_level_table = rebalancing_data.get('sub_level_table', [])
            portfolio_state['sub_level_table'] = sub_level_table
            
            # Build current allocation percentages (as fraction of REBALANCEABLE value)
            for asset_class, class_data in class_allocation.items():
                if isinstance(class_data, dict):
                    # If it's a dict with 'value' key
                    current_value = class_data.get('value', 0)
                    if rebalanceable_value > 0:
                        pct = current_value / rebalanceable_value
                        portfolio_state['current_allocation'][asset_class] = pct
                    else:
                        portfolio_state['current_allocation'][asset_class] = 0.0
                elif isinstance(class_data, (int, float)):
                    # If it's just a percentage value
                    portfolio_state['current_allocation'][asset_class] = class_data
            
            self.logger.info(f"Extracted portfolio state: {len(portfolio_state['current_allocation'])} asset classes, "
                           f"rebalanceable value: ¥{rebalanceable_value:,.0f}, "
                           f"non-rebalanceable: {self.non_rebalanceable_classes}")
            
        except Exception as e:
            self.logger.error(f"Error extracting portfolio state: {e}")
        
        return portfolio_state
