"""
Goal Planning Module

This module provides functionality for defining, managing, and tracking financial goals,
including Monte Carlo simulations for goal achievement probability analysis.

Components:
- goal_manager: Goal definition and management
- simulation: Deterministic and Monte Carlo portfolio projections
- progress_tracker: Goal progress tracking and analysis (planned)
"""

__version__ = "1.0.0"
__author__ = "Personal Investment System"

from .goal_manager import GoalManager
from .simulation import DeterministicProjection, MonteCarloSimulation, GoalAnalyzer, ProjectionResult, MonteCarloResult
from .advisor import GoalAdvisor, ScenarioAnalysis, Recommendation, RecommendationPriority, RecommendationType

__all__ = [
    'GoalManager',
    'DeterministicProjection',
    'MonteCarloSimulation',
    'GoalAnalyzer', 
    'ProjectionResult',
    'MonteCarloResult',
    'GoalAdvisor',
    'ScenarioAnalysis',
    'Recommendation',
    'RecommendationPriority',
    'RecommendationType'
]