#!/usr/bin/env python3
"""
Time Series Analysis Module for Portfolio Optimization

This module provides time-series analysis capabilities for historical portfolio data,
including portfolio performance attribution, risk analysis, and trend identification.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any
from datetime import datetime
import warnings

# Try relative import first, fall back to absolute
try:
    from ..financial_analysis.metrics import FinancialMetrics
except ImportError:
    from financial_analysis.metrics import FinancialMetrics

class TimeSeriesAnalyzer:
    """
    Time series analysis for portfolio performance and risk metrics.
    """
    
    def __init__(self, historical_holdings: pd.DataFrame, historical_balance_sheet: pd.DataFrame):
        """
        Initialize the time series analyzer.
        
        Args:
            historical_holdings: MultiIndex DataFrame with (date, asset) structure
            historical_balance_sheet: DataFrame with date index and financial metrics
        """
        self.historical_holdings = historical_holdings
        self.historical_balance_sheet = historical_balance_sheet
        self.metrics = FinancialMetrics(risk_free_rate=0.02)  # Default risk-free rate
        self._validate_data()
        
    def _validate_data(self):
        """Validate input data structure and consistency."""
        if not isinstance(self.historical_holdings.index, pd.MultiIndex):
            raise ValueError("historical_holdings must have MultiIndex (date, asset) structure")
            
        if self.historical_holdings.empty:
            raise ValueError("historical_holdings cannot be empty")
            
        if self.historical_balance_sheet.empty:
            warnings.warn("historical_balance_sheet is empty - some analyses may be limited")
    
    def calculate_portfolio_returns(self, frequency: str = 'monthly') -> pd.Series:
        """
        Calculate portfolio returns over time based on total portfolio value using centralized metrics.
        
        Args:
            frequency: Return frequency ('daily', 'weekly', 'monthly')
            
        Returns:
            Series of portfolio returns indexed by date
        """
        # Calculate total portfolio value for each snapshot date
        portfolio_values = self.historical_holdings.groupby(level=0)['Market_Value_CNY'].sum()
        portfolio_values = portfolio_values.sort_index()
        
        # Remove duplicate dates by keeping the last value
        portfolio_values = portfolio_values[~portfolio_values.index.duplicated(keep='last')]
        
        if len(portfolio_values) < 2:
            warnings.warn("Insufficient data points for return calculation")
            return pd.Series(dtype=float)
        
        # Use centralized calculation for returns
        returns = self.metrics.calculate_simple_returns(portfolio_values).dropna()
        
        # Resample if needed (for now, we work with available frequency)
        if frequency == 'monthly' and len(returns) > 1:
            # If we have more frequent data, resample to monthly
            try:
                returns = returns.resample('ME').apply(lambda x: (1 + x).prod() - 1 if len(x) > 0 else np.nan)
            except Exception:
                # If resampling fails, use original returns
                pass
        
        return returns
    
    def calculate_asset_returns(self) -> pd.DataFrame:
        """
        Calculate individual asset returns over time using centralized metrics.
        
        Returns:
            DataFrame with assets as columns and dates as rows, containing returns
        """
        asset_returns = {}
        
        # Get unique assets across all snapshots
        all_assets = self.historical_holdings.index.get_level_values(1).unique()
        
        for asset in all_assets:
            try:
                # Get values for this asset across time
                asset_data = self.historical_holdings.xs(asset, level=1, drop_level=False)
                if len(asset_data) < 2:
                    continue
                    
                # Extract dates and values
                dates = asset_data.index.get_level_values(0)
                values = asset_data['Market_Value_CNY'].values
                
                # Create time series and calculate returns using centralized method
                asset_series = pd.Series(values, index=dates).sort_index()
                
                # Remove duplicate dates by keeping the last value
                asset_series = asset_series[~asset_series.index.duplicated(keep='last')]
                
                if len(asset_series) >= 2:
                    asset_returns[asset] = self.metrics.calculate_simple_returns(asset_series).dropna()
                    
            except Exception as e:
                # Skip assets that cause issues
                warnings.warn(f"Failed to calculate returns for asset {asset}: {e}")
                continue
        
        if not asset_returns:
            return pd.DataFrame()
        
        # Combine all asset returns into a DataFrame
        # Handle different date ranges by using outer join
        returns_df = pd.DataFrame(asset_returns)
        return returns_df.fillna(0)  # Fill NaN with 0 for assets not present in certain periods
    
    def calculate_portfolio_metrics(self, returns: pd.Series, risk_free_rate: float = 0.02) -> Dict[str, float]:
        """
        Calculate comprehensive portfolio performance metrics using centralized calculations.
        
        Args:
            returns: Series of portfolio returns
            risk_free_rate: Annual risk-free rate
            
        Returns:
            Dictionary of performance metrics
        """
        if returns.empty:
            return {}
        
        # Update metrics calculator risk-free rate if different
        if risk_free_rate != self.metrics.risk_free_rate:
            self.metrics.risk_free_rate = risk_free_rate
        
        # Create a price series from returns to enable comprehensive metrics
        initial_value = 100  # Start with $100
        price_series = (1 + returns).cumprod() * initial_value
        # Add initial price point
        initial_date = returns.index[0] - pd.DateOffset(days=1)
        price_series = pd.concat([pd.Series([initial_value], index=[initial_date]), price_series])
        
        # Use centralized metrics calculations
        metrics_summary = self.metrics.get_metrics_summary(price_series)
        
        # Convert to the expected format for backward compatibility
        return {
            'total_return': metrics_summary['total_return'],
            'annualized_return': metrics_summary['annualized_return'], 
            'volatility': metrics_summary['annualized_volatility'],
            'sharpe_ratio': metrics_summary['sharpe_ratio'],
            'max_drawdown': metrics_summary['max_drawdown_analysis']['max_drawdown'],
            'calmar_ratio': metrics_summary['calmar_ratio'],
            'var_5_percent': metrics_summary['var_analysis'].get('var_95', 0),
            'num_periods': len(returns)
        }
    
    def analyze_asset_allocation_evolution(self) -> pd.DataFrame:
        """
        Analyze how asset allocation has evolved over time.
        
        Returns:
            DataFrame showing percentage allocation by asset over time
        """
        allocation_history = []
        
        snapshot_dates = self.historical_holdings.index.get_level_values(0).unique().sort_values()
        
        for date in snapshot_dates:
            try:
                date_holdings = self.historical_holdings.loc[date]
                
                # Handle potential duplicate asset entries by summing them
                if isinstance(date_holdings, pd.DataFrame):
                    date_holdings = date_holdings.groupby(date_holdings.index)['Market_Value_CNY'].sum()
                
                total_value = date_holdings.sum() if hasattr(date_holdings, 'sum') else date_holdings['Market_Value_CNY'].sum()
                
                if total_value > 0:
                    if hasattr(date_holdings, 'index'):
                        # Series case
                        allocations = (date_holdings / total_value * 100).to_dict()
                    else:
                        # DataFrame case
                        allocations = (date_holdings['Market_Value_CNY'] / total_value * 100).to_dict()
                    
                    allocations['Date'] = date
                    allocation_history.append(allocations)
                    
            except Exception as e:
                warnings.warn(f"Failed to process allocation for date {date}: {e}")
                continue
        
        if not allocation_history:
            return pd.DataFrame()
        
        allocation_df = pd.DataFrame(allocation_history)
        allocation_df.set_index('Date', inplace=True)
        return allocation_df.fillna(0)
    
    def identify_concentration_risk(self, threshold: float = 0.1) -> Dict[str, Any]:
        """
        Identify concentration risk in the portfolio over time.
        
        Args:
            threshold: Concentration threshold (e.g., 0.1 for 10%)
            
        Returns:
            Dictionary with concentration risk analysis
        """
        allocation_df = self.analyze_asset_allocation_evolution()
        
        if allocation_df.empty:
            return {}
        
        # Convert percentages to decimals
        allocation_df = allocation_df / 100
        
        concentration_metrics = {}
        
        for date in allocation_df.index:
            date_allocations = allocation_df.loc[date]
            
            # Herfindahl-Hirschman Index (HHI)
            hhi = (date_allocations ** 2).sum()
            
            # Number of assets above threshold
            concentrated_assets = date_allocations[date_allocations > threshold]
            
            # Top asset concentration
            top_asset_weight = date_allocations.max()
            top_asset = date_allocations.idxmax()
            
            concentration_metrics[date] = {
                'hhi': hhi,
                'num_concentrated_assets': len(concentrated_assets),
                'concentrated_assets': concentrated_assets.to_dict(),
                'top_asset': top_asset,
                'top_asset_weight': top_asset_weight,
                'is_concentrated': top_asset_weight > threshold
            }
        
        return concentration_metrics
    
    def analyze_diversification_trend(self) -> Dict[str, Any]:
        """
        Analyze diversification trends over time.
        
        Returns:
            Dictionary with diversification analysis
        """
        allocation_df = self.analyze_asset_allocation_evolution()
        
        if allocation_df.empty:
            return {}
        
        diversification_metrics = {}
        
        for date in allocation_df.index:
            date_allocations = allocation_df.loc[date] / 100  # Convert to decimals
            
            # Effective number of assets (inverse HHI)
            hhi = (date_allocations ** 2).sum()
            effective_assets = 1 / hhi if hhi > 0 else 0
            
            # Shannon entropy (diversification measure)
            # Filter out zero allocations to avoid log(0)
            non_zero_allocations = date_allocations[date_allocations > 0]
            shannon_entropy = -(non_zero_allocations * np.log(non_zero_allocations)).sum()
            
            diversification_metrics[date] = {
                'total_assets': len(date_allocations[date_allocations > 0]),
                'effective_assets': effective_assets,
                'shannon_entropy': shannon_entropy,
                'hhi': hhi
            }
        
        return diversification_metrics
    
    def calculate_correlation_analysis(self) -> Dict[str, Any]:
        """
        Analyze correlation patterns in asset returns.
        
        Returns:
            Dictionary with correlation analysis
        """
        asset_returns = self.calculate_asset_returns()
        
        if asset_returns.empty or len(asset_returns.columns) < 2:
            return {}
        
        correlation_matrix = asset_returns.corr()
        
        # Calculate average correlation
        # Get upper triangle excluding diagonal
        upper_triangle = correlation_matrix.where(
            np.triu(np.ones(correlation_matrix.shape), k=1).astype(bool)
        )
        avg_correlation = upper_triangle.stack().mean()
        
        # Find highest and lowest correlations
        correlations_flat = upper_triangle.stack()
        highest_corr = correlations_flat.max()
        lowest_corr = correlations_flat.min()
        
        highest_pair = correlations_flat.idxmax() if not correlations_flat.empty else None
        lowest_pair = correlations_flat.idxmin() if not correlations_flat.empty else None
        
        return {
            'correlation_matrix': correlation_matrix,
            'average_correlation': avg_correlation,
            'highest_correlation': highest_corr,
            'lowest_correlation': lowest_corr,
            'highest_corr_pair': highest_pair,
            'lowest_corr_pair': lowest_pair
        }
    
    def generate_comprehensive_analysis(self) -> Dict[str, Any]:
        """
        Generate a comprehensive time-series analysis report.
        
        Returns:
            Dictionary containing all analysis results
        """
        # Calculate portfolio returns
        portfolio_returns = self.calculate_portfolio_returns()
        
        # Calculate performance metrics
        performance_metrics = self.calculate_portfolio_metrics(portfolio_returns)
        
        # Analyze asset allocation evolution
        allocation_evolution = self.analyze_asset_allocation_evolution()
        
        # Analyze concentration risk
        concentration_analysis = self.identify_concentration_risk()
        
        # Analyze diversification trends
        diversification_analysis = self.analyze_diversification_trend()
        
        # Analyze correlations
        correlation_analysis = self.calculate_correlation_analysis()
        
        return {
            'portfolio_returns': portfolio_returns,
            'performance_metrics': performance_metrics,
            'allocation_evolution': allocation_evolution,
            'concentration_analysis': concentration_analysis,
            'diversification_analysis': diversification_analysis,
            'correlation_analysis': correlation_analysis,
            'analysis_date': datetime.now(),
            'data_period': {
                'start_date': self.historical_holdings.index.get_level_values(0).min(),
                'end_date': self.historical_holdings.index.get_level_values(0).max(),
                'num_snapshots': len(self.historical_holdings.index.get_level_values(0).unique())
            }
        }
