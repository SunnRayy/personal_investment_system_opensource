"""
Data Adapter for Multi-Period Attribution Analysis

This module provides data transformation utilities to convert DataManager's
historical holdings format into the format required for multi-period
attribution analysis.
"""

import pandas as pd
from typing import Dict, List, Optional
from datetime import date
from dateutil.relativedelta import relativedelta


class AttributionDataAdapter:
    """
    Adapts data from DataManager and PortfolioAnalysisManager for use in
    multi-period attribution analysis.
    """
    
    def __init__(self, taxonomy_manager=None):
        """
        Initialize the data adapter
        
        Args:
            taxonomy_manager: Optional TaxonomyManager for asset classification
        """
        self.taxonomy_manager = taxonomy_manager
    
    def prepare_portfolio_data_for_attribution(
        self,
        historical_holdings: pd.DataFrame,
        returns_data: Optional[pd.DataFrame] = None,
        periods: int = 24
    ) -> pd.DataFrame:
        """
        Convert historical holdings data to format suitable for attribution analysis
        
        Args:
            historical_holdings: DataFrame with MultiIndex (Snapshot_Date, Asset_ID)
            returns_data: Optional DataFrame with monthly returns by asset class
            periods: Number of periods to include
            
        Returns:
            DataFrame with columns ['Date', 'Asset_Class', 'Weight', 'Return']
        """
        if historical_holdings is None or historical_holdings.empty:
            raise ValueError("Historical holdings data is required")
        
        # Get available snapshot dates
        if isinstance(historical_holdings.index, pd.MultiIndex):
            snapshot_dates = historical_holdings.index.get_level_values('Snapshot_Date').unique()
        else:
            raise ValueError("Expected MultiIndex with Snapshot_Date level")
        
        # Sort dates and take the most recent periods
        snapshot_dates = sorted(snapshot_dates)[-periods:]
        
        portfolio_data = []
        
        for snapshot_date in snapshot_dates:
            try:
                # Get holdings for this snapshot
                holdings_snapshot = historical_holdings.loc[snapshot_date]
                
                # Calculate total portfolio value
                if 'Market_Value_CNY' in holdings_snapshot.columns:
                    total_value = holdings_snapshot['Market_Value_CNY'].sum()
                else:
                    # Try alternative column names
                    value_cols = [col for col in holdings_snapshot.columns 
                                if 'value' in col.lower() or 'market' in col.lower()]
                    if value_cols:
                        total_value = holdings_snapshot[value_cols[0]].sum()
                    else:
                        print(f"Warning: No market value column found for {snapshot_date}")
                        continue
                
                if total_value <= 0:
                    print(f"Warning: Zero or negative portfolio value for {snapshot_date}")
                    continue
                
                # Map holdings to asset classes and calculate weights
                asset_class_data = self._aggregate_by_asset_class(holdings_snapshot, total_value)
                
                # Add returns if available
                if returns_data is not None:
                    asset_class_data = self._add_returns_data(
                        asset_class_data, returns_data, snapshot_date
                    )
                
                # Add to portfolio data
                for asset_class, data in asset_class_data.items():
                    portfolio_data.append({
                        'Date': snapshot_date,
                        'Asset_Class': asset_class,
                        'Weight': data['weight'],
                        'Return': data.get('return', 0.0)
                    })
                    
            except Exception as e:
                print(f"Error processing snapshot {snapshot_date}: {e}")
                continue
        
        if not portfolio_data:
            raise ValueError("No valid portfolio data could be prepared")
        
        return pd.DataFrame(portfolio_data)
    
    def prepare_benchmark_data_for_attribution(
        self,
        benchmark_config: Dict,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        Convert benchmark configuration to format suitable for attribution analysis
        
        Args:
            benchmark_config: Benchmark configuration dictionary
            start_date: Start date for benchmark data
            end_date: End date for benchmark data
            
        Returns:
            DataFrame with columns ['Date', 'Asset_Class', 'Weight', 'Return']
        """
        # Generate monthly dates
        dates = self._generate_monthly_dates(start_date, end_date)
        
        benchmark_data = []
        
        # Get benchmark allocation
        if 'strategic_benchmark' in benchmark_config:
            strategic_config = benchmark_config['strategic_benchmark']
            # Use 'weights' instead of 'allocation' based on actual config structure
            allocation = strategic_config.get('weights', strategic_config.get('allocation', {}))
            # Default expected returns if not provided
            expected_returns = strategic_config.get('expected_returns', {})
        else:
            raise ValueError("No strategic_benchmark found in benchmark config")
        
        if not allocation:
            raise ValueError("No allocation weights found in benchmark config")
        
        for snapshot_date in dates:
            for asset_class, weight in allocation.items():
                # Calculate monthly return (convert annual to monthly)
                # Use default expected returns if not provided
                annual_return = expected_returns.get(asset_class, 0.08 if 'Equity' in asset_class else 0.04)
                monthly_return = (1 + annual_return) ** (1/12) - 1
                
                benchmark_data.append({
                    'Date': snapshot_date,
                    'Asset_Class': asset_class,
                    'Weight': weight,
                    'Return': monthly_return
                })
        
        return pd.DataFrame(benchmark_data)
    
    def _aggregate_by_asset_class(self, holdings_snapshot: pd.DataFrame, total_value: float) -> Dict:
        """Aggregate holdings by asset class and calculate weights"""
        asset_class_data = {}
        
        for _, holding in holdings_snapshot.iterrows():
            # Get asset class mapping
            asset_class = self._map_to_asset_class(holding)
            
            # Get market value
            if 'Market_Value_CNY' in holding:
                market_value = holding['Market_Value_CNY']
            else:
                value_cols = [col for col in holding.index 
                            if 'value' in str(col).lower() or 'market' in str(col).lower()]
                if value_cols:
                    market_value = holding[value_cols[0]]
                else:
                    continue
            
            if pd.isna(market_value) or market_value <= 0:
                continue
            
            # Aggregate by asset class
            if asset_class not in asset_class_data:
                asset_class_data[asset_class] = {'value': 0.0, 'weight': 0.0}
            
            asset_class_data[asset_class]['value'] += market_value
        
        # Calculate weights
        for asset_class in asset_class_data:
            asset_class_data[asset_class]['weight'] = (
                asset_class_data[asset_class]['value'] / total_value
            )
        
        return asset_class_data
    
    def _map_to_asset_class(self, holding: pd.Series) -> str:
        """Map individual holding to asset class"""
        if self.taxonomy_manager is not None:
            try:
                # Use taxonomy manager if available
                if 'Asset_Name' in holding:
                    asset_name = holding['Asset_Name']
                elif 'Name' in holding:
                    asset_name = holding['Name']
                else:
                    asset_name = str(holding.get('Symbol', 'Unknown'))
                
                # Get mapping from taxonomy manager
                mapping = self.taxonomy_manager.map_asset_to_categories(asset_name)
                return mapping.get('top_level', 'Other')
                
            except Exception as e:
                print(f"Error mapping asset to class: {e}")
        
        # Fallback: simple heuristic mapping
        if 'Asset_Name' in holding:
            asset_name = str(holding['Asset_Name']).upper()
        elif 'Name' in holding:
            asset_name = str(holding['Name']).upper()
        else:
            return 'Other'
        
        # Simple classification rules
        if any(keyword in asset_name for keyword in ['股票', 'STOCK', 'EQUITY']):
            return 'Equity'
        elif any(keyword in asset_name for keyword in ['债券', 'BOND', 'FIXED']):
            return 'Fixed_Income'
        elif any(keyword in asset_name for keyword in ['现金', 'CASH', 'MONEY']):
            return 'Cash'
        elif any(keyword in asset_name for keyword in ['基金', 'FUND']):
            return 'Mutual_Funds'
        else:
            return 'Other'
    
    def _add_returns_data(
        self,
        asset_class_data: Dict,
        returns_data: pd.DataFrame,
        snapshot_date: pd.Timestamp
    ) -> Dict:
        """Add return data to asset class data"""
        if returns_data is None or returns_data.empty:
            return asset_class_data
        
        try:
            # Find the closest date in returns data
            if isinstance(returns_data.index, pd.DatetimeIndex):
                available_dates = returns_data.index
            else:
                available_dates = pd.to_datetime(returns_data['Date']) if 'Date' in returns_data.columns else None
            
            if available_dates is not None:
                closest_date = available_dates[available_dates <= snapshot_date].max()
                
                if pd.notna(closest_date):
                    if isinstance(returns_data.index, pd.DatetimeIndex):
                        returns_row = returns_data.loc[closest_date]
                    else:
                        returns_row = returns_data[returns_data['Date'] == closest_date].iloc[0]
                    
                    # Add returns to asset class data
                    for asset_class in asset_class_data:
                        if asset_class in returns_row:
                            asset_class_data[asset_class]['return'] = returns_row[asset_class]
                        else:
                            asset_class_data[asset_class]['return'] = 0.0
                    
        except Exception as e:
            print(f"Error adding returns data: {e}")
            # Set default returns
            for asset_class in asset_class_data:
                asset_class_data[asset_class]['return'] = 0.0
        
        return asset_class_data
    
    def _generate_monthly_dates(self, start_date: date, end_date: date) -> List[date]:
        """Generate list of monthly dates between start and end"""
        dates = []
        current_date = start_date
        
        while current_date <= end_date:
            dates.append(current_date)
            current_date = current_date + relativedelta(months=1)
        
        return dates
    
    def validate_attribution_data(
        self,
        portfolio_data: pd.DataFrame,
        benchmark_data: pd.DataFrame
    ) -> Dict[str, any]:
        """
        Validate that portfolio and benchmark data are suitable for attribution analysis
        
        Returns:
            Dictionary with validation results
        """
        validation = {
            'is_valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Check required columns
        required_cols = ['Date', 'Asset_Class', 'Weight', 'Return']
        
        for col in required_cols:
            if col not in portfolio_data.columns:
                validation['errors'].append(f"Missing column '{col}' in portfolio data")
                validation['is_valid'] = False
            if col not in benchmark_data.columns:
                validation['errors'].append(f"Missing column '{col}' in benchmark data")
                validation['is_valid'] = False
        
        if not validation['is_valid']:
            return validation
        
        # Check date alignment
        portfolio_dates = set(portfolio_data['Date'].unique())
        benchmark_dates = set(benchmark_data['Date'].unique())
        
        if not portfolio_dates.intersection(benchmark_dates):
            validation['errors'].append("No overlapping dates between portfolio and benchmark data")
            validation['is_valid'] = False
        
        missing_portfolio_dates = benchmark_dates - portfolio_dates
        missing_benchmark_dates = portfolio_dates - benchmark_dates
        
        if missing_portfolio_dates:
            validation['warnings'].append(f"Missing portfolio data for dates: {sorted(missing_portfolio_dates)[:5]}")
        if missing_benchmark_dates:
            validation['warnings'].append(f"Missing benchmark data for dates: {sorted(missing_benchmark_dates)[:5]}")
        
        # Check weight normalization
        for analysis_date in portfolio_dates:
            portfolio_weights = portfolio_data[portfolio_data['Date'] == analysis_date]['Weight'].sum()
            if abs(portfolio_weights - 1.0) > 0.05:  # 5% tolerance
                validation['warnings'].append(f"Portfolio weights for {analysis_date} sum to {portfolio_weights:.3f}")
        
        for analysis_date in benchmark_dates:
            benchmark_weights = benchmark_data[benchmark_data['Date'] == analysis_date]['Weight'].sum()
            if abs(benchmark_weights - 1.0) > 0.05:  # 5% tolerance
                validation['warnings'].append(f"Benchmark weights for {analysis_date} sum to {benchmark_weights:.3f}")
        
        return validation
