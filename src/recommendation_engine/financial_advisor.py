"""
Financial Advisor Module

Provides financial health recommendations including cash flow optimization,
debt management, emergency fund analysis, and savings strategies.
"""

import pandas as pd
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecommendationType(Enum):
    """Types of financial recommendations"""
    CASH_FLOW = "cash_flow"
    DEBT_MANAGEMENT = "debt_management"
    EMERGENCY_FUND = "emergency_fund"
    SAVINGS_RATE = "savings_rate"
    INCOME_OPTIMIZATION = "income_optimization"
    EXPENSE_REDUCTION = "expense_reduction"

class RecommendationUrgency(Enum):
    """Urgency levels for recommendations"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class FinancialRecommendation:
    """Financial recommendation data structure"""
    id: str
    type: RecommendationType
    title: str
    description: str
    urgency: RecommendationUrgency
    impact_score: float  # 0-100 scale
    ease_score: float    # 0-100 scale (higher = easier)
    estimated_benefit: Optional[float] = None  # CNY amount
    implementation_time: Optional[str] = None  # e.g., "1 week", "3 months"
    prerequisites: List[str] = None
    action_steps: List[str] = None
    
    def __post_init__(self):
        if self.prerequisites is None:
            self.prerequisites = []
        if self.action_steps is None:
            self.action_steps = []

class FinancialAdvisor:
    """
    Generates financial health recommendations based on analysis results
    """
    
    def __init__(self):
        self.recommendations = []
        
    def analyze_financial_health(self, 
                                balance_sheet_df: pd.DataFrame,
                                monthly_df: pd.DataFrame,
                                financial_analysis_results: Dict[str, Any],
                                historical_performance_results: Dict[str, Any] = None) -> List[FinancialRecommendation]:
        """
        Generate comprehensive financial health recommendations
        
        Args:
            balance_sheet_df: Balance sheet data
            monthly_df: Monthly income/expense data
            financial_analysis_results: Results from financial analysis module
            historical_performance_results: Historical performance and trend analysis results
            
        Returns:
            List of financial recommendations
        """
        
        recommendations = []
        
        try:
            # Analyze different aspects of financial health with historical context
            recommendations.extend(self._analyze_cash_flow(monthly_df, financial_analysis_results))
            recommendations.extend(self._analyze_emergency_fund(balance_sheet_df, monthly_df))
            recommendations.extend(self._analyze_debt_situation(balance_sheet_df, historical_performance_results))
            recommendations.extend(self._analyze_savings_rate(monthly_df, financial_analysis_results, historical_performance_results))
            recommendations.extend(self._analyze_income_sources(monthly_df))
            
            # Add new historical trend-based recommendations
            if historical_performance_results:
                recommendations.extend(self._analyze_historical_trends(historical_performance_results))
                recommendations.extend(self._analyze_net_worth_trends(historical_performance_results))
            
        except Exception as e:
            # Add error recommendation
            error_rec = FinancialRecommendation(
                id="financial_analysis_error",
                type=RecommendationType.CASH_FLOW,
                title="Financial Analysis Error",
                description=f"Error analyzing financial data: {str(e)}",
                urgency=RecommendationUrgency.MEDIUM,
                impact_score=0,
                ease_score=0
            )
            recommendations.append(error_rec)
        
        self.recommendations = recommendations
        return recommendations
    
    def _analyze_cash_flow(self, monthly_df: pd.DataFrame, 
                          financial_results: Dict[str, Any]) -> List[FinancialRecommendation]:
        """Analyze cash flow patterns and generate recommendations"""
        
        recommendations = []
        
        try:
            if monthly_df is None or monthly_df.empty:
                return recommendations
            
            # Calculate recent cash flow metrics
            recent_months = monthly_df.tail(6)  # Last 6 months
            
            if 'Net_Cash_Flow_CNY' in recent_months.columns:
                avg_cash_flow = recent_months['Net_Cash_Flow_CNY'].mean()
                cash_flow_volatility = recent_months['Net_Cash_Flow_CNY'].std()
                negative_months = (recent_months['Net_Cash_Flow_CNY'] < 0).sum()
                
                # Negative cash flow recommendation
                if avg_cash_flow < 0:
                    recommendations.append(FinancialRecommendation(
                        id="negative_cash_flow",
                        type=RecommendationType.CASH_FLOW,
                        title="Address Negative Cash Flow",
                        description=f"Average monthly cash flow is negative (¥{avg_cash_flow:,.0f}). "
                                  f"This indicates spending exceeds income and needs immediate attention.",
                        urgency=RecommendationUrgency.CRITICAL,
                        impact_score=90,
                        ease_score=60,
                        estimated_benefit=abs(avg_cash_flow) * 12,
                        implementation_time="1-3 months",
                        action_steps=[
                            "Review detailed expense breakdown to identify areas for reduction",
                            "Look for opportunities to increase income",
                            "Create a strict budget and track spending daily",
                            "Consider temporary lifestyle adjustments"
                        ]
                    ))
                
                # Cash flow volatility recommendation
                if cash_flow_volatility > abs(avg_cash_flow) * 0.5:
                    recommendations.append(FinancialRecommendation(
                        id="cash_flow_volatility",
                        type=RecommendationType.CASH_FLOW,
                        title="Stabilize Cash Flow Volatility",
                        description=f"Cash flow shows high volatility (σ=¥{cash_flow_volatility:,.0f}). "
                                  f"Consider strategies to smooth income and expenses.",
                        urgency=RecommendationUrgency.MEDIUM,
                        impact_score=60,
                        ease_score=70,
                        implementation_time="3-6 months",
                        action_steps=[
                            "Build up emergency fund to handle volatility",
                            "Explore more stable income sources",
                            "Consider averaging variable expenses",
                            "Set up automatic savings during high cash flow months"
                        ]
                    ))
                
                # Positive cash flow optimization
                if avg_cash_flow > 0:
                    recommendations.append(FinancialRecommendation(
                        id="optimize_surplus",
                        type=RecommendationType.SAVINGS_RATE,
                        title="Optimize Cash Flow Surplus",
                        description=f"Positive average cash flow of ¥{avg_cash_flow:,.0f} per month. "
                                  f"Ensure this surplus is being used effectively for wealth building.",
                        urgency=RecommendationUrgency.MEDIUM,
                        impact_score=70,
                        ease_score=80,
                        estimated_benefit=avg_cash_flow * 12 * 0.05,  # 5% investment return
                        implementation_time="1 month",
                        action_steps=[
                            "Automate transfers to investment accounts",
                            "Review and optimize investment allocation",
                            "Consider increasing retirement contributions",
                            "Evaluate tax-advantaged saving opportunities"
                        ]
                    ))
        
        except Exception as e:
            # Fallback recommendation for analysis errors
            recommendations.append(FinancialRecommendation(
                id="cash_flow_analysis_error",
                type=RecommendationType.CASH_FLOW,
                title="Cash Flow Analysis Needed",
                description=f"Unable to analyze cash flow patterns: {str(e)}. "
                          f"Manual review of income and expenses recommended.",
                urgency=RecommendationUrgency.LOW,
                impact_score=30,
                ease_score=90
            ))
        
        return recommendations
    
    def _analyze_emergency_fund(self, balance_sheet_df: pd.DataFrame,
                               monthly_df: pd.DataFrame) -> List[FinancialRecommendation]:
        """Analyze emergency fund adequacy"""
        
        recommendations = []
        
        try:
            if balance_sheet_df is None or balance_sheet_df.empty or monthly_df is None:
                return recommendations
            
            # Get current liquid assets (cash and cash equivalents)
            current_assets = balance_sheet_df.iloc[-1]
            liquid_assets = 0
            
            # Look for cash/liquid asset columns
            cash_columns = [col for col in current_assets.index if 
                          any(keyword in col.lower() for keyword in ['cash', 'deposit', 'liquid', '现金', '存款'])]
            
            if cash_columns:
                liquid_assets = sum([current_assets[col] for col in cash_columns 
                                   if pd.notna(current_assets[col])])
            
            # Calculate monthly expenses
            recent_expenses = monthly_df.tail(6)
            if 'Expense_CNY' in recent_expenses.columns:
                avg_monthly_expenses = recent_expenses['Expense_CNY'].mean()
                
                if avg_monthly_expenses > 0:
                    months_covered = liquid_assets / avg_monthly_expenses
                    
                    if months_covered < 3:
                        recommendations.append(FinancialRecommendation(
                            id="insufficient_emergency_fund",
                            type=RecommendationType.EMERGENCY_FUND,
                            title="Build Emergency Fund",
                            description=f"Current liquid assets (¥{liquid_assets:,.0f}) cover only "
                                      f"{months_covered:.1f} months of expenses. Recommend 3-6 months.",
                            urgency=RecommendationUrgency.HIGH,
                            impact_score=85,
                            ease_score=70,
                            estimated_benefit=(3 * avg_monthly_expenses) - liquid_assets,
                            implementation_time="6-12 months",
                            action_steps=[
                                f"Set target emergency fund of ¥{3 * avg_monthly_expenses:,.0f}",
                                "Open high-yield savings account for emergency fund",
                                f"Automate monthly savings of ¥{((3 * avg_monthly_expenses) - liquid_assets) / 12:,.0f}",
                                "Keep emergency fund separate from investment accounts"
                            ]
                        ))
                    
                    elif months_covered > 12:
                        recommendations.append(FinancialRecommendation(
                            id="excess_emergency_fund",
                            type=RecommendationType.EMERGENCY_FUND,
                            title="Optimize Excess Emergency Fund",
                            description=f"Emergency fund covers {months_covered:.1f} months of expenses. "
                                      f"Consider investing excess beyond 6-month target.",
                            urgency=RecommendationUrgency.LOW,
                            impact_score=40,
                            ease_score=80,
                            estimated_benefit=(liquid_assets - (6 * avg_monthly_expenses)) * 0.05,
                            implementation_time="1 month",
                            action_steps=[
                                f"Keep ¥{6 * avg_monthly_expenses:,.0f} in emergency fund",
                                f"Consider investing excess ¥{liquid_assets - (6 * avg_monthly_expenses):,.0f}",
                                "Review investment allocation for excess funds",
                                "Maintain easy access to core emergency fund"
                            ]
                        ))
        
        except Exception as e:
            recommendations.append(FinancialRecommendation(
                id="emergency_fund_analysis_error",
                type=RecommendationType.EMERGENCY_FUND,
                title="Emergency Fund Review Needed",
                description=f"Unable to analyze emergency fund: {str(e)}. Manual review recommended.",
                urgency=RecommendationUrgency.LOW,
                impact_score=30,
                ease_score=90
            ))
        
        return recommendations
    
    def _analyze_debt_situation(self, balance_sheet_df: pd.DataFrame, 
                               historical_performance_results: Dict[str, Any] = None) -> List[FinancialRecommendation]:
        """Analyze debt levels and repayment strategies"""
        
        recommendations = []
        
        try:
            if balance_sheet_df is None or balance_sheet_df.empty:
                return recommendations
            
            current_position = balance_sheet_df.iloc[-1]
            
            # Look for liability columns
            if 'Total_Liabilities_CNY' in current_position.index:
                total_liabilities = current_position['Total_Liabilities_CNY']
                
                if pd.notna(total_liabilities) and total_liabilities > 0:
                    
                    # Get total assets for debt-to-asset ratio
                    if 'Total_Assets_CNY' in current_position.index:
                        total_assets = current_position['Total_Assets_CNY']
                        debt_to_asset_ratio = total_liabilities / total_assets if total_assets > 0 else 0
                        
                        # Use historical trends if available
                        historical_context = ""
                        trend_urgency_modifier = 0
                        
                        if (historical_performance_results and 
                            'trend_analysis' in historical_performance_results and
                            'debt_to_asset_ratio' in historical_performance_results['trend_analysis']):
                            
                            debt_trend = historical_performance_results['trend_analysis']['debt_to_asset_ratio']
                            if 'error' not in debt_trend:
                                trend_direction = debt_trend.get('trend_direction', 'Unknown')
                                cagr = debt_trend.get('cagr', 0)
                                
                                if trend_direction == "Increasing":
                                    historical_context = f" Historical trend shows debt ratio increasing at {abs(cagr*100):.1f}% annually - urgent action needed."
                                    trend_urgency_modifier = 1
                                elif trend_direction == "Decreasing":
                                    historical_context = f" Good progress: debt ratio decreasing at {abs(cagr*100):.1f}% annually."
                                    trend_urgency_modifier = -1
                        
                        if debt_to_asset_ratio > 0.4:  # High debt ratio
                            urgency = RecommendationUrgency.HIGH
                            if trend_urgency_modifier > 0:
                                urgency = RecommendationUrgency.CRITICAL
                                
                            recommendations.append(FinancialRecommendation(
                                id="high_debt_ratio",
                                type=RecommendationType.DEBT_MANAGEMENT,
                                title="Reduce High Debt-to-Asset Ratio",
                                description=f"Debt-to-asset ratio is {debt_to_asset_ratio:.1%}, which is relatively high. "
                                          f"Consider debt reduction strategies.{historical_context}",
                                urgency=urgency,
                                impact_score=80 + (trend_urgency_modifier * 10),
                                ease_score=50,
                                estimated_benefit=total_liabilities * 0.05,  # Interest savings
                                implementation_time="12-24 months",
                                action_steps=[
                                    "List all debts with interest rates and balances",
                                    "Prioritize paying off highest interest rate debts first",
                                    "Consider debt consolidation options",
                                    "Allocate extra cash flow to debt repayment",
                                    "Avoid taking on new debt"
                                ]
                            ))
                        
                        elif debt_to_asset_ratio < 0.1 and total_liabilities > 50000:
                            recommendations.append(FinancialRecommendation(
                                id="low_leverage_opportunity",
                                type=RecommendationType.DEBT_MANAGEMENT,
                                title="Consider Strategic Leverage",
                                description=f"Very low debt ratio ({debt_to_asset_ratio:.1%}). "
                                          f"Consider strategic borrowing for investments if rates are favorable.{historical_context}",
                                urgency=RecommendationUrgency.LOW,
                                impact_score=30,
                                ease_score=40,
                                implementation_time="3-6 months",
                                action_steps=[
                                    "Compare borrowing rates to expected investment returns",
                                    "Consider mortgage or investment property financing",
                                    "Evaluate tax benefits of certain types of debt",
                                    "Maintain conservative approach to leverage"
                                ]
                            ))
        
        except Exception as e:
            recommendations.append(FinancialRecommendation(
                id="debt_analysis_error",
                type=RecommendationType.DEBT_MANAGEMENT,
                title="Debt Analysis Review Needed",
                description=f"Unable to analyze debt situation: {str(e)}. Manual review recommended.",
                urgency=RecommendationUrgency.LOW,
                impact_score=30,
                ease_score=90
            ))
        
        return recommendations
    
    def _analyze_savings_rate(self, monthly_df: pd.DataFrame,
                             financial_results: Dict[str, Any],
                             historical_performance_results: Dict[str, Any] = None) -> List[FinancialRecommendation]:
        """Analyze savings rate and provide improvement recommendations"""
        
        recommendations = []
        
        try:
            if monthly_df is None or monthly_df.empty:
                return recommendations
            
            recent_months = monthly_df.tail(12)  # Last 12 months
            
            if 'Income_CNY' in recent_months.columns and 'Expense_CNY' in recent_months.columns:
                total_income = recent_months['Income_CNY'].sum()
                total_expenses = recent_months['Expense_CNY'].sum()
                
                if total_income > 0:
                    savings_rate = (total_income - total_expenses) / total_income
                    
                    # Get historical savings rate trend if available
                    historical_context = ""
                    trend_modifier = 0
                    
                    if (historical_performance_results and 
                        'trend_analysis' in historical_performance_results and
                        'savings_rate' in historical_performance_results['trend_analysis']):
                        
                        savings_trend = historical_performance_results['trend_analysis']['savings_rate']
                        if 'error' not in savings_trend:
                            trend_direction = savings_trend.get('trend_direction', 'Unknown')
                            cagr = savings_trend.get('cagr', 0)
                            
                            if trend_direction == "Increasing":
                                historical_context = f" Excellent: savings rate has been improving by {abs(cagr*100):.1f}% annually."
                                trend_modifier = 10
                            elif trend_direction == "Decreasing":
                                historical_context = f" Concerning: savings rate has been declining by {abs(cagr*100):.1f}% annually."
                                trend_modifier = -10
                    
                    if savings_rate < 0.1:  # Less than 10% savings rate
                        urgency = RecommendationUrgency.HIGH
                        if trend_modifier < 0:  # Declining trend makes it more urgent
                            urgency = RecommendationUrgency.CRITICAL
                            
                        recommendations.append(FinancialRecommendation(
                            id="low_savings_rate",
                            type=RecommendationType.SAVINGS_RATE,
                            title="Improve Savings Rate",
                            description=f"Current savings rate is {savings_rate:.1%}, which is below the "
                                      f"recommended 15-20%. Focus on increasing savings.{historical_context}",
                            urgency=urgency,
                            impact_score=85 + abs(trend_modifier),
                            ease_score=65,
                            estimated_benefit=(0.15 - savings_rate) * total_income,
                            implementation_time="3-6 months",
                            action_steps=[
                                "Set target savings rate of 15-20%",
                                "Automate savings transfers on payday",
                                "Review and reduce non-essential expenses",
                                "Track spending to identify savings opportunities",
                                "Consider the 50/30/20 budgeting rule"
                            ]
                        ))
                    
                    elif savings_rate > 0.3:  # Very high savings rate
                        recommendations.append(FinancialRecommendation(
                            id="high_savings_rate",
                            type=RecommendationType.SAVINGS_RATE,
                            title="Optimize High Savings Rate",
                            description=f"Excellent savings rate of {savings_rate:.1%}! "
                                      f"Ensure savings are optimally invested for growth.{historical_context}",
                            urgency=RecommendationUrgency.LOW,
                            impact_score=50 + max(0, trend_modifier),
                            ease_score=80,
                            implementation_time="1 month",
                            action_steps=[
                                "Review investment allocation of savings",
                                "Consider tax-advantaged accounts",
                                "Balance current vs future consumption",
                                "Ensure emergency fund is adequate first"
                            ]
                        ))
        
        except Exception as e:
            recommendations.append(FinancialRecommendation(
                id="savings_rate_analysis_error",
                type=RecommendationType.SAVINGS_RATE,
                title="Savings Rate Analysis Needed",
                description=f"Unable to analyze savings rate: {str(e)}. Manual calculation recommended.",
                urgency=RecommendationUrgency.LOW,
                impact_score=30,
                ease_score=90
            ))
        
        return recommendations
    
    def _analyze_income_sources(self, monthly_df: pd.DataFrame) -> List[FinancialRecommendation]:
        """Analyze income diversification and optimization opportunities"""
        
        recommendations = []
        
        try:
            if monthly_df is None or monthly_df.empty:
                return recommendations
            
            # Look for passive income indicators
            income_columns = [col for col in monthly_df.columns if 
                            any(keyword in col.lower() for keyword in ['income', 'dividend', 'interest', '收入', '分红'])]
            
            if income_columns:
                recent_months = monthly_df.tail(6)
                
                # Analyze income stability and diversification
                # This is a simplified analysis - could be expanded based on actual data structure
                if 'Income_CNY' in recent_months.columns:
                    income_volatility = recent_months['Income_CNY'].std()
                    avg_income = recent_months['Income_CNY'].mean()
                    
                    if avg_income > 0 and income_volatility / avg_income > 0.2:
                        recommendations.append(FinancialRecommendation(
                            id="income_volatility",
                            type=RecommendationType.INCOME_OPTIMIZATION,
                            title="Diversify Income Sources",
                            description=f"Income shows high volatility (CV={income_volatility/avg_income:.1%}). "
                                      f"Consider developing more stable income streams.",
                            urgency=RecommendationUrgency.MEDIUM,
                            impact_score=60,
                            ease_score=40,
                            implementation_time="6-12 months",
                            action_steps=[
                                "Develop passive income sources",
                                "Consider side business or freelancing",
                                "Build dividend-paying investment portfolio",
                                "Explore skill development for income growth"
                            ]
                        ))
        
        except Exception as e:
            # This is optional analysis, so don't add error recommendations
            pass
        
        return recommendations
    
    def get_recommendations_by_urgency(self, urgency: RecommendationUrgency) -> List[FinancialRecommendation]:
        """Get recommendations filtered by urgency level"""
        return [rec for rec in self.recommendations if rec.urgency == urgency]
    
    def get_recommendations_by_type(self, rec_type: RecommendationType) -> List[FinancialRecommendation]:
        """Get recommendations filtered by type"""
        return [rec for rec in self.recommendations if rec.type == rec_type]
    
    def generate_recommendations(self, financial_data: Dict[str, Any], 
                               analysis_results: Dict[str, Any]) -> List[FinancialRecommendation]:
        """
        Generate financial recommendations based on data and analysis
        
        Args:
            financial_data: Dictionary containing raw DataFrames
            analysis_results: Dictionary containing analysis results
            
        Returns:
            List of financial recommendations
        """
        recommendations = []
        
        try:
            # Extract DataFrames from financial_data
            balance_sheet_df = financial_data.get('balance_sheet_df')
            monthly_df = financial_data.get('monthly_df')
            
            # Extract analysis results
            financial_analysis = analysis_results.get('financial_analysis', {})
            
            # Generate practical recommendations based on real data
            recommendations.extend(self._generate_cash_flow_recommendations(monthly_df, financial_analysis))
            recommendations.extend(self._generate_emergency_fund_recommendations(balance_sheet_df, monthly_df))
            recommendations.extend(self._generate_debt_recommendations(balance_sheet_df))
            recommendations.extend(self._generate_savings_recommendations(monthly_df, financial_analysis))
            
            logger.info(f"Generated {len(recommendations)} financial recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating financial recommendations: {str(e)}")
            # Return at least one meaningful recommendation
            return [FinancialRecommendation(
                id="data_review_needed",
                type=RecommendationType.CASH_FLOW,
                title="Review Financial Data Quality",
                description=f"Unable to analyze financial data due to: {str(e)}. Please verify data completeness.",
                urgency=RecommendationUrgency.MEDIUM,
                impact_score=50,
                ease_score=90,
                action_steps=[
                    "Check that Excel files are properly formatted",
                    "Verify all required worksheets are present",
                    "Ensure dates and numbers are in correct format",
                    "Review data for missing or corrupted entries"
                ]
            )]
    
    def _generate_cash_flow_recommendations(self, monthly_df: pd.DataFrame, 
                                          financial_analysis: Dict[str, Any]) -> List[FinancialRecommendation]:
        """Generate cash flow related recommendations"""
        recommendations = []
        
        try:
            if monthly_df is None or monthly_df.empty:
                return recommendations
            
            # Calculate key metrics from monthly data
            if 'Net_Cash_Flow_CNY' in monthly_df.columns:
                recent_months = monthly_df.tail(6)
                avg_cash_flow = recent_months['Net_Cash_Flow_CNY'].mean()
                
                # Negative cash flow recommendation
                if avg_cash_flow < 0:
                    recommendations.append(FinancialRecommendation(
                        id="improve_cash_flow",
                        type=RecommendationType.CASH_FLOW,
                        title="Improve Monthly Cash Flow",
                        description=f"Average monthly cash flow is negative (¥{avg_cash_flow:,.0f}). "
                                  f"Focus on expense reduction and income optimization.",
                        urgency=RecommendationUrgency.HIGH,
                        impact_score=85,
                        ease_score=70,
                        estimated_benefit=abs(avg_cash_flow) * 12,
                        implementation_time="1-3 months",
                        action_steps=[
                            "Review monthly expenses for reduction opportunities",
                            "Consider additional income sources",
                            "Create detailed budget tracking",
                            "Set spending limits for discretionary categories"
                        ]
                    ))
                
                # Cash flow volatility analysis
                cash_flow_std = recent_months['Net_Cash_Flow_CNY'].std()
                if cash_flow_std > abs(avg_cash_flow) * 0.3 and avg_cash_flow > 0:
                    recommendations.append(FinancialRecommendation(
                        id="stabilize_cash_flow",
                        type=RecommendationType.CASH_FLOW,
                        title="Stabilize Income and Expenses",
                        description=f"Cash flow volatility is high (σ=¥{cash_flow_std:,.0f}). "
                                  f"Consider strategies to smooth income and expenses.",
                        urgency=RecommendationUrgency.MEDIUM,
                        impact_score=60,
                        ease_score=50,
                        implementation_time="3-6 months",
                        action_steps=[
                            "Build budget buffer for variable expenses",
                            "Explore more stable income sources",
                            "Consider automatic investment to smooth cash flow",
                            "Plan for seasonal expense variations"
                        ]
                    ))
            
        except Exception as e:
            logger.warning(f"Error analyzing cash flow: {str(e)}")
        
        return recommendations
    
    def _generate_emergency_fund_recommendations(self, balance_sheet_df: pd.DataFrame,
                                               monthly_df: pd.DataFrame) -> List[FinancialRecommendation]:
        """Generate emergency fund recommendations"""
        recommendations = []
        
        try:
            if balance_sheet_df is None or monthly_df is None:
                return recommendations
            
            # Get current liquid assets (cash + deposits)
            current_balance = balance_sheet_df.iloc[-1] if not balance_sheet_df.empty else pd.Series()
            liquid_assets = 0
            
            # Sum up cash and deposit columns
            for col in current_balance.index:
                if any(keyword in col.lower() for keyword in ['cash', 'deposit', '现金', '存款']):
                    if pd.notna(current_balance[col]):
                        liquid_assets += current_balance[col]
            
            # Get average monthly expenses
            if 'Total_Expenses_CNY' in monthly_df.columns:
                recent_expenses = monthly_df['Total_Expenses_CNY'].tail(6)
                avg_monthly_expenses = recent_expenses.mean()
                
                if avg_monthly_expenses > 0:
                    months_covered = liquid_assets / avg_monthly_expenses
                    target_months = 6
                    
                    if months_covered < target_months:
                        shortfall = (target_months - months_covered) * avg_monthly_expenses
                        
                        recommendations.append(FinancialRecommendation(
                            id="build_emergency_fund",
                            type=RecommendationType.EMERGENCY_FUND,
                            title="Build Adequate Emergency Fund",
                            description=f"Current emergency fund covers {months_covered:.1f} months of expenses. "
                                      f"Target: {target_months} months (¥{target_months * avg_monthly_expenses:,.0f}). "
                                      f"Shortfall: ¥{shortfall:,.0f}",
                            urgency=RecommendationUrgency.HIGH if months_covered < 3 else RecommendationUrgency.MEDIUM,
                            impact_score=80,
                            ease_score=70,
                            estimated_benefit=shortfall,
                            implementation_time="6-12 months",
                            action_steps=[
                                f"Save additional ¥{shortfall/12:,.0f} per month",
                                "Open separate high-yield savings account",
                                "Set up automatic monthly transfers",
                                "Keep funds easily accessible but separate from daily banking"
                            ]
                        ))
                    
                    elif months_covered > 12:
                        excess = (months_covered - 6) * avg_monthly_expenses
                        recommendations.append(FinancialRecommendation(
                            id="optimize_excess_emergency_fund",
                            type=RecommendationType.EMERGENCY_FUND,
                            title="Invest Excess Emergency Fund",
                            description=f"Emergency fund covers {months_covered:.1f} months - above optimal range. "
                                      f"Consider investing excess ¥{excess:,.0f} for better returns.",
                            urgency=RecommendationUrgency.LOW,
                            impact_score=40,
                            ease_score=60,
                            estimated_benefit=excess * 0.05,  # Assume 5% investment return
                            implementation_time="1 month",
                            action_steps=[
                                f"Keep ¥{6 * avg_monthly_expenses:,.0f} in emergency fund",
                                f"Invest excess ¥{excess:,.0f} in diversified portfolio",
                                "Consider low-risk investment options for excess funds",
                                "Maintain quick access to core emergency fund"
                            ]
                        ))
            
        except Exception as e:
            logger.warning(f"Error analyzing emergency fund: {str(e)}")
        
        return recommendations
    
    def _generate_debt_recommendations(self, balance_sheet_df: pd.DataFrame) -> List[FinancialRecommendation]:
        """Generate debt management recommendations"""
        recommendations = []
        
        try:
            if balance_sheet_df is None or balance_sheet_df.empty:
                return recommendations
            
            current_balance = balance_sheet_df.iloc[-1]
            total_liabilities = 0
            total_assets = 0
            
            # Sum up liability and asset columns
            for col in current_balance.index:
                if 'liabilit' in col.lower() or '负债' in col.lower():
                    if pd.notna(current_balance[col]):
                        total_liabilities += current_balance[col]
                elif any(keyword in col.lower() for keyword in ['asset', 'value', '资产', '市值']):
                    if pd.notna(current_balance[col]):
                        total_assets += current_balance[col]
            
            if total_assets > 0:
                debt_ratio = total_liabilities / total_assets
                
                if debt_ratio > 0.4:  # High debt ratio
                    recommendations.append(FinancialRecommendation(
                        id="reduce_debt_ratio",
                        type=RecommendationType.DEBT_MANAGEMENT,
                        title="Reduce Debt-to-Asset Ratio",
                        description=f"Current debt ratio is {debt_ratio:.1%}, above recommended 40%. "
                                  f"Focus on debt reduction strategies.",
                        urgency=RecommendationUrgency.HIGH,
                        impact_score=75,
                        ease_score=60,
                        estimated_benefit=total_liabilities * 0.05,  # Interest savings
                        implementation_time="12-24 months",
                        action_steps=[
                            "List all debts by interest rate (highest first)",
                            "Pay minimums on all debts, extra on highest rate",
                            "Consider debt consolidation if beneficial",
                            "Avoid taking on new debt until ratio improves"
                        ]
                    ))
                
                elif total_liabilities > 0 and debt_ratio < 0.2:  # Very low debt
                    recommendations.append(FinancialRecommendation(
                        id="leverage_opportunity",
                        type=RecommendationType.DEBT_MANAGEMENT,
                        title="Consider Strategic Leverage",
                        description=f"Debt ratio is low ({debt_ratio:.1%}). "
                                  f"Consider strategic borrowing for investment opportunities.",
                        urgency=RecommendationUrgency.LOW,
                        impact_score=30,
                        ease_score=40,
                        implementation_time="As opportunities arise",
                        action_steps=[
                            "Research low-interest borrowing options",
                            "Evaluate investment opportunities with returns > borrowing cost",
                            "Maintain conservative debt levels",
                            "Consider mortgage for real estate investment"
                        ]
                    ))
            
        except Exception as e:
            logger.warning(f"Error analyzing debt situation: {str(e)}")
        
        return recommendations
    
    def _generate_savings_recommendations(self, monthly_df: pd.DataFrame,
                                        financial_analysis: Dict[str, Any]) -> List[FinancialRecommendation]:
        """Generate savings rate recommendations"""
        recommendations = []
        
        try:
            if monthly_df is None or monthly_df.empty:
                return recommendations
            
            # Calculate savings rate from recent months
            recent_months = monthly_df.tail(6)
            
            if 'Total_Income_CNY' in recent_months.columns and 'Total_Expenses_CNY' in recent_months.columns:
                total_income = recent_months['Total_Income_CNY'].sum()
                total_expenses = recent_months['Total_Expenses_CNY'].sum()
                
                if total_income > 0:
                    savings_rate = (total_income - total_expenses) / total_income
                    
                    if savings_rate < 0.1:  # Less than 10% savings rate
                        recommendations.append(FinancialRecommendation(
                            id="increase_savings_rate",
                            type=RecommendationType.SAVINGS_RATE,
                            title="Increase Savings Rate",
                            description=f"Current savings rate is {savings_rate:.1%}, below recommended 20%. "
                                      f"Focus on increasing monthly savings.",
                            urgency=RecommendationUrgency.HIGH,
                            impact_score=85,
                            ease_score=60,
                            estimated_benefit=(0.2 - savings_rate) * total_income / 6 * 12,
                            implementation_time="3-6 months",
                            action_steps=[
                                "Set up automatic transfers to savings on payday",
                                "Review and reduce discretionary spending",
                                "Look for ways to increase income",
                                "Use the 50/30/20 budgeting rule as a guide"
                            ]
                        ))
                    
                    elif savings_rate > 0.3:  # Very high savings rate
                        recommendations.append(FinancialRecommendation(
                            id="optimize_high_savings",
                            type=RecommendationType.SAVINGS_RATE,
                            title="Optimize High Savings Rate",
                            description=f"Excellent savings rate of {savings_rate:.1%}! "
                                      f"Consider optimizing investment allocation for better returns.",
                            urgency=RecommendationUrgency.LOW,
                            impact_score=60,
                            ease_score=80,
                            implementation_time="1-2 months",
                            action_steps=[
                                "Review investment portfolio allocation",
                                "Consider tax-advantaged investment accounts",
                                "Evaluate risk tolerance for higher return investments",
                                "Maintain balance between savings and quality of life"
                            ]
                        ))
            
        except Exception as e:
            logger.warning(f"Error analyzing savings rate: {str(e)}")
        
        return recommendations
    
    def analyze_emergency_fund(self, financial_data: Dict[str, Any]) -> Optional[FinancialRecommendation]:
        """
        Analyze emergency fund adequacy
        
        Args:
            financial_data: Dictionary containing financial metrics
            
        Returns:
            Emergency fund recommendation if needed
        """
        try:
            emergency_fund = financial_data.get('emergency_fund', 0)
            monthly_expenses = financial_data.get('monthly_expenses', 0)
            
            if monthly_expenses <= 0:
                return None
            
            months_coverage = emergency_fund / monthly_expenses
            target_months = 6  # Standard recommendation
            
            if months_coverage < target_months:
                shortfall = (target_months - months_coverage) * monthly_expenses
                
                return FinancialRecommendation(
                    id="emergency_fund_build",
                    type=RecommendationType.EMERGENCY_FUND,
                    title="Build Emergency Fund",
                    description=f"Current emergency fund covers {months_coverage:.1f} months of expenses. "
                              f"Target is {target_months} months (¥{target_months * monthly_expenses:,.0f}). "
                              f"Shortfall: ¥{shortfall:,.0f}",
                    urgency=RecommendationUrgency.HIGH if months_coverage < 3 else RecommendationUrgency.MEDIUM,
                    impact_score=85,
                    ease_score=60,
                    estimated_benefit=shortfall,
                    implementation_time="6-12 months",
                    action_steps=[
                        f"Save additional ¥{shortfall:,.0f} for emergency fund",
                        "Open high-yield savings account for emergency funds",
                        "Set up automatic monthly transfers",
                        "Keep emergency fund separate from daily banking"
                    ]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing emergency fund: {str(e)}")
            return None
    
    def _analyze_historical_trends(self, historical_performance_results: Dict[str, Any]) -> List[FinancialRecommendation]:
        """Analyze long-term trends and provide strategic recommendations"""
        
        recommendations = []
        
        try:
            if 'trend_analysis' not in historical_performance_results:
                return recommendations
            
            trends = historical_performance_results['trend_analysis']
            
            # Analyze portfolio growth trend
            if 'portfolio_growth' in trends and 'error' not in trends['portfolio_growth']:
                portfolio_trend = trends['portfolio_growth']
                trend_direction = portfolio_trend.get('trend_direction', 'Unknown')
                cagr = portfolio_trend.get('cagr', 0)
                
                if trend_direction == "Decreasing" and cagr < -0.02:  # Declining more than 2% annually
                    recommendations.append(FinancialRecommendation(
                        id="portfolio_decline_trend",
                        type=RecommendationType.SAVINGS_RATE,
                        title="Address Portfolio Decline Trend",
                        description=f"Portfolio value has been declining at {abs(cagr*100):.1f}% annually. "
                                  f"Review investment strategy and increase savings contributions.",
                        urgency=RecommendationUrgency.HIGH,
                        impact_score=85,
                        ease_score=60,
                        implementation_time="1-3 months",
                        action_steps=[
                            "Conduct comprehensive portfolio review",
                            "Increase regular investment contributions",
                            "Consider rebalancing to more growth-oriented allocation",
                            "Review fees and expenses that may be dragging down returns",
                            "Consider dollar-cost averaging strategy during market downturns"
                        ]
                    ))
                elif trend_direction == "Increasing" and cagr > 0.15:  # Very strong growth
                    recommendations.append(FinancialRecommendation(
                        id="strong_portfolio_growth",
                        type=RecommendationType.SAVINGS_RATE,
                        title="Capitalize on Strong Portfolio Growth",
                        description=f"Excellent portfolio growth of {cagr*100:.1f}% annually. "
                                  f"Consider increasing investment contributions to accelerate wealth building.",
                        urgency=RecommendationUrgency.MEDIUM,
                        impact_score=70,
                        ease_score=80,
                        implementation_time="1 month",
                        action_steps=[
                            "Increase automatic investment contributions",
                            "Consider maximizing tax-advantaged accounts",
                            "Review if current allocation is sustainable long-term",
                            "Maintain diversification despite strong performance"
                        ]
                    ))
            
            return recommendations
            
        except Exception as e:
            logger.warning(f"Error analyzing historical trends: {str(e)}")
            return recommendations
    
    def _analyze_net_worth_trends(self, historical_performance_results: Dict[str, Any]) -> List[FinancialRecommendation]:
        """Analyze net worth trends and provide strategic financial planning recommendations"""
        
        recommendations = []
        
        try:
            if 'trend_analysis' not in historical_performance_results:
                return recommendations
            
            trends = historical_performance_results['trend_analysis']
            
            # Analyze net worth trend
            if 'net_worth' in trends and 'error' not in trends['net_worth']:
                net_worth_trend = trends['net_worth']
                trend_direction = net_worth_trend.get('trend_direction', 'Unknown')
                cagr = net_worth_trend.get('cagr', 0)
                current_value = net_worth_trend.get('current_value', 0)
                
                if trend_direction == "Decreasing":
                    recommendations.append(FinancialRecommendation(
                        id="declining_net_worth",
                        type=RecommendationType.CASH_FLOW,
                        title="Address Declining Net Worth Trend",
                        description=f"Net worth has been declining at {abs(cagr*100):.1f}% annually. "
                                  f"This indicates spending is outpacing wealth accumulation.",
                        urgency=RecommendationUrgency.CRITICAL,
                        impact_score=95,
                        ease_score=50,
                        implementation_time="Immediate",
                        action_steps=[
                            "Conduct comprehensive financial audit",
                            "Identify and eliminate sources of wealth erosion",
                            "Increase savings and investment contributions",
                            "Review all major expenses and eliminate non-essentials",
                            "Consider financial counseling or advisory services"
                        ]
                    ))
                elif trend_direction == "Increasing" and cagr > 0.10:
                    recommendations.append(FinancialRecommendation(
                        id="strong_wealth_building",
                        type=RecommendationType.SAVINGS_RATE,
                        title="Accelerate Wealth Building Momentum",
                        description=f"Excellent net worth growth of {cagr*100:.1f}% annually. "
                                  f"Consider strategies to further accelerate wealth building.",
                        urgency=RecommendationUrgency.LOW,
                        impact_score=60,
                        ease_score=70,
                        implementation_time="3-6 months",
                        action_steps=[
                            "Explore additional investment opportunities",
                            "Consider increasing risk tolerance for higher returns",
                            "Look into tax optimization strategies",
                            "Plan for long-term financial goals (retirement, major purchases)"
                        ]
                    ))
            
            # Analyze total assets trend
            if 'total_assets' in trends and 'error' not in trends['total_assets']:
                assets_trend = trends['total_assets']
                trend_direction = assets_trend.get('trend_direction', 'Unknown')
                cagr = assets_trend.get('cagr', 0)
                
                if trend_direction == "Stable" or (abs(cagr) < 0.02):
                    recommendations.append(FinancialRecommendation(
                        id="stagnant_asset_growth",
                        type=RecommendationType.SAVINGS_RATE,
                        title="Accelerate Asset Growth",
                        description=f"Asset growth has been relatively flat ({cagr*100:.1f}% annually). "
                                  f"Consider strategies to increase asset accumulation.",
                        urgency=RecommendationUrgency.MEDIUM,
                        impact_score=70,
                        ease_score=60,
                        implementation_time="3-6 months",
                        action_steps=[
                            "Increase regular savings and investment contributions",
                            "Review investment allocation for growth potential",
                            "Consider additional income sources",
                            "Look for underperforming assets to optimize or divest"
                        ]
                    ))
            
            return recommendations
            
        except Exception as e:
            logger.warning(f"Error analyzing net worth trends: {str(e)}")
            return recommendations
