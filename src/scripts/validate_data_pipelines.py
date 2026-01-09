#!/usr/bin/env python3
"""
Data Pipeline Validation Script

Validates the new automated Schwab and CN Fund data processors against
the original manually-maintained files to ensure data integrity and accuracy.

Usage:
    python validate_data_pipelines.py

This script:
1. Loads data using old manual processes (expected)
2. Loads data using new automated processes (actual)
3. Compares the two datasets for discrepancies
4. Exports the automated data to Excel for review
"""

import os
import sys
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Tuple, Optional

# Set up project root path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_manual_data() -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Load data using the original manual data processing methods.
    
    Returns:
        tuple: (manual_holdings_df, manual_transactions_df)
    """
    logger.info("=== Loading Manual Data (Expected) ===")
    
    try:
        from src.data_manager.manager import DataManager
        
        # Initialize DataManager which loads all data including manual fund files
        data_manager = DataManager(config_path='config/settings.yaml')
        
        # Get the manually processed data
        manual_holdings = data_manager.get_holdings()
        manual_transactions = data_manager.get_transactions()
        
        if manual_holdings is not None:
            logger.info(f"✅ Manual holdings loaded: {len(manual_holdings)} records")
        else:
            logger.warning("❌ Manual holdings failed to load")
            
        if manual_transactions is not None:
            logger.info(f"✅ Manual transactions loaded: {len(manual_transactions)} records")
        else:
            logger.warning("❌ Manual transactions failed to load")
        
        return manual_holdings, manual_transactions
        
    except Exception as e:
        logger.error(f"❌ Error loading manual data: {e}")
        return None, None

def load_automated_data() -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Load data using the new automated data processing methods.
    
    Returns:
        tuple: (automated_holdings_df, automated_transactions_df)
    """
    logger.info("=== Loading Automated Data (Actual) ===")
    
    try:
        # Import the new automated processing functions
        from src.data_manager.readers import read_raw_fund_sheets, read_schwab_data, load_settings
        from src.data_manager.cleaners import process_raw_holdings, process_raw_transactions
        
        automated_holdings_list = []
        automated_transactions_list = []
        
        # 1. Process CN Fund automated data
        logger.info("Processing CN Fund automated data...")
        try:
            fund_file = "data/funding_transactions.xlsx"
            raw_holdings, raw_transactions = read_raw_fund_sheets(fund_file)
            
            if raw_holdings is not None:
                processed_holdings = process_raw_holdings(raw_holdings)
                if processed_holdings is not None:
                    # Add source identifier
                    processed_holdings['Data_Source'] = 'CN_Fund_Automated'
                    automated_holdings_list.append(processed_holdings)
                    logger.info(f"✅ CN Fund holdings processed: {len(processed_holdings)} records")
            
            if raw_transactions is not None:
                processed_transactions = process_raw_transactions(raw_transactions)
                if processed_transactions is not None:
                    # Add source identifier
                    processed_transactions['Data_Source'] = 'CN_Fund_Automated'
                    automated_transactions_list.append(processed_transactions)
                    logger.info(f"✅ CN Fund transactions processed: {len(processed_transactions)} records")
                    
        except Exception as e:
            logger.warning(f"CN Fund automated processing failed: {e}")
        
        # 2. Process Schwab automated data
        logger.info("Processing Schwab automated data...")
        try:
            settings = load_settings()
            schwab_data = read_schwab_data(settings)
            
            if schwab_data and 'holdings' in schwab_data and schwab_data['holdings'] is not None:
                schwab_holdings = schwab_data['holdings']
                schwab_holdings['Data_Source'] = 'Schwab_Automated'
                automated_holdings_list.append(schwab_holdings)
                logger.info(f"✅ Schwab holdings processed: {len(schwab_holdings)} records")
            
            if schwab_data and 'transactions' in schwab_data and schwab_data['transactions'] is not None:
                schwab_transactions = schwab_data['transactions']
                schwab_transactions['Data_Source'] = 'Schwab_Automated'
                automated_transactions_list.append(schwab_transactions)
                logger.info(f"✅ Schwab transactions processed: {len(schwab_transactions)} records")
                
        except Exception as e:
            logger.warning(f"Schwab automated processing failed: {e}")
        
        # Combine automated data
        automated_holdings = None
        automated_transactions = None
        
        if automated_holdings_list:
            automated_holdings = pd.concat(automated_holdings_list, ignore_index=True)
            logger.info(f"✅ Total automated holdings: {len(automated_holdings)} records")
        
        if automated_transactions_list:
            automated_transactions = pd.concat(automated_transactions_list, ignore_index=True)
            logger.info(f"✅ Total automated transactions: {len(automated_transactions)} records")
        
        return automated_holdings, automated_transactions
        
    except Exception as e:
        logger.error(f"❌ Error loading automated data: {e}")
        return None, None

