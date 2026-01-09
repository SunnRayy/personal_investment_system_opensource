import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

from src.goal_planning.goal_manager import GoalManager
from src.goal_planning.simulation import MonteCarloSimulation, DeterministicProjection, ProjectionResult, MonteCarloResult

logger = logging.getLogger(__name__)

class SimulationService:
    """
    Service to handle financial simulations (Monte Carlo and Deterministic) for the Web UI.
    Provides a caching layer and abstracts the simulation engine.
    """
    
    CACHE_DIR = Path('data/cache/simulation')
    
    def __init__(self, config_path: str = 'config/settings.yaml', goal_config_path: str = 'config/goals.yaml'):
        """Initialize SimulationService with goal manager and engines."""
        # Use goal_config_path if provided, otherwise check for existence
        if not Path(goal_config_path).exists() and Path('config/goal_config.yaml').exists():
            goal_config_path = 'config/goal_config.yaml'
            
        self.goal_manager = GoalManager(config_path=goal_config_path)
        self.mc_engine = MonteCarloSimulation(self.goal_manager)
        self.det_engine = DeterministicProjection(self.goal_manager)
        
        # Ensure cache directory exists
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def run_monte_carlo(self, 
                       initial_value: float,
                       expected_return: float,
                       volatility: float,
                       annual_contribution: float = 0.0,
                       num_simulations: int = 1000,
                       force_refresh: bool = False) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation and return JSON-serializable results.
        """
        # Create cache key based on primary parameters
        cache_key = f"mc_{initial_value}_{expected_return}_{volatility}_{annual_contribution}_{num_simulations}.json"
        cache_path = self.CACHE_DIR / cache_key
        
        if not force_refresh and cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading MC cache: {e}")

        # Run simulation
        result = self.mc_engine.run_simulation(
            initial_portfolio_value=initial_value,
            expected_annual_return=expected_return,
            market_volatility=volatility,
            annual_contribution=annual_contribution,
            num_simulations=num_simulations
        )
        
        # Process results for Web UI (JSON serializable)
        processed_result = self._process_mc_result(result)
        
        # Cache results
        try:
            with open(cache_path, 'w') as f:
                json.dump(processed_result, f)
        except Exception as e:
            logger.error(f"Error saving MC cache: {e}")
            
        return processed_result

    def _process_mc_result(self, result: MonteCarloResult) -> Dict[str, Any]:
        """Convert MonteCarloResult to a JSON-ready dictionary."""
        # Calculate aggregate success rate (percentage of goals with > 75% probability)
        total_goals = len(result.goal_probabilities)
        if total_goals > 0:
            goals_met = sum(1 for prob in result.goal_probabilities.values() if prob >= 0.75)
            aggregate_success_rate = goals_met / total_goals
        else:
            aggregate_success_rate = 0.0

        # Primary goal info for fallback (e.g., Retirement)
        primary_goal_id = next((gid for gid in result.goal_probabilities if 'retirement' in gid.lower()), None)
        if not primary_goal_id and result.goal_probabilities:
             primary_goal_id = list(result.goal_probabilities.keys())[0]

        return {
            'years': result.years,
            'dates': [d.isoformat() for d in result.dates],
            'percentiles': result.percentiles,
            'goal_probabilities': result.goal_probabilities,
            'aggregate_success_rate': aggregate_success_rate,
            'primary_goal_id': primary_goal_id,
            'summary': {
                'median_final_value': result.percentiles.get('p50', [0])[-1],
                'p5_final_value': result.percentiles.get('p5', [0])[-1],
                'p95_final_value': result.percentiles.get('p95', [0])[-1],
                'projection_years': len(result.years) - 1
            },
            'assumptions': result.assumptions,
            'timestamp': datetime.now().isoformat()
        }

    def get_simulation_metadata(self) -> Dict[str, Any]:
        """Get information about goals and current assumptions."""
        goals = self.goal_manager.list_goals()
        config = self.goal_manager.get_planning_config()
        
        return {
            'goals': [
                {
                    'id': g_id,
                    'name': g.name,
                    'target_amount': g.target_amount,
                    'target_date': g.target_date.isoformat(),
                    'priority': g.priority,
                    'category': g.category,
                    'years_remaining': g.years_remaining
                } for g_id, g in goals.items()
            ],
            'default_assumptions': config.get('assumptions', {}),
            'simulation_config': config.get('simulation', {})
        }
