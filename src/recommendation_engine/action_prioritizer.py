"""
Action Prioritizer Module for Investment Recommendation System

This module prioritizes and consolidates recommendations from financial, portfolio,
and risk advisors to create a unified action plan.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ActionCategory(Enum):
    """Action category types"""
    IMMEDIATE = "immediate"
    SHORT_TERM = "short_term"
    MEDIUM_TERM = "medium_term"
    LONG_TERM = "long_term"
    MONITORING = "monitoring"


class ActionType(Enum):
    """Types of recommended actions"""
    BUY = "buy"
    SELL = "sell"
    REBALANCE = "rebalance"
    RESEARCH = "research"
    MONITOR = "monitor"
    REDUCE_RISK = "reduce_risk"
    INCREASE_ALLOCATION = "increase_allocation"
    DIVERSIFY = "diversify"
    OPTIMIZE = "optimize"


@dataclass
class PrioritizedAction:
    """Prioritized investment action"""
    id: str
    category: ActionCategory
    action_type: ActionType
    priority_score: float
    title: str
    description: str
    rationale: str
    expected_impact: str
    effort_required: str
    timeline: str
    source_recommendations: List[str]  # Which advisors suggested this
    specific_steps: List[str]
    success_metrics: List[str]
    dependencies: List[str]


@dataclass
class ActionPlan:
    """Complete prioritized action plan"""
    immediate_actions: List[PrioritizedAction]
    short_term_actions: List[PrioritizedAction]
    medium_term_actions: List[PrioritizedAction]
    long_term_actions: List[PrioritizedAction]
    monitoring_actions: List[PrioritizedAction]
    summary: Dict[str, Any]


class ActionPrioritizer:
    """
    Prioritizes and consolidates recommendations from multiple advisors
    """
    
    def __init__(self):
        """Initialize the ActionPrioritizer"""
        self.priority_weights = {
            'financial_health': 0.30,
            'risk_management': 0.35,
            'portfolio_optimization': 0.25,
            'implementation_ease': 0.10
        }
        
        self.impact_scores = {
            'high': 3.0,
            'medium': 2.0,
            'low': 1.0
        }
        
        self.effort_scores = {
            'low': 3.0,
            'medium': 2.0,
            'high': 1.0
        }
    
    def create_action_plan(self, 
                          financial_recommendations: List[Any],
                          portfolio_recommendations: List[Any],
                          risk_recommendations: List[Any],
                          user_preferences: Optional[Dict[str, Any]] = None) -> ActionPlan:
        """
        Create a comprehensive, prioritized action plan
        
        Args:
            financial_recommendations: Financial advisor recommendations
            portfolio_recommendations: Portfolio advisor recommendations
            risk_recommendations: Risk advisor recommendations
            user_preferences: User preferences for prioritization
            
        Returns:
            Complete action plan with prioritized actions
        """
        try:
            # Consolidate all recommendations
            all_actions = self._consolidate_recommendations(
                financial_recommendations,
                portfolio_recommendations, 
                risk_recommendations
            )
            
            # Apply user preferences if provided
            if user_preferences:
                all_actions = self._apply_user_preferences(all_actions, user_preferences)
            
            # Calculate priority scores
            for action in all_actions:
                action.priority_score = self._calculate_priority_score(action)
            
            # Sort by priority score
            all_actions.sort(key=lambda x: x.priority_score, reverse=True)
            
            # Categorize actions by timeline
            action_plan = self._categorize_actions(all_actions)
            
            # Generate summary
            action_plan.summary = self._generate_plan_summary(action_plan)
            
            logger.info(f"Created action plan with {len(all_actions)} total actions")
            return action_plan
            
        except Exception as e:
            logger.error(f"Error creating action plan: {str(e)}")
            return ActionPlan([], [], [], [], [], {"error": str(e)})
    
    def _consolidate_recommendations(self,
                                   financial_recs: List[Any],
                                   portfolio_recs: List[Any],
                                   risk_recs: List[Any]) -> List[PrioritizedAction]:
        """Consolidate recommendations from all advisors"""
        actions = []
        action_id = 1
        
        # Process financial recommendations
        for rec in financial_recs:
            action = self._convert_financial_recommendation(rec, action_id)
            if action:
                actions.append(action)
                action_id += 1
        
        # Process portfolio recommendations
        for rec in portfolio_recs:
            action = self._convert_portfolio_recommendation(rec, action_id)
            if action:
                actions.append(action)
                action_id += 1
        
        # Process risk recommendations
        for rec in risk_recs:
            action = self._convert_risk_recommendation(rec, action_id)
            if action:
                actions.append(action)
                action_id += 1
        
        # Remove duplicates and merge similar actions
        actions = self._merge_similar_actions(actions)
        
        return actions
    
    def _convert_financial_recommendation(self, rec: Any, action_id: int) -> Optional[PrioritizedAction]:
        """Convert financial recommendation to prioritized action"""
        try:
            # Map recommendation type to action type
            action_type_mapping = {
                'emergency_fund': ActionType.INCREASE_ALLOCATION,
                'debt_reduction': ActionType.OPTIMIZE,
                'expense_reduction': ActionType.OPTIMIZE,
                'income_optimization': ActionType.RESEARCH,
                'tax_optimization': ActionType.OPTIMIZE
            }
            
            rec_type = getattr(rec, 'recommendation_type', 'unknown')
            action_type = action_type_mapping.get(rec_type, ActionType.RESEARCH)
            
            # Determine timeline category
            timeline = getattr(rec, 'timeline', '3-6 months')
            category = self._map_timeline_to_category(timeline)
            
            return PrioritizedAction(
                id=f"FIN_{action_id:03d}",
                category=category,
                action_type=action_type,
                priority_score=0.0,  # Will be calculated later
                title=getattr(rec, 'action', f"Financial Action {action_id}"),
                description=getattr(rec, 'rationale', ''),
                rationale=getattr(rec, 'rationale', ''),
                expected_impact=getattr(rec, 'expected_impact', 'Improve financial health'),
                effort_required=getattr(rec, 'effort_level', 'medium'),
                timeline=timeline,
                source_recommendations=['financial_advisor'],
                specific_steps=self._generate_financial_steps(rec),
                success_metrics=self._generate_financial_metrics(rec),
                dependencies=[]
            )
            
        except Exception as e:
            logger.error(f"Error converting financial recommendation: {str(e)}")
            return None
    
    def _convert_portfolio_recommendation(self, rec: Any, action_id: int) -> Optional[PrioritizedAction]:
        """Convert portfolio recommendation to prioritized action"""
        try:
            # Map recommendation type to action type
            action_type_mapping = {
                'rebalance': ActionType.REBALANCE,
                'add_position': ActionType.BUY,
                'reduce_position': ActionType.SELL,
                'diversify': ActionType.DIVERSIFY,
                'optimize_allocation': ActionType.OPTIMIZE
            }
            
            rec_type = getattr(rec, 'recommendation_type', 'unknown')
            action_type = action_type_mapping.get(rec_type, ActionType.REBALANCE)
            
            # Determine timeline category
            timeline = getattr(rec, 'timeline', '1-3 months')
            category = self._map_timeline_to_category(timeline)
            
            return PrioritizedAction(
                id=f"PORT_{action_id:03d}",
                category=category,
                action_type=action_type,
                priority_score=0.0,  # Will be calculated later
                title=getattr(rec, 'action', f"Portfolio Action {action_id}"),
                description=getattr(rec, 'rationale', ''),
                rationale=getattr(rec, 'rationale', ''),
                expected_impact=getattr(rec, 'expected_impact', 'Improve portfolio performance'),
                effort_required=getattr(rec, 'effort_level', 'medium'),
                timeline=timeline,
                source_recommendations=['portfolio_advisor'],
                specific_steps=self._generate_portfolio_steps(rec),
                success_metrics=self._generate_portfolio_metrics(rec),
                dependencies=[]
            )
            
        except Exception as e:
            logger.error(f"Error converting portfolio recommendation: {str(e)}")
            return None
    
    def _convert_risk_recommendation(self, rec: Any, action_id: int) -> Optional[PrioritizedAction]:
        """Convert risk recommendation to prioritized action"""
        try:
            return PrioritizedAction(
                id=f"RISK_{action_id:03d}",
                category=self._map_timeline_to_category(getattr(rec, 'timeline', '1-3 months')),
                action_type=ActionType.REDUCE_RISK,
                priority_score=0.0,  # Will be calculated later
                title=getattr(rec, 'action', f"Risk Management Action {action_id}"),
                description=getattr(rec, 'rationale', ''),
                rationale=getattr(rec, 'rationale', ''),
                expected_impact=getattr(rec, 'expected_impact', 'Reduce portfolio risk'),
                effort_required=getattr(rec, 'effort_level', 'medium'),
                timeline=getattr(rec, 'timeline', '1-3 months'),
                source_recommendations=['risk_advisor'],
                specific_steps=self._generate_risk_steps(rec),
                success_metrics=self._generate_risk_metrics(rec),
                dependencies=[]
            )
            
        except Exception as e:
            logger.error(f"Error converting risk recommendation: {str(e)}")
            return None
    
    def _map_timeline_to_category(self, timeline: str) -> ActionCategory:
        """Map timeline string to action category"""
        timeline_lower = timeline.lower()
        
        if 'immediate' in timeline_lower or 'urgent' in timeline_lower:
            return ActionCategory.IMMEDIATE
        elif 'week' in timeline_lower or '1 month' in timeline_lower:
            return ActionCategory.SHORT_TERM
        elif 'month' in timeline_lower and not 'year' in timeline_lower:
            return ActionCategory.MEDIUM_TERM
        elif 'year' in timeline_lower or 'long' in timeline_lower:
            return ActionCategory.LONG_TERM
        else:
            return ActionCategory.MONITORING
    
    def _merge_similar_actions(self, actions: List[PrioritizedAction]) -> List[PrioritizedAction]:
        """Merge similar actions to avoid duplication"""
        # Simple implementation - group by action type and merge rationales
        merged_actions = []
        action_groups = {}
        
        for action in actions:
            key = (action.action_type, action.category)
            if key not in action_groups:
                action_groups[key] = []
            action_groups[key].append(action)
        
        for group in action_groups.values():
            if len(group) == 1:
                merged_actions.append(group[0])
            else:
                # Merge multiple similar actions
                merged_action = self._merge_action_group(group)
                merged_actions.append(merged_action)
        
        return merged_actions
    
    def _merge_action_group(self, actions: List[PrioritizedAction]) -> PrioritizedAction:
        """Merge a group of similar actions"""
        primary_action = actions[0]
        
        # Combine source recommendations
        all_sources = []
        for action in actions:
            all_sources.extend(action.source_recommendations)
        
        # Combine specific steps
        all_steps = []
        for action in actions:
            all_steps.extend(action.specific_steps)
        
        # Combine rationales
        combined_rationale = "; ".join([action.rationale for action in actions if action.rationale])
        
        return PrioritizedAction(
            id=primary_action.id,
            category=primary_action.category,
            action_type=primary_action.action_type,
            priority_score=primary_action.priority_score,
            title=primary_action.title,
            description=combined_rationale,
            rationale=combined_rationale,
            expected_impact=primary_action.expected_impact,
            effort_required=primary_action.effort_required,
            timeline=primary_action.timeline,
            source_recommendations=list(set(all_sources)),
            specific_steps=list(set(all_steps)),
            success_metrics=primary_action.success_metrics,
            dependencies=primary_action.dependencies
        )
    
    def _calculate_priority_score(self, action: PrioritizedAction) -> float:
        """Calculate priority score for an action"""
        try:
            # Base score from impact and effort
            impact_score = self.impact_scores.get(
                action.expected_impact.lower() if 'high' in action.expected_impact.lower() else 'medium', 
                2.0
            )
            effort_score = self.effort_scores.get(action.effort_required.lower(), 2.0)
            
            # Timeline urgency factor
            timeline_multiplier = {
                ActionCategory.IMMEDIATE: 2.0,
                ActionCategory.SHORT_TERM: 1.5,
                ActionCategory.MEDIUM_TERM: 1.0,
                ActionCategory.LONG_TERM: 0.8,
                ActionCategory.MONITORING: 0.5
            }.get(action.category, 1.0)
            
            # Source credibility factor (more sources = higher credibility)
            source_factor = min(len(action.source_recommendations) * 0.2 + 0.8, 1.5)
            
            # Action type importance
            action_importance = {
                ActionType.REDUCE_RISK: 1.3,
                ActionType.REBALANCE: 1.2,
                ActionType.OPTIMIZE: 1.1,
                ActionType.BUY: 1.0,
                ActionType.SELL: 1.0,
                ActionType.DIVERSIFY: 1.1,
                ActionType.INCREASE_ALLOCATION: 1.0,
                ActionType.RESEARCH: 0.8,
                ActionType.MONITOR: 0.6
            }.get(action.action_type, 1.0)
            
            # Calculate final score
            priority_score = (
                impact_score * effort_score * timeline_multiplier * 
                source_factor * action_importance
            )
            
            return round(priority_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating priority score: {str(e)}")
            return 1.0
    
    def _categorize_actions(self, actions: List[PrioritizedAction]) -> ActionPlan:
        """Categorize actions by timeline"""
        immediate = [a for a in actions if a.category == ActionCategory.IMMEDIATE]
        short_term = [a for a in actions if a.category == ActionCategory.SHORT_TERM]
        medium_term = [a for a in actions if a.category == ActionCategory.MEDIUM_TERM]
        long_term = [a for a in actions if a.category == ActionCategory.LONG_TERM]
        monitoring = [a for a in actions if a.category == ActionCategory.MONITORING]
        
        return ActionPlan(
            immediate_actions=immediate[:5],  # Limit to top 5
            short_term_actions=short_term[:8],  # Limit to top 8
            medium_term_actions=medium_term[:10],  # Limit to top 10
            long_term_actions=long_term[:5],  # Limit to top 5
            monitoring_actions=monitoring[:5],  # Limit to top 5
            summary={}
        )
    
    def _generate_plan_summary(self, action_plan: ActionPlan) -> Dict[str, Any]:
        """Generate summary of the action plan"""
        all_actions = (
            action_plan.immediate_actions + 
            action_plan.short_term_actions + 
            action_plan.medium_term_actions + 
            action_plan.long_term_actions + 
            action_plan.monitoring_actions
        )
        
        # Count actions by type
        action_type_counts = {}
        for action in all_actions:
            action_type = action.action_type.value
            action_type_counts[action_type] = action_type_counts.get(action_type, 0) + 1
        
        # Count actions by source
        source_counts = {}
        for action in all_actions:
            for source in action.source_recommendations:
                source_counts[source] = source_counts.get(source, 0) + 1
        
        # Calculate average priority scores by category
        avg_priorities = {}
        for category_name, actions in [
            ('immediate', action_plan.immediate_actions),
            ('short_term', action_plan.short_term_actions),
            ('medium_term', action_plan.medium_term_actions),
            ('long_term', action_plan.long_term_actions),
            ('monitoring', action_plan.monitoring_actions)
        ]:
            if actions:
                avg_priorities[category_name] = round(
                    np.mean([a.priority_score for a in actions]), 2
                )
        
        return {
            "total_actions": len(all_actions),
            "actions_by_category": {
                "immediate": len(action_plan.immediate_actions),
                "short_term": len(action_plan.short_term_actions),
                "medium_term": len(action_plan.medium_term_actions),
                "long_term": len(action_plan.long_term_actions),
                "monitoring": len(action_plan.monitoring_actions)
            },
            "actions_by_type": action_type_counts,
            "actions_by_source": source_counts,
            "average_priority_scores": avg_priorities,
            "top_priority_action": all_actions[0].title if all_actions else None,
            "key_focus_areas": list(action_type_counts.keys())[:3]
        }
    
    def _generate_financial_steps(self, rec: Any) -> List[str]:
        """Generate specific steps for financial recommendations"""
        rec_type = getattr(rec, 'recommendation_type', 'unknown')
        
        step_mapping = {
            'emergency_fund': [
                "Calculate 3-6 months of expenses",
                "Open high-yield savings account",
                "Set up automatic transfers",
                "Monitor fund growth monthly"
            ],
            'debt_reduction': [
                "List all debts by interest rate",
                "Choose debt payoff strategy",
                "Increase minimum payments",
                "Track progress monthly"
            ],
            'expense_reduction': [
                "Review all monthly expenses",
                "Identify non-essential spending",
                "Negotiate recurring bills",
                "Implement spending tracking"
            ]
        }
        
        return step_mapping.get(rec_type, ["Review recommendation details", "Create implementation plan"])
    
    def _generate_portfolio_steps(self, rec: Any) -> List[str]:
        """Generate specific steps for portfolio recommendations"""
        rec_type = getattr(rec, 'recommendation_type', 'unknown')
        
        step_mapping = {
            'rebalance': [
                "Calculate current allocation percentages",
                "Determine target allocation",
                "Identify positions to adjust",
                "Execute trades in tax-efficient manner"
            ],
            'diversify': [
                "Analyze current holdings concentration",
                "Research new asset classes or sectors",
                "Select appropriate investments",
                "Implement gradual diversification"
            ]
        }
        
        return step_mapping.get(rec_type, ["Analyze current portfolio", "Research implementation options"])
    
    def _generate_risk_steps(self, rec: Any) -> List[str]:
        """Generate specific steps for risk recommendations"""
        return [
            "Assess current risk exposure",
            "Research risk mitigation options",
            "Implement risk reduction measures",
            "Monitor risk levels regularly"
        ]
    
    def _generate_financial_metrics(self, rec: Any) -> List[str]:
        """Generate success metrics for financial recommendations"""
        return [
            "Monthly expense ratio improvement",
            "Emergency fund months coverage",
            "Debt-to-income ratio reduction",
            "Net worth growth rate"
        ]
    
    def _generate_portfolio_metrics(self, rec: Any) -> List[str]:
        """Generate success metrics for portfolio recommendations"""
        return [
            "Portfolio allocation deviation from target",
            "Risk-adjusted returns (Sharpe ratio)",
            "Portfolio volatility reduction",
            "Diversification coefficient improvement"
        ]
    
    def _generate_risk_metrics(self, rec: Any) -> List[str]:
        """Generate success metrics for risk recommendations"""
        return [
            "Overall portfolio risk score",
            "Maximum position concentration",
            "Sector concentration levels",
            "Portfolio volatility measures"
        ]
    
    def _apply_user_preferences(self, actions: List[PrioritizedAction], 
                               preferences: Dict[str, Any]) -> List[PrioritizedAction]:
        """Apply user preferences to modify action priorities"""
        # This could adjust priorities based on user risk tolerance,
        # time availability, financial goals, etc.
        
        risk_tolerance = preferences.get('risk_tolerance', 'moderate')
        time_availability = preferences.get('time_availability', 'medium')
        
        for action in actions:
            # Adjust based on risk tolerance
            if risk_tolerance == 'conservative' and action.action_type == ActionType.REDUCE_RISK:
                action.priority_score *= 1.2
            elif risk_tolerance == 'aggressive' and action.action_type in [ActionType.BUY, ActionType.OPTIMIZE]:
                action.priority_score *= 1.1
            
            # Adjust based on time availability
            if time_availability == 'low' and action.effort_required == 'high':
                action.priority_score *= 0.8
            elif time_availability == 'high' and action.effort_required == 'low':
                action.priority_score *= 1.1
        
        return actions