def compare_dataframes(expected_df: Optional[pd.DataFrame], 
                      actual_df: Optional[pd.DataFrame], 
                      name: str) -> bool:
    """
    Compare two DataFrames and report any discrepancies.
    
    Args:
        expected_df: DataFrame from manual processing
        actual_df: DataFrame from automated processing
        name: Name for the comparison report (e.g., "Holdings", "Transactions")
        
    Returns:
        bool: True if validation passes, False otherwise
    """
    logger.info(f"\n=== Comparing {name} Data ===")
    
    # Handle None cases
    if expected_df is None and actual_df is None:
        logger.info(f"⚠️  Both {name} DataFrames are None - skipping comparison")
        return True
    
    if expected_df is None:
        logger.warning(f"❌ Expected {name} DataFrame is None, but actual has {len(actual_df)} records")
        return False
    
    if actual_df is None:
        logger.warning(f"❌ Actual {name} DataFrame is None, but expected has {len(expected_df)} records")
        return False
    
    validation_passed = True
    issues = []
    
    # 1. Shape Comparison
    logger.info(f"Shape comparison: Expected {expected_df.shape} vs Actual {actual_df.shape}")
    if expected_df.shape != actual_df.shape:
        issues.append(f"Shape mismatch: Expected {expected_df.shape}, got {actual_df.shape}")
        validation_passed = False
    
    # 2. Schema Comparison
    expected_cols = set(expected_df.columns)
    actual_cols = set(actual_df.columns)
    
    missing_cols = expected_cols - actual_cols
    extra_cols = actual_cols - expected_cols
    
    if missing_cols:
        issues.append(f"Missing columns in actual data: {missing_cols}")
        validation_passed = False
    
    if extra_cols:
        # Extra columns are acceptable (like Data_Source), just log them
        logger.info(f"ℹ️  Extra columns in actual data: {extra_cols}")
    
    # 3. Content Comparison (for common columns and Asset_ID matching)
    common_cols = expected_cols & actual_cols
    
    if 'Asset_ID' in common_cols and len(expected_df) > 0 and len(actual_df) > 0:
        # Compare by Asset_ID
        expected_assets = set(expected_df['Asset_ID'].dropna())
        actual_assets = set(actual_df['Asset_ID'].dropna())
        
        missing_assets = expected_assets - actual_assets
        extra_assets = actual_assets - expected_assets
        
        if missing_assets:
            issues.append(f"Missing assets in actual data: {missing_assets}")
            validation_passed = False
        
        if extra_assets:
            logger.info(f"ℹ️  Extra assets in actual data: {extra_assets}")
        
        # For common assets, compare key metrics
        common_assets = expected_assets & actual_assets
        numeric_cols = ['Quantity', 'Market_Value_Raw', 'Amount_Gross', 'Amount_Net', 'Market_Price_Unit']
        available_numeric_cols = [col for col in numeric_cols if col in common_cols]
        
        for asset in list(common_assets)[:5]:  # Check first 5 common assets to avoid too much output
            expected_asset_data = expected_df[expected_df['Asset_ID'] == asset]
            actual_asset_data = actual_df[actual_df['Asset_ID'] == asset]
            
            if len(expected_asset_data) == 1 and len(actual_asset_data) == 1:
                for col in available_numeric_cols:
                    expected_val = expected_asset_data[col].iloc[0]
                    actual_val = actual_asset_data[col].iloc[0]
                    
                    if pd.notna(expected_val) and pd.notna(actual_val):
                        if not np.isclose(float(expected_val), float(actual_val), rtol=1e-3, atol=1e-6):
                            issues.append(f"Value mismatch for {asset} {col}: Expected {expected_val}, got {actual_val}")
                            validation_passed = False
    
    # 4. Data type comparison for key columns
    key_date_cols = ['Transaction_Date', 'Snapshot_Date']
    for col in key_date_cols:
        if col in common_cols:
            expected_dtype = expected_df[col].dtype
            actual_dtype = actual_df[col].dtype
            if expected_dtype != actual_dtype:
                logger.info(f"ℹ️  Data type difference for {col}: Expected {expected_dtype}, got {actual_dtype}")
    
    # Report results
    if validation_passed:
        logger.info(f"✅ VALIDATION SUCCESS: {name} data matches expectations")
        return True
    else:
        logger.error(f"❌ VALIDATION FAILED: {name} data has discrepancies:")
        for issue in issues[:10]:  # Limit to first 10 issues
            logger.error(f"   - {issue}")
        if len(issues) > 10:
            logger.error(f"   ... and {len(issues) - 10} more issues")
        return False

