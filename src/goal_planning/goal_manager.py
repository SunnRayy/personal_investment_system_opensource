"""
Goal Manager Module

This module handles the loading, validation, and management of financial goals
defined in the goals.yaml configuration file.

Classes:
    Goal: Represents a single financial goal
    GoalManager: Manages collection of goals and provides analysis methods
"""

import yaml
from datetime import datetime, date
from typing import Dict, Optional, Union, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Goal:
    """
    Represents a single financial goal with all its attributes.
    """
    name: str
    target_amount: float
    target_date: Union[str, date]
    priority: str
    category: str
    description: str = ""
    current_progress: float = 0.0
    
    def __post_init__(self):
        """Convert string dates to date objects and validate data."""
        if isinstance(self.target_date, str):
            try:
                self.target_date = datetime.strptime(self.target_date, "%Y-%m-%d").date()
            except ValueError as e:
                raise ValueError(f"Invalid date format for goal '{self.name}': {self.target_date}. Expected YYYY-MM-DD") from e
        
        # Validate priority
        if self.priority not in ['high', 'medium', 'low']:
            raise ValueError(f"Invalid priority '{self.priority}' for goal '{self.name}'. Must be 'high', 'medium', or 'low'")
        
        # Validate amounts
        if self.target_amount <= 0:
            raise ValueError(f"Target amount must be positive for goal '{self.name}'")
        
        if self.current_progress < 0:
            raise ValueError(f"Current progress cannot be negative for goal '{self.name}'")
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress as a percentage of target."""
        if self.target_amount == 0:
            return 0.0
        return min(self.current_progress / self.target_amount * 100, 100.0)
    
    @property
    def remaining_amount(self) -> float:
        """Calculate remaining amount needed to reach goal."""
        return max(self.target_amount - self.current_progress, 0.0)
    
    @property
    def days_remaining(self) -> int:
        """Calculate days remaining until target date."""
        today = date.today()
        if isinstance(self.target_date, str):
            target = datetime.strptime(self.target_date, "%Y-%m-%d").date()
        else:
            target = self.target_date
        return (target - today).days
    
    @property
    def years_remaining(self) -> float:
        """Calculate years remaining until target date."""
        return self.days_remaining / 365.25
    
    @property
    def is_overdue(self) -> bool:
        """Check if the goal target date has passed."""
        return self.days_remaining < 0
    
    @property
    def monthly_savings_needed(self) -> float:
        """Calculate monthly savings needed to reach goal (without investment returns)."""
        if self.days_remaining <= 0:
            return float('inf') if self.remaining_amount > 0 else 0.0
        
        months_remaining = self.days_remaining / 30.44  # Average days per month
        return self.remaining_amount / months_remaining if months_remaining > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert goal to dictionary format."""
        goal_dict = asdict(self)
        # Convert date to string for JSON serialization
        if isinstance(goal_dict['target_date'], date):
            goal_dict['target_date'] = goal_dict['target_date'].isoformat()
        return goal_dict


