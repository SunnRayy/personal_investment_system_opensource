"""
Strategic Directive Builder - Extracts and formats market regime strategy into user-friendly directive.

This module implements Phase 1 of Action Compass V2.0 "Pyramid Logic" enhancement.
It transforms raw market regime data into a clear strategic directive that answers: "What should we do?" (What should we do?)

Author: Personal Investment System - Action Compass V2.0
Date: October 30, 2025
Version: 1.0
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


@dataclass
class StrategicDirective:
    """
    Data class representing a strategic directive extracted from market regime.
    
    Attributes:
        regime_name: English name of market regime (e.g., "Maximum Defense")
        regime_name_cn: Chinese name (e.g., "Maximum Defense")
        regime_description: English description of market condition
        regime_description_cn: Chinese description
        core_objective: Main strategic goal (e.g., "Preserve capital and build cash reserves")
        core_objective_cn: Chinese translation
        action_steps: List of prioritized action items (3-5 items)
        allocation_changes: List of key allocation adjustments with arrows
        allocation_gaps: Optional list of portfolio gaps (current vs target) - Phase 1B
        risk_level: Overall risk posture (HIGH/MEDIUM/LOW)
        confidence: Confidence level based on number of matched indicators (0-100)
    """
    regime_name: str
    regime_name_cn: str
    regime_description: str
    regime_description_cn: str
    core_objective: str
    core_objective_cn: str
    action_steps: List[Dict[str, str]] = field(default_factory=list)
    allocation_changes: List[Dict[str, str]] = field(default_factory=list)
    allocation_gaps: Optional[List[Dict]] = None  # Phase 1B: Portfolio-aware gaps
    risk_level: str = "MEDIUM"
    confidence: int = 100


class StrategicDirectiveBuilder:
    """
    Builds strategic directives from market regime data.
    
    This class transforms raw market regime configuration (from market_regimes.yaml
    and IndicatorRegimeDetector) into user-friendly strategic guidance that appears
    at the top of Action Compass reports.
    
    Design Principles:
    - Clarity over complexity: Use simple language
    - Action-oriented: Every directive leads to concrete actions
    - Hierarchical: Strategic → Tactical → Asset (this handles Strategic)
    """
    
    def __init__(self):
        """Initialize the strategic directive builder."""
        self.logger = logging.getLogger(__name__)
    
    def build_directive(
        self, 
        market_regime: Dict,
        portfolio_state: Optional[Dict] = None
    ) -> Optional[StrategicDirective]:
        """
        Build strategic directive from market regime data and current portfolio state.
        
        Args:
            market_regime: Dict containing:
                - regime_name/name: Regime name (e.g., "Cautious Rotation")
                - regime_name_cn/name_cn: Chinese name
                - description: English description
                - description_cn: Chinese description
                - strategic_recommendations: List of recommendation dicts
                - dynamic_targets: Dict with top_level and sub_category allocations
                - indicators: Dict of indicator values that triggered this regime
            portfolio_state: Optional dict with:
                - current_allocation: {asset_class_cn: percentage, ...}
                - total_value: total portfolio value in CNY
                - liquid_value: liquid assets value (excludes insurance)
        
        Returns:
            StrategicDirective object or None if insufficient data
        
        Example:
            >>> builder = StrategicDirectiveBuilder()
            >>> directive = builder.build_directive(regime_data, portfolio_state)
            >>> print(directive.core_objective)
            "Reduce equity by 12.6% (¥1.2M) from 82.6% to 70%"
        """
        if not market_regime:
            self.logger.warning("Empty market_regime provided")
            return None
        
        try:
            # Extract basic regime info (support both 'name' and 'regime_name' keys)
            regime_name = market_regime.get('regime_name') or market_regime.get('name', 'Unknown Regime')
            regime_name_cn = market_regime.get('regime_name_cn') or market_regime.get('name_cn', 'Unknown Regime')
            regime_description = market_regime.get('description', '')
            regime_description_cn = market_regime.get('description_cn', '')
            
            # Extract strategic recommendations
            strategic_recs = market_regime.get('strategic_recommendations', [])
            if not strategic_recs:
                self.logger.warning(f"No strategic recommendations for regime: {regime_name}")
                return None
            
            # Calculate allocation gaps if portfolio state provided
            allocation_gaps = None
            if portfolio_state:
                allocation_gaps = self._calculate_allocation_gaps(
                    market_regime.get('dynamic_targets', {}),
                    portfolio_state
                )
            
            # Extract core objective from highest priority recommendation
            core_objective, core_objective_cn = self._extract_core_objective(
                strategic_recs,
                allocation_gaps
            )
            
            # Build action steps from top 3-5 recommendations
            action_steps = self._build_action_steps(
                strategic_recs,
                allocation_gaps,
                portfolio_state,  # Pass portfolio_state for regional calculations
                max_steps=5
            )
            
            # Format allocation changes from dynamic_targets
            allocation_changes = self._format_allocation_changes(
                market_regime.get('dynamic_targets', {})
            )
            
            # Determine risk level from regime name
            risk_level = self._determine_risk_level(regime_name)
            
            # Calculate confidence based on indicator match count
            confidence = self._calculate_confidence(market_regime)
            
            directive = StrategicDirective(
                regime_name=regime_name,
                regime_name_cn=regime_name_cn,
                regime_description=regime_description,
                regime_description_cn=regime_description_cn,
                core_objective=core_objective,
                core_objective_cn=core_objective_cn,
                action_steps=action_steps,
                allocation_changes=allocation_changes,
                allocation_gaps=allocation_gaps,  # Phase 1B: Add portfolio gaps
                risk_level=risk_level,
                confidence=confidence
            )
            
            self.logger.info(f"Built strategic directive for regime: {regime_name}")
            return directive
        
        except Exception as e:
            self.logger.error(f"Error building strategic directive: {e}", exc_info=True)
            return None
    
    def _calculate_allocation_gaps(
        self,
        regime_targets: Dict,
        portfolio_state: Dict
    ) -> List[Dict]:
        """
        Calculate gaps between current allocation and regime targets.
        
        CRITICAL: Only calculates gaps for REBALANCEABLE asset classes.
        Excludes: Real Estate, Insurance
        
        Args:
            regime_targets: {'top_level': {'股票': 0.70, '固定收益': 0.15, ...}}
            portfolio_state: {
                'current_allocation': {asset_class: percentage, ...},
                'rebalanceable_value': liquid rebalanceable portfolio value,
                'non_rebalanceable_classes': ['Real Estate', 'Insurance']
            }
        
        Returns:
            List of gap dicts sorted by magnitude:
            [{
                'asset_class': '股票',
                'asset_class_en': 'Equity',
                'current_pct': 0.826,
                'target_pct': 0.70,
                'gap_pct': -0.126,  # negative = overweight (reduce), positive = underweight (add)
                'gap_amount': -1200000,  # CNY amount to REMOVE (negative) or ADD (positive)
                'status': 'reduce',  # 'reduce' | 'increase' | 'aligned'
                'alignment': 'danger' (>10% gap) | 'warning' (5-10%) | 'success' (<5%)
            }]
        """
        gaps = []
        current_allocation = portfolio_state.get('current_allocation', {})
        # Use rebalanceable_value (excludes insurance, real estate)
        rebalanceable_value = portfolio_state.get('rebalanceable_value') or \
                             portfolio_state.get('liquid_value') or \
                             portfolio_state.get('total_value', 0)
        non_rebalanceable = portfolio_state.get('non_rebalanceable_classes', ['Real Estate', 'Insurance'])
        
        # Extract top-level targets
        top_level_targets = regime_targets.get('top_level', {})
        
        if not top_level_targets:
            self.logger.warning("No top_level targets in regime_targets")
            return gaps
        
        # Asset class name mapping (Internal → Display EN)
        asset_name_map = {
            'Equity': 'Equity',
            'Fixed Income': 'Fixed Income',
            'Cash': 'Cash',
            'Commodities': 'Commodities',
            'Alternative': 'Alternative',
            'Gold': 'Gold',
            'Crypto': 'Crypto',
            'Real Estate': 'Real Estate',
            'Insurance': 'Insurance'
        }
        
        self.logger.debug(f"Gap calculation - Current: {current_allocation}")
        self.logger.debug(f"Gap calculation - Targets: {top_level_targets}")
        self.logger.debug(f"Gap calculation - Rebalanceable value: ¥{rebalanceable_value:,.0f}")
        self.logger.debug(f"Gap calculation - Non-rebalanceable: {non_rebalanceable}")
        
        # Calculate gaps for all target asset classes (skip non-rebalanceable)
        for asset_class_cn, target_pct in top_level_targets.items():
            # SKIP non-rebalanceable classes
            if asset_class_cn in non_rebalanceable:
                self.logger.debug(f"  Skipping non-rebalanceable: {asset_class_cn}")
                continue
            
            current_pct = current_allocation.get(asset_class_cn, 0.0)
            
            # gap_pct = current - target
            # Negative = underweight (need to ADD money)
            # Positive = overweight (need to REMOVE money)
            gap_pct = current_pct - target_pct
            
            # gap_amount follows gap_pct sign
            # Negative = ADD this much money
            # Positive = REMOVE this much money
            gap_amount = gap_pct * rebalanceable_value
            
            # Determine status and alignment level
            abs_gap = abs(gap_pct)
            if abs_gap < 0.05:  # <5% gap
                status = 'aligned'
                alignment = 'success'
            elif gap_pct < 0:  # Negative = underweight (need to add)
                status = 'increase'
                alignment = 'danger' if abs_gap > 0.10 else 'warning'
            else:  # Positive = overweight (need to reduce)
                status = 'reduce'
                alignment = 'danger' if abs_gap > 0.10 else 'warning'
            
            # Map asset class name
            asset_class_en = asset_name_map.get(asset_class_cn, asset_class_cn)
            
            gaps.append({
                'asset_class': asset_class_cn,
                'asset_class_en': asset_class_en,
                'current_pct': round(current_pct, 4),
                'target_pct': round(target_pct, 4),
                'gap_pct': round(gap_pct, 4),
                'gap_amount': round(gap_amount, 0),
                'status': status,
                'alignment': alignment
            })
            
            self.logger.debug(f"  {asset_class_cn}: {current_pct:.1%} vs {target_pct:.1%}, "
                            f"gap={gap_pct:+.1%} ({status}), amount={gap_amount:+,.0f}")
        
        # Sort by absolute gap magnitude (largest first)
        gaps.sort(key=lambda x: abs(x['gap_pct']), reverse=True)
        
        self.logger.info(f"Calculated {len(gaps)} allocation gaps (excluding {len(non_rebalanceable)} non-rebalanceable)")
        return gaps
    
    def _extract_core_objective(
        self,
        strategic_recs: List[Dict],
        allocation_gaps: Optional[List[Dict]] = None
    ) -> tuple:
        """
        Extract and contextualize core strategic objective.
        
        Args:
            strategic_recs: List of strategic recommendation dicts
            allocation_gaps: Optional list of gap dicts from _calculate_allocation_gaps()
        
        Returns:
            Tuple of (core_objective_en, core_objective_cn) - contextualized with portfolio state
        
        Examples:
            Generic: "Rotate from US to CN stocks"
            Contextualized: "Continue CN overweight - already at 65% (target: 60%)"
            
            Generic: "Reduce equity to 70%"
            Contextualized: "Reduce equity by 12.6% (¥1.2M) from 82.6% to 70%"
        
        Logic:
            1. Get highest priority recommendation
            2. If no portfolio gaps, return generic objective
            3. Otherwise, contextualize with current state and gap amounts
        """
        if not strategic_recs:
            return "Maintain current portfolio strategy", "维持当前投资组合策略"
        
        # Sort by priority (highest first)
        sorted_recs = sorted(strategic_recs, key=lambda x: x.get('priority', 0), reverse=True)
        top_rec = sorted_recs[0]
        
        # Extract action text
        objective_en = top_rec.get('action', 'Maintain strategy')
        objective_cn = top_rec.get('action_cn', 'Maintain strategy')
        
        # If no portfolio state, return generic objective
        if not allocation_gaps:
            return objective_en, objective_cn
        
        # Phase 1B: Contextualize with portfolio gaps
        # Find the largest gap to focus objective
        if allocation_gaps:
            largest_gap = allocation_gaps[0]  # Already sorted by magnitude
            asset_class = largest_gap['asset_class']
            status = largest_gap['status']
            current_pct = largest_gap['current_pct']
            target_pct = largest_gap['target_pct']
            gap_amount = largest_gap['gap_amount']
            
            # Format gap amount in millions or thousands
            if abs(gap_amount) >= 1000000:
                amount_str = f"¥{abs(gap_amount)/1000000:.1f}M"
            elif abs(gap_amount) >= 10000:
                amount_str = f"¥{abs(gap_amount)/10000:.0f}万"
            else:
                amount_str = f"¥{abs(gap_amount):.0f}"
            
            # Contextualize based on status
            if status == 'aligned':
                objective_en = f"Maintain {asset_class} allocation - currently aligned at {current_pct:.1%}"
                objective_cn = f"Maintain {asset_class} allocation - currently aligned at {current_pct:.1%}"
            elif status == 'reduce':
                pct_change = abs(current_pct - target_pct)
                objective_en = f"Reduce {asset_class} by {pct_change:.1%} ({amount_str}) from {current_pct:.1%} to {target_pct:.1%}"
                objective_cn = f"Reduce {asset_class} by {pct_change:.1%} ({amount_str}) from {current_pct:.1%} to {target_pct:.1%}"
            else:  # increase
                pct_change = abs(current_pct - target_pct)
                objective_en = f"Increase {asset_class} by {pct_change:.1%} ({amount_str}) from {current_pct:.1%} to {target_pct:.1%}"
                objective_cn = f"Increase {asset_class} by {pct_change:.1%} ({amount_str}) from {current_pct:.1%} to {target_pct:.1%}"
        
        return objective_en, objective_cn
    
    def _build_action_steps(
        self,
        strategic_recs: List[Dict],
        allocation_gaps: Optional[List[Dict]] = None,
        portfolio_state: Optional[Dict] = None,  # Phase 1B: Added for regional calculations
        max_steps: int = 5
    ) -> List[Dict[str, str]]:
        """
        Build ordered list of action steps with portfolio-aware details.
        
        Args:
            strategic_recs: List of strategic recommendation dicts
            allocation_gaps: Optional list of gap dicts from _calculate_allocation_gaps()
            max_steps: Maximum number of steps to include (default 5)
        
        Returns:
            List of action step dicts with structure:
            [
                {
                    'action': 'English action text',
                    'action_cn': 'Chinese action text',
                    'rationale': 'English rationale',
                    'rationale_cn': 'Chinese rationale',
                    'priority': 100,
                    'gap_amount': -1200000,  # Phase 1B: Added
                    'status': 'reduce',      # Phase 1B: Added
                    'alignment': 'warning'   # Phase 1B: Added
                },
                ...
            ]
        
        Logic:
            1. Sort by priority
            2. Take top max_steps recommendations
            3. Match with allocation gaps and enrich with context
        """
        if not strategic_recs:
            return []
        
        # Sort by priority (highest first)
        sorted_recs = sorted(strategic_recs, key=lambda x: x.get('priority', 0), reverse=True)
        
        # Take top N and format
        action_steps = []
        for rec in sorted_recs[:max_steps]:
            step = {
                'action': rec.get('action', ''),
                'action_cn': rec.get('action_cn', ''),
                'rationale': rec.get('rationale', ''),
                'rationale_cn': rec.get('rationale_cn', ''),
                'priority': rec.get('priority', 0)
            }
            
            # Phase 1B: Enrich with portfolio gap details if available
            if allocation_gaps:
                # Try to match this action with a gap
                matching_gap = self._find_matching_gap(step, allocation_gaps, portfolio_state)
                if matching_gap:
                    step['gap_amount'] = matching_gap['gap_amount']
                    step['status'] = matching_gap['status']
                    step['alignment'] = matching_gap['alignment']
                    step['current_pct'] = matching_gap['current_pct']
                    step['target_pct'] = matching_gap['target_pct']
                    
                    # Enhance rationale with specific numbers
                    if matching_gap['status'] != 'aligned':
                        # Check if this is a regional rotation gap (special display)
                        if matching_gap.get('is_regional_rotation'):
                            regional_detail = matching_gap.get('regional_detail', {})
                            cn_data = regional_detail.get('cn', {})
                            us_data = regional_detail.get('us', {})
                            rotation_dir = matching_gap.get('rotation_direction')
                            
                            # Format CN details
                            cn_current = f"{cn_data.get('current', 0):.1f}%"
                            cn_target = f"{cn_data.get('target', 0):.1f}%"
                            cn_gap_val = cn_data.get('gap', 0)
                            cn_status = 'Overweight' if cn_gap_val > 0 else 'Underweight'
                            
                            # Format US details for context
                            us_current = f"{us_data.get('current', 0):.1f}%"
                            us_target = f"{us_data.get('target', 0):.1f}%"
                            us_gap_val = us_data.get('gap', 0)
                            us_status = 'Overweight' if us_gap_val > 0 else 'Underweight'
                            
                            # Format gap amount
                            if abs(matching_gap['gap_amount']) >= 1000000:
                                amount_str = f"¥{abs(matching_gap['gap_amount'])/1000000:.1f}M"
                            elif abs(matching_gap['gap_amount']) >= 10000:
                                amount_str = f"¥{abs(matching_gap['gap_amount'])/10000:.0f}万"
                            else:
                                amount_str = f"¥{abs(matching_gap['gap_amount']):.0f}"
                            
                            # Show regional breakdown with rotation direction
                            if rotation_dir:
                                step['rationale'] += f" (CN: {cn_current}→{cn_target} {cn_status}, US: {us_current}→{us_target} {us_status}, Rotation: {rotation_dir})"
                                step['rationale_cn'] += f" (CN: {cn_current}→{cn_target} {cn_status}, US: {us_current}→{us_target} {us_status}, Rotation: {rotation_dir})"
                            else:
                                # No rotation possible (both over or both under)
                                step['rationale'] += f" (CN: {cn_current}→{cn_target} {cn_status}, US: {us_current}→{us_target} {us_status})"
                                step['rationale_cn'] += f" (CN: {cn_current}→{cn_target} {cn_status}, US: {us_current}→{us_target} {us_status})"
                        else:
                            # Standard gap display for non-regional actions
                            pct_str = f"{abs(matching_gap['gap_pct']):.1%}"
                            current_str = f"{matching_gap['current_pct']:.1%}"
                            target_str = f"{matching_gap['target_pct']:.1%}"
                            if abs(matching_gap['gap_amount']) >= 1000000:
                                amount_str = f"¥{abs(matching_gap['gap_amount'])/1000000:.1f}M"
                            elif abs(matching_gap['gap_amount']) >= 10000:
                                amount_str = f"¥{abs(matching_gap['gap_amount'])/10000:.0f}万"
                            else:
                                amount_str = f"¥{abs(matching_gap['gap_amount']):.0f}"
                            
                            step['rationale'] += f" (Current: {current_str}, Target: {target_str}, Gap: {pct_str} / {amount_str})"
                            step['rationale_cn'] += f" (Current: {current_str}, Target: {target_str}, Gap: {pct_str} / {amount_str})"
            
            action_steps.append(step)
        
        return action_steps
    
    def _find_matching_gap(self, action_step: Dict, allocation_gaps: List[Dict], 
                          portfolio_state: Optional[Dict] = None) -> Optional[Dict]:
        """
        Find allocation gap that matches this action step.
        
        Args:
            action_step: Action dict with 'action' and 'action_cn' text
            allocation_gaps: List of gap dicts
            portfolio_state: Optional portfolio state for sub-category calculations
        
        Returns:
            Matching gap dict or None (can be synthesized for regional rotations)
        
        Logic:
            - Match by asset class keywords (股票, 债券, etc.)
            - For regional rotations (CN vs US), synthesize a custom gap
        """
        action_text = (action_step.get('action', '') + ' ' + action_step.get('action_cn', '')).lower()
        
        self.logger.debug(f"🔍 Matching action: {action_step.get('action_cn', '')[:60]}")
        
        # Check for regional rotation patterns
        # Pattern 1: Explicit rotation language "Rotate from US to CN" or "Rotate to undervalued Chinese assets"
        # Pattern 2: Chinese equity specific actions "Increase Chinese equity" or "Adjust Chinese equity allocation"
        is_explicit_rotation = ('rotate' in action_text or 'rotate' in action_text) and \
                               (('china' in action_text or 'china' in action_text or 'cn' in action_text) and \
                                ('us' in action_text or 'us' in action_text or 'us stock' in action_text))
        
        is_chinese_equity_action = ('chinese equity' in action_text or 'chinese equity' in action_text or \
                                   ('china' in action_text and 'equity' in action_text)) and \
                                   ('60%' in action_text or 'equity portfolio' in action_text)
        
        self.logger.debug(f"  Pattern check: explicit_rotation={is_explicit_rotation}, cn_equity={is_chinese_equity_action}")
        
        if is_explicit_rotation or is_chinese_equity_action:
            self.logger.info(f"✅ Detected regional/CN-specific action: {action_step.get('action_cn', '')[:60]}")
            if portfolio_state:
                # This is a regional rotation or CN-specific recommendation
                # Calculate the gap for Chinese equity specifically
                return self._calculate_regional_rotation_gap(portfolio_state)
            else:
                self.logger.warning(f"❌ Regional action detected but no portfolio_state available: {action_step.get('action_cn', '')[:50]}")
        
        # Standard asset class matching
        asset_keywords = {
            'Equity': ['equity', 'equit', 'stock', 'equity'],
            'Fixed Income': ['fixed income', 'bond', 'fixed income', 'bond'],
            'Cash': ['cash'],
            'Commodities': ['commodity', 'commodities'],
            'Gold': ['gold'],
            'Crypto': ['crypto', 'bitcoin', 'btc', 'cryptocurrency']
        }
        
        for gap in allocation_gaps:
            asset_class = gap['asset_class']
            keywords = asset_keywords.get(asset_class, [asset_class.lower()])
            
            # Check if any keyword matches
            if any(kw in action_text for kw in keywords):
                return gap
        
        return None
    
    def _calculate_regional_rotation_gap(self, portfolio_state: Dict) -> Optional[Dict]:
        """
        Calculate gap for US→CN equity rotation recommendations.
        
        Args:
            portfolio_state: Portfolio state with sub_level_table containing sub-category data
        
        Returns:
            Synthesized gap dict showing CN vs US equity gaps:
            {
                'asset_class': '股票',
                'asset_class_en': 'Equity',
                'current_pct': <total equity %>,
                'target_pct': <target equity %>,
                'gap_pct': <equity gap>,
                'gap_amount': <equity gap amount>,
                'status': 'reduce' or 'increase',
                'alignment': 'danger' or 'warning',
                'regional_detail': {
                    'cn': {'current': %, 'target': %, 'gap': %},
                    'us': {'current': %, 'target': %, 'gap': %}
                }
            }
        
        Logic:
            - Extract CN and US equity sub-categories from sub_level_table
            - Compare current vs target for both regions
            - Return overall equity gap with regional breakdown
        """
        try:
            sub_level_table = portfolio_state.get('sub_level_table', [])
            if not sub_level_table:
                self.logger.debug("No sub_level_table data for regional rotation calculation")
                return None
            
            # Find and aggregate CN and US equity sub-categories
            cn_items = []
            us_items = []
            
            for item in sub_level_table:
                sub_cat = item.get('sub_category', '').lower()
                asset_class = item.get('asset_class', '')
                
                if asset_class != '股票':
                    continue
                
                # Match CN equity (Domestic, China)
                if any(kw in sub_cat for kw in ['domestic', 'china', 'cn']):
                    cn_items.append(item)
                
                # Match US equity (US, America, RSU)
                elif any(kw in sub_cat for kw in ['us', 'america', 'rsu']):
                    us_items.append(item)
            
            if not cn_items and not us_items:
                self.logger.debug("CN/US equity data not found in sub_level_table")
                return None
            
            # Aggregate CN equity data
            regional_detail = {}
            
            if cn_items:
                cn_current_pct = sum(item.get('current_pct', 0) for item in cn_items)
                cn_target_pct = sum(item.get('target_pct', 0) for item in cn_items)
                cn_current_value = sum(item.get('current_value', 0) for item in cn_items)
                cn_target_value = sum(item.get('target_value', 0) for item in cn_items)
                
                regional_detail['cn'] = {
                    'current': cn_current_pct,
                    'target': cn_target_pct,
                    'gap': cn_current_pct - cn_target_pct,
                    'current_value': cn_current_value,
                    'target_value': cn_target_value
                }
                self.logger.debug(f"Aggregated {len(cn_items)} CN equity sub-categories: {[item.get('sub_category') for item in cn_items]}")
            
            # Aggregate US equity data
            if us_items:
                us_current_pct = sum(item.get('current_pct', 0) for item in us_items)
                us_target_pct = sum(item.get('target_pct', 0) for item in us_items)
                us_current_value = sum(item.get('current_value', 0) for item in us_items)
                us_target_value = sum(item.get('target_value', 0) for item in us_items)
                
                regional_detail['us'] = {
                    'current': us_current_pct,
                    'target': us_target_pct,
                    'gap': us_current_pct - us_target_pct,
                    'current_value': us_current_value,
                    'target_value': us_target_value
                }
                self.logger.debug(f"Aggregated {len(us_items)} US equity sub-categories: {[item.get('sub_category') for item in us_items]}")
            
            # Calculate rotation direction based on gap signs
            rotation_direction = None
            
            if regional_detail.get('cn') and regional_detail.get('us'):
                cn_gap = regional_detail['cn']['gap']  # drift = current - target
                us_gap = regional_detail['us']['gap']
                
                # Rotation scenario: US overweight (positive gap), CN underweight (negative gap)
                if us_gap > 0 and cn_gap < 0:
                    # Rotate from US to CN
                    rotation_amount = min(abs(cn_gap), abs(us_gap)) * portfolio_state.get('rebalanceable_value', 0) / 100
                    rotation_direction = 'US→CN'
                    self.logger.debug(f"Regional rotation US→CN: US gap={us_gap:.2f}%, CN gap={cn_gap:.2f}%, amount=¥{rotation_amount:,.0f}")
                elif cn_gap > 0 and us_gap < 0:
                    # Rotate from CN to US (less common)
                    rotation_amount = min(abs(cn_gap), abs(us_gap)) * portfolio_state.get('rebalanceable_value', 0) / 100
                    rotation_direction = 'CN→US'
                    self.logger.debug(f"Regional rotation CN→US: CN gap={cn_gap:.2f}%, US gap={us_gap:.2f}%, amount=¥{rotation_amount:,.0f}")
                else:
                    # Both regions overweight or both underweight - no clear rotation
                    self.logger.debug(f"No clear rotation: CN gap={cn_gap:.2f}%, US gap={us_gap:.2f}% (both same direction)")

            
            # Return synthesized gap for equity with regional detail
            # For display purposes, show CN-specific data (primary region in rotation)
            cn_data = regional_detail.get('cn', {})
            cn_gap_amount = abs(cn_data.get('gap', 0) * portfolio_state.get('rebalanceable_value', 0) / 100)
            
            return {
                'asset_class': '股票',
                'asset_class_en': 'Equity',
                'current_pct': cn_data.get('current', 0) / 100,  # CN current % for display
                'target_pct': cn_data.get('target', 0) / 100,    # CN target % for display
                'gap_pct': cn_data.get('gap', 0) / 100,          # CN gap % for display
                'gap_amount': cn_gap_amount,                     # CN gap amount for display
                'status': 'reduce' if cn_data.get('gap', 0) > 0 else 'increase',
                'alignment': 'warning',
                'regional_detail': regional_detail,              # Full CN/US details preserved
                'rotation_direction': rotation_direction,
                'is_regional_rotation': True                     # Flag for special display logic
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating regional rotation gap: {e}")
            return None
    
    def _format_allocation_changes(self, dynamic_targets: Dict) -> List[Dict[str, str]]:
        """
        Format allocation changes with directional arrows for display.
        
        Args:
            dynamic_targets: Dict containing:
                - top_level: Dict of {asset_class: target_pct}
                - sub_category: Optional nested dict for sub-allocations
        
        Returns:
            List of allocation change dicts:
            [
                {
                    'asset_class': '股票',
                    'asset_class_en': 'Equity',
                    'change': '↓ -20%',
                    'new_target': '55%',
                    'description': 'Reduce from 75% to 55%',
                    'description_cn': '从75%降至55%'
                },
                ...
            ]
        
        Logic:
            1. Compare dynamic targets with baseline (from asset_taxonomy.yaml 成长型)
            2. Calculate deltas
            3. Format with arrows (↑ increase, ↓ decrease, → maintain)
            4. Focus on significant changes (>5%)
        """
        if not dynamic_targets:
            return []
        
        top_level = dynamic_targets.get('top_level', {})
        if not top_level:
            return []
        
        # Baseline targets from 成长型 profile (hardcoded for Phase 1, could load from config later)
        baseline_targets = {
            'Equity': 0.75,
            'Fixed Income': 0.10,
            'Commodities': 0.05,
            'Alternative': 0.05,
            'Cash': 0.05,
            'Real Estate': 0.00,
            'Insurance': 0.00
        }
        
        # Asset class name mapping
        asset_class_en_map = {
            'Equity': 'Equity',
            'Fixed Income': 'Fixed Income',
            'Commodities': 'Commodities',
            'Alternative': 'Alternatives',
            'Cash': 'Cash',
            'Real Estate': 'Real Estate',
            'Insurance': 'Insurance'
        }
        
        allocation_changes = []
        
        for asset_class, new_target in top_level.items():
            baseline = baseline_targets.get(asset_class, 0)
            delta = new_target - baseline
            
            # Only include significant changes (>5% or if baseline is 0)
            if abs(delta) >= 0.05 or (baseline == 0 and new_target > 0):
                # Determine arrow and change text
                if delta > 0:
                    arrow = '↑'
                    change_text = f'+{delta*100:.0f}%'
                elif delta < 0:
                    arrow = '↓'
                    change_text = f'{delta*100:.0f}%'
                else:
                    arrow = '→'
                    change_text = '0%'
                
                change = {
                    'asset_class': asset_class,
                    'asset_class_en': asset_class_en_map.get(asset_class, asset_class),
                    'change': f'{arrow} {change_text}',
                    'new_target': f'{new_target*100:.0f}%',
                    'baseline': f'{baseline*100:.0f}%',
                    'description': f'Adjust from {baseline*100:.0f}% to {new_target*100:.0f}%',
                    'description_cn': f'Adjust from {baseline*100:.0f}% to {new_target*100:.0f}%'
                }
                allocation_changes.append(change)
        
        # Sort by magnitude of change (largest first)
        allocation_changes.sort(key=lambda x: abs(float(x['change'].split()[1].rstrip('%'))), reverse=True)
        
        return allocation_changes
    
    def _determine_risk_level(self, regime_name: str) -> str:
        """
        Determine overall risk level from regime name.
        
        Args:
            regime_name: Name of market regime
        
        Returns:
            Risk level: 'HIGH', 'MEDIUM', or 'LOW'
        
        Logic:
            - "Maximum Defense" → HIGH risk environment (need defense)
            - "Cautious Rotation" → MEDIUM risk (balanced approach)
            - "Maximum Offense" / "Benchmark Cruising" → LOW risk (opportunity zone)
        """
        regime_lower = regime_name.lower()
        
        if 'defense' in regime_lower or 'defensive' in regime_lower:
            return 'HIGH'
        elif 'cautious' in regime_lower or 'rotation' in regime_lower:
            return 'MEDIUM'
        elif 'offense' in regime_lower or 'cruising' in regime_lower or 'opportunity' in regime_lower:
            return 'LOW'
        else:
            return 'MEDIUM'
    
    def _calculate_confidence(self, market_regime: Dict) -> int:
        """
        Calculate confidence score based on indicator matches.
        
        Args:
            market_regime: Market regime dict with 'indicators' key
        
        Returns:
            Confidence score 0-100
        
        Logic:
            - Full match (all indicators): 100
            - Partial match: Scale based on percentage of indicators matched
            - No indicator data: Default to 80 (assume regime detection is correct)
        """
        indicators = market_regime.get('indicators', {})
        if not indicators:
            # No indicator data available, assume decent confidence
            return 80
        
        # Count how many indicators have values
        total_indicators = len(indicators)
        matched_indicators = sum(1 for v in indicators.values() if v is not None)
        
        if total_indicators == 0:
            return 80
        
        # Calculate percentage and scale to 0-100
        confidence = int((matched_indicators / total_indicators) * 100)
        return max(50, confidence)  # Floor at 50%
    
    def to_dict(self, directive: StrategicDirective) -> Dict:
        """
        Convert StrategicDirective to dictionary for serialization.
        
        Args:
            directive: StrategicDirective object
        
        Returns:
            Dictionary representation
        """
        if not directive:
            return {}
        
        return {
            'regime_name': directive.regime_name,
            'regime_name_cn': directive.regime_name_cn,
            'regime_description': directive.regime_description,
            'regime_description_cn': directive.regime_description_cn,
            'core_objective': directive.core_objective,
            'core_objective_cn': directive.core_objective_cn,
            'action_steps': directive.action_steps,
            'allocation_changes': directive.allocation_changes,
            'allocation_gaps': directive.allocation_gaps,  # Phase 1B: Add portfolio gaps
            'risk_level': directive.risk_level,
            'confidence': directive.confidence
        }
