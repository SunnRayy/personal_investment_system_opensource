"""
Simulation Engine Module

This module provides functionality for projecting portfolio growth and analyzing
goal achievement probability using various simulation methods.

Classes:
    DeterministicProjection: Simple linear growth projections
    MonteCarloSimulation: Probabilistic simulation with market volatility
    GoalAnalyzer: Integration between goals and portfolio projections
"""

from datetime import date
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging
import numpy as np

from .goal_manager import GoalManager

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ProjectionResult:
    """
    Container for projection results with yearly breakdown.
    """
    years: List[int]
    dates: List[date]
    portfolio_values: List[float]
    goal_progress: Dict[str, List[float]]  # goal_id -> list of progress percentages
    goal_status: Dict[str, str]  # goal_id -> 'on_track', 'behind', 'achieved'
    assumptions: Dict[str, Any]


@dataclass
class MonteCarloResult:
    """
    Container for Monte Carlo simulation results.
    """
    years: List[int]
    dates: List[date]
    simulations: np.ndarray  # Shape: (num_simulations, num_years)
    percentiles: Dict[str, List[float]]  # percentile -> portfolio values by year
    goal_probabilities: Dict[str, float]  # goal_id -> probability of success
    final_values: List[float]  # Final portfolio values for all simulations
    assumptions: Dict[str, Any]


class DeterministicProjection:
    """
    Implements deterministic (fixed return) portfolio growth projections.
    """
    
    def __init__(self, goal_manager: GoalManager):
        """
        Initialize the deterministic projection engine.
        
        Args:
            goal_manager: GoalManager instance with loaded goals and configuration
        """
        self.goal_manager = goal_manager
        self.planning_config = goal_manager.get_planning_config()
        
        # Validate that planning configuration is available
        config_status = goal_manager.get_planning_config_status()
        if not config_status['valid']:
            raise ValueError(f"Planning configuration validation failed: {config_status['errors']}")
    
    def project_portfolio_growth(
        self,
        initial_portfolio_value: float,
        annual_return_rate: Optional[float] = None,
        annual_contribution: float = 0.0,
        contribution_growth_rate: float = 0.0,
        end_date: Optional[date] = None
    ) -> ProjectionResult:
        """
        Project portfolio growth using deterministic (fixed) returns.
        
        Args:
            initial_portfolio_value: Starting portfolio value
            annual_return_rate: Annual return rate (decimal). If None, uses default from config
            annual_contribution: Annual contribution amount
            contribution_growth_rate: Annual growth rate for contributions (e.g., salary increases)
            end_date: End date for projection. If None, uses latest goal target date
            
        Returns:
            ProjectionResult containing yearly projections and goal analysis
        """
        # Get parameters from configuration if not provided
        if annual_return_rate is None:
            assumptions = self.planning_config.get('assumptions', {})
            annual_return_rate = assumptions.get('default_investment_return', 0.07)
        
        # Determine projection end date
        if end_date is None:
            goals = self.goal_manager.list_goals()
            if not goals:
                raise ValueError("No goals defined and no end_date provided")
            end_date = max(goal.target_date for goal in goals.values())
        
        # Calculate projection period
        start_date = date.today()
        years_to_project = max(1, int((end_date - start_date).days / 365.25) + 1)
        
        logger.info(f"Projecting portfolio growth for {years_to_project} years")
        logger.info(f"Initial value: ${initial_portfolio_value:,.2f}")
        logger.info(f"Annual return: {annual_return_rate:.2%}")
        logger.info(f"Annual contribution: ${annual_contribution:,.2f}")
        
        # Initialize result containers
        years = list(range(years_to_project + 1))  # Include year 0
        dates = [start_date.replace(year=start_date.year + year) for year in years]
        portfolio_values = []
        goal_progress = {goal_id: [] for goal_id in self.goal_manager.list_goals().keys()}
        
        # Calculate yearly projections
        current_value = initial_portfolio_value
        current_contribution = annual_contribution
        
        for year in years:
            # Add current value to results
            portfolio_values.append(current_value)
            
            # Calculate goal progress for this year
            for goal_id, goal in self.goal_manager.list_goals().items():
                progress_pct = min(current_value / goal.target_amount * 100, 100.0)
                goal_progress[goal_id].append(progress_pct)
            
            # Project to next year (skip for last year)
            if year < years_to_project:
                # Apply investment returns
                current_value *= (1 + annual_return_rate)
                
                # Add contributions
                current_value += current_contribution
                
                # Grow contributions for next year
                current_contribution *= (1 + contribution_growth_rate)
        
        # Analyze goal achievement status
        goal_status = self._analyze_goal_status(portfolio_values, dates)
        
        # Prepare assumptions dictionary
        assumptions = {
            'initial_portfolio_value': initial_portfolio_value,
            'annual_return_rate': annual_return_rate,
            'annual_contribution': annual_contribution,
            'contribution_growth_rate': contribution_growth_rate,
            'projection_years': years_to_project,
            'end_date': end_date.isoformat(),
            'method': 'deterministic'
        }
        
        return ProjectionResult(
            years=years,
            dates=dates,
            portfolio_values=portfolio_values,
            goal_progress=goal_progress,
            goal_status=goal_status,
            assumptions=assumptions
        )
    
    def _analyze_goal_status(
        self, 
        portfolio_values: List[float], 
        dates: List[date]
    ) -> Dict[str, str]:
        """
        Analyze whether goals are on track based on projection results.
        
        Args:
            portfolio_values: List of projected portfolio values
            dates: List of projection dates
            
        Returns:
            Dictionary mapping goal_id to status ('achieved', 'on_track', 'behind', 'at_risk')
        """
        goal_status = {}
        
        for goal_id, goal in self.goal_manager.list_goals().items():
            # Find the projected value closest to the goal's target date
            target_date = goal.target_date
            
            # Find the closest date index
            date_diffs = [abs((d - target_date).days) for d in dates]
            closest_idx = date_diffs.index(min(date_diffs))
            
            projected_value = portfolio_values[closest_idx]
            progress_ratio = projected_value / goal.target_amount
            
            if progress_ratio >= 1.0:
                status = 'achieved'
            elif progress_ratio >= 0.9:  # Within 10% of target
                status = 'on_track'
            elif progress_ratio >= 0.7:  # Within 30% of target
                status = 'behind'
            else:
                status = 'at_risk'
            
            goal_status[goal_id] = status
            
            logger.debug(f"Goal '{goal.name}': {progress_ratio:.1%} of target -> {status}")
        
        return goal_status
    
    def generate_projection_summary(self, result: ProjectionResult) -> Dict[str, Any]:
        """
        Generate a summary of the projection results.
        
        Args:
            result: ProjectionResult from project_portfolio_growth
            
        Returns:
            Dictionary with summary statistics
        """
        final_value = result.portfolio_values[-1]
        initial_value = result.portfolio_values[0]
        total_growth = final_value - initial_value
        total_years = len(result.years) - 1
        
        # Calculate goal achievement summary
        goals = self.goal_manager.list_goals()
        total_goal_target = sum(goal.target_amount for goal in goals.values())
        
        status_counts = {}
        for status in result.goal_status.values():
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'projection_period': f"{total_years} years",
            'initial_portfolio_value': initial_value,
            'final_portfolio_value': final_value,
            'total_growth': total_growth,
            'annualized_growth_rate': (final_value / initial_value) ** (1/total_years) - 1 if total_years > 0 else 0,
            'total_goal_target': total_goal_target,
            'goal_coverage_ratio': final_value / total_goal_target if total_goal_target > 0 else 0,
            'goals_analysis': {
                'total_goals': len(goals),
                'achieved': status_counts.get('achieved', 0),
                'on_track': status_counts.get('on_track', 0),
                'behind': status_counts.get('behind', 0),
                'at_risk': status_counts.get('at_risk', 0)
            },
            'assumptions': result.assumptions
        }


