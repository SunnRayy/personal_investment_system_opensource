import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from src.data_manager.manager import DataManager
from src.performance_attribution.attribution_model import AttributionModel, MultiPeriodAttributionModel
from src.performance_attribution.benchmark_manager import BenchmarkManager
from src.performance_attribution.benchmark_performance import BenchmarkPerformance
from src.portfolio_lib.data_integration import PortfolioAnalysisManager
from src.data_manager.connectors.market_data_connector import MarketDataConnector
from src.portfolio_lib.core.asset_mapper import create_asset_class_mapper

class AttributionBuilder:
    """
    Builder for performance attribution report data.
    Handles data preparation for waterfall charts, tables, and summary metrics.
    """
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.logger = logging.getLogger(__name__)
        # InitializeManagers
        self.attribution_model = AttributionModel()
        self.benchmark_manager = BenchmarkManager()
        # PortfolioAnalysisManager is initialized with default paths
        # In production, we might want to pass config paths if they differ
        self.portfolio_manager = PortfolioAnalysisManager() 
        self.market_connector = MarketDataConnector()
        self.benchmark_performance = BenchmarkPerformance(self.benchmark_manager, self.market_connector)

    def build_attribution_data(self, period_months: int = 12) -> Dict[str, Any]:
        """
        Build comprehensive attribution data using Brinson-Fachler Model.
        """
        self.logger.info(f"Building Brinson-Fachler attribution data for {period_months} months")
        
        try:
            # 1. Define Period
            # We need to look at available data to determine the end date
            # Using PortfolioAnalysisManager to access historical holdings
            if self.portfolio_manager.historical_holdings_df is not None and not self.portfolio_manager.historical_holdings_df.empty:
                holdings_dates = self.portfolio_manager.historical_holdings_df.index.get_level_values('Snapshot_Date').unique().sort_values()
                end_date = holdings_dates.max()
                # Calculate start date based on period_months
                target_start_date = end_date - pd.DateOffset(months=period_months)
                # Find closest actual snapshot
                start_date = holdings_dates[holdings_dates.searchsorted(target_start_date)] if target_start_date > holdings_dates.min() else holdings_dates.min()
            else:
                # Fallback if no historical holdings (unlikely provided Deep Dive findings, but safety first)
                end_date = pd.Timestamp.now().date()
                start_date = end_date - pd.DateOffset(months=period_months)
                self.logger.warning("No historical holdings found in PortfolioAnalysisManager, using current date range.")

            self.logger.info(f"Analysis Period: {start_date} to {end_date}")

            # 2. Get Portfolio Data (Weights & Returns) via PortfolioAnalysisManager
            # Force analysis to ensure we have latest calculations
            # Note: In a real persistent service, we might assume analysis is already done or cached.
            # For now, we run it to be safe.
            analysis_results = self.portfolio_manager.analyze_portfolio(debug=False)
            
            # Extract Returns
            portfolio_returns_df = analysis_results.get('returns_df')
            
            # Calculate Portfolio Returns for the specific period per asset class
            # We assume returns_df has columns like 'Global_Equity', 'Global_Bonds', etc. and indexed by Date
            portfolio_returns = {}
            if portfolio_returns_df is not None and not portfolio_returns_df.empty:
                # Filter for period
                period_returns = portfolio_returns_df.loc[start_date:end_date]
                if not period_returns.empty:
                    # Calculate cumulative return for the period: (1+r1)*(1+r2)... - 1
                    # Assuming returns are daily/monthly percentage changes
                    cumulative_returns = (1 + period_returns).prod() - 1
                    portfolio_returns = cumulative_returns.to_dict()
                else:
                    self.logger.warning(f"No portfolio returns found for period {start_date} to {end_date}")
            
            # Extract Weights (Average over period)
            # Use historical holdings to calculate average allocation
            portfolio_weights = self._calculate_period_average_weights(start_date, end_date)
            
            # 3. Get Benchmark Data
            # Weights from config (Static/Strategic)
            benchmark_weights = self.benchmark_manager.get_benchmark_weights()
            
            # Returns from Market Data
            benchmark_returns = self.benchmark_performance.get_benchmark_returns(start_date, end_date)
            
            # 4. Exclude Non-Liquid/Non-Rebalanceable Asset Classes
            # These distort attribution (Cash includes income, Property/Insurance are illiquid)
            excluded_classes = {'Cash', 'Real_Estate'}
            # Note: Insurance is mapped to Global_Bonds, but we keep bonds as they include tradeable bond ETFs
            
            self.logger.info(f"Excluding non-liquid classes from attribution: {excluded_classes}")
            
            # Filter portfolio weights and returns
            filtered_weights = {k: v for k, v in portfolio_weights.items() if k not in excluded_classes}
            filtered_returns = {k: v for k, v in portfolio_returns.items() if k not in excluded_classes}
            
            # Filter benchmark weights and returns to match
            filtered_bench_weights = {k: v for k, v in benchmark_weights.items() if k not in excluded_classes}
            filtered_bench_returns = {k: v for k, v in benchmark_returns.items() if k not in excluded_classes}
            
            # 5. Sanitize Inputs (Filter out Non-Benchmark Keys)
            # This ensures no "ghost" keys like '股票' enter the model
            valid_keys = set(filtered_bench_weights.keys())
            
            sanitized_weights = {}
            for k, v in filtered_weights.items():
                if k in valid_keys:
                    sanitized_weights[k] = v
                else:
                    self.logger.warning(f"Dropping invalid weight key: '{k}' (Value: {v:.4f})")
            
            sanitized_returns = {}
            for k, v in filtered_returns.items():
                if k in valid_keys:
                    sanitized_returns[k] = v
                else:
                    self.logger.warning(f"Dropping invalid return key: '{k}' (Value: {v:.4f})")
            
            # Recalculate weights sum and re-normalize
            total_weight = sum(sanitized_weights.values())
            if total_weight < 0.5:
                 self.logger.warning(f"Total weight after filtering is very low: {total_weight:.2%}. Check asset mapping.")
            elif total_weight > 0:
                 # Re-normalize to sum to 1.0
                 for k in sanitized_weights:
                     sanitized_weights[k] /= total_weight
                 self.logger.info(f"Re-normalized portfolio weights to 100% (from {total_weight:.2%})")
            
            # Also re-normalize benchmark weights
            bench_total = sum(filtered_bench_weights.values())
            if bench_total > 0:
                for k in filtered_bench_weights:
                    filtered_bench_weights[k] /= bench_total
            
            # 6. Run Attribution Calculation
            attribution_result = self.attribution_model.calculate_attribution(
                portfolio_weights=sanitized_weights,
                portfolio_returns=sanitized_returns,
                benchmark_weights=filtered_bench_weights,
                benchmark_returns=filtered_bench_returns,
                period_start=start_date,
                period_end=end_date
            )
            
            # 5. Format Output for Web App
            return self._format_attribution_for_view(attribution_result)

        except Exception as e:
            self.logger.error(f"Error building attribution data: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._get_empty_structure()

    def _calculate_period_average_weights(self, start_date, end_date) -> Dict[str, float]:
        """
        Calculate average portfolio weights for each asset class over the period.
        """
        historical_holdings = self.portfolio_manager.historical_holdings_df
        if historical_holdings is None or historical_holdings.empty:
            # Fallback to current holdings if no history
            self.logger.warning("Using current holdings for weights (no history)")
            current_holdings = self.portfolio_manager.holdings_df
            if current_holdings is None or current_holdings.empty:
                return {}
            
            # Calculate weights from current
            total_value = current_holdings['Market_Value_CNY'].sum()
            if total_value == 0: return {}
            weights = current_holdings.groupby('Asset_Class')['Market_Value_CNY'].sum() / total_value
            
            # Map Chinese keys to English Benchmark keys for current holdings fallback
            weights_dict = weights.to_dict()
            key_mapping = {
                '股票': 'Global_Equity',
                '固定收益': 'Global_Bonds', 
                '房地产': 'Real_Estate',
                '商品': 'Commodities',
                '现金': 'Cash',
                '另类投资': 'Commodities',
                '保险': 'Global_Bonds', 
                '其他': 'Cash'
            }
            mapped_weights = {}
            for k, v in weights_dict.items():
                clean_k = str(k).strip()
                new_key = key_mapping.get(clean_k, clean_k)
                mapped_weights[new_key] = mapped_weights.get(new_key, 0.0) + v
                
            return mapped_weights

        # Filter for period
        # Note: Index is MultiIndex (Snapshot_Date, Asset_ID)
        # We need to handle slicing on the first level
        try:
            # Create mask for date range
            dates = historical_holdings.index.get_level_values('Snapshot_Date')
            mask = (dates >= start_date) & (dates <= end_date)
            period_holdings = historical_holdings[mask]
            
            if period_holdings.empty:
                return {}

            # Check if Asset_Class is in columns (it should be)
            if 'Asset_Class' not in period_holdings.columns:
                # Need to map assets. accessing mapper from portfolio manager
                # Use helper from asset_mapper
                self.logger.info("Mapping historical holdings to asset classes...")
                map_to_sub, map_to_top = create_asset_class_mapper()
                
                # Apply mapping
                if 'Asset_ID' in period_holdings.index.names:
                    asset_ids = period_holdings.index.get_level_values('Asset_ID')
                    period_holdings = period_holdings.copy()
                    period_holdings['Asset_Class'] = [map_to_top(str(aid)) for aid in asset_ids]
                elif 'Asset_ID' in period_holdings.columns:
                     period_holdings = period_holdings.copy()
                     period_holdings['Asset_Class'] = period_holdings['Asset_ID'].apply(lambda x: map_to_top(str(x)))
                else:
                    self.logger.warning("Could not find Asset_ID for mapping")
                    return {}

            # Group by Date then Asset Class to get daily weights
            # 1. Sum value by Date
            daily_totals = period_holdings.groupby('Snapshot_Date')['Market_Value_CNY'].sum()
            
            # 2. Sum value by Date and Asset Class
            daily_class_totals = period_holdings.groupby(['Snapshot_Date', 'Asset_Class'])['Market_Value_CNY'].sum()
            
            # 3. Calculate weights per day
            daily_weights = daily_class_totals.div(daily_totals, level='Snapshot_Date')
            
            # 4. Average weights over all days in period
            # Use unstack(fill_value=0) to ensure days where a class is not present count as 0 weight
            daily_weights_matrix = daily_weights.unstack(level='Asset_Class', fill_value=0)
            avg_weights = daily_weights_matrix.mean()
            
            # Map Chinese keys to English Benchmark keys (align with PortfolioAnalysisManager return mapping)
            weights_dict = avg_weights.to_dict()
            key_mapping = {
                '股票': 'Global_Equity',
                '固定收益': 'Global_Bonds', 
                '房地产': 'Real_Estate',
                '商品': 'Commodities',
                '现金': 'Cash',
                '另类投资': 'Commodities',
                '保险': 'Global_Bonds', # Map Insurance to Bonds as proxy
                '其他': 'Cash'
            }
            mapped_weights = {}
            for k, v in weights_dict.items():
                # Clean key
                clean_k = str(k).strip()
                new_key = key_mapping.get(clean_k, clean_k)
                mapped_weights[new_key] = mapped_weights.get(new_key, 0.0) + v
            
            # Debug: Log mapped weights keys
            self.logger.info(f"Mapped Portfolio Weights Keys: {list(mapped_weights.keys())}")
            return mapped_weights
            
        except Exception as e:
            self.logger.error(f"Error calculating average weights: {e}")
            return {}

    def _format_attribution_for_view(self, result) -> Dict[str, Any]:
        """
        Format the AttributionResult object into dictionary for HTML template/Chart.js.
        """
        # Waterfall Chart Data
        # Order: Benchmark -> Allocation -> Selection -> Interaction -> Portfolio
        labels = ['Benchmark Return', 'Allocation Effect', 'Selection Effect', 'Interaction Effect', 'Portfolio Return']
        
        # Convert to percentage (multiply by 100 for display)
        data_values = [
            result.benchmark_return * 100,
            result.total_allocation_effect * 100,
            result.total_selection_effect * 100,
            result.total_interaction_effect * 100,
            result.portfolio_return * 100
        ]
        
        waterfall_series = {
            'labels': labels,
            'values': data_values
        }
        
        # Detailed Table Data
        details_df = result.to_dataframe()
        
        asset_class_table = []
        for _, row in details_df.iterrows():
            if row['Asset_Class'] == 'TOTAL': continue
            
            total_effect = row['Total_Effect'] * 100
            
            # Filter out rows with negligible effect (e.g. unmapped assets or zeros)
            # This cleans up the UI from showing "股票: 0.00%" etc if mapping failed partially
            if abs(total_effect) < 0.001 and abs(row['Allocation_Effect']) < 0.001:
                continue

            item = {
                'name': row['Asset_Class'],
                'allocation_effect': row['Allocation_Effect'] * 100,
                'selection_effect': row['Selection_Effect'] * 100,
                'interaction_effect': row['Interaction_Effect'] * 100,
                'total_effect': total_effect
            }
            asset_class_table.append(item)
            
        # Sort by total effect
        asset_class_table.sort(key=lambda x: abs(x['total_effect']), reverse=True)

        return {
            'period': f"Analysis", # We can make this dynamic
            'summary': {
                'portfolio_return': result.portfolio_return * 100,
                'benchmark_return': result.benchmark_return * 100,
                'excess_return': result.excess_return * 100,
                'allocation_contrib': result.total_allocation_effect * 100,
                'selection_contrib': result.total_selection_effect * 100,
                'interaction_contrib': result.total_interaction_effect * 100
            },
            'waterfall_chart': waterfall_series,
            'asset_class_table': asset_class_table
        }

    def _get_empty_structure(self):
        return {
            'period': 'N/A',
            'summary': {
                'portfolio_return': 0, 'benchmark_return': 0, 'excess_return': 0
            },
            'waterfall_chart': {'labels': [], 'values': []},
            'asset_class_table': []
        }
