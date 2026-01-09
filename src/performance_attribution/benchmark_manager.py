"""
Benchmark Manager for Performance Attribution

This module handles loading and managing benchmark configurations for 
performance attribution analysis. It integrates with the existing portfolio
system to provide benchmark data for attribution calculations.
"""

import yaml
import os
from typing import Dict, List, Optional, Tuple
import pandas as pd
from datetime import datetime, date
from pathlib import Path


class BenchmarkManager:
    """
    Manages benchmark configurations and data for performance attribution analysis
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize benchmark manager
        
        Args:
            config_path: Path to benchmark.yaml config file. If None, uses default location.
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
        self.current_benchmark = "strategic_benchmark"  # Default benchmark
        
    def _get_default_config_path(self) -> str:
        """Get default path to benchmark configuration file"""
        # Assume we're in src/performance_attribution, need to go up to find config
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent
        return str(project_root / "config" / "benchmark.yaml")
    
    def _load_config(self) -> Dict:
        """Load benchmark configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Benchmark config file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing benchmark config file: {e}")
    
    def get_benchmark_weights(self, benchmark_name: Optional[str] = None) -> Dict[str, float]:
        """
        Get benchmark asset allocation weights
        
        Args:
            benchmark_name: Name of benchmark to use. If None, uses current benchmark.
            
        Returns:
            Dictionary of asset class weights
        """
        benchmark_name = benchmark_name or self.current_benchmark
        
        if benchmark_name == "strategic_benchmark":
            weights = self.config["strategic_benchmark"]["weights"]
        elif benchmark_name in self.config.get("alternative_benchmarks", {}):
            weights = self.config["alternative_benchmarks"][benchmark_name]["weights"]
        else:
            raise ValueError(f"Unknown benchmark: {benchmark_name}")
        
        # Validate weights sum to 1.0
        weight_sum = sum(weights.values())
        tolerance = self.config.get("attribution_settings", {}).get("weight_tolerance", 0.01)
        
        if abs(weight_sum - 1.0) > tolerance:
            raise ValueError(f"Benchmark weights sum to {weight_sum:.4f}, expected 1.0")
        
        return weights
    
    def get_market_indices(self) -> Dict[str, Dict[str, str]]:
        """
        Get market index definitions for benchmark returns
        
        Returns:
            Dictionary mapping asset classes to their market index information
        """
        return self.config.get("market_indices", {})
    
    def get_benchmark_info(self, benchmark_name: Optional[str] = None) -> Dict[str, str]:
        """
        Get benchmark metadata (name, description, etc.)
        
        Args:
            benchmark_name: Name of benchmark. If None, uses current benchmark.
            
        Returns:
            Dictionary with benchmark information
        """
        benchmark_name = benchmark_name or self.current_benchmark
        
        if benchmark_name == "strategic_benchmark":
            return {
                "name": self.config["strategic_benchmark"]["name"],
                "description": self.config["strategic_benchmark"]["description"]
            }
        elif benchmark_name in self.config.get("alternative_benchmarks", {}):
            benchmark_config = self.config["alternative_benchmarks"][benchmark_name]
            return {
                "name": benchmark_config["name"],
                "description": benchmark_config["description"]
            }
        else:
            raise ValueError(f"Unknown benchmark: {benchmark_name}")
    
    def list_available_benchmarks(self) -> List[str]:
        """Get list of all available benchmark configurations"""
        benchmarks = ["strategic_benchmark"]
        alternative_benchmarks = self.config.get("alternative_benchmarks", {})
        benchmarks.extend(alternative_benchmarks.keys())
        return benchmarks
    
    def set_current_benchmark(self, benchmark_name: str) -> None:
        """
        Set the current active benchmark
        
        Args:
            benchmark_name: Name of benchmark to set as current
        """
        available_benchmarks = self.list_available_benchmarks()
        if benchmark_name not in available_benchmarks:
            raise ValueError(f"Unknown benchmark: {benchmark_name}. "
                           f"Available: {available_benchmarks}")
        
        self.current_benchmark = benchmark_name
    
    def get_attribution_settings(self) -> Dict:
        """Get attribution analysis configuration settings"""
        return self.config.get("attribution_settings", {})
    
    def get_reporting_settings(self) -> Dict:
        """Get reporting configuration settings"""
        return self.config.get("reporting", {})
    
    def create_benchmark_returns_template(self) -> pd.DataFrame:
        """
        Create a template DataFrame for benchmark returns data
        
        This can be used to ensure benchmark returns data has the correct format
        for attribution analysis.
        
        Returns:
            Empty DataFrame with proper column structure
        """
        asset_classes = list(self.get_benchmark_weights().keys())
        market_indices = self.get_market_indices()
        
        columns = ['Date'] + asset_classes + [market_indices[ac]['primary_index'] 
                                             for ac in asset_classes if ac in market_indices]
        
        return pd.DataFrame(columns=columns)
    
    def validate_portfolio_data(
        self, 
        portfolio_weights: Dict[str, float],
        portfolio_returns: Dict[str, float]
    ) -> Tuple[bool, List[str]]:
        """
        Validate portfolio data against benchmark configuration
        
        Args:
            portfolio_weights: Portfolio asset class weights
            portfolio_returns: Portfolio asset class returns
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check if portfolio has all benchmark asset classes
        benchmark_weights = self.get_benchmark_weights()
        benchmark_assets = set(benchmark_weights.keys())
        portfolio_assets = set(portfolio_weights.keys())
        
        missing_assets = benchmark_assets - portfolio_assets
        if missing_assets:
            issues.append(f"Portfolio missing benchmark asset classes: {missing_assets}")
        
        extra_assets = portfolio_assets - benchmark_assets
        if extra_assets:
            issues.append(f"Portfolio has additional asset classes not in benchmark: {extra_assets}")
        
        # Check weight normalization
        weight_sum = sum(portfolio_weights.values())
        tolerance = self.get_attribution_settings().get("weight_tolerance", 0.01)
        
        if abs(weight_sum - 1.0) > tolerance:
            issues.append(f"Portfolio weights sum to {weight_sum:.4f}, expected 1.0")
        
        # Check for extreme weights or returns
        settings = self.get_attribution_settings()
        max_weight = settings.get("max_asset_weight", 0.95)
        max_return = settings.get("max_return_threshold", 2.0)
        min_return = settings.get("min_return_threshold", -0.90)
        
        for asset, weight in portfolio_weights.items():
            if weight > max_weight:
                issues.append(f"Extreme weight detected: {asset} = {weight:.2%}")
        
        for asset, return_val in portfolio_returns.items():
            if return_val > max_return or return_val < min_return:
                issues.append(f"Extreme return detected: {asset} = {return_val:.2%}")
        
        return len(issues) == 0, issues
    
    def get_benchmark_summary(self) -> Dict:
        """Get a comprehensive summary of the current benchmark configuration"""
        benchmark_name = self.current_benchmark
        weights = self.get_benchmark_weights()
        info = self.get_benchmark_info()
        indices = self.get_market_indices()
        
        summary = {
            "benchmark_name": benchmark_name,
            "benchmark_info": info,
            "asset_allocation": weights,
            "market_indices": {ac: indices.get(ac, {}).get("primary_index", "N/A") 
                             for ac in weights.keys()},
            "total_assets": len(weights),
            "largest_allocation": max(weights.items(), key=lambda x: x[1]),
            "smallest_allocation": min(weights.items(), key=lambda x: x[1])
        }
        
        return summary
