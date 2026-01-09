"""
Attribution Model Implementation using Brinson-Fachler Method

The Brinson-Fachler model decomposes portfolio excess return into three components:
1. Allocation Effect: Impact of over/underweighting asset classes vs benchmark
2. Selection Effect: Impact of security selection within each asset class  
3. Interaction Effect: Combined effect of allocation and selection decisions

Mathematical Framework:
- Portfolio Return: Rp = Σ(wi * Ri) where wi = portfolio weight, Ri = asset class return
- Benchmark Return: Rb = Σ(Wi * Bi) where Wi = benchmark weight, Bi = benchmark return
- Excess Return: Rp - Rb = Allocation + Selection + Interaction

Attribution Effects:
- Allocation Effect: Σ((wi - Wi) * Bi)
- Selection Effect: Σ(Wi * (Ri - Bi))  
- Interaction Effect: Σ((wi - Wi) * (Ri - Bi))
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import date
from dateutil.relativedelta import relativedelta


@dataclass
class AttributionResult:
    """
    Container for performance attribution analysis results
    """
    # Portfolio and benchmark totals
    portfolio_return: float
    benchmark_return: float
    excess_return: float
    
    # Attribution effects by asset class
    allocation_effects: Dict[str, float]
    selection_effects: Dict[str, float] 
    interaction_effects: Dict[str, float]
    
    # Total attribution effects
    total_allocation_effect: float
    total_selection_effect: float
    total_interaction_effect: float
    
    # Metadata
    period_start: date
    period_end: date
    asset_classes: List[str]
    
    def __post_init__(self):
        """Validate attribution results consistency"""
        calculated_excess = (self.total_allocation_effect + 
                           self.total_selection_effect + 
                           self.total_interaction_effect)
        
        tolerance = 0.0001  # 1 basis point tolerance
        if abs(self.excess_return - calculated_excess) > tolerance:
            raise ValueError(
                f"Attribution decomposition error: "
                f"Excess return {self.excess_return:.4f} != "
                f"Sum of effects {calculated_excess:.4f}"
            )
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert attribution results to DataFrame for analysis"""
        data = []
        for asset_class in self.asset_classes:
            data.append({
                'Asset_Class': asset_class,
                'Allocation_Effect': self.allocation_effects.get(asset_class, 0.0),
                'Selection_Effect': self.selection_effects.get(asset_class, 0.0),
                'Interaction_Effect': self.interaction_effects.get(asset_class, 0.0),
                'Total_Effect': (self.allocation_effects.get(asset_class, 0.0) +
                               self.selection_effects.get(asset_class, 0.0) +
                               self.interaction_effects.get(asset_class, 0.0))
            })
        
        df = pd.DataFrame(data)
        
        # Add totals row
        totals = {
            'Asset_Class': 'TOTAL',
            'Allocation_Effect': self.total_allocation_effect,
            'Selection_Effect': self.total_selection_effect,
            'Interaction_Effect': self.total_interaction_effect,
            'Total_Effect': self.excess_return
        }
        df = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)
        
        return df


