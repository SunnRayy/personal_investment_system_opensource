"""
Tax-Aware Investment Advisor

This module provides tax-aware rebalancing recommendations by analyzing
cost basis, unrealized gains/losses, and tax implications of investment decisions.
"""

import logging
from typing import Dict, List, Any, Optional, NamedTuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd

# Use try/except for imports to handle different execution contexts
try:
    from ..financial_analysis.cost_basis import CostBasisCalculator
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from financial_analysis.cost_basis import CostBasisCalculator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LotAnalysis(NamedTuple):
    """Analysis of a specific purchase lot for tax purposes"""
    lot_date: datetime
    quantity: float
    cost_basis: float
    current_value: float
    unrealized_pnl: float
    is_short_term: bool
    is_long_term: bool
    tax_character: str


@dataclass
class TaxRecommendation:
    """Tax-aware investment recommendation"""
    recommendation_type: str
    asset_id: str
    action: str
    specific_lot_date: Optional[datetime] = None
    quantity: Optional[float] = None
    estimated_tax_impact: Optional[float] = None
    message: str = ""
    priority: str = "medium"
    rationale: str = ""


class TaxAdvisor:
    """
    Provides tax-aware investment recommendations based on cost basis analysis
    and rebalancing suggestions.
    """
    
    def __init__(self, short_term_tax_rate: float = 0.37, long_term_tax_rate: float = 0.20):
        """Initialize the tax advisor."""
        self.short_term_tax_rate = short_term_tax_rate
        self.long_term_tax_rate = long_term_tax_rate
        self.short_term_threshold = 365
        logger.info(f"TaxAdvisor initialized with rates: ST={short_term_tax_rate:.1%}, LT={long_term_tax_rate:.1%}")
    
    def analyze_tax_implications(self,
                               cost_basis_calculators: Dict[str, CostBasisCalculator],
                               current_prices: Dict[str, float],
                               rebalancing_actions: Optional[Dict[str, float]] = None,
                               analysis_date: Optional[datetime] = None) -> List[TaxRecommendation]:
        """Analyze tax implications and generate tax-aware recommendations."""
        if analysis_date is None:
            analysis_date = datetime.now()
        
        recommendations = []
        logger.info(f"Analyzing tax implications for {len(cost_basis_calculators)} assets")
        
        for asset_id, calculator in cost_basis_calculators.items():
            if asset_id not in current_prices:
                logger.warning(f"No current price available for {asset_id}, skipping tax analysis")
                continue
            
            current_price = current_prices[asset_id]
            lot_analyses = self._analyze_lots(calculator, current_price, analysis_date)
            
            if not lot_analyses:
                continue
            
            asset_recommendations = self._generate_asset_recommendations(
                asset_id, lot_analyses, rebalancing_actions
            )
            recommendations.extend(asset_recommendations)
        
        recommendations = self._prioritize_recommendations(recommendations)
        logger.info(f"Generated {len(recommendations)} tax-aware recommendations")
        return recommendations
    
    def _analyze_lots(self, calculator, current_price, analysis_date):
        """Analyze individual purchase lots for tax implications."""
        lot_analyses = []
        
        for lot in calculator.lots:
            if lot.is_empty():
                continue
            
            holding_days = (analysis_date.date() - lot.purchase_date.date()).days
            is_long_term = holding_days >= self.short_term_threshold
            is_short_term = not is_long_term
            
            current_value = lot.remaining_quantity * current_price
            unrealized_pnl = current_value - lot.get_remaining_value()
            
            if unrealized_pnl > 0:
                tax_character = 'long_term_gain' if is_long_term else 'short_term_gain'
            else:
                tax_character = 'long_term_loss' if is_long_term else 'short_term_loss'
            
            lot_analysis = LotAnalysis(
                lot_date=lot.purchase_date,
                quantity=lot.remaining_quantity,
                cost_basis=lot.get_remaining_value(),
                current_value=current_value,
                unrealized_pnl=unrealized_pnl,
                is_short_term=is_short_term,
                is_long_term=is_long_term,
                tax_character=tax_character
            )
            lot_analyses.append(lot_analysis)
        
        return lot_analyses
    
    def _generate_asset_recommendations(self, asset_id, lot_analyses, rebalancing_actions):
        """Generate tax recommendations for a specific asset."""
        recommendations = []
        suggested_action = rebalancing_actions.get(asset_id, 0.0) if rebalancing_actions else 0.0
        
        loss_lots = [lot for lot in lot_analyses if lot.unrealized_pnl < 0]
        gain_lots = [lot for lot in lot_analyses if lot.unrealized_pnl > 0]
        short_term_gains = [lot for lot in gain_lots if lot.is_short_term]
        long_term_gains = [lot for lot in gain_lots if lot.is_long_term]
        
        # Tax loss harvesting opportunities
        if loss_lots:
            loss_lots.sort(key=lambda x: x.unrealized_pnl)
            
            for lot in loss_lots:
                tax_savings = abs(lot.unrealized_pnl) * (
                    self.long_term_tax_rate if lot.is_long_term else self.short_term_tax_rate
                )
                
                recommendation = TaxRecommendation(
                    recommendation_type='tax_loss_harvest',
                    asset_id=asset_id,
                    action='sell',
                    specific_lot_date=lot.lot_date,
                    quantity=lot.quantity,
                    estimated_tax_impact=-tax_savings,
                    message=f"Consider selling the lot of {asset_id} purchased on {lot.lot_date.strftime('%Y-%m-%d')} to harvest a loss of ${abs(lot.unrealized_pnl):,.2f}",
                    priority='high' if abs(lot.unrealized_pnl) > 5000 else 'medium',
                    rationale=f"Tax loss harvesting opportunity: ${tax_savings:,.2f} in tax savings"
                )
                recommendations.append(recommendation)
        
        # Warning for short-term gains
        if suggested_action < 0 and short_term_gains:
            total_short_term_gain = sum(lot.unrealized_pnl for lot in short_term_gains)
            estimated_tax = total_short_term_gain * self.short_term_tax_rate
            
            recommendation = TaxRecommendation(
                recommendation_type='warning',
                asset_id=asset_id,
                action='hold',
                estimated_tax_impact=estimated_tax,
                message=f"Warning: Selling {asset_id} now will realize a short-term gain of ${total_short_term_gain:,.2f}",
                priority='high' if estimated_tax > 1000 else 'medium',
                rationale=f"Consider waiting for long-term treatment"
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def _prioritize_recommendations(self, recommendations):
        """Prioritize recommendations based on tax impact and priority level."""
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        
        recommendations.sort(
            key=lambda x: (
                priority_order.get(x.priority, 0),
                -(x.estimated_tax_impact or 0) if x.estimated_tax_impact else 0
            ),
            reverse=True
        )
        return recommendations
    
    def generate_tax_summary(self, cost_basis_calculators, current_prices):
        """Generate a comprehensive tax summary for the portfolio."""
        summary = {
            'total_unrealized_gains': 0.0,
            'total_unrealized_losses': 0.0,
            'net_unrealized_pnl': 0.0,
            'short_term_gains': 0.0,
            'long_term_gains': 0.0,
            'potential_tax_liability': 0.0,
            'tax_efficiency_ratio': 0.0
        }
        return summary
