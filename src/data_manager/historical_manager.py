# Phase 3 Enhanced Data Manager - Historical Data Extension
# src/data_manager/historical_manager.py

"""
Enhanced Historical Data Management for Personal Investment System
Extends the base DataManager with advanced historical data capabilities.

Phase 3 Features:
- Multi-timeframe data support (daily, weekly, monthly, quarterly)
- External data source integration (Schwab, market data APIs)
- Enhanced cost basis tracking with multiple accounting methods
- Performance attribution infrastructure
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import os
import logging

# Import base data manager
from .manager import DataManager

# Import external data connectors (to be implemented)
# from .connectors import SchwabConnector, MarketDataConnector

logger = logging.getLogger(__name__)


class HistoricalDataManager(DataManager):
    """
    Enhanced DataManager with advanced historical data capabilities.
    Extends the base DataManager with Phase 3 features.
    """
    
    def __init__(self, config_path: str = 'config/settings.yaml'):
        """
        Initialize the Enhanced Historical Data Manager.
        
        Args:
            config_path: Path to the main settings YAML file
        """
        # Initialize base DataManager
        super().__init__(config_path)
        
        # Phase 3 specific initialization
        self.historical_storage_path = self._get_historical_storage_path()
        self.cost_basis_method = self.settings.get('cost_basis', {}).get('method', 'FIFO')
        self.market_data_enabled = self.settings.get('market_data', {}).get('enabled', False)
        
        # Initialize historical data structures
        self.historical_prices: Dict[str, pd.DataFrame] = {}
        self.cost_basis_lots: Dict[str, List[Dict]] = {}
        self.performance_attribution: Dict[str, pd.DataFrame] = {}
        
        # Initialize external data connectors
        self._init_external_connectors()
        
        print(f"Enhanced Historical Data Manager initialized with cost basis method: {self.cost_basis_method}")
    
    def _get_historical_storage_path(self) -> str:
        """Get the path for historical data storage."""
        base_path = self.settings.get('historical_data', {}).get('storage_path', 'data/historical')
        return os.path.abspath(base_path)
    
    def _init_external_connectors(self):
        """Initialize external data source connectors."""
        self.schwab_enabled = self.settings.get('external_data', {}).get('schwab', {}).get('enabled', False)
        self.market_data_provider = self.settings.get('external_data', {}).get('market_data', {}).get('provider', 'yahoo')
        
        # Initialize connectors when implemented
        # if self.schwab_enabled:
        #     self.schwab_connector = SchwabConnector(self.settings['external_data']['schwab'])
        # 
        # if self.market_data_enabled:
        #     self.market_data_connector = MarketDataConnector(
        #         provider=self.market_data_provider,
        #         config=self.settings['external_data']['market_data']
        #     )
    
    # === Multi-timeframe Historical Data Support ===
    
    def get_historical_holdings_multiframe(self, 
                                          start_date: Optional[pd.Timestamp] = None,
                                          end_date: Optional[pd.Timestamp] = None,
                                          frequency: str = 'monthly',
                                          fill_method: str = 'forward') -> Optional[pd.DataFrame]:
        """
        Get historical holdings with enhanced multi-timeframe support.
        
        Args:
            start_date: Start date for filtering
            end_date: End date for filtering  
            frequency: 'daily', 'weekly', 'monthly', 'quarterly'
            fill_method: 'forward', 'backward', 'interpolate', 'none'
            
        Returns:
            Enhanced historical holdings DataFrame with interpolated data
        """
        logger.info(f"Getting multi-timeframe data: {frequency} frequency, {fill_method} fill method")
        
        # Get base historical data
        base_historical = self.get_historical_holdings(start_date, end_date, frequency)
        
        if base_historical is None:
            logger.warning("No base historical data available")
            return None
        
        # Remove duplicates BEFORE any processing
        if base_historical.index.duplicated().any():
            duplicate_count = base_historical.index.duplicated().sum()
            logger.warning(f"Removing {duplicate_count} duplicate index entries")
            base_historical = base_historical[~base_historical.index.duplicated(keep='last')]
        
        # Validate data quality
        validation_results = self._validate_historical_data(base_historical)
        
        if not validation_results['valid']:
            logger.error(f"Data validation failed: {validation_results['errors']}")
            return None
        
        if validation_results['warnings']:
            for warning in validation_results['warnings']:
                logger.warning(f"Data quality warning: {warning}")
        
        # Apply data filling based on method
        if fill_method != 'none':
            logger.info(f"Applying {fill_method} gap filling for {frequency} frequency")
            print(f"🔧 DEBUG: About to call _fill_historical_gaps with fill_method={fill_method}")
            base_historical = self._fill_historical_gaps(base_historical, frequency, fill_method)
        
        # Add enhanced metadata
        logger.info("Adding enhanced metadata columns")
        base_historical = self._add_historical_metadata(base_historical)
        
        logger.info(f"Multi-timeframe data processing complete. Final shape: {base_historical.shape}")
        return base_historical
    
    def _fill_historical_gaps(self, df: pd.DataFrame, frequency: str, method: str) -> pd.DataFrame:
        """Fill gaps in historical data using specified method."""
        if df is None or len(df) == 0:
            return df
        
        logger.info(f"Starting gap filling: method={method}, frequency={frequency}")
        logger.info(f"Input data shape: {df.shape}, duplicates: {df.index.duplicated().sum()}")
        
        # CRITICAL: Remove duplicates at the very start
        if df.index.duplicated().any():
            duplicate_count = df.index.duplicated().sum()
            logger.warning(f"Removing {duplicate_count} duplicate index entries before gap filling")
            df = df[~df.index.duplicated(keep='last')]
            logger.info(f"After duplicate removal shape: {df.shape}")
        
        # Validate minimum data requirements
        unique_dates = df.index.get_level_values(0).unique()
        if len(unique_dates) < 2:
            logger.warning(f"Insufficient dates ({len(unique_dates)}) for gap filling. Returning original data.")
            return df
        
        # Check for sufficient date span
        date_span_days = (unique_dates.max() - unique_dates.min()).days
        min_span_required = {'daily': 7, 'weekly': 21, 'monthly': 60, 'quarterly': 180}
        
        if date_span_days < min_span_required.get(frequency, 30):
            logger.warning(f"Date span ({date_span_days} days) insufficient for {frequency} frequency. Returning original data.")
            return df
        
        # Create complete date range based on frequency
        date_range = self._create_date_range(df, frequency)
        
        if len(date_range) <= len(unique_dates):
            logger.info(f"No gaps to fill for {frequency} frequency. Returning original data.")
            return df
        
        try:
            # Create new MultiIndex with complete date range
            all_assets = df.index.get_level_values(1).unique()
            new_index = pd.MultiIndex.from_product(
                [date_range, all_assets], 
                names=['Snapshot_Date', 'Asset_ID']
            )
            
            logger.info(f"Before reindex: df.shape={df.shape}, df.index.duplicated().sum()={df.index.duplicated().sum()}")
            logger.info(f"New index length: {len(new_index)}, is_unique: {new_index.is_unique}")
            
            # Reindex with new complete index
            df_reindexed = df.reindex(new_index)
            
            # Apply filling method
            if method == 'forward':
                df_filled = df_reindexed.groupby(level=1).ffill()  # Forward fill by asset
            elif method == 'backward':
                df_filled = df_reindexed.groupby(level=1).bfill()  # Backward fill by asset
            elif method == 'interpolate':
                df_filled = df_reindexed.groupby(level=1).apply(
                    lambda x: x.interpolate(method='time') if len(x) > 1 else x
                ).droplevel(0)
            else:
                df_filled = df_reindexed
            
            # Remove rows that are still completely NaN
            df_result = df_filled.dropna(how='all')
            
            logger.info(f"Gap filling completed: {len(df)} -> {len(df_result)} records")
            return df_result
            
        except Exception as e:
            logger.error(f"Error during gap filling: {e}")
            logger.info("Returning original data without gap filling.")
            return df
    
    def _create_date_range(self, df: pd.DataFrame, frequency: str) -> pd.DatetimeIndex:
        """Create complete date range for gap filling."""
        dates = df.index.get_level_values(0).unique()
        start_date = dates.min()
        end_date = dates.max()
        
        freq_map = {
            'daily': 'D',
            'weekly': 'W',
            'monthly': 'ME',  # Changed from 'M' to 'ME' for month-end
            'quarterly': 'Q'
        }
        
        return pd.date_range(start=start_date, end=end_date, freq=freq_map.get(frequency, 'ME'))
    
    def _add_historical_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add metadata columns to historical holdings."""
        if df is None or len(df) == 0:
            return df
        
        try:
            # Ensure we have the required column
            if 'Market_Value_CNY' not in df.columns:
                logger.warning("Market_Value_CNY column not found. Skipping metadata enhancement.")
                return df
            
            # Add period-over-period change columns
            df_copy = df.copy()
            
            # Calculate changes by asset (level=1 in MultiIndex)
            df_copy['Market_Value_Change_Pct'] = df_copy.groupby(level=1)['Market_Value_CNY'].pct_change()
            df_copy['Market_Value_Change_Abs'] = df_copy.groupby(level=1)['Market_Value_CNY'].diff()
            
            # Add performance attribution fields (framework ready)
            df_copy['Attribution_Return'] = np.nan
            df_copy['Attribution_Weight'] = np.nan
            
            logger.info("Enhanced metadata columns added successfully.")
            return df_copy
            
        except Exception as e:
            logger.error(f"Error adding historical metadata: {e}")
            return df
    

    def _validate_historical_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Comprehensive validation of historical data quality.
        
        Returns:
            Dictionary with validation results and recommendations
        """
        if df is None or len(df) == 0:
            return {'valid': False, 'reason': 'No data provided'}
        
        validation_results = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'metrics': {}
        }
        
        try:
            # Check index structure
            if not isinstance(df.index, pd.MultiIndex):
                validation_results['errors'].append('Expected MultiIndex with (Snapshot_Date, Asset_ID)')
                validation_results['valid'] = False
                return validation_results
            
            # Check index levels
            if df.index.names != ['Snapshot_Date', 'Asset_ID']:
                validation_results['warnings'].append(f'Unexpected index names: {df.index.names}')
            
            # Check for duplicates
            duplicates = df.index.duplicated().sum()
            if duplicates > 0:
                validation_results['warnings'].append(f'{duplicates} duplicate index entries found')
                validation_results['metrics']['duplicates'] = duplicates
            
            # Check date span
            dates = df.index.get_level_values(0).unique()
            date_span_days = (dates.max() - dates.min()).days
            validation_results['metrics']['date_span_days'] = date_span_days
            validation_results['metrics']['unique_dates'] = len(dates)
            validation_results['metrics']['unique_assets'] = len(df.index.get_level_values(1).unique())
            
            # Check for unrealistic portfolio changes
            if 'Market_Value_CNY' in df.columns:
                portfolio_values = df.groupby(level=0)['Market_Value_CNY'].sum()
                if len(portfolio_values) > 1:
                    changes = portfolio_values.pct_change().dropna()
                    large_changes = changes[abs(changes) > 0.5]  # >50% change
                    
                    if len(large_changes) > 0:
                        validation_results['warnings'].append(
                            f'{len(large_changes)} periods with >50% portfolio value change detected'
                        )
                        validation_results['metrics']['large_changes'] = len(large_changes)
            
            # Check data completeness
            if 'Market_Value_CNY' in df.columns:
                completeness = df['Market_Value_CNY'].notna().sum() / len(df)
                validation_results['metrics']['completeness'] = completeness
                
                if completeness < 0.8:
                    validation_results['warnings'].append(
                        f'Low data completeness: {completeness:.1%}'
                    )
            
            logger.info(f"Data validation completed. Valid: {validation_results['valid']}")
            return validation_results
            
        except Exception as e:
            validation_results['errors'].append(f'Validation error: {str(e)}')
            validation_results['valid'] = False
            return validation_results

    # === Enhanced Cost Basis Tracking ===
    
    def calculate_cost_basis(self, 
                           asset_id: str, 
                           date: Optional[pd.Timestamp] = None,
                           method: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate cost basis for an asset using specified accounting method.
        
        Args:
            asset_id: Asset identifier
            date: Date for calculation (default: latest)
            method: 'FIFO', 'LIFO', 'AVERAGE', 'SPECIFIC' (default: from config)
            
        Returns:
            Dictionary with cost basis details
        """
        method = method or self.cost_basis_method
        date = date or pd.Timestamp.now()
        
        # Get transaction history for asset
        transactions = self._get_asset_transactions(asset_id, end_date=date)
        
        if transactions is None or len(transactions) == 0:
            return self._empty_cost_basis_result()
        
        # Calculate based on method
        if method == 'FIFO':
            return self._calculate_fifo_cost_basis(transactions, asset_id, date)
        elif method == 'LIFO':
            return self._calculate_lifo_cost_basis(transactions, asset_id, date)
        elif method == 'AVERAGE':
            return self._calculate_average_cost_basis(transactions, asset_id, date)
        elif method == 'SPECIFIC':
            return self._calculate_specific_cost_basis(transactions, asset_id, date)
        else:
            logger.warning(f"Unknown cost basis method: {method}, defaulting to FIFO")
            return self._calculate_fifo_cost_basis(transactions, asset_id, date)
    
    def _get_asset_transactions(self, asset_id: str, end_date: pd.Timestamp) -> Optional[pd.DataFrame]:
        """Get all transactions for a specific asset up to end_date."""
        all_transactions = self.get_transactions()
        
        if all_transactions is None:
            return None
        
        # Filter by asset and date
        asset_txns = all_transactions[
            (all_transactions['Asset_ID'] == asset_id) & 
            (all_transactions.index <= end_date)
        ].copy()
        
        return asset_txns.sort_index() if len(asset_txns) > 0 else None
    
    def _calculate_fifo_cost_basis(self, transactions: pd.DataFrame, asset_id: str, date: pd.Timestamp) -> Dict[str, Any]:
        """Calculate cost basis using First-In-First-Out method."""
        # Initialize tracking variables
        lots = []  # List of (date, quantity, unit_cost, remaining_quantity)
        total_quantity = 0
        total_cost = 0
        realized_gains = 0
        
        for idx, txn in transactions.iterrows():
            txn_type = txn.get('Transaction_Type', '')
            quantity = txn.get('Quantity', 0)
            unit_price = txn.get('Unit_Price', 0)
            
            if txn_type in ['Buy', 'Dividend_Reinvest']:
                # Add to lots
                lots.append({
                    'date': idx,
                    'quantity': quantity,
                    'unit_cost': unit_price,
                    'remaining_quantity': quantity
                })
                total_quantity += quantity
                total_cost += quantity * unit_price
                
            elif txn_type == 'Sell':
                # Remove from lots using FIFO
                remaining_to_sell = abs(quantity)
                
                while remaining_to_sell > 0 and lots:
                    lot = lots[0]
                    
                    if lot['remaining_quantity'] <= remaining_to_sell:
                        # Use entire lot
                        sold_quantity = lot['remaining_quantity']
                        proceeds = sold_quantity * unit_price
                        cost = sold_quantity * lot['unit_cost']
                        realized_gains += proceeds - cost
                        
                        remaining_to_sell -= sold_quantity
                        total_quantity -= sold_quantity
                        total_cost -= cost
                        lots.pop(0)
                    else:
                        # Partial lot usage
                        proceeds = remaining_to_sell * unit_price
                        cost = remaining_to_sell * lot['unit_cost']
                        realized_gains += proceeds - cost
                        
                        lot['remaining_quantity'] -= remaining_to_sell
                        total_quantity -= remaining_to_sell
                        total_cost -= cost
                        remaining_to_sell = 0
        
        # Calculate weighted average cost for remaining holdings
        avg_cost = total_cost / total_quantity if total_quantity > 0 else 0
        
        return {
            'asset_id': asset_id,
            'as_of_date': date,
            'method': 'FIFO',
            'total_quantity': total_quantity,
            'total_cost_basis': total_cost,
            'average_cost_per_share': avg_cost,
            'realized_gains_losses': realized_gains,
            'lots': lots,
            'calculation_date': pd.Timestamp.now()
        }
    
    def _calculate_lifo_cost_basis(self, transactions: pd.DataFrame, asset_id: str, date: pd.Timestamp) -> Dict[str, Any]:
        """Calculate cost basis using Last-In-First-Out method."""
        # Similar to FIFO but process lots in reverse order
        # Implementation would be similar but with lots.pop() instead of lots.pop(0)
        # For brevity, returning placeholder
        return self._empty_cost_basis_result(method='LIFO')
    
    def _calculate_average_cost_basis(self, transactions: pd.DataFrame, asset_id: str, date: pd.Timestamp) -> Dict[str, Any]:
        """Calculate cost basis using weighted average method."""
        # Implementation for average cost method
        # For brevity, returning placeholder
        return self._empty_cost_basis_result(method='AVERAGE')
    
    def _calculate_specific_cost_basis(self, transactions: pd.DataFrame, asset_id: str, date: pd.Timestamp) -> Dict[str, Any]:
        """Calculate cost basis using specific identification method."""
        # Implementation for specific lot identification
        # For brevity, returning placeholder
        return self._empty_cost_basis_result(method='SPECIFIC')
    
    def _empty_cost_basis_result(self, method: str = 'FIFO') -> Dict[str, Any]:
        """Return empty cost basis result structure."""
        return {
            'asset_id': '',
            'as_of_date': pd.Timestamp.now(),
            'method': method,
            'total_quantity': 0,
            'total_cost_basis': 0,
            'average_cost_per_share': 0,
            'realized_gains_losses': 0,
            'lots': [],
            'calculation_date': pd.Timestamp.now()
        }
    
    # === Performance Attribution System ===
    
    def calculate_performance_attribution(self, 
                                        start_date: Optional[pd.Timestamp] = None,
                                        end_date: Optional[pd.Timestamp] = None,
                                        attribution_method: str = 'sector') -> Dict[str, pd.DataFrame]:
        """
        Calculate performance attribution analysis.
        
        Args:
            start_date: Start date for attribution period
            end_date: End date for attribution period
            attribution_method: 'sector', 'asset_class', 'security'
            
        Returns:
            Dictionary of attribution DataFrames by method
        """
        # Get historical holdings and transactions for period
        holdings = self.get_historical_holdings_multiframe(start_date, end_date, 'monthly')
        
        if holdings is None:
            return {}
        
        attribution_results = {}
        
        if attribution_method in ['sector', 'all']:
            attribution_results['sector'] = self._calculate_sector_attribution(holdings, start_date, end_date)
        
        if attribution_method in ['asset_class', 'all']:
            attribution_results['asset_class'] = self._calculate_asset_class_attribution(holdings, start_date, end_date)
        
        if attribution_method in ['security', 'all']:
            attribution_results['security'] = self._calculate_security_attribution(holdings, start_date, end_date)
        
        return attribution_results
    
    def _calculate_sector_attribution(self, holdings: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
        """Calculate sector-level performance attribution."""
        # Placeholder implementation
        # Would calculate contribution by sector using holdings and returns
        return pd.DataFrame()
    
    def _calculate_asset_class_attribution(self, holdings: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
        """Calculate asset class-level performance attribution."""
        # Placeholder implementation
        return pd.DataFrame()
    
    def _calculate_security_attribution(self, holdings: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
        """Calculate security-level performance attribution."""
        # Placeholder implementation
        return pd.DataFrame()
    
    # === External Data Integration (Schwab, Market Data) ===
    
    def sync_schwab_data(self) -> bool:
        """
        Synchronize data from Schwab account.
        
        Returns:
            True if sync successful, False otherwise
        """
        if not self.schwab_enabled:
            logger.info("Schwab integration disabled in configuration")
            return False
        
        try:
            # Placeholder for Schwab API integration
            logger.info("Schwab data sync not yet implemented")
            return False
            
            # When implemented:
            # schwab_holdings = self.schwab_connector.get_account_holdings()
            # schwab_transactions = self.schwab_connector.get_account_transactions(start_date, end_date)
            # self._integrate_schwab_data(schwab_holdings, schwab_transactions)
            # return True
            
        except Exception as e:
            logger.error(f"Error syncing Schwab data: {e}")
            return False
    
    def update_market_prices(self, asset_ids: Optional[List[str]] = None) -> bool:
        """
        Update market prices for assets from external data source.
        
        Args:
            asset_ids: List of asset IDs to update (None for all)
            
        Returns:
            True if update successful, False otherwise
        """
        if not self.market_data_enabled:
            logger.info("Market data integration disabled in configuration")
            return False
        
        try:
            # Placeholder for market data API integration
            logger.info("Market data update not yet implemented")
            return False
            
            # When implemented:
            # if asset_ids is None:
            #     asset_ids = self._get_all_trackable_assets()
            # 
            # price_data = self.market_data_connector.get_current_prices(asset_ids)
            # self._update_asset_prices(price_data)
            # return True
            
        except Exception as e:
            logger.error(f"Error updating market prices: {e}")
            return False
    
    # === Enhanced Reporting and Analytics ===
    
    def generate_advanced_holdings_report(self, 
                                        as_of_date: Optional[pd.Timestamp] = None,
                                        include_attribution: bool = True,
                                        include_cost_basis: bool = True) -> Dict[str, Any]:
        """
        Generate comprehensive holdings report with advanced analytics.
        
        Args:
            as_of_date: Report date (default: latest)
            include_attribution: Include performance attribution analysis
            include_cost_basis: Include cost basis details
            
        Returns:
            Comprehensive report dictionary
        """
        as_of_date = as_of_date or pd.Timestamp.now()
        
        report = {
            'report_date': as_of_date,
            'generation_time': pd.Timestamp.now(),
            'holdings_summary': {},
            'performance_summary': {},
            'risk_metrics': {},
            'cost_basis_summary': {},
            'attribution_analysis': {}
        }
        
        # Get current holdings
        current_holdings = self.get_holdings(latest_only=True)
        if current_holdings is not None:
            report['holdings_summary'] = self._generate_holdings_summary(current_holdings, as_of_date)
        
        # Add cost basis analysis if requested
        if include_cost_basis and current_holdings is not None:
            report['cost_basis_summary'] = self._generate_cost_basis_summary(current_holdings, as_of_date)
        
        # Add performance attribution if requested
        if include_attribution:
            attribution_start = as_of_date - pd.DateOffset(months=12)  # 1-year attribution
            attribution_data = self.calculate_performance_attribution(attribution_start, as_of_date, 'all')
            report['attribution_analysis'] = attribution_data
        
        return report
    
    def _generate_holdings_summary(self, holdings: pd.DataFrame, as_of_date: pd.Timestamp) -> Dict[str, Any]:
        """Generate summary statistics for holdings."""
        if holdings is None or len(holdings) == 0:
            return {
                'total_assets': 0,
                'total_market_value': 0,
                'largest_holding': None,
                'concentration_ratio': 0
            }
        
        total_market_value = holdings['Market_Value_CNY'].sum()
        max_value_idx = holdings['Market_Value_CNY'].idxmax()
        largest_holding = max_value_idx[1] if isinstance(max_value_idx, tuple) else str(max_value_idx)  # Extract Asset_ID from MultiIndex
        
        return {
            'total_assets': len(holdings),
            'total_market_value': total_market_value,
            'largest_holding': largest_holding,
            'concentration_ratio': holdings['Market_Value_CNY'].max() / total_market_value if total_market_value > 0 else 0
        }
    
    def _generate_cost_basis_summary(self, holdings: pd.DataFrame, as_of_date: pd.Timestamp) -> Dict[str, Any]:
        """Generate cost basis summary for all holdings."""
        cost_basis_data = {}
        
        # Get Asset_IDs from the MultiIndex
        asset_ids = holdings.index.get_level_values('Asset_ID').unique()
        
        for asset_id in asset_ids:
            cost_basis = self.calculate_cost_basis(asset_id, as_of_date)
            cost_basis_data[asset_id] = cost_basis
        
        return cost_basis_data


def create_enhanced_data_manager(config_path: str = 'config/settings.yaml') -> HistoricalDataManager:
    """
    Factory function to create an enhanced data manager instance.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configured HistoricalDataManager instance
    """
    return HistoricalDataManager(config_path)
