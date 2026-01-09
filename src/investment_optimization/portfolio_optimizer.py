#!/usr/bin/env python3
"""
Portfolio Optimization Module

This module provides advanced portfolio optimization capabilities using historical data,
integrating with the existing MPT framework and time-series analysis.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List
import warnings
from datetime import datetime

try:
    from portfolio_lib.core.mpt import AssetAllocationModel
except ImportError:
    # Try relative import when run from project root
    from src.portfolio_lib.core.mpt import AssetAllocationModel
from .time_series_analyzer import TimeSeriesAnalyzer


class PortfolioOptimizer:
    """
    Advanced portfolio optimization using historical data and multiple optimization strategies.
    """
    
    def __init__(self, data_manager, config: Dict[str, Any] = None):
        """
        Initialize the portfolio optimizer.
        
        Args:
            data_manager: DataManager instance with historical data
            config: Configuration dictionary for optimization parameters
        """
        self.data_manager = data_manager
        self.config = config or self._default_config()
        self.time_series_analyzer = None
        self._initialize_analyzer()
        
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for portfolio optimization."""
        return {
            'risk_free_rate': 0.02,
            'min_weight': 0.0,
            'max_weight': 1.0,
            'rebalancing_frequency': 'quarterly',
            'optimization_window': 24,  # months
            'min_history_length': 12,  # months
            'correlation_threshold': 0.8,
            'concentration_limit': 0.3,
            'target_return': None,
            'risk_tolerance': 'moderate'  # conservative, moderate, aggressive
        }
    
    def _initialize_analyzer(self):
        """Initialize the time series analyzer with historical data."""
        try:
            historical_holdings = self.data_manager.get_historical_holdings()
            historical_balance_sheet = self.data_manager.get_balance_sheet()
            
            if historical_holdings is not None and not historical_holdings.empty:
                self.time_series_analyzer = TimeSeriesAnalyzer(
                    historical_holdings, historical_balance_sheet
                )
            else:
                warnings.warn("No historical holdings data available")
        except Exception as e:
            warnings.warn(f"Failed to initialize time series analyzer: {e}")
    
    def prepare_optimization_data(self, lookback_months: int = None) -> Dict[str, Any]:
        """
        Prepare data for portfolio optimization.
        
        Args:
            lookback_months: Number of months to look back for analysis
            
        Returns:
            Dictionary containing prepared data for optimization
        """
        lookback_months = lookback_months or self.config['optimization_window']
        
        if self.time_series_analyzer is None:
            raise ValueError("Time series analyzer not initialized - no historical data")
        
        # 1. Calculate current allocation FIRST to ensure it's always available
        current_holdings = self.data_manager.get_holdings(latest_only=True)
        current_allocation = self._calculate_current_allocation(current_holdings)
        
        # 2. Get asset returns
        asset_returns = self.time_series_analyzer.calculate_asset_returns()
        
        # 3. Strengthen the check to handle None and empty DataFrame
        if asset_returns is None or asset_returns.empty:
            # If returns are not available, return a structure with empty/default
            # values for MPT data, but WITH the current_allocation
            return {
                'asset_returns': pd.DataFrame(),  # Return an empty DataFrame
                'current_allocation': current_allocation,
                'portfolio_returns': pd.Series(dtype=float),
                'performance_metrics': {},
                'correlation_matrix': pd.DataFrame(),
                'data_quality': self._assess_data_quality(pd.DataFrame())  # Assess empty data
            }
        
        # Filter to lookback period if we have enough data
        if len(asset_returns) > lookback_months:
            asset_returns = asset_returns.tail(lookback_months)
        
        # Get portfolio performance metrics
        portfolio_returns = self.time_series_analyzer.calculate_portfolio_returns()
        performance_metrics = self.time_series_analyzer.calculate_portfolio_metrics(
            portfolio_returns, self.config['risk_free_rate']
        )
        
        return {
            'asset_returns': asset_returns,
            'current_allocation': current_allocation,
            'portfolio_returns': portfolio_returns,
            'performance_metrics': performance_metrics,
            'correlation_matrix': asset_returns.corr() if not asset_returns.empty else pd.DataFrame(),
            'data_quality': self._assess_data_quality(asset_returns)
        }
    
    def _calculate_current_allocation(self, holdings: pd.DataFrame) -> Dict[str, float]:
        """Calculate current portfolio allocation percentages."""
        if holdings is None or holdings.empty:
            return {}
        
        total_value = holdings['Market_Value_CNY'].sum()
        if total_value <= 0:
            return {}
        
        allocation = {}
        for _, row in holdings.iterrows():
            asset_id = row.get('Asset_ID', 'Unknown')
            weight = row['Market_Value_CNY'] / total_value
            allocation[asset_id] = weight
        
        return allocation
    
    def _assess_data_quality(self, asset_returns: pd.DataFrame) -> Dict[str, Any]:
        """Assess the quality of data for optimization."""
        if asset_returns.empty:
            return {'quality': 'poor', 'issues': ['No returns data']}
        
        issues = []
        
        # Check for sufficient history
        if len(asset_returns) < self.config['min_history_length']:
            issues.append(f"Insufficient history: {len(asset_returns)} months (min: {self.config['min_history_length']})")
        
        # Check for missing data
        missing_pct = asset_returns.isnull().sum().sum() / (len(asset_returns) * len(asset_returns.columns))
        if missing_pct > 0.1:
            issues.append(f"High missing data: {missing_pct:.1%}")
        
        # Check for assets with zero variance
        zero_var_assets = asset_returns.std()[asset_returns.std() == 0].index.tolist()
        if zero_var_assets:
            issues.append(f"Zero variance assets: {zero_var_assets}")
        
        # Determine overall quality
        if not issues:
            quality = 'excellent'
        elif len(issues) == 1 and 'Insufficient history' in issues[0]:
            quality = 'good'
        elif len(issues) <= 2:
            quality = 'fair'
        else:
            quality = 'poor'
        
        return {
            'quality': quality,
            'issues': issues,
            'data_points': len(asset_returns),
            'assets_count': len(asset_returns.columns),
            'missing_data_pct': missing_pct
        }
    
    def optimize_portfolio(self, 
                          strategy: str = 'risk_parity',
                          constraints: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Optimize portfolio using specified strategy.
        
        Args:
            strategy: Optimization strategy ('risk_parity', 'mean_variance', 'min_variance', 'max_sharpe')
            constraints: Additional constraints for optimization
            
        Returns:
            Dictionary containing optimization results
        """
        optimization_data = self.prepare_optimization_data()
        asset_returns = optimization_data['asset_returns']
        
        # Check if asset_returns is empty, which now signals that MPT analysis is not possible
        if asset_returns.empty:
            # Return the structured failure response required by the Investment Compass team
            return {
                "status": "MPT_ANALYSIS_FAILED",
                "reason": "Historical returns unavailable",
                "current_allocation": optimization_data.get('current_allocation', {})
            }
        
        # Check data quality
        if optimization_data['data_quality']['quality'] == 'poor':
            return {
                'success': False, 
                'error': 'Data quality insufficient for optimization',
                'issues': optimization_data['data_quality']['issues']
            }
        
        try:
            if strategy == 'risk_parity':
                result = self._optimize_risk_parity(asset_returns, constraints)
            elif strategy == 'mean_variance':
                result = self._optimize_mean_variance(asset_returns, constraints)
            elif strategy == 'min_variance':
                result = self._optimize_min_variance(asset_returns, constraints)
            elif strategy == 'max_sharpe':
                result = self._optimize_max_sharpe(asset_returns, constraints)
            else:
                return {'success': False, 'error': f'Unknown strategy: {strategy}'}
            
            # Add metadata to result
            result.update({
                'strategy': strategy,
                'optimization_data': optimization_data,
                'timestamp': datetime.now(),
                'config': self.config.copy()
            })
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': f'Optimization failed: {str(e)}'}
    
    def _optimize_risk_parity(self, asset_returns: pd.DataFrame, constraints: Dict = None) -> Dict[str, Any]:
        """Optimize for risk parity (equal risk contribution)."""
        # Create MPT model first to get filtered assets
        mpt_model = AssetAllocationModel(
            asset_returns, 
            risk_free_rate=self.config['risk_free_rate']
        )
        
        # Get the filtered assets from MPT model
        filtered_assets = mpt_model.assets
        filtered_returns = asset_returns[filtered_assets]
        
        # Calculate risk parity weights for filtered assets only
        # This is a simplified implementation - in practice, you'd use iterative optimization
        
        # Calculate volatilities for filtered assets
        volatilities = filtered_returns.std() * np.sqrt(12)  # Annualized
        
        # Inverse volatility weights (basic risk parity)
        inv_vol_weights = 1 / volatilities
        weights = inv_vol_weights / inv_vol_weights.sum()
        
        # Apply constraints if specified
        if constraints:
            weights = self._apply_constraints(weights, constraints)
        
        # Calculate portfolio performance using filtered weights
        returns, volatility, sharpe = mpt_model.portfolio_performance(weights.values)
        
        return {
            'success': True,
            'weights': weights.to_dict(),
            'expected_return': returns,
            'volatility': volatility,
            'sharpe_ratio': sharpe,
            'strategy_details': {
                'type': 'risk_parity',
                'method': 'inverse_volatility'
            }
        }
    
    def _optimize_mean_variance(self, asset_returns: pd.DataFrame, constraints: Dict = None) -> Dict[str, Any]:
        """Optimize using mean-variance optimization."""
        mpt_model = AssetAllocationModel(
            asset_returns,
            risk_free_rate=self.config['risk_free_rate']
        )
        
        # Determine target return
        target_return = None
        if constraints and 'target_return' in constraints:
            target_return = constraints['target_return']
        elif self.config.get('target_return'):
            target_return = self.config['target_return']
        
        # Optimize
        if target_return:
            result = mpt_model.optimize_portfolio(objective='min_volatility', target_return=target_return)
        else:
            result = mpt_model.optimize_portfolio(objective='sharpe')
        
        if result['success']:
            return {
                'success': True,
                'weights': result['weights'],
                'expected_return': result['returns'],
                'volatility': result['volatility'],
                'sharpe_ratio': result['sharpe'],
                'strategy_details': {
                    'type': 'mean_variance',
                    'objective': 'min_volatility' if target_return else 'max_sharpe',
                    'target_return': target_return
                }
            }
        else:
            return {'success': False, 'error': result.get('message', 'Optimization failed')}
    
    def _optimize_min_variance(self, asset_returns: pd.DataFrame, constraints: Dict = None) -> Dict[str, Any]:
        """Optimize for minimum variance."""
        mpt_model = AssetAllocationModel(
            asset_returns,
            risk_free_rate=self.config['risk_free_rate']
        )
        
        result = mpt_model.optimize_portfolio(objective='min_volatility')
        
        if result['success']:
            return {
                'success': True,
                'weights': result['weights'],
                'expected_return': result['returns'],
                'volatility': result['volatility'],
                'sharpe_ratio': result['sharpe'],
                'strategy_details': {
                    'type': 'min_variance',
                    'objective': 'minimize_volatility'
                }
            }
        else:
            return {'success': False, 'error': result.get('message', 'Optimization failed')}
    
    def _optimize_max_sharpe(self, asset_returns: pd.DataFrame, constraints: Dict = None) -> Dict[str, Any]:
        """Optimize for maximum Sharpe ratio."""
        mpt_model = AssetAllocationModel(
            asset_returns,
            risk_free_rate=self.config['risk_free_rate']
        )
        
        result = mpt_model.optimize_portfolio(objective='sharpe')
        
        if result['success']:
            return {
                'success': True,
                'weights': result['weights'],
                'expected_return': result['returns'],
                'volatility': result['volatility'],
                'sharpe_ratio': result['sharpe'],
                'strategy_details': {
                    'type': 'max_sharpe',
                    'objective': 'maximize_sharpe_ratio'
                }
            }
        else:
            return {'success': False, 'error': result.get('message', 'Optimization failed')}
    
    def _apply_constraints(self, weights: pd.Series, constraints: Dict) -> pd.Series:
        """Apply constraints to portfolio weights."""
        # Apply min/max weight constraints
        if 'min_weight' in constraints:
            weights = weights.clip(lower=constraints['min_weight'])
        if 'max_weight' in constraints:
            weights = weights.clip(upper=constraints['max_weight'])
        
        # Renormalize to sum to 1
        weights = weights / weights.sum()
        
        return weights
    
    def compare_strategies(self, strategies: List[str] = None) -> Dict[str, Any]:
        """
        Compare multiple optimization strategies.
        
        Args:
            strategies: List of strategies to compare
            
        Returns:
            Dictionary containing comparison results
        """
        if strategies is None:
            strategies = ['risk_parity', 'mean_variance', 'min_variance', 'max_sharpe']
        
        results = {}
        for strategy in strategies:
            result = self.optimize_portfolio(strategy=strategy)
            if result['success']:
                results[strategy] = result
        
        if not results:
            return {'success': False, 'error': 'No successful optimizations'}
        
        # Create comparison summary
        comparison = {
            'strategies': list(results.keys()),
            'performance_summary': {},
            'weight_comparison': {},
            'best_sharpe': None,
            'min_volatility': None,
            'max_return': None
        }
        
        best_sharpe = -np.inf
        min_vol = np.inf
        max_ret = -np.inf
        
        for strategy, result in results.items():
            comparison['performance_summary'][strategy] = {
                'return': result['expected_return'],
                'volatility': result['volatility'],
                'sharpe': result['sharpe_ratio']
            }
            
            comparison['weight_comparison'][strategy] = result['weights']
            
            # Track best performing strategies
            if result['sharpe_ratio'] > best_sharpe:
                best_sharpe = result['sharpe_ratio']
                comparison['best_sharpe'] = strategy
            
            if result['volatility'] < min_vol:
                min_vol = result['volatility']
                comparison['min_volatility'] = strategy
            
            if result['expected_return'] > max_ret:
                max_ret = result['expected_return']
                comparison['max_return'] = strategy
        
        comparison['success'] = True
        return comparison
    
    def generate_rebalancing_recommendations(self) -> Dict[str, Any]:
        """
        Generate portfolio rebalancing recommendations.
        
        Returns:
            Dictionary containing rebalancing analysis and recommendations
        """
        if self.time_series_analyzer is None:
            return {'success': False, 'error': 'No historical data available'}
        
        # Get current allocation
        current_holdings = self.data_manager.get_holdings(latest_only=True)
        current_allocation = self._calculate_current_allocation(current_holdings)
        
        if not current_allocation:
            return {'success': False, 'error': 'No current holdings data'}
        
        # Run optimization to get optimal allocation
        optimization_result = self.optimize_portfolio(strategy='mean_variance')
        
        if not optimization_result['success']:
            return {'success': False, 'error': 'Failed to generate optimal allocation'}
        
        optimal_allocation = optimization_result['weights']
        
        # Calculate rebalancing needed
        rebalancing_analysis = self._analyze_rebalancing(current_allocation, optimal_allocation)
        
        # Add portfolio analysis
        portfolio_analysis = self.time_series_analyzer.generate_comprehensive_analysis()
        
        return {
            'success': True,
            'current_allocation': current_allocation,
            'optimal_allocation': optimal_allocation,
            'rebalancing_analysis': rebalancing_analysis,
            'portfolio_analysis': portfolio_analysis['performance_metrics'],
            'recommendations': self._generate_rebalancing_recommendations(rebalancing_analysis),
            'timestamp': datetime.now()
        }
    
    def _analyze_rebalancing(self, current: Dict[str, float], optimal: Dict[str, float]) -> Dict[str, Any]:
        """Analyze the difference between current and optimal allocations."""
        all_assets = set(current.keys()) | set(optimal.keys())
        
        differences = {}
        total_change = 0
        
        for asset in all_assets:
            current_weight = current.get(asset, 0)
            optimal_weight = optimal.get(asset, 0)
            difference = optimal_weight - current_weight
            
            differences[asset] = {
                'current': current_weight,
                'optimal': optimal_weight,
                'difference': difference,
                'percentage_change': (difference / current_weight * 100) if current_weight > 0 else float('inf') if difference > 0 else 0
            }
            
            total_change += abs(difference)
        
        # Sort by absolute difference
        sorted_differences = dict(sorted(differences.items(), key=lambda x: abs(x[1]['difference']), reverse=True))
        
        return {
            'asset_differences': sorted_differences,
            'total_rebalancing_magnitude': total_change,
            'needs_rebalancing': total_change > 0.05,  # 5% threshold
            'largest_changes': list(sorted_differences.keys())[:5]
        }
    
    def _generate_rebalancing_recommendations(self, rebalancing_analysis: Dict[str, Any]) -> List[str]:
        """Generate human-readable rebalancing recommendations."""
        recommendations = []
        
        if not rebalancing_analysis['needs_rebalancing']:
            recommendations.append("Portfolio is well-balanced. No significant rebalancing needed.")
            return recommendations
        
        asset_diffs = rebalancing_analysis['asset_differences']
        
        # Recommendations for largest changes
        for asset in rebalancing_analysis['largest_changes']:
            diff_info = asset_diffs[asset]
            
            if abs(diff_info['difference']) > 0.02:  # 2% threshold
                if diff_info['difference'] > 0:
                    recommendations.append(
                        f"Increase {asset} allocation by {diff_info['difference']:.1%} "
                        f"(from {diff_info['current']:.1%} to {diff_info['optimal']:.1%})"
                    )
                else:
                    recommendations.append(
                        f"Decrease {asset} allocation by {abs(diff_info['difference']):.1%} "
                        f"(from {diff_info['current']:.1%} to {diff_info['optimal']:.1%})"
                    )
        
        # General recommendation
        total_magnitude = rebalancing_analysis['total_rebalancing_magnitude']
        if total_magnitude > 0.2:
            recommendations.append("Significant rebalancing recommended - consider implementing changes gradually.")
        elif total_magnitude > 0.1:
            recommendations.append("Moderate rebalancing recommended.")
        else:
            recommendations.append("Minor adjustments recommended.")
        
        return recommendations
