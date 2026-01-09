"""
Analysis Configuration Management

Handles configuration for different analysis scenarios and user preferences.
Provides standardized configuration profiles for different risk tolerances and analysis types.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
import yaml
import os

class RiskProfile(Enum):
    """Risk tolerance profiles for portfolio optimization"""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"

class OptimizationStrategy(Enum):
    """Portfolio optimization strategies"""
    RISK_PARITY = "risk_parity"
    MEAN_VARIANCE = "mean_variance"
    MIN_VARIANCE = "min_variance" 
    MAX_SHARPE = "max_sharpe"
    ALL_STRATEGIES = "all_strategies"

@dataclass
class AnalysisConfig:
    """Configuration class for unified analysis"""
    
    # Risk and optimization preferences
    risk_profile: RiskProfile = RiskProfile.BALANCED
    optimization_strategy: OptimizationStrategy = OptimizationStrategy.ALL_STRATEGIES
    
    # Rebalancing preferences
    rebalancing_threshold: float = 0.05  # 5% drift threshold
    min_trade_amount: float = 1000.0     # Minimum trade size
    
    # Analysis preferences
    include_cash_flow_analysis: bool = True
    include_performance_attribution: bool = True
    include_risk_analysis: bool = True
    include_tax_analysis: bool = False  # Phase 5 feature
    
    # Reporting preferences
    generate_excel_report: bool = True
    generate_web_dashboard: bool = True
    include_charts: bool = True
    chart_style: str = "professional"
    
    # Data source preferences
    data_source_priority: List[str] = field(default_factory=lambda: [
        "excel_holdings", "excel_transactions", "excel_balance_sheet", "excel_cash_flow"
    ])
    
    # Output preferences
    output_directory: str = "output"
    report_filename_prefix: str = "financial_analysis"
    
    # Advanced settings
    monte_carlo_simulations: int = 1000
    confidence_intervals: List[float] = field(default_factory=lambda: [0.05, 0.95])
    lookback_periods: Dict[str, int] = field(default_factory=lambda: {
        "short_term": 3,  # months
        "medium_term": 12,  # months
        "long_term": 36   # months
    })

class ConfigManager:
    """Manages analysis configuration loading, saving, and validation"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/analysis_config.yaml"
        self.config = AnalysisConfig()
        
    def load_config(self, config_path: Optional[str] = None) -> AnalysisConfig:
        """Load configuration from YAML file"""
        path = config_path or self.config_path
        
        if os.path.exists(path):
            try:
                with open(path, 'r') as file:
                    config_data = yaml.safe_load(file)
                    
                # Update config with loaded values
                for key, value in config_data.items():
                    if hasattr(self.config, key):
                        # Handle enum values
                        if key == 'risk_profile':
                            value = RiskProfile(value)
                        elif key == 'optimization_strategy':
                            value = OptimizationStrategy(value)
                        
                        setattr(self.config, key, value)
                        
            except Exception as e:
                print(f"Warning: Could not load config from {path}: {e}")
                print("Using default configuration")
        
        return self.config
    
    def save_config(self, config: Optional[AnalysisConfig] = None, 
                   config_path: Optional[str] = None) -> None:
        """Save configuration to YAML file"""
        config = config or self.config
        path = config_path or self.config_path
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Convert config to dictionary
        config_dict = {}
        for key, value in config.__dict__.items():
            if isinstance(value, Enum):
                config_dict[key] = value.value
            else:
                config_dict[key] = value
        
        with open(path, 'w') as file:
            yaml.dump(config_dict, file, default_flow_style=False, indent=2)
    
    def get_risk_profile_settings(self, risk_profile: RiskProfile) -> Dict[str, Any]:
        """Get predefined settings for a risk profile"""
        profiles = {
            RiskProfile.CONSERVATIVE: {
                "rebalancing_threshold": 0.03,  # 3% threshold
                "min_trade_amount": 500.0,
                "optimization_strategy": OptimizationStrategy.MIN_VARIANCE
            },
            RiskProfile.BALANCED: {
                "rebalancing_threshold": 0.05,  # 5% threshold
                "min_trade_amount": 1000.0,
                "optimization_strategy": OptimizationStrategy.RISK_PARITY
            },
            RiskProfile.AGGRESSIVE: {
                "rebalancing_threshold": 0.07,  # 7% threshold
                "min_trade_amount": 2000.0,
                "optimization_strategy": OptimizationStrategy.MAX_SHARPE
            }
        }
        
        return profiles.get(risk_profile, profiles[RiskProfile.BALANCED])
    
    def apply_risk_profile(self, risk_profile: RiskProfile) -> None:
        """Apply predefined settings for a risk profile"""
        settings = self.get_risk_profile_settings(risk_profile)
        
        self.config.risk_profile = risk_profile
        for key, value in settings.items():
            setattr(self.config, key, value)
    
    def validate_config(self, config: Optional[AnalysisConfig] = None) -> List[str]:
        """Validate configuration and return list of issues"""
        config = config or self.config
        issues = []
        
        # Validate thresholds
        if config.rebalancing_threshold <= 0 or config.rebalancing_threshold > 1:
            issues.append("Rebalancing threshold must be between 0 and 1")
            
        if config.min_trade_amount < 0:
            issues.append("Minimum trade amount must be positive")
            
        # Validate confidence intervals
        for ci in config.confidence_intervals:
            if ci <= 0 or ci >= 1:
                issues.append(f"Confidence interval {ci} must be between 0 and 1")
        
        # Validate lookback periods
        for period, months in config.lookback_periods.items():
            if months <= 0:
                issues.append(f"Lookback period {period} must be positive")
        
        return issues
