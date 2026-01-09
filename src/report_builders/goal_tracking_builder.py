import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from src.data_manager.manager import DataManager
from src.goal_planning.simulation import MonteCarloSimulation
# We assume GoalManager exists in src.goal_planning.goal_manager or similar
# If not found, we will mock/stub it for now as per the plan to rebuild integration layer
try:
    from src.goal_planning.goal_manager import GoalManager
except ImportError:
    # Fallback if GoalManager is not yet available in the expected path
    class GoalManager:
        def __init__(self, config_path=None): pass
        def list_goals(self): return {}
        def get_goal(self, goal_id): return None

class GoalTrackingBuilder:
    """
    Builder for goal tracking and Monte Carlo simulation data.
    Implements 'Bucket' allocation strategy to prevent double-counting of assets.
    """
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.logger = logging.getLogger(__name__)
        self.goal_manager = GoalManager(config_path='config/goals.yaml')
        self.monte_carlo = MonteCarloSimulation(self.goal_manager)

    def build_goal_data(self) -> Dict[str, Any]:
        """
        Build comprehensive goal tracking data.
        
        Returns:
            Dictionary containing:
            - summary: Overall progress metrics
            - goals: List of individual goal details with Monte Carlo results
            - allocation_chart: Data showing how portfolio is split across goals
        """
        self.logger.info("Building goal tracking data")
        
        try:
            # 1. Get current portfolio value (Logic aligned with Real Report)
            # Try to get sum of all holdings first (includes illiquid assets)
            current_holdings = self.data_manager.get_holdings(latest_only=True)
            current_portfolio_value = 0.0
            
            if current_holdings is not None and not current_holdings.empty:
                current_portfolio_value = current_holdings['Market_Value_CNY'].sum()
                self.logger.info(f"Using holdings sum for goal tracking: {current_portfolio_value}")
            
            # Fallback to balance sheet if holdings sum is 0
            if current_portfolio_value == 0:
                balance_sheet = self.data_manager.get_balance_sheet()
                if balance_sheet is not None and not balance_sheet.empty:
                    current_portfolio_value = balance_sheet['Total_Assets_Calc_CNY'].iloc[-1]
                    self.logger.info(f"Fallback to balance sheet for goal tracking: {current_portfolio_value}")
                
            # 2. Get goals
            try:
                goals_dict = self.goal_manager.list_goals()
                if not goals_dict:
                    self.logger.warning("No goals found in GoalManager, using mocks")
                    goals = self._get_mock_goals()
                else:
                    # Convert Dict[str, Goal] to List[Dict]
                    goals = []
                    for goal_id, goal_obj in goals_dict.items():
                        goal_data = goal_obj.to_dict()
                        goal_data['id'] = goal_id # Ensure ID is present
                        goals.append(goal_data)
            except Exception as e:
                self.logger.warning(f"Error fetching goals from manager: {e}, using mocks")
                goals = self._get_mock_goals()
            
            # 3. Allocate assets to goals (The FIX for double-counting)
            allocations = self._allocate_assets_to_goals(current_portfolio_value, goals)
            
            # 4. Run Monte Carlo for each goal using allocated amounts
            goal_results = []
            for goal in goals:
                goal_id = goal['id']
                allocated_amount = allocations.get(goal_id, 0.0)
                
                # Run simulation with specific starting value
                mc_result = self._run_simulation_for_goal(goal, allocated_amount)
                
                goal_data = {
                    'id': goal_id,
                    'name': goal['name'],
                    'target_amount': goal['target_amount'],
                    'current_value': allocated_amount,
                    'progress_pct': (allocated_amount / goal['target_amount']) * 100 if goal['target_amount'] > 0 else 0,
                    'status': self._determine_status(allocated_amount, goal['target_amount'], mc_result),
                    'monte_carlo': mc_result
                }
                goal_results.append(goal_data)
                
            # 5. Build allocation chart data
            allocation_chart = {
                'labels': [g['name'] for g in goals] + ['Unallocated'],
                'data': [allocations.get(g['id'], 0.0) for g in goals]
            }
            # Calculate unallocated
            total_allocated = sum(allocation_chart['data'])
            unallocated = max(0, current_portfolio_value - total_allocated)
            allocation_chart['data'].append(unallocated)
            
            # Fix: Count both 'On Track' and 'Achieved' as on track
            on_track_count = sum(1 for g in goal_results if g['status'] in ['On Track', 'Achieved'])
            
            return {
                'summary': {
                    'total_portfolio': current_portfolio_value,
                    'total_allocated': total_allocated,
                    'goals_on_track': on_track_count,
                    'total_goals': len(goals)
                },
                'goals': goal_results,
                'allocation_chart': allocation_chart
            }

        except Exception as e:
            self.logger.error(f"Error building goal data: {str(e)}")
            return {'goals': [], 'summary': {}, 'error': str(e)}

    def _allocate_assets_to_goals(self, total_portfolio: float, goals: List[Dict]) -> Dict[str, float]:
        """
        Allocate portfolio assets to goals based on priority/buckets.
        Prevents double-counting by consuming the 'available' portfolio.
        
        Args:
            total_portfolio: Total current portfolio value
            goals: List of goal dictionaries (must be sorted by priority)
            
        Returns:
            Dictionary mapping goal_id to allocated amount
        """
        allocations = {}
        remaining_portfolio = total_portfolio
        
        # Sort goals by priority (1 is highest)
        sorted_goals = sorted(goals, key=lambda x: x.get('priority', 999))
        
        for goal in sorted_goals:
            target = goal['target_amount']
            
            # Simple bucket logic: Fill high priority goals first
            # In a more complex version, we could map specific asset classes to goals
            # e.g. Cash -> Emergency Fund
            
            if remaining_portfolio <= 0:
                allocations[goal['id']] = 0.0
                continue
                
            # Allocate up to the target amount, or whatever is left
            # For 'accumulation' goals (like retirement), we might allocate everything remaining
            # But for fixed targets (house), we cap at target.
            
            if goal.get('type') == 'accumulation':
                # Accumulation goals take everything available (usually lowest priority)
                allocated = remaining_portfolio
            else:
                # Fixed target goals take what they need
                allocated = min(remaining_portfolio, target)
            
            allocations[goal['id']] = allocated
            remaining_portfolio -= allocated
            
        return allocations

    def _run_simulation_for_goal(self, goal: Dict, initial_value: float) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation for a specific goal.
        """
        # Placeholder for actual MC run
        # In real implementation: 
        # return self.monte_carlo.run_simulation(initial_value, goal['time_horizon'], ...)
        
        # Mock result
        return {
            'success_probability': 0.85 if initial_value > goal['target_amount'] * 0.5 else 0.4,
            'percentiles': {
                'p10': [initial_value * (1.02 ** i) for i in range(10)],
                'p50': [initial_value * (1.05 ** i) for i in range(10)],
                'p90': [initial_value * (1.08 ** i) for i in range(10)]
            },
            'years': list(range(10))
        }

    def _determine_status(self, current: float, target: float, mc_result: Dict) -> str:
        if current >= target:
            return "Achieved"
        if mc_result['success_probability'] > 0.8:
            return "On Track"
        if mc_result['success_probability'] > 0.5:
            return "At Risk"
        return "Critical"

    def _get_mock_goals(self) -> List[Dict]:
        """Temporary mock goals until GoalManager integration is complete."""
        return [
            {
                'id': 'emergency',
                'name': 'Emergency Fund',
                'target_amount': 100000, # 100k CNY
                'priority': 1,
                'type': 'fixed',
                'time_horizon': 1
            },
            {
                'id': 'house',
                'name': 'House Down Payment',
                'target_amount': 1000000, # 1M CNY
                'priority': 2,
                'type': 'fixed',
                'time_horizon': 3
            },
            {
                'id': 'retirement',
                'name': 'Retirement',
                'target_amount': 10000000, # 10M CNY
                'priority': 3,
                'type': 'accumulation', # Takes remaining
                'time_horizon': 20
            }
        ]
