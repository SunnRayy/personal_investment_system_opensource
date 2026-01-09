"""
Financial Metrics Module - Centralized Return and Risk Calculations

This module provides a single source of truth for all financial return and risk calculations
used throughout the personal investment system. All functions are designed to be mathematically
consistent, well-documented, and handle edge cases gracefully.

Author: Personal Investment System
Created: August 2025 (Phase 2.3)
"""

import pandas as pd
import numpy as np
from typing import Union, Optional, Dict, Any
import warnings

class FinancialMetrics:
    """
    Centralized financial metrics calculator providing standardized return and risk calculations.
    
    This class ensures mathematical consistency across the entire application and provides
    a single source of truth for all financial calculations.
    """
    
    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize the FinancialMetrics calculator.
        
        Args:
            risk_free_rate: Annual risk-free rate (default: 2%)
        """
        self.risk_free_rate = risk_free_rate
    
    # ========================================================================================
    # CORE RETURN CALCULATIONS
    # ========================================================================================
    
    def calculate_simple_returns(self, price_series: pd.Series) -> pd.Series:
        """
        Calculate simple period-over-period returns.
        
        Formula: R_t = (P_t / P_{t-1}) - 1
        
        Args:
            price_series: Time series of prices (pandas Series with datetime index)
            
        Returns:
            Series of simple returns (same index as input, first value will be NaN)
            
        Example:
            >>> prices = pd.Series([100, 105, 102, 108], index=pd.date_range('2023-01-01', periods=4))
            >>> returns = metrics.calculate_simple_returns(prices)
            >>> returns
            2023-01-01         NaN
            2023-01-02    0.050000  # (105/100) - 1
            2023-01-03   -0.028571  # (102/105) - 1  
            2023-01-04    0.058824  # (108/102) - 1
        """
        if not isinstance(price_series, pd.Series):
            raise TypeError("price_series must be a pandas Series")
        
        if len(price_series) < 2:
            warnings.warn("Price series has fewer than 2 data points")
            return pd.Series(dtype=float, index=price_series.index)
        
        # Handle zero or negative prices
        if (price_series <= 0).any():
            warnings.warn("Price series contains zero or negative values")
            price_series = price_series.replace(0, np.nan)
        
        return price_series.pct_change()
    
    def calculate_cumulative_return(self, price_series: pd.Series) -> float:
        """
        Calculate total cumulative return over the entire period.
        
        Formula: Total Return = (P_end / P_start) - 1
        
        Args:
            price_series: Time series of prices
            
        Returns:
            Total cumulative return as a float
            
        Example:
            >>> prices = pd.Series([100, 105, 102, 108])
            >>> total_return = metrics.calculate_cumulative_return(prices)
            >>> total_return
            0.08  # (108/100) - 1 = 8%
        """
        if not isinstance(price_series, pd.Series):
            raise TypeError("price_series must be a pandas Series")
        
        if len(price_series) < 2:
            return 0.0
        
        # Remove NaN values and ensure we have valid start/end prices
        clean_series = price_series.dropna()
        if len(clean_series) < 2:
            return 0.0
        
        start_price = clean_series.iloc[0]
        end_price = clean_series.iloc[-1]
        
        if start_price <= 0:
            warnings.warn("Starting price is zero or negative")
            return 0.0
        
        return (end_price / start_price) - 1
    
    def calculate_annualized_return(self, price_series: pd.Series, 
                                  periods_per_year: Optional[int] = None) -> float:
        """
        Calculate annualized return with automatic period detection.
        
        Formula: Annualized Return = (1 + Total Return)^(periods_per_year / n_periods) - 1
        
        Args:
            price_series: Time series of prices with datetime index
            periods_per_year: Number of periods per year. If None, auto-detected from index
            
        Returns:
            Annualized return as a float
            
        Example:
            >>> # Monthly data over 2 years
            >>> dates = pd.date_range('2022-01-01', periods=24, freq='M')  
            >>> prices = pd.Series([100 * (1.005)**i for i in range(24)], index=dates)
            >>> ann_return = metrics.calculate_annualized_return(prices)
            >>> ann_return  # Should be close to 6% annually
        """
        if not isinstance(price_series, pd.Series):
            raise TypeError("price_series must be a pandas Series")
        
        if len(price_series) < 2:
            return 0.0
        
        # Calculate total return
        total_return = self.calculate_cumulative_return(price_series)
        
        if total_return == 0:
            return 0.0
        
        # Auto-detect periods per year if not provided
        if periods_per_year is None:
            periods_per_year = self._estimate_periods_per_year(price_series.index)
        
        n_periods = len(price_series.dropna())
        
        if n_periods <= 1:
            return total_return
        
        # Calculate annualized return
        try:
            annualized_return = (1 + total_return) ** (periods_per_year / n_periods) - 1
            return annualized_return
        except (OverflowError, ZeroDivisionError):
            warnings.warn("Error in annualized return calculation, returning total return")
            return total_return
    
    def calculate_cagr(self, price_series: pd.Series) -> float:
        """
        Calculate Compound Annual Growth Rate (CAGR).
        
        Formula: CAGR = (Ending Value / Beginning Value)^(1/years) - 1
        
        Args:
            price_series: Time series of prices with datetime index
            
        Returns:
            CAGR as a float
            
        Example:
            >>> # Investment grows from $100 to $150 over 3 years
            >>> dates = pd.date_range('2021-01-01', '2024-01-01', freq='D')
            >>> prices = pd.Series([100 + (50/len(dates)) * i for i in range(len(dates))], index=dates)
            >>> cagr = metrics.calculate_cagr(prices)
            >>> cagr  # Should be around 14.47%
        """
        if not isinstance(price_series, pd.Series) or not hasattr(price_series.index, 'to_pydatetime'):
            raise TypeError("price_series must be a pandas Series with datetime index")
        
        clean_series = price_series.dropna()
        if len(clean_series) < 2:
            return 0.0
        
        start_value = clean_series.iloc[0]
        end_value = clean_series.iloc[-1]
        start_date = clean_series.index[0]
        end_date = clean_series.index[-1]
        
        if start_value <= 0:
            warnings.warn("Starting value is zero or negative")
            return 0.0
        
        # Calculate number of years
        years = (end_date - start_date).days / 365.25
        
        if years <= 0:
            return 0.0
        
        try:
            cagr = (end_value / start_value) ** (1 / years) - 1
            return cagr
        except (OverflowError, ZeroDivisionError):
            warnings.warn("Error in CAGR calculation")
            return 0.0
    
    # ========================================================================================
    # RISK CALCULATIONS
    # ========================================================================================
    
    def calculate_volatility(self, return_series: pd.Series) -> float:
        """
        Calculate period volatility (standard deviation of returns).
        
        Formula: σ = sqrt(E[(R - E[R])^2])
        
        Args:
            return_series: Series of returns
            
        Returns:
            Period volatility as a float
        """
        if not isinstance(return_series, pd.Series):
            raise TypeError("return_series must be a pandas Series")
        
        clean_returns = return_series.dropna()
        if len(clean_returns) < 2:
            return 0.0
        
        return clean_returns.std()
    
    def calculate_annualized_volatility(self, return_series: pd.Series,
                                      periods_per_year: Optional[int] = None) -> float:
        """
        Calculate annualized volatility with automatic period detection.
        
        Formula: σ_annual = σ_period * sqrt(periods_per_year)
        
        Args:
            return_series: Series of returns with datetime index
            periods_per_year: Number of periods per year. If None, auto-detected
            
        Returns:
            Annualized volatility as a float
        """
        if not isinstance(return_series, pd.Series):
            raise TypeError("return_series must be a pandas Series")
        
        period_volatility = self.calculate_volatility(return_series)
        
        if period_volatility == 0:
            return 0.0
        
        # Auto-detect periods per year if not provided
        if periods_per_year is None:
            periods_per_year = self._estimate_periods_per_year(return_series.index)
        
        return period_volatility * np.sqrt(periods_per_year)
    
    def calculate_downside_deviation(self, return_series: pd.Series, 
                                   target_return: float = 0.0) -> float:
        """
        Calculate downside deviation (volatility of negative excess returns).
        
        Formula: DD = sqrt(E[min(R - target, 0)^2])
        
        Args:
            return_series: Series of returns
            target_return: Target return threshold (default: 0%)
            
        Returns:
            Downside deviation as a float
        """
        if not isinstance(return_series, pd.Series):
            raise TypeError("return_series must be a pandas Series")
        
        clean_returns = return_series.dropna()
        if len(clean_returns) < 2:
            return 0.0
        
        # Calculate excess returns below target
        excess_returns = clean_returns - target_return
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0:
            return 0.0
        
        return downside_returns.std()
    
    def calculate_twr(self, price_series: pd.Series, transactions: pd.DataFrame) -> pd.Series:
        """
        Calculate Time-Weighted Return (TWR) removing the effect of external cash flows.
        
        TWR measures the compound growth rate of a portfolio, eliminating the distorting 
        effects of external cash flows (deposits and withdrawals). It's calculated by
        geometrically linking holding period returns between cash flow dates.
        
        Formula: TWR = ∏(1 + HPR_i) - 1
        Where HPR_i = (End_Value - Begin_Value - Cash_Flow) / Begin_Value
        
        Args:
            price_series: Time series of portfolio market values (pandas Series with datetime index)
            transactions: DataFrame with columns ['Date', 'Transaction_Type', 'Amount_Net']
            
        Returns:
            Series of cumulative TWR indexed by date
        """
        if not isinstance(price_series, pd.Series):
            raise TypeError("price_series must be a pandas Series")
        if not isinstance(transactions, pd.DataFrame):
            raise TypeError("transactions must be a pandas DataFrame")
        
        # Clean and prepare price series
        clean_prices = price_series.dropna()
        if len(clean_prices) < 2:
            return pd.Series(dtype=float, name='twr')
        
        # Filter transactions for external cash flows
        external_flow_types = ['Buy', 'Sell', 'Cash_Deposit', 'Cash_Withdrawal', 'Deposit', 'Withdrawal']
        if 'Transaction_Type' in transactions.columns and 'Amount_Net' in transactions.columns:
            # Filter for external cash flows
            external_flows = transactions[
                transactions['Transaction_Type'].isin(external_flow_types)
            ].copy()
            
            # Ensure Date column exists - check if Transaction_Date is in index or columns
            if 'Transaction_Date' in external_flows.columns:
                date_col = 'Transaction_Date'
                external_flows = external_flows[[date_col, 'Amount_Net']].copy()
                external_flows[date_col] = pd.to_datetime(external_flows[date_col])
                # Aggregate cash flows by date
                daily_flows = external_flows.groupby(date_col)['Amount_Net'].sum()
            elif external_flows.index.name == 'Transaction_Date' or 'transaction_date' in str(external_flows.index.name).lower():
                # Transaction_Date is the index
                external_flows = external_flows[['Amount_Net']].copy()
                external_flows.index = pd.to_datetime(external_flows.index)
                # Aggregate cash flows by date
                daily_flows = external_flows.groupby(external_flows.index)['Amount_Net'].sum()
            elif 'Date' in external_flows.columns:
                date_col = 'Date'
                external_flows = external_flows[[date_col, 'Amount_Net']].copy()
                external_flows[date_col] = pd.to_datetime(external_flows[date_col])
                # Aggregate cash flows by date
                daily_flows = external_flows.groupby(date_col)['Amount_Net'].sum()
            else:
                # Check if index appears to be datetime
                try:
                    pd.to_datetime(external_flows.index[:5])
                    # Use index as date column
                    external_flows = external_flows[['Amount_Net']].copy()
                    external_flows.index = pd.to_datetime(external_flows.index)
                    daily_flows = external_flows.groupby(external_flows.index)['Amount_Net'].sum()
                except Exception:
                    print("Warning: No valid date column found in transactions")
                    return pd.Series(dtype=float, name='twr')
        else:
            # No external flows data available, assume no cash flows
            daily_flows = pd.Series(dtype=float, name='Amount_Net')
        
        # Align price series and cash flows
        combined_dates = clean_prices.index.union(daily_flows.index).sort_values()
        aligned_prices = clean_prices.reindex(combined_dates, method='ffill')
        aligned_flows = daily_flows.reindex(combined_dates, fill_value=0.0)
        
        # Calculate holding period returns
        hpr_series = []
        cumulative_twr = []
        
        for i in range(1, len(aligned_prices)):
            begin_value = aligned_prices.iloc[i-1]
            end_value = aligned_prices.iloc[i]
            cash_flow = aligned_flows.iloc[i]
            
            # Skip if begin_value is zero or negative (would cause division issues)
            if begin_value <= 0:
                hpr = 0.0
            else:
                # HPR = (End_Value - Begin_Value - Cash_Flow) / Begin_Value
                hpr = (end_value - begin_value - cash_flow) / begin_value
            
            hpr_series.append(hpr)
            
            # Calculate cumulative TWR: ∏(1 + HPR) - 1
            if len(cumulative_twr) == 0:
                cumulative_twr.append(hpr)
            else:
                cumulative_twr.append((1 + cumulative_twr[-1]) * (1 + hpr) - 1)
        
        # Create result series
        twr_dates = combined_dates[1:]  # Skip first date since we need pairs
        result = pd.Series(cumulative_twr, index=twr_dates, name='twr')
        
        return result
    
    def calculate_max_drawdown(self, price_series: pd.Series) -> Dict[str, Any]:
        """
        Calculate comprehensive maximum drawdown analysis.
        
        Formula: DD_t = (P_t - Peak_t) / Peak_t where Peak_t = max(P_0, P_1, ..., P_t)
        
        Args:
            price_series: Time series of prices or cumulative values
            
        Returns:
            Dictionary with drawdown analysis:
            - max_drawdown: Maximum drawdown as negative float
            - max_drawdown_start: Start date of maximum drawdown
            - max_drawdown_end: End date of maximum drawdown  
            - current_drawdown: Current drawdown from recent peak
            - recovery_time_days: Days to recover from max drawdown (if recovered)
        """
        if not isinstance(price_series, pd.Series):
            raise TypeError("price_series must be a pandas Series")
        
        clean_series = price_series.dropna()
        if len(clean_series) < 2:
            return {
                'max_drawdown': 0.0,
                'max_drawdown_start': None,
                'max_drawdown_end': None, 
                'current_drawdown': 0.0,
                'recovery_time_days': None
            }
        
        # Calculate running maximum (peak values)
        rolling_max = clean_series.expanding().max()
        
        # Calculate drawdown series
        drawdown = (clean_series - rolling_max) / rolling_max
        
        # Find maximum drawdown
        max_drawdown = drawdown.min()
        max_dd_date = drawdown.idxmin()
        
        # Find start of maximum drawdown period (when price was at peak before the drop)
        max_dd_start = None
        if max_dd_date:
            peak_value = rolling_max.loc[max_dd_date]
            # Find the last time price was at this peak before the max drawdown date
            peak_dates = clean_series[clean_series == peak_value].index
            peak_dates_before_dd = peak_dates[peak_dates <= max_dd_date]
            if len(peak_dates_before_dd) > 0:
                max_dd_start = peak_dates_before_dd[-1]
        
        # Calculate current drawdown
        current_drawdown = drawdown.iloc[-1]
        
        # Calculate recovery time for max drawdown
        recovery_time_days = None
        if max_dd_date and max_dd_start:
            # Find when price recovered to the pre-drawdown peak
            recovery_dates = clean_series[clean_series >= rolling_max.loc[max_dd_date]].index
            recovery_dates_after_dd = recovery_dates[recovery_dates > max_dd_date]
            if len(recovery_dates_after_dd) > 0:
                recovery_date = recovery_dates_after_dd[0]
                recovery_time_days = (recovery_date - max_dd_start).days
        
        return {
            'max_drawdown': max_drawdown,
            'max_drawdown_start': max_dd_start,
            'max_drawdown_end': max_dd_date,
            'current_drawdown': current_drawdown, 
            'recovery_time_days': recovery_time_days,
            'drawdown_series': drawdown  # Full drawdown time series
        }
    
    def calculate_var(self, return_series: pd.Series, 
                     confidence_levels: Union[float, list] = [0.95, 0.99]) -> Dict[str, float]:
        """
        Calculate Value at Risk (VaR) at specified confidence levels.
        
        Formula: VaR_α = -Percentile(Returns, (1-α)*100)
        
        Args:
            return_series: Series of returns
            confidence_levels: Confidence level(s) for VaR calculation
            
        Returns:
            Dictionary with VaR values for each confidence level
        """
        if not isinstance(return_series, pd.Series):
            raise TypeError("return_series must be a pandas Series")
        
        if isinstance(confidence_levels, float):
            confidence_levels = [confidence_levels]
        
        clean_returns = return_series.dropna()
        if len(clean_returns) < 10:  # Need reasonable sample size
            warnings.warn("Insufficient data points for reliable VaR calculation")
            return {f'var_{int(cl*100)}': 0.0 for cl in confidence_levels}
        
        var_results = {}
        for cl in confidence_levels:
            if not (0 < cl < 1):
                warnings.warn(f"Confidence level {cl} should be between 0 and 1")
                continue
            
            percentile = (1 - cl) * 100
            var_value = -np.percentile(clean_returns, percentile)
            var_results[f'var_{int(cl*100)}'] = var_value
        
        return var_results
    
    def calculate_cvar(self, return_series: pd.Series,
                      confidence_levels: Union[float, list] = [0.95, 0.99]) -> Dict[str, float]:
        """
        Calculate Conditional Value at Risk (CVaR) - average of returns beyond VaR.
        
        Formula: CVaR_α = E[R | R <= VaR_α]
        
        Args:
            return_series: Series of returns
            confidence_levels: Confidence level(s) for CVaR calculation
            
        Returns:
            Dictionary with CVaR values for each confidence level
        """
        if not isinstance(return_series, pd.Series):
            raise TypeError("return_series must be a pandas Series")
        
        if isinstance(confidence_levels, float):
            confidence_levels = [confidence_levels]
        
        clean_returns = return_series.dropna()
        if len(clean_returns) < 10:
            warnings.warn("Insufficient data points for reliable CVaR calculation")
            return {f'cvar_{int(cl*100)}': 0.0 for cl in confidence_levels}
        
        # First calculate VaR values
        var_results = self.calculate_var(return_series, confidence_levels)
        
        cvar_results = {}
        for cl in confidence_levels:
            var_key = f'var_{int(cl*100)}'
            if var_key not in var_results:
                continue
            
            var_threshold = -var_results[var_key]  # VaR is positive, we need negative threshold
            tail_returns = clean_returns[clean_returns <= var_threshold]
            
            if len(tail_returns) > 0:
                cvar_value = -tail_returns.mean()  # Make positive like VaR
            else:
                cvar_value = -var_results[var_key]
            
            cvar_results[f'cvar_{int(cl*100)}'] = cvar_value
        
        return cvar_results
    
    # ========================================================================================
    # RISK-ADJUSTED METRICS
    # ========================================================================================
    
    def calculate_sharpe_ratio(self, return_series: pd.Series,
                              risk_free_rate: Optional[float] = None,
                              periods_per_year: Optional[int] = None) -> float:
        """
        Calculate Sharpe ratio with automatic annualization.
        
        Formula: Sharpe = (E[R] - R_f) / σ[R]
        
        Args:
            return_series: Series of returns with datetime index
            risk_free_rate: Annual risk-free rate. If None, uses instance default
            periods_per_year: Periods per year. If None, auto-detected
            
        Returns:
            Annualized Sharpe ratio as a float
        """
        if not isinstance(return_series, pd.Series):
            raise TypeError("return_series must be a pandas Series")
        
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate
        
        clean_returns = return_series.dropna()
        if len(clean_returns) < 2:
            return 0.0
        
        # Calculate annualized return and volatility
        if hasattr(return_series.index, 'to_pydatetime'):
            # If we have price data, convert to returns first
            if all(clean_returns >= 0) and clean_returns.mean() > 0.1:
                # Likely price data, convert to returns
                price_series = return_series
                return_series = self.calculate_simple_returns(price_series).dropna()
                clean_returns = return_series.dropna()
        
        if len(clean_returns) < 2:
            return 0.0
        
        # Auto-detect periods per year
        if periods_per_year is None:
            periods_per_year = self._estimate_periods_per_year(return_series.index)
        
        # Annualize metrics
        mean_return = clean_returns.mean() * periods_per_year
        volatility = clean_returns.std() * np.sqrt(periods_per_year)
        
        if volatility == 0:
            return 0.0
        
        excess_return = mean_return - risk_free_rate
        return excess_return / volatility
    
    def calculate_sortino_ratio(self, return_series: pd.Series,
                               target_return: float = 0.0,
                               risk_free_rate: Optional[float] = None,
                               periods_per_year: Optional[int] = None) -> float:
        """
        Calculate Sortino ratio using downside deviation.
        
        Formula: Sortino = (E[R] - Target) / DD where DD = downside deviation
        
        Args:
            return_series: Series of returns
            target_return: Target return threshold (annualized)
            risk_free_rate: Risk-free rate (used if target_return is None)
            periods_per_year: Periods per year. If None, auto-detected
            
        Returns:
            Annualized Sortino ratio as a float
        """
        if not isinstance(return_series, pd.Series):
            raise TypeError("return_series must be a pandas Series")
        
        clean_returns = return_series.dropna()
        if len(clean_returns) < 2:
            return 0.0
        
        # Auto-detect periods per year
        if periods_per_year is None:
            periods_per_year = self._estimate_periods_per_year(return_series.index)
        
        # Convert target return to period return
        period_target = target_return / periods_per_year
        
        # Calculate annualized mean return
        mean_return = clean_returns.mean() * periods_per_year
        
        # Calculate annualized downside deviation
        downside_dev = self.calculate_downside_deviation(clean_returns, period_target)
        annualized_dd = downside_dev * np.sqrt(periods_per_year)
        
        if annualized_dd == 0:
            return np.inf if mean_return > target_return else 0.0
        
        excess_return = mean_return - target_return
        return excess_return / annualized_dd
    
    def calculate_calmar_ratio(self, price_series: pd.Series) -> float:
        """
        Calculate Calmar ratio (annualized return / maximum drawdown).
        
        Formula: Calmar = Annualized Return / |Max Drawdown|
        
        Args:
            price_series: Time series of prices
            
        Returns:
            Calmar ratio as a float
        """
        if not isinstance(price_series, pd.Series):
            raise TypeError("price_series must be a pandas Series")
        
        # Calculate annualized return
        ann_return = self.calculate_annualized_return(price_series)
        
        # Calculate maximum drawdown
        dd_analysis = self.calculate_max_drawdown(price_series)
        max_drawdown = dd_analysis['max_drawdown']
        
        if max_drawdown == 0:
            return np.inf if ann_return > 0 else 0.0
        
        return ann_return / abs(max_drawdown)
    
    def calculate_beta(self, asset_returns: pd.Series, 
                      benchmark_returns: pd.Series) -> float:
        """
        Calculate beta (systematic risk measure relative to benchmark).
        
        Formula: β = Cov(R_asset, R_benchmark) / Var(R_benchmark)
        
        Args:
            asset_returns: Series of asset returns
            benchmark_returns: Series of benchmark returns
            
        Returns:
            Beta as a float
        """
        if not isinstance(asset_returns, pd.Series) or not isinstance(benchmark_returns, pd.Series):
            raise TypeError("Both inputs must be pandas Series")
        
        # Align the series and remove NaN values
        aligned_data = pd.DataFrame({
            'asset': asset_returns,
            'benchmark': benchmark_returns
        }).dropna()
        
        if len(aligned_data) < 10:  # Need reasonable sample size
            warnings.warn("Insufficient overlapping data points for reliable beta calculation")
            return 1.0  # Default beta
        
        asset_clean = aligned_data['asset']
        benchmark_clean = aligned_data['benchmark']
        
        # Calculate beta using covariance and variance
        covariance = np.cov(asset_clean, benchmark_clean)[0, 1]
        benchmark_variance = np.var(benchmark_clean, ddof=1)
        
        if benchmark_variance == 0:
            warnings.warn("Benchmark has zero variance")
            return 1.0
        
        beta = covariance / benchmark_variance
        return beta
    
    def calculate_alpha(self, asset_returns: pd.Series,
                       benchmark_returns: pd.Series,
                       risk_free_rate: Optional[float] = None,
                       periods_per_year: Optional[int] = None) -> float:
        """
        Calculate alpha (excess return above what CAPM predicts).
        
        Formula: α = E[R_asset] - (R_f + β * (E[R_benchmark] - R_f))
        
        Args:
            asset_returns: Series of asset returns
            benchmark_returns: Series of benchmark returns  
            risk_free_rate: Annual risk-free rate
            periods_per_year: Periods per year. If None, auto-detected
            
        Returns:
            Annualized alpha as a float
        """
        if not isinstance(asset_returns, pd.Series) or not isinstance(benchmark_returns, pd.Series):
            raise TypeError("Both inputs must be pandas Series")
        
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate
        
        # Align the series
        aligned_data = pd.DataFrame({
            'asset': asset_returns,
            'benchmark': benchmark_returns
        }).dropna()
        
        if len(aligned_data) < 10:
            warnings.warn("Insufficient overlapping data points for reliable alpha calculation")
            return 0.0
        
        asset_clean = aligned_data['asset']
        benchmark_clean = aligned_data['benchmark']
        
        # Auto-detect periods per year
        if periods_per_year is None:
            periods_per_year = self._estimate_periods_per_year(asset_returns.index)
        
        # Calculate beta
        beta = self.calculate_beta(asset_clean, benchmark_clean)
        
        # Calculate average returns (annualized)
        asset_mean = asset_clean.mean() * periods_per_year
        benchmark_mean = benchmark_clean.mean() * periods_per_year
        
        # Calculate alpha using CAPM
        expected_return = risk_free_rate + beta * (benchmark_mean - risk_free_rate)
        alpha = asset_mean - expected_return
        
        return alpha
    
    # ========================================================================================
    # ROLLING METRICS
    # ========================================================================================
    
    def calculate_rolling_sharpe(self, return_series: pd.Series,
                                window: int,
                                risk_free_rate: Optional[float] = None) -> pd.Series:
        """
        Calculate rolling Sharpe ratio over specified window.
        
        Args:
            return_series: Series of returns
            window: Rolling window size (number of periods)
            risk_free_rate: Period risk-free rate. If None, uses annualized rate
            
        Returns:
            Series of rolling Sharpe ratios
        """
        if not isinstance(return_series, pd.Series):
            raise TypeError("return_series must be a pandas Series")
        
        if risk_free_rate is None:
            # Convert annual risk-free rate to period rate
            periods_per_year = self._estimate_periods_per_year(return_series.index)
            risk_free_rate = self.risk_free_rate / periods_per_year
        
        def rolling_sharpe(x):
            if len(x.dropna()) < 2:
                return np.nan
            excess_returns = x - risk_free_rate
            return excess_returns.mean() / excess_returns.std() if excess_returns.std() > 0 else 0
        
        return return_series.rolling(window=window, min_periods=window//2).apply(rolling_sharpe)
    
    def calculate_rolling_volatility(self, return_series: pd.Series,
                                   window: int) -> pd.Series:
        """
        Calculate rolling volatility over specified window.
        
        Args:
            return_series: Series of returns
            window: Rolling window size (number of periods)
            
        Returns:
            Series of rolling volatilities
        """
        if not isinstance(return_series, pd.Series):
            raise TypeError("return_series must be a pandas Series")
        
        return return_series.rolling(window=window, min_periods=window//2).std()
    
    def calculate_rolling_beta(self, asset_returns: pd.Series,
                              benchmark_returns: pd.Series, 
                              window: int) -> pd.Series:
        """
        Calculate rolling beta over specified window.
        
        Args:
            asset_returns: Series of asset returns
            benchmark_returns: Series of benchmark returns
            window: Rolling window size
            
        Returns:
            Series of rolling betas
        """
        if not isinstance(asset_returns, pd.Series) or not isinstance(benchmark_returns, pd.Series):
            raise TypeError("Both inputs must be pandas Series")
        
        # Align series
        aligned_data = pd.DataFrame({
            'asset': asset_returns,
            'benchmark': benchmark_returns
        }).dropna()
        
        if len(aligned_data) < window:
            return pd.Series(dtype=float, index=asset_returns.index)
        
        # Calculate rolling correlation and volatilities separately
        rolling_corr = aligned_data['asset'].rolling(window).corr(aligned_data['benchmark'])
        rolling_asset_vol = aligned_data['asset'].rolling(window).std()
        rolling_bench_vol = aligned_data['benchmark'].rolling(window).std()
        
        # Beta = correlation * (asset_vol / benchmark_vol)
        rolling_beta = rolling_corr * (rolling_asset_vol / rolling_bench_vol)
        
        # Handle division by zero
        rolling_beta = rolling_beta.fillna(1.0)
        
        return rolling_beta
    
    # ========================================================================================
    # UTILITY METHODS
    # ========================================================================================
    
    def _estimate_periods_per_year(self, datetime_index: pd.DatetimeIndex) -> int:
        """
        Estimate periods per year from datetime index frequency.
        
        Args:
            datetime_index: Pandas datetime index
            
        Returns:
            Estimated number of periods per year
        """
        if len(datetime_index) < 2:
            return 252  # Default to daily
        
        # Calculate median time difference
        time_diffs = pd.Series(datetime_index).diff().dropna()
        median_diff = time_diffs.median()
        
        # Estimate periods per year based on median difference
        if median_diff.days >= 28:  # Monthly or less frequent
            return 12
        elif median_diff.days >= 6:  # Weekly
            return 52
        else:  # Daily
            return 252
    
    def get_metrics_summary(self, price_series: pd.Series,
                           benchmark_series: Optional[pd.Series] = None) -> Dict[str, Any]:
        """
        Calculate a comprehensive summary of all key metrics.
        
        Args:
            price_series: Time series of prices
            benchmark_series: Optional benchmark price series for relative metrics
            
        Returns:
            Dictionary with comprehensive metrics summary
        """
        if not isinstance(price_series, pd.Series):
            raise TypeError("price_series must be a pandas Series")
        
        # Calculate return series
        returns = self.calculate_simple_returns(price_series).dropna()
        
        # Basic return metrics
        summary = {
            'total_return': self.calculate_cumulative_return(price_series),
            'annualized_return': self.calculate_annualized_return(price_series),
            'cagr': self.calculate_cagr(price_series),
            
            # Risk metrics
            'volatility': self.calculate_volatility(returns),
            'annualized_volatility': self.calculate_annualized_volatility(returns),
            'max_drawdown_analysis': self.calculate_max_drawdown(price_series),
            'var_analysis': self.calculate_var(returns),
            'cvar_analysis': self.calculate_cvar(returns),
            
            # Risk-adjusted metrics
            'sharpe_ratio': self.calculate_sharpe_ratio(returns),
            'sortino_ratio': self.calculate_sortino_ratio(returns),
            'calmar_ratio': self.calculate_calmar_ratio(price_series),
        }
        
        # Add benchmark-relative metrics if provided
        if benchmark_series is not None:
            benchmark_returns = self.calculate_simple_returns(benchmark_series).dropna()
            summary.update({
                'beta': self.calculate_beta(returns, benchmark_returns),
                'alpha': self.calculate_alpha(returns, benchmark_returns),
            })
        
        return summary

    # ========================================================================================
    # CONCENTRATION RISK CALCULATIONS
    # ========================================================================================
    
    def calculate_single_asset_concentration_risk(self, holdings_data: pd.DataFrame, 
                                                 value_column: str = 'Market_Value_CNY',
                                                 symbol_column: str = 'Symbol',
                                                 name_column: str = 'Asset_Name') -> Dict[str, Any]:
        """
        Calculate concentration risk from the single largest holding.
        
        Args:
            holdings_data: DataFrame containing portfolio holdings
            value_column: Column name containing market values
            symbol_column: Column name containing asset symbols/tickers
            name_column: Column name containing asset names (fallback for symbol)
            
        Returns:
            Dictionary containing ticker, percentage, and risk level
            
        Example:
            {
                "ticker": "AMZN",
                "percentage": 18.5,
                "level": "风险较高"
            }
        """
        if holdings_data is None or holdings_data.empty:
            return {
                "ticker": "Unknown",
                "percentage": 0.0,
                "level": "无风险"
            }
        
        # Ensure value column exists
        if value_column not in holdings_data.columns:
            return {
                "ticker": "Error",
                "percentage": 0.0,
                "level": "数据错误"
            }
        
        # Calculate total portfolio value
        total_value = holdings_data[value_column].sum()
        
        if total_value <= 0:
            return {
                "ticker": "Empty",
                "percentage": 0.0,
                "level": "无投资"
            }
        
        # Find the largest holding by market value
        largest_holding_idx = holdings_data[value_column].idxmax()
        
        # Handle MultiIndex case - get the actual row data
        if isinstance(holdings_data.index, pd.MultiIndex):
            largest_holding_row = holdings_data.loc[largest_holding_idx]
            # If still returns DataFrame (multiple matches), take first
            if isinstance(largest_holding_row, pd.DataFrame):
                largest_holding_row = largest_holding_row.iloc[0]
        else:
            largest_holding_row = holdings_data.loc[largest_holding_idx]
        
        # Get ticker/symbol (with fallback logic)
        ticker = "Unknown"
        
        # Try Symbol column first
        if symbol_column in holdings_data.columns:
            try:
                symbol_value = largest_holding_row[symbol_column]
                if pd.notna(symbol_value) and str(symbol_value).strip():
                    ticker = str(symbol_value)
            except (KeyError, TypeError):
                pass
        
        # Try Asset_Name column as fallback
        if ticker == "Unknown" and name_column in holdings_data.columns:
            try:
                name_value = largest_holding_row[name_column]
                if pd.notna(name_value) and str(name_value).strip():
                    ticker = str(name_value)
            except (KeyError, TypeError):
                pass
        
        # Try Name column as final fallback
        if ticker == "Unknown" and 'Name' in holdings_data.columns:
            try:
                name_value = largest_holding_row['Name']
                if pd.notna(name_value) and str(name_value).strip():
                    ticker = str(name_value)
            except (KeyError, TypeError):
                pass
        
        # If still no ticker, try using the Asset_ID from index
        if ticker == "Unknown" and hasattr(largest_holding_idx, '__getitem__') and len(largest_holding_idx) > 1:
            try:
                ticker = str(largest_holding_idx[1])  # Asset_ID from MultiIndex
            except Exception:
                pass
        
        # Calculate percentage
        largest_value = largest_holding_row[value_column]
        percentage = (largest_value / total_value) * 100
        
        # Determine risk level based on concentration percentage
        if percentage >= 30:
            risk_level = "风险极高"
        elif percentage >= 20:
            risk_level = "风险较高"
        elif percentage >= 10:
            risk_level = "风险中等"
        elif percentage >= 5:
            risk_level = "风险较低"
        else:
            risk_level = "风险很低"
        
        return {
            "ticker": ticker,
            "percentage": round(percentage, 1),
            "level": risk_level
        }


# Convenience function for backward compatibility
def create_metrics_calculator(risk_free_rate: float = 0.02) -> FinancialMetrics:
    """
    Create a FinancialMetrics calculator instance.
    
    Args:
        risk_free_rate: Annual risk-free rate (default: 2%)
        
    Returns:
        FinancialMetrics calculator instance
    """
    return FinancialMetrics(risk_free_rate=risk_free_rate)
