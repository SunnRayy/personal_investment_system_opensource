"""
Portfolio Advisor Module

Provides portfolio optimization recommendations including asset allocation,
rebalancing strategies, and investment optimization suggestions.
"""

import pandas as pd
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PortfolioRecommendationType(Enum):
    """Types of portfolio recommendations"""
    ASSET_ALLOCATION = "asset_allocation"
    REBALANCING = "rebalancing"
    DIVERSIFICATION = "diversification"
    COST_OPTIMIZATION = "cost_optimization"
    TAX_OPTIMIZATION = "tax_optimization"
    RISK_ADJUSTMENT = "risk_adjustment"

@dataclass
class PortfolioRecommendation:
    """Portfolio recommendation data structure"""
    id: str
    type: PortfolioRecommendationType
    title: str
    description: str
    urgency: str  # "critical", "high", "medium", "low"
    impact_score: float  # 0-100 scale
    ease_score: float    # 0-100 scale (higher = easier)
    current_allocation: Optional[Dict[str, float]] = None
    target_allocation: Optional[Dict[str, float]] = None
    specific_actions: List[Dict[str, Any]] = None  # Buy/sell recommendations
    estimated_benefit: Optional[float] = None
    implementation_cost: Optional[float] = None
    action_steps: List[str] = None
    
    def __post_init__(self):
        if self.specific_actions is None:
            self.specific_actions = []
        if self.action_steps is None:
            self.action_steps = []