class GoalAnalyzer:
    """
    Integrates goal planning with portfolio projections and existing analysis modules.
    """
    
    def __init__(self, goal_manager: GoalManager):
        """
        Initialize the goal analyzer.
        
        Args:
            goal_manager: GoalManager instance with loaded goals
        """
        self.goal_manager = goal_manager
        self.deterministic = DeterministicProjection(goal_manager)
    
    def analyze_goal_feasibility(
        self,
        current_portfolio_value: float,
        annual_contribution: float = 0.0,
        scenarios: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Analyze the feasibility of achieving goals under different scenarios.
        
        Args:
            current_portfolio_value: Current portfolio value
            annual_contribution: Annual contribution amount
            scenarios: Dictionary of scenario_name -> annual_return_rate
            
        Returns:
            Dictionary with feasibility analysis for each scenario
        """
        if scenarios is None:
            # Default scenarios based on historical market performance
            scenarios = {
                'conservative': 0.04,  # 4% annual return
                'moderate': 0.07,      # 7% annual return
                'aggressive': 0.10     # 10% annual return
            }
        
        results = {}
        
        for scenario_name, return_rate in scenarios.items():
            try:
                projection = self.deterministic.project_portfolio_growth(
                    initial_portfolio_value=current_portfolio_value,
                    annual_return_rate=return_rate,
                    annual_contribution=annual_contribution
                )
                
                summary = self.deterministic.generate_projection_summary(projection)
                
                results[scenario_name] = {
                    'return_rate': return_rate,
                    'final_value': projection.portfolio_values[-1],
                    'goal_status': projection.goal_status,
                    'summary': summary
                }
                
                logger.info(f"Scenario '{scenario_name}' ({return_rate:.1%}): "
                          f"Final value ${projection.portfolio_values[-1]:,.0f}")
                
            except Exception as e:
                logger.error(f"Error analyzing scenario '{scenario_name}': {e}")
                results[scenario_name] = {'error': str(e)}
        
        return results
    
    def calculate_required_return(
        self,
        current_portfolio_value: float,
        goal_id: str,
        annual_contribution: float = 0.0
    ) -> float:
        """
        Calculate the annual return rate required to achieve a specific goal.
        
        Args:
            current_portfolio_value: Current portfolio value
            goal_id: ID of the goal to analyze
            annual_contribution: Annual contribution amount
            
        Returns:
            Required annual return rate (decimal)
        """
        goal = self.goal_manager.get_goal(goal_id)
        if not goal:
            raise ValueError(f"Goal '{goal_id}' not found")
        
        years_remaining = goal.years_remaining
        target_amount = goal.target_amount
        
        if years_remaining <= 0:
            return float('inf')  # Goal is overdue
        
        # Calculate required return using compound growth formula
        # Future Value = Present Value * (1 + r)^n + Contribution * [((1 + r)^n - 1) / r]
        # Solve for r using iterative method
        
        def future_value(rate):
            if rate == 0:
                return current_portfolio_value + annual_contribution * years_remaining
            else:
                investment_growth = current_portfolio_value * ((1 + rate) ** years_remaining)
                contribution_growth = annual_contribution * (((1 + rate) ** years_remaining - 1) / rate)
                return investment_growth + contribution_growth
        
        # Binary search for required return rate
        low_rate = -0.5  # -50%
        high_rate = 0.5   # 50%
        tolerance = 0.0001
        
        for _ in range(100):  # Max iterations
            mid_rate = (low_rate + high_rate) / 2
            projected_value = future_value(mid_rate)
            
            if abs(projected_value - target_amount) < tolerance:
                return mid_rate
            elif projected_value < target_amount:
                low_rate = mid_rate
            else:
                high_rate = mid_rate
        
        return (low_rate + high_rate) / 2  # Return best estimate


class MonteCarloSimulation:
    """
    Implements Monte Carlo portfolio growth simulations with market volatility.
    """
    
    def __init__(self, goal_manager: GoalManager):
        """
        Initialize the Monte Carlo simulation engine.
        
        Args:
            goal_manager: GoalManager instance with loaded goals and configuration
        """
        self.goal_manager = goal_manager
        self.planning_config = goal_manager.get_planning_config()
        
        # Validate configuration
        config_status = goal_manager.get_planning_config_status()
        if not config_status['valid']:
            raise ValueError(f"Invalid planning configuration: {config_status['errors']}")
        
        logger.info("Monte Carlo simulation engine initialized")
    
    def run_simulation(
        self,
        initial_portfolio_value: float,
        expected_annual_return: Optional[float] = None,
        market_volatility: Optional[float] = None,
        annual_contribution: float = 0.0,
        contribution_growth_rate: float = 0.0,
        num_simulations: Optional[int] = None,
        confidence_levels: Optional[List[float]] = None
    ) -> MonteCarloResult:
        """
        Run Monte Carlo simulation for portfolio growth.
        
        Args:
            initial_portfolio_value: Starting portfolio value
            expected_annual_return: Expected annual return (uses config default if None)
            market_volatility: Annual volatility (uses config default if None)
            annual_contribution: Annual contribution amount
            contribution_growth_rate: Annual growth rate for contributions
            num_simulations: Number of Monte Carlo simulations (uses config default if None)
            confidence_levels: List of confidence levels for percentile calculation
            
        Returns:
            MonteCarloResult with simulation outcomes
        """
        # Use configuration defaults if parameters not provided
        assumptions = self.planning_config['assumptions']
        simulation_config = self.planning_config['simulation']
        
        if initial_portfolio_value is None:
             # Fallback to default if not provided (though type hint says float, good for safety)
             initial_portfolio_value = assumptions.get('initial_portfolio_value', 0.0)

        if expected_annual_return is None:
            expected_annual_return = assumptions['default_investment_return']
        if market_volatility is None:
            market_volatility = simulation_config['market_volatility']
        if num_simulations is None:
            num_simulations = simulation_config['num_simulations']
        if confidence_levels is None:
            confidence_levels = simulation_config['confidence_levels']
        
        logger.info(f"Running Monte Carlo simulation with {num_simulations} iterations")
        logger.info(f"Initial Value: {initial_portfolio_value:,.2f}")
        logger.info(f"Expected return: {expected_annual_return:.2%}, Volatility: {market_volatility:.2%}")
        
        # Determine projection timeframe based on goals
        goals = self.goal_manager.list_goals()
        if not goals:
            raise ValueError("No goals defined for simulation")
        
        max_years = max(goal.years_remaining for goal in goals.values())
        projection_years = max(int(np.ceil(max_years)), 1)
        
        # Generate date sequence
        start_date = date.today()
        dates = []
        years = []
        for year in range(projection_years + 1):
            year_date = date(start_date.year + year, start_date.month, start_date.day)
            dates.append(year_date)
            years.append(year)
        
        # Run Monte Carlo simulations
        simulations = np.zeros((num_simulations, len(years)))
        simulations[:, 0] = initial_portfolio_value  # Set initial value
        
        # Set random seed for reproducible results
        np.random.seed(42)
        
        for sim in range(num_simulations):
            portfolio_value = initial_portfolio_value
            contribution = annual_contribution
            
            for year_idx in range(1, len(years)):
                # Generate random annual return
                annual_return = np.random.normal(expected_annual_return, market_volatility)
                
                # Apply investment growth
                portfolio_value = portfolio_value * (1 + annual_return)
                
                # Add annual contribution
                portfolio_value += contribution
                
                # Store result
                simulations[sim, year_idx] = portfolio_value
                
                # Grow contribution for next year
                contribution *= (1 + contribution_growth_rate)
        
        # Calculate percentiles
        percentiles = {}
        for confidence_level in confidence_levels:
            percentile = confidence_level * 100
            percentile_values = []
            for year_idx in range(len(years)):
                value = np.percentile(simulations[:, year_idx], percentile)
                percentile_values.append(value)
            percentiles[f"p{int(percentile)}"] = percentile_values
        
        # Calculate goal success probabilities
        goal_probabilities = {}
        for goal_id, goal in goals.items():
            if goal.years_remaining <= projection_years:
                year_idx = min(int(np.ceil(goal.years_remaining)), projection_years)
                year_idx = max(year_idx, 0)  # Ensure non-negative
                
                # Count simulations where goal is achieved
                achieved_count = np.sum(simulations[:, year_idx] >= goal.target_amount)
                probability = achieved_count / num_simulations
                goal_probabilities[goal_id] = probability
                
                logger.info(f"Goal '{goal.name}': {probability:.1%} success probability")
        
        # Extract final portfolio values
        final_values = simulations[:, -1].tolist()
        
        # Store assumptions used
        simulation_assumptions = {
            'initial_portfolio_value': initial_portfolio_value,
            'expected_annual_return': expected_annual_return,
            'market_volatility': market_volatility,
            'annual_contribution': annual_contribution,
            'contribution_growth_rate': contribution_growth_rate,
            'num_simulations': num_simulations,
            'projection_years': projection_years,
            'confidence_levels': confidence_levels
        }
        
        logger.info(f"Monte Carlo simulation completed successfully")
        
        return MonteCarloResult(
            years=years,
            dates=dates,
            simulations=simulations,
            percentiles=percentiles,
            goal_probabilities=goal_probabilities,
            final_values=final_values,
            assumptions=simulation_assumptions
        )
    
    def analyze_scenario_probabilities(
        self,
        initial_portfolio_value: float,
        annual_contribution: float = 0.0,
        scenarios: Optional[Dict[str, Dict[str, float]]] = None
    ) -> Dict[str, MonteCarloResult]:
        """
        Run Monte Carlo simulations for multiple market scenarios.
        
        Args:
            initial_portfolio_value: Starting portfolio value
            annual_contribution: Annual contribution amount
            scenarios: Dictionary of scenario_name -> {'return': float, 'volatility': float}
                      If None, uses predefined conservative/moderate/aggressive scenarios
            
        Returns:
            Dictionary mapping scenario names to MonteCarloResult objects
        """
        if scenarios is None:
            scenarios = {
                'conservative': {'return': 0.05, 'volatility': 0.10},
                'moderate': {'return': 0.07, 'volatility': 0.15},
                'aggressive': {'return': 0.10, 'volatility': 0.20}
            }
        
        results = {}
        for scenario_name, params in scenarios.items():
            try:
                logger.info(f"Running Monte Carlo scenario: {scenario_name}")
                result = self.run_simulation(
                    initial_portfolio_value=initial_portfolio_value,
                    expected_annual_return=params['return'],
                    market_volatility=params['volatility'],
                    annual_contribution=annual_contribution
                )
                results[scenario_name] = result
            except Exception as e:
                logger.error(f"Error running Monte Carlo scenario '{scenario_name}': {e}")
                results[scenario_name] = {'error': str(e)}
        
        return results
