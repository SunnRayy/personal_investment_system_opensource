"""
Historical Performance Analysis Module

This module calculates advanced performance metrics using the full historical dataset,
including portfolio returns, volatility, Sharpe ratio, and long-term trend analysis.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class HistoricalPerformanceAnalyzer:
    """
    Analyzer for calculating comprehensive historical performance metrics
    using multi-year historical data.
    """
    
    def __init__(self, risk_free_rate: float = 0.035):
        """
        Initialize the analyzer.
        
        Args:
            risk_free_rate: Annual risk-free rate for Sharpe ratio calculation
        """
        self.risk_free_rate = risk_free_rate
        self.logger = logging.getLogger(__name__)
    
    def calculate_historical_performance(self, 
                                       historical_holdings: pd.DataFrame,
                                       balance_sheet_df: pd.DataFrame,
                                       monthly_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate comprehensive historical performance metrics.
        
        Args:
            historical_holdings: DataFrame with historical holdings data (MultiIndex: Date, Asset_ID)
            balance_sheet_df: Balance sheet data for trend analysis
            monthly_df: Monthly income/expense data for savings rate analysis
            
        Returns:
            Dictionary containing all calculated historical metrics
        """
        self.logger.info("Starting comprehensive historical performance analysis...")
        
        results = {}
        
        try:
            # 1. Portfolio Performance Metrics
            self.logger.info("Calculating portfolio performance metrics...")
            portfolio_metrics = self._calculate_portfolio_performance(historical_holdings)
            results['portfolio_performance'] = portfolio_metrics
            
            # 2. Risk Metrics
            self.logger.info("Calculating risk metrics...")
            risk_metrics = self._calculate_risk_metrics(historical_holdings)
            results['risk_metrics'] = risk_metrics
            
            # 3. Long-term Trend Analysis
            self.logger.info("Calculating long-term trends...")
            trend_analysis = self._calculate_long_term_trends(
                historical_holdings, balance_sheet_df, monthly_df
            )
            results['trend_analysis'] = trend_analysis
            
            # 4. Performance Attribution
            self.logger.info("Calculating performance attribution...")
            attribution = self._calculate_performance_attribution(historical_holdings)
            results['performance_attribution'] = attribution
            
            # 5. Summary Statistics
            results['summary'] = self._generate_performance_summary(results)
            
            self.logger.info("Historical performance analysis completed successfully")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in historical performance analysis: {e}")
            return {'error': str(e), 'status': 'failed'}
    
    def _calculate_portfolio_performance(self, historical_holdings: pd.DataFrame) -> Dict[str, Any]:
        """Calculate portfolio-level performance metrics."""
        
        if historical_holdings is None or historical_holdings.empty:
            return {'error': 'No historical holdings data available'}
        
        try:
            # Calculate total portfolio value by date
            portfolio_values = historical_holdings.groupby(level=0)['Market_Value_CNY'].sum()
            portfolio_values = portfolio_values.sort_index()
            
            if len(portfolio_values) < 2:
                return {'error': 'Insufficient data points for performance calculation'}
            
            # Calculate returns
            returns = portfolio_values.pct_change().dropna()
            
            # Annualized metrics
            periods_per_year = self._estimate_periods_per_year(portfolio_values.index)
            
            # Total return
            total_return = (portfolio_values.iloc[-1] / portfolio_values.iloc[0]) - 1
            
            # Annualized return
            years = (portfolio_values.index[-1] - portfolio_values.index[0]).days / 365.25
            annualized_return = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
            
            # Volatility (annualized standard deviation)
            annualized_volatility = returns.std() * np.sqrt(periods_per_year)
            
            # Sharpe Ratio
            excess_returns = returns - (self.risk_free_rate / periods_per_year)
            sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(periods_per_year) if excess_returns.std() > 0 else 0
            
            # Maximum Drawdown
            running_max = portfolio_values.expanding().max()
            drawdown = (portfolio_values - running_max) / running_max
            max_drawdown = drawdown.min()
            
            # Calmar Ratio (annualized return / absolute max drawdown)
            calmar_ratio = abs(annualized_return / max_drawdown) if max_drawdown < 0 else np.inf
            
            return {
                'total_return': total_return,
                'annualized_return': annualized_return,
                'annualized_volatility': annualized_volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'calmar_ratio': calmar_ratio,
                'current_value': portfolio_values.iloc[-1],
                'initial_value': portfolio_values.iloc[0],
                'data_period_years': years,
                'number_of_observations': len(portfolio_values)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating portfolio performance: {e}")
            return {'error': str(e)}
    
    def _calculate_risk_metrics(self, historical_holdings: pd.DataFrame) -> Dict[str, Any]:
        """Calculate detailed risk metrics."""
        
        try:
            # Portfolio values and returns
            portfolio_values = historical_holdings.groupby(level=0)['Market_Value_CNY'].sum()
            returns = portfolio_values.pct_change().dropna()
            
            if len(returns) < 10:  # Need reasonable sample size
                return {'error': 'Insufficient data for risk metrics'}
            
            periods_per_year = self._estimate_periods_per_year(portfolio_values.index)
            
            # Value at Risk (VaR) - 5% and 1%
            var_5 = returns.quantile(0.05)
            var_1 = returns.quantile(0.01)
            
            # Conditional Value at Risk (CVaR)
            cvar_5 = returns[returns <= var_5].mean()
            cvar_1 = returns[returns <= var_1].mean()
            
            # Downside deviation (semi-deviation)
            downside_returns = returns[returns < 0]
            downside_deviation = downside_returns.std() * np.sqrt(periods_per_year)
            
            # Sortino Ratio
            sortino_ratio = (returns.mean() * periods_per_year - self.risk_free_rate) / downside_deviation if downside_deviation > 0 else 0
            
            # Skewness and Kurtosis
            skewness = returns.skew()
            kurtosis = returns.kurtosis()
            
            # Rolling volatility (quarterly windows)
            rolling_window = max(20, len(returns) // 10)  # Adaptive window size
            rolling_vol = returns.rolling(window=rolling_window).std() * np.sqrt(periods_per_year)
            volatility_of_volatility = rolling_vol.std()
            
            return {
                'value_at_risk_5pct': var_5,
                'value_at_risk_1pct': var_1,
                'conditional_var_5pct': cvar_5,
                'conditional_var_1pct': cvar_1,
                'downside_deviation': downside_deviation,
                'sortino_ratio': sortino_ratio,
                'skewness': skewness,
                'kurtosis': kurtosis,
                'volatility_of_volatility': volatility_of_volatility,
                'periods_per_year': periods_per_year
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating risk metrics: {e}")
            return {'error': str(e)}
    
    def _calculate_long_term_trends(self, 
                                  historical_holdings: pd.DataFrame,
                                  balance_sheet_df: pd.DataFrame,
                                  monthly_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate long-term trend analysis for key financial metrics."""
        
        trends = {}
        
        try:
            # Portfolio Net Worth Trend
            if historical_holdings is not None and not historical_holdings.empty:
                portfolio_values = historical_holdings.groupby(level=0)['Market_Value_CNY'].sum()
                trends['portfolio_growth'] = self._calculate_trend_metrics(portfolio_values, 'Portfolio Value')
            
            # Balance Sheet Trends
            if balance_sheet_df is not None and not balance_sheet_df.empty:
                if 'Date' in balance_sheet_df.columns:
                    balance_sheet_df = balance_sheet_df.set_index('Date')
                
                # Net Worth Trend
                if 'Net_Worth' in balance_sheet_df.columns:
                    net_worth_trend = self._calculate_trend_metrics(
                        balance_sheet_df['Net_Worth'], 'Net Worth'
                    )
                    trends['net_worth'] = net_worth_trend
                
                # Total Assets Trend
                if 'Total_Assets' in balance_sheet_df.columns:
                    assets_trend = self._calculate_trend_metrics(
                        balance_sheet_df['Total_Assets'], 'Total Assets'
                    )
                    trends['total_assets'] = assets_trend
                
                # Debt-to-Asset Ratio Trend
                if 'Total_Assets' in balance_sheet_df.columns and 'Total_Liabilities' in balance_sheet_df.columns:
                    debt_to_asset = balance_sheet_df['Total_Liabilities'] / balance_sheet_df['Total_Assets']
                    debt_trend = self._calculate_trend_metrics(debt_to_asset, 'Debt-to-Asset Ratio')
                    trends['debt_to_asset_ratio'] = debt_trend
            
            # Savings Rate Trend
            if monthly_df is not None and not monthly_df.empty:
                if 'Date' in monthly_df.columns:
                    monthly_df = monthly_df.set_index('Date')
                
                # Calculate savings rate if we have income and expenses
                if 'Total_Income' in monthly_df.columns and 'Total_Expenses' in monthly_df.columns:
                    monthly_savings = monthly_df['Total_Income'] - monthly_df['Total_Expenses']
                    savings_rate = monthly_savings / monthly_df['Total_Income']
                    savings_rate = savings_rate.replace([np.inf, -np.inf], np.nan).dropna()
                    
                    if len(savings_rate) > 0:
                        trends['savings_rate'] = self._calculate_trend_metrics(savings_rate, 'Savings Rate')
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error calculating long-term trends: {e}")
            return {'error': str(e)}
    
    def _calculate_trend_metrics(self, series: pd.Series, metric_name: str) -> Dict[str, Any]:
        """Calculate trend statistics for a time series."""
        
        if series is None or len(series) < 2:
            return {'error': f'Insufficient data for {metric_name} trend analysis'}
        
        try:
            # Clean the series
            series = series.dropna()
            
            if len(series) < 2:
                return {'error': f'No valid data points for {metric_name}'}
            
            # Basic statistics
            current_value = series.iloc[-1]
            initial_value = series.iloc[0]
            total_change = current_value - initial_value
            total_change_pct = (current_value / initial_value - 1) * 100 if initial_value != 0 else 0
            
            # Calculate CAGR if we have date information
            if hasattr(series.index, 'to_pydatetime'):
                years = (series.index[-1] - series.index[0]).days / 365.25
                cagr = (current_value / initial_value) ** (1/years) - 1 if years > 0 and initial_value > 0 else 0
            else:
                cagr = None
            
            # Linear trend
            x = np.arange(len(series))
            slope, intercept = np.polyfit(x, series.values, 1)
            
            # Rolling statistics
            if len(series) >= 4:
                # Calculate rolling means for different periods
                short_window = max(2, len(series) // 4)
                long_window = max(4, len(series) // 2)
                
                short_ma = series.rolling(window=short_window).mean().iloc[-1]
                long_ma = series.rolling(window=long_window).mean().iloc[-1]
                
                # Trend direction
                trend_direction = "Increasing" if short_ma > long_ma else "Decreasing" if short_ma < long_ma else "Stable"
            else:
                short_ma = series.mean()
                long_ma = series.mean()
                trend_direction = "Increasing" if slope > 0 else "Decreasing" if slope < 0 else "Stable"
            
            # Volatility
            volatility = series.std()
            coefficient_of_variation = volatility / series.mean() if series.mean() != 0 else 0
            
            return {
                'metric_name': metric_name,
                'current_value': current_value,
                'initial_value': initial_value,
                'total_change': total_change,
                'total_change_pct': total_change_pct,
                'cagr': cagr,
                'trend_direction': trend_direction,
                'linear_slope': slope,
                'average_value': series.mean(),
                'volatility': volatility,
                'coefficient_of_variation': coefficient_of_variation,
                'min_value': series.min(),
                'max_value': series.max(),
                'data_points': len(series),
                'short_term_average': short_ma,
                'long_term_average': long_ma
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating trend metrics for {metric_name}: {e}")
            return {'error': str(e)}
    
    def _calculate_performance_attribution(self, historical_holdings: pd.DataFrame) -> Dict[str, Any]:
        """Calculate performance attribution by asset class and individual assets."""
        
        try:
            if 'Asset_Class' not in historical_holdings.columns:
                return {'error': 'Asset_Class column not found in historical holdings'}
            
            # Calculate returns by asset class
            asset_class_performance = {}
            asset_performance = {}
            
            # Group by date and asset class to get asset class values over time
            class_values = historical_holdings.groupby([historical_holdings.index.get_level_values(0), 'Asset_Class'])['Market_Value_CNY'].sum()
            
            for asset_class in historical_holdings['Asset_Class'].unique():
                if pd.isna(asset_class):
                    continue
                    
                class_series = class_values.xs(asset_class, level=1)
                if len(class_series) > 1:
                    returns = class_series.pct_change().dropna()
                    if len(returns) > 0:
                        total_return = (class_series.iloc[-1] / class_series.iloc[0]) - 1
                        avg_return = returns.mean()
                        volatility = returns.std()
                        
                        asset_class_performance[asset_class] = {
                            'total_return': total_return,
                            'average_return': avg_return,
                            'volatility': volatility,
                            'current_value': class_series.iloc[-1],
                            'initial_value': class_series.iloc[0]
                        }
            
            # Calculate individual asset performance for top holdings
            asset_ids = historical_holdings.index.get_level_values(1).unique()
            
            for asset_id in asset_ids[:20]:  # Limit to top 20 for performance
                asset_series = historical_holdings.xs(asset_id, level=1)['Market_Value_CNY']
                if len(asset_series) > 1:
                    returns = asset_series.pct_change().dropna()
                    if len(returns) > 0:
                        total_return = (asset_series.iloc[-1] / asset_series.iloc[0]) - 1
                        
                        asset_performance[asset_id] = {
                            'total_return': total_return,
                            'current_value': asset_series.iloc[-1],
                            'initial_value': asset_series.iloc[0]
                        }
            
            return {
                'asset_class_performance': asset_class_performance,
                'top_asset_performance': asset_performance
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating performance attribution: {e}")
            return {'error': str(e)}
    
    def _generate_performance_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of key performance insights."""
        
        summary = {}
        
        try:
            # Portfolio Performance Summary
            if 'portfolio_performance' in results and 'error' not in results['portfolio_performance']:
                perf = results['portfolio_performance']
                summary['portfolio_summary'] = {
                    'annualized_return_pct': round(perf.get('annualized_return', 0) * 100, 2),
                    'sharpe_ratio': round(perf.get('sharpe_ratio', 0), 2),
                    'max_drawdown_pct': round(perf.get('max_drawdown', 0) * 100, 2),
                    'data_period_years': round(perf.get('data_period_years', 0), 1),
                    'performance_rating': self._rate_performance(perf.get('sharpe_ratio', 0))
                }
            
            # Risk Summary
            if 'risk_metrics' in results and 'error' not in results['risk_metrics']:
                risk = results['risk_metrics']
                summary['risk_summary'] = {
                    'sortino_ratio': round(risk.get('sortino_ratio', 0), 2),
                    'downside_deviation_pct': round(risk.get('downside_deviation', 0) * 100, 2),
                    'risk_rating': self._rate_risk(risk)
                }
            
            # Trend Summary
            if 'trend_analysis' in results:
                trends = results['trend_analysis']
                summary['trend_summary'] = {}
                
                for metric, trend_data in trends.items():
                    if 'error' not in trend_data:
                        summary['trend_summary'][metric] = {
                            'direction': trend_data.get('trend_direction', 'Unknown'),
                            'cagr_pct': round(trend_data.get('cagr', 0) * 100, 2) if trend_data.get('cagr') else None
                        }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating performance summary: {e}")
            return {'error': str(e)}
    
    def _rate_performance(self, sharpe_ratio: float) -> str:
        """Rate portfolio performance based on Sharpe ratio."""
        if sharpe_ratio >= 2.0:
            return "Excellent"
        elif sharpe_ratio >= 1.0:
            return "Good"
        elif sharpe_ratio >= 0.5:
            return "Acceptable"
        elif sharpe_ratio >= 0:
            return "Poor"
        else:
            return "Very Poor"
    
    def _rate_risk(self, risk_metrics: Dict[str, Any]) -> str:
        """Rate portfolio risk based on multiple risk metrics."""
        sortino = risk_metrics.get('sortino_ratio', 0)
        max_dd = abs(risk_metrics.get('max_drawdown', 0))
        
        if sortino >= 1.5 and max_dd <= 0.1:
            return "Low Risk"
        elif sortino >= 1.0 and max_dd <= 0.2:
            return "Moderate Risk"
        elif sortino >= 0.5 and max_dd <= 0.3:
            return "High Risk"
        else:
            return "Very High Risk"
    
    def _estimate_periods_per_year(self, date_index: pd.DatetimeIndex) -> float:
        """Estimate the number of periods per year based on the date frequency."""
        if len(date_index) < 2:
            return 252  # Default to daily
        
        # Calculate average time difference between observations
        time_diffs = pd.Series(date_index).diff().dropna()
        avg_diff_days = time_diffs.dt.days.mean()
        
        if avg_diff_days <= 1.5:
            return 252  # Daily
        elif avg_diff_days <= 7.5:
            return 52   # Weekly
        elif avg_diff_days <= 32:
            return 12   # Monthly
        else:
            return 4    # Quarterly