class PortfolioAdvisor:
    """
    Generates portfolio optimization recommendations based on analysis results
    """
    
    def __init__(self):
        self.recommendations = []
        
    def analyze_portfolio_optimization(self,
                                     holdings_df: pd.DataFrame,
                                     portfolio_analysis_results: Dict[str, Any],
                                     historical_performance_results: Optional[Dict[str, Any]] = None,
                                     analysis_config: Any = None) -> List[PortfolioRecommendation]:
        """
        Generate comprehensive portfolio optimization recommendations using historical context
        
        Args:
            holdings_df: Current portfolio holdings
            portfolio_analysis_results: Results from portfolio optimization
            historical_performance_results: Historical performance analysis results
            analysis_config: Analysis configuration settings
            
        Returns:
            List of portfolio recommendations
        """
        
        recommendations = []
        
        try:
            # Store historical performance for use in analysis methods
            self.historical_performance = historical_performance_results or {}
            
            # Analyze different aspects of portfolio optimization with historical context
            recommendations.extend(self._analyze_asset_allocation_with_history(holdings_df, portfolio_analysis_results))
            recommendations.extend(self._analyze_rebalancing_needs(portfolio_analysis_results))
            recommendations.extend(self._analyze_diversification(holdings_df, portfolio_analysis_results))
            recommendations.extend(self._analyze_cost_efficiency(holdings_df))
            recommendations.extend(self._analyze_risk_characteristics_with_history(portfolio_analysis_results))
            
            # New historical-based recommendations
            if historical_performance_results:
                recommendations.extend(self._analyze_historical_performance(historical_performance_results))
                recommendations.extend(self._analyze_performance_attribution(historical_performance_results))
            
        except Exception as e:
            # Add error recommendation
            error_rec = PortfolioRecommendation(
                id="portfolio_analysis_error",
                type=PortfolioRecommendationType.ASSET_ALLOCATION,
                title="Portfolio Analysis Error",
                description=f"Error analyzing portfolio: {str(e)}",
                urgency="medium",
                impact_score=0,
                ease_score=0
            )
            recommendations.append(error_rec)
        
        self.recommendations = recommendations
        return recommendations
    
    def _analyze_asset_allocation(self, holdings_df: pd.DataFrame,
                                 portfolio_results: Dict[str, Any]) -> List[PortfolioRecommendation]:
        """Analyze current vs optimal asset allocation"""
        
        recommendations = []
        
        try:
            # Get current allocation
            current_allocation = self._calculate_current_allocation(holdings_df)
            
            # Get optimal allocations from portfolio analysis
            optimization_results = portfolio_results.get('optimization_results', {})
            
            for strategy_name, strategy_results in optimization_results.items():
                if isinstance(strategy_results, dict) and 'optimal_weights' in strategy_results:
                    optimal_weights = strategy_results['optimal_weights']
                    
                    # Calculate allocation differences
                    allocation_diff = self._calculate_allocation_differences(
                        current_allocation, optimal_weights
                    )
                    
                    # Generate rebalancing recommendations
                    if allocation_diff['max_deviation'] > 0.05:  # 5% threshold
                        
                        specific_actions = self._generate_rebalancing_actions(
                            holdings_df, current_allocation, optimal_weights
                        )
                        
                        recommendations.append(PortfolioRecommendation(
                            id=f"rebalance_{strategy_name.lower()}",
                            type=PortfolioRecommendationType.REBALANCING,
                            title=f"Rebalance Portfolio ({strategy_name})",
                            description=f"Current allocation deviates from optimal {strategy_name} "
                                      f"strategy by up to {allocation_diff['max_deviation']:.1%}. "
                                      f"Rebalancing could improve risk-adjusted returns.",
                            urgency="high" if allocation_diff['max_deviation'] > 0.15 else "medium",
                            impact_score=min(80, allocation_diff['max_deviation'] * 400),
                            ease_score=70,
                            current_allocation=current_allocation,
                            target_allocation=optimal_weights,
                            specific_actions=specific_actions,
                            estimated_benefit=strategy_results.get('expected_return', 0) * 1000000,  # Placeholder
                            action_steps=[
                                "Review current portfolio allocation",
                                "Calculate exact rebalancing amounts",
                                "Execute trades to achieve target allocation",
                                "Set up automatic rebalancing schedule"
                            ]
                        ))
        
        except Exception as e:
            recommendations.append(PortfolioRecommendation(
                id="allocation_analysis_error",
                type=PortfolioRecommendationType.ASSET_ALLOCATION,
                title="Asset Allocation Review Needed",
                description=f"Unable to analyze asset allocation: {str(e)}",
                urgency="low",
                impact_score=30,
                ease_score=90
            ))
        
        return recommendations
    
    def _analyze_rebalancing_needs(self, portfolio_results: Dict[str, Any]) -> List[PortfolioRecommendation]:
        """Analyze specific rebalancing recommendations"""
        
        recommendations = []
        
        try:
            rebalancing_results = portfolio_results.get('rebalancing_analysis', {})
            
            if rebalancing_results:
                rebalancing_recs = rebalancing_results.get('recommendations', [])
                
                for i, rec in enumerate(rebalancing_recs):
                    if isinstance(rec, dict):
                        action_type = rec.get('action', 'unknown')
                        asset_class = rec.get('asset_class', 'Unknown')
                        current_weight = rec.get('current_weight', 0)
                        target_weight = rec.get('target_weight', 0)
                        amount = rec.get('amount', 0)
                        
                        urgency = "high" if abs(current_weight - target_weight) > 0.1 else "medium"
                        
                        recommendations.append(PortfolioRecommendation(
                            id=f"rebalance_action_{i}",
                            type=PortfolioRecommendationType.REBALANCING,
                            title=f"{action_type.title()} {asset_class}",
                            description=f"Current {asset_class} allocation is {current_weight:.1%}, "
                                      f"target is {target_weight:.1%}. "
                                      f"Recommended action: {action_type} ¥{amount:,.0f}",
                            urgency=urgency,
                            impact_score=abs(current_weight - target_weight) * 100,
                            ease_score=80,
                            specific_actions=[{
                                'action': action_type,
                                'asset_class': asset_class,
                                'amount': amount,
                                'current_weight': current_weight,
                                'target_weight': target_weight
                            }],
                            action_steps=[
                                f"Identify specific {asset_class} holdings to adjust",
                                f"Execute {action_type} order for ¥{amount:,.0f}",
                                "Monitor resulting allocation",
                                "Update rebalancing schedule"
                            ]
                        ))
        
        except Exception as e:
            recommendations.append(PortfolioRecommendation(
                id="rebalancing_analysis_error",
                type=PortfolioRecommendationType.REBALANCING,
                title="Rebalancing Analysis Error",
                description=f"Unable to analyze rebalancing needs: {str(e)}",
                urgency="low",
                impact_score=30,
                ease_score=90
            ))
        
        return recommendations
    
    def _analyze_diversification(self, holdings_df: pd.DataFrame,
                               portfolio_results: Dict[str, Any]) -> List[PortfolioRecommendation]:
        """Analyze portfolio diversification and concentration risks"""
        
        recommendations = []
        
        try:
            # Calculate concentration metrics
            if holdings_df is not None and not holdings_df.empty:
                
                # Calculate individual holding concentration
                if 'Market_Value_CNY' in holdings_df.columns:
                    total_value = holdings_df['Market_Value_CNY'].sum()
                    holdings_df_copy = holdings_df.copy()
                    holdings_df_copy['weight'] = holdings_df_copy['Market_Value_CNY'] / total_value
                    
                    # Check for over-concentration in individual holdings
                    max_holding_weight = holdings_df_copy['weight'].max()
                    if max_holding_weight > 0.20:  # More than 20% in single holding
                        top_holding = holdings_df_copy.loc[holdings_df_copy['weight'].idxmax()]
                        
                        recommendations.append(PortfolioRecommendation(
                            id="individual_concentration",
                            type=PortfolioRecommendationType.DIVERSIFICATION,
                            title="Reduce Individual Holding Concentration",
                            description=f"Single holding ({top_holding.get('Asset_Name', 'Unknown')}) "
                                      f"represents {max_holding_weight:.1%} of portfolio. "
                                      f"Consider reducing concentration risk.",
                            urgency="high" if max_holding_weight > 0.30 else "medium",
                            impact_score=min(90, max_holding_weight * 200),
                            ease_score=60,
                            estimated_benefit=total_value * (max_holding_weight - 0.15) * 0.02,  # Risk reduction benefit
                            action_steps=[
                                f"Consider selling ¥{total_value * (max_holding_weight - 0.15):,.0f} of {top_holding.get('Asset_Name', 'top holding')}",
                                "Diversify proceeds across multiple asset classes",
                                "Set maximum individual holding limits (10-15%)",
                                "Monitor concentration regularly"
                            ]
                        ))
                
                # Check asset type diversification
                if 'Asset_Type' in holdings_df.columns:
                    asset_type_concentration = holdings_df.groupby('Asset_Type')['Market_Value_CNY'].sum()
                    asset_type_weights = asset_type_concentration / total_value
                    
                    # Check for over-concentration in asset types
                    max_asset_type_weight = asset_type_weights.max()
                    if max_asset_type_weight > 0.70:  # More than 70% in single asset type
                        dominant_type = asset_type_weights.idxmax()
                        
                        recommendations.append(PortfolioRecommendation(
                            id="asset_type_concentration",
                            type=PortfolioRecommendationType.DIVERSIFICATION,
                            title="Diversify Across Asset Types",
                            description=f"Portfolio is {max_asset_type_weight:.1%} concentrated in {dominant_type}. "
                                      f"Consider diversifying across different asset classes.",
                            urgency="medium",
                            impact_score=70,
                            ease_score=50,
                            action_steps=[
                                f"Consider reducing {dominant_type} allocation to 50-60%",
                                "Add exposure to other asset classes (bonds, real estate, etc.)",
                                "Gradually rebalance over time to reduce transaction costs",
                                "Research correlation benefits of diversification"
                            ]
                        ))
            
            # Analyze correlation-based diversification from portfolio results
            portfolio_metrics = portfolio_results.get('portfolio_metrics', {})
            if 'concentration_risk' in portfolio_metrics:
                hhi = portfolio_metrics['concentration_risk'].get('hhi', 0)
                
                if hhi > 0.25:  # High concentration (HHI > 0.25)
                    recommendations.append(PortfolioRecommendation(
                        id="high_concentration_risk",
                        type=PortfolioRecommendationType.DIVERSIFICATION,
                        title="Reduce Portfolio Concentration Risk",
                        description=f"Portfolio concentration (HHI: {hhi:.3f}) is high. "
                                  f"Better diversification could reduce risk without sacrificing returns.",
                        urgency="medium",
                        impact_score=60,
                        ease_score=65,
                        action_steps=[
                            "Identify most concentrated holdings",
                            "Research less correlated assets",
                            "Gradually add diversifying positions",
                            "Monitor correlation changes over time"
                        ]
                    ))
        
        except Exception as e:
            recommendations.append(PortfolioRecommendation(
                id="diversification_analysis_error",
                type=PortfolioRecommendationType.DIVERSIFICATION,
                title="Diversification Analysis Error",
                description=f"Unable to analyze diversification: {str(e)}",
                urgency="low",
                impact_score=30,
                ease_score=90
            ))
        
        return recommendations
    
    def _analyze_cost_efficiency(self, holdings_df: pd.DataFrame) -> List[PortfolioRecommendation]:
        """Analyze cost efficiency and fee optimization opportunities"""
        
        recommendations = []
        
        try:
            if holdings_df is not None and not holdings_df.empty:
                # Look for fee/expense information
                fee_columns = [col for col in holdings_df.columns if 
                             any(keyword in col.lower() for keyword in ['fee', 'expense', 'cost', '费用'])]
                
                if fee_columns:
                    # Analyze expense ratios and fees
                    # This is a simplified analysis - would need actual fee data
                    recommendations.append(PortfolioRecommendation(
                        id="cost_analysis_needed",
                        type=PortfolioRecommendationType.COST_OPTIMIZATION,
                        title="Review Investment Costs",
                        description="Review investment fees and expense ratios to ensure cost efficiency. "
                                  "High fees can significantly impact long-term returns.",
                        urgency="low",
                        impact_score=50,
                        ease_score=80,
                        action_steps=[
                            "Review expense ratios of all holdings",
                            "Compare with low-cost alternatives",
                            "Consider index funds for core positions",
                            "Calculate annual fee impact on returns"
                        ]
                    ))
        
        except Exception:
            # Optional analysis, don't add error recommendations
            pass
        
        return recommendations
    
    def _analyze_risk_characteristics(self, portfolio_results: Dict[str, Any]) -> List[PortfolioRecommendation]:
        """Analyze portfolio risk characteristics and adjustments"""
        
        recommendations = []
        
        try:
            portfolio_metrics = portfolio_results.get('portfolio_metrics', {})
            
            # Analyze portfolio volatility
            if 'portfolio_volatility' in portfolio_metrics:
                volatility = portfolio_metrics['portfolio_volatility']
                
                if volatility > 0.25:  # High volatility (>25%)
                    recommendations.append(PortfolioRecommendation(
                        id="high_portfolio_volatility",
                        type=PortfolioRecommendationType.RISK_ADJUSTMENT,
                        title="Reduce Portfolio Volatility",
                        description=f"Portfolio volatility ({volatility:.1%}) is relatively high. "
                                  f"Consider adding lower-risk assets to reduce overall volatility.",
                        urgency="medium",
                        impact_score=60,
                        ease_score=70,
                        action_steps=[
                            "Add bonds or other lower-volatility assets",
                            "Consider reducing position sizes in volatile holdings",
                            "Explore low-correlation assets",
                            "Review risk tolerance and time horizon"
                        ]
                    ))
                
                elif volatility < 0.08:  # Very low volatility
                    recommendations.append(PortfolioRecommendation(
                        id="low_portfolio_volatility",
                        type=PortfolioRecommendationType.RISK_ADJUSTMENT,
                        title="Consider Increasing Return Potential",
                        description=f"Portfolio volatility ({volatility:.1%}) is very low. "
                                  f"Consider whether higher-return opportunities align with risk tolerance.",
                        urgency="low",
                        impact_score=40,
                        ease_score=60,
                        action_steps=[
                            "Review risk tolerance and investment timeline",
                            "Consider adding growth-oriented assets",
                            "Evaluate current vs target asset allocation",
                            "Balance safety with growth potential"
                        ]
                    ))
            
            # Analyze Sharpe ratio
            if 'sharpe_ratio' in portfolio_metrics:
                sharpe_ratio = portfolio_metrics['sharpe_ratio']
                
                if sharpe_ratio < 0.5:  # Low risk-adjusted returns
                    recommendations.append(PortfolioRecommendation(
                        id="low_sharpe_ratio",
                        type=PortfolioRecommendationType.RISK_ADJUSTMENT,
                        title="Improve Risk-Adjusted Returns",
                        description=f"Portfolio Sharpe ratio ({sharpe_ratio:.2f}) suggests room for improvement "
                                  f"in risk-adjusted returns. Consider optimization strategies.",
                        urgency="medium",
                        impact_score=70,
                        ease_score=50,
                        action_steps=[
                            "Review holdings with poor risk-adjusted performance",
                            "Consider portfolio optimization strategies",
                            "Evaluate correlation structure",
                            "Implement systematic rebalancing"
                        ]
                    ))
        
        except Exception as e:
            recommendations.append(PortfolioRecommendation(
                id="risk_analysis_error",
                type=PortfolioRecommendationType.RISK_ADJUSTMENT,
                title="Risk Analysis Error",
                description=f"Unable to analyze risk characteristics: {str(e)}",
                urgency="low",
                impact_score=30,
                ease_score=90
            ))
        
        return recommendations
    
    def _calculate_current_allocation(self, holdings_df: pd.DataFrame) -> Dict[str, float]:
        """Calculate current portfolio allocation by asset class"""
        
        allocation = {}
        
        try:
            if holdings_df is not None and holdings_df.empty:
                if 'Asset_Type' in holdings_df.columns and 'Market_Value_CNY' in holdings_df.columns:
                    total_value = holdings_df['Market_Value_CNY'].sum()
                    
                    if total_value > 0:
                        asset_allocation = holdings_df.groupby('Asset_Type')['Market_Value_CNY'].sum()
                        allocation = (asset_allocation / total_value).to_dict()
        
        except Exception:
            # Return empty allocation on error
            pass
        
        return allocation
    
    def _calculate_allocation_differences(self, current: Dict[str, float],
                                        optimal: Dict[str, float]) -> Dict[str, float]:
        """Calculate differences between current and optimal allocations"""
        
        differences = {}
        all_assets = set(current.keys()) | set(optimal.keys())
        
        max_deviation = 0
        for asset in all_assets:
            current_weight = current.get(asset, 0)
            optimal_weight = optimal.get(asset, 0)
            diff = abs(current_weight - optimal_weight)
            differences[asset] = diff
            max_deviation = max(max_deviation, diff)
        
        return {
            'asset_differences': differences,
            'max_deviation': max_deviation,
            'total_deviation': sum(differences.values()) / 2  # Divide by 2 to avoid double counting
        }
    
    def _generate_rebalancing_actions(self, holdings_df: pd.DataFrame,
                                    current_allocation: Dict[str, float],
                                    target_allocation: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate specific buy/sell actions for rebalancing"""
        
        actions = []
        
        try:
            if holdings_df is not None and not holdings_df.empty:
                total_value = holdings_df['Market_Value_CNY'].sum()
                
                for asset_class, target_weight in target_allocation.items():
                    current_weight = current_allocation.get(asset_class, 0)
                    weight_diff = target_weight - current_weight
                    
                    if abs(weight_diff) > 0.01:  # 1% threshold
                        amount = weight_diff * total_value
                        action_type = "buy" if amount > 0 else "sell"
                        
                        actions.append({
                            'action': action_type,
                            'asset_class': asset_class,
                            'amount': abs(amount),
                            'current_weight': current_weight,
                            'target_weight': target_weight,
                            'weight_difference': weight_diff
                        })
        
        except Exception:
            # Return empty actions on error
            pass
        
        return actions
    
    def get_recommendations_by_type(self, rec_type: PortfolioRecommendationType) -> List[PortfolioRecommendation]:
        """Get recommendations filtered by type"""
        return [rec for rec in self.recommendations if rec.type == rec_type]
    
    def get_recommendations_by_urgency(self, urgency: str) -> List[PortfolioRecommendation]:
        """Get recommendations filtered by urgency level"""
        return [rec for rec in self.recommendations if rec.urgency == urgency]
    
    def generate_recommendations(self, portfolio_data: Dict[str, Any], 
                               analysis_results: Dict[str, Any]) -> List[PortfolioRecommendation]:
        """
        Generate portfolio recommendations based on data and analysis
        
        Args:
            portfolio_data: Dictionary containing portfolio holdings and metrics
            analysis_results: Dictionary containing analysis results
            
        Returns:
            List of portfolio recommendations
        """
        recommendations = []
        
        try:
            # Extract holdings DataFrame - check both 'holdings' and 'holdings_df' keys
            holdings_df = portfolio_data.get('holdings_df') or portfolio_data.get('holdings', pd.DataFrame())
            
            if holdings_df is None or holdings_df.empty:
                return [PortfolioRecommendation(
                    id="no_portfolio_data",
                    type=PortfolioRecommendationType.ASSET_ALLOCATION,
                    title="Portfolio Data Missing",
                    description="No portfolio holdings data available for analysis.",
                    urgency="high",
                    impact_score=0,
                    ease_score=100,
                    action_steps=["Verify portfolio data source", "Check Excel file format"]
                )]
            
            # Extract portfolio analysis results
            portfolio_analysis = analysis_results.get('portfolio_analysis', {})
            
            # Generate practical recommendations
            recommendations.extend(self._generate_allocation_recommendations(holdings_df, portfolio_analysis))
            recommendations.extend(self._generate_rebalancing_recommendations(portfolio_analysis))
            recommendations.extend(self._generate_diversification_recommendations(holdings_df, portfolio_analysis))
            recommendations.extend(self._generate_cost_optimization_recommendations(holdings_df))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating portfolio recommendations: {str(e)}")
            return [PortfolioRecommendation(
                id="portfolio_analysis_error",
                type=PortfolioRecommendationType.ASSET_ALLOCATION,
                title="Portfolio Analysis Error",
                description=f"Error analyzing portfolio: {str(e)}",
                urgency="medium",
                impact_score=0,
                ease_score=90,
                action_steps=["Check portfolio data format", "Verify analysis configuration"]
            )]
    
    def analyze_asset_allocation(self, portfolio_data: Dict[str, Any], 
                               analysis_results: Dict[str, Any]) -> Optional[PortfolioRecommendation]:
        """
        Analyze asset allocation and provide recommendation
        
        Args:
            portfolio_data: Dictionary containing portfolio data
            analysis_results: Dictionary containing analysis results
            
        Returns:
            Asset allocation recommendation if needed
        """
        try:
            holdings_df = portfolio_data.get('holdings', pd.DataFrame())
            optimization_results = analysis_results.get('optimization_results', {})
            
            if holdings_df.empty:
                return None
            
            current_allocation = optimization_results.get('current_allocation', {})
            recommended_allocation = optimization_results.get('recommended_allocation', {})
            rebalancing_needed = optimization_results.get('rebalancing_needed', False)
            
            if rebalancing_needed and current_allocation and recommended_allocation:
                # Calculate allocation differences
                allocation_diffs = {}
                for asset_class in recommended_allocation:
                    current = current_allocation.get(asset_class, 0)
                    target = recommended_allocation[asset_class]
                    allocation_diffs[asset_class] = target - current
                
                return PortfolioRecommendation(
                    id="asset_allocation_rebalance",
                    type=PortfolioRecommendationType.ASSET_ALLOCATION,
                    title="Rebalance Asset Allocation",
                    description=f"Portfolio allocation deviates from target. Rebalancing recommended.",
                    urgency="medium",
                    impact_score=75,
                    ease_score=80,
                    current_allocation=current_allocation,
                    target_allocation=recommended_allocation,
                    action_steps=[
                        "Review current portfolio allocation",
                        "Calculate rebalancing trades needed",
                        "Execute trades in tax-efficient manner",
                        "Monitor allocation going forward"
                    ]
                )
            
            return None
            
        except Exception as e:
            print(f"Error analyzing asset allocation: {str(e)}")
            return None
    
    def _generate_allocation_recommendations(self, holdings_df: pd.DataFrame,
                                           portfolio_analysis: Dict[str, Any]) -> List[PortfolioRecommendation]:
        """Generate asset allocation recommendations"""
        recommendations = []
        
        try:
            # Get current allocation from portfolio analysis
            current_allocation = portfolio_analysis.get('current_allocation', {})
            asset_class_summary = portfolio_analysis.get('asset_class_summary', {})
            
            if current_allocation:
                # Check for concentration risk
                max_allocation = max(current_allocation.values()) if current_allocation else 0
                
                if max_allocation > 0.6:  # More than 60% in single asset class
                    dominant_class = max(current_allocation, key=current_allocation.get)
                    
                    recommendations.append(PortfolioRecommendation(
                        id="reduce_concentration_risk",
                        type=PortfolioRecommendationType.ASSET_ALLOCATION,
                        title="Reduce Portfolio Concentration Risk",
                        description=f"Portfolio is heavily concentrated in {dominant_class} ({max_allocation:.1%}). "
                                  f"Consider diversifying across asset classes.",
                        urgency="high",
                        impact_score=80,
                        ease_score=60,
                        current_allocation=current_allocation,
                        action_steps=[
                            f"Reduce {dominant_class} allocation to 40-50%",
                            "Increase allocation to other asset classes",
                            "Consider international diversification",
                            "Implement gradual rebalancing over 3-6 months"
                        ]
                    ))
                
                # Check for missing asset classes
                expected_classes = ['Equity', 'Fixed_Income', 'Alternatives', 'Cash']
                missing_classes = [cls for cls in expected_classes if cls not in current_allocation or current_allocation[cls] < 0.05]
                
                if len(missing_classes) > 1:
                    recommendations.append(PortfolioRecommendation(
                        id="improve_asset_diversification",
                        type=PortfolioRecommendationType.DIVERSIFICATION,
                        title="Add Missing Asset Classes",
                        description=f"Portfolio lacks exposure to: {', '.join(missing_classes)}. "
                                  f"Consider adding these for better diversification.",
                        urgency="medium",
                        impact_score=70,
                        ease_score=70,
                        current_allocation=current_allocation,
                        action_steps=[
                            f"Consider adding {missing_classes[0]} exposure (5-15%)",
                            "Research appropriate investment vehicles for missing classes",
                            "Start with low-cost index funds or ETFs",
                            "Gradually build allocation over time"
                        ]
                    ))
            
        except Exception as e:
            logger.warning(f"Error analyzing asset allocation: {str(e)}")
        
        return recommendations
    
    def _generate_rebalancing_recommendations(self, portfolio_analysis: Dict[str, Any]) -> List[PortfolioRecommendation]:
        """Generate rebalancing recommendations"""
        recommendations = []
        
        try:
            # Get rebalancing suggestions from portfolio analysis
            rebalancing_suggestions = portfolio_analysis.get('rebalancing_suggestions', [])
            optimization_results = portfolio_analysis.get('optimization_results', {})
            
            if rebalancing_suggestions and len(rebalancing_suggestions) > 0:
                # Create a comprehensive rebalancing recommendation
                total_trades = len(rebalancing_suggestions)
                total_value = sum(abs(trade.get('value_change_cny', 0)) for trade in rebalancing_suggestions)
                
                # Build specific actions from rebalancing suggestions
                specific_actions = []
                for suggestion in rebalancing_suggestions:
                    action_type = suggestion.get('action', 'Unknown')
                    asset_id = suggestion.get('asset_id', 'Unknown')
                    value_change = suggestion.get('value_change_cny', 0)
                    
                    specific_actions.append({
                        'action': action_type,
                        'asset': asset_id,
                        'amount_cny': abs(value_change),
                        'direction': 'buy' if value_change > 0 else 'sell'
                    })
                recommendations.append(PortfolioRecommendation(
                    id="execute_portfolio_rebalancing",
                    type=PortfolioRecommendationType.REBALANCING,
                    title="Execute Portfolio Rebalancing",
                    description=f"Portfolio has drifted from target allocation. "
                              f"{total_trades} trades needed, total value: ¥{total_value:,.0f}",
                    urgency="medium",
                    impact_score=75,
                    ease_score=60,
                    specific_actions=specific_actions,
                    estimated_benefit=total_value * 0.02,  # Assume 2% efficiency gain
                    implementation_cost=total_value * 0.001,  # Assume 0.1% transaction cost
                    action_steps=[
                        "Review suggested trades for reasonableness",
                        "Execute highest priority trades first",
                        "Consider tax implications of selling",
                        "Monitor portfolio after rebalancing"
                    ]
                ))
            
            # Check for portfolio efficiency improvements
            if optimization_results:
                best_strategy = optimization_results.get('best_strategy')
                if best_strategy:
                    current_sharpe = optimization_results.get('current_metrics', {}).get('sharpe_ratio', 0)
                    optimal_sharpe = best_strategy.get('sharpe_ratio', 0)
                    
                    if optimal_sharpe > current_sharpe + 0.1:  # Significant improvement possible
                        recommendations.append(PortfolioRecommendation(
                            id="optimize_risk_return_profile",
                            type=PortfolioRecommendationType.RISK_ADJUSTMENT,
                            title="Optimize Risk-Return Profile",
                            description=f"Current Sharpe ratio: {current_sharpe:.2f}. "
                                      f"Optimized strategy could achieve: {optimal_sharpe:.2f}",
                            urgency="low",
                            impact_score=60,
                            ease_score=50,
                            target_allocation=best_strategy.get('allocation', {}),
                            action_steps=[
                                "Review optimized allocation strategy",
                                "Compare with current allocation",
                                "Consider gradual transition to optimal allocation",
                                "Monitor performance improvements"
                            ]
                        ))
            
        except Exception as e:
            logger.warning(f"Error analyzing rebalancing needs: {str(e)}")
        
        return recommendations
    
    def _generate_diversification_recommendations(self, holdings_df: pd.DataFrame,
                                                portfolio_analysis: Dict[str, Any]) -> List[PortfolioRecommendation]:
        """Generate diversification recommendations"""
        recommendations = []
        
        try:
            if holdings_df is None or holdings_df.empty:
                return recommendations
            
            # Analyze individual holding concentration
            if 'Market_Value_CNY' in holdings_df.columns:
                total_value = holdings_df['Market_Value_CNY'].sum()
                holdings_df_copy = holdings_df.copy()
                holdings_df_copy['weight'] = holdings_df_copy['Market_Value_CNY'] / total_value
                
                # Check for individual stock concentration
                max_single_holding = holdings_df_copy['weight'].max()
                
                if max_single_holding > 0.25:  # Single holding > 25%
                    largest_holding = holdings_df_copy.loc[holdings_df_copy['weight'].idxmax()]
                    
                    recommendations.append(PortfolioRecommendation(
                        id="reduce_single_holding_risk",
                        type=PortfolioRecommendationType.DIVERSIFICATION,
                        title="Reduce Individual Holding Concentration",
                        description=f"Single holding ({largest_holding.get('Asset_Name', 'Unknown')}) "
                                  f"represents {max_single_holding:.1%} of portfolio. Consider reducing.",
                        urgency="medium",
                        impact_score=70,
                        ease_score=60,
                        action_steps=[
                            f"Consider reducing position in {largest_holding.get('Asset_Name', 'largest holding')}",
                            "Target individual holdings to <20% of portfolio",
                            "Reinvest proceeds in diversified funds",
                            "Monitor concentration risk regularly"
                        ]
                    ))
                
                # Check number of holdings
                num_holdings = len(holdings_df)
                if num_holdings < 10:
                    recommendations.append(PortfolioRecommendation(
                        id="increase_diversification",
                        type=PortfolioRecommendationType.DIVERSIFICATION,
                        title="Increase Portfolio Diversification",
                        description=f"Portfolio has only {num_holdings} holdings. "
                                  f"Consider adding more diversified investments.",
                        urgency="medium",
                        impact_score=65,
                        ease_score=75,
                        action_steps=[
                            "Consider broad market index funds",
                            "Add international exposure",
                            "Include different sectors and asset classes",
                            "Target 15-25 total holdings for adequate diversification"
                        ]
                    ))
            
        except Exception as e:
            logger.warning(f"Error analyzing diversification: {str(e)}")
        
        return recommendations
    
    def _generate_cost_optimization_recommendations(self, holdings_df: pd.DataFrame) -> List[PortfolioRecommendation]:
        """Generate cost optimization recommendations"""
        recommendations = []
        
        try:
            if holdings_df is None or holdings_df.empty:
                return recommendations
            
            # Look for high-cost investments (this would need expense ratio data)
            # For now, provide general cost optimization guidance
            if len(holdings_df) > 0:
                total_value = holdings_df.get('Market_Value_CNY', pd.Series([0])).sum()
                
                if total_value > 100000:  # Only for portfolios > 100k CNY
                    recommendations.append(PortfolioRecommendation(
                        id="review_investment_costs",
                        type=PortfolioRecommendationType.COST_OPTIMIZATION,
                        title="Review Investment Expense Ratios",
                        description=f"Portfolio value ¥{total_value:,.0f} justifies reviewing fund expenses. "
                                  f"High fees can significantly impact long-term returns.",
                        urgency="low",
                        impact_score=50,
                        ease_score=80,
                        estimated_benefit=total_value * 0.005,  # Assume 0.5% annual fee savings
                        action_steps=[
                            "Research expense ratios of current holdings",
                            "Compare with low-cost index fund alternatives",
                            "Consider ETFs vs actively managed funds",
                            "Calculate long-term cost impact of fee differences"
                        ]
                    ))
            
        except Exception as e:
            logger.warning(f"Error analyzing costs: {str(e)}")
        
        return recommendations
    
    def _analyze_asset_allocation_with_history(self, holdings_df: pd.DataFrame,
                                             portfolio_analysis_results: Dict[str, Any]) -> List[PortfolioRecommendation]:
        """Enhanced asset allocation analysis using historical performance context"""
        recommendations = []
        
        try:
            # Get historical performance context
            historical_perf = self.historical_performance.get('portfolio_performance', {})
            performance_attribution = self.historical_performance.get('performance_attribution', {})
            
            # Check if we have sufficient historical data
            if 'error' in historical_perf or not historical_perf:
                return self._analyze_asset_allocation(holdings_df, portfolio_analysis_results)
            
            # Analyze based on historical Sharpe ratio
            sharpe_ratio = historical_perf.get('sharpe_ratio', 0)
            annualized_return = historical_perf.get('annualized_return', 0)
            max_drawdown = historical_perf.get('max_drawdown', 0)
            
            if sharpe_ratio < 0.5:  # Poor risk-adjusted performance
                recommendations.append(PortfolioRecommendation(
                    id="improve_risk_adjusted_returns",
                    type=PortfolioRecommendationType.RISK_ADJUSTMENT,
                    title="Improve Risk-Adjusted Returns",
                    description=f"Your portfolio's historical Sharpe ratio is {sharpe_ratio:.2f}, indicating poor risk-adjusted returns. "
                               f"Consider diversifying into assets with better risk-return profiles.",
                    urgency="high",
                    impact_score=85,
                    ease_score=60,
                    action_steps=[
                        "Review asset allocation for over-concentration in volatile assets",
                        "Consider adding low-correlation assets (bonds, REITs, international equities)",
                        "Evaluate expense ratios and switch to lower-cost alternatives",
                        "Implement systematic rebalancing to maintain target allocation"
                    ]
                ))
            
            # Analyze based on maximum drawdown
            if abs(max_drawdown) > 0.3:  # More than 30% drawdown
                recommendations.append(PortfolioRecommendation(
                    id="reduce_downside_risk",
                    type=PortfolioRecommendationType.RISK_ADJUSTMENT,
                    title="Reduce Portfolio Downside Risk",
                    description=f"Your portfolio experienced a maximum drawdown of {abs(max_drawdown)*100:.1f}%, "
                               f"which is quite high. Consider adding defensive assets to reduce volatility.",
                    urgency="high",
                    impact_score=80,
                    ease_score=70,
                    action_steps=[
                        "Increase allocation to bonds or other defensive assets",
                        "Consider adding dividend-paying stocks for stability",
                        "Implement stop-loss strategies for high-risk positions",
                        "Review correlation between holdings to improve diversification"
                    ]
                ))
            
            # Performance attribution recommendations
            if 'asset_class_performance' in performance_attribution:
                class_performance = performance_attribution['asset_class_performance']
                underperforming_classes = []
                outperforming_classes = []
                
                for asset_class, perf_data in class_performance.items():
                    total_return = perf_data.get('total_return', 0)
                    if total_return < -0.1:  # More than 10% loss
                        underperforming_classes.append((asset_class, total_return))
                    elif total_return > 0.2:  # More than 20% gain
                        outperforming_classes.append((asset_class, total_return))
                
                if underperforming_classes:
                    worst_class, worst_return = min(underperforming_classes, key=lambda x: x[1])
                    recommendations.append(PortfolioRecommendation(
                        id="address_underperforming_assets",
                        type=PortfolioRecommendationType.ASSET_ALLOCATION,
                        title="Address Underperforming Asset Classes",
                        description=f"Your {worst_class} allocation has underperformed with a {worst_return*100:.1f}% return. "
                                   f"Consider reducing exposure or switching to better-performing alternatives.",
                        urgency="medium",
                        impact_score=70,
                        ease_score=60,
                        action_steps=[
                            f"Review reasons for {worst_class} underperformance",
                            "Consider reducing allocation to underperforming asset class",
                            "Research alternative investments in the same category",
                            "Gradually rebalance to avoid tax implications"
                        ]
                    ))
                
                if outperforming_classes:
                    best_class, best_return = max(outperforming_classes, key=lambda x: x[1])
                    recommendations.append(PortfolioRecommendation(
                        id="capitalize_on_outperformers",
                        type=PortfolioRecommendationType.ASSET_ALLOCATION,
                        title="Consider Rebalancing Strong Performers",
                        description=f"Your {best_class} allocation has performed very well with a {best_return*100:.1f}% return. "
                                   f"Consider taking some profits to maintain target allocation and reduce concentration risk.",
                        urgency="medium",
                        impact_score=60,
                        ease_score=80,
                        action_steps=[
                            f"Review current allocation to {best_class}",
                            "Consider taking partial profits if over-allocated",
                            "Rebalance into underweighted asset classes",
                            "Maintain disciplined allocation targets"
                        ]
                    ))
            
        except Exception as e:
            logger.error(f"Error in historical asset allocation analysis: {e}")
        
        return recommendations
    
    def _analyze_risk_characteristics_with_history(self, portfolio_analysis_results: Dict[str, Any]) -> List[PortfolioRecommendation]:
        """Enhanced risk analysis using historical risk metrics"""
        recommendations = []
        
        try:
            risk_metrics = self.historical_performance.get('risk_metrics', {})
            
            if 'error' in risk_metrics or not risk_metrics:
                return self._analyze_risk_characteristics(portfolio_analysis_results)
            
            # Analyze Sortino ratio
            sortino_ratio = risk_metrics.get('sortino_ratio', 0)
            if sortino_ratio < 1.0:
                recommendations.append(PortfolioRecommendation(
                    id="improve_downside_protection",
                    type=PortfolioRecommendationType.RISK_ADJUSTMENT,
                    title="Improve Downside Protection",
                    description=f"Your Sortino ratio of {sortino_ratio:.2f} suggests room for improvement in downside protection. "
                               f"Focus on reducing negative volatility while maintaining upside potential.",
                    urgency="medium",
                    impact_score=75,
                    ease_score=65,
                    action_steps=[
                        "Add defensive assets that perform well in market downturns",
                        "Consider protective options strategies if appropriate",
                        "Increase allocation to low-volatility, high-quality stocks",
                        "Review correlation patterns during market stress periods"
                    ]
                ))
            
            # Analyze Value at Risk
            var_5pct = risk_metrics.get('value_at_risk_5pct', 0)
            if abs(var_5pct) > 0.1:  # More than 10% potential daily loss
                recommendations.append(PortfolioRecommendation(
                    id="reduce_tail_risk",
                    type=PortfolioRecommendationType.RISK_ADJUSTMENT,
                    title="Reduce Tail Risk Exposure",
                    description=f"Your 5% Value at Risk is {abs(var_5pct)*100:.1f}%, indicating significant tail risk. "
                               f"Consider strategies to limit extreme losses.",
                    urgency="high",
                    impact_score=85,
                    ease_score=50,
                    action_steps=[
                        "Review positions with highest individual risk contributions",
                        "Consider position sizing limits (e.g., max 5% in any single stock)",
                        "Add uncorrelated assets to reduce portfolio-wide risk",
                        "Consider hedging strategies for extreme market events"
                    ]
                ))
            
            # Analyze skewness
            skewness = risk_metrics.get('skewness', 0)
            if skewness < -0.5:  # Negative skew indicates more frequent large losses
                recommendations.append(PortfolioRecommendation(
                    id="address_negative_skew",
                    type=PortfolioRecommendationType.RISK_ADJUSTMENT,
                    title="Address Negative Return Skewness",
                    description=f"Your portfolio exhibits negative skewness ({skewness:.2f}), meaning it experiences "
                               f"more frequent large losses than gains. Consider adding positive-skew assets.",
                    urgency="medium",
                    impact_score=70,
                    ease_score=55,
                    action_steps=[
                        "Add assets with positive skewness (e.g., momentum stocks, certain alternatives)",
                        "Review and reduce exposure to assets prone to sudden large drops",
                        "Consider options strategies that benefit from positive skew",
                        "Diversify across investment styles and geographies"
                    ]
                ))
            
        except Exception as e:
            logger.error(f"Error in historical risk analysis: {e}")
        
        return recommendations
    
    def _analyze_historical_performance(self, historical_performance_results: Dict[str, Any]) -> List[PortfolioRecommendation]:
        """Generate recommendations based on overall historical performance"""
        recommendations = []
        
        try:
            portfolio_perf = historical_performance_results.get('portfolio_performance', {})
            summary = historical_performance_results.get('summary', {})
            
            if 'error' in portfolio_perf:
                return recommendations
            
            # Performance rating recommendations
            portfolio_summary = summary.get('portfolio_summary', {})
            performance_rating = portfolio_summary.get('performance_rating', 'Unknown')
            annualized_return_pct = portfolio_summary.get('annualized_return_pct', 0)
            sharpe_ratio = portfolio_summary.get('sharpe_ratio', 0)
            data_period_years = portfolio_summary.get('data_period_years', 0)
            
            if performance_rating in ['Poor', 'Very Poor']:
                recommendations.append(PortfolioRecommendation(
                    id="comprehensive_portfolio_review",
                    type=PortfolioRecommendationType.ASSET_ALLOCATION,
                    title="Comprehensive Portfolio Review Needed",
                    description=f"Your portfolio's overall performance rating is '{performance_rating}' with an annualized return of "
                               f"{annualized_return_pct:.1f}% over {data_period_years:.1f} years. A comprehensive review and "
                               f"restructuring may be beneficial.",
                    urgency="critical",
                    impact_score=95,
                    ease_score=40,
                    action_steps=[
                        "Conduct thorough analysis of each holding's contribution to performance",
                        "Review investment philosophy and strategy alignment",
                        "Consider low-cost index funds for core positions",
                        "Evaluate tax efficiency of current holdings",
                        "Set up systematic investment and rebalancing plan"
                    ]
                ))
            
            elif performance_rating == 'Acceptable' and sharpe_ratio < 1.0:
                recommendations.append(PortfolioRecommendation(
                    id="optimize_risk_return_tradeoff",
                    type=PortfolioRecommendationType.RISK_ADJUSTMENT,
                    title="Optimize Risk-Return Trade-off",
                    description=f"While your {annualized_return_pct:.1f}% annual return is acceptable, your Sharpe ratio of "
                               f"{sharpe_ratio:.2f} suggests you're taking more risk than necessary for the returns achieved.",
                    urgency="medium",
                    impact_score=75,
                    ease_score=70,
                    action_steps=[
                        "Analyze which holdings contribute most to volatility",
                        "Consider reducing position sizes in high-volatility, low-return assets",
                        "Add defensive assets to improve risk-adjusted returns",
                        "Implement more systematic rebalancing"
                    ]
                ))
            
            # Calmar ratio analysis
            calmar_ratio = portfolio_perf.get('calmar_ratio', 0)
            if calmar_ratio < 1.0 and calmar_ratio > 0:
                recommendations.append(PortfolioRecommendation(
                    id="improve_drawdown_recovery",
                    type=PortfolioRecommendationType.RISK_ADJUSTMENT,
                    title="Improve Drawdown Recovery",
                    description=f"Your Calmar ratio of {calmar_ratio:.2f} indicates that your portfolio takes a long time to "
                               f"recover from drawdowns relative to its returns. Focus on reducing maximum drawdown.",
                    urgency="medium",
                    impact_score=80,
                    ease_score=60,
                    action_steps=[
                        "Add assets that perform well during market stress",
                        "Consider dynamic allocation strategies",
                        "Implement downside protection through options or other hedges",
                        "Review and improve diversification across asset classes"
                    ]
                ))
            
        except Exception as e:
            logger.error(f"Error analyzing historical performance: {e}")
        
        return recommendations
    
    def _analyze_performance_attribution(self, historical_performance_results: Dict[str, Any]) -> List[PortfolioRecommendation]:
        """Generate recommendations based on performance attribution analysis"""
        recommendations = []
        
        try:
            attribution = historical_performance_results.get('performance_attribution', {})
            
            if 'error' in attribution:
                return recommendations
            
            # Analyze top asset performance
            top_assets = attribution.get('top_asset_performance', {})
            if top_assets:
                # Find best and worst performers
                best_asset = max(top_assets.items(), key=lambda x: x[1].get('total_return', 0))
                worst_asset = min(top_assets.items(), key=lambda x: x[1].get('total_return', 0))
                
                best_name, best_data = best_asset
                worst_name, worst_data = worst_asset
                
                best_return = best_data.get('total_return', 0)
                worst_return = worst_data.get('total_return', 0)
                
                # Recommendation for underperforming assets
                if worst_return < -0.2:  # More than 20% loss
                    recommendations.append(PortfolioRecommendation(
                        id="review_worst_performers",
                        type=PortfolioRecommendationType.ASSET_ALLOCATION,
                        title="Review Worst Performing Assets",
                        description=f"Asset '{worst_name}' has lost {abs(worst_return)*100:.1f}% over the analysis period. "
                                   f"Consider whether this position still aligns with your investment thesis.",
                        urgency="high",
                        impact_score=85,
                        ease_score=75,
                        action_steps=[
                            f"Research current fundamentals and outlook for {worst_name}",
                            "Determine if poor performance is temporary or structural",
                            "Consider tax implications of selling at a loss",
                            "Evaluate replacement options in the same asset class"
                        ]
                    ))
                
                # Concentration risk from winners
                if best_return > 1.0:  # More than 100% gain
                    current_value = best_data.get('current_value', 0)
                    if current_value > 50000:  # Significant absolute value
                        recommendations.append(PortfolioRecommendation(
                            id="manage_concentration_risk",
                            type=PortfolioRecommendationType.RISK_ADJUSTMENT,
                            title="Manage Concentration Risk from Winners",
                            description=f"Asset '{best_name}' has gained {best_return*100:.1f}% and may now represent "
                                       f"outsized portfolio concentration. Consider taking partial profits.",
                            urgency="medium",
                            impact_score=70,
                            ease_score=80,
                            action_steps=[
                                f"Calculate current allocation percentage for {best_name}",
                                "Set target allocation limits (e.g., max 10% in any single asset)",
                                "Consider systematic profit-taking strategy",
                                "Reinvest proceeds in underweighted asset classes"
                            ]
                        ))
            
        except Exception as e:
            logger.error(f"Error in performance attribution analysis: {e}")
        
        return recommendations
