import pandas as pd
import os
import logging
from typing import Dict, List, Any
# Ensure this import path is correct relative to your project structure
try:
    from src.data_manager.historical_manager import HistoricalDataManager as DataManager
except ImportError:
    print("Could not import HistoricalDataManager with absolute path, trying relative...")
    try:
        from src.data_manager.historical_manager import HistoricalDataManager as DataManager
    except ImportError:
        print("ERROR: Failed to import HistoricalDataManager. Check project structure and PYTHONPATH.")
        # Define a dummy class to avoid errors later if import fails
        class DataManager:
             def __init__(self, *args, **kwargs): print("Dummy DataManager initialized (IMPORT FAILED)")
             def get_balance_sheet(self): return pd.DataFrame()
             def get_monthly_income_expense(self): return pd.DataFrame()
             def get_holdings(self): return pd.DataFrame()
             def get_transactions(self): return pd.DataFrame()
             def get_historical_holdings(self): return pd.DataFrame()

# Import the analysis modules
from . import balance_sheet # Use relative import
from . import cash_flow     # <-- Add import for cash_flow
from . import investment    # <-- Add import for investment module
from . import visualizations # Add import for visualizations module
from . import historical_performance # Add import for historical performance module

# Configure logging for this module
# Basic configuration is fine here, but usually done at application entry point
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FinancialAnalyzer:
    """
    Main class for performing financial analysis.
    Initializes DataManager and loads required dataframes.
    Orchestrates different analysis components.
    """

    def __init__(self, config_dir: str = 'config'):
        """
        Initializes the FinancialAnalyzer.

        Args:
            config_dir (str): Path to the configuration directory relative
                              to the project root (e.g., 'config').
        """
        # Store the original config_dir path, might be relative
        self.relative_config_dir = config_dir
        # Resolve to absolute path for internal use, assuming execution from project root if relative
        self.absolute_config_dir = os.path.abspath(config_dir)
        self.settings_path = os.path.join(self.absolute_config_dir, 'settings.yaml')
        logger.info(f"FinancialAnalyzer initialized. Absolute config dir: {self.absolute_config_dir}")
        logger.info(f"Expecting settings at: {self.settings_path}")

        self.data_manager = None
        self.balance_sheet_df = pd.DataFrame()
        self.monthly_df = pd.DataFrame()
        self.holdings_df = pd.DataFrame()
        self.transactions_df = pd.DataFrame()

        self._load_data()

    def _load_data(self):
        """Loads data using the DataManager."""
        logger.info(f"Attempting to load data using settings file: {self.settings_path}")

        if not os.path.exists(self.settings_path):
            logger.error(f"Settings file not found at '{self.settings_path}'. Make sure the path is correct relative to your execution context or provide an absolute path.")
            raise FileNotFoundError(f"Settings file not found: {self.settings_path}")

        try:
            # Use 'config_path' as the argument name, matching DataManager.__init__
            # Pass the absolute path to settings.yaml
            self.data_manager = DataManager(config_path=self.settings_path)

            logger.info("Loading Balance Sheet data...")
            self.balance_sheet_df = self.data_manager.get_balance_sheet()
            if self.balance_sheet_df is None: self.balance_sheet_df = pd.DataFrame() # Ensure it's a DF
            logger.info(f"Loaded Balance Sheet: {self.balance_sheet_df.shape}")

            logger.info("Loading Monthly Income/Expense data...")
            self.monthly_df = self.data_manager.get_monthly_income_expense()
            if self.monthly_df is None: self.monthly_df = pd.DataFrame()
            logger.info(f"Loaded Monthly Data: {self.monthly_df.shape}")

            logger.info("Loading Holdings data...")
            self.holdings_df = self.data_manager.get_holdings()
            if self.holdings_df is None: self.holdings_df = pd.DataFrame()
            logger.info(f"Loaded Holdings Data: {self.holdings_df.shape}")

            logger.info("Loading Transactions data...")
            self.transactions_df = self.data_manager.get_transactions()
            if self.transactions_df is None: self.transactions_df = pd.DataFrame()
            logger.info(f"Loaded Transactions Data: {self.transactions_df.shape}")

            logger.info("All data loaded successfully via DataManager.")

        except FileNotFoundError as e:
            logger.error(f"File not found during DataManager initialization or data loading. Check paths in '{self.settings_path}' and ensure data files exist. Error: {e}")
            raise
        except TypeError as e:
             logger.error(f"TypeError initializing DataManager. Potential mismatch in expected arguments for DataManager.__init__. Error: {e}", exc_info=True)
             raise
        except Exception as e:
            logger.error(f"Failed to initialize DataManager or load data: {e}", exc_info=True)
            raise

    def run_analysis(self):
        """
        Run all analysis functions and return a consolidated results dictionary.
        """
        logger.info("Starting full analysis...")
        results = {}
        
        try:
            # Run balance sheet analysis
            results['balance_sheet'] = self.analyze_balance_sheet(config_dir=self.absolute_config_dir)
            
            # Run cash flow analysis
            results['cash_flow'] = self.analyze_cash_flow()
            
            # Run investment analysis
            results['investment'] = self.analyze_investments(config_dir=self.absolute_config_dir)  # Pass the config_dir argument
            
            # Run historical performance analysis
            results['historical_performance'] = self.analyze_historical_performance(config_dir=self.absolute_config_dir)  # Pass the config_dir argument
            
            logger.info("Full analysis completed successfully.")
            return results
        except Exception as e:
            logger.error(f"Error during full analysis: {e}")
            logger.exception("Full analysis failed.")
            return results  # Return whatever was completed

    # --- Update this method to accept and pass config_dir ---
    def analyze_balance_sheet(self, config_dir=None):
        """Performs balance sheet analysis."""
        logger.info("Running Balance Sheet Analysis...")
        # Use the instance's config_dir if none provided
        if config_dir is None:
            config_dir = self.absolute_config_dir
            
        if self.balance_sheet_df.empty:
            logger.warning("Balance sheet data is empty, skipping analysis.")
            return {"status": "skipped", "reason": "No data"}

        try:
            # Call the function from balance_sheet.py, passing the DataFrame and config_dir
            results = balance_sheet.run_balance_sheet_analysis(
                balance_sheet_df=self.balance_sheet_df,
                config_dir=config_dir # Pass the config directory path
            )
            logger.info("Balance sheet analysis successfully completed.")
            return results
        except Exception as e:
            logger.error(f"Error during balance sheet analysis: {e}", exc_info=True)
            return {"status": "error", "reason": str(e)}

    # --- Update this method to call the actual cash flow analysis ---
    def analyze_cash_flow(self):
        """Performs income and expense analysis."""
        logger.info("Running Cash Flow Analysis...") # Removed (Placeholder)
        if self.monthly_df.empty:
            logger.warning("Monthly income/expense data is empty, skipping analysis.")
            return {"status": "skipped", "reason": "No data"}

        try:
            # Call the function from cash_flow.py
            results = cash_flow.run_cash_flow_analysis(self.monthly_df)
            logger.info("Cash flow analysis successfully completed.")
            return results # Return the actual results
        except Exception as e:
            logger.error(f"Error during cash flow analysis: {e}", exc_info=True)
            return {"status": "error", "reason": str(e)} # Return error status

    # --- analyze_investments method (UPDATED) ---
    def get_realized_unrealized_gains(self) -> Dict[str, float]:
        """
        Get portfolio-wide realized and unrealized gains analysis.
        
        Returns:
            Dictionary with realized_gains, unrealized_gains, and total_gains
        """
        logger.info("Calculating realized and unrealized gains...")
        
        try:
            # Import the cost basis module functions
            from .cost_basis import get_gains_analysis
            
            # Use current holdings for market values
            current_holdings = self.holdings_df if not self.holdings_df.empty else None
            
            # Calculate portfolio-wide gains with sub-class breakdown
            gains_analysis = get_gains_analysis(
                transactions_df=self.transactions_df,
                current_holdings_df=current_holdings,
                include_subclass_breakdown=True
            )
            
            logger.info(f"Gains analysis completed: Realized=¥{gains_analysis['realized_gains']:,.2f}, "
                       f"Unrealized=¥{gains_analysis['unrealized_gains']:,.2f}, "
                       f"Total=¥{gains_analysis['total_gains']:,.2f}")
            
            return gains_analysis
            
        except Exception as e:
            logger.error(f"Error calculating realized/unrealized gains: {e}", exc_info=True)
            return {
                "realized_gains": 0.0,
                "unrealized_gains": 0.0,
                "total_gains": 0.0,
                "status": "error",
                "reason": str(e)
            }

    def get_lifetime_asset_performance(self) -> List[Dict[str, Any]]:
        """
        Get comprehensive performance data for all assets ever held in the portfolio.
        Includes both currently held assets and previously sold assets.
        
        Returns:
            List of dictionaries with detailed performance metrics for each asset
        """
        logger.info("Calculating lifetime asset performance...")
        
        try:
            # Import the cost basis module functions
            from .cost_basis import get_lifetime_asset_performance
            
            # Use current holdings for market values and asset info
            current_holdings = self.holdings_df if not self.holdings_df.empty else None
            
            # Get lifetime performance data for all assets
            lifetime_performance = get_lifetime_asset_performance(
                transactions_df=self.transactions_df,
                current_holdings_df=current_holdings
            )
            
            logger.info(f"Lifetime asset performance calculated for {len(lifetime_performance)} assets")
            
            return lifetime_performance
            
        except Exception as e:
            logger.error(f"Error calculating lifetime asset performance: {e}", exc_info=True)
            return []

    def analyze_investments(self, config_dir: str):
        """Performs investment portfolio analysis."""
        logger.info("Running Investment Analysis...")
        # Check for essential dataframes for this analysis
        if self.holdings_df.empty:
             logger.warning("Holdings data is empty, skipping investment analysis.")
             return {"status": "skipped", "reason": "No holdings data"}
        if self.transactions_df.empty:
             logger.warning("Transactions data is empty. XIRR calculations will not be available.")
             # Allow analysis to proceed, but XIRR results will be None/skipped

        try:
            # Call the main function from investment.py
            results = investment.run_investment_analysis(
                holdings_df=self.holdings_df,
                transactions_df=self.transactions_df, # Pass transactions even if empty
                balance_sheet_df=self.balance_sheet_df, # Pass balance sheet for Sharpe ratio fallback
                config_dir=config_dir # Pass config dir for centralized configuration system
            )
            logger.info("Investment analysis successfully completed.")
            return results
        except Exception as e:
            logger.error(f"Error during investment analysis: {e}", exc_info=True)
            return {"status": "error", "reason": str(e)}

    def get_dual_timeframe_metrics(self, lifetime_metrics: dict, config_dir: str = 'config') -> dict:
        """
        Calculate both lifetime and 12-month metrics for portfolio overview.
        
        Args:
            lifetime_metrics: Dict containing lifetime xirr, sharpe_ratio, twr
            config_dir: Configuration directory path
            
        Returns:
            Dict with 'lifetime' and '12month' keys containing respective metrics
        """
        logger.info("Calculating dual-timeframe metrics...")
        
        try:
            from .dual_timeframe_metrics import calculate_dual_timeframe_metrics
            
            # Extract lifetime metrics
            lifetime_xirr = lifetime_metrics.get('xirr', 0.0)
            lifetime_sharpe = lifetime_metrics.get('sharpe_ratio', 0.0)
            lifetime_twr = lifetime_metrics.get('twr', 0.0)
            
            # Calculate dual timeframe metrics
            dual_metrics = calculate_dual_timeframe_metrics(
                transactions_df=self.transactions_df,
                holdings_df=self.holdings_df,
                balance_sheet_df=self.balance_sheet_df,
                lifetime_xirr=lifetime_xirr,
                lifetime_sharpe=lifetime_sharpe,
                lifetime_twr=lifetime_twr,
                risk_free_rate=0.02,
                config_dir=config_dir
            )
            
            logger.info("✓ Dual-timeframe metrics calculated successfully")
            return dual_metrics
            
        except Exception as e:
            logger.error(f"Error calculating dual-timeframe metrics: {e}", exc_info=True)
            # Return lifetime metrics only as fallback
            return {
                'lifetime': {
                    'xirr': lifetime_metrics.get('xirr'),
                    'sharpe_ratio': lifetime_metrics.get('sharpe_ratio'),
                    'twr': lifetime_metrics.get('twr'),
                    'timeframe': 'Lifetime'
                },
                '12month': {
                    'xirr': None,
                    'sharpe_ratio': None,
                    'twr': None,
                    'timeframe': 'Trailing 12 Months (calculation failed)'
                }
            }

    # --- New method for historical performance analysis ---
    def analyze_historical_performance(self, config_dir: str = None):
        """Performs comprehensive historical performance analysis using multi-year data."""
        logger.info("Running Historical Performance Analysis...")
        
        # Use the instance's config_dir if none provided
        if config_dir is None:
            config_dir = self.absolute_config_dir
        
        # Get historical holdings data
        if not hasattr(self.data_manager, 'get_historical_holdings'):
            logger.warning("DataManager does not support historical holdings. Skipping historical analysis.")
            return {"status": "skipped", "reason": "Historical data not available"}
        
        try:
            # Load historical holdings data (use full historical range)
            historical_holdings = self.data_manager.get_historical_holdings()
            
            if historical_holdings is None or historical_holdings.empty:
                logger.warning("No historical holdings data available.")
                return {"status": "skipped", "reason": "No historical data"}
            
            logger.info(f"Loaded historical holdings: {len(historical_holdings.index.get_level_values(0).unique())} snapshots")
            
            # Initialize the historical performance analyzer
            analyzer = historical_performance.HistoricalPerformanceAnalyzer()
            
            # Run comprehensive historical analysis
            results = analyzer.calculate_historical_performance(
                historical_holdings=historical_holdings,
                balance_sheet_df=self.balance_sheet_df,
                monthly_df=self.monthly_df
            )
            
            logger.info("Historical performance analysis successfully completed.")
            return results
            
        except Exception as e:
            logger.error(f"Error during historical performance analysis: {e}", exc_info=True)
            return {"status": "error", "reason": str(e)}

    def plot_balance_sheet_trends(self):
        if self.results and 'balance_sheet' in self.results and 'trends' in self.results['balance_sheet']:
            trend_data = self.results['balance_sheet']['trends'].get('trend_data')
            if isinstance(trend_data, pd.DataFrame) and not trend_data.empty:
                return visualizations.plot_balance_sheet_trends(trend_data)
        logger.warning("Could not plot balance sheet trends due to missing data.")
        return None, None

    def plot_allocation(self):
         if self.results and 'balance_sheet' in self.results and 'allocation' in self.results['balance_sheet']:
             alloc_data = self.results['balance_sheet']['allocation']
             if alloc_data:
                  return visualizations.plot_asset_liability_allocation(alloc_data)
         logger.warning("Could not plot allocation due to missing data.")
         return None, None

    def show_all_balance_sheet_plots(self):
         """Generates and shows all balance sheet related plots."""
         logger.info("Generating all balance sheet plots...")
         fig_trend, ax_trend = self.plot_balance_sheet_trends()
         fig_alloc, axs_alloc = self.plot_allocation()

    # --- Other analysis methods remain placeholders for now ---
        
    def generate_recommendations(self):
        """Generates financial recommendations based on all analyses."""
        logger.info("Generating Recommendations (Placeholder)...")
        print("     (Recommendations Generation would run here)")
        return {"status": "placeholder"}

    def run_performance_reconciliation(self):
        """
        Calculate and return key metrics for cross-validation of performance calculations.
        
        This function validates that Total Portfolio Gain = Realized Gains + Unrealized Gains
        and provides detailed breakdown for reconciliation purposes.
        
        Returns:
            Dict containing:
            - total_portfolio_gain: Total gain/loss across all holdings
            - realized_gains: Sum of all realized gains from sold positions
            - unrealized_gains: Sum of all unrealized gains from current holdings
            - reconciliation_difference: Difference between total and sum of components
            - detailed_breakdown: Asset-level breakdown for investigation
        """
        logger.info("Running Performance Reconciliation Analysis...")
        
        try:
            # Import required modules
            from . import cost_basis
            
            # Initialize results dictionary
            reconciliation = {
                'total_portfolio_gain': 0.0,
                'realized_gains': 0.0,
                'unrealized_gains': 0.0,
                'reconciliation_difference': 0.0,
                'detailed_breakdown': {},
                'status': 'success',
                'reason': None
            }
            
            # Get gains analysis from cost_basis module
            try:
                gains_result = cost_basis.get_gains_analysis(
                    self.transactions_df,
                    self.holdings_df
                )
                
                if gains_result:
                    # Extract key metrics from the direct result
                    reconciliation['realized_gains'] = gains_result.get('realized_gains', 0.0)
                    reconciliation['unrealized_gains'] = gains_result.get('unrealized_gains', 0.0)
                    reconciliation['total_portfolio_gain'] = gains_result.get('total_gains', 0.0)
                    
                    # Calculate reconciliation difference (should be close to zero)
                    expected_total = reconciliation['realized_gains'] + reconciliation['unrealized_gains']
                    reconciliation['reconciliation_difference'] = (
                        reconciliation['total_portfolio_gain'] - expected_total
                    )
                    
                    # Note: Detailed breakdown by asset is not available in current cost_basis implementation
                    # This would require enhancing cost_basis.get_gains_analysis to return asset-level details
                    reconciliation['detailed_breakdown'] = {}
                    
                    logger.info("Performance Reconciliation completed successfully:")
                    logger.info(f"  Total Portfolio Gain: ¥{reconciliation['total_portfolio_gain']:,.2f}")
                    logger.info(f"  Realized Gains: ¥{reconciliation['realized_gains']:,.2f}")
                    logger.info(f"  Unrealized Gains: ¥{reconciliation['unrealized_gains']:,.2f}")
                    logger.info(f"  Reconciliation Difference: ¥{reconciliation['reconciliation_difference']:,.2f}")
                    
                    # Check if reconciliation is within acceptable tolerance (0.1% of total)
                    tolerance = abs(reconciliation['total_portfolio_gain']) * 0.001
                    if abs(reconciliation['reconciliation_difference']) <= tolerance:
                        reconciliation['reconciliation_status'] = 'PASS'
                        logger.info("✅ Reconciliation PASSED - differences within tolerance")
                    else:
                        reconciliation['reconciliation_status'] = 'WARN'
                        logger.warning(f"⚠️  Reconciliation WARNING - difference exceeds tolerance: {tolerance:.2f}")
                        
                else:
                    reconciliation['status'] = 'error'
                    reconciliation['reason'] = 'No gains analysis results'
                    logger.error("No gains analysis results from cost_basis module")
                    return reconciliation
                    
            except Exception as gains_error:
                reconciliation['status'] = 'error'
                reconciliation['reason'] = f'Error in gains analysis: {gains_error}'
                logger.error(f"Error running gains analysis: {gains_error}")
                
            # Add additional validation metrics
            try:
                # Calculate total current portfolio value
                if not self.holdings_df.empty and 'Market_Value_CNY' in self.holdings_df.columns:
                    total_current_value = self.holdings_df['Market_Value_CNY'].sum()
                    reconciliation['total_current_portfolio_value'] = total_current_value
                    
                    # Calculate total invested (from transactions)
                    if not self.transactions_df.empty and 'Amount_Net' in self.transactions_df.columns:
                        investment_types = ['Buy', 'Sell', 'Dividend', 'Dividend_Cash', 'Interest']
                        investment_txns = self.transactions_df[
                            self.transactions_df['Transaction_Type'].isin(investment_types)
                        ]
                        total_net_invested = -investment_txns[investment_txns['Amount_Net'] < 0]['Amount_Net'].sum()
                        reconciliation['total_net_invested'] = total_net_invested
                        
                        # Alternative calculation of total gain: Current Value - Net Invested
                        alternative_total_gain = total_current_value - total_net_invested
                        reconciliation['alternative_total_gain'] = alternative_total_gain
                        
                        # Compare with our calculated total gain
                        alternative_difference = reconciliation['total_portfolio_gain'] - alternative_total_gain
                        reconciliation['alternative_calculation_difference'] = alternative_difference
                        
                        logger.info("Alternative calculation validation:")
                        logger.info(f"  Current Portfolio Value: ¥{total_current_value:,.2f}")
                        logger.info(f"  Total Net Invested: ¥{total_net_invested:,.2f}")
                        logger.info(f"  Alternative Total Gain: ¥{alternative_total_gain:,.2f}")
                        logger.info(f"  Difference from main calculation: ¥{alternative_difference:,.2f}")
                        
            except Exception as validation_error:
                logger.warning(f"Error in additional validation metrics: {validation_error}")
                
            return reconciliation
            
        except Exception as e:
            logger.error(f"Performance Reconciliation failed: {e}")
            return {
                'total_portfolio_gain': 0.0,
                'realized_gains': 0.0,
                'unrealized_gains': 0.0,
                'reconciliation_difference': 0.0,
                'detailed_breakdown': {},
                'status': 'error',
                'reason': str(e)
            }