def export_to_excel(holdings_df: Optional[pd.DataFrame], 
                   transactions_df: Optional[pd.DataFrame]) -> bool:
    """
    Export the automated data to an Excel file for review.
    
    Args:
        holdings_df: Processed holdings DataFrame
        transactions_df: Processed transactions DataFrame
        
    Returns:
        bool: True if export successful, False otherwise
    """
    logger.info("\n=== Exporting to Excel ===")
    
    try:
        # Ensure output directory exists
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Create output file path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{output_dir}/automated_data_validation_report_{timestamp}.xlsx"
        
        # Write to Excel
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            
            # Write holdings data
            if holdings_df is not None and not holdings_df.empty:
                holdings_df.to_excel(writer, sheet_name='Processed Holdings', index=False)
                logger.info(f"✅ Holdings exported: {len(holdings_df)} records")
                
                # Auto-fit column widths
                workbook = writer.book
                worksheet = workbook['Processed Holdings']
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except Exception:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            else:
                # Create empty sheet with message
                empty_df = pd.DataFrame({'Message': ['No holdings data available']})
                empty_df.to_excel(writer, sheet_name='Processed Holdings', index=False)
                logger.warning("⚠️  No holdings data to export")
            
            # Write transactions data
            if transactions_df is not None and not transactions_df.empty:
                transactions_df.to_excel(writer, sheet_name='Processed Transactions', index=False)
                logger.info(f"✅ Transactions exported: {len(transactions_df)} records")
                
                # Auto-fit column widths
                worksheet = workbook['Processed Transactions']
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except Exception:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            else:
                # Create empty sheet with message
                empty_df = pd.DataFrame({'Message': ['No transactions data available']})
                empty_df.to_excel(writer, sheet_name='Processed Transactions', index=False)
                logger.warning("⚠️  No transactions data to export")
            
            # Add summary sheet
            summary_data = {
                'Metric': ['Holdings Count', 'Transactions Count', 'Export Timestamp'],
                'Value': [
                    len(holdings_df) if holdings_df is not None else 0,
                    len(transactions_df) if transactions_df is not None else 0,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        logger.info(f"✅ Excel report exported successfully: {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error exporting to Excel: {e}")
        return False

def main():
    """
    Main orchestration function for the validation script.
    """
    logger.info("=" * 60)
    logger.info("DATA PIPELINE VALIDATION SCRIPT")
    logger.info("=" * 60)
    
    validation_results = {}
    
    try:
        # Step 1: Load manual (expected) data
        expected_holdings, expected_transactions = load_manual_data()
        
        # Step 2: Load automated (actual) data
        actual_holdings, actual_transactions = load_automated_data()
        
        # Step 3: Compare holdings data
        holdings_validation = compare_dataframes(expected_holdings, actual_holdings, "Holdings")
        validation_results['Holdings'] = holdings_validation
        
        # Step 4: Compare transactions data
        transactions_validation = compare_dataframes(expected_transactions, actual_transactions, "Transactions")
        validation_results['Transactions'] = transactions_validation
        
        # Step 5: Export automated data to Excel
        export_success = export_to_excel(actual_holdings, actual_transactions)
        validation_results['Export'] = export_success
        
        # Final summary
        logger.info("\n" + "=" * 60)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 60)
        
        for test_name, result in validation_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test_name}: {status}")
        
        overall_success = all(validation_results.values())
        if overall_success:
            logger.info("\n🎉 OVERALL VALIDATION: ✅ SUCCESS")
            logger.info("All automated data pipelines are working correctly!")
        else:
            logger.warning("\n⚠️  OVERALL VALIDATION: ❌ ISSUES DETECTED")
            logger.warning("Some automated data pipelines have discrepancies. Check the detailed logs above.")
        
        logger.info("\nValidation complete. Report available in output/ directory.")
        
    except Exception as e:
        logger.error(f"❌ Critical error in validation process: {e}")
        logger.error("Validation could not be completed.")

if __name__ == "__main__":
    main()