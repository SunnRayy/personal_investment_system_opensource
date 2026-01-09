# portfolio_lib/data_integration.py
"""
Module for integrating data_manager with portfolio_lib components.
Acts as a central integration point for data flow within the system.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional, List
import os
import sys
from datetime import datetime

# Import data_manager
from src.data_manager.manager import DataManager

# Import portfolio_lib components
from .core.asset_mapper import (
    initialize_mapper_taxonomy, 
    extract_and_map_holdings_from_df
)
from .core.transaction_analyzer import calculate_returns_from_transactions
from .core.mpt import AssetAllocationModel

# Use these to maintain backward compatibility during transition
from .data_loader.data_manager_adapter import (
    load_data_from_data_manager,
    compatibility_conversion
)


class PortfolioAnalysisManager:
    """
    Manages the integration between the data_manager and portfolio_lib modules.
    Handles data flow and orchestrates the analysis process.
    """
    
    def __init__(self, config_path: str = 'config/settings.yaml', taxonomy_path: str = 'config/asset_taxonomy.yaml'):
        """
        Initializes the integration manager.
        
        Args:
            config_path: Path to the configuration file.
            taxonomy_path: Path to the asset taxonomy file.
        """
        self.config_path = config_path
        self.taxonomy_path = taxonomy_path
        self.data_manager = None
        self.settings = None
        self.taxonomy = None
        
        # Data containers
        self.data_dict = {}
        self.balance_sheet_df = None
        self.monthly_df = None
        self.holdings_df = None
        self.transactions_df = None
        self.historical_holdings_df = None  # NEW: Add historical holdings container
        
        # Analysis results
        self.holdings_mapping = None
        self.returns_df = None
        self.returns_quality = None
        self.mpt_model = None
        
        # Initialize components
        self._load_configuration()
        self._initialize_data_manager()
    
    def _load_configuration(self):
        """Loads configuration and taxonomy settings."""
        try:
            # Import config loader from portfolio_lib
            from .config_loader import load_settings_config, load_asset_taxonomy_config
            
            # Load settings
            self.settings = load_settings_config(self.config_path)
            print(f"Configuration loaded successfully from {self.config_path}")
            
            # Load taxonomy
            self.taxonomy = load_asset_taxonomy_config(self.taxonomy_path)
            print(f"Asset taxonomy loaded successfully from {self.taxonomy_path}")
            
            # Initialize the asset mapper with the taxonomy
            if self.taxonomy:
                initialize_mapper_taxonomy(self.taxonomy)
            else:
                print("Taxonomy is None, skipping mapper initialization.") # Or handle error
            
        except Exception as e:
            print(f"Error loading configuration: {e}")
            import traceback
            print(traceback.format_exc())
    
    def _initialize_data_manager(self):
        """Initializes the data_manager and loads the data."""
        try:
            print(f"Initializing DataManager...")
            self.data_manager = DataManager(config_path=self.config_path)
            print(f"DataManager initialized")
            
            # Load data
            self._load_data()
            
        except Exception as e:
            print(f"Error initializing DataManager: {e}")
            import traceback
            print(traceback.format_exc())
    
    def _load_data(self):
        """Loads data from the DataManager."""
        try:
            print(f"Loading data from DataManager...")
            
            # Get data from DataManager
            self.balance_sheet_df = self.data_manager.get_balance_sheet()
            self.monthly_df = self.data_manager.get_monthly_income_expense()
            self.holdings_df = self.data_manager.get_holdings()
            self.transactions_df = self.data_manager.get_transactions()
            
            # NEW: Also get historical holdings for time series analysis
            self.historical_holdings_df = self.data_manager.get_historical_holdings()
            
            # Store in a dictionary for easier access
            self.data_dict = {
                'balance_sheet_df': self.balance_sheet_df,
                'monthly_df': self.monthly_df,
                'holdings_df': self.holdings_df,
                'transactions_df': self.transactions_df,
                'historical_holdings_df': self.historical_holdings_df
            }
            
            # Log loaded data info
            if self.balance_sheet_df is not None:
                print(f"Balance Sheet loaded: {self.balance_sheet_df.shape[0]} rows, {self.balance_sheet_df.shape[1]} columns")
            
            if self.monthly_df is not None:
                print(f"Monthly Income/Expense loaded: {self.monthly_df.shape[0]} rows, {self.monthly_df.shape[1]} columns")
            
            if self.holdings_df is not None:
                print(f"Holdings loaded: {self.holdings_df.shape[0]} rows, {self.holdings_df.shape[1]} columns")
            
            if self.transactions_df is not None:
                print(f"Transactions loaded: {self.transactions_df.shape[0]} rows, {self.transactions_df.shape[1]} columns")
                
            # NEW: Log historical holdings info
            if self.historical_holdings_df is not None and not self.historical_holdings_df.empty:
                if isinstance(self.historical_holdings_df.index, pd.MultiIndex):
                    snapshot_dates = self.historical_holdings_df.index.get_level_values('Snapshot_Date').unique()
                    print(f"Historical Holdings loaded: {len(self.historical_holdings_df)} records across {len(snapshot_dates)} snapshots")
                    print(f"Date range: {snapshot_dates.min().date()} to {snapshot_dates.max().date()}")
                else:
                    print(f"Historical Holdings loaded: {self.historical_holdings_df.shape[0]} rows, {self.historical_holdings_df.shape[1]} columns")
            else:
                print("No historical holdings data available")
            
        except Exception as e:
            print(f"Error loading data: {e}")
            import traceback
            print(traceback.format_exc())
    
    def analyze_portfolio(self, debug: bool = False):
        """
        Performs the complete portfolio analysis workflow.
        
        Args:
            debug: Whether to print detailed debugging information.
            
        Returns:
            A dictionary containing analysis results.
        """
        results = {}
        
        # 1. Map holdings to asset classes
        print("\nSTEP 1: Mapping holdings to asset classes...")
        self.holdings_mapping = self._map_holdings(debug)
        results['holdings_mapping'] = self.holdings_mapping
        
        # 2. Calculate historical returns
        print("\nSTEP 2: Calculating historical returns...")
        self.returns_df, self.returns_quality = self._calculate_returns(debug)
        results['returns_df'] = self.returns_df
        results['returns_quality'] = self.returns_quality
        
        # 3. Run MPT analysis
        print("\nSTEP 3: Running MPT analysis...")
        results['mpt_results'] = self._run_mpt_analysis(debug)
        
        # NEW: Include historical holdings data in results
        results['historical_holdings_df'] = self.historical_holdings_df
        
        return results
    
    def _map_holdings(self, debug: bool = False):
        """
        Maps holdings to asset classes.
        
        Args:
            debug: Whether to print detailed debugging information.
            
        Returns:
            Mapping results.
        """
        if self.holdings_df is not None and not self.holdings_df.empty:
            print("Using holdings_df from DataManager for asset mapping...")
            return extract_and_map_holdings_from_df(self.holdings_df, debug=debug)
        elif self.balance_sheet_df is not None and not self.balance_sheet_df.empty:
            print("Falling back to balance_sheet_df for asset mapping...")
            from .core.asset_mapper import extract_and_map_holdings
            return extract_and_map_holdings(self.balance_sheet_df, debug=debug)
        else:
            print("Error: No holdings or balance sheet data available for mapping")
            return {'top_level': {}, 'sub_level': {}, 'mapping_details': {}}
    
    def _calculate_returns(self, debug: bool = False):
        """
        Calculates historical returns using the best available data source.
        
        Priority order:
        1. Transaction-based returns (if sufficient holdings snapshots available)
        2. Balance sheet-based returns (fallback for top-level asset class returns)
        
        Args:
            debug: Whether to print detailed debugging information.
            
        Returns:
            A tuple containing (returns DataFrame, data quality assessment).
        """
        print("\nCalculating Historical Returns from Transactions...")
        
        # First, try transaction-based calculation if we have sufficient data
        # NEW: Check historical holdings first, then current holdings
        holdings_to_use = None
        snapshot_count = 0
        
        if (hasattr(self, 'historical_holdings_df') and 
            self.historical_holdings_df is not None and 
            not self.historical_holdings_df.empty):
            holdings_to_use = self.historical_holdings_df
            if isinstance(self.historical_holdings_df.index, pd.MultiIndex):
                snapshot_dates = self.historical_holdings_df.index.get_level_values('Snapshot_Date').unique()
                snapshot_count = len(snapshot_dates)
                if debug:
                    print(f"Found {snapshot_count} historical snapshots from {snapshot_dates.min().date()} to {snapshot_dates.max().date()}")
        elif (self.holdings_df is not None and not self.holdings_df.empty):
            holdings_to_use = self.holdings_df
            if isinstance(self.holdings_df.index, pd.MultiIndex):
                snapshot_dates = self.holdings_df.index.get_level_values('Snapshot_Date').unique()
                snapshot_count = len(snapshot_dates)
                if debug:
                    print(f"Using current holdings with {snapshot_count} snapshots")
        
        # Import here so it's available for all fallback paths
        from .core.historical import extract_historical_returns_with_assessment
        
        if (self.transactions_df is not None and not self.transactions_df.empty and 
            holdings_to_use is not None and snapshot_count >= 2):
            
            if debug:
                print(f"Using transaction-based returns with {snapshot_count} holdings snapshots...")
            
            transaction_returns, trans_quality = calculate_returns_from_transactions(
                self.transactions_df, 
                holdings_to_use,
                debug=debug
            )
            
            # Check if we actually got valid returns
            if transaction_returns is not None and not transaction_returns.empty and transaction_returns.shape[1] > 0:
                 if debug:
                     print(f"Successfully calculated returns for {transaction_returns.shape[1]} assets using transactions.")
                 final_returns = transaction_returns
                 final_quality = trans_quality
            else:
                 if debug:
                     print("Transaction-based calculation yielded empty results. Falling back to balance sheet...")
                 # Fallback logic
                 final_returns, final_quality = extract_historical_returns_with_assessment(
                    self.balance_sheet_df, self.monthly_df, self.settings
                 )
        else:
            if debug:
                print(f"Insufficient holdings snapshots ({snapshot_count}) for transaction-based returns.")
                print("Falling back to balance sheet-based returns...")
            
            # Fallback logic
            final_returns, final_quality = extract_historical_returns_with_assessment(
                self.balance_sheet_df, self.monthly_df, self.settings
            )

        # Post-process final_returns: Clean inf/nan and Map columns to English
        # Apply this to WHATEVER source we used (Transactions or Balance Sheet)
        if final_returns is not None and not final_returns.empty:
            # 1. Clean Data
            final_returns = final_returns.replace([np.inf, -np.inf], 0.0).fillna(0.0)
            
            # 2. Map Columns (Taxonomy/Chinese -> Benchmark/English)
            column_mapping = {
                '股票': 'Global_Equity',
                '固定收益': 'Global_Bonds',
                '房地产': 'Real_Estate',
                '商品': 'Commodities',
                '现金': 'Cash',
                '另类投资': 'Commodities', # Map Alternative to Commodities or keep separate depending on benchmark
                '保险': 'Global_Bonds',
                '其他': 'Cash'
            }
            
            new_columns = {}
            for col in final_returns.columns:
                clean_col = str(col).strip()
                new_columns[col] = column_mapping.get(clean_col, clean_col)
                
            final_returns = final_returns.rename(columns=new_columns)
            
            if debug:
                print(f"Mapped return columns: {new_columns}")
                
        return final_returns, final_quality
    
    def _run_mpt_analysis(self, debug: bool = False):
        """
        Runs the MPT analysis.
        
        Args:
            debug: Whether to print detailed debugging information.
            
        Returns:
            MPT analysis results.
        """
        mpt_results = {
            'success': False,
            'message': '',
            'model': None,
            'allocation': None,
            'frontier': None
        }
        
        # Check if we have returns data
        if self.returns_df is None or self.returns_df.empty:
            mpt_results['message'] = "No returns data available for MPT analysis"
            return mpt_results
        
        # Check data quality
        use_historical = self.returns_quality.get('sufficient_for_mpt', False)
        
        if not use_historical:
            # Generate default returns if historical data is insufficient
            from .core.historical import generate_default_returns_data
            print("Insufficient historical return data quality, using simulated returns...")
            default_returns_df = generate_default_returns_data(self.settings)
            input_returns = default_returns_df
            data_source = "Default (Simulated)"
        else:
            print("Using historical return data for MPT analysis...")
            input_returns = self.returns_df
            data_source = "Historical"
        
        try:
            # Clean returns data
            input_returns_cleaned = input_returns.ffill().dropna(how='any')
            
            # Check if cleaned data is sufficient
            min_rows_for_cov = len(input_returns.columns) + 1
            if input_returns_cleaned.empty or input_returns_cleaned.isnull().values.any() or len(input_returns_cleaned) < min_rows_for_cov:
                mpt_results['message'] = f"Insufficient clean return data: {input_returns_cleaned.shape}"
                return mpt_results
            
            # Create MPT model
            print(f"Creating MPT model with {data_source} returns data...")
            risk_free_rate = self.settings.get('mpt_params', {}).get('risk_free_rate', 0.02)
            annualization_factor = self.settings.get('mpt_params', {}).get('annualization_factor', 12)
            std_dev_threshold = self.settings.get('mpt_params', {}).get('std_dev_threshold', 1e-8)
            
            self.mpt_model = AssetAllocationModel(
                returns_data=input_returns_cleaned,
                risk_free_rate=risk_free_rate,
                annualization_factor=annualization_factor,
                std_dev_threshold=std_dev_threshold
            )
            
            # Run optimizations
            if self.mpt_model and self.mpt_model.num_assets > 0:
                mpt_results['model'] = self.mpt_model
                mpt_results['success'] = True
                mpt_results['message'] = f"MPT analysis completed successfully with {data_source} returns data"
                
                # Max Sharpe portfolio
                max_sharpe_portfolio = self.mpt_model.optimize_portfolio(objective='sharpe')
                
                # Min Volatility portfolio
                min_vol_portfolio = self.mpt_model.optimize_portfolio(objective='min_volatility')
                
                # Calculate efficient frontier
                efficient_frontier = self.mpt_model.calculate_efficient_frontier()
                
                # Generate recommendation based on risk preference
                risk_preference = self.settings.get('analysis_params', {}).get('risk_preference', '均衡型')
                recommendation = self.mpt_model.recommend_allocation(risk_preference=risk_preference)
                
                # Store results
                mpt_results['allocation'] = {
                    'max_sharpe': max_sharpe_portfolio,
                    'min_volatility': min_vol_portfolio,
                    'recommendation': recommendation
                }
                
                mpt_results['frontier'] = efficient_frontier
                
                if debug:
                    print(f"\nMPT Analysis Results:")
                    print(f"  Max Sharpe Ratio: {max_sharpe_portfolio.get('sharpe', 'N/A'):.2f}")
                    print(f"  Min Volatility: {min_vol_portfolio.get('volatility', 'N/A'):.2%}")
                    if recommendation:
                        print(f"  Recommended allocation based on {risk_preference} risk preference:")
                        weights = recommendation.get('allocation_float', {})
                        for asset, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
                            if weight > 0.01:  # Show assets with > 1% allocation
                                print(f"    {asset}: {weight:.2%}")
            else:
                mpt_results['message'] = f"MPT model initialization failed or no assets remained after filtering"
                
        except Exception as e:
            mpt_results['message'] = f"Error in MPT analysis: {str(e)}"
            print(f"Error in MPT analysis: {e}")
            import traceback
            print(traceback.format_exc())
        
        return mpt_results
    
    def get_financial_analysis_data(self):
        """
        Interface for receiving future data from the Financial Analysis Module.
        
        Returns:
            The current data dictionary.
        """
        return self.data_dict
    
    def set_future_cash_flow_forecast(self, forecast_data: pd.DataFrame):
        """
        Sets future cash flow forecast data from the Financial Analysis Module.
        
        Args:
            forecast_data: DataFrame containing cash flow forecast data.
        """
        self.data_dict['future_cash_flow_forecast'] = forecast_data
        print(f"Future cash flow forecast data set: {forecast_data.shape[0]} rows, {forecast_data.shape[1]} columns")


# Function to provide backward compatibility with the old approach
def load_and_analyze_portfolio(
    config_path: str = '../config/settings.yaml', 
    taxonomy_path: str = '../config/asset_taxonomy.yaml',
    debug: bool = False
):
    """
    Loads data using DataManager and performs portfolio analysis.
    Provides backward compatibility with the existing workflow.
    
    Args:
        config_path: Path to the configuration file.
        taxonomy_path: Path to the asset taxonomy file.
        debug: Whether to print detailed debugging information.
        
    Returns:
        A dictionary containing analysis results.
    """
    # Create the integration manager
    manager = PortfolioAnalysisManager(config_path, taxonomy_path)
    
    # Run the analysis
    results = manager.analyze_portfolio(debug=debug)
    
    # Return the model for backward compatibility
    return manager, results
