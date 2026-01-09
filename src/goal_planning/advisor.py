"""
Goal Planning Advisor Module

This module provides actionable advice and scenario analysis based on Monte Carlo simulation results.
It translates complex financial projections into clear, practical recommendations for users.

Classes:
    GoalAdvisor: Main class for generating recommendations and scenario analysis
    ScenarioAnalysis: Container for scenario comparison results
    Recommendation: Structured recommendation with priority and rationale
"""

from datetime import date, datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging
import numpy as np

from .goal_manager import GoalManager, Goal
from .simulation import MonteCarloSimulation, MonteCarloResult

# Configure logging
logger = logging.getLogger(__name__)


class RecommendationPriority(Enum):
    """Priority levels for recommendations"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationType(Enum):
    """Types of recommendations"""
    SAVINGS_INCREASE = "savings_increase"
    TIMELINE_ADJUSTMENT = "timeline_adjustment"
    GOAL_MODIFICATION = "goal_modification"
    RISK_ADJUSTMENT = "risk_adjustment"
    ALLOCATION_CHANGE = "allocation_change"


@dataclass
class Recommendation:
    """
    A structured recommendation with rationale and priority.
    """
    title: str
    description: str
    action_required: str
    priority: RecommendationPriority
    recommendation_type: RecommendationType
    impact_description: str
    current_value: Optional[float] = None
    recommended_value: Optional[float] = None
    probability_improvement: Optional[float] = None


@dataclass
class ScenarioAnalysis:
    """
    Container for scenario analysis results.
    """
    scenario_name: str
    base_probability: float
    modified_probability: float
    parameter_changed: str
    parameter_value: Any
    monthly_impact: Optional[float] = None
    annual_impact: Optional[float] = None
    recommendations: List[Recommendation] = None

    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []


class GoalAdvisor:
    """
    Provides actionable advice and scenario analysis for financial goals.
    """
    
    def __init__(self, goal_manager: GoalManager, monte_carlo_engine: MonteCarloSimulation):
        """
        Initialize the Goal Advisor.
        
        Args:
            goal_manager: GoalManager instance with loaded goals
            monte_carlo_engine: MonteCarloSimulation instance for analysis
        """
        self.goal_manager = goal_manager
        self.monte_carlo_engine = monte_carlo_engine
        self.planning_config = goal_manager.get_planning_config()
        
        # Recommendation thresholds
        self.probability_thresholds = {
            'excellent': 0.90,
            'good': 0.80,
            'acceptable': 0.70,
            'concerning': 0.50
        }
        
        logger.info("Goal Advisor initialized")
    
    def analyze_current_situation(
        self, 
        portfolio_value: float, 
        annual_contribution: float
    ) -> Tuple[MonteCarloResult, List[Recommendation]]:
        """
        Analyze the current financial situation and generate baseline recommendations.
        
        Args:
            portfolio_value: Current portfolio value
            annual_contribution: Current annual contribution
            
        Returns:
            Tuple of (simulation_result, recommendations)
        """
        logger.info("Analyzing current financial situation")
        
        # Run baseline Monte Carlo simulation
        baseline_result = self.monte_carlo_engine.run_simulation(
            initial_portfolio_value=portfolio_value,
            annual_contribution=annual_contribution
        )
        
        # Generate recommendations based on current situation
        recommendations = []
        goals = self.goal_manager.list_goals()
        
        for goal_id, goal in goals.items():
            probability = baseline_result.goal_probabilities.get(goal_id, 0.0)
            goal_recommendations = self._analyze_goal_probability(goal, probability, annual_contribution)
            recommendations.extend(goal_recommendations)
        
        # Add portfolio-level recommendations
        portfolio_recommendations = self._analyze_portfolio_health(baseline_result, annual_contribution)
        recommendations.extend(portfolio_recommendations)
        
        return baseline_result, recommendations
    
    def scenario_analysis_savings_increase(
        self,
        goal_id: str,
        portfolio_value: float,
        current_annual_contribution: float,
        target_probability: float = 0.90
    ) -> ScenarioAnalysis:
        """
        Analyze how increasing savings affects goal success probability.
        
        Args:
            goal_id: Goal to analyze
            portfolio_value: Current portfolio value
            current_annual_contribution: Current annual contribution
            target_probability: Target success probability
            
        Returns:
            ScenarioAnalysis with savings increase recommendations
        """
        goals = self.goal_manager.list_goals()
        goal = goals.get(goal_id)
        if not goal:
            raise ValueError(f"Goal {goal_id} not found")
        
        logger.info(f"Analyzing savings increase scenario for goal: {goal.name}")
        
        # Get baseline probability
        baseline_result = self.monte_carlo_engine.run_simulation(
            initial_portfolio_value=portfolio_value,
            annual_contribution=current_annual_contribution
        )
        base_probability = baseline_result.goal_probabilities.get(goal_id, 0.0)
        
        # Binary search for required contribution increase
        required_contribution = self._find_required_contribution(
            goal_id, portfolio_value, current_annual_contribution, target_probability
        )
        
        # Run simulation with required contribution
        modified_result = self.monte_carlo_engine.run_simulation(
            initial_portfolio_value=portfolio_value,
            annual_contribution=required_contribution
        )
        modified_probability = modified_result.goal_probabilities.get(goal_id, 0.0)
        
        # Calculate impact
        contribution_increase = required_contribution - current_annual_contribution
        monthly_increase = contribution_increase / 12
        
        # Generate recommendations
        recommendations = []
        if contribution_increase > 0:
            if monthly_increase <= 100:
                priority = RecommendationPriority.LOW
            elif monthly_increase <= 300:
                priority = RecommendationPriority.MEDIUM
            elif monthly_increase <= 600:
                priority = RecommendationPriority.HIGH
            else:
                priority = RecommendationPriority.CRITICAL
            
            recommendations.append(Recommendation(
                title=f"Increase Monthly Savings for {goal.name}",
                description=f"To achieve {target_probability:.0%} success probability for {goal.name}, increase monthly savings by ${monthly_increase:.0f}",
                action_required=f"Increase monthly contribution from ${current_annual_contribution/12:.0f} to ${required_contribution/12:.0f}",
                priority=priority,
                recommendation_type=RecommendationType.SAVINGS_INCREASE,
                impact_description=f"Success probability improves from {base_probability:.1%} to {modified_probability:.1%}",
                current_value=current_annual_contribution,
                recommended_value=required_contribution,
                probability_improvement=modified_probability - base_probability
            ))
        
        return ScenarioAnalysis(
            scenario_name=f"Savings Increase for {goal.name}",
            base_probability=base_probability,
            modified_probability=modified_probability,
            parameter_changed="annual_contribution",
            parameter_value=required_contribution,
            monthly_impact=monthly_increase,
            annual_impact=contribution_increase,
            recommendations=recommendations
        )
    
    def scenario_analysis_timeline_adjustment(
        self,
        goal_id: str,
        portfolio_value: float,
        annual_contribution: float,
        timeline_adjustments: List[int] = None
    ) -> List[ScenarioAnalysis]:
        """
        Analyze how adjusting goal timeline affects success probability.
        
        Args:
            goal_id: Goal to analyze
            portfolio_value: Current portfolio value
            annual_contribution: Current annual contribution
            timeline_adjustments: List of year adjustments to test (default: [-2, -1, 1, 2, 3])
            
        Returns:
            List of ScenarioAnalysis for different timeline adjustments
        """
        if timeline_adjustments is None:
            timeline_adjustments = [-2, -1, 1, 2, 3]
        
        goals = self.goal_manager.list_goals()
        goal = goals.get(goal_id)
        if not goal:
            raise ValueError(f"Goal {goal_id} not found")
        
        logger.info(f"Analyzing timeline adjustment scenarios for goal: {goal.name}")
        
        # Get baseline probability
        baseline_result = self.monte_carlo_engine.run_simulation(
            initial_portfolio_value=portfolio_value,
            annual_contribution=annual_contribution
        )
        base_probability = baseline_result.goal_probabilities.get(goal_id, 0.0)
        
        scenarios = []
        original_target_date = goal.target_date
        
        for year_adjustment in timeline_adjustments:
            try:
                # Temporarily modify goal timeline
                new_target_date = date(
                    original_target_date.year + year_adjustment,
                    original_target_date.month,
                    original_target_date.day
                )
                
                # Create modified goal for simulation
                modified_goals = goals.copy()
                modified_goal = Goal(
                    name=goal.name,
                    target_amount=goal.target_amount,
                    target_date=new_target_date,
                    priority=goal.priority,
                    category=goal.category,
                    current_progress=goal.current_progress,
                    description=goal.description
                )
                modified_goals[goal_id] = modified_goal
                
                # Temporarily update goal manager
                original_goals = self.goal_manager.goals
                self.goal_manager.goals = modified_goals
                
                # Run simulation with modified timeline
                modified_result = self.monte_carlo_engine.run_simulation(
                    initial_portfolio_value=portfolio_value,
                    annual_contribution=annual_contribution
                )
                modified_probability = modified_result.goal_probabilities.get(goal_id, 0.0)
                
                # Generate recommendations
                recommendations = []
                probability_change = modified_probability - base_probability
                
                if abs(probability_change) > 0.05:  # Significant change
                    if year_adjustment > 0:
                        action = f"Extend {goal.name} timeline by {year_adjustment} year{'s' if year_adjustment > 1 else ''}"
                        impact = f"Moving target date from {original_target_date} to {new_target_date}"
                    else:
                        action = f"Accelerate {goal.name} timeline by {abs(year_adjustment)} year{'s' if abs(year_adjustment) > 1 else ''}"
                        impact = f"Moving target date from {original_target_date} to {new_target_date}"
                    
                    priority = (RecommendationPriority.HIGH if abs(probability_change) > 0.15 
                              else RecommendationPriority.MEDIUM)
                    
                    recommendations.append(Recommendation(
                        title=f"Timeline Adjustment for {goal.name}",
                        description=f"Adjusting timeline by {year_adjustment} years changes success probability by {probability_change:+.1%}",
                        action_required=action,
                        priority=priority,
                        recommendation_type=RecommendationType.TIMELINE_ADJUSTMENT,
                        impact_description=impact,
                        probability_improvement=probability_change
                    ))
                
                scenarios.append(ScenarioAnalysis(
                    scenario_name=f"{goal.name} Timeline {year_adjustment:+d} Years",
                    base_probability=base_probability,
                    modified_probability=modified_probability,
                    parameter_changed="target_date",
                    parameter_value=new_target_date,
                    recommendations=recommendations
                ))
                
            finally:
                # Restore original goals
                self.goal_manager.goals = original_goals
        
        return scenarios
    
    def scenario_analysis_goal_amount_adjustment(
        self,
        goal_id: str,
        portfolio_value: float,
        annual_contribution: float,
        amount_adjustments: List[float] = None
    ) -> List[ScenarioAnalysis]:
        """
        Analyze how adjusting goal target amount affects success probability.
        
        Args:
            goal_id: Goal to analyze
            portfolio_value: Current portfolio value
            annual_contribution: Current annual contribution
            amount_adjustments: List of percentage adjustments (default: [-0.2, -0.1, 0.1, 0.2])
            
        Returns:
            List of ScenarioAnalysis for different amount adjustments
        """
        if amount_adjustments is None:
            amount_adjustments = [-0.2, -0.1, 0.1, 0.2]
        
        goals = self.goal_manager.list_goals()
        goal = goals.get(goal_id)
        if not goal:
            raise ValueError(f"Goal {goal_id} not found")
        
        logger.info(f"Analyzing goal amount adjustment scenarios for goal: {goal.name}")
        
        # Get baseline probability
        baseline_result = self.monte_carlo_engine.run_simulation(
            initial_portfolio_value=portfolio_value,
            annual_contribution=annual_contribution
        )
        base_probability = baseline_result.goal_probabilities.get(goal_id, 0.0)
        
        scenarios = []
        original_target_amount = goal.target_amount
        
        for amount_adjustment in amount_adjustments:
            try:
                # Calculate new target amount
                new_target_amount = original_target_amount * (1 + amount_adjustment)
                
                # Create modified goal for simulation
                modified_goals = goals.copy()
                modified_goal = Goal(
                    name=goal.name,
                    target_amount=new_target_amount,
                    target_date=goal.target_date,
                    priority=goal.priority,
                    category=goal.category,
                    current_progress=goal.current_progress,
                    description=goal.description
                )
                modified_goals[goal_id] = modified_goal
                
                # Temporarily update goal manager
                original_goals = self.goal_manager.goals
                self.goal_manager.goals = modified_goals
                
                # Run simulation with modified amount
                modified_result = self.monte_carlo_engine.run_simulation(
                    initial_portfolio_value=portfolio_value,
                    annual_contribution=annual_contribution
                )
                modified_probability = modified_result.goal_probabilities.get(goal_id, 0.0)
                
                # Generate recommendations
                recommendations = []
                probability_change = modified_probability - base_probability
                amount_change = new_target_amount - original_target_amount
                
                if abs(probability_change) > 0.05:  # Significant change
                    if amount_adjustment < 0:
                        action = f"Reduce {goal.name} target by ${abs(amount_change):,.0f} ({abs(amount_adjustment):.0%})"
                    else:
                        action = f"Increase {goal.name} target by ${amount_change:,.0f} ({amount_adjustment:.0%})"
                    
                    priority = (RecommendationPriority.MEDIUM if abs(probability_change) > 0.10 
                              else RecommendationPriority.LOW)
                    
                    recommendations.append(Recommendation(
                        title=f"Goal Amount Adjustment for {goal.name}",
                        description=f"Adjusting target amount by {amount_adjustment:+.0%} changes success probability by {probability_change:+.1%}",
                        action_required=action,
                        priority=priority,
                        recommendation_type=RecommendationType.GOAL_MODIFICATION,
                        impact_description=f"Target changes from ${original_target_amount:,.0f} to ${new_target_amount:,.0f}",
                        current_value=original_target_amount,
                        recommended_value=new_target_amount,
                        probability_improvement=probability_change
                    ))
                
                scenarios.append(ScenarioAnalysis(
                    scenario_name=f"{goal.name} Amount {amount_adjustment:+.0%}",
                    base_probability=base_probability,
                    modified_probability=modified_probability,
                    parameter_changed="target_amount",
                    parameter_value=new_target_amount,
                    recommendations=recommendations
                ))
                
            finally:
                # Restore original goals
                self.goal_manager.goals = original_goals
        
        return scenarios
    
    def generate_comprehensive_recommendations(
        self,
        portfolio_value: float,
        annual_contribution: float
    ) -> Dict[str, List[Recommendation]]:
        """
        Generate comprehensive recommendations across all goals and scenarios.
        
        Args:
            portfolio_value: Current portfolio value
            annual_contribution: Current annual contribution
            
        Returns:
            Dictionary with categorized recommendations
        """
        logger.info("Generating comprehensive recommendations")
        
        all_recommendations = {
            'immediate_actions': [],
            'optimization_opportunities': [],
            'long_term_planning': [],
            'risk_management': []
        }
        
        # Get baseline analysis
        baseline_result, baseline_recommendations = self.analyze_current_situation(
            portfolio_value, annual_contribution
        )
        
        # Categorize baseline recommendations
        for rec in baseline_recommendations:
            if rec.priority in [RecommendationPriority.CRITICAL, RecommendationPriority.HIGH]:
                all_recommendations['immediate_actions'].append(rec)
            elif rec.recommendation_type == RecommendationType.RISK_ADJUSTMENT:
                all_recommendations['risk_management'].append(rec)
            elif rec.recommendation_type in [RecommendationType.SAVINGS_INCREASE, RecommendationType.ALLOCATION_CHANGE]:
                all_recommendations['optimization_opportunities'].append(rec)
            else:
                all_recommendations['long_term_planning'].append(rec)
        
        # Analyze scenarios for goals with concerning probabilities
        goals = self.goal_manager.list_goals()
        for goal_id, goal in goals.items():
            probability = baseline_result.goal_probabilities.get(goal_id, 0.0)
            
            if probability < self.probability_thresholds['acceptable']:
                # Add savings increase analysis
                try:
                    savings_scenario = self.scenario_analysis_savings_increase(
                        goal_id, portfolio_value, annual_contribution, 0.80
                    )
                    all_recommendations['optimization_opportunities'].extend(savings_scenario.recommendations)
                except Exception as e:
                    logger.warning(f"Could not analyze savings scenario for {goal.name}: {e}")
                
                # Add timeline adjustment analysis
                try:
                    timeline_scenarios = self.scenario_analysis_timeline_adjustment(
                        goal_id, portfolio_value, annual_contribution, [1, 2, 3]
                    )
                    for scenario in timeline_scenarios:
                        all_recommendations['long_term_planning'].extend(scenario.recommendations)
                except Exception as e:
                    logger.warning(f"Could not analyze timeline scenarios for {goal.name}: {e}")
        
        # Sort recommendations by priority within each category
        priority_order = [RecommendationPriority.CRITICAL, RecommendationPriority.HIGH, 
                         RecommendationPriority.MEDIUM, RecommendationPriority.LOW]
        
        for category in all_recommendations:
            all_recommendations[category].sort(
                key=lambda x: priority_order.index(x.priority)
            )
        
        return all_recommendations
    
    def _analyze_goal_probability(
        self, 
        goal: Goal, 
        probability: float, 
        annual_contribution: float
    ) -> List[Recommendation]:
        """
        Analyze individual goal probability and generate recommendations.
        """
        recommendations = []
        
        if probability >= self.probability_thresholds['excellent']:
            # Goal is in excellent shape
            recommendations.append(Recommendation(
                title=f"{goal.name} - Excellent Progress",
                description=f"Your {goal.name} has a {probability:.1%} success probability - excellent progress!",
                action_required="Continue current savings plan",
                priority=RecommendationPriority.LOW,
                recommendation_type=RecommendationType.ALLOCATION_CHANGE,
                impact_description="Goal is well on track for success"
            ))
        
        elif probability >= self.probability_thresholds['good']:
            # Goal is in good shape
            recommendations.append(Recommendation(
                title=f"{goal.name} - Good Progress",
                description=f"Your {goal.name} has a {probability:.1%} success probability - good progress",
                action_required="Consider minor optimizations",
                priority=RecommendationPriority.LOW,
                recommendation_type=RecommendationType.SAVINGS_INCREASE,
                impact_description="Small adjustments could improve outcomes"
            ))
        
        elif probability >= self.probability_thresholds['acceptable']:
            # Goal needs attention
            recommendations.append(Recommendation(
                title=f"{goal.name} - Needs Attention",
                description=f"Your {goal.name} has a {probability:.1%} success probability - consider improvements",
                action_required="Increase monthly savings or extend timeline",
                priority=RecommendationPriority.MEDIUM,
                recommendation_type=RecommendationType.SAVINGS_INCREASE,
                impact_description="Moderate adjustments recommended for better outcomes"
            ))
        
        else:
            # Goal is at risk
            urgency = "CRITICAL" if probability < self.probability_thresholds['concerning'] else "HIGH"
            priority = RecommendationPriority.CRITICAL if urgency == "CRITICAL" else RecommendationPriority.HIGH
            
            recommendations.append(Recommendation(
                title=f"{goal.name} - {urgency} ATTENTION NEEDED",
                description=f"Your {goal.name} has only a {probability:.1%} success probability",
                action_required="Significantly increase savings, extend timeline, or reduce target amount",
                priority=priority,
                recommendation_type=RecommendationType.SAVINGS_INCREASE,
                impact_description="Major adjustments required to achieve this goal"
            ))
        
        return recommendations
    
    def _analyze_portfolio_health(
        self, 
        result: MonteCarloResult, 
        annual_contribution: float
    ) -> List[Recommendation]:
        """
        Analyze overall portfolio health and generate recommendations.
        """
        recommendations = []
        
        final_values = result.final_values
        median_final = np.median(final_values)
        mean_final = np.mean(final_values)
        std_final = np.std(final_values)
        
        # Analyze volatility
        coefficient_of_variation = std_final / mean_final
        if coefficient_of_variation > 0.8:
            recommendations.append(Recommendation(
                title="High Portfolio Volatility",
                description=f"Your portfolio shows high volatility (CV: {coefficient_of_variation:.1f})",
                action_required="Consider reducing risk through diversification or more conservative allocation",
                priority=RecommendationPriority.MEDIUM,
                recommendation_type=RecommendationType.RISK_ADJUSTMENT,
                impact_description="Lower volatility could provide more predictable outcomes"
            ))
        
        # Analyze contribution adequacy
        total_contributions = annual_contribution * len(result.years)
        contribution_ratio = total_contributions / median_final
        
        if contribution_ratio < 0.2:  # Contributions are less than 20% of final value
            recommendations.append(Recommendation(
                title="Investment Growth Dependency",
                description="Your plan relies heavily on investment growth rather than contributions",
                action_required="Consider increasing regular contributions for more control over outcomes",
                priority=RecommendationPriority.MEDIUM,
                recommendation_type=RecommendationType.SAVINGS_INCREASE,
                impact_description="Higher contributions reduce dependency on market performance"
            ))
        
        return recommendations
    
    def _find_required_contribution(
        self,
        goal_id: str,
        portfolio_value: float,
        current_contribution: float,
        target_probability: float,
        max_iterations: int = 20
    ) -> float:
        """
        Use binary search to find required contribution for target probability.
        """
        # Set search bounds
        low_contribution = current_contribution
        high_contribution = current_contribution * 5  # Start with 5x current contribution
        tolerance = 0.01  # 1% tolerance for probability
        
        # First check if even 5x contribution achieves target
        test_result = self.monte_carlo_engine.run_simulation(
            initial_portfolio_value=portfolio_value,
            annual_contribution=high_contribution
        )
        test_probability = test_result.goal_probabilities.get(goal_id, 0.0)
        
        if test_probability < target_probability:
            # Even 5x doesn't work, return the high value
            logger.warning(f"Target probability {target_probability:.1%} may not be achievable even with 5x contribution")
            return high_contribution
        
        # Binary search
        for _ in range(max_iterations):
            mid_contribution = (low_contribution + high_contribution) / 2
            
            test_result = self.monte_carlo_engine.run_simulation(
                initial_portfolio_value=portfolio_value,
                annual_contribution=mid_contribution
            )
            test_probability = test_result.goal_probabilities.get(goal_id, 0.0)
            
            if abs(test_probability - target_probability) < tolerance:
                return mid_contribution
            elif test_probability < target_probability:
                low_contribution = mid_contribution
            else:
                high_contribution = mid_contribution
        
        return (low_contribution + high_contribution) / 2

    def format_recommendations_report(
        self,
        recommendations: Dict[str, List[Recommendation]]
    ) -> str:
        """
        Format recommendations into a readable text report.
        
        Args:
            recommendations: Dictionary of categorized recommendations
            
        Returns:
            Formatted text report
        """
        report_lines = []
        report_lines.append("📋 PERSONALIZED FINANCIAL RECOMMENDATIONS")
        report_lines.append("=" * 50)
        
        category_titles = {
            'immediate_actions': '🚨 IMMEDIATE ACTIONS REQUIRED',
            'optimization_opportunities': '⚡ OPTIMIZATION OPPORTUNITIES', 
            'long_term_planning': '🎯 LONG-TERM PLANNING',
            'risk_management': '🛡️ RISK MANAGEMENT'
        }
        
        category_descriptions = {
            'immediate_actions': 'These recommendations require urgent attention to keep your goals on track.',
            'optimization_opportunities': 'These suggestions can help improve your financial outcomes.',
            'long_term_planning': 'Consider these adjustments for your long-term financial strategy.',
            'risk_management': 'These recommendations help manage risk and improve predictability.'
        }
        
        for category, title in category_titles.items():
            recs = recommendations.get(category, [])
            if recs:
                report_lines.append(f"\n{title}")
                report_lines.append("-" * len(title))
                report_lines.append(category_descriptions[category])
                report_lines.append("")
                
                for i, rec in enumerate(recs, 1):
                    priority_emoji = {
                        RecommendationPriority.CRITICAL: "🔴",
                        RecommendationPriority.HIGH: "🟠", 
                        RecommendationPriority.MEDIUM: "🟡",
                        RecommendationPriority.LOW: "🟢"
                    }
                    
                    report_lines.append(f"{i}. {priority_emoji[rec.priority]} {rec.title}")
                    report_lines.append(f"   Description: {rec.description}")
                    report_lines.append(f"   Action: {rec.action_required}")
                    report_lines.append(f"   Impact: {rec.impact_description}")
                    if rec.probability_improvement:
                        report_lines.append(f"   Success Rate Improvement: {rec.probability_improvement:+.1%}")
                    report_lines.append("")
        
        # Add summary
        total_recs = sum(len(recs) for recs in recommendations.values())
        critical_count = len([r for recs in recommendations.values() for r in recs 
                            if r.priority == RecommendationPriority.CRITICAL])
        high_count = len([r for recs in recommendations.values() for r in recs 
                        if r.priority == RecommendationPriority.HIGH])
        
        report_lines.append("\n📊 SUMMARY")
        report_lines.append("-" * 10)
        report_lines.append(f"Total Recommendations: {total_recs}")
        report_lines.append(f"Critical Priority: {critical_count}")
        report_lines.append(f"High Priority: {high_count}")
        
        if critical_count > 0:
            report_lines.append("\n⚠️ IMPORTANT: Address critical priority items first to avoid goal failure.")
        elif high_count > 0:
            report_lines.append("\n💡 TIP: Focus on high priority items for the biggest impact.")
        else:
            report_lines.append("\n✅ GREAT NEWS: Your financial plan is in good shape!")
        
        return "\n".join(report_lines)
