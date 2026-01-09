"""
Data Pipeline Management

Orchestrates data flow between modules and manages the complete analysis pipeline.
Handles module integration, data validation, and error recovery.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
import logging

# Import existing modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data_manager.historical_manager import HistoricalDataManager
from financial_analysis.analyzer import FinancialAnalyzer
from financial_analysis.cost_basis import calculate_cost_basis_for_portfolio
from portfolio_lib.data_integration import PortfolioAnalysisManager

class DataPipeline:
    """
    Manages the complete data pipeline from Excel files to analysis results.
    Coordinates between DataManager, FinancialAnalyzer, and PortfolioAnalysisManager.
    """
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """Initialize the data pipeline with configuration"""
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        
        # Initialize modules
        self.data_manager = None
        self.financial_analyzer = None
        self.portfolio_manager = None
        
        # Data storage
        self.raw_data = {}
        self.processed_data = {}
        self.analysis_results = {}
        
        self.pipeline_status = {
            "data_loading": False,
            "cost_basis": False,
            "financial_analysis": False,
            "portfolio_analysis": False,
            "completed": False
        }
    
    def initialize_modules(self) -> bool:
        """Initialize all required modules"""
        try:
            # Initialize DataManager (now using HistoricalDataManager)
            self.data_manager = HistoricalDataManager(config_path=self.config_path)
            self.logger.info("DataManager initialized successfully")
            
            # Initialize FinancialAnalyzer
            self.financial_analyzer = FinancialAnalyzer()
            self.logger.info("FinancialAnalyzer initialized successfully")
            
            # Initialize PortfolioAnalysisManager
            self.portfolio_manager = PortfolioAnalysisManager(
                config_path=self.config_path
            )
            self.logger.info("PortfolioAnalysisManager initialized successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize modules: {e}")
            return False
    
    def load_data(self) -> bool:
        """Load and validate data from all sources"""
        try:
            if not self.data_manager:
                if not self.initialize_modules():
                    return False
            
            # Load data using HistoricalDataManager
            self.raw_data = {
                'balance_sheet_df': self.data_manager.get_balance_sheet(),
                'monthly_df': self.data_manager.get_monthly_income_expense(),
                'holdings_df': self.data_manager.get_holdings(),
                'transactions_df': self.data_manager.get_transactions(),
                'historical_holdings_df': self.data_manager.get_historical_holdings()  # NEW: Get full historical data
            }
            
            # Validate data quality
            validation_results = self._validate_data_quality()
            
            if validation_results['overall_quality'] == 'poor':
                self.logger.warning("Data quality is poor, analysis may be unreliable")
            
            self.pipeline_status["data_loading"] = True
            self.logger.info("Data loading completed successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Data loading failed: {e}")
            return False
    
    def calculate_cost_basis(self) -> bool:
        """Calculate cost basis for all assets using FIFO methodology"""
        try:
            if not self.pipeline_status["data_loading"]:
                self.logger.error("Data must be loaded before calculating cost basis")
                return False
            
            transactions_df = self.raw_data.get('transactions_df')
            holdings_df = self.raw_data.get('holdings_df')
            
            if transactions_df is None or transactions_df.empty:
                self.logger.warning("No transaction data available for cost basis calculation")
                return False
            
            self.logger.info(f"Starting cost basis calculation with {len(transactions_df)} transactions")
            
            # Get current market prices from holdings data
            current_prices = {}
            if holdings_df is not None and not holdings_df.empty:
                # Reset index to access Asset_ID as column (it's in the index)
                holdings_reset = holdings_df.reset_index()
                for _, holding in holdings_reset.iterrows():
                    try:
                        asset_id = holding.get('Asset_ID')
                        if asset_id is None:
                            continue
                            
                        # Use Market_Value_CNY instead of Market_Value
                        market_value = holding.get('Market_Value_CNY', 0)
                        quantity = holding.get('Quantity', 0)
                        
                        if quantity > 0 and market_value > 0:
                            current_prices[asset_id] = market_value / quantity
                            
                    except Exception as e:
                        self.logger.debug(f"Skipping holding due to data issue: {e}")
                        continue
            
            self.logger.info(f"Extracted {len(current_prices)} current prices from holdings")
            
            # Calculate cost basis using FIFO methodology
            cost_basis_results = calculate_cost_basis_for_portfolio(
                transactions_df, 
                current_prices
            )
            
            if not cost_basis_results:
                self.logger.warning("Cost basis calculation returned no results")
                return False
            
            # Store results and enrich holdings data
            self.processed_data['cost_basis_results'] = cost_basis_results
            
            # Enrich holdings data with cost basis information
            if holdings_df is not None and not holdings_df.empty:
                try:
                    enriched_holdings = self._enrich_holdings_with_cost_basis(
                        holdings_df, cost_basis_results
                    )
                    self.processed_data['enriched_holdings'] = enriched_holdings
                    self.logger.info(f"Holdings enriched with cost basis data: {len(enriched_holdings)} rows")
                except Exception as e:
                    self.logger.warning(f"Holdings enrichment failed: {e}")
                    # Continue without enrichment
            
            self.pipeline_status["cost_basis"] = True
            self.logger.info(f"Cost basis calculated for {len(cost_basis_results)} assets")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Cost basis calculation failed: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _enrich_holdings_with_cost_basis(self, holdings_df, cost_basis_results):
        """Enrich holdings DataFrame with cost basis information"""
        enriched_df = holdings_df.copy()
        
        # Add new columns for cost basis information
        enriched_df['Cost_Basis'] = 0.0
        enriched_df['Average_Cost'] = 0.0
        enriched_df['Realized_PnL'] = 0.0
        enriched_df['Unrealized_PnL'] = 0.0
        enriched_df['Total_Return'] = 0.0
        
        for idx, holding in enriched_df.iterrows():
            asset_id = holding['Asset_ID']
            
            if asset_id in cost_basis_results:
                cb_data = cost_basis_results[asset_id]
                
                enriched_df.at[idx, 'Cost_Basis'] = cb_data['total_cost_basis']
                enriched_df.at[idx, 'Average_Cost'] = cb_data['average_cost']
                enriched_df.at[idx, 'Realized_PnL'] = cb_data['realized_pnl']
                
                if 'unrealized_pnl' in cb_data:
                    enriched_df.at[idx, 'Unrealized_PnL'] = cb_data['unrealized_pnl']
                
                # Calculate total return
                total_return = cb_data['realized_pnl'] + cb_data.get('unrealized_pnl', 0)
                enriched_df.at[idx, 'Total_Return'] = total_return
        
        return enriched_df
    
    def run_financial_analysis(self) -> bool:
        """Execute comprehensive financial analysis"""
        try:
            if not self.pipeline_status["data_loading"]:
                self.logger.error("Data must be loaded before running financial analysis")
                return False
            
            # Run financial analysis using existing method
            analysis_results = self.financial_analyzer.run_analysis()
            
            self.analysis_results['financial_analysis'] = analysis_results
            self.pipeline_status["financial_analysis"] = True
            self.logger.info("Financial analysis completed successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Financial analysis failed: {e}")
            return False
    
    def run_portfolio_analysis(self) -> bool:
        """Execute comprehensive portfolio optimization analysis"""
        try:
            if not self.pipeline_status["data_loading"]:
                self.logger.error("Data must be loaded before running portfolio analysis")
                return False
            
            # Run portfolio analysis using existing method
            portfolio_results = self.portfolio_manager.analyze_portfolio(debug=False)
            
            # NOTE: Don't override historical_holdings_df - it's already included by PortfolioAnalysisManager
            
            self.analysis_results['portfolio_analysis'] = portfolio_results
            self.pipeline_status["portfolio_analysis"] = True
            self.logger.info("Portfolio analysis completed successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Portfolio analysis failed: {e}")
            return False
    
    def run_complete_pipeline(self) -> Dict[str, Any]:
        """Execute the complete analysis pipeline"""
        start_time = datetime.now()
        
        try:
            # Step 1: Load data
            if not self.load_data():
                raise Exception("Data loading failed")
            
            # Step 2: Calculate cost basis (NEW)
            if not self.calculate_cost_basis():
                self.logger.warning("Cost basis calculation failed, continuing without it")
            
            # Step 3: Run financial analysis
            if not self.run_financial_analysis():
                raise Exception("Financial analysis failed")
            
            # Step 4: Run portfolio analysis
            if not self.run_portfolio_analysis():
                raise Exception("Portfolio analysis failed")
            
            # Mark pipeline as completed
            self.pipeline_status["completed"] = True
            
            # Compile comprehensive results
            comprehensive_results = {
                'pipeline_status': self.pipeline_status,
                'execution_time': (datetime.now() - start_time).total_seconds(),
                'data_summary': self._generate_data_summary(),
                'cost_basis_results': self.processed_data.get('cost_basis_results', {}),
                'enriched_holdings': self.processed_data.get('enriched_holdings', pd.DataFrame()),
                'financial_analysis': self.analysis_results.get('financial_analysis', {}),
                'portfolio_analysis': self.analysis_results.get('portfolio_analysis', {}),
                'integrated_insights': self._generate_integrated_insights()
            }
            
            self.logger.info(f"Complete pipeline executed successfully in {comprehensive_results['execution_time']:.2f} seconds")
            
            return comprehensive_results
            
        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {e}")
            return {
                'pipeline_status': self.pipeline_status,
                'execution_time': (datetime.now() - start_time).total_seconds(),
                'error': str(e),
                'partial_results': self.analysis_results
            }
    
    def _validate_data_quality(self) -> Dict[str, Any]:
        """Validate data quality across all DataFrames"""
        validation_results = {}
        
        for df_name, df in self.raw_data.items():
            if df is None or df.empty:
                validation_results[df_name] = {
                    'status': 'empty',
                    'quality': 'poor',
                    'row_count': 0,
                    'issues': ['DataFrame is empty']
                }
                continue
            
            issues = []
            
            # Check for missing data
            missing_pct = (df.isnull().sum() / len(df) * 100)
            if missing_pct.max() > 50:
                issues.append(f"High missing data: {missing_pct.max():.1f}%")
            
            # Check for duplicate rows
            if df.duplicated().any():
                issues.append(f"Duplicate rows found: {df.duplicated().sum()}")
            
            # Determine quality level
            if len(issues) == 0:
                quality = 'excellent'
            elif len(issues) <= 2:
                quality = 'good'
            elif len(issues) <= 4:
                quality = 'fair'
            else:
                quality = 'poor'
            
            validation_results[df_name] = {
                'status': 'loaded',
                'quality': quality,
                'row_count': len(df),
                'column_count': len(df.columns),
                'issues': issues
            }
        
        # Overall quality assessment
        qualities = [result['quality'] for result in validation_results.values()]
        if 'poor' in qualities:
            overall_quality = 'poor'
        elif 'fair' in qualities:
            overall_quality = 'fair'
        elif 'good' in qualities:
            overall_quality = 'good'
        else:
            overall_quality = 'excellent'
        
        validation_results['overall_quality'] = overall_quality
        
        return validation_results
    
    def _generate_data_summary(self) -> Dict[str, Any]:
        """Generate summary statistics for loaded data"""
        summary = {}
        
        for df_name, df in self.raw_data.items():
            if df is not None and not df.empty:
                summary[df_name] = {
                    'rows': len(df),
                    'columns': len(df.columns),
                    'date_range': self._get_date_range(df),
                    'key_metrics': self._get_key_metrics(df_name, df)
                }
        
        return summary
    
    def _get_date_range(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract date range from DataFrame"""
        date_columns = df.select_dtypes(include=['datetime64']).columns
        
        if len(date_columns) == 0:
            # Try to find date in index
            if hasattr(df.index, 'dtype') and 'datetime' in str(df.index.dtype):
                return {
                    'start_date': df.index.min().strftime('%Y-%m-%d'),
                    'end_date': df.index.max().strftime('%Y-%m-%d'),
                    'period_months': (df.index.max() - df.index.min()).days / 30
                }
            return {'start_date': None, 'end_date': None, 'period_months': None}
        
        date_col = date_columns[0]
        return {
            'start_date': df[date_col].min().strftime('%Y-%m-%d'),
            'end_date': df[date_col].max().strftime('%Y-%m-%d'),
            'period_months': (df[date_col].max() - df[date_col].min()).days / 30
        }
    
    def _get_key_metrics(self, df_name: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract key metrics based on DataFrame type"""
        if df_name == 'balance_sheet_df':
            return {
                'total_assets_current': df['Total_Assets_CNY'].iloc[-1] if 'Total_Assets_CNY' in df.columns else None,
                'total_liabilities_current': df['Total_Liabilities_CNY'].iloc[-1] if 'Total_Liabilities_CNY' in df.columns else None,
                'net_worth_current': df['Net_Worth_CNY'].iloc[-1] if 'Net_Worth_CNY' in df.columns else None
            }
        elif df_name == 'holdings_df':
            return {
                'total_portfolio_value': df['Market_Value_CNY'].sum() if 'Market_Value_CNY' in df.columns else None,
                'number_of_holdings': len(df),
                'asset_types': df['Asset_Type'].nunique() if 'Asset_Type' in df.columns else None
            }
        elif df_name == 'transactions_df':
            return {
                'total_transactions': len(df),
                'transaction_types': df['Transaction_Type'].nunique() if 'Transaction_Type' in df.columns else None,
                'total_invested': df[df['Transaction_Type'] == 'Buy']['Amount_Net_CNY'].sum() if 'Amount_Net_CNY' in df.columns else None
            }
        
        return {}
    
    def _generate_integrated_insights(self) -> Dict[str, Any]:
        """Generate insights that combine financial and portfolio analysis"""
        insights = {
            'cash_flow_investment_alignment': None,
            'portfolio_risk_vs_financial_capacity': None,
            'rebalancing_vs_cash_flow': None
        }
        
        try:
            # This would be implemented based on specific analysis results
            # For now, return placeholder structure
            if self.analysis_results.get('financial_analysis') and self.analysis_results.get('portfolio_analysis'):
                insights['integration_status'] = 'available'
            else:
                insights['integration_status'] = 'partial'
                
        except Exception as e:
            insights['integration_status'] = 'error'
            insights['error'] = str(e)
        
        return insights
