"""
Risk Advisor Module for Investment Recommendation System

This module provides risk management recommendations based on portfolio analysis,
market conditions, and individual risk profile.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level classifications"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"


class RiskCategory(Enum):
    """Risk category types"""
    CONCENTRATION = "concentration"
    VOLATILITY = "volatility"
    LIQUIDITY = "liquidity"
    CREDIT = "credit"
    MARKET = "market"
    CURRENCY = "currency"


@dataclass
class RiskAssessment:
    """Risk assessment result"""
    category: RiskCategory
    level: RiskLevel
    score: float
    description: str
    impact: str
    mitigation_strategies: List[str]


@dataclass
class RiskRecommendation:
    """Risk management recommendation"""
    risk_type: RiskCategory
    priority: int
    action: str
    rationale: str
    expected_impact: str
    timeline: str
    effort_level: str


class RiskAdvisor:
    """
    Provides risk management recommendations based on portfolio analysis
    """
    
    def __init__(self):
        """Initialize the RiskAdvisor"""
        self.risk_thresholds = {
            'concentration_limit': 0.20,  # Maximum 20% in single position
            'sector_concentration_limit': 0.30,  # Maximum 30% in single sector
            'volatility_threshold': 0.25,  # 25% annualized volatility threshold
            'liquidity_threshold': 0.10,  # Minimum 10% in liquid assets
            'correlation_threshold': 0.80,  # High correlation threshold
        }
        
    def analyze_portfolio_risks(self, portfolio_data: Dict[str, Any], 
                              market_data: Optional[Dict[str, Any]] = None,
                              historical_performance_results: Optional[Dict[str, Any]] = None) -> List[RiskAssessment]:
        """
        Analyze portfolio for various risk factors
        
        Args:
            portfolio_data: Portfolio holdings and analysis data
            market_data: Optional market condition data
            historical_performance_results: Historical performance and risk analysis results
            
        Returns:
            List of risk assessments
        """
        risk_assessments = []
        
        try:
            # Analyze concentration risk
            concentration_assessment = self._assess_concentration_risk(portfolio_data)
            if concentration_assessment:
                risk_assessments.append(concentration_assessment)
            
            # Analyze volatility risk with historical context
            volatility_assessment = self._assess_volatility_risk(portfolio_data, historical_performance_results)
            if volatility_assessment:
                risk_assessments.append(volatility_assessment)
            
            # Analyze liquidity risk
            liquidity_assessment = self._assess_liquidity_risk(portfolio_data)
            if liquidity_assessment:
                risk_assessments.append(liquidity_assessment)
            
            # Analyze correlation risk
            correlation_assessment = self._assess_correlation_risk(portfolio_data)
            if correlation_assessment:
                risk_assessments.append(correlation_assessment)
            
            # Analyze market risk if market data available
            if market_data:
                market_assessment = self._assess_market_risk(portfolio_data, market_data)
                if market_assessment:
                    risk_assessments.append(market_assessment)
            
            # Add historical risk assessments if available
            if historical_performance_results:
                historical_risk_assessments = self._assess_historical_risks(historical_performance_results)
                risk_assessments.extend(historical_risk_assessments)
                
                concentration_history = self._assess_historical_concentration(historical_performance_results)
                if concentration_history:
                    risk_assessments.append(concentration_history)
            
            logger.info(f"Completed risk analysis with {len(risk_assessments)} assessments")
            return risk_assessments
            
        except Exception as e:
            logger.error(f"Error in portfolio risk analysis: {str(e)}")
            return []
    
    def _assess_concentration_risk(self, portfolio_data: Dict[str, Any]) -> Optional[RiskAssessment]:
        """Assess concentration risk in portfolio"""
        try:
            if 'holdings' not in portfolio_data:
                return None
            
            holdings_df = portfolio_data['holdings']
            if holdings_df.empty:
                return None
            
            # Calculate position concentrations
            total_value = holdings_df['market_value'].sum()
            holdings_df['weight'] = holdings_df['market_value'] / total_value
            
            max_position = holdings_df['weight'].max()
            top_5_concentration = holdings_df.nlargest(5, 'weight')['weight'].sum()
            
            # Assess sector concentration if available
            sector_concentration = 0
            if 'sector' in holdings_df.columns:
                sector_weights = holdings_df.groupby('sector')['weight'].sum()
                sector_concentration = sector_weights.max()
            
            # Determine risk level
            risk_score = max(max_position, sector_concentration)
            
            if risk_score > 0.40:
                level = RiskLevel.EXTREME
            elif risk_score > 0.30:
                level = RiskLevel.HIGH
            elif risk_score > 0.20:
                level = RiskLevel.MODERATE
            else:
                level = RiskLevel.LOW
            
            mitigation_strategies = []
            if max_position > self.risk_thresholds['concentration_limit']:
                mitigation_strategies.append("Reduce largest position size")
                mitigation_strategies.append("Diversify into additional holdings")
            
            if sector_concentration > self.risk_thresholds['sector_concentration_limit']:
                mitigation_strategies.append("Reduce sector concentration")
                mitigation_strategies.append("Add holdings from underrepresented sectors")
            
            return RiskAssessment(
                category=RiskCategory.CONCENTRATION,
                level=level,
                score=risk_score,
                description=f"Maximum position: {max_position:.1%}, Top 5 concentration: {top_5_concentration:.1%}",
                impact="High concentration increases portfolio volatility and single-point-of-failure risk",
                mitigation_strategies=mitigation_strategies
            )
            
        except Exception as e:
            logger.error(f"Error assessing concentration risk: {str(e)}")
            return None
    
    def _assess_volatility_risk(self, portfolio_data: Dict[str, Any], 
                               historical_performance_results: Optional[Dict[str, Any]] = None) -> Optional[RiskAssessment]:
        """Assess portfolio volatility risk with historical context"""
        try:
            # Try to get volatility from portfolio analysis or historical data
            portfolio_volatility = None
            historical_context = ""
            
            # First, try historical performance results
            if (historical_performance_results and 
                'portfolio_performance' in historical_performance_results and
                'annualized_volatility' in historical_performance_results['portfolio_performance']):
                portfolio_volatility = historical_performance_results['portfolio_performance']['annualized_volatility']
                years = historical_performance_results['portfolio_performance'].get('data_period_years', 0)
                historical_context = f" Based on {years:.1f} years of historical data."
            
            # Fallback to current analysis
            if portfolio_volatility is None and 'analysis_results' in portfolio_data:
                analysis = portfolio_data['analysis_results']
                if 'portfolio_volatility' in analysis:
                    portfolio_volatility = analysis['portfolio_volatility']
                elif 'risk_metrics' in analysis and 'volatility' in analysis['risk_metrics']:
                    portfolio_volatility = analysis['risk_metrics']['volatility']
            
            if portfolio_volatility is None:
                return None
            
            # Check for volatility trends if historical data available
            volatility_trend_context = ""
            if (historical_performance_results and 
                'risk_metrics' in historical_performance_results and
                'volatility_of_volatility' in historical_performance_results['risk_metrics']):
                vol_of_vol = historical_performance_results['risk_metrics']['volatility_of_volatility']
                if vol_of_vol > 0.05:  # High volatility of volatility
                    volatility_trend_context = f" Portfolio shows high volatility clustering (σ of σ = {vol_of_vol:.1%})."
            
            # Determine risk level based on volatility
            if portfolio_volatility > 0.35:
                level = RiskLevel.EXTREME
            elif portfolio_volatility > 0.25:
                level = RiskLevel.HIGH
            elif portfolio_volatility > 0.15:
                level = RiskLevel.MODERATE
            else:
                level = RiskLevel.LOW
            
            mitigation_strategies = []
            if portfolio_volatility > self.risk_thresholds['volatility_threshold']:
                mitigation_strategies.extend([
                    "Add low-volatility assets (bonds, defensive stocks)",
                    "Implement volatility management strategies",
                    "Consider diversification across asset classes",
                    "Review position sizing for high-volatility holdings"
                ])
                
                # Add historical context-specific strategies
                if historical_performance_results:
                    if 'risk_metrics' in historical_performance_results:
                        risk_metrics = historical_performance_results['risk_metrics']
                        sortino_ratio = risk_metrics.get('sortino_ratio', 0)
                        if sortino_ratio < 1.0:
                            mitigation_strategies.append("Focus on reducing downside risk rather than total volatility")
                        
                        skewness = risk_metrics.get('skewness', 0)
                        if skewness < -0.5:  # Negative skew indicates tail risk
                            mitigation_strategies.append("Address tail risk exposure through hedging strategies")
            
            return RiskAssessment(
                category=RiskCategory.VOLATILITY,
                level=level,
                score=portfolio_volatility,
                description=f"Portfolio volatility: {portfolio_volatility:.1%} annualized{historical_context}{volatility_trend_context}",
                impact="High volatility increases potential for large losses and emotional decision-making",
                mitigation_strategies=mitigation_strategies
            )
            
        except Exception as e:
            logger.error(f"Error assessing volatility risk: {str(e)}")
            return None
    
    def _assess_liquidity_risk(self, portfolio_data: Dict[str, Any]) -> Optional[RiskAssessment]:
        """Assess portfolio liquidity risk"""
        try:
            if 'holdings' not in portfolio_data:
                return None
            
            holdings_df = portfolio_data['holdings']
            if holdings_df.empty:
                return None
            
            total_value = holdings_df['market_value'].sum()
            
            # Categorize holdings by liquidity (simplified approach)
            liquid_assets = 0
            illiquid_assets = 0
            
            for _, holding in holdings_df.iterrows():
                asset_type = holding.get('asset_type', '').lower()
                if asset_type in ['cash', 'money_market', 'etf', 'large_cap_stock']:
                    liquid_assets += holding['market_value']
                elif asset_type in ['small_cap_stock', 'reit', 'bond']:
                    # Moderately liquid
                    liquid_assets += holding['market_value'] * 0.7
                else:
                    # Assume illiquid
                    illiquid_assets += holding['market_value']
            
            liquidity_ratio = liquid_assets / total_value if total_value > 0 else 0
            
            # Determine risk level
            if liquidity_ratio < 0.50:
                level = RiskLevel.EXTREME
            elif liquidity_ratio < 0.70:
                level = RiskLevel.HIGH
            elif liquidity_ratio < 0.85:
                level = RiskLevel.MODERATE
            else:
                level = RiskLevel.LOW
            
            mitigation_strategies = []
            if liquidity_ratio < 0.80:
                mitigation_strategies.extend([
                    "Increase allocation to liquid assets (ETFs, large-cap stocks)",
                    "Maintain emergency cash reserves",
                    "Reduce exposure to illiquid investments",
                    "Stagger maturity dates for fixed-income holdings"
                ])
            
            return RiskAssessment(
                category=RiskCategory.LIQUIDITY,
                level=level,
                score=1 - liquidity_ratio,  # Higher score = more risk
                description=f"Liquidity ratio: {liquidity_ratio:.1%} of portfolio in liquid assets",
                impact="Low liquidity limits ability to respond to opportunities or emergencies",
                mitigation_strategies=mitigation_strategies
            )
            
        except Exception as e:
            logger.error(f"Error assessing liquidity risk: {str(e)}")
            return None
    
    def _assess_correlation_risk(self, portfolio_data: Dict[str, Any]) -> Optional[RiskAssessment]:
        """Assess correlation risk between holdings"""
        try:
            # This is a simplified correlation assessment
            # In practice, you'd need historical price data to calculate correlations
            
            if 'holdings' not in portfolio_data:
                return None
            
            holdings_df = portfolio_data['holdings']
            if holdings_df.empty or len(holdings_df) < 2:
                return None
            
            # Simplified correlation assessment based on asset types and sectors
            correlation_risk_score = 0
            
            # Check sector concentration
            if 'sector' in holdings_df.columns:
                sector_weights = holdings_df.groupby('sector')['market_value'].sum()
                total_value = holdings_df['market_value'].sum()
                sector_percentages = sector_weights / total_value
                
                # High concentration in similar sectors increases correlation risk
                max_sector_weight = sector_percentages.max()
                correlation_risk_score = max_sector_weight
            
            # Determine risk level
            if correlation_risk_score > 0.50:
                level = RiskLevel.HIGH
            elif correlation_risk_score > 0.30:
                level = RiskLevel.MODERATE
            else:
                level = RiskLevel.LOW
            
            mitigation_strategies = []
            if correlation_risk_score > 0.30:
                mitigation_strategies.extend([
                    "Diversify across uncorrelated asset classes",
                    "Add international exposure to reduce correlation",
                    "Include alternative investments (REITs, commodities)",
                    "Balance growth and value styles"
                ])
            
            return RiskAssessment(
                category=RiskCategory.MARKET,
                level=level,
                score=correlation_risk_score,
                description=f"Estimated correlation risk based on sector concentration: {correlation_risk_score:.1%}",
                impact="High correlation reduces diversification benefits during market stress",
                mitigation_strategies=mitigation_strategies
            )
            
        except Exception as e:
            logger.error(f"Error assessing correlation risk: {str(e)}")
            return None
    
    def _assess_market_risk(self, portfolio_data: Dict[str, Any], 
                           market_data: Dict[str, Any]) -> Optional[RiskAssessment]:
        """Assess market-wide risk factors"""
        try:
            # This would analyze market conditions like:
            # - Market valuation levels
            # - Economic indicators
            # - Volatility indices
            # - Interest rate environment
            
            # Simplified implementation
            market_risk_score = 0.5  # Default moderate risk
            level = RiskLevel.MODERATE
            
            mitigation_strategies = [
                "Monitor market conditions regularly",
                "Maintain defensive positions during high uncertainty",
                "Consider hedging strategies if appropriate",
                "Review and adjust asset allocation based on market cycle"
            ]
            
            return RiskAssessment(
                category=RiskCategory.MARKET,
                level=level,
                score=market_risk_score,
                description="General market risk assessment based on current conditions",
                impact="Market-wide factors can affect entire portfolio simultaneously",
                mitigation_strategies=mitigation_strategies
            )
            
        except Exception as e:
            logger.error(f"Error assessing market risk: {str(e)}")
            return None
    
    def _assess_historical_risks(self, historical_performance_results: Dict[str, Any]) -> List[RiskAssessment]:
        """Assess risks based on historical performance patterns"""
        assessments = []
        
        try:
            if 'risk_metrics' not in historical_performance_results:
                return assessments
            
            risk_metrics = historical_performance_results['risk_metrics']
            
            # Assess Value at Risk (VaR) concerns
            var_5 = risk_metrics.get('value_at_risk_5pct', 0)
            var_1 = risk_metrics.get('value_at_risk_1pct', 0)
            
            if var_5 < -0.05:  # More than 5% potential loss in 5% worst cases
                level = RiskLevel.HIGH if var_5 < -0.10 else RiskLevel.MODERATE
                
                assessments.append(RiskAssessment(
                    category=RiskCategory.MARKET,
                    level=level,
                    score=abs(var_5),
                    description=f"Historical VaR analysis shows 5% chance of losing more than {abs(var_5):.1%} in a period",
                    impact="Significant potential for large losses during market stress",
                    mitigation_strategies=[
                        "Implement downside protection strategies",
                        "Consider portfolio insurance or hedging",
                        "Reduce exposure to high-risk assets during uncertain periods",
                        "Build cash reserves for market downturns"
                    ]
                ))
            
            # Assess downside risk (Sortino ratio)
            sortino_ratio = risk_metrics.get('sortino_ratio', 0)
            if sortino_ratio < 1.0:
                level = RiskLevel.HIGH if sortino_ratio < 0.5 else RiskLevel.MODERATE
                
                assessments.append(RiskAssessment(
                    category=RiskCategory.VOLATILITY,
                    level=level,
                    score=1.0 - sortino_ratio,
                    description=f"Poor downside risk management (Sortino ratio: {sortino_ratio:.2f})",
                    impact="Inadequate compensation for downside risk exposure",
                    mitigation_strategies=[
                        "Focus on reducing downside volatility rather than total volatility",
                        "Consider asymmetric return strategies",
                        "Add defensive assets to reduce downside capture",
                        "Implement stop-loss or protective strategies"
                    ]
                ))
            
            # Assess skewness (tail risk)
            skewness = risk_metrics.get('skewness', 0)
            if skewness < -0.5:  # Significant negative skew indicates tail risk
                assessments.append(RiskAssessment(
                    category=RiskCategory.MARKET,
                    level=RiskLevel.MODERATE,
                    score=abs(skewness),
                    description=f"Portfolio exhibits negative skewness ({skewness:.2f}), indicating tail risk exposure",
                    impact="Higher probability of extreme negative returns than normal distribution suggests",
                    mitigation_strategies=[
                        "Consider tail risk hedging strategies",
                        "Diversify across different return distributions",
                        "Add assets with positive skew characteristics",
                        "Monitor position sizing in volatile assets"
                    ]
                ))
            
            # Assess kurtosis (fat tails)
            kurtosis = risk_metrics.get('kurtosis', 0)
            if kurtosis > 2.0:  # Excess kurtosis indicates fat tails
                assessments.append(RiskAssessment(
                    category=RiskCategory.VOLATILITY,
                    level=RiskLevel.MODERATE,
                    score=kurtosis,
                    description=f"Portfolio shows high kurtosis ({kurtosis:.2f}), indicating fat-tail risk",
                    impact="Higher probability of extreme outcomes than normal distribution",
                    mitigation_strategies=[
                        "Prepare for extreme market events",
                        "Consider position sizing adjustments",
                        "Diversify across assets with different tail characteristics",
                        "Maintain higher cash reserves for extreme scenarios"
                    ]
                ))
            
            return assessments
            
        except Exception as e:
            logger.error(f"Error assessing historical risks: {str(e)}")
            return []
    
    def _assess_historical_concentration(self, historical_performance_results: Dict[str, Any]) -> Optional[RiskAssessment]:
        """Assess concentration risk based on historical performance attribution"""
        try:
            if 'performance_attribution' not in historical_performance_results:
                return None
            
            attribution = historical_performance_results['performance_attribution']
            
            # Analyze asset class concentration from historical data
            if 'asset_class_performance' in attribution:
                asset_class_perf = attribution['asset_class_performance']
                
                if not asset_class_perf:
                    return None
                
                # Calculate concentration based on performance impact
                total_performance_impact = sum(abs(perf.get('total_return', 0)) 
                                             for perf in asset_class_perf.values())
                
                if total_performance_impact > 0:
                    max_class_impact = max(abs(perf.get('total_return', 0)) 
                                         for perf in asset_class_perf.values())
                    concentration_ratio = max_class_impact / total_performance_impact
                    
                    if concentration_ratio > 0.6:  # Single asset class dominates performance
                        level = RiskLevel.HIGH
                        impact_desc = "Single asset class dominates portfolio performance"
                    elif concentration_ratio > 0.4:
                        level = RiskLevel.MODERATE  
                        impact_desc = "Portfolio shows moderate asset class concentration"
                    else:
                        return None  # No concerning concentration
                    
                    # Identify the dominant asset class
                    dominant_class = max(asset_class_perf.keys(), 
                                       key=lambda k: abs(asset_class_perf[k].get('total_return', 0)))
                    
                    return RiskAssessment(
                        category=RiskCategory.CONCENTRATION,
                        level=level,
                        score=concentration_ratio,
                        description=f"Historical analysis shows {dominant_class} dominates portfolio performance "
                                  f"({concentration_ratio:.1%} of total impact)",
                        impact=impact_desc,
                        mitigation_strategies=[
                            f"Reduce allocation to {dominant_class}",
                            "Diversify across more asset classes",
                            "Add uncorrelated assets to reduce single-class dependence",
                            "Monitor sector rotation opportunities",
                            "Consider market-neutral strategies"
                        ]
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error assessing historical concentration: {str(e)}")
            return None
    
    def generate_recommendations(self, risk_assessments: List[RiskAssessment]) -> List[RiskRecommendation]:
        """
        Generate prioritized risk management recommendations
        
        Args:
            risk_assessments: List of risk assessments
            
        Returns:
            List of prioritized risk recommendations
        """
        recommendations = []
        
        try:
            # Sort assessments by risk level and score
            sorted_assessments = sorted(
                risk_assessments,
                key=lambda x: (x.level.value, x.score),
                reverse=True
            )
            
            priority = 1
            for assessment in sorted_assessments:
                if assessment.level in [RiskLevel.HIGH, RiskLevel.EXTREME]:
                    # Generate high-priority recommendations for significant risks
                    for strategy in assessment.mitigation_strategies[:2]:  # Top 2 strategies
                        recommendation = RiskRecommendation(
                            risk_type=assessment.category,
                            priority=priority,
                            action=strategy,
                            rationale=f"Address {assessment.level.value} {assessment.category.value} risk",
                            expected_impact="Reduce portfolio risk and improve stability",
                            timeline="1-3 months" if assessment.level == RiskLevel.EXTREME else "3-6 months",
                            effort_level="High" if assessment.level == RiskLevel.EXTREME else "Medium"
                        )
                        recommendations.append(recommendation)
                        priority += 1
                
                elif assessment.level == RiskLevel.MODERATE:
                    # Generate medium-priority recommendations
                    if assessment.mitigation_strategies:
                        strategy = assessment.mitigation_strategies[0]  # Top strategy
                        recommendation = RiskRecommendation(
                            risk_type=assessment.category,
                            priority=priority,
                            action=strategy,
                            rationale=f"Improve {assessment.category.value} risk profile",
                            expected_impact="Enhance portfolio resilience",
                            timeline="6-12 months",
                            effort_level="Medium"
                        )
                        recommendations.append(recommendation)
                        priority += 1
            
            # Limit to top 10 recommendations
            recommendations = recommendations[:10]
            
            logger.info(f"Generated {len(recommendations)} risk recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating risk recommendations: {str(e)}")
            return []
    
    def get_risk_summary(self, risk_assessments: List[RiskAssessment]) -> Dict[str, Any]:
        """
        Generate a summary of portfolio risk profile
        
        Args:
            risk_assessments: List of risk assessments
            
        Returns:
            Risk summary dictionary
        """
        try:
            if not risk_assessments:
                return {"overall_risk": "Unknown", "risk_count": 0}
            
            # Count risks by level
            risk_counts = {level.value: 0 for level in RiskLevel}
            for assessment in risk_assessments:
                risk_counts[assessment.level.value] += 1
            
            # Determine overall risk level
            if risk_counts['extreme'] > 0:
                overall_risk = "Extreme"
            elif risk_counts['high'] > 1:
                overall_risk = "High"
            elif risk_counts['high'] > 0 or risk_counts['moderate'] > 2:
                overall_risk = "High"
            elif risk_counts['moderate'] > 0:
                overall_risk = "Moderate"
            else:
                overall_risk = "Low"
            
            # Calculate average risk score
            avg_risk_score = np.mean([assessment.score for assessment in risk_assessments])
            
            return {
                "overall_risk": overall_risk,
                "risk_count": len(risk_assessments),
                "risk_breakdown": risk_counts,
                "average_risk_score": round(avg_risk_score, 3),
                "primary_concerns": [
                    assessment.category.value for assessment in risk_assessments
                    if assessment.level in [RiskLevel.HIGH, RiskLevel.EXTREME]
                ][:3]
            }
            
        except Exception as e:
            logger.error(f"Error generating risk summary: {str(e)}")
            return {"overall_risk": "Unknown", "risk_count": 0, "error": str(e)}
