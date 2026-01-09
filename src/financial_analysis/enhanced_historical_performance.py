"""
Refactored Historical Performance Analysis Module

Enhanced version with robust time-series handling using standardized utilities.
Provides stable analysis of portfolio performance with comprehensive data validation.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional, List

from ..data_manager.time_series_utils import (
    TimeSeriesProcessor, 
    standardize_time_series,
    validate_financial_time_series
)
from .metrics import FinancialMetrics

logger = logging.getLogger(__name__)


class EnhancedHistoricalPerformanceAnalyzer:
    """
    Enhanced analyzer with robust time-series handling and data validation.
    """
    
    def __init__(self, data_manager=None, risk_free_rate: float = 0.035):
        """Initialize the enhanced analyzer."""
        self.risk_free_rate = risk_free_rate
        self.ts_processor = TimeSeriesProcessor(frequency='M', fill_method='interpolate')
        self.logger = logging.getLogger(__name__)
        self.metrics = FinancialMetrics(risk_free_rate=risk_free_rate)
        self.data_manager = data_manager  # Store DataManager for TWR calculations
    
    def calculate_historical_performance(self, 
                                       historical_holdings: pd.DataFrame,
                                       balance_sheet_df: pd.DataFrame,
                                       monthly_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate comprehensive historical performance with enhanced data validation.
        """
        self.logger.info("Starting enhanced historical performance analysis...")
        
        results = {
            'data_quality': {},
            'portfolio_performance': {},
            'risk_metrics': {},
            'trend_analysis': {},
            'performance_attribution': {},
            'summary': {}
        }
        
        try:
            # Step 1: Validate and standardize all input data
            self.logger.info("Validating and standardizing input data...")
            
            validation_results = self._validate_and_prepare_data(
                historical_holdings, balance_sheet_df, monthly_df
            )
            
            results['data_quality'] = validation_results
            
            # Check if we have sufficient valid data
            if not validation_results.get('sufficient_data', False):
                self.logger.warning("Insufficient valid data for comprehensive analysis")
                return results
            
            # Get standardized data
            std_holdings = validation_results.get('standardized_holdings')
            std_balance_sheet = validation_results.get('standardized_balance_sheet')  
            std_monthly = validation_results.get('standardized_monthly')
            
            # Step 2: Calculate portfolio performance with error handling
            if std_holdings is not None and not std_holdings.empty:
                self.logger.info("Calculating portfolio performance metrics...")
                portfolio_metrics = self._calculate_robust_portfolio_performance(std_holdings)
                results['portfolio_performance'] = portfolio_metrics
            
            # Step 3: Calculate risk metrics
            if std_holdings is not None and not std_holdings.empty:
                self.logger.info("Calculating risk metrics...")
                risk_metrics = self._calculate_enhanced_risk_metrics(std_holdings)
                results['risk_metrics'] = risk_metrics
            
            # Step 4: Calculate trend analysis
            self.logger.info("Calculating comprehensive trend analysis...")
            trend_analysis = self._calculate_enhanced_trends(
                std_holdings, std_balance_sheet, std_monthly
            )
            results['trend_analysis'] = trend_analysis
            
            # Step 5: Performance attribution
            if std_holdings is not None and not std_holdings.empty:
                self.logger.info("Calculating performance attribution...")
                attribution = self._calculate_robust_attribution(std_holdings)
                results['performance_attribution'] = attribution
            
            # Step 6: Generate enhanced summary
            results['summary'] = self._generate_enhanced_summary(results)
            
            self.logger.info("Enhanced historical performance analysis completed successfully")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in enhanced historical performance analysis: {e}")
            results['error'] = str(e)
            results['status'] = 'failed'
            return results
    
    def _validate_and_prepare_data(self, 
                                  historical_holdings: pd.DataFrame,
                                  balance_sheet_df: pd.DataFrame,
                                  monthly_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate and standardize all input data for analysis.
        """
        validation_results = {
            'holdings_validation': {},
            'balance_sheet_validation': {},
            'monthly_validation': {},
            'standardized_holdings': None,
            'standardized_balance_sheet': None,
            'standardized_monthly': None,
            'sufficient_data': False
        }
        
        try:
            # Validate historical holdings
            if historical_holdings is not None and not historical_holdings.empty:
                # Check if MultiIndex (Date, Asset_ID)
                if isinstance(historical_holdings.index, pd.MultiIndex):
                    # Convert to single datetime index by aggregating
                    holdings_by_date = historical_holdings.groupby(level=0).agg({
                        'Market_Value_CNY': 'sum',
                        'Asset_Class': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'Mixed'
                    })
                    
                    # Validate time-series
                    holdings_validation = validate_financial_time_series(
                        holdings_by_date, 
                        expected_frequency='M',
                        asset_columns=['Market_Value_CNY']
                    )
                    validation_results['holdings_validation'] = holdings_validation
                    
                    # Standardize if valid
                    if holdings_validation.get('is_valid', False):
                        std_holdings = standardize_time_series(
                            holdings_by_date, 
                            frequency='M', 
                            fill_gaps=True
                        )
                        validation_results['standardized_holdings'] = std_holdings
                        
                else:
                    # Already single index - validate directly
                    holdings_validation = validate_financial_time_series(
                        historical_holdings,
                        expected_frequency='M',
                        asset_columns=['Market_Value_CNY'] if 'Market_Value_CNY' in historical_holdings.columns else None
                    )
                    validation_results['holdings_validation'] = holdings_validation
                    
                    if holdings_validation.get('is_valid', False):
                        std_holdings = standardize_time_series(
                            historical_holdings,
                            frequency='M',
                            fill_gaps=True
                        )
                        validation_results['standardized_holdings'] = std_holdings
            
            # Validate balance sheet
            if balance_sheet_df is not None and not balance_sheet_df.empty:
                asset_columns = [col for col in balance_sheet_df.columns 
                               if any(term in col.lower() for term in ['asset', 'worth', 'value', 'liability'])]
                
                balance_validation = validate_financial_time_series(
                    balance_sheet_df,
                    expected_frequency='M',
                    asset_columns=asset_columns
                )
                validation_results['balance_sheet_validation'] = balance_validation
                
                if balance_validation.get('is_valid', False):
                    std_balance = standardize_time_series(
                        balance_sheet_df,
                        frequency='M',
                        fill_gaps=True
                    )
                    validation_results['standardized_balance_sheet'] = std_balance
            
            # Validate monthly data
            if monthly_df is not None and not monthly_df.empty:
                income_expense_cols = [col for col in monthly_df.columns
                                     if any(term in col.lower() for term in ['income', 'expense', 'total'])]
                
                monthly_validation = validate_financial_time_series(
                    monthly_df,
                    expected_frequency='M', 
                    asset_columns=income_expense_cols
                )
                validation_results['monthly_validation'] = monthly_validation
                
                if monthly_validation.get('is_valid', False):
                    std_monthly = standardize_time_series(
                        monthly_df,
                        frequency='M',
                        fill_gaps=True
                    )
                    validation_results['standardized_monthly'] = std_monthly
            
            # Determine if we have sufficient data for analysis
            has_holdings = validation_results['standardized_holdings'] is not None
            has_balance = validation_results['standardized_balance_sheet'] is not None
            has_monthly = validation_results['standardized_monthly'] is not None
            
            validation_results['sufficient_data'] = has_holdings or has_balance
            
            # Add summary statistics
            validation_results['summary'] = {
                'has_valid_holdings': has_holdings,
                'has_valid_balance_sheet': has_balance,
                'has_valid_monthly': has_monthly,
                'holdings_records': len(validation_results['standardized_holdings']) if has_holdings else 0,
                'balance_records': len(validation_results['standardized_balance_sheet']) if has_balance else 0,
                'monthly_records': len(validation_results['standardized_monthly']) if has_monthly else 0
            }
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error validating and preparing data: {e}")
            validation_results['error'] = str(e)
            return validation_results
    
    def _calculate_robust_portfolio_performance(self, holdings_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate portfolio performance using centralized metrics with robust error handling.
        """
        try:
            if 'Market_Value_CNY' not in holdings_df.columns:
                return {'error': 'Market_Value_CNY column not found'}
            
            portfolio_values = holdings_df['Market_Value_CNY'].dropna()
            
            if len(portfolio_values) < 2:
                return {'error': 'Insufficient data points for performance calculation'}
            
            # Calculate returns with outlier detection
            returns = self.metrics.calculate_simple_returns(portfolio_values)
            
            # Detect and handle outliers in returns
            outlier_analysis = self.ts_processor.detect_outliers(returns.dropna(), method='modified_zscore', threshold=3)
            
            if outlier_analysis.get('outlier_count', 0) > 0:
                self.logger.warning(f"Detected {outlier_analysis['outlier_count']} outlier returns")
                # Optionally cap extreme returns
                returns = returns.clip(lower=returns.quantile(0.01), upper=returns.quantile(0.99))
            
            # Use centralized metrics calculations
            total_return = self.metrics.calculate_cumulative_return(portfolio_values)
            annualized_return = self.metrics.calculate_annualized_return(portfolio_values)
            annualized_volatility = self.metrics.calculate_annualized_volatility(returns)
            sharpe_ratio = self.metrics.calculate_sharpe_ratio(returns)
            drawdown_analysis = self.metrics.calculate_max_drawdown(portfolio_values)
            
            # Calculate Time-Weighted Return if DataManager is available
            twr_series = None
            if self.data_manager is not None:
                try:
                    transactions_df = self.data_manager.get_transactions()
                    twr_series = self.metrics.calculate_twr(portfolio_values, transactions_df)
                    self.logger.info(f"TWR calculation successful: {len(twr_series)} data points")
                except Exception as e:
                    self.logger.warning(f"TWR calculation failed: {e}")
                    twr_series = None
            
            # Estimate periods per year for additional context
            periods_per_year = self.metrics._estimate_periods_per_year(portfolio_values.index)
            
            # Rolling performance analysis (keep existing TS processor for consistency)
            rolling_metrics = self.ts_processor.calculate_rolling_metrics(
                returns.fillna(0),
                windows=[30, 90, 365],
                metrics=['mean', 'std']
            )
            
            return {
                'total_return': total_return,
                'annualized_return': annualized_return,
                'annualized_volatility': annualized_volatility,
                'sharpe_ratio': sharpe_ratio,
                'periods_per_year': periods_per_year,
                'data_period_years': len(portfolio_values) / periods_per_year,
                'outlier_analysis': outlier_analysis,
                'max_drawdown_analysis': drawdown_analysis,
                'twr_series': twr_series,  # Add TWR series
                'rolling_metrics_available': not rolling_metrics.empty,
                'final_value': portfolio_values.iloc[-1],
                'initial_value': portfolio_values.iloc[0]
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating robust portfolio performance: {e}")
            return {'error': str(e)}
    
    def _calculate_enhanced_risk_metrics(self, holdings_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate enhanced risk metrics using centralized metrics calculations.
        """
        try:
            if 'Market_Value_CNY' not in holdings_df.columns:
                return {'error': 'Market_Value_CNY column not found'}
            
            portfolio_values = holdings_df['Market_Value_CNY'].dropna()
            returns = self.metrics.calculate_simple_returns(portfolio_values).dropna()
            
            if len(returns) < 30:  # Need minimum data for stable risk metrics
                return {'error': 'Insufficient data for stable risk metrics (minimum 30 periods)'}
            
            # Use centralized risk metrics calculations
            results = {}
            
            # Basic risk metrics
            results['volatility'] = self.metrics.calculate_volatility(returns)
            results['annualized_volatility'] = self.metrics.calculate_annualized_volatility(returns)
            results['downside_deviation'] = self.metrics.calculate_downside_deviation(returns)
            
            # Risk-adjusted metrics
            results['sortino_ratio'] = self.metrics.calculate_sortino_ratio(returns)
            
            # VaR and CVaR calculations
            var_results = self.metrics.calculate_var(returns, [0.95, 0.99])
            cvar_results = self.metrics.calculate_cvar(returns, [0.95, 0.99])
            
            results.update(var_results)
            results.update(cvar_results)
            
            # Additional risk stability metrics (using existing methods)
            rolling_vol = self.metrics.calculate_rolling_volatility(returns, window=30)
            results['volatility_of_volatility'] = rolling_vol.std()
            results['risk_stability'] = 1 / (1 + results['volatility_of_volatility']) if results['volatility_of_volatility'] > 0 else 1
            
            # Maximum consecutive losses (keep existing implementation for consistency)
            consecutive_losses = self._calculate_consecutive_losses(returns)
            results['max_consecutive_losses'] = consecutive_losses['max_consecutive']
            results['max_consecutive_loss_value'] = consecutive_losses['max_loss_value']
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error calculating enhanced risk metrics: {e}")
            return {'error': str(e)}
    
    def _calculate_enhanced_trends(self, 
                                 holdings_df: Optional[pd.DataFrame],
                                 balance_sheet_df: Optional[pd.DataFrame],
                                 monthly_df: Optional[pd.DataFrame]) -> Dict[str, Any]:
        """
        Calculate comprehensive trend analysis with robust time-series handling.
        """
        trends = {}
        
        try:
            # Portfolio trends
            if holdings_df is not None and 'Market_Value_CNY' in holdings_df.columns:
                portfolio_values = holdings_df['Market_Value_CNY'].dropna()
                if len(portfolio_values) >= 2:
                    trends['portfolio_growth'] = self._calculate_robust_trend_metrics(
                        portfolio_values, 'Portfolio Value'
                    )
            
            # Balance sheet trends
            if balance_sheet_df is not None and not balance_sheet_df.empty:
                # Net Worth trend
                net_worth_cols = [col for col in balance_sheet_df.columns 
                                if 'net_worth' in col.lower() or 'net worth' in col.lower()]
                
                if net_worth_cols:
                    net_worth_series = balance_sheet_df[net_worth_cols[0]].dropna()
                    if len(net_worth_series) >= 2:
                        trends['net_worth'] = self._calculate_robust_trend_metrics(
                            net_worth_series, 'Net Worth'
                        )
                
                # Assets trend
                asset_cols = [col for col in balance_sheet_df.columns 
                            if 'total_assets' in col.lower() or 'total assets' in col.lower()]
                
                if asset_cols:
                    assets_series = balance_sheet_df[asset_cols[0]].dropna()
                    if len(assets_series) >= 2:
                        trends['total_assets'] = self._calculate_robust_trend_metrics(
                            assets_series, 'Total Assets'
                        )
            
            # Monthly trends (income/expense analysis)
            if monthly_df is not None and not monthly_df.empty:
                # Income trend
                income_cols = [col for col in monthly_df.columns 
                             if 'total_income' in col.lower()]
                
                if income_cols:
                    income_series = monthly_df[income_cols[0]].dropna()
                    if len(income_series) >= 2:
                        trends['income'] = self._calculate_robust_trend_metrics(
                            income_series, 'Total Income'
                        )
                
                # Expense trend  
                expense_cols = [col for col in monthly_df.columns 
                              if 'total_expense' in col.lower()]
                
                if expense_cols:
                    expense_series = monthly_df[expense_cols[0]].dropna()
                    if len(expense_series) >= 2:
                        trends['expenses'] = self._calculate_robust_trend_metrics(
                            expense_series, 'Total Expenses'
                        )
                
                # Savings rate trend
                if income_cols and expense_cols:
                    income_series = monthly_df[income_cols[0]].dropna()
                    expense_series = monthly_df[expense_cols[0]].dropna()
                    
                    # Align series and calculate savings rate
                    aligned_data = pd.concat([income_series, expense_series], axis=1, keys=['income', 'expense']).dropna()
                    
                    if len(aligned_data) >= 2:
                        savings = aligned_data['income'] - aligned_data['expense']
                        savings_rate = savings / aligned_data['income']
                        savings_rate = savings_rate.replace([np.inf, -np.inf], np.nan).dropna()
                        
                        if len(savings_rate) >= 2:
                            trends['savings_rate'] = self._calculate_robust_trend_metrics(
                                savings_rate, 'Savings Rate'
                            )
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error calculating enhanced trends: {e}")
            return {'error': str(e)}
    
    def _calculate_robust_trend_metrics(self, series: pd.Series, metric_name: str) -> Dict[str, Any]:
        """
        Calculate robust trend metrics with enhanced statistical analysis.
        """
        try:
            if len(series) < 2:
                return {'error': f'Insufficient data for {metric_name} trend analysis'}
            
            # Basic trend analysis
            current_value = series.iloc[-1]
            initial_value = series.iloc[0]
            total_change = current_value - initial_value
            total_change_pct = (current_value / initial_value - 1) * 100 if initial_value != 0 else 0
            
            # Time-based CAGR calculation
            if isinstance(series.index, pd.DatetimeIndex):
                years = (series.index[-1] - series.index[0]).days / 365.25
                cagr = (current_value / initial_value) ** (1/years) - 1 if years > 0 and initial_value > 0 else 0
            else:
                years = None
                cagr = None
            
            # Robust trend detection using multiple methods
            trend_analysis = self._detect_trend_direction(series)
            
            # Statistical measures
            volatility = series.std()
            coefficient_of_variation = volatility / series.mean() if series.mean() != 0 else np.inf
            
            # Rolling trend consistency
            if len(series) >= 12:  # Need sufficient data for rolling analysis
                rolling_trends = self._analyze_rolling_trends(series)
                trend_consistency = rolling_trends['consistency']
            else:
                trend_consistency = None
            
            return {
                'metric_name': metric_name,
                'current_value': current_value,
                'initial_value': initial_value,
                'total_change': total_change,
                'total_change_pct': total_change_pct,
                'cagr': cagr,
                'years_analyzed': years,
                'trend_direction': trend_analysis['direction'],
                'trend_strength': trend_analysis['strength'],
                'trend_consistency': trend_consistency,
                'average_value': series.mean(),
                'volatility': volatility,
                'coefficient_of_variation': coefficient_of_variation,
                'min_value': series.min(),
                'max_value': series.max(),
                'data_points': len(series),
                'is_robust': len(series) >= 12 and coefficient_of_variation < 2.0  # Quality indicator
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating robust trend metrics for {metric_name}: {e}")
            return {'error': str(e)}
    
    def _detect_trend_direction(self, series: pd.Series) -> Dict[str, Any]:
        """
        Robust trend direction detection using multiple methods.
        """
        try:
            # Method 1: Linear regression slope
            x = np.arange(len(series))
            slope, _ = np.polyfit(x, series.values, 1)
            
            # Method 2: Moving averages comparison  
            if len(series) >= 4:
                short_window = max(2, len(series) // 4)
                long_window = max(4, len(series) // 2)
                
                short_ma = series.rolling(window=short_window).mean().iloc[-1]
                long_ma = series.rolling(window=long_window).mean().iloc[-1]
                ma_trend = 1 if short_ma > long_ma else -1 if short_ma < long_ma else 0
            else:
                ma_trend = 0
            
            # Method 3: First vs last quartile comparison
            q1_avg = series.iloc[:len(series)//4].mean() if len(series) >= 4 else series.iloc[0]
            q4_avg = series.iloc[3*len(series)//4:].mean() if len(series) >= 4 else series.iloc[-1]
            quartile_trend = 1 if q4_avg > q1_avg else -1 if q4_avg < q1_avg else 0
            
            # Combine methods for robust detection
            trend_signals = [
                1 if slope > 0 else -1 if slope < 0 else 0,
                ma_trend,
                quartile_trend
            ]
            
            # Majority vote
            trend_vote = sum(trend_signals)
            
            if trend_vote > 0:
                direction = "Increasing"
            elif trend_vote < 0:
                direction = "Decreasing" 
            else:
                direction = "Stable"
            
            # Calculate trend strength (0-1)
            strength = abs(trend_vote) / len([s for s in trend_signals if s != 0]) if any(trend_signals) else 0
            
            return {
                'direction': direction,
                'strength': strength,
                'linear_slope': slope,
                'methods_agreement': len([s for s in trend_signals if s == np.sign(trend_vote)]) if trend_vote != 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error detecting trend direction: {e}")
            return {'direction': 'Unknown', 'strength': 0}
    
    def _analyze_rolling_trends(self, series: pd.Series, window: int = 6) -> Dict[str, Any]:
        """
        Analyze consistency of trends over rolling windows.
        """
        try:
            if len(series) < window * 2:
                return {'consistency': None, 'error': 'Insufficient data for rolling trend analysis'}
            
            rolling_slopes = []
            
            for i in range(window, len(series)):
                window_data = series.iloc[i-window:i]
                x = np.arange(len(window_data))
                slope, _ = np.polyfit(x, window_data.values, 1)
                rolling_slopes.append(slope)
            
            rolling_slopes = np.array(rolling_slopes)
            
            # Calculate consistency metrics
            slope_std = np.std(rolling_slopes)
            slope_mean = np.mean(rolling_slopes)
            
            # Consistency as inverse of coefficient of variation
            consistency = 1 / (1 + slope_std / abs(slope_mean)) if slope_mean != 0 else 0
            
            # Direction consistency (percentage of periods with same trend direction)
            positive_slopes = (rolling_slopes > 0).sum()
            negative_slopes = (rolling_slopes < 0).sum()
            direction_consistency = max(positive_slopes, negative_slopes) / len(rolling_slopes)
            
            return {
                'consistency': consistency,
                'direction_consistency': direction_consistency,
                'average_slope': slope_mean,
                'slope_volatility': slope_std
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing rolling trends: {e}")
            return {'consistency': None, 'error': str(e)}
    
    def _calculate_robust_attribution(self, holdings_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate robust performance attribution with error handling.
        """
        try:
            # This is a simplified version - in practice would need asset-level data
            total_performance = self._calculate_robust_portfolio_performance(holdings_df)
            
            attribution = {
                'portfolio_performance': total_performance,
                'attribution_method': 'simplified_total_portfolio',
                'note': 'Detailed asset-level attribution requires MultiIndex holdings data'
            }
            
            return attribution
            
        except Exception as e:
            self.logger.error(f"Error calculating robust attribution: {e}")
            return {'error': str(e)}
    
    def _calculate_robust_drawdown(self, portfolio_values: pd.Series) -> Dict[str, Any]:
        """
        Calculate robust drawdown analysis.
        """
        try:
            # Calculate running maximum
            running_max = portfolio_values.expanding().max()
            
            # Calculate drawdown
            drawdown = (portfolio_values - running_max) / running_max
            
            # Find maximum drawdown
            max_drawdown = drawdown.min()
            
            # Find drawdown periods
            drawdown_periods = self._identify_drawdown_periods(drawdown)
            
            return {
                'max_drawdown': max_drawdown,
                'max_drawdown_pct': max_drawdown * 100,
                'drawdown_periods': len(drawdown_periods),
                'longest_drawdown_days': max([p['duration_days'] for p in drawdown_periods]) if drawdown_periods else 0,
                'current_drawdown': drawdown.iloc[-1],
                'current_drawdown_pct': drawdown.iloc[-1] * 100
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating robust drawdown: {e}")
            return {'error': str(e)}
    
    def _identify_drawdown_periods(self, drawdown: pd.Series) -> List[Dict[str, Any]]:
        """
        Identify distinct drawdown periods.
        """
        try:
            periods = []
            in_drawdown = False
            start_date = None
            
            for date, dd_value in drawdown.items():
                if dd_value < -0.001 and not in_drawdown:  # Start of drawdown (0.1% threshold)
                    in_drawdown = True
                    start_date = date
                elif dd_value >= -0.001 and in_drawdown:  # End of drawdown
                    in_drawdown = False
                    if start_date:
                        duration = (date - start_date).days
                        min_dd = drawdown.loc[start_date:date].min()
                        periods.append({
                            'start_date': start_date,
                            'end_date': date,
                            'duration_days': duration,
                            'max_drawdown': min_dd
                        })
            
            return periods
            
        except Exception as e:
            self.logger.error(f"Error identifying drawdown periods: {e}")
            return []
    
    def _calculate_consecutive_losses(self, returns: pd.Series) -> Dict[str, Any]:
        """
        Calculate maximum consecutive losses.
        """
        try:
            consecutive_count = 0
            max_consecutive = 0
            consecutive_sum = 0
            max_loss_value = 0
            
            for return_val in returns:
                if return_val < 0:
                    consecutive_count += 1
                    consecutive_sum += return_val
                    max_consecutive = max(max_consecutive, consecutive_count)
                    max_loss_value = min(max_loss_value, consecutive_sum)
                else:
                    consecutive_count = 0
                    consecutive_sum = 0
            
            return {
                'max_consecutive': max_consecutive,
                'max_loss_value': max_loss_value
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating consecutive losses: {e}")
            return {'max_consecutive': 0, 'max_loss_value': 0}
    
    def _estimate_periods_per_year_robust(self, date_index: pd.DatetimeIndex) -> float:
        """
        Robust estimation of periods per year from date index.
        """
        try:
            if len(date_index) < 2:
                return 12.0  # Default to monthly
            
            # Calculate median time difference for robust estimation
            time_diffs = pd.Series(date_index).diff().dropna()
            median_diff = time_diffs.median()
            
            # Convert to periods per year
            days_per_period = median_diff.days
            
            if days_per_period <= 7:
                return 52  # Weekly
            elif days_per_period <= 35:
                return 12  # Monthly  
            elif days_per_period <= 100:
                return 4   # Quarterly
            else:
                return 1   # Yearly
                
        except Exception as e:
            self.logger.warning(f"Error estimating periods per year: {e}")
            return 12.0  # Default to monthly
    
    def _generate_enhanced_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate enhanced performance summary with data quality indicators.
        """
        try:
            summary = {
                'data_quality_score': 0,
                'analysis_reliability': 'Unknown',
                'key_metrics': {},
                'recommendations': []
            }
            
            # Calculate data quality score
            quality_factors = []
            
            # Check data validation results
            if 'data_quality' in results:
                dq = results['data_quality']
                if dq.get('sufficient_data', False):
                    quality_factors.append(0.3)
                
                summary_stats = dq.get('summary', {})
                if summary_stats.get('has_valid_holdings', False):
                    quality_factors.append(0.3)
                if summary_stats.get('has_valid_balance_sheet', False):
                    quality_factors.append(0.2)
                if summary_stats.get('has_valid_monthly', False):
                    quality_factors.append(0.2)
            
            summary['data_quality_score'] = sum(quality_factors)
            
            # Determine analysis reliability
            if summary['data_quality_score'] >= 0.8:
                summary['analysis_reliability'] = 'High'
            elif summary['data_quality_score'] >= 0.5:
                summary['analysis_reliability'] = 'Medium'
            else:
                summary['analysis_reliability'] = 'Low'
            
            # Extract key metrics
            if 'portfolio_performance' in results and 'error' not in results['portfolio_performance']:
                perf = results['portfolio_performance']
                summary['key_metrics']['annualized_return_pct'] = round(perf.get('annualized_return', 0) * 100, 2)
                summary['key_metrics']['sharpe_ratio'] = round(perf.get('sharpe_ratio', 0), 2)
                summary['key_metrics']['max_drawdown_pct'] = round(perf.get('drawdown_analysis', {}).get('max_drawdown_pct', 0), 2)
            
            # Generate recommendations based on analysis
            if summary['data_quality_score'] < 0.5:
                summary['recommendations'].append("Improve data quality and completeness for more reliable analysis")
            
            if 'risk_metrics' in results and results['risk_metrics'].get('risk_stability', 0) < 0.7:
                summary['recommendations'].append("Consider risk management strategies due to high volatility")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating enhanced summary: {e}")
            return {'error': str(e)}
