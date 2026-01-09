"""
Recommendation Engine Module

This module provides comprehensive recommendation capabilities for personal finance
and investment optimization. It generates actionable insights based on financial
analysis and portfolio optimization results.

Key Components:
- FinancialAdvisor: Financial health and cash flow recommendations (legacy)
- PortfolioAdvisor: Portfolio optimization and rebalancing recommendations (legacy)
- RecommendationEngine: Multi-dimensional recommendation orchestrator (V2.0)
- ProportionalAllocationOptimizer: Proportional capital allocation
- SubClassAnalyzer: Sub-class breakdown recommendations
- RiskAdvisor: Risk management and diversification recommendations
- ActionPrioritizer: Recommendation prioritization and implementation guidance
"""

from .financial_advisor import FinancialAdvisor, FinancialRecommendation
from .portfolio_advisor import PortfolioAdvisor, PortfolioRecommendation
from .risk_advisor import RiskAdvisor, RiskRecommendation, RiskAssessment
from .action_prioritizer import ActionPrioritizer, PrioritizedAction, ActionPlan
from .comprehensive_engine import (
    ComprehensiveRecommendationEngine, 
    RecommendationEngineConfig,
    ComprehensiveRecommendationResult
)

__all__ = [
    'FinancialAdvisor',
    'PortfolioAdvisor', 
    'RiskAdvisor',
    'ActionPrioritizer',
    'ComprehensiveRecommendationEngine',
    'FinancialRecommendation',
    'PortfolioRecommendation',
    'RiskRecommendation',
    'RiskAssessment',
    'PrioritizedAction',
    'ActionPlan',
    'RecommendationEngineConfig',
    'ComprehensiveRecommendationResult',
    # V2.0 Components
    'RecommendationEngine',
    'ProportionalAllocationOptimizer',
    'SubClassAnalyzer'
]

__version__ = "1.0.0"