class AttributionModel:
    """
    Brinson-Fachler Performance Attribution Model
    
    This class implements the Brinson-Fachler attribution methodology to analyze
    portfolio performance relative to a benchmark.
    """
    
    def __init__(self):
        """Initialize the attribution model"""
        self.last_attribution: Optional[AttributionResult] = None
    
    def calculate_attribution(
        self,
        portfolio_weights: Dict[str, float],
        portfolio_returns: Dict[str, float],
        benchmark_weights: Dict[str, float],
        benchmark_returns: Dict[str, float],
        period_start: date,
        period_end: date
    ) -> AttributionResult:
        """
        Calculate Brinson-Fachler attribution effects
        
        Args:
            portfolio_weights: Asset class weights in portfolio (e.g., {'Equity': 0.6, 'Bonds': 0.4})
            portfolio_returns: Asset class returns in portfolio (e.g., {'Equity': 0.08, 'Bonds': 0.03})
            benchmark_weights: Asset class weights in benchmark
            benchmark_returns: Asset class returns in benchmark
            period_start: Analysis period start date
            period_end: Analysis period end date
            
        Returns:
            AttributionResult object containing detailed attribution analysis
        """
        
        # Validate inputs
        self._validate_inputs(portfolio_weights, portfolio_returns, 
                            benchmark_weights, benchmark_returns)
        
        # Get common asset classes
        asset_classes = list(set(portfolio_weights.keys()) | set(benchmark_weights.keys()))
        
        # Initialize results dictionaries
        allocation_effects = {}
        selection_effects = {}
        interaction_effects = {}
        
        # Calculate attribution effects for each asset class
        for asset_class in asset_classes:
            # Get weights and returns (default to 0 if missing)
            wp = portfolio_weights.get(asset_class, 0.0)  # Portfolio weight
            wb = benchmark_weights.get(asset_class, 0.0)  # Benchmark weight
            rp = portfolio_returns.get(asset_class, 0.0)  # Portfolio return
            rb = benchmark_returns.get(asset_class, 0.0)  # Benchmark return
            
            # Calculate Brinson-Fachler effects
            allocation_effects[asset_class] = (wp - wb) * rb
            selection_effects[asset_class] = wb * (rp - rb)
            interaction_effects[asset_class] = (wp - wb) * (rp - rb)
        
        # Calculate portfolio and benchmark total returns
        portfolio_return = sum(portfolio_weights.get(ac, 0) * portfolio_returns.get(ac, 0) 
                             for ac in asset_classes)
        benchmark_return = sum(benchmark_weights.get(ac, 0) * benchmark_returns.get(ac, 0) 
                             for ac in asset_classes)
        
        # Calculate total effects
        total_allocation = sum(allocation_effects.values())
        total_selection = sum(selection_effects.values())
        total_interaction = sum(interaction_effects.values())
        
        # Create and store result
        result = AttributionResult(
            portfolio_return=portfolio_return,
            benchmark_return=benchmark_return,
            excess_return=portfolio_return - benchmark_return,
            allocation_effects=allocation_effects,
            selection_effects=selection_effects,
            interaction_effects=interaction_effects,
            total_allocation_effect=total_allocation,
            total_selection_effect=total_selection,
            total_interaction_effect=total_interaction,
            period_start=period_start,
            period_end=period_end,
            asset_classes=asset_classes
        )
        
        self.last_attribution = result
        return result
    
    def _validate_inputs(
        self,
        portfolio_weights: Dict[str, float],
        portfolio_returns: Dict[str, float],
        benchmark_weights: Dict[str, float],
        benchmark_returns: Dict[str, float]
    ) -> None:
        """Validate input data for attribution calculation"""
        
        # Check weight normalization (should sum to approximately 1.0)
        portfolio_weight_sum = sum(portfolio_weights.values())
        benchmark_weight_sum = sum(benchmark_weights.values())
        
        tolerance = 0.01  # 1% tolerance for weight normalization
        
        if abs(portfolio_weight_sum - 1.0) > tolerance:
            raise ValueError(
                f"Portfolio weights sum to {portfolio_weight_sum:.4f}, "
                f"expected approximately 1.0"
            )
            
        if abs(benchmark_weight_sum - 1.0) > tolerance:
            raise ValueError(
                f"Benchmark weights sum to {benchmark_weight_sum:.4f}, "
                f"expected approximately 1.0"
            )
        
        # Check for negative weights (flag as warning, don't fail)
        negative_portfolio = [ac for ac, w in portfolio_weights.items() if w < 0]
        negative_benchmark = [ac for ac, w in benchmark_weights.items() if w < 0]
        
        if negative_portfolio:
            print(f"Warning: Negative portfolio weights detected: {negative_portfolio}")
        if negative_benchmark:
            print(f"Warning: Negative benchmark weights detected: {negative_benchmark}")
        
        # Check for extremely large returns (potential data error)
        extreme_threshold = 2.0  # 200% return threshold
        
        extreme_portfolio = [ac for ac, r in portfolio_returns.items() if abs(r) > extreme_threshold]
        extreme_benchmark = [ac for ac, r in benchmark_returns.items() if abs(r) > extreme_threshold]
        
        if extreme_portfolio:
            print(f"Warning: Extreme portfolio returns detected: {extreme_portfolio}")
        if extreme_benchmark:
            print(f"Warning: Extreme benchmark returns detected: {extreme_benchmark}")
    
    def analyze_attribution_trends(
        self, 
        attribution_history: List[AttributionResult]
    ) -> Dict[str, any]:
        """
        Analyze trends in attribution results over time
        
        Args:
            attribution_history: List of AttributionResult objects from different periods
            
        Returns:
            Dictionary containing trend analysis
        """
        if len(attribution_history) < 2:
            return {"error": "Need at least 2 periods for trend analysis"}
        
        # Convert to DataFrame for easier analysis
        trend_data = []
        for result in attribution_history:
            trend_data.append({
                'Period_End': result.period_end,
                'Excess_Return': result.excess_return,
                'Allocation_Effect': result.total_allocation_effect,
                'Selection_Effect': result.total_selection_effect,
                'Interaction_Effect': result.total_interaction_effect
            })
        
        df = pd.DataFrame(trend_data).sort_values('Period_End')
        
        # Calculate trends
        trends = {
            'periods_analyzed': len(attribution_history),
            'average_excess_return': df['Excess_Return'].mean(),
            'excess_return_volatility': df['Excess_Return'].std(),
            'average_allocation_effect': df['Allocation_Effect'].mean(),
            'average_selection_effect': df['Selection_Effect'].mean(),
            'allocation_consistency': 1 - (df['Allocation_Effect'].std() / 
                                         abs(df['Allocation_Effect'].mean()) if df['Allocation_Effect'].mean() != 0 else np.inf),
            'selection_consistency': 1 - (df['Selection_Effect'].std() / 
                                        abs(df['Selection_Effect'].mean()) if df['Selection_Effect'].mean() != 0 else np.inf),
            'data': df
        }
        
        return trends


