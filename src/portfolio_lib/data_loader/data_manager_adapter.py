# portfolio_lib/data_loader/data_manager_adapter.py
"""
Module for loading financial data from the data_manager module.
Acts as an adapter between the data_manager module and portfolio_lib.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional

from src.data_manager.manager import DataManager

def load_data_from_data_manager(config_path: str = '../config/settings.yaml') -> Dict[str, pd.DataFrame]:
    """
    Loads financial data using the DataManager module.
    
    Args:
        config_path: Path to the configuration file for DataManager.
        
    Returns:
        A dictionary containing the loaded DataFrames:
        - 'balance_sheet_df': Balance sheet data
        - 'monthly_df': Monthly income/expense data
        - 'holdings_df': Detailed holdings data
        - 'transactions_df': Transaction history data
    """
    print(f"Initializing DataManager with config: {config_path}")
    try:
        # Initialize DataManager
        data_manager = DataManager(config_path=config_path)
        
        # Get data from DataManager
        print("Retrieving data from DataManager...")
        balance_sheet_df = data_manager.get_balance_sheet()
        monthly_df = data_manager.get_monthly_income_expense()
        holdings_df = data_manager.get_holdings()
        transactions_df = data_manager.get_transactions()
        
        # Verify data was retrieved successfully
        result = {}
        if balance_sheet_df is not None:
            print(f"Balance Sheet loaded: {balance_sheet_df.shape[0]} rows, {balance_sheet_df.shape[1]} columns")
            result['balance_sheet_df'] = balance_sheet_df
        else:
            print("Warning: Balance Sheet data could not be loaded")
            
        if monthly_df is not None:
            print(f"Monthly Income/Expense loaded: {monthly_df.shape[0]} rows, {monthly_df.shape[1]} columns")
            result['monthly_df'] = monthly_df
        else:
            print("Warning: Monthly Income/Expense data could not be loaded")
            
        if holdings_df is not None:
            print(f"Holdings loaded: {holdings_df.shape[0]} rows, {holdings_df.shape[1]} columns")
            result['holdings_df'] = holdings_df
        else:
            print("Warning: Holdings data could not be loaded")
            
        if transactions_df is not None:
            print(f"Transactions loaded: {transactions_df.shape[0]} rows, {transactions_df.shape[1]} columns")
            result['transactions_df'] = transactions_df
        else:
            print("Warning: Transactions data could not be loaded")
            
        return result
    
    except Exception as e:
        print(f"Error loading data from DataManager: {e}")
        import traceback
        print(traceback.format_exc())
        return {}

def compatibility_conversion(data_dict: Dict[str, pd.DataFrame]) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Converts data from DataManager format to the format expected by legacy portfolio_lib functions.
    This function helps maintain backward compatibility during transition.
    
    Args:
        data_dict: Dictionary containing DataFrames from DataManager.
        
    Returns:
        A tuple containing (balance_sheet_df, monthly_df) in legacy format.
    """
    balance_sheet_df = data_dict.get('balance_sheet_df')
    monthly_df = data_dict.get('monthly_df')
    
    # For now, return the DataFrames directly as they are expected to be compatible
    # This function can be expanded to modify the format if needed
    return balance_sheet_df, monthly_df
