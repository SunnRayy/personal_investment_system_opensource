"""
Cash Flow Forecasting Module using SARIMA Models

This module provides time-series forecasting capabilities for monthly income,
expenses, and net cash flow using Seasonal ARIMA (SARIMA) models.

Author: Personal Investment System
Date: August 17, 2025
Phase: 5.3 - Machine Learning & Predictive Analytics
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Any, List
import warnings
import logging

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.figure import Figure
except ImportError:
    plt = None
    mdates = None
    Figure = None

try:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from statsmodels.stats.diagnostic import acorr_ljungbox
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    STATSMODELS_AVAILABLE = True
except ImportError:
    SARIMAX = None
    acorr_ljungbox = None
    ExponentialSmoothing = None
    STATSMODELS_AVAILABLE = False

try:
    from pmdarima import auto_arima
    from pmdarima.arima import ARIMA
    PMDARIMA_AVAILABLE = True
except ImportError as e:
    auto_arima = None
    ARIMA = None
    PMDARIMA_AVAILABLE = False
    print(f"⚠️ pmdarima import failed: {e}")
except Exception as e:
    auto_arima = None
    ARIMA = None
    PMDARIMA_AVAILABLE = False
    print(f"⚠️ pmdarima compatibility issue: {e}")

try:
    from ..data_manager.manager import DataManager
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from data_manager.manager import DataManager  # noqa: F401
    
# For type hints when DataManager might not be available
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from data_manager.manager import DataManager as DataManagerType
else:
    DataManagerType = object


class CashFlowForecaster:
    """
    Cash Flow Forecasting class using SARIMA models for predictive analytics.
    
    This class provides methods to analyze historical cash flow data and generate
    forecasts for future monthly income, expenses, and net cash flow using
    automated SARIMA model selection.
    """
    
    def __init__(self, data_manager):
        """
        Initialize the CashFlowForecaster with a DataManager instance.
        
        Args:
            data_manager (DataManager): Instance of DataManager for data access
        """
        self.data_manager = data_manager
        self.logger = logging.getLogger(__name__)
        
        # Check package availability
        if auto_arima is None or ARIMA is None:
            self.pmdarima_available = False
        else:
            self.pmdarima_available = True
            
        # Provide user feedback about available functionality
        if self.pmdarima_available and STATSMODELS_AVAILABLE:
            self.logger.info("Both pmdarima and statsmodels available - full functionality enabled")
        elif self.pmdarima_available:
            self.logger.info("pmdarima available - using auto_arima for modeling")
        elif STATSMODELS_AVAILABLE:
            self.logger.info("statsmodels available - using grid search fallback for modeling")
            print("⚠️ pmdarima not available, using statsmodels fallback")
            print("💡 For faster performance, install: pip install 'pmdarima==1.8.5' --no-cache-dir")
        else:
            self.logger.warning("Neither pmdarima nor statsmodels available - forecasting disabled")
            print("❌ No SARIMA modeling packages available")
            print("💡 Install statsmodels: pip install statsmodels")
            print("💡 Or install pmdarima: pip install 'pmdarima==1.8.5' --no-cache-dir")
        
        # Storage for processed data and models
        self.monthly_data: Optional[pd.DataFrame] = None
        self.income_model = None  # Will store ARIMA model
        self.expense_model = None  # Will store ARIMA model
        self.investment_model = None  # Will store ARIMA model for investment flows
        self.net_cashflow_model = None  # Will store ARIMA model
        
        # Model parameters storage
        self.model_params: Dict[str, Dict] = {}
        
        # Model source tracking for smart dispatch
        self._models_source: Optional[str] = None
        self._pmdarima_models_fitted: bool = False
        self._statsmodels_models_fitted: bool = False
        
    def fetch_and_process_historical_data(self) -> pd.DataFrame:
        """
        Fetch and process monthly cash flow data for enhanced analysis.
        
        This method now prioritizes actual monthly cash flow data over transaction-level processing:
        1. Fetch monthly income/expense data from DataManager
        2. Apply data validation and cleaning
        3. Structure data for time series analysis with proper column mapping
        4. Fallback to transaction-level processing only if monthly data unavailable
        
        Returns:
            pd.DataFrame: Monthly aggregated cash flow data with columns:
                         - Date (datetime index)
                         - Total_Income
                         - Total_Expenses
                         - Total_Investment  
                         - Net_Cash_Flow (Income - Expenses - Investment)
                         
        Raises:
            ValueError: If insufficient data is available for analysis
        """
        try:
            # Primary method: Get pre-aggregated monthly cash flow data from DataManager
            self.logger.info("Fetching monthly cash flow data from DataManager...")
            monthly_cash_flow = self.data_manager.get_monthly_income_expense()
            
            if monthly_cash_flow is not None and not monthly_cash_flow.empty:
                self.logger.info(f"Found monthly cash flow data: {monthly_cash_flow.shape[0]} months available")
                
                # Process and standardize the monthly data
                monthly_data = self._process_monthly_cash_flow_data(monthly_cash_flow)
                
                # Validate data sufficiency for time series analysis
                if len(monthly_data) < 12:  # Minimum 12 months for seasonal analysis
                    self.logger.warning(
                        f"Only {len(monthly_data)} months of data available. "
                        "Minimum 12 months recommended for seasonal analysis."
                    )
                
                # Store processed data
                self.monthly_data = monthly_data
                
                self.logger.info(
                    f"Successfully processed {len(monthly_data)} months of cash flow data "
                    f"from {monthly_data.index.min()} to {monthly_data.index.max()}"
                )
                
                return monthly_data
            
            # Fallback method 1: Process transaction-level data
            self.logger.info("No monthly cash flow data available, attempting transaction-level processing...")
            transactions_df = self.data_manager.get_transactions()
            
            if transactions_df is not None and not transactions_df.empty:
                self.logger.info(f"Processing {len(transactions_df)} transactions for cash flow analysis...")
                
                # Apply transaction filtering and categorization
                filtered_transactions = self._apply_transaction_filters(transactions_df)
                categorized_transactions = self._categorize_transactions(filtered_transactions)
                
                # Aggregate to monthly cash flow data
                monthly_data = self._aggregate_transactions_to_monthly(categorized_transactions)
                
                # Store processed data
                self.monthly_data = monthly_data
                
                self.logger.info(
                    f"Successfully processed {len(monthly_data)} months from transaction data "
                    f"from {monthly_data.index.min()} to {monthly_data.index.max()}"
                )
                
                return monthly_data
            
            # Fallback method 2: Try to derive from historical holdings
            self.logger.info("No transaction data available, attempting fallback method using holdings...")
            monthly_data = self._get_monthly_summary_from_snapshots()
            
            if monthly_data is None or monthly_data.empty:
                raise ValueError("No cash flow data available from any DataManager source")
            
            # Store processed data
            self.monthly_data = monthly_data
            
            self.logger.info(
                f"Successfully processed {len(monthly_data)} months using holdings fallback method "
                f"from {monthly_data.index.min()} to {monthly_data.index.max()}"
            )
            
            return monthly_data
            
        except Exception as e:
            self.logger.error(f"Error fetching and processing historical data: {str(e)}")
            raise
    
    def _process_monthly_cash_flow_data(self, monthly_cash_flow: pd.DataFrame) -> pd.DataFrame:
        """
        Process and standardize monthly cash flow data from DataManager.
        
        Args:
            monthly_cash_flow (pd.DataFrame): Raw monthly cash flow data from DataManager
            
        Returns:
            pd.DataFrame: Standardized monthly cash flow data with required columns
        """
        try:
            # Create a copy to avoid modifying the original data
            processed_df = monthly_cash_flow.copy()
            
            # Ensure the index is datetime
            if not isinstance(processed_df.index, pd.DatetimeIndex):
                if 'Date' in processed_df.columns:
                    processed_df['Date'] = pd.to_datetime(processed_df['Date'])
                    processed_df = processed_df.set_index('Date')
                else:
                    processed_df.index = pd.to_datetime(processed_df.index)
            
            # Map columns to standard format - priority-based detection
            column_mapping = {}
            
            # Step 1: Look for exact calculated columns first (highest priority)
            # These are the validated, correctly calculated columns from DataManager
            if 'Total_Income_Calc_CNY' in processed_df.columns:
                column_mapping['Total_Income'] = 'Total_Income_Calc_CNY'
                self.logger.info("Found validated Total_Income_Calc_CNY column - using for income tracking")
            
            if 'Total_Expense_Calc_CNY' in processed_df.columns:
                column_mapping['Total_Expenses'] = 'Total_Expense_Calc_CNY'
                self.logger.info("Found validated Total_Expense_Calc_CNY column - using for expense tracking")
            
            if 'Total_Investment_Calc_CNY' in processed_df.columns:
                column_mapping['Total_Investment'] = 'Total_Investment_Calc_CNY'
                self.logger.info("Found validated Total_Investment_Calc_CNY column - using for investment tracking")
            
            # Step 2: Fallback to expense column detection if Total_Expense_Calc_CNY not found
            if 'Total_Expenses' not in column_mapping:
                expense_keywords = ['expense', 'cost', 'spending', 'expenditure']
                for col in processed_df.columns:
                    col_lower = str(col).lower()
                    if any(keyword in col_lower for keyword in expense_keywords):
                        # Prioritize total/sum columns, then any expense column
                        if ('total' in col_lower or 'sum' in col_lower) and 'Total_Expenses' not in column_mapping:
                            column_mapping['Total_Expenses'] = col
                        elif 'expense' in col_lower and 'Total_Expenses' not in column_mapping:
                            column_mapping['Total_Expenses'] = col
                        elif any(kw in col_lower for kw in expense_keywords) and 'Total_Expenses' not in column_mapping:
                            column_mapping['Total_Expenses'] = col
            
            # Step 3: Fallback to income column detection if Total_Income_Calc_CNY not found
            if 'Total_Income' not in column_mapping:
                income_keywords = ['income', 'revenue', 'salary', 'earning', 'inflow']
                exclude_from_income = ['investment', 'invest', 'saving', 'portfolio', 'allocation', 'contribution']
                
                for col in processed_df.columns:
                    col_lower = str(col).lower()
                    # Check if it's income-related but NOT investment-related
                    is_income = any(keyword in col_lower for keyword in income_keywords)
                    is_investment = any(keyword in col_lower for keyword in exclude_from_income)
                    
                    if is_income and not is_investment:
                        # Prioritize total/sum columns, then any pure income column
                        if ('total' in col_lower or 'sum' in col_lower) and 'Total_Income' not in column_mapping:
                            column_mapping['Total_Income'] = col
                        elif 'income' in col_lower and 'Total_Income' not in column_mapping:
                            column_mapping['Total_Income'] = col
                        elif 'Total_Income' not in column_mapping:
                            column_mapping['Total_Income'] = col
            
            # Step 4: Handle investment columns only if Total_Investment_Calc_CNY not found
            if 'Total_Investment' not in column_mapping:
                investment_keywords = ['investment', 'invest', 'saving', 'portfolio', 'allocation', 'contribution']
                investment_candidates = []
            
            # Step 4: Handle investment columns only if Total_Investment_Calc_CNY not found
            if 'Total_Investment' not in column_mapping:
                self.logger.info("Total_Investment_Calc_CNY not found, falling back to legacy investment detection")
                investment_keywords = ['investment', 'invest', 'saving', 'portfolio', 'allocation', 'contribution']
                investment_candidates = []
                
                # First pass: keyword-based detection (legacy logic for backward compatibility)
                for col in processed_df.columns:
                    col_lower = str(col).lower()
                    if any(keyword in col_lower for keyword in investment_keywords):
                        # Skip if already mapped to income or expenses
                        if col not in column_mapping.values():
                            investment_candidates.append((col, col_lower, 'keyword'))
                
                # Apply legacy selection logic if needed
                if investment_candidates:
                    self.logger.info(f"Found {len(investment_candidates)} legacy investment column candidates")
                    # Selection priority: keyword-based with 'investment' in name and high activity
                    for col, col_lower, method in investment_candidates:
                        if (method == 'keyword' and 'investment' in col_lower and 
                            (processed_df[col] != 0).sum() > len(processed_df) * 0.2):
                            column_mapping['Total_Investment'] = col
                            break
                    
                    # Fallback: choose first candidate with activity
                    if 'Total_Investment' not in column_mapping and investment_candidates:
                        column_mapping['Total_Investment'] = investment_candidates[0][0]
            
            # Create standardized DataFrame with required columns
            result_df = pd.DataFrame(index=processed_df.index)
            
            # Map existing columns or create zero-filled columns
            for target_col, source_col in column_mapping.items():
                if source_col in processed_df.columns:
                    result_df[target_col] = processed_df[source_col].fillna(0)
                    self.logger.info(f"Mapped {source_col} -> {target_col}")
            
            # Ensure all required columns exist
            required_columns = ['Total_Income', 'Total_Expenses', 'Total_Investment']
            for col in required_columns:
                if col not in result_df.columns:
                    result_df[col] = 0.0
                    self.logger.warning(f"Column {col} not found in data, filled with zeros")
            
            # Calculate Net Cash Flow: Income - Expenses - Investment
            # Note: Investment should be treated as an outflow (positive investment = money going out)
            result_df['Net_Cash_Flow'] = (
                result_df['Total_Income'] - 
                result_df['Total_Expenses'] - 
                result_df['Total_Investment']
            )
            
            # Remove rows where all values are zero
            result_df = result_df[(result_df != 0).any(axis=1)]
            
            # Sort by date
            result_df = result_df.sort_index()
            
            self.logger.info(f"Processed monthly cash flow data: {len(result_df)} months")
            self.logger.info(f"Column mapping applied: {column_mapping}")
            
            return result_df
            
        except Exception as e:
            self.logger.error(f"Error processing monthly cash flow data: {str(e)}")
            raise

    def _aggregate_to_monthly(self, cash_flow_data: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate cash flow data to monthly frequency.
        
        Args:
            cash_flow_data (pd.DataFrame): Raw cash flow data
            
        Returns:
            pd.DataFrame: Monthly aggregated data
        """
        try:
            # Ensure we have the required columns
            # Try different possible column names
            column_mapping = {}
            for col in cash_flow_data.columns:
                if 'date' in col.lower() or 'time' in col.lower():
                    column_mapping['Date'] = col
                elif 'income' in col.lower() or 'revenue' in col.lower():
                    column_mapping['Income'] = col
                elif 'expense' in col.lower() or 'cost' in col.lower() or 'spending' in col.lower():
                    column_mapping['Expenses'] = col
            
            # If direct cash flow data is not available, try to construct from other sources
            if len(column_mapping) < 3:
                # Try to get monthly summary data from DataManager
                monthly_summary = self._get_monthly_summary_from_snapshots()
                if monthly_summary is not None:
                    return monthly_summary
            
            # Rename columns to standard format
            df = cash_flow_data.copy()
            for standard_name, actual_name in column_mapping.items():
                if actual_name in df.columns:
                    df = df.rename(columns={actual_name: standard_name})
            
            # Convert Date column to datetime
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.set_index('Date')
            
            # Aggregate to monthly frequency
            monthly_agg = df.resample('ME').agg({
                'Income': 'sum',
                'Expenses': 'sum'
            })
            
            # Calculate net cash flow
            monthly_agg['Net_Cash_Flow'] = monthly_agg['Income'] - monthly_agg['Expenses']
            
            # Rename columns to match expected format
            monthly_agg = monthly_agg.rename(columns={
                'Income': 'Total_Income',
                'Expenses': 'Total_Expenses'
            })
            
            return monthly_agg.dropna()
            
        except Exception as e:
            self.logger.error(f"Error aggregating data to monthly frequency: {str(e)}")
            raise
    
    def _get_monthly_summary_from_snapshots(self) -> Optional[pd.DataFrame]:
        """
        Create monthly cash flow summary from historical snapshots if direct data unavailable.
        
        Returns:
            pd.DataFrame or None: Monthly cash flow data or None if unavailable
        """
        try:
            # Get historical holdings data
            historical_data = self.data_manager.get_historical_holdings()
            
            if historical_data is None or historical_data.empty:
                return None
            
            # Group by month and calculate cash flow proxies
            historical_data['Date'] = pd.to_datetime(historical_data['Date'])
            monthly_holdings = historical_data.groupby(historical_data['Date'].dt.to_period('M')).agg({
                'Market_Value_CNY': 'sum'
            }).reset_index()
            
            monthly_holdings['Date'] = monthly_holdings['Date'].dt.to_timestamp()
            monthly_holdings = monthly_holdings.set_index('Date')
            
            # Calculate month-over-month changes as proxy for cash flow
            monthly_holdings['Portfolio_Change'] = monthly_holdings['Market_Value_CNY'].diff()
            
            # Create synthetic income/expense estimates (this is a simplified approach)
            # In practice, you'd want actual cash flow data
            monthly_holdings['Total_Income'] = np.where(
                monthly_holdings['Portfolio_Change'] > 0, 
                monthly_holdings['Portfolio_Change'], 
                0
            )
            monthly_holdings['Total_Expenses'] = np.where(
                monthly_holdings['Portfolio_Change'] < 0, 
                -monthly_holdings['Portfolio_Change'], 
                0
            )
            monthly_holdings['Net_Cash_Flow'] = monthly_holdings['Portfolio_Change']
            
            return monthly_holdings[['Total_Income', 'Total_Expenses', 'Net_Cash_Flow']].dropna()
            
        except Exception as e:
            self.logger.warning(f"Could not create monthly summary from snapshots: {str(e)}")
            return None
    
    def _apply_transaction_filters(self, transactions_df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply filtering logic to exclude outlier transactions and specific categories.
        
        Args:
            transactions_df (pd.DataFrame): Raw transaction data
            
        Returns:
            pd.DataFrame: Filtered transaction data
        """
        try:
            filtered_df = transactions_df.copy()
            initial_count = len(filtered_df)
            
            # 1. Outlier Exclusion: Housing purchase in August 2020
            # Filter out large transactions in August 2020 (likely housing purchase)
            aug_2020_mask = (
                (filtered_df.index.year == 2020) & 
                (filtered_df.index.month == 8) &
                (abs(filtered_df['Amount_Net']) > 500000)  # Transactions above 500k CNY
            )
            outlier_count = aug_2020_mask.sum()
            if outlier_count > 0:
                self.logger.info(f"Excluding {outlier_count} large transactions from August 2020 (likely housing purchase)")
                filtered_df = filtered_df[~aug_2020_mask]
            
            # 2. Category Exclusion: Work Reimbursement transactions
            # Check multiple possible fields for reimbursement indicators
            reimbursement_indicators = ['work reimbursement', 'reimbursement', '报销', '工作报销']
            reimbursement_mask = pd.Series(False, index=filtered_df.index)
            
            for field in ['Asset_Name', 'Memo', 'Account']:
                if field in filtered_df.columns:
                    field_mask = filtered_df[field].astype(str).str.lower().str.contains(
                        '|'.join(reimbursement_indicators), na=False, regex=True
                    )
                    reimbursement_mask |= field_mask
            
            reimbursement_count = reimbursement_mask.sum()
            if reimbursement_count > 0:
                self.logger.info(f"Excluding {reimbursement_count} work reimbursement transactions")
                filtered_df = filtered_df[~reimbursement_mask]
            
            # 3. Additional filtering: Remove transactions with missing critical data
            before_cleanup = len(filtered_df)
            filtered_df = filtered_df.dropna(subset=['Amount_Net'])
            after_cleanup = len(filtered_df)
            
            if before_cleanup > after_cleanup:
                self.logger.info(f"Removed {before_cleanup - after_cleanup} transactions with missing Amount_Net")
            
            self.logger.info(
                f"Transaction filtering complete: {initial_count} → {len(filtered_df)} transactions "
                f"({initial_count - len(filtered_df)} filtered out)"
            )
            
            return filtered_df
            
        except Exception as e:
            self.logger.error(f"Error applying transaction filters: {str(e)}")
            raise
    
    def _categorize_transactions(self, transactions_df: pd.DataFrame) -> pd.DataFrame:
        """
        Categorize transactions into Income, Expenses, and Investment flows.
        
        Args:
            transactions_df (pd.DataFrame): Filtered transaction data
            
        Returns:
            pd.DataFrame: Transaction data with added Cash_Flow_Category column
        """
        try:
            categorized_df = transactions_df.copy()
            
            # Initialize category column
            categorized_df['Cash_Flow_Category'] = 'Other'
            
            # Income Categories
            income_types = ['Dividend', 'Interest', 'RSU_Vest']
            income_mask = categorized_df['Transaction_Type'].isin(income_types)
            
            # Also consider asset sales as potential income (depending on context)
            # For investment assets, sales are typically reinvestment, but for RSU it's income
            rsu_sales_mask = (
                (categorized_df['Transaction_Type'] == 'Sell') &
                (categorized_df['Asset_ID'].astype(str).str.contains('RSU', na=False))
            )
            
            categorized_df.loc[income_mask | rsu_sales_mask, 'Cash_Flow_Category'] = 'Income'
            
            # Expense Categories
            expense_types = ['Premium_Payment', 'Commission_Fee']
            expense_mask = categorized_df['Transaction_Type'].isin(expense_types)
            
            # Also consider transactions with negative amounts that aren't investments
            non_investment_negative_mask = (
                (categorized_df['Amount_Net'] < 0) &
                (~categorized_df['Transaction_Type'].isin(['Buy', 'Sell']))
            )
            
            categorized_df.loc[expense_mask | non_investment_negative_mask, 'Cash_Flow_Category'] = 'Expenses'
            
            # Investment Categories (Buy/Sell of investment assets)
            investment_types = ['Buy', 'Sell']
            investment_mask = categorized_df['Transaction_Type'].isin(investment_types)
            
            # Exclude RSU sales from investment category (already categorized as income)
            investment_mask = investment_mask & (~rsu_sales_mask)
            
            categorized_df.loc[investment_mask, 'Cash_Flow_Category'] = 'Investment'
            
            # Log categorization results
            category_counts = categorized_df['Cash_Flow_Category'].value_counts()
            self.logger.info(f"Transaction categorization: {category_counts.to_dict()}")
            
            return categorized_df
            
        except Exception as e:
            self.logger.error(f"Error categorizing transactions: {str(e)}")
            raise
    
    def _aggregate_transactions_to_monthly(self, transactions_df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate categorized transactions to monthly cash flow data.
        
        Args:
            transactions_df (pd.DataFrame): Categorized transaction data
            
        Returns:
            pd.DataFrame: Monthly aggregated cash flow data
        """
        try:
            # Ensure we have the required columns
            if 'Cash_Flow_Category' not in transactions_df.columns:
                raise ValueError("Transactions must be categorized before aggregation")
            
            # Group by month and category, sum the Amount_Net
            monthly_agg = transactions_df.groupby([
                transactions_df.index.to_period('M'),
                'Cash_Flow_Category'
            ])['Amount_Net'].sum().unstack(fill_value=0)
            
            # Convert period index back to datetime
            monthly_agg.index = monthly_agg.index.to_timestamp()
            
            # Ensure all required columns exist
            for col in ['Income', 'Expenses', 'Investment']:
                if col not in monthly_agg.columns:
                    monthly_agg[col] = 0.0
            
            # Calculate net cash flow: Income - Expenses - Investment
            # Note: Investment outflows (buys) are negative, inflows (sells) are positive
            # So we subtract investment to get the net cash impact
            monthly_agg['Net_Cash_Flow'] = (
                monthly_agg['Income'] - 
                abs(monthly_agg['Expenses']) -  # Ensure expenses are treated as outflows
                monthly_agg['Investment']  # Investment can be positive (sells) or negative (buys)
            )
            
            # Rename columns to match expected format
            result_df = pd.DataFrame({
                'Total_Income': monthly_agg['Income'],
                'Total_Expenses': abs(monthly_agg['Expenses']),  # Present expenses as positive values
                'Total_Investment': abs(monthly_agg['Investment']),  # Present investment flows as positive values
                'Net_Cash_Flow': monthly_agg['Net_Cash_Flow']
            }, index=monthly_agg.index)
            
            # Remove months with no data
            result_df = result_df[(result_df != 0).any(axis=1)]
            
            self.logger.info(
                f"Monthly aggregation complete: {len(result_df)} months from "
                f"{result_df.index.min()} to {result_df.index.max()}"
            )
            
            return result_df
            
        except Exception as e:
            self.logger.error(f"Error aggregating transactions to monthly data: {str(e)}")
            raise

    def _fit_statsmodels_sarima(self, series_data: pd.Series, seasonal_period: int = 12) -> Optional[Any]:
        """
        Fit the best SARIMA model using statsmodels with grid search parameter optimization.
        
        This method serves as a robust fallback when pmdarima is unavailable, implementing
        a systematic grid search to find optimal SARIMA parameters based on AIC.
        
        Args:
            series_data (pd.Series): Time series data to model
            seasonal_period (int): Seasonal period for SARIMA model (default: 12 for monthly data)
            
        Returns:
            SARIMAX: Best fitted statsmodels SARIMA model object, or None if fitting fails
        """
        if not STATSMODELS_AVAILABLE:
            self.logger.warning("statsmodels not available for SARIMA modeling")
            return None
            
        if series_data is None or len(series_data) < 4:
            self.logger.warning("Insufficient data for SARIMA modeling")
            return None
            
        # Clean the data
        series_clean = series_data.dropna()
        if len(series_clean) < 4:
            self.logger.warning("Insufficient clean data for SARIMA modeling")
            return None
        
        # Define parameter search grid
        # Keep ranges small but sensible for performance and stability
        p_values = [0, 1, 2]  # AR order
        d_values = [0, 1]     # Differencing order
        q_values = [0, 1, 2]  # MA order
        
        # Seasonal parameters - only use if sufficient data
        use_seasonal = len(series_clean) >= 2 * seasonal_period
        if use_seasonal:
            P_values = [0, 1, 2]  # Seasonal AR order
            D_values = [0, 1]     # Seasonal differencing order  
            Q_values = [0, 1, 2]  # Seasonal MA order
        else:
            P_values = [0]
            D_values = [0]
            Q_values = [0]
        
        best_aic = float('inf')
        best_model = None
        best_params = None
        
        self.logger.info(f"Starting SARIMA grid search for series with {len(series_clean)} observations")
        
        # Grid search over parameter combinations
        for p in p_values:
            for d in d_values:
                for q in q_values:
                    for P in P_values:
                        for D in D_values:
                            for Q in Q_values:
                                try:
                                    # Define SARIMA order
                                    order = (p, d, q)
                                    seasonal_order = (P, D, Q, seasonal_period) if use_seasonal else (0, 0, 0, 0)
                                    
                                    # Fit SARIMA model
                                    with warnings.catch_warnings():
                                        warnings.simplefilter("ignore")
                                        model = SARIMAX(
                                            series_clean,
                                            order=order,
                                            seasonal_order=seasonal_order,
                                            enforce_stationarity=False,
                                            enforce_invertibility=False
                                        )
                                        fitted_model = model.fit(disp=False, maxiter=100)
                                    
                                    # Check if this model is better
                                    if fitted_model.aic < best_aic:
                                        best_aic = fitted_model.aic
                                        best_model = fitted_model
                                        best_params = {
                                            'order': order,
                                            'seasonal_order': seasonal_order,
                                            'aic': fitted_model.aic,
                                            'bic': fitted_model.bic
                                        }
                                
                                except Exception as e:
                                    # Skip problematic parameter combinations
                                    continue
        
        if best_model is not None:
            self.logger.info(
                f"Best SARIMA model found: "
                f"order={best_params['order']}, "
                f"seasonal_order={best_params['seasonal_order']}, "
                f"AIC={best_params['aic']:.2f}"
            )
        else:
            self.logger.warning("No suitable SARIMA model could be fitted")
            
        return best_model

    def fit_sarima_models(self, seasonal_period: int = 12) -> Dict[str, Any]:
        """
        Find optimal SARIMA models for income, expenses, investment, and net cash flow.
        Uses pmdarima auto_arima when available, falls back to statsmodels grid search.
        
        Args:
            seasonal_period (int): Seasonal period for SARIMA model (default: 12 for monthly data)
            
        Returns:
            Dict[str, Any]: Dictionary containing fitted SARIMA models
            
        Raises:
            ValueError: If data has not been processed yet or no modeling packages available
        """
        if self.monthly_data is None:
            raise ValueError("Must call fetch_and_process_historical_data() first")
        
        # Check availability of modeling packages
        use_pmdarima = hasattr(self, 'pmdarima_available') and self.pmdarima_available
        use_statsmodels = STATSMODELS_AVAILABLE
        
        if not use_pmdarima and not use_statsmodels:
            raise ValueError("Neither pmdarima nor statsmodels available. Cannot fit SARIMA models.")
        
        # Store which modeling approach is being used
        self._models_source = None
        self._pmdarima_models_fitted = False
        self._statsmodels_models_fitted = False
        
        # Determine which method to use and fit models
        if use_pmdarima:
            self.logger.info("Using pmdarima auto_arima for SARIMA model fitting")
            try:
                models = self._fit_pmdarima_models(seasonal_period)
                self._models_source = 'pmdarima'
                self._pmdarima_models_fitted = True
                self.logger.info("Successfully fitted models using pmdarima")
                return models
            except Exception as e:
                self.logger.warning(f"pmdarima model fitting failed: {e}")
                if use_statsmodels:
                    self.logger.info("Falling back to statsmodels for model fitting")
                    models = self._fit_statsmodels_models(seasonal_period)
                    self._models_source = 'statsmodels'
                    self._statsmodels_models_fitted = True
                    self.logger.info("Successfully fitted models using statsmodels fallback")
                    return models
                else:
                    raise
        else:
            self.logger.info("Using statsmodels fallback for SARIMA model fitting")
            models = self._fit_statsmodels_models(seasonal_period)
            self._models_source = 'statsmodels'
            self._statsmodels_models_fitted = True
            self.logger.info("Successfully fitted models using statsmodels")
            return models
    
    def _fit_pmdarima_models(self, seasonal_period: int = 12) -> Dict[str, Any]:
        """
        Fit SARIMA models using pmdarima auto_arima (original implementation).
        
        Args:
            seasonal_period (int): Seasonal period for SARIMA model
            
        Returns:
            Dict[str, Any]: Dictionary containing fitted SARIMA models
        """
        models = {}
        
        # Suppress warnings for cleaner output
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            try:
                # Fit model for Total Income
                self.logger.info("Fitting SARIMA model for Total Income...")
                income_series = self.monthly_data['Total_Income'].dropna()
                
                if len(income_series) >= 2 * seasonal_period:  # Sufficient data for seasonal model
                    self.income_model = auto_arima(
                        income_series,
                        seasonal=True,
                        m=seasonal_period,
                        start_p=1, start_q=1,
                        max_p=2, max_q=2,  # Reduced from 3 to 2
                        start_P=0, start_Q=0,
                        max_P=1, max_Q=1,  # Reduced from 2 to 1
                        stepwise=True,
                        suppress_warnings=True,
                        error_action='ignore',
                        trace=False,
                        maxiter=50  # Limit iterations for speed
                    )
                else:
                    # Use non-seasonal model if insufficient data
                    self.income_model = auto_arima(
                        income_series,
                        seasonal=False,
                        start_p=1, start_q=1,
                        max_p=2, max_q=2,  # Reduced from 3 to 2
                        stepwise=True,
                        suppress_warnings=True,
                        error_action='ignore',
                        trace=False,
                        maxiter=50  # Limit iterations for speed
                    )
                
                models['income'] = self.income_model
                self.model_params['income'] = self.income_model.get_params()
                
                # Fit model for Total Expenses
                self.logger.info("Fitting SARIMA model for Total Expenses...")
                expense_series = self.monthly_data['Total_Expenses'].dropna()
                
                if len(expense_series) >= 2 * seasonal_period:
                    self.expense_model = auto_arima(
                        expense_series,
                        seasonal=True,
                        m=seasonal_period,
                        start_p=1, start_q=1,
                        max_p=2, max_q=2,  # Reduced from 3 to 2
                        start_P=0, start_Q=0,
                        max_P=1, max_Q=1,  # Reduced from 2 to 1
                        stepwise=True,
                        suppress_warnings=True,
                        error_action='ignore',
                        trace=False,
                        maxiter=50  # Limit iterations for speed
                    )
                else:
                    self.expense_model = auto_arima(
                        expense_series,
                        seasonal=False,
                        start_p=1, start_q=1,
                        max_p=2, max_q=2,  # Reduced from 3 to 2
                        stepwise=True,
                        suppress_warnings=True,
                        error_action='ignore',
                        trace=False
                    )
                
                models['expenses'] = self.expense_model
                self.model_params['expenses'] = self.expense_model.get_params()
                
                # Fit model for Total Investment (NEW)
                self.logger.info("Fitting SARIMA model for Total Investment...")
                investment_series = self.monthly_data['Total_Investment'].dropna()
                
                if len(investment_series) >= 2 * seasonal_period:
                    self.investment_model = auto_arima(
                        investment_series,
                        seasonal=True,
                        m=seasonal_period,
                        start_p=1, start_q=1,
                        max_p=2, max_q=2,  # Reduced from 3 to 2
                        start_P=0, start_Q=0,
                        max_P=1, max_Q=1,  # Reduced from 2 to 1
                        stepwise=True,
                        suppress_warnings=True,
                        error_action='ignore',
                        trace=False,
                        maxiter=50  # Limit iterations for speed
                    )
                else:
                    self.investment_model = auto_arima(
                        investment_series,
                        seasonal=False,
                        start_p=1, start_q=1,
                        max_p=2, max_q=2,  # Reduced from 3 to 2
                        stepwise=True,
                        suppress_warnings=True,
                        error_action='ignore',
                        trace=False,
                        maxiter=50  # Limit iterations for speed
                    )
                
                models['investment'] = self.investment_model
                self.model_params['investment'] = self.investment_model.get_params()
                
                # Fit model for Net Cash Flow
                self.logger.info("Fitting SARIMA model for Net Cash Flow...")
                netcf_series = self.monthly_data['Net_Cash_Flow'].dropna()
                
                if len(netcf_series) >= 2 * seasonal_period:
                    self.net_cashflow_model = auto_arima(
                        netcf_series,
                        seasonal=True,
                        m=seasonal_period,
                        start_p=0, start_q=0,
                        max_p=3, max_q=3,
                        start_P=0, start_Q=0,
                        max_P=2, max_Q=2,
                        stepwise=True,
                        suppress_warnings=True,
                        error_action='ignore',
                        trace=False,
                        maxiter=50  # Limit iterations for speed
                    )
                else:
                    self.net_cashflow_model = auto_arima(
                        netcf_series,
                        seasonal=False,
                        start_p=1, start_q=1,
                        max_p=2, max_q=2,  # Reduced from 3 to 2
                        stepwise=True,
                        suppress_warnings=True,
                        error_action='ignore',
                        trace=False,
                        maxiter=50  # Limit iterations for speed
                    )
                
                models['net_cash_flow'] = self.net_cashflow_model
                self.model_params['net_cash_flow'] = self.net_cashflow_model.get_params()
                
                self.logger.info("Successfully fitted all SARIMA models using pmdarima")
                
                return models
                
            except Exception as e:
                self.logger.error(f"Error fitting SARIMA models with pmdarima: {str(e)}")
                raise
                
    def _fit_statsmodels_models(self, seasonal_period: int = 12) -> Dict[str, Any]:
        """
        Fit SARIMA models using statsmodels with grid search (fallback implementation).
        
        Args:
            seasonal_period (int): Seasonal period for SARIMA model
            
        Returns:
            Dict[str, Any]: Dictionary containing fitted SARIMA models
        """
        models = {}
        
        try:
            # Fit model for Total Income
            self.logger.info("Fitting SARIMA model for Total Income using statsmodels...")
            income_series = self.monthly_data['Total_Income'].dropna()
            self.income_model = self._fit_statsmodels_sarima(income_series, seasonal_period)
            
            if self.income_model is not None:
                models['income'] = self.income_model
                self.model_params['income'] = {
                    'order': self.income_model.specification.get('order', 'unknown'),
                    'seasonal_order': self.income_model.specification.get('seasonal_order', 'unknown'),
                    'aic': self.income_model.aic,
                    'bic': self.income_model.bic
                }
            
            # Fit model for Total Expenses
            self.logger.info("Fitting SARIMA model for Total Expenses using statsmodels...")
            expense_series = self.monthly_data['Total_Expenses'].dropna()
            self.expense_model = self._fit_statsmodels_sarima(expense_series, seasonal_period)
            
            if self.expense_model is not None:
                models['expenses'] = self.expense_model
                self.model_params['expenses'] = {
                    'order': self.expense_model.specification.get('order', 'unknown'),
                    'seasonal_order': self.expense_model.specification.get('seasonal_order', 'unknown'),
                    'aic': self.expense_model.aic,
                    'bic': self.expense_model.bic
                }
            
            # Fit model for Total Investment
            self.logger.info("Fitting SARIMA model for Total Investment using statsmodels...")
            investment_series = self.monthly_data['Total_Investment'].dropna()
            self.investment_model = self._fit_statsmodels_sarima(investment_series, seasonal_period)
            
            if self.investment_model is not None:
                models['investment'] = self.investment_model
                self.model_params['investment'] = {
                    'order': self.investment_model.specification.get('order', 'unknown'),
                    'seasonal_order': self.investment_model.specification.get('seasonal_order', 'unknown'),
                    'aic': self.investment_model.aic,
                    'bic': self.investment_model.bic
                }
            
            # Fit model for Net Cash Flow
            self.logger.info("Fitting SARIMA model for Net Cash Flow using statsmodels...")
            netcf_series = self.monthly_data['Net_Cash_Flow'].dropna()
            self.net_cashflow_model = self._fit_statsmodels_sarima(netcf_series, seasonal_period)
            
            if self.net_cashflow_model is not None:
                models['net_cash_flow'] = self.net_cashflow_model
                self.model_params['net_cash_flow'] = {
                    'order': self.net_cashflow_model.specification.get('order', 'unknown'),
                    'seasonal_order': self.net_cashflow_model.specification.get('seasonal_order', 'unknown'),
                    'aic': self.net_cashflow_model.aic,
                    'bic': self.net_cashflow_model.bic
                }
            
            self.logger.info("Successfully fitted all SARIMA models using statsmodels")
            
            return models
            
        except Exception as e:
            self.logger.error(f"Error fitting SARIMA models with statsmodels: {str(e)}")
            raise
    
    def _fit_ets_models(self, seasonal_period: int = 12) -> Dict[str, Any]:
        """
        Fit Exponential Smoothing (ETS) models to the four financial series.
        
        This method implements Step 3.1 of Phase 5.3 Step 3 - Cash Flow Model Enhancement.
        Uses statsmodels ExponentialSmoothing for ETS model fitting.
        
        Args:
            seasonal_period (int): Seasonal period for ETS model (default: 12)
            
        Returns:
            Dict[str, Any]: Dictionary containing fitted ETS models
            
        Raises:
            ValueError: If required data is not available
            Exception: If model fitting fails
        """
        if not STATSMODELS_AVAILABLE:
            raise ImportError("statsmodels is required for ETS model fitting")
        
        try:
            # Try to use existing monthly data first (for testing and consistency)
            if hasattr(self, 'monthly_data') and self.monthly_data is not None:
                historical_data = self.monthly_data
                self.logger.info("Using existing monthly_data for ETS model fitting")
            else:
                # Get historical cash flow data from DataManager
                historical_data = self.data_manager.get_monthly_cashflow_analysis()
                self.logger.info("Fetching fresh data from DataManager for ETS model fitting")
            
            if historical_data is None or historical_data.empty:
                raise ValueError("No historical cash flow data available for ETS model fitting")
            
            # Map column names for flexibility (handle both formats)
            column_mapping = {
                'income': ['Total_Income_Calc_CNY', 'Total_Income'],
                'expense': ['Total_Expense_Calc_CNY', 'Total_Expenses'], 
                'investment': ['Total_Investment_Calc_CNY', 'Total_Investment'],
                'net_cash_flow': ['Net_Cash_Flow_Calc_CNY', 'Net_Cash_Flow']
            }
            
            # Find available columns
            available_columns = {}
            for series_name, possible_cols in column_mapping.items():
                for col in possible_cols:
                    if col in historical_data.columns:
                        available_columns[series_name] = col
                        break
                        
            if not available_columns:
                raise ValueError(f"No required columns found in data. Available: {list(historical_data.columns)}")
            
            models = {}
            self.ets_models = {}
            
            # Fit ETS models for each financial series
            for series_name, column_name in available_columns.items():
                series_data = historical_data[column_name].dropna()
                
                if len(series_data) < seasonal_period:
                    self.logger.warning(f"Insufficient data for {series_name} ETS model (need >= {seasonal_period}, got {len(series_data)})")
                    continue
                
                try:
                    # Fit ETS model with automatic model selection
                    # Use additive seasonal component for financial data
                    ets_model = ExponentialSmoothing(
                        series_data,
                        trend='add',
                        seasonal='add',
                        seasonal_periods=seasonal_period
                    ).fit(optimized=True)
                    
                    models[series_name] = ets_model
                    self.ets_models[series_name] = ets_model
                    
                    self.logger.info(f"Successfully fitted ETS model for {series_name}")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to fit ETS model for {series_name}: {str(e)}")
                    # Try without seasonal component as fallback
                    try:
                        ets_model = ExponentialSmoothing(
                            series_data,
                            trend='add'
                        ).fit(optimized=True)
                        
                        models[series_name] = ets_model
                        self.ets_models[series_name] = ets_model
                        
                        self.logger.info(f"Successfully fitted ETS model for {series_name} (no seasonal)")
                        
                    except Exception as e2:
                        self.logger.error(f"Failed to fit ETS model for {series_name} even without seasonal: {str(e2)}")
                        continue
            
            if not models:
                raise ValueError("Failed to fit any ETS models")
            
            self.logger.info(f"Successfully fitted ETS models for {len(models)} series")
            return models
            
        except Exception as e:
            self.logger.error(f"Error fitting ETS models: {str(e)}")
            raise
    
    def _forecast_ets_direct(self, periods: int = 12) -> pd.DataFrame:
        """
        Generate forecasts using fitted ETS models.
        
        This method implements Step 3.1 of Phase 5.3 Step 3 - Cash Flow Model Enhancement.
        Generates predictions and confidence intervals from fitted ETS models.
        
        Args:
            periods (int): Number of periods to forecast (default: 12)
            
        Returns:
            pd.DataFrame: Forecast results with predictions and confidence intervals
            
        Raises:
            ValueError: If ETS models are not fitted
            Exception: If forecasting fails
        """
        if not hasattr(self, 'ets_models') or not self.ets_models:
            raise ValueError("ETS models must be fitted first. Call _fit_ets_models() first.")
        
        try:
            forecasts = {}
            
            # Generate forecasts for each fitted ETS model
            for series_name, model in self.ets_models.items():
                try:
                    # Generate forecast with confidence intervals
                    forecast_result = model.forecast(periods)
                    
                    # For ExponentialSmoothing, we need to simulate prediction intervals
                    # since get_prediction method is not available
                    try:
                        # Try to get confidence intervals if available
                        residuals = model.resid
                        residual_std = np.std(residuals)
                        
                        # Create approximate 95% confidence intervals
                        # Using 1.96 * std for 95% CI
                        margin = 1.96 * residual_std
                        
                        forecasts[f'{series_name}_forecast'] = forecast_result
                        forecasts[f'{series_name}_lower'] = forecast_result - margin
                        forecasts[f'{series_name}_upper'] = forecast_result + margin
                        
                    except Exception:
                        # Fallback: use forecast values with simple margin
                        margin = np.abs(forecast_result) * 0.1  # 10% margin
                        forecasts[f'{series_name}_forecast'] = forecast_result
                        forecasts[f'{series_name}_lower'] = forecast_result - margin
                        forecasts[f'{series_name}_upper'] = forecast_result + margin
                    
                    self.logger.info(f"Generated ETS forecast for {series_name}")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to generate ETS forecast for {series_name}: {str(e)}")
                    # Create placeholder values
                    forecasts[f'{series_name}_forecast'] = np.zeros(periods)
                    forecasts[f'{series_name}_lower'] = np.zeros(periods)
                    forecasts[f'{series_name}_upper'] = np.zeros(periods)
            
            if not forecasts:
                raise ValueError("No ETS forecasts could be generated")
            
            # Create forecast DataFrame with date logic that works for both test and production
            if hasattr(self, 'monthly_data') and self.monthly_data is not None:
                last_date = self.monthly_data.index[-1]
            else:
                last_date = self.data_manager.get_monthly_cashflow_analysis().index[-1]
                
            forecast_dates = pd.date_range(
                start=last_date + pd.DateOffset(months=1),
                periods=periods,
                freq='ME'  # Use 'ME' instead of deprecated 'M'
            )
            
            forecast_df = pd.DataFrame(forecasts, index=forecast_dates)
            
            self.logger.info(f"Successfully generated ETS forecasts for {periods} periods")
            return forecast_df
            
        except Exception as e:
            self.logger.error(f"Error generating ETS forecasts: {str(e)}")
            raise
    
    def forecast(self, periods: int = 12, alpha: float = 0.10, confidence_level: str = '90') -> pd.DataFrame:
        """
        Smart dispatcher for forecast generation using fitted SARIMA models.
        
        This method automatically selects the appropriate forecasting approach:
        - Uses pmdarima models if available and successfully fitted
        - Falls back to statsmodels models otherwise
        
        Args:
            periods (int): Number of periods to forecast (default: 12 months)
            alpha (float): Significance level for confidence intervals (default: 0.10 for 90% CI)
                          - 0.20 for 80% CI (faster)
                          - 0.10 for 90% CI (balanced, recommended)
                          - 0.05 for 95% CI (wider bounds, slower)
            confidence_level (str): Confidence level label for output (default: '90')
            
        Returns:
            pd.DataFrame: Forecast results with columns:
                         - Date (datetime index)
                         - Income_Forecast
                         - Income_Lower_CI
                         - Income_Upper_CI
                         - Expenses_Forecast
                         - Expenses_Lower_CI
                         - Expenses_Upper_CI
                         - Investment_Forecast
                         - Investment_Lower_CI
                         - Investment_Upper_CI
                         - Net_Cash_Flow_Forecast
                         - Net_Cash_Flow_Lower_CI
                         - Net_Cash_Flow_Upper_CI
                         
        Raises:
            ValueError: If models haven't been fitted yet
        """
        if (self.income_model is None or 
            self.expense_model is None or 
            self.investment_model is None or
            self.net_cashflow_model is None):
            raise ValueError("Must call fit_sarima_models() before forecasting")
        
        if self.monthly_data is None:
            raise ValueError("No historical data available for forecasting")
        
        # Smart dispatch based on available models and packages
        try:
            # Check if pmdarima is available and models were fitted successfully
            if (hasattr(self, '_pmdarima_models_fitted') and 
                self._pmdarima_models_fitted and 
                hasattr(self, 'pmdarima_available') and 
                self.pmdarima_available):
                
                self.logger.info(f"Forecasting with {confidence_level}% confidence level (alpha={alpha})")
                self.logger.info(f"Using pmdarima models for {periods}-period forecast")
                return self._forecast_pmdarima_direct(periods, alpha)
                
            # Check if statsmodels models are available
            elif (hasattr(self, '_statsmodels_models_fitted') and 
                  self._statsmodels_models_fitted and 
                  STATSMODELS_AVAILABLE):
                
                self.logger.warning("pmdarima models not available, using statsmodels fallback")
                return self._forecast_statsmodels_direct(periods, alpha)
                
            # Fallback to forecast_statsmodels if no model state tracking
            elif STATSMODELS_AVAILABLE:
                self.logger.warning("Model state unknown, using statsmodels fallback method")
                return self.forecast_statsmodels(periods)
                
            else:
                raise ValueError("No suitable forecasting method available")
                
        except Exception as e:
            self.logger.error(f"Error in forecast dispatch: {str(e)}")
            # Final fallback attempt
            if STATSMODELS_AVAILABLE:
                self.logger.warning("Attempting final fallback to statsmodels method")
                try:
                    return self.forecast_statsmodels(periods)
                except Exception as fallback_error:
                    self.logger.error(f"Fallback also failed: {fallback_error}")
                    raise e
            else:
                raise
                
    def _forecast_pmdarima_direct(self, periods: int, alpha: float = 0.10) -> pd.DataFrame:
        """
        Generate forecasts using fitted pmdarima models (optimized version).
        
        Args:
            periods (int): Number of periods to forecast
            alpha (float): Significance level for confidence intervals (default: 0.10 for 90% CI)
            
        Returns:
            pd.DataFrame: Forecast results with datetime index
        """
        try:
            # Generate future dates
            last_date = self.monthly_data.index.max()
            future_dates = pd.date_range(
                start=last_date + pd.DateOffset(months=1),
                periods=periods,
                freq='ME'
            )
            
            # Generate forecasts using pmdarima models with configurable alpha
            forecasts = self._forecast_pmdarima(periods, alpha)
            
            # Create forecast DataFrame
            forecast_df = pd.DataFrame(forecasts, index=future_dates)
            
            self.logger.info(f"Successfully generated {periods}-period pmdarima forecast")
            return forecast_df
            
        except Exception as e:
            self.logger.error(f"Error in pmdarima forecast generation: {str(e)}")
            raise
            
    def _forecast_statsmodels_direct(self, periods: int, alpha: float = 0.10) -> pd.DataFrame:
        """
        Generate forecasts using fitted statsmodels models (optimized version).
        
        Args:
            periods (int): Number of periods to forecast
            alpha (float): Significance level for confidence intervals (default: 0.10 for 90% CI)
            
        Returns:
            pd.DataFrame: Forecast results with datetime index
        """
        try:
            # Generate future dates
            last_date = self.monthly_data.index.max()
            future_dates = pd.date_range(
                start=last_date + pd.DateOffset(months=1),
                periods=periods,
                freq='ME'
            )
            
            # Generate forecasts using statsmodels models with configurable alpha
            forecasts = self._forecast_statsmodels(periods, alpha)
            
            # Create forecast DataFrame
            forecast_df = pd.DataFrame(forecasts, index=future_dates)
            
            self.logger.info(f"Successfully generated {periods}-period statsmodels forecast")
            return forecast_df
            
        except Exception as e:
            self.logger.error(f"Error in statsmodels forecast generation: {str(e)}")
            raise
            
    def _forecast_pmdarima(self, periods: int, alpha: float = 0.10) -> Dict[str, np.ndarray]:
        """
        Generate forecasts using pmdarima models.
        
        Args:
            periods (int): Number of periods to forecast
            alpha (float): Significance level for confidence intervals (default: 0.10 for 90% CI)
            
        Returns:
            Dict[str, np.ndarray]: Dictionary of forecast series
        """
        forecasts = {}
        
        # Income forecasts with configurable confidence level
        income_forecast, income_conf_int = self.income_model.predict(
            n_periods=periods, 
            return_conf_int=True,
            alpha=alpha
        )
        forecasts['Income_Forecast'] = income_forecast
        forecasts['Income_Lower_CI'] = income_conf_int[:, 0]
        forecasts['Income_Upper_CI'] = income_conf_int[:, 1]
        
        # Expenses forecasts
        expense_forecast, expense_conf_int = self.expense_model.predict(
            n_periods=periods,
            return_conf_int=True,
            alpha=alpha
        )
        forecasts['Expenses_Forecast'] = expense_forecast
        forecasts['Expenses_Lower_CI'] = expense_conf_int[:, 0]
        forecasts['Expenses_Upper_CI'] = expense_conf_int[:, 1]
        
        # Investment forecasts
        investment_forecast, investment_conf_int = self.investment_model.predict(
            n_periods=periods,
            return_conf_int=True,
            alpha=alpha
        )
        forecasts['Investment_Forecast'] = investment_forecast
        forecasts['Investment_Lower_CI'] = investment_conf_int[:, 0]
        forecasts['Investment_Upper_CI'] = investment_conf_int[:, 1]
        
        # Net cash flow forecasts
        netcf_forecast, netcf_conf_int = self.net_cashflow_model.predict(
            n_periods=periods,
            return_conf_int=True,
            alpha=alpha
        )
        forecasts['Net_Cash_Flow_Forecast'] = netcf_forecast
        forecasts['Net_Cash_Flow_Lower_CI'] = netcf_conf_int[:, 0]
        forecasts['Net_Cash_Flow_Upper_CI'] = netcf_conf_int[:, 1]
        
        return forecasts
        
    def _forecast_statsmodels(self, periods: int, alpha: float = 0.10) -> Dict[str, np.ndarray]:
        """
        Generate forecasts using statsmodels models.
        
        Args:
            periods (int): Number of periods to forecast
            alpha (float): Significance level for confidence intervals (default: 0.10 for 90% CI)
            
        Returns:
            Dict[str, np.ndarray]: Dictionary of forecast series
        """
        forecasts = {}
        
        # Income forecasts with configurable confidence level
        income_forecast = self.income_model.forecast(steps=periods)
        income_forecast_result = self.income_model.get_forecast(steps=periods)
        income_conf_int = income_forecast_result.conf_int(alpha=alpha)
        
        forecasts['Income_Forecast'] = income_forecast
        forecasts['Income_Lower_CI'] = income_conf_int.iloc[:, 0].values
        forecasts['Income_Upper_CI'] = income_conf_int.iloc[:, 1].values
        
        # Expenses forecasts
        expense_forecast = self.expense_model.forecast(steps=periods)
        expense_forecast_result = self.expense_model.get_forecast(steps=periods)
        expense_conf_int = expense_forecast_result.conf_int(alpha=alpha)
        
        forecasts['Expenses_Forecast'] = expense_forecast
        forecasts['Expenses_Lower_CI'] = expense_conf_int.iloc[:, 0].values
        forecasts['Expenses_Upper_CI'] = expense_conf_int.iloc[:, 1].values
        
        # Investment forecasts
        investment_forecast = self.investment_model.forecast(steps=periods)
        investment_forecast_result = self.investment_model.get_forecast(steps=periods)
        investment_conf_int = investment_forecast_result.conf_int(alpha=alpha)
        
        forecasts['Investment_Forecast'] = investment_forecast
        forecasts['Investment_Lower_CI'] = investment_conf_int.iloc[:, 0].values
        forecasts['Investment_Upper_CI'] = investment_conf_int.iloc[:, 1].values
        
        # Net cash flow forecasts
        netcf_forecast = self.net_cashflow_model.forecast(steps=periods)
        netcf_forecast_result = self.net_cashflow_model.get_forecast(steps=periods)
        netcf_conf_int = netcf_forecast_result.conf_int(alpha=alpha)
        
        forecasts['Net_Cash_Flow_Forecast'] = netcf_forecast
        forecasts['Net_Cash_Flow_Lower_CI'] = netcf_conf_int.iloc[:, 0].values
        forecasts['Net_Cash_Flow_Upper_CI'] = netcf_conf_int.iloc[:, 1].values
        
        return forecasts

    def forecast_fast(self, periods: int = 12) -> pd.DataFrame:
        """
        Generate fast forecasts without confidence intervals for better performance.
        
        Args:
            periods (int): Number of periods to forecast (default: 12 months)
            
        Returns:
            pd.DataFrame: Forecast results with columns:
                         - Date (datetime index)
                         - Income_Forecast
                         - Expenses_Forecast
                         - Investment_Forecast
                         - Net_Cash_Flow_Forecast
                         
        Raises:
            ValueError: If models haven't been fitted yet
        """
        if (self.income_model is None or 
            self.expense_model is None or 
            self.investment_model is None or
            self.net_cashflow_model is None):
            raise ValueError("Must call fit_sarima_models() before forecasting")
        
        if self.monthly_data is None:
            raise ValueError("No historical data available for forecasting")
        
        try:
            import time
            start_time = time.time()
            
            # Generate future dates
            last_date = self.monthly_data.index.max()
            future_dates = pd.date_range(
                start=last_date + pd.DateOffset(months=1),
                periods=periods,
                freq='ME'
            )
            
            # Generate forecasts for each series (no confidence intervals)
            forecasts = {}
            
            self.logger.info("Generating fast income forecast...")
            income_forecast = self.income_model.predict(n_periods=periods)
            forecasts['Income_Forecast'] = income_forecast
            
            self.logger.info("Generating fast expenses forecast...")
            expense_forecast = self.expense_model.predict(n_periods=periods)
            forecasts['Expenses_Forecast'] = expense_forecast
            
            self.logger.info("Generating fast investment forecast...")
            investment_forecast = self.investment_model.predict(n_periods=periods)
            forecasts['Investment_Forecast'] = investment_forecast
            
            self.logger.info("Generating fast net cash flow forecast...")
            netcf_forecast = self.net_cashflow_model.predict(n_periods=periods)
            forecasts['Net_Cash_Flow_Forecast'] = netcf_forecast
            
            # Create forecast DataFrame
            forecast_df = pd.DataFrame(forecasts, index=future_dates)
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"Successfully generated fast {periods}-period forecast in {elapsed_time:.2f} seconds")
            
            return forecast_df
            
        except Exception as e:
            self.logger.error(f"Error generating fast forecasts: {str(e)}")
            raise
    
    def forecast_statsmodels(self, periods: int = 12) -> pd.DataFrame:
        """
        Generate forecasts using statsmodels SARIMA models with grid search optimization.
        
        This method provides a pure statsmodels implementation that fits optimal SARIMA models
        for each financial series and generates forecasts with confidence intervals. It serves
        as an alternative to the pmdarima-based forecasting when pmdarima is unavailable.
        
        Args:
            periods (int): Number of periods to forecast (default: 12 months)
            
        Returns:
            pd.DataFrame: Forecast results with columns:
                         - Date (datetime index)
                         - Income_Forecast
                         - Income_Lower_CI  
                         - Income_Upper_CI
                         - Expenses_Forecast
                         - Expenses_Lower_CI
                         - Expenses_Upper_CI
                         - Investment_Forecast
                         - Investment_Lower_CI
                         - Investment_Upper_CI
                         - Net_Cash_Flow_Forecast
                         - Net_Cash_Flow_Lower_CI
                         - Net_Cash_Flow_Upper_CI
                         
        Raises:
            ValueError: If data has not been processed yet or statsmodels not available
        """
        if self.monthly_data is None:
            raise ValueError("Must call fetch_and_process_historical_data() first")
        
        if not STATSMODELS_AVAILABLE:
            raise ValueError("statsmodels package not available. Cannot generate forecasts.")
        
        try:
            self.logger.info(f"Generating {periods}-period forecasts using statsmodels SARIMA models...")
            
            # Generate future dates
            last_date = self.monthly_data.index.max()
            future_dates = pd.date_range(
                start=last_date + pd.DateOffset(months=1),
                periods=periods,
                freq='ME'
            )
            
            # Initialize forecasts dictionary
            forecasts = {}
            
            # Define financial series to process
            series_config = [
                ('Income', 'Total_Income'),
                ('Expenses', 'Total_Expenses'), 
                ('Investment', 'Total_Investment'),
                ('Net_Cash_Flow', 'Net_Cash_Flow')
            ]
            
            # Generate forecasts for each series
            for series_name, column_name in series_config:
                self.logger.info(f"Fitting statsmodels SARIMA model for {series_name}...")
                
                # Get clean time series data
                series_data = self.monthly_data[column_name].dropna()
                
                # Fit optimal SARIMA model using grid search
                fitted_model = self._fit_statsmodels_sarima(series_data, seasonal_period=12)
                
                if fitted_model is None:
                    raise ValueError(f"Failed to fit SARIMA model for {series_name}")
                
                self.logger.info(f"Generating {periods}-period forecast for {series_name}...")
                
                # Generate point forecasts
                point_forecast = fitted_model.forecast(steps=periods)
                
                # Generate forecast with confidence intervals
                forecast_result = fitted_model.get_forecast(steps=periods)
                conf_int = forecast_result.conf_int()
                
                # Store forecasts in dictionary
                forecasts[f'{series_name}_Forecast'] = point_forecast
                forecasts[f'{series_name}_Lower_CI'] = conf_int.iloc[:, 0].values
                forecasts[f'{series_name}_Upper_CI'] = conf_int.iloc[:, 1].values
                
                self.logger.info(f"Successfully generated forecast for {series_name}")
            
            # Create forecast DataFrame
            forecast_df = pd.DataFrame(forecasts, index=future_dates)
            
            self.logger.info(f"Successfully completed {periods}-period statsmodels forecasting")
            
            return forecast_df
            
        except Exception as e:
            self.logger.error(f"Error generating statsmodels forecasts: {str(e)}")
            raise

    def forecast_ensemble(self, periods: int = 12) -> pd.DataFrame:
        """
        Generate ensemble forecasts combining SARIMA and ETS models.
        
        This method implements Step 3.2 of Phase 5.3 Step 3 - Cash Flow Model Enhancement.
        Combines SARIMA and ETS predictions using simple averaging for forecasts and
        uses the widest confidence intervals for conservative estimation.
        
        Args:
            periods (int): Number of periods to forecast (default: 12)
            
        Returns:
            pd.DataFrame: Ensemble forecast results with same format as other forecast methods
                         - Date (datetime index)
                         - Income_Forecast, Income_Lower_CI, Income_Upper_CI
                         - Expenses_Forecast, Expenses_Lower_CI, Expenses_Upper_CI
                         - Investment_Forecast, Investment_Lower_CI, Investment_Upper_CI
                         - Net_Cash_Flow_Forecast, Net_Cash_Flow_Lower_CI, Net_Cash_Flow_Upper_CI
                         
        Raises:
            ValueError: If models haven't been fitted yet
            Exception: If ensemble forecasting fails
        """
        try:
            self.logger.info(f"Starting ensemble forecast generation for {periods} periods")
            
            # Step 1: Generate SARIMA forecasts
            try:
                sarima_forecast = self.forecast_statsmodels(periods)
                self.logger.info("SARIMA forecasts generated successfully")
            except Exception as e:
                self.logger.error(f"Failed to generate SARIMA forecasts: {e}")
                raise ValueError(f"SARIMA forecasting failed: {e}")
            
            # Step 2: Fit ETS models and generate ETS forecasts
            try:
                # Fit ETS models if not already fitted
                if not hasattr(self, 'ets_models') or not self.ets_models:
                    self._fit_ets_models()
                
                ets_forecast = self._forecast_ets_direct(periods)
                self.logger.info("ETS forecasts generated successfully")
            except Exception as e:
                self.logger.error(f"Failed to generate ETS forecasts: {e}")
                raise ValueError(f"ETS forecasting failed: {e}")
            
            # Step 3: Combine forecasts using ensemble logic
            ensemble_data = {}
            forecast_dates = sarima_forecast.index
            
            # Mapping between series names and column prefixes
            series_mapping = {
                'income': 'Income',
                'expense': 'Expenses', 
                'investment': 'Investment',
                'net_cash_flow': 'Net_Cash_Flow'
            }
            
            for ets_series, sarima_prefix in series_mapping.items():
                # SARIMA column names
                sarima_forecast_col = f'{sarima_prefix}_Forecast'
                sarima_lower_col = f'{sarima_prefix}_Lower_CI'
                sarima_upper_col = f'{sarima_prefix}_Upper_CI'
                
                # ETS column names
                ets_forecast_col = f'{ets_series}_forecast'
                ets_lower_col = f'{ets_series}_lower'
                ets_upper_col = f'{ets_series}_upper'
                
                # Check if both forecasts have the required columns
                if (sarima_forecast_col in sarima_forecast.columns and 
                    ets_forecast_col in ets_forecast.columns):
                    
                    # Ensemble forecast: simple average of SARIMA and ETS predictions
                    ensemble_forecast = (sarima_forecast[sarima_forecast_col] + 
                                       ets_forecast[ets_forecast_col]) / 2
                    
                    # Conservative confidence intervals: use the widest bounds
                    if (sarima_lower_col in sarima_forecast.columns and 
                        ets_lower_col in ets_forecast.columns):
                        ensemble_lower = np.minimum(sarima_forecast[sarima_lower_col],
                                                  ets_forecast[ets_lower_col])
                    else:
                        ensemble_lower = sarima_forecast.get(sarima_lower_col, ensemble_forecast * 0.9)
                    
                    if (sarima_upper_col in sarima_forecast.columns and 
                        ets_upper_col in ets_forecast.columns):
                        ensemble_upper = np.maximum(sarima_forecast[sarima_upper_col],
                                                  ets_forecast[ets_upper_col])
                    else:
                        ensemble_upper = sarima_forecast.get(sarima_upper_col, ensemble_forecast * 1.1)
                    
                    # Store ensemble results
                    ensemble_data[sarima_forecast_col] = ensemble_forecast
                    ensemble_data[sarima_lower_col] = ensemble_lower
                    ensemble_data[sarima_upper_col] = ensemble_upper
                    
                    self.logger.info(f"Combined forecasts for {ets_series}")
                    
                else:
                    # Fallback to SARIMA if ETS data is missing
                    self.logger.warning(f"ETS data missing for {ets_series}, using SARIMA only")
                    if sarima_forecast_col in sarima_forecast.columns:
                        ensemble_data[sarima_forecast_col] = sarima_forecast[sarima_forecast_col]
                        ensemble_data[sarima_lower_col] = sarima_forecast.get(sarima_lower_col, 
                                                                            sarima_forecast[sarima_forecast_col] * 0.9)
                        ensemble_data[sarima_upper_col] = sarima_forecast.get(sarima_upper_col,
                                                                            sarima_forecast[sarima_forecast_col] * 1.1)
            
            # Create ensemble forecast DataFrame
            ensemble_df = pd.DataFrame(ensemble_data, index=forecast_dates)
            
            # Validate ensemble DataFrame structure
            expected_columns = []
            for prefix in ['Income', 'Expenses', 'Investment', 'Net_Cash_Flow']:
                expected_columns.extend([f'{prefix}_Forecast', f'{prefix}_Lower_CI', f'{prefix}_Upper_CI'])
            
            missing_columns = [col for col in expected_columns if col not in ensemble_df.columns]
            if missing_columns:
                self.logger.warning(f"Missing ensemble columns: {missing_columns}")
            
            self.logger.info(f"Successfully generated ensemble forecast with {len(ensemble_df.columns)} columns")
            return ensemble_df
            
        except Exception as e:
            self.logger.error(f"Error generating ensemble forecasts: {str(e)}")
            raise

    def simulate_stress_scenario(self, 
                                 periods: int = 12, 
                                 income_shock: float = 0.0, 
                                 expense_shock: float = 0.0,
                                 shock_start_period: int = 0) -> pd.DataFrame:
        """
        Simulate a stress scenario by applying shocks to forecasted cash flows.
        
        Args:
            periods (int): Number of periods to forecast
            income_shock (float): Fractional change in income (e.g., -0.2 for 20% drop)
            expense_shock (float): Fractional change in expenses (e.g., 0.3 for 30% increase)
            shock_start_period (int): Period index when the shock starts (0 to periods-1)
            
        Returns:
            pd.DataFrame: Forecasted data with stress shocks applied
        """
        # 1. Get baseline forecast
        if self.pmdarima_available:
            forecast_df = self.forecast(periods)
        else:
            forecast_df = self.forecast_statsmodels(periods)
            
        # 2. Apply shocks
        stressed_df = forecast_df.copy()
        
        # Apply income shock
        if income_shock != 0:
            stressed_df.iloc[shock_start_period:, stressed_df.columns.get_loc('Income_Forecast')] *= (1 + income_shock)
            
        # Apply expense shock
        if expense_shock != 0:
            stressed_df.iloc[shock_start_period:, stressed_df.columns.get_loc('Expenses_Forecast')] *= (1 + expense_shock)
            
        # 3. Recalculate Net Cash Flow
        # stressed_df['Net_Cash_Flow_Forecast'] = stressed_df['Income_Forecast'] - stressed_df['Expenses_Forecast'] - stressed_df['Investment_Forecast']
        # Note: We need to check if Investment_Forecast exists
        if 'Investment_Forecast' in stressed_df.columns:
            stressed_df['Net_Cash_Flow_Forecast'] = stressed_df['Income_Forecast'] - stressed_df['Expenses_Forecast'] - stressed_df['Investment_Forecast']
        else:
            stressed_df['Net_Cash_Flow_Forecast'] = stressed_df['Income_Forecast'] - stressed_df['Expenses_Forecast']
            
        # 4. Add flag for liquidity warning
        stressed_df['Liquidity_Warning'] = stressed_df['Net_Cash_Flow_Forecast'] < 0
        
        return stressed_df

    def run_rolling_backtesting(self, test_periods: int = 12, num_splits: int = 5, 
                       methods: List[str] = None) -> Dict[str, Any]:
        """
        Perform rolling forecast origin cross-validation for robust model validation.
        
        Enhanced for Phase 5.3 Step 3.3 to support multiple forecasting methods including
        ensemble evaluation. Compares SARIMA, ETS, and Ensemble methods side-by-side.
        
        Args:
            test_periods (int): Number of periods to forecast in each split
            num_splits (int): Number of validation splits to perform
            methods (List[str]): Methods to evaluate. Options: ['sarima', 'ets', 'ensemble']
                                Default: ['sarima', 'ensemble'] for backward compatibility
            
        Returns:
            Dict[str, Any]: Dictionary containing:
                - method_performance: Performance metrics for each method
                - method_comparison: Side-by-side comparison statistics  
                - split_results: Detailed results for each split and method
                - summary_stats: Additional statistical measures
                - best_method: Method with lowest overall MAPE
                
        Raises:
            ValueError: If insufficient data for backtesting with specified parameters
        """
        if self.monthly_data is None:
            raise ValueError("Must call fetch_and_process_historical_data() first")
        
        # Default methods for ensemble evaluation
        if methods is None:
            methods = ['sarima', 'ensemble']  # Start with SARIMA and ensemble comparison
        
        # Validate method names
        valid_methods = {'sarima', 'ets', 'ensemble'}
        invalid_methods = set(methods) - valid_methods
        if invalid_methods:
            raise ValueError(f"Invalid methods: {invalid_methods}. Valid options: {valid_methods}")
        
        total_periods = len(self.monthly_data)
        min_train_periods = 12  # Minimum training periods
        required_periods = min_train_periods + test_periods + (num_splits - 1)
        
        if total_periods < required_periods:
            raise ValueError(
                f"Insufficient data for rolling backtesting. "
                f"Need at least {required_periods} periods, but have {total_periods}. "
                f"Consider reducing num_splits ({num_splits}) or test_periods ({test_periods})"
            )
        
        self.logger.info(
            f"Starting enhanced rolling backtesting: {num_splits} splits, "
            f"{test_periods} test periods each, methods: {methods}, "
            f"{total_periods} total periods available"
        )
        
        try:
            # Store original data and models for restoration
            original_data = self.monthly_data.copy()
            original_income_model = self.income_model
            original_expense_model = self.expense_model
            original_investment_model = self.investment_model
            original_netcf_model = self.net_cashflow_model
            
            split_results = []
            # Track performance for each method
            method_performance = {method: {'Income': [], 'Expenses': [], 'Investment': [], 'Net_Cash_Flow': []} 
                                for method in methods}
            
            # Calculate split points for rolling validation
            for split_idx in range(num_splits):
                test_start_idx = min_train_periods + split_idx
                test_end_idx = test_start_idx + test_periods
                
                # Ensure we don't exceed available data
                if test_end_idx > total_periods:
                    self.logger.warning(f"Split {split_idx + 1} exceeds available data. Stopping at {split_idx} splits.")
                    break
                
                # Extract training and test data for this split
                train_data = original_data.iloc[:test_start_idx].copy()
                test_data = original_data.iloc[test_start_idx:test_end_idx].copy()
                
                # Validate split data sufficiency
                if len(train_data) < min_train_periods or len(test_data) != test_periods:
                    self.logger.warning(
                        f"Insufficient data for split {split_idx + 1}. "
                        f"Train: {len(train_data)} (need >= {min_train_periods}), "
                        f"Test: {len(test_data)} (need {test_periods}). Skipping."
                    )
                    continue
                
                self.logger.info(
                    f"Split {split_idx + 1}/{num_splits}: "
                    f"Training on {len(train_data)} periods "
                    f"({train_data.index[0].strftime('%Y-%m')} to {train_data.index[-1].strftime('%Y-%m')}), "
                    f"testing on {len(test_data)} periods "
                    f"({test_data.index[0].strftime('%Y-%m')} to {test_data.index[-1].strftime('%Y-%m')})"
                )
                
                # Set training data for this split
                self.monthly_data = train_data
                
                # Evaluate each method for this split
                split_result = {
                    'split_number': split_idx + 1,
                    'train_start': train_data.index[0],
                    'train_end': train_data.index[-1],
                    'test_start': test_data.index[0],
                    'test_end': test_data.index[-1],
                    'train_periods': len(train_data),
                    'test_periods': len(test_data),
                    'methods': {}
                }
                
                # Evaluate each method on this split
                for method in methods:
                    try:
                        method_mapes = self._fit_and_evaluate_split_method(
                            train_data, test_data, method, split_idx + 1
                        )
                        
                        # Store results for this method and split
                        split_result['methods'][method] = method_mapes
                        
                        # Accumulate for overall performance tracking
                        method_performance[method]['Income'].append(method_mapes['Income_MAPE'])
                        method_performance[method]['Expenses'].append(method_mapes['Expenses_MAPE'])
                        method_performance[method]['Investment'].append(method_mapes['Investment_MAPE'])
                        method_performance[method]['Net_Cash_Flow'].append(method_mapes['Net_Cash_Flow_MAPE'])
                        
                    except Exception as e:
                        self.logger.error(f"Error evaluating {method} on split {split_idx + 1}: {e}")
                        # Store error placeholder
                        split_result['methods'][method] = {
                            'Income_MAPE': float('inf'),
                            'Expenses_MAPE': float('inf'),
                            'Investment_MAPE': float('inf'),
                            'Net_Cash_Flow_MAPE': float('inf'),
                            'Overall_MAPE': float('inf'),
                            'error': str(e)
                        }
                
                split_results.append(split_result)
            
            # Calculate average performance for each method
            method_summary = {}
            best_method = None
            best_overall_mape = float('inf')
            
            for method in methods:
                if method_performance[method]['Income']:  # Check if method has results
                    method_mean_mape = {
                        'Income': np.mean(method_performance[method]['Income']),
                        'Expenses': np.mean(method_performance[method]['Expenses']),
                        'Investment': np.mean(method_performance[method]['Investment']),
                        'Net_Cash_Flow': np.mean(method_performance[method]['Net_Cash_Flow'])
                    }
                    method_mean_mape['Overall'] = np.mean(list(method_mean_mape.values()))
                    
                    # Calculate summary statistics for this method
                    method_summary_stats = self._calculate_summary_statistics(method_performance[method])
                    
                    method_summary[method] = {
                        'mean_mape': method_mean_mape,
                        'summary_stats': method_summary_stats,
                        'num_successful_splits': len(method_performance[method]['Income'])
                    }
                    
                    # Track best performing method
                    if method_mean_mape['Overall'] < best_overall_mape:
                        best_overall_mape = method_mean_mape['Overall']
                        best_method = method
                else:
                    # Method failed on all splits
                    method_summary[method] = {
                        'mean_mape': {
                            'Income': float('inf'),
                            'Expenses': float('inf'),
                            'Investment': float('inf'),
                            'Net_Cash_Flow': float('inf'),
                            'Overall': float('inf')
                        },
                        'summary_stats': {},
                        'num_successful_splits': 0
                    }
            
            # Create method comparison matrix
            method_comparison = self._create_method_comparison(method_summary, methods)
            
            # Restore original data and models
            self.monthly_data = original_data
            self.income_model = original_income_model
            self.expense_model = original_expense_model
            self.investment_model = original_investment_model
            self.net_cashflow_model = original_netcf_model
            
            results = {
                'method_performance': method_summary,
                'method_comparison': method_comparison,
                'split_results': split_results,
                'best_method': best_method,
                'num_splits_completed': len(split_results),
                'methods_evaluated': methods
            }
            
            self.logger.info(
                f"Enhanced rolling backtesting completed. {len(split_results)} splits performed across {len(methods)} methods. "
                f"Best method: {best_method} (Overall MAPE: {best_overall_mape:.2f}%)"
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error during rolling backtesting: {str(e)}")
            # Restore original data in case of error
            if 'original_data' in locals():
                self.monthly_data = original_data
                self.income_model = original_income_model
                self.expense_model = original_expense_model
                self.investment_model = original_investment_model
                self.net_cashflow_model = original_netcf_model
            raise

    def _fit_and_evaluate_split_method(self, train_data: pd.DataFrame, test_data: pd.DataFrame, 
                                     method: str, split_number: int) -> Dict[str, float]:
        """
        Fit models using specified method and evaluate on test data for a single split.
        
        Enhanced for Phase 5.3 Step 3.3 to support multiple forecasting methods.
        
        Args:
            train_data (pd.DataFrame): Training data for this split
            test_data (pd.DataFrame): Test data for this split
            method (str): Forecasting method ('sarima', 'ets', or 'ensemble')
            split_number (int): Split number for logging
            
        Returns:
            Dict[str, float]: MAPE scores for this split using the specified method
        """
        self.logger.debug(f"Evaluating {method} method on split {split_number}")
        
        # Generate forecasts using the specified method
        if method == 'sarima':
            # Use traditional SARIMA forecasting
            if PMDARIMA_AVAILABLE:
                # Fit pmdarima models
                self.fit_sarima_models()
                forecast_df = self.forecast(len(test_data))
            else:
                # Use statsmodels fallback
                forecast_df = self.forecast_statsmodels(len(test_data))
                
        elif method == 'ets':
            # Use ETS forecasting only
            self._fit_ets_models()
            forecast_df = self._forecast_ets_direct(len(test_data))
            
        elif method == 'ensemble':
            # Use ensemble forecasting (SARIMA + ETS)
            forecast_df = self.forecast_ensemble(len(test_data))
            
        else:
            raise ValueError(f"Unknown forecasting method: {method}")
        
        # Calculate MAPE for each series
        mape_results = {}
        
        # Handle different column naming conventions
        if method == 'ets':
            # ETS uses lowercase naming
            series_mapping = {
                'Income': 'income_forecast',
                'Expenses': 'expense_forecast', 
                'Investment': 'investment_forecast',
                'Net_Cash_Flow': 'net_cash_flow_forecast'
            }
        else:
            # SARIMA and ensemble use standard naming
            series_mapping = {
                'Income': 'Income_Forecast',
                'Expenses': 'Expenses_Forecast',
                'Investment': 'Investment_Forecast', 
                'Net_Cash_Flow': 'Net_Cash_Flow_Forecast'
            }
        
        # Calculate MAPE for each financial series
        for series_name, forecast_col in series_mapping.items():
            data_col = f'Total_{series_name}' if series_name != 'Net_Cash_Flow' else 'Net_Cash_Flow'
            
            if data_col in test_data.columns and forecast_col in forecast_df.columns:
                actual_values = test_data[data_col].values
                forecast_values = forecast_df[forecast_col].values
                mape_results[f'{series_name}_MAPE'] = self._calculate_mape(actual_values, forecast_values)
            else:
                # Handle missing data/columns gracefully
                self.logger.warning(f"Missing data for {series_name} in {method} evaluation")
                mape_results[f'{series_name}_MAPE'] = float('inf')
        
        # Calculate overall MAPE (average of individual MAPEs)
        valid_mapes = [mape for mape in mape_results.values() if not np.isinf(mape)]
        mape_results['Overall_MAPE'] = np.mean(valid_mapes) if valid_mapes else float('inf')
        
        self.logger.debug(f"{method} method on split {split_number}: Overall MAPE = {mape_results['Overall_MAPE']:.2f}%")
        
        return mape_results
    
    def _create_method_comparison(self, method_summary: Dict[str, Any], methods: List[str]) -> Dict[str, Any]:
        """
        Create a comprehensive comparison matrix between different forecasting methods.
        
        Args:
            method_summary (Dict[str, Any]): Summary statistics for each method
            methods (List[str]): List of methods evaluated
            
        Returns:
            Dict[str, Any]: Comparison metrics and rankings
        """
        comparison = {
            'performance_ranking': {},
            'improvement_matrix': {},
            'statistical_significance': {},
            'series_performance': {}
        }
        
        # Rank methods by overall performance
        method_scores = []
        for method in methods:
            if method in method_summary and method_summary[method]['num_successful_splits'] > 0:
                overall_mape = method_summary[method]['mean_mape']['Overall']
                # Only include methods with valid (non-NaN, non-infinite) MAPE values
                if not (np.isnan(overall_mape) or np.isinf(overall_mape)):
                    method_scores.append((method, overall_mape))
        
        # Sort by performance (lower MAPE is better)
        method_scores.sort(key=lambda x: x[1])
        comparison['performance_ranking'] = {
            f"rank_{i+1}": {"method": method, "overall_mape": mape}
            for i, (method, mape) in enumerate(method_scores)
        }
        
        # Calculate improvement matrix (how much better is method A vs method B)
        if len(method_scores) >= 2:
            for i, (method_a, mape_a) in enumerate(method_scores):
                for j, (method_b, mape_b) in enumerate(method_scores):
                    if i != j:
                        improvement_pct = ((mape_b - mape_a) / mape_b) * 100
                        comparison['improvement_matrix'][f"{method_a}_vs_{method_b}"] = {
                            'improvement_percentage': improvement_pct,
                            'interpretation': 'better' if improvement_pct > 0 else 'worse'
                        }
        
        # Analyze performance by series
        series_names = ['Income', 'Expenses', 'Investment', 'Net_Cash_Flow']
        for series in series_names:
            series_ranking = []
            for method in methods:
                if (method in method_summary and 
                    method_summary[method]['num_successful_splits'] > 0 and
                    series in method_summary[method]['mean_mape']):
                    series_mape = method_summary[method]['mean_mape'][series]
                    series_ranking.append((method, series_mape))
            
            series_ranking.sort(key=lambda x: x[1])
            comparison['series_performance'][series] = {
                f"rank_{i+1}": {"method": method, "mape": mape}
                for i, (method, mape) in enumerate(series_ranking)
            }
        
        return comparison
    
    def _fit_and_evaluate_split(self, train_data: pd.DataFrame, test_data: pd.DataFrame, 
                               split_number: int) -> Dict[str, float]:
        """
        Fit models on training data and evaluate on test data for a single split.
        
        Args:
            train_data (pd.DataFrame): Training data for this split
            test_data (pd.DataFrame): Test data for this split
            split_number (int): Split number for logging
            
        Returns:
            Dict[str, float]: MAPE scores for this split
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            seasonal_period = 12
            
            # Income model
            income_series = train_data['Total_Income'].dropna()
            if len(income_series) >= 2 * seasonal_period:
                self.income_model = auto_arima(
                    income_series, seasonal=True, m=seasonal_period,
                    stepwise=True, suppress_warnings=True, error_action='ignore'
                )
            else:
                self.income_model = auto_arima(
                    income_series, seasonal=False,
                    stepwise=True, suppress_warnings=True, error_action='ignore'
                )
            
            # Expense model
            expense_series = train_data['Total_Expenses'].dropna()
            if len(expense_series) >= 2 * seasonal_period:
                self.expense_model = auto_arima(
                    expense_series, seasonal=True, m=seasonal_period,
                    stepwise=True, suppress_warnings=True, error_action='ignore'
                )
            else:
                self.expense_model = auto_arima(
                    expense_series, seasonal=False,
                    stepwise=True, suppress_warnings=True, error_action='ignore'
                )
            
            # Investment model (NEW)
            if 'Total_Investment' in train_data.columns:
                investment_series = train_data['Total_Investment'].dropna()
                if len(investment_series) >= 2 * seasonal_period:
                    self.investment_model = auto_arima(
                        investment_series, seasonal=True, m=seasonal_period,
                        stepwise=True, suppress_warnings=True, error_action='ignore'
                    )
                else:
                    self.investment_model = auto_arima(
                        investment_series, seasonal=False,
                        stepwise=True, suppress_warnings=True, error_action='ignore'
                    )
            else:
                # Create a dummy model if no investment data available
                self.investment_model = auto_arima(
                    pd.Series([0.0] * len(income_series), index=income_series.index),
                    seasonal=False, stepwise=True, suppress_warnings=True, error_action='ignore'
                )
            
            # Net cash flow model
            netcf_series = train_data['Net_Cash_Flow'].dropna()
            if len(netcf_series) >= 2 * seasonal_period:
                self.net_cashflow_model = auto_arima(
                    netcf_series, seasonal=True, m=seasonal_period,
                    stepwise=True, suppress_warnings=True, error_action='ignore'
                )
            else:
                self.net_cashflow_model = auto_arima(
                    netcf_series, seasonal=False,
                    stepwise=True, suppress_warnings=True, error_action='ignore'
                )
        
        # Generate forecasts for test period
        forecast_df = self.forecast(len(test_data))
        
        # Calculate MAPE for each series
        mape_results = {}
        
        # Income MAPE
        income_actual = test_data['Total_Income'].values
        income_forecast = forecast_df['Income_Forecast'].values
        mape_results['Income_MAPE'] = self._calculate_mape(income_actual, income_forecast)
        
        # Expenses MAPE
        expense_actual = test_data['Total_Expenses'].values
        expense_forecast = forecast_df['Expenses_Forecast'].values
        mape_results['Expenses_MAPE'] = self._calculate_mape(expense_actual, expense_forecast)
        
        # Investment MAPE (NEW)
        if 'Total_Investment' in test_data.columns:
            investment_actual = test_data['Total_Investment'].values
            investment_forecast = forecast_df['Investment_Forecast'].values
            mape_results['Investment_MAPE'] = self._calculate_mape(investment_actual, investment_forecast)
        else:
            mape_results['Investment_MAPE'] = 0.0  # No investment data to evaluate
        
        # Net Cash Flow MAPE
        netcf_actual = test_data['Net_Cash_Flow'].values
        netcf_forecast = forecast_df['Net_Cash_Flow_Forecast'].values
        mape_results['Net_Cash_Flow_MAPE'] = self._calculate_mape(netcf_actual, netcf_forecast)
        
        # Overall MAPE (average)
        mape_results['Overall_MAPE'] = np.mean([
            mape_results['Income_MAPE'],
            mape_results['Expenses_MAPE'],
            mape_results['Investment_MAPE'],
            mape_results['Net_Cash_Flow_MAPE']
        ])
        
        return mape_results
    
    def _calculate_summary_statistics(self, all_mapes: Dict[str, List[float]]) -> Dict[str, Dict[str, float]]:
        """
        Calculate summary statistics for the rolling backtesting results.
        
        Args:
            all_mapes (Dict[str, List[float]]): MAPE values for each series across splits
            
        Returns:
            Dict[str, Dict[str, float]]: Summary statistics for each series
        """
        summary_stats = {}
        
        for series_name, mape_values in all_mapes.items():
            if mape_values:  # Check if we have values
                summary_stats[series_name] = {
                    'mean': np.mean(mape_values),
                    'std': np.std(mape_values),
                    'min': np.min(mape_values),
                    'max': np.max(mape_values),
                    'median': np.median(mape_values),
                    'q25': np.percentile(mape_values, 25),
                    'q75': np.percentile(mape_values, 75)
                }
            else:
                summary_stats[series_name] = {
                    'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0,
                    'median': 0.0, 'q25': 0.0, 'q75': 0.0
                }
        
        return summary_stats
    
    # Backward compatibility: keep original backtest method as alias
    def backtest(self, test_periods: int = 12) -> Dict[str, float]:
        """
        Legacy backtesting method for backward compatibility.
        
        This method is deprecated. Use run_backtesting() for more robust validation.
        Performs a single train-test split for quick validation.
        
        Args:
            test_periods (int): Number of recent periods to hold out for testing
            
        Returns:
            Dict[str, float]: Dictionary containing MAPE scores for each series
        """
        # Use run_backtesting with single split for compatibility
        results = self.run_backtesting(test_periods=test_periods, num_splits=1)
        
        # Extract single split results for backward compatibility
        if results['split_results']:
            single_split = results['split_results'][0]
            return {
                'Income_MAPE': single_split['Income_MAPE'],
                'Expenses_MAPE': single_split['Expenses_MAPE'],
                'Net_Cash_Flow_MAPE': single_split['Net_Cash_Flow_MAPE'],
                'Overall_MAPE': single_split['Overall_MAPE']
            }
        else:
            return {'Income_MAPE': 0.0, 'Expenses_MAPE': 0.0, 'Net_Cash_Flow_MAPE': 0.0, 'Overall_MAPE': 0.0}
    
    def _calculate_mape(self, actual: np.ndarray, forecast: np.ndarray) -> float:
        """
        Calculate Mean Absolute Percentage Error (MAPE).
        
        Args:
            actual (np.ndarray): Actual values
            forecast (np.ndarray): Forecasted values
            
        Returns:
            float: MAPE as a percentage
        """
        # Avoid division by zero
        mask = actual != 0
        if not mask.any():
            return 100.0  # Return 100% error if all actual values are zero
        
        mape = np.mean(np.abs((actual[mask] - forecast[mask]) / actual[mask])) * 100
        return mape
    
    def get_model_summary(self) -> Dict[str, Any]:
        """
        Get summary information about the fitted models.
        
        Returns:
            Dict[str, Any]: Summary information about all fitted models
        """
        summary = {
            'data_period': {
                'start_date': self.monthly_data.index.min() if self.monthly_data is not None else None,
                'end_date': self.monthly_data.index.max() if self.monthly_data is not None else None,
                'months_of_data': len(self.monthly_data) if self.monthly_data is not None else 0
            },
            'models': {}
        }
        
        for model_name, model in [
            ('income', self.income_model),
            ('expenses', self.expense_model),
            ('investment', self.investment_model),
            ('net_cash_flow', self.net_cashflow_model)
        ]:
            if model is not None:
                try:
                    # Check if this is a pmdarima model (has order attribute)
                    if hasattr(model, 'order') and hasattr(model, 'seasonal_order'):
                        # pmdarima model
                        summary['models'][model_name] = {
                            'order': model.order,
                            'seasonal_order': model.seasonal_order,
                            'aic': model.aic() if callable(model.aic) else model.aic,
                            'bic': model.bic() if callable(model.bic) else model.bic
                        }
                    else:
                        # statsmodels model - get info from model specification
                        if hasattr(model, 'specification') and model.specification:
                            order = model.specification.get('order', 'unknown')
                            seasonal_order = model.specification.get('seasonal_order', 'unknown')
                        else:
                            # Fallback: get from model_params if available
                            order = self.model_params.get(model_name, {}).get('order', 'unknown')
                            seasonal_order = self.model_params.get(model_name, {}).get('seasonal_order', 'unknown')
                        
                        summary['models'][model_name] = {
                            'order': order,
                            'seasonal_order': seasonal_order,
                            'aic': model.aic,
                            'bic': model.bic
                        }
                except Exception as e:
                    # Fallback for any model access issues
                    self.logger.warning(f"Could not extract model info for {model_name}: {e}")
                    summary['models'][model_name] = {
                        'order': 'unknown',
                        'seasonal_order': 'unknown',
                        'aic': 'unknown',
                        'bic': 'unknown',
                        'error': str(e)
                    }
        
        return summary
    
    def plot_forecast(self, historical_data: pd.DataFrame, forecast_df: pd.DataFrame, 
                     series_to_plot: Optional[List[str]] = None):
        """
        Generate comprehensive plots for specified cash flow series with forecasts and confidence intervals.
        
        Args:
            historical_data (pd.DataFrame): Historical monthly data with columns 
                                          ['Total_Income', 'Total_Expenses', 'Total_Investment', 'Net_Cash_Flow']
            forecast_df (pd.DataFrame): Forecast data with columns for each series:
                                       - '{Series}_Forecast'
                                       - '{Series}_Lower_CI' 
                                       - '{Series}_Upper_CI'
            series_to_plot (Optional[List[str]]): List of series to plot. Options:
                                                 ['Income', 'Expenses', 'Investment', 'Net_Cash_Flow']
                                                 If None, plots all four series.
        
        Returns:
            matplotlib.figure.Figure: Figure object for further customization or saving
            
        Raises:
            ImportError: If matplotlib is not installed
            ValueError: If required data columns are missing
        """
        if plt is None or mdates is None:
            raise ImportError(
                "matplotlib package is required for visualization. "
                "Please install it using: pip install matplotlib"
            )
        
        # Default to plotting all series if not specified
        if series_to_plot is None:
            series_to_plot = ['Income', 'Expenses', 'Investment', 'Net_Cash_Flow']
        
        # Validate input data
        self._validate_plot_data(historical_data, forecast_df, series_to_plot)
        
        # Set up the plotting configuration
        n_series = len(series_to_plot)
        fig, axes = plt.subplots(n_series, 1, figsize=(15, 4 * n_series))
        
        # Ensure axes is always a list for consistent handling
        if n_series == 1:
            axes = [axes]
        
        # Color and style configuration
        colors = {
            'Income': '#2E86AB',      # Blue
            'Expenses': '#A23B72',    # Red/Purple
            'Investment': '#28A745',  # Green
            'Net_Cash_Flow': '#F18F01' # Orange
        }
        
        # Plot each series
        for i, series in enumerate(series_to_plot):
            ax = axes[i]
            
            # Map series name to historical data column
            historical_col = self._get_historical_column_name(series)
            forecast_col = f"{series}_Forecast"
            lower_ci_col = f"{series}_Lower_CI"
            upper_ci_col = f"{series}_Upper_CI"
            
            # Get color for this series
            color = colors.get(series, '#333333')
            
            # Plot historical data
            ax.plot(historical_data.index, historical_data[historical_col], 
                   label=f'Historical {series}', color=color, linewidth=2, 
                   marker='o', markersize=3, alpha=0.8)
            
            # Plot forecasted values
            ax.plot(forecast_df.index, forecast_df[forecast_col], 
                   label=f'{series} Forecast', color=color, linestyle='--', 
                   linewidth=2, marker='s', markersize=4, alpha=0.9)
            
            # Add confidence interval shading
            ax.fill_between(forecast_df.index, 
                           forecast_df[lower_ci_col], 
                           forecast_df[upper_ci_col], 
                           alpha=0.3, color=color, 
                           label='95% Confidence Interval')
            
            # Add vertical line to separate historical from forecast
            if len(historical_data) > 0:
                last_historical = historical_data.index[-1]
                ax.axvline(x=last_historical, color='red', linestyle=':', 
                          alpha=0.7, linewidth=1, label='Forecast Start')
            
            # Add horizontal reference line for Net Cash Flow (zero line)
            if series == 'Net_Cash_Flow':
                ax.axhline(y=0, color='black', linestyle='-', alpha=0.4, 
                          linewidth=1, label='Break-even')
            
            # Formatting and styling
            ax.set_title(f'Monthly {series}: Historical Data and 12-Month Forecast', 
                        fontsize=14, fontweight='bold', pad=20)
            ax.set_ylabel(f'{series} (¥)', fontsize=12)
            ax.legend(loc='best', frameon=True, fancybox=True, shadow=True)
            ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
            
            # Format x-axis dates
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))  # Every 6 months
            
            # Rotate x-axis labels for better readability
            for label in ax.get_xticklabels():
                label.set_rotation(45)
                label.set_ha('right')
            
            # Add some padding to y-axis
            y_min, y_max = ax.get_ylim()
            y_range = y_max - y_min
            ax.set_ylim(y_min - 0.05 * y_range, y_max + 0.05 * y_range)
        
        # Set x-label only on the bottom subplot
        axes[-1].set_xlabel('Date', fontsize=12)
        
        # Add overall title
        if n_series > 1:
            fig.suptitle('Cash Flow Forecasting Analysis', fontsize=16, fontweight='bold', y=0.98)
        
        # Adjust layout to prevent overlapping
        plt.tight_layout()
        
        # Add some additional spacing if there's a main title
        if n_series > 1:
            plt.subplots_adjust(top=0.94)
        
        return fig
    
    def _validate_plot_data(self, historical_data: pd.DataFrame, forecast_df: pd.DataFrame, 
                           series_to_plot: List[str]) -> None:
        """
        Validate that the required data columns exist for plotting.
        
        Args:
            historical_data (pd.DataFrame): Historical data
            forecast_df (pd.DataFrame): Forecast data
            series_to_plot (List[str]): Series to validate
            
        Raises:
            ValueError: If required columns are missing
        """
        # Check historical data columns
        for series in series_to_plot:
            historical_col = self._get_historical_column_name(series)
            if historical_col not in historical_data.columns:
                raise ValueError(f"Historical data missing required column: {historical_col}")
        
        # Check forecast data columns
        for series in series_to_plot:
            required_forecast_cols = [
                f"{series}_Forecast",
                f"{series}_Lower_CI", 
                f"{series}_Upper_CI"
            ]
            
            for col in required_forecast_cols:
                if col not in forecast_df.columns:
                    raise ValueError(f"Forecast data missing required column: {col}")
    
    def _get_historical_column_name(self, series: str) -> str:
        """
        Map series name to historical data column name.
        
        Args:
            series (str): Series name ('Income', 'Expenses', 'Investment', 'Net_Cash_Flow')
            
        Returns:
            str: Corresponding historical data column name
        """
        mapping = {
            'Income': 'Total_Income',
            'Expenses': 'Total_Expenses',
            'Investment': 'Total_Investment',
            'Net_Cash_Flow': 'Net_Cash_Flow'
        }
        
        if series not in mapping:
            raise ValueError(f"Unknown series: {series}. Valid options: {list(mapping.keys())}")
        
        return mapping[series]