@dataclass
class MultiPeriodAttributionResult:
    """
    Container for multi-period performance attribution analysis results
    """
    # Summary data
    total_periods: int
    period_start: date
    period_end: date
    
    # Cumulative effects
    cumulative_portfolio_return: float
    cumulative_benchmark_return: float
    cumulative_excess_return: float
    cumulative_allocation_effect: float
    cumulative_selection_effect: float
    cumulative_interaction_effect: float
    
    # Period-by-period results
    monthly_results: List[AttributionResult]
    monthly_summary: pd.DataFrame
    
    # Validation
    attribution_reconciliation_error: float
    
    def __post_init__(self):
        """Validate multi-period attribution results consistency"""
        tolerance = 0.0001  # 1 basis point tolerance
        
        # Verify cumulative excess return equals sum of effects
        calculated_excess = (self.cumulative_allocation_effect + 
                           self.cumulative_selection_effect + 
                           self.cumulative_interaction_effect)
        
        if abs(self.cumulative_excess_return - calculated_excess) > tolerance:
            raise ValueError(
                f"Multi-period attribution decomposition error: "
                f"Cumulative excess return {self.cumulative_excess_return:.4f} != "
                f"Sum of cumulative effects {calculated_excess:.4f}"
            )
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert multi-period attribution results to summary DataFrame"""
        summary_data = {
            'Period': 'CUMULATIVE',
            'Portfolio_Return': self.cumulative_portfolio_return,
            'Benchmark_Return': self.cumulative_benchmark_return,
            'Excess_Return': self.cumulative_excess_return,
            'Allocation_Effect': self.cumulative_allocation_effect,
            'Selection_Effect': self.cumulative_selection_effect,
            'Interaction_Effect': self.cumulative_interaction_effect,
            'Total_Attribution': self.cumulative_allocation_effect + 
                               self.cumulative_selection_effect + 
                               self.cumulative_interaction_effect
        }
        
        cumulative_df = pd.DataFrame([summary_data])
        combined_df = pd.concat([self.monthly_summary, cumulative_df], ignore_index=True)
        
        return combined_df


class MultiPeriodAttributionModel:
    """
    Multi-Period Brinson-Fachler Performance Attribution Model
    
    This class extends the single-period AttributionModel to handle multi-period
    attribution analysis by chaining monthly attribution effects and providing
    cumulative analysis across time periods.
    """
    
    def __init__(self):
        """Initialize the multi-period attribution model"""
        self.single_period_model = AttributionModel()
        self.last_multi_period_attribution: Optional[MultiPeriodAttributionResult] = None
    
    def calculate_multi_period_attribution(
        self,
        historical_portfolio_data: pd.DataFrame,
        historical_benchmark_data: pd.DataFrame,
        end_date: date,
        periods: int = 24
    ) -> MultiPeriodAttributionResult:
        """
        Calculate multi-period Brinson-Fachler attribution effects
        
        Args:
            historical_portfolio_data: DataFrame with columns ['Date', 'Asset_Class', 'Weight', 'Return']
            historical_benchmark_data: DataFrame with columns ['Date', 'Asset_Class', 'Weight', 'Return']
            end_date: End date for analysis
            periods: Number of monthly periods to analyze (default: 24)
            
        Returns:
            MultiPeriodAttributionResult object containing detailed multi-period attribution analysis
        """
        
        # Calculate start date based on periods
        start_date = end_date - relativedelta(months=periods-1)
        
        # Get monthly periods for analysis
        analysis_periods = self._generate_analysis_periods(start_date, end_date)
        
        if len(analysis_periods) < periods:
            print(f"Warning: Only {len(analysis_periods)} periods available, requested {periods}")
        
        # Perform monthly attribution analysis
        monthly_results = []
        monthly_summary_data = []
        
        for period_start, period_end in analysis_periods:
            try:
                # Extract data for this period
                portfolio_data = self._extract_period_data(
                    historical_portfolio_data, period_start, period_end
                )
                benchmark_data = self._extract_period_data(
                    historical_benchmark_data, period_start, period_end
                )
                
                if portfolio_data is None or benchmark_data is None:
                    print(f"Warning: Insufficient data for period {period_start} to {period_end}")
                    continue
                
                # Calculate single-period attribution
                attribution_result = self.single_period_model.calculate_attribution(
                    portfolio_weights=portfolio_data['weights'],
                    portfolio_returns=portfolio_data['returns'],
                    benchmark_weights=benchmark_data['weights'],
                    benchmark_returns=benchmark_data['returns'],
                    period_start=period_start,
                    period_end=period_end
                )
                
                monthly_results.append(attribution_result)
                
                # Add to summary data
                monthly_summary_data.append({
                    'Period': f"{period_start.strftime('%Y-%m')}",
                    'Portfolio_Return': attribution_result.portfolio_return,
                    'Benchmark_Return': attribution_result.benchmark_return,
                    'Excess_Return': attribution_result.excess_return,
                    'Allocation_Effect': attribution_result.total_allocation_effect,
                    'Selection_Effect': attribution_result.total_selection_effect,
                    'Interaction_Effect': attribution_result.total_interaction_effect,
                    'Total_Attribution': (attribution_result.total_allocation_effect + 
                                        attribution_result.total_selection_effect + 
                                        attribution_result.total_interaction_effect)
                })
                
            except Exception as e:
                print(f"Error calculating attribution for period {period_start} to {period_end}: {e}")
                continue
        
        if not monthly_results:
            raise ValueError("No successful attribution calculations for any periods")
        
        # Calculate cumulative effects using geometric linking
        cumulative_portfolio_return = self._calculate_cumulative_return(
            [r.portfolio_return for r in monthly_results]
        )
        cumulative_benchmark_return = self._calculate_cumulative_return(
            [r.benchmark_return for r in monthly_results]
        )
        cumulative_excess_return = cumulative_portfolio_return - cumulative_benchmark_return
        
        # Sum attribution effects (additive for Brinson-Fachler)
        cumulative_allocation_effect = sum(r.total_allocation_effect for r in monthly_results)
        cumulative_selection_effect = sum(r.total_selection_effect for r in monthly_results)
        cumulative_interaction_effect = sum(r.total_interaction_effect for r in monthly_results)
        
        # Calculate reconciliation error
        attribution_sum = (cumulative_allocation_effect + 
                          cumulative_selection_effect + 
                          cumulative_interaction_effect)
        reconciliation_error = abs(cumulative_excess_return - attribution_sum)
        
        # Create monthly summary DataFrame
        monthly_summary = pd.DataFrame(monthly_summary_data)
        
        # Create and store result
        result = MultiPeriodAttributionResult(
            total_periods=len(monthly_results),
            period_start=monthly_results[0].period_start,
            period_end=monthly_results[-1].period_end,
            cumulative_portfolio_return=cumulative_portfolio_return,
            cumulative_benchmark_return=cumulative_benchmark_return,
            cumulative_excess_return=cumulative_excess_return,
            cumulative_allocation_effect=cumulative_allocation_effect,
            cumulative_selection_effect=cumulative_selection_effect,
            cumulative_interaction_effect=cumulative_interaction_effect,
            monthly_results=monthly_results,
            monthly_summary=monthly_summary,
            attribution_reconciliation_error=reconciliation_error
        )
        
        self.last_multi_period_attribution = result
        return result
    
    def _generate_analysis_periods(self, start_date: date, end_date: date) -> List[tuple]:
        """Generate list of monthly analysis periods"""
        periods = []
        current_date = start_date
        
        while current_date <= end_date:
            period_end = min(current_date + relativedelta(months=1) - relativedelta(days=1), end_date)
            periods.append((current_date, period_end))
            current_date = current_date + relativedelta(months=1)
        
        return periods
    
    def _extract_period_data(self, data: pd.DataFrame, period_start: date, period_end: date) -> Optional[Dict]:
        """Extract portfolio/benchmark data for a specific period"""
        try:
            # Filter data for the period
            if 'Date' in data.columns:
                period_data = data[
                    (pd.to_datetime(data['Date']).dt.date >= period_start) &
                    (pd.to_datetime(data['Date']).dt.date <= period_end)
                ]
            else:
                # Assume data is already filtered or indexed by date
                period_data = data
            
            if period_data.empty:
                return None
            
            # Group by asset class and calculate weighted average
            weights = {}
            returns = {}
            
            for asset_class in period_data['Asset_Class'].unique():
                asset_data = period_data[period_data['Asset_Class'] == asset_class]
                
                # Use the most recent weight and return for the period
                if not asset_data.empty:
                    weights[asset_class] = asset_data['Weight'].iloc[-1]
                    returns[asset_class] = asset_data['Return'].iloc[-1]
            
            return {'weights': weights, 'returns': returns}
            
        except Exception as e:
            print(f"Error extracting period data: {e}")
            return None
    
    def _calculate_cumulative_return(self, monthly_returns: List[float]) -> float:
        """Calculate cumulative return using geometric linking"""
        cumulative = 1.0
        for monthly_return in monthly_returns:
            cumulative *= (1.0 + monthly_return)
        return cumulative - 1.0
    
    def analyze_attribution_patterns(self) -> Dict[str, any]:
        """
        Analyze patterns in multi-period attribution results
        
        Returns:
            Dictionary containing pattern analysis
        """
        if self.last_multi_period_attribution is None:
            return {"error": "No multi-period attribution results available"}
        
        result = self.last_multi_period_attribution
        df = result.monthly_summary
        
        patterns = {
            'total_periods': result.total_periods,
            'cumulative_excess_return': result.cumulative_excess_return,
            'attribution_reconciliation_error': result.attribution_reconciliation_error,
            
            # Effect consistency
            'allocation_effect_consistency': {
                'mean': df['Allocation_Effect'].mean(),
                'std': df['Allocation_Effect'].std(),
                'consistent_direction': (df['Allocation_Effect'] > 0).sum() / len(df)
            },
            'selection_effect_consistency': {
                'mean': df['Selection_Effect'].mean(),
                'std': df['Selection_Effect'].std(),
                'consistent_direction': (df['Selection_Effect'] > 0).sum() / len(df)
            },
            
            # Performance consistency
            'excess_return_stats': {
                'mean': df['Excess_Return'].mean(),
                'std': df['Excess_Return'].std(),
                'positive_periods': (df['Excess_Return'] > 0).sum(),
                'negative_periods': (df['Excess_Return'] <= 0).sum()
            },
            
            # Attribution quality
            'attribution_quality': {
                'total_attribution_error': df['Total_Attribution'].sum() - result.cumulative_excess_return,
                'max_monthly_error': abs(df['Excess_Return'] - df['Total_Attribution']).max()
            }
        }
        
        return patterns
