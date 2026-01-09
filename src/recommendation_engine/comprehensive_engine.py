"""
Comprehensive Recommendation Engine

This module provides the main interface for generating comprehensive investment
recommendations by coordinating all advisor modules.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from .financial_advisor import FinancialAdvisor
from .portfolio_advisor import PortfolioAdvisor  
from .risk_advisor import RiskAdvisor
from .tax_advisor import TaxAdvisor
from .action_prioritizer import ActionPrioritizer, ActionPlan

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RecommendationEngineConfig:
    """Configuration for the recommendation engine"""
    include_financial_analysis: bool = True
    include_portfolio_optimization: bool = True
    include_risk_management: bool = True
    include_tax_optimization: bool = True
    max_recommendations_per_category: int = 10
    prioritize_risk_management: bool = True
    user_risk_tolerance: str = "moderate"  # conservative, moderate, aggressive
    user_time_availability: str = "medium"  # low, medium, high
    focus_areas: List[str] = None  # Custom focus areas
    short_term_tax_rate: float = 0.37
    long_term_tax_rate: float = 0.20


@dataclass  
class ComprehensiveRecommendationResult:
    """Complete recommendation engine output"""
    financial_recommendations: List[Any]
    portfolio_recommendations: List[Any]
    risk_recommendations: List[Any]
    tax_recommendations: List[Any]
    prioritized_action_plan: ActionPlan
    summary: Dict[str, Any]
    execution_metadata: Dict[str, Any]


class ComprehensiveRecommendationEngine:
    """
    Main recommendation engine that coordinates all advisor modules
    """
    
    def __init__(self, config: Optional[RecommendationEngineConfig] = None):
        """Initialize the comprehensive recommendation engine"""
        self.config = config or RecommendationEngineConfig()
        
        # Initialize advisor modules
        self.financial_advisor = FinancialAdvisor()
        self.portfolio_advisor = PortfolioAdvisor()
        self.risk_advisor = RiskAdvisor()
        self.tax_advisor = TaxAdvisor(
            short_term_tax_rate=self.config.short_term_tax_rate,
            long_term_tax_rate=self.config.long_term_tax_rate
        )
        self.action_prioritizer = ActionPrioritizer()
        
        logger.info("Comprehensive Recommendation Engine initialized with TaxAdvisor")
    
    def generate_recommendations(self, 
                               financial_data: Dict[str, Any],
                               portfolio_data: Dict[str, Any],
                               analysis_results: Dict[str, Any],
                               user_preferences: Optional[Dict[str, Any]] = None) -> ComprehensiveRecommendationResult:
        """
        Generate comprehensive investment recommendations
        
        Args:
            financial_data: Financial health and cash flow data
            portfolio_data: Portfolio holdings and performance data
            analysis_results: Results from unified analysis engine
            user_preferences: User-specific preferences and constraints
            
        Returns:
            Comprehensive recommendation result
        """
        start_time = datetime.now()
        
        try:
            logger.info("Starting comprehensive recommendation generation")
            logger.info(f"Input data summary - Financial data keys: {list(financial_data.keys())}")
            logger.info(f"Input data summary - Portfolio data keys: {list(portfolio_data.keys())}")
            logger.info(f"Input data summary - Analysis results keys: {list(analysis_results.keys())}")
            
            # Initialize recommendation lists
            financial_recs = []
            portfolio_recs = []
            risk_recs = []
            tax_recs = []
            
            # Generate financial recommendations
            if self.config.include_financial_analysis:
                try:
                    financial_recs = self._generate_financial_recommendations(
                        financial_data, analysis_results
                    )
                    logger.info(f"Generated {len(financial_recs)} financial recommendations")
                    
                    # Add fallback recommendation if none generated
                    if not financial_recs:
                        logger.info("Adding fallback financial recommendation")
                        financial_recs = self._create_fallback_financial_recommendations()
                        
                except Exception as e:
                    logger.error(f"Error generating financial recommendations: {str(e)}")
                    financial_recs = self._create_fallback_financial_recommendations()
            
            # Generate portfolio recommendations  
            if self.config.include_portfolio_optimization:
                try:
                    portfolio_recs = self._generate_portfolio_recommendations(
                        portfolio_data, analysis_results
                    )
                    logger.info(f"Generated {len(portfolio_recs)} portfolio recommendations")
                    
                    # Add fallback recommendation if none generated
                    if not portfolio_recs:
                        logger.info("Adding fallback portfolio recommendation")
                        portfolio_recs = self._create_fallback_portfolio_recommendations()
                        
                except Exception as e:
                    logger.error(f"Error generating portfolio recommendations: {str(e)}")
                    portfolio_recs = self._create_fallback_portfolio_recommendations()
            
            # Generate risk management recommendations
            if self.config.include_risk_management:
                try:
                    risk_recs = self._generate_risk_recommendations(
                        portfolio_data, analysis_results
                    )
                    logger.info(f"Generated {len(risk_recs)} risk recommendations")
                except Exception as e:
                    logger.error(f"Error generating risk recommendations: {str(e)}")
            
            # Generate tax optimization recommendations
            if self.config.include_tax_optimization:
                try:
                    tax_recs = self._generate_tax_recommendations(
                        portfolio_data, analysis_results
                    )
                    logger.info(f"Generated {len(tax_recs)} tax recommendations")
                except Exception as e:
                    logger.error(f"Error generating tax recommendations: {str(e)}")
                    tax_recs = []
            
            # Create prioritized action plan
            user_prefs = self._prepare_user_preferences(user_preferences)
            action_plan = self.action_prioritizer.create_action_plan(
                financial_recs, portfolio_recs, risk_recs, user_prefs
            )
            
            # Generate summary
            summary = self._generate_recommendation_summary(
                financial_recs, portfolio_recs, risk_recs, tax_recs, action_plan
            )
            
            # Create execution metadata
            end_time = datetime.now()
            execution_metadata = {
                "generation_time": (end_time - start_time).total_seconds(),
                "timestamp": end_time.isoformat(),
                "config_used": self.config.__dict__,
                "recommendation_counts": {
                    "financial": len(financial_recs),
                    "portfolio": len(portfolio_recs),  
                    "risk": len(risk_recs),
                    "tax": len(tax_recs),
                    "total_actions": action_plan.summary.get('total_actions', 0)
                }
            }
            
            result = ComprehensiveRecommendationResult(
                financial_recommendations=financial_recs,
                portfolio_recommendations=portfolio_recs,
                risk_recommendations=risk_recs,
                tax_recommendations=tax_recs,
                prioritized_action_plan=action_plan,
                summary=summary,
                execution_metadata=execution_metadata
            )
            
            logger.info(f"Recommendation generation completed in {execution_metadata['generation_time']:.2f} seconds")
            return result
            
        except Exception as e:
            logger.error(f"Error in comprehensive recommendation generation: {str(e)}")
            
            # Return minimal result with error info
            return ComprehensiveRecommendationResult(
                financial_recommendations=[],
                portfolio_recommendations=[],
                risk_recommendations=[],
                prioritized_action_plan=ActionPlan([], [], [], [], [], {"error": str(e)}),
                summary={"error": str(e)},
                execution_metadata={"error": str(e), "generation_time": 0}
            )
    
    def _generate_financial_recommendations(self, 
                                          financial_data: Dict[str, Any],
                                          analysis_results: Dict[str, Any]) -> List[Any]:
        """Generate financial health recommendations"""
        try:
            logger.info("=== FINANCIAL RECOMMENDATIONS GENERATION ===")
            logger.info(f"Financial data input: {type(financial_data)} with keys: {list(financial_data.keys()) if financial_data else 'None'}")
            logger.info(f"Analysis results input: {type(analysis_results)} with keys: {list(analysis_results.keys()) if analysis_results else 'None'}")
            
            # Validate input data
            if not financial_data:
                logger.warning("Financial data is empty or None")
                return []
            
            if not analysis_results:
                logger.warning("Analysis results is empty or None")
                return []
            
            # Generate recommendations using FinancialAdvisor with full analysis_results
            logger.info("Calling FinancialAdvisor.generate_recommendations...")
            recommendations = self.financial_advisor.generate_recommendations(
                financial_data, analysis_results
            )
            
            logger.info(f"FinancialAdvisor returned {len(recommendations)} recommendations")
            if recommendations:
                for i, rec in enumerate(recommendations[:3], 1):  # Log first 3
                    logger.info(f"  {i}. {getattr(rec, 'title', 'No title')} (Urgency: {getattr(rec, 'urgency', 'Unknown')})")
            else:
                logger.warning("FinancialAdvisor returned empty recommendation list")
            
            # Limit number of recommendations if configured
            max_recs = self.config.max_recommendations_per_category
            return recommendations[:max_recs] if max_recs > 0 else recommendations
            
        except Exception as e:
            logger.error(f"Error in financial recommendation generation: {str(e)}")
            return []
    
    def _generate_portfolio_recommendations(self,
                                          portfolio_data: Dict[str, Any],
                                          analysis_results: Dict[str, Any]) -> List[Any]:
        """Generate portfolio optimization recommendations"""
        try:
            logger.info("=== PORTFOLIO RECOMMENDATIONS GENERATION ===")
            logger.info(f"Portfolio data input: {type(portfolio_data)} with keys: {list(portfolio_data.keys()) if portfolio_data else 'None'}")
            logger.info(f"Analysis results input: {type(analysis_results)} with keys: {list(analysis_results.keys()) if analysis_results else 'None'}")
            
            # Validate input data
            if not portfolio_data:
                logger.warning("Portfolio data is empty or None")
                return []
            
            if not analysis_results:
                logger.warning("Analysis results is empty or None")
                return []
            
            # Generate recommendations using PortfolioAdvisor with full analysis_results
            logger.info("Calling PortfolioAdvisor.generate_recommendations...")
            recommendations = self.portfolio_advisor.generate_recommendations(
                portfolio_data, analysis_results
            )
            
            logger.info(f"PortfolioAdvisor returned {len(recommendations)} recommendations")
            if recommendations:
                for i, rec in enumerate(recommendations[:3], 1):  # Log first 3
                    logger.info(f"  {i}. {getattr(rec, 'title', 'No title')} (Type: {getattr(rec, 'type', 'Unknown')})")
            else:
                logger.warning("PortfolioAdvisor returned empty recommendation list")
            
            # Limit number of recommendations if configured
            max_recs = self.config.max_recommendations_per_category
            return recommendations[:max_recs] if max_recs > 0 else recommendations
            
        except Exception as e:
            logger.error(f"Error in portfolio recommendation generation: {str(e)}")
            return []
    
    def _generate_risk_recommendations(self,
                                     portfolio_data: Dict[str, Any], 
                                     analysis_results: Dict[str, Any]) -> List[Any]:
        """Generate risk management recommendations"""
        try:
            logger.info("=== RISK RECOMMENDATIONS GENERATION ===")
            logger.info(f"Portfolio data input: {type(portfolio_data)} with keys: {list(portfolio_data.keys()) if portfolio_data else 'None'}")
            logger.info(f"Analysis results input: {type(analysis_results)} with keys: {list(analysis_results.keys()) if analysis_results else 'None'}")
            
            # Validate input data
            if not portfolio_data:
                logger.warning("Portfolio data is empty or None")
                return []
            
            # Transform portfolio data to RiskAdvisor expected format
            risk_advisor_data = self._transform_portfolio_data_for_risk_advisor(portfolio_data)
            logger.info(f"Transformed portfolio data keys: {list(risk_advisor_data.keys())}")
            
            # Get historical performance results if available
            historical_performance_results = analysis_results.get('historical_performance')
            logger.info(f"Historical performance data available: {historical_performance_results is not None}")
            
            # Analyze portfolio risks with historical context
            logger.info("Calling RiskAdvisor.analyze_portfolio_risks...")
            risk_assessments = self.risk_advisor.analyze_portfolio_risks(
                risk_advisor_data, 
                analysis_results.get('market_data'),
                historical_performance_results
            )
            
            logger.info(f"RiskAdvisor.analyze_portfolio_risks returned {len(risk_assessments)} assessments")
            if risk_assessments:
                for i, assessment in enumerate(risk_assessments[:3], 1):
                    logger.info(f"  {i}. {getattr(assessment, 'category', 'Unknown')} - {getattr(assessment, 'level', 'Unknown')}")
            
            # Generate risk recommendations
            logger.info("Calling RiskAdvisor.generate_recommendations...")
            recommendations = self.risk_advisor.generate_recommendations(
                risk_assessments
            )
            
            logger.info(f"RiskAdvisor returned {len(recommendations)} recommendations")
            if recommendations:
                for i, rec in enumerate(recommendations[:3], 1):  # Log first 3
                    logger.info(f"  {i}. Priority {getattr(rec, 'priority', 'Unknown')}: {getattr(rec, 'action', 'No action')}")
            else:
                logger.warning("RiskAdvisor returned empty recommendation list")
            
            # Limit number of recommendations if configured
            max_recs = self.config.max_recommendations_per_category
            return recommendations[:max_recs] if max_recs > 0 else recommendations
            
        except Exception as e:
            logger.error(f"Error in risk recommendation generation: {str(e)}")
            return []
    
    def _transform_portfolio_data_for_risk_advisor(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform portfolio data to format expected by RiskAdvisor"""
        try:
            transformed_data = {}
            
            # Transform holdings_df to holdings with correct column names
            if 'holdings_df' in portfolio_data and portfolio_data['holdings_df'] is not None:
                holdings_df = portfolio_data['holdings_df'].copy()
                
                # Rename columns to match RiskAdvisor expectations
                column_mapping = {
                    'Market_Value_CNY': 'market_value',
                    'Asset_Name': 'symbol',
                    'Asset_Type': 'asset_type',
                    'Asset_Class': 'sector',
                    'Symbol': 'symbol',
                    'Quantity': 'quantity',
                    'Price_CNY': 'price'
                }
                
                # Apply column mappings that exist
                for old_col, new_col in column_mapping.items():
                    if old_col in holdings_df.columns:
                        holdings_df = holdings_df.rename(columns={old_col: new_col})
                
                # Ensure required columns exist
                if 'market_value' not in holdings_df.columns:
                    logger.warning("No market_value column found in holdings data")
                    return {}
                
                # Add missing columns with defaults if needed
                if 'symbol' not in holdings_df.columns:
                    holdings_df['symbol'] = holdings_df.index.astype(str)
                
                transformed_data['holdings'] = holdings_df
                logger.info(f"Transformed holdings_df: {len(holdings_df)} rows with columns {list(holdings_df.columns)}")
            
            # Copy other data as-is
            for key, value in portfolio_data.items():
                if key != 'holdings_df':
                    transformed_data[key] = value
            
            return transformed_data
            
        except Exception as e:
            logger.error(f"Error transforming portfolio data for risk advisor: {str(e)}")
            return {}
    
    def _prepare_user_preferences(self, user_preferences: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare user preferences for action prioritizer"""
        prefs = {
            'risk_tolerance': self.config.user_risk_tolerance,
            'time_availability': self.config.user_time_availability,
            'prioritize_risk': self.config.prioritize_risk_management
        }
        
        # Override with provided preferences
        if user_preferences:
            prefs.update(user_preferences)
        
        return prefs
    
    def _generate_tax_recommendations(self,
                                    portfolio_data: Dict[str, Any], 
                                    analysis_results: Dict[str, Any]) -> List[Any]:
        """Generate tax optimization recommendations"""
        try:
            logger.info("=== TAX RECOMMENDATIONS GENERATION ===")
            logger.info(f"Portfolio data input: {type(portfolio_data)} with keys: {list(portfolio_data.keys()) if portfolio_data else 'None'}")
            logger.info(f"Analysis results input: {type(analysis_results)} with keys: {list(analysis_results.keys()) if analysis_results else 'None'}")
            
            # Validate input data
            if not portfolio_data:
                logger.warning("Portfolio data is empty or None")
                return []
            
            # Extract cost basis calculators and current prices
            cost_basis_calculators = {}
            current_prices = {}
            
            # Try to get cost basis data from portfolio_data
            if 'cost_basis_calculators' in portfolio_data:
                cost_basis_calculators = portfolio_data['cost_basis_calculators']
            elif 'cost_basis_data' in portfolio_data:
                # If cost basis data is in different format, we might need to convert
                logger.info("Cost basis data found but not in calculator format")
                return []
            else:
                logger.warning("No cost basis data found in portfolio_data")
                return []
            
            # Try to get current prices
            if 'current_prices' in portfolio_data:
                current_prices = portfolio_data['current_prices']
            elif 'holdings_df' in portfolio_data and hasattr(portfolio_data['holdings_df'], 'index'):
                # Extract current prices from holdings DataFrame
                holdings_df = portfolio_data['holdings_df']
                if 'Current_Price' in holdings_df.columns and 'Asset_ID' in holdings_df.columns:
                    current_prices = dict(zip(holdings_df['Asset_ID'], holdings_df['Current_Price']))
                else:
                    logger.warning("Holdings DataFrame missing required price columns")
                    return []
            else:
                logger.warning("No current price data found in portfolio_data")
                return []
            
            logger.info(f"Found cost basis calculators for {len(cost_basis_calculators)} assets")
            logger.info(f"Found current prices for {len(current_prices)} assets")
            
            # Get rebalancing actions if available
            rebalancing_actions = analysis_results.get('rebalancing_actions')
            if rebalancing_actions:
                logger.info(f"Found rebalancing actions for {len(rebalancing_actions)} assets")
            
            # Generate tax recommendations
            logger.info("Calling TaxAdvisor.analyze_tax_implications...")
            recommendations = self.tax_advisor.analyze_tax_implications(
                cost_basis_calculators=cost_basis_calculators,
                current_prices=current_prices,
                rebalancing_actions=rebalancing_actions
            )
            
            logger.info(f"TaxAdvisor returned {len(recommendations)} recommendations")
            if recommendations:
                for i, rec in enumerate(recommendations[:3], 1):  # Log first 3
                    logger.info(f"  {i}. {rec.recommendation_type}: {rec.asset_id} - {rec.action}")
            else:
                logger.info("TaxAdvisor returned empty recommendation list")
            
            # Limit number of recommendations if configured
            max_recs = self.config.max_recommendations_per_category
            return recommendations[:max_recs] if max_recs > 0 else recommendations
            
        except Exception as e:
            logger.error(f"Error in tax recommendation generation: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    def _generate_recommendation_summary(self,
                                       financial_recs: List[Any],
                                       portfolio_recs: List[Any],
                                       risk_recs: List[Any],
                                       tax_recs: List[Any],
                                       action_plan: ActionPlan) -> Dict[str, Any]:
        """Generate overall recommendation summary"""
        
        # Count high-priority recommendations
        high_priority_count = len([
            action for action in action_plan.immediate_actions + action_plan.short_term_actions
            if action.priority_score > 5.0
        ])
        
        # Identify key focus areas
        focus_areas = []
        if financial_recs:
            focus_areas.append("Financial Health")
        if portfolio_recs:
            focus_areas.append("Portfolio Optimization")
        if risk_recs:
            focus_areas.append("Risk Management")
        if tax_recs:
            focus_areas.append("Tax Optimization")
        
        # Determine overall recommendation theme
        total_actions = action_plan.summary.get('total_actions', 0)
        
        if total_actions == 0:
            theme = "Portfolio Maintenance"
        elif high_priority_count > 3:
            theme = "Active Portfolio Management Required"
        elif len(risk_recs) > len(financial_recs) + len(portfolio_recs) + len(tax_recs):
            theme = "Risk Management Focus"
        elif len(portfolio_recs) > len(financial_recs) + len(tax_recs):
            theme = "Portfolio Optimization Focus"
        elif len(tax_recs) > len(financial_recs) + len(portfolio_recs):
            theme = "Tax Optimization Focus"
        else:
            theme = "Balanced Financial Improvement"
        
        return {
            "overall_theme": theme,
            "focus_areas": focus_areas,
            "total_recommendations": len(financial_recs) + len(portfolio_recs) + len(risk_recs) + len(tax_recs),
            "high_priority_actions": high_priority_count,
            "immediate_actions_required": len(action_plan.immediate_actions),
            "estimated_implementation_timeline": self._estimate_implementation_timeline(action_plan),
            "key_benefits": self._identify_key_benefits(financial_recs, portfolio_recs, risk_recs, tax_recs),
            "complexity_level": self._assess_complexity_level(action_plan)
        }
    
    def _estimate_implementation_timeline(self, action_plan: ActionPlan) -> str:
        """Estimate overall implementation timeline"""
        immediate = len(action_plan.immediate_actions)
        short_term = len(action_plan.short_term_actions)
        medium_term = len(action_plan.medium_term_actions)
        
        if immediate > 3:
            return "2-4 weeks for immediate actions, 3-6 months for complete implementation"
        elif short_term > 5:
            return "1-3 months for major changes, 6-12 months for complete implementation"
        elif medium_term > 5:
            return "3-6 months for most changes, up to 12 months for complete implementation"
        else:
            return "6-12 months for gradual implementation"
    
    def _identify_key_benefits(self, financial_recs: List[Any], 
                             portfolio_recs: List[Any], 
                             risk_recs: List[Any],
                             tax_recs: List[Any]) -> List[str]:
        """Identify key benefits from implementing recommendations"""
        benefits = []
        
        if financial_recs:
            benefits.append("Improved financial health and cash flow")
        if portfolio_recs:
            benefits.append("Enhanced portfolio performance and efficiency")
        if risk_recs:
            benefits.append("Reduced portfolio risk and increased stability")
        if tax_recs:
            benefits.append("Optimized tax efficiency and after-tax returns")
        
        # Add specific benefits based on recommendation types
        if len(portfolio_recs) > 3:
            benefits.append("Better diversification and risk-adjusted returns")
        if len(risk_recs) > 2:
            benefits.append("Enhanced downside protection")
        if len(tax_recs) > 2:
            benefits.append("Significant tax savings opportunities")
        
        return benefits[:4]  # Limit to top 4 benefits
    
    def _assess_complexity_level(self, action_plan: ActionPlan) -> str:
        """Assess overall complexity of implementation"""
        total_actions = action_plan.summary.get('total_actions', 0)
        high_effort_actions = 0
        
        for action_list in [action_plan.immediate_actions, action_plan.short_term_actions, 
                           action_plan.medium_term_actions]:
            high_effort_actions += len([
                action for action in action_list 
                if action.effort_required.lower() == 'high'
            ])
        
        if total_actions > 15 or high_effort_actions > 5:
            return "High - Consider phased implementation"
        elif total_actions > 8 or high_effort_actions > 2:
            return "Medium - Manageable with planning"
        else:
            return "Low - Straightforward implementation"
    
    def get_quick_recommendations(self, 
                                analysis_results: Dict[str, Any],
                                max_recommendations: int = 5) -> Dict[str, Any]:
        """
        Generate quick top-priority recommendations
        
        Args:
            analysis_results: Results from unified analysis
            max_recommendations: Maximum number of recommendations to return
            
        Returns:
            Quick recommendation summary
        """
        try:
            # Extract key data
            financial_data = analysis_results.get('financial_analysis', {})
            portfolio_data = analysis_results.get('portfolio_analysis', {})
            
            # Generate a subset of recommendations
            config = RecommendationEngineConfig(
                max_recommendations_per_category=3  # Limit for quick analysis
            )
            
            temp_engine = ComprehensiveRecommendationEngine(config)
            result = temp_engine.generate_recommendations(
                financial_data, portfolio_data, analysis_results
            )
            
            # Extract top recommendations
            all_actions = (
                result.prioritized_action_plan.immediate_actions + 
                result.prioritized_action_plan.short_term_actions
            )
            
            top_actions = sorted(all_actions, key=lambda x: x.priority_score, reverse=True)[:max_recommendations]
            
            return {
                "top_recommendations": [
                    {
                        "title": action.title,
                        "description": action.description,
                        "priority_score": action.priority_score,
                        "timeline": action.timeline,
                        "category": action.category.value
                    }
                    for action in top_actions
                ],
                "summary": result.summary,
                "recommendation_count": len(top_actions)
            }
            
        except Exception as e:
            logger.error(f"Error generating quick recommendations: {str(e)}")
            return {
                "top_recommendations": [],
                "summary": {"error": str(e)},
                "recommendation_count": 0
            }
    
    def _create_fallback_financial_recommendations(self) -> List[Any]:
        """Create fallback financial recommendations when none are generated"""
        from .financial_advisor import FinancialRecommendation, RecommendationType, RecommendationUrgency
        
        logger.info("Creating fallback financial recommendations")
        return [
            FinancialRecommendation(
                id="fallback_financial_1",
                type=RecommendationType.CASH_FLOW,
                title="Review Financial Data",
                description="Insufficient data available for detailed financial analysis. Consider reviewing and updating your financial records.",
                urgency=RecommendationUrgency.MEDIUM,
                impact_score=50.0,
                ease_score=80.0,
                action_steps=[
                    "Verify all income and expense categories are properly recorded",
                    "Ensure balance sheet data is current and complete",
                    "Review data formatting and completeness"
                ]
            )
        ]
    
    def _create_fallback_portfolio_recommendations(self) -> List[Any]:
        """Create fallback portfolio recommendations when none are generated"""
        from .portfolio_advisor import PortfolioRecommendation, PortfolioRecommendationType
        
        logger.info("Creating fallback portfolio recommendations")
        return [
            PortfolioRecommendation(
                id="fallback_portfolio_1",
                type=PortfolioRecommendationType.ASSET_ALLOCATION,
                title="Portfolio Review Required", 
                description="Unable to generate specific portfolio recommendations due to insufficient data or analysis constraints.",
                urgency="medium",
                impact_score=60.0,
                ease_score=70.0,
                action_steps=[
                    "Verify portfolio holdings data is complete and current",
                    "Ensure transaction history is properly recorded",
                    "Check asset classification and mapping"
                ]
            )
        ]