class GoalManager:
    """
    Manages a collection of financial goals and provides analysis methods.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the Goal Manager.
        
        Args:
            config_path: Path to the goals.yaml file. If None, uses default location.
        """
        if config_path is None:
            # Default to config/goals.yaml relative to project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "goals.yaml"
        
        self.config_path = Path(config_path)
        self.goals: Dict[str, Goal] = {}
        self.planning_config: Dict[str, Any] = {}
        
        # Load goals if config file exists
        if self.config_path.exists():
            self.load_goals()
        else:
            logger.warning(f"Goals configuration file not found at {self.config_path}")
    
    def load_goals(self) -> None:
        """Load goals from the YAML configuration file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config_data = yaml.safe_load(file)
            
            # Load planning configuration
            self.planning_config = config_data.get('planning_config', {})
            
            # Validate planning configuration
            self._validate_planning_config()
            
            # Load and validate goals
            goals_data = config_data.get('goals', {})
            self.goals = {}
            
            for goal_id, goal_data in goals_data.items():
                try:
                    goal = Goal(**goal_data)
                    self.goals[goal_id] = goal
                    logger.info(f"Loaded goal: {goal.name}")
                except Exception as e:
                    logger.error(f"Error loading goal '{goal_id}': {e}")
                    continue
            
            logger.info(f"Successfully loaded {len(self.goals)} goals from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Error loading goals configuration: {e}")
            raise
    
    def _validate_planning_config(self) -> None:
        """
        Validate the planning_config section to ensure all critical parameters
        are present and have valid data types for simulation engine usage.
        """
        if not self.planning_config:
            logger.warning("No planning_config section found in goals configuration")
            return
        
        # Define required sections and their expected structure
        required_sections = {
            'assumptions': {
                'annual_inflation_rate': (float, int),
                'default_investment_return': (float, int),
                'risk_free_rate': (float, int)
            },
            'simulation': {
                'num_simulations': int,
                'confidence_levels': list,
                'market_volatility': (float, int)
            },
            'tracking': {
                'update_frequency': str,
                'rebalancing_threshold': (float, int),
                'alert_thresholds': dict
            },
            'categories': dict
        }
        
        validation_errors = []
        
        # Check each required section
        for section_name, expected_params in required_sections.items():
            if section_name not in self.planning_config:
                validation_errors.append(f"Missing required section: '{section_name}'")
                continue
            
            section_data = self.planning_config[section_name]
            
            # For dictionary sections with specific parameter requirements
            if isinstance(expected_params, dict):
                for param_name, expected_type in expected_params.items():
                    if param_name not in section_data:
                        validation_errors.append(f"Missing parameter '{param_name}' in section '{section_name}'")
                        continue
                    
                    param_value = section_data[param_name]
                    
                    # Handle tuple of allowed types (e.g., (float, int))
                    if isinstance(expected_type, tuple):
                        if not isinstance(param_value, expected_type):
                            validation_errors.append(
                                f"Parameter '{param_name}' in section '{section_name}' must be one of types {expected_type}, "
                                f"got {type(param_value).__name__}"
                            )
                    else:
                        if not isinstance(param_value, expected_type):
                            validation_errors.append(
                                f"Parameter '{param_name}' in section '{section_name}' must be {expected_type.__name__}, "
                                f"got {type(param_value).__name__}"
                            )
            
            # For sections that should just be dictionaries
            elif expected_params is dict:
                if not isinstance(section_data, dict):
                    validation_errors.append(f"Section '{section_name}' must be a dictionary")
        
        # Validate specific parameter ranges and values
        self._validate_parameter_ranges(validation_errors)
        
        # Log validation results
        if validation_errors:
            error_msg = "Planning configuration validation failed:\n" + "\n".join(f"  - {error}" for error in validation_errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        else:
            logger.info("Planning configuration validation passed")
    
    def _validate_parameter_ranges(self, validation_errors: list) -> None:
        """Validate that parameters are within reasonable ranges."""
        try:
            # Validate assumptions section
            assumptions = self.planning_config.get('assumptions', {})
            
            # Check inflation rate (should be between -0.1 and 0.2, i.e., -10% to 20%)
            if 'annual_inflation_rate' in assumptions:
                inflation = assumptions['annual_inflation_rate']
                if not (-0.1 <= inflation <= 0.2):
                    validation_errors.append(f"annual_inflation_rate should be between -10% and 20%, got {inflation:.1%}")
            
            # Check investment return (should be between -0.5 and 0.5, i.e., -50% to 50%)
            if 'default_investment_return' in assumptions:
                return_rate = assumptions['default_investment_return']
                if not (-0.5 <= return_rate <= 0.5):
                    validation_errors.append(f"default_investment_return should be between -50% and 50%, got {return_rate:.1%}")
            
            # Check risk-free rate (should be between 0 and 0.2, i.e., 0% to 20%)
            if 'risk_free_rate' in assumptions:
                risk_free = assumptions['risk_free_rate']
                if not (0 <= risk_free <= 0.2):
                    validation_errors.append(f"risk_free_rate should be between 0% and 20%, got {risk_free:.1%}")
            
            # Validate simulation section
            simulation = self.planning_config.get('simulation', {})
            
            # Check number of simulations (should be between 1000 and 100000)
            if 'num_simulations' in simulation:
                num_sims = simulation['num_simulations']
                if not (1000 <= num_sims <= 100000):
                    validation_errors.append(f"num_simulations should be between 1,000 and 100,000, got {num_sims:,}")
            
            # Check market volatility (should be between 0 and 1, i.e., 0% to 100%)
            if 'market_volatility' in simulation:
                volatility = simulation['market_volatility']
                if not (0 <= volatility <= 1):
                    validation_errors.append(f"market_volatility should be between 0% and 100%, got {volatility:.1%}")
            
            # Check confidence levels (should be list of values between 0 and 1)
            if 'confidence_levels' in simulation:
                conf_levels = simulation['confidence_levels']
                if isinstance(conf_levels, list):
                    for i, level in enumerate(conf_levels):
                        if not isinstance(level, (float, int)) or not (0 <= level <= 1):
                            validation_errors.append(f"confidence_levels[{i}] should be between 0 and 1, got {level}")
                    
                    # Check for duplicates
                    if len(conf_levels) != len(set(conf_levels)):
                        validation_errors.append("confidence_levels should not contain duplicates")
                    
                    # Check if sorted
                    if conf_levels != sorted(conf_levels):
                        logger.warning("confidence_levels should be sorted in ascending order for best results")
            
            # Validate tracking section
            tracking = self.planning_config.get('tracking', {})
            
            # Check rebalancing threshold (should be between 0 and 1)
            if 'rebalancing_threshold' in tracking:
                threshold = tracking['rebalancing_threshold']
                if not (0 <= threshold <= 1):
                    validation_errors.append(f"rebalancing_threshold should be between 0% and 100%, got {threshold:.1%}")
            
            # Check update frequency
            if 'update_frequency' in tracking:
                frequency = tracking['update_frequency']
                valid_frequencies = ['daily', 'weekly', 'monthly', 'quarterly', 'annually']
                if frequency not in valid_frequencies:
                    validation_errors.append(f"update_frequency must be one of {valid_frequencies}, got '{frequency}'")
            
        except Exception as e:
            validation_errors.append(f"Error during parameter range validation: {e}")
    
    def get_planning_config_status(self) -> Dict[str, Any]:
        """
        Get the validation status of the planning configuration.
        
        Returns:
            Dictionary with validation status and any issues found.
        """
        try:
            self._validate_planning_config()
            return {
                'valid': True,
                'errors': [],
                'warnings': [],
                'config_present': True
            }
        except ValueError as e:
            return {
                'valid': False,
                'errors': str(e).split('\n')[1:],  # Skip the first line (header)
                'warnings': [],
                'config_present': bool(self.planning_config)
            }
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Unexpected error during validation: {e}"],
                'warnings': [],
                'config_present': bool(self.planning_config)
            }
    
    def save_goals(self) -> None:
        """Save current goals back to the YAML configuration file."""
        try:
            # Prepare data structure
            config_data = {
                'goals': {},
                'planning_config': self.planning_config
            }
            
            # Convert goals to dictionaries
            for goal_id, goal in self.goals.items():
                config_data['goals'][goal_id] = goal.to_dict()
            
            # Write to file
            with open(self.config_path, 'w', encoding='utf-8') as file:
                yaml.dump(config_data, file, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Successfully saved {len(self.goals)} goals to {self.config_path}")
            
        except Exception as e:
            logger.error(f"Error saving goals configuration: {e}")
            raise
    
    def add_goal(self, goal_id: str, goal: Goal) -> None:
        """Add a new goal to the collection."""
        self.goals[goal_id] = goal
        logger.info(f"Added goal: {goal.name}")
    
    def update_goal(self, goal_id: str, goal_data: Dict[str, Any]) -> bool:
        """Update an existing goal's attributes."""
        if goal_id not in self.goals:
            # Try reloading in case file changed externally
            logger.info(f"Goal {goal_id} not found in memory, reloading from file...")
            self._load_goals()
            
        if goal_id not in self.goals:
            logger.warning(f"Attempted to update non-existent goal: '{goal_id}'")
            logger.warning(f"Available goals: {list(self.goals.keys())}")
            return False
            
        try:
            # Create new Goal object to validate data
            current_goal = self.goals[goal_id]
            updated_data = asdict(current_goal)
            updated_data.update(goal_data)
            
            # Remove 'id' if present, as it's not a field in the Goal class
            if 'id' in updated_data:
                del updated_data['id']
            
            # Handle date conversion if string provided
            if isinstance(updated_data.get('target_date'), str):
                updated_data['target_date'] = datetime.strptime(updated_data['target_date'], "%Y-%m-%d").date()
            
            # Handle numeric conversion
            if 'target_amount' in updated_data and isinstance(updated_data['target_amount'], str):
                updated_data['target_amount'] = float(updated_data['target_amount'])
                
            new_goal = Goal(**updated_data)
            self.goals[goal_id] = new_goal
            logger.info(f"Updated goal: {new_goal.name}")
            return True
        except Exception as e:
            logger.error(f"Error updating goal '{goal_id}': {e}")
            return False
    
    def remove_goal(self, goal_id: str) -> bool:
        """Remove a goal from the collection."""
        if goal_id in self.goals:
            goal_name = self.goals[goal_id].name
            del self.goals[goal_id]
            logger.info(f"Removed goal: {goal_name}")
            return True
        return False
    
    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Get a specific goal by ID."""
        return self.goals.get(goal_id)
    
    def list_goals(self) -> Dict[str, Goal]:
        """Get all goals."""
        return self.goals.copy()
    
    def get_goals_by_priority(self, priority: str) -> Dict[str, Goal]:
        """Get goals filtered by priority level."""
        return {
            goal_id: goal for goal_id, goal in self.goals.items()
            if goal.priority == priority
        }
    
    def get_goals_by_category(self, category: str) -> Dict[str, Goal]:
        """Get goals filtered by category."""
        return {
            goal_id: goal for goal_id, goal in self.goals.items()
            if goal.category == category
        }
    
    def get_overdue_goals(self) -> Dict[str, Goal]:
        """Get goals that are overdue."""
        return {
            goal_id: goal for goal_id, goal in self.goals.items()
            if goal.is_overdue
        }
    
    def get_goals_by_timeframe(self, years_threshold: float) -> Dict[str, Goal]:
        """Get goals within a specific timeframe (in years)."""
        return {
            goal_id: goal for goal_id, goal in self.goals.items()
            if 0 <= goal.years_remaining <= years_threshold
        }
    
    def update_goal_progress(self, goal_id: str, current_progress: float) -> bool:
        """Update the current progress for a specific goal."""
        if goal_id in self.goals:
            self.goals[goal_id].current_progress = current_progress
            logger.info(f"Updated progress for goal '{self.goals[goal_id].name}': ${current_progress:,.2f}")
            return True
        return False
    
    def get_planning_config(self, section: Optional[str] = None) -> Dict[str, Any]:
        """Get planning configuration or a specific section."""
        if section:
            return self.planning_config.get(section, {})
        return self.planning_config
    
    def calculate_total_target(self) -> float:
        """Calculate total target amount across all goals."""
        return sum(goal.target_amount for goal in self.goals.values())
    
    def calculate_total_progress(self) -> float:
        """Calculate total current progress across all goals."""
        return sum(goal.current_progress for goal in self.goals.values())
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for all goals."""
        if not self.goals:
            return {
                'total_goals': 0,
                'total_target_amount': 0.0,
                'total_current_progress': 0.0,
                'overall_progress_percentage': 0.0,
                'goals_by_priority': {'high': 0, 'medium': 0, 'low': 0},
                'overdue_goals': 0
            }
        
        total_target = self.calculate_total_target()
        total_progress = self.calculate_total_progress()
        
        return {
            'total_goals': len(self.goals),
            'total_target_amount': total_target,
            'total_current_progress': total_progress,
            'overall_progress_percentage': (total_progress / total_target * 100) if total_target > 0 else 0.0,
            'goals_by_priority': {
                'high': len(self.get_goals_by_priority('high')),
                'medium': len(self.get_goals_by_priority('medium')),
                'low': len(self.get_goals_by_priority('low'))
            },
            'overdue_goals': len(self.get_overdue_goals())
        }
    
    def __repr__(self) -> str:
        """String representation of the GoalManager."""
        return f"GoalManager(goals={len(self.goals)}, config_path={self.config_path})"
