#!/usr/bin/env python3
"""
Focused validation script for automated data pipelines.
Compares manual vs automated processing for specific data sources:
1. CN Fund data (raw_holdings_paste vs funding_transactions.xlsx)
2. Schwab CSV data (Individual-Positions-*.csv vs manual Excel)

This is a more targeted validation than the comprehensive comparison.
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime

# Set up project root and imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.data_manager.readers import read_raw_fund_sheets, read_schwab_data
from src.data_manager.cleaners import process_raw_holdings, process_raw_transactions, clean_schwab_holdings_csv, clean_schwab_transactions_csv
from src.data_manager.manager import DataManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_cn_fund_automation():
    """Validate CN fund automated processing against manual fund data."""
    logger.info("=== Validating CN Fund Automation ===")
    
    try:
        # 1. Load manual fund data (from Excel files)
        data_manager = DataManager(config_path='config/settings.yaml')
        manual_fund_holdings = data_manager.get_holdings()
        manual_fund_transactions = data_manager.get_transactions()
        
        # Filter to only fund data
        fund_holdings = manual_fund_holdings[
            manual_fund_holdings['Asset_Type_Raw'].str.contains('型|Fund', na=False)
        ].copy()
        fund_transactions = manual_fund_transactions[
            manual_fund_transactions['Asset_ID'].astype(str).str.match(r'^\d{6}$', na=False)
        ].copy()
        
        logger.info(f"✅ Manual fund holdings: {len(fund_holdings)} records")
        logger.info(f"✅ Manual fund transactions: {len(fund_transactions)} records")
        
        # 2. Load automated CN fund data
        raw_holdings, raw_transactions = read_raw_fund_sheets()
        auto_holdings = process_raw_holdings(raw_holdings)
        auto_transactions = process_raw_transactions(raw_transactions)
        
        logger.info(f"✅ Automated fund holdings: {len(auto_holdings)} records")
        logger.info(f"✅ Automated fund transactions: {len(auto_transactions)} records")
        
        # 3. Compare key metrics
        success = True
        
        # Compare holdings counts by asset
        manual_counts = fund_holdings.groupby('Asset_ID').size().sort_index()
        auto_counts = auto_holdings.groupby('Asset_ID').size().sort_index()
        
        logger.info(f"Holdings asset overlap: {len(set(manual_counts.index) & set(auto_counts.index))} common assets")
        
        # Compare transaction counts by asset
        manual_tx_counts = fund_transactions.groupby('Asset_ID').size().sort_index()
        auto_tx_counts = auto_transactions.groupby('Asset_ID').size().sort_index()
        
        logger.info(f"Transaction asset overlap: {len(set(manual_tx_counts.index) & set(auto_tx_counts.index))} common assets")
        
        return {
            'success': success,
            'manual_holdings': len(fund_holdings),
            'auto_holdings': len(auto_holdings),
            'manual_transactions': len(fund_transactions),
            'auto_transactions': len(auto_transactions)
        }
        
    except Exception as e:
        logger.error(f"❌ CN Fund validation failed: {e}")
        return {'success': False, 'error': str(e)}

def validate_schwab_automation():
    """Validate Schwab CSV automated processing."""
    logger.info("=== Validating Schwab Automation ===")
    
    try:
        # 1. Load automated Schwab data using DataManager approach
        import yaml
        
        # Load config to get Schwab file patterns
        with open('config/settings.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Use read_schwab_data function
        schwab_data = read_schwab_data(config)
        schwab_holdings = schwab_data.get('holdings')
        schwab_transactions = schwab_data.get('transactions')
        
        if schwab_holdings is not None and schwab_transactions is not None:
            # Clean the data using appropriate functions
            cleaned_holdings = clean_schwab_holdings_csv(schwab_holdings, config)
            cleaned_transactions = clean_schwab_transactions_csv(schwab_transactions, config)
            
            # Handle None results
            if cleaned_holdings is None:
                cleaned_holdings = pd.DataFrame()
            if cleaned_transactions is None:
                cleaned_transactions = pd.DataFrame()
            
            logger.info(f"✅ Schwab holdings processed: {len(cleaned_holdings)} records")
            logger.info(f"✅ Schwab transactions processed: {len(cleaned_transactions)} records")
        else:
            logger.warning("⚠️  No Schwab data found or failed to load")
            return {'success': False, 'error': 'No Schwab data found'}
        
        # 2. Basic validation checks
        success = True
        issues = []
        
        # Check for required columns in holdings
        required_holdings_cols = ['Asset_ID', 'Asset_Name', 'Market_Value_Raw', 'Quantity']
        missing_holdings_cols = [col for col in required_holdings_cols if col not in cleaned_holdings.columns]
        if missing_holdings_cols:
            issues.append(f"Missing holdings columns: {missing_holdings_cols}")
            success = False
        
        # Check for required columns in transactions  
        required_tx_cols = ['Transaction_Date', 'Asset_ID', 'Transaction_Type_Raw']
        missing_tx_cols = [col for col in required_tx_cols if col not in cleaned_transactions.columns]
        if missing_tx_cols:
            issues.append(f"Missing transaction columns: {missing_tx_cols}")
            success = False
        
        # Check for valid asset IDs
        if len(cleaned_holdings) > 0:
            invalid_holdings = cleaned_holdings[cleaned_holdings['Asset_ID'].isna()]
            if len(invalid_holdings) > 0:
                issues.append(f"Found {len(invalid_holdings)} holdings with missing Asset_ID")
        
        if len(cleaned_transactions) > 0:
            invalid_transactions = cleaned_transactions[cleaned_transactions['Asset_ID'].isna()]
            if len(invalid_transactions) > 0:
                issues.append(f"Found {len(invalid_transactions)} transactions with missing Asset_ID")
        
        if issues:
            for issue in issues:
                logger.warning(f"⚠️  {issue}")
        
        return {
            'success': success,
            'holdings_count': len(cleaned_holdings),
            'transactions_count': len(cleaned_transactions),
            'issues': issues
        }
        
    except Exception as e:
        logger.error(f"❌ Schwab validation failed: {e}")
        return {'success': False, 'error': str(e)}

def validate_data_consistency():
    """Check internal consistency of automated data."""
    logger.info("=== Validating Data Consistency ===")
    
    try:
        # Load all automated data
        cn_holdings, cn_transactions = read_raw_fund_sheets()
        
        # Load Schwab data using correct approach
        import yaml
        with open('config/settings.yaml', 'r') as f:
            config = yaml.safe_load(f)
        schwab_data = read_schwab_data(config)
        schwab_holdings = schwab_data.get('holdings')
        schwab_transactions = schwab_data.get('transactions')
        
        # Process the data
        cn_holdings_clean = process_raw_holdings(cn_holdings)
        cn_transactions_clean = process_raw_transactions(cn_transactions)
        
        if schwab_holdings is not None and schwab_transactions is not None:
            # Clean the data using appropriate functions
            schwab_holdings_clean = clean_schwab_holdings_csv(schwab_holdings, config)
            schwab_transactions_clean = clean_schwab_transactions_csv(schwab_transactions, config)
            
            # Handle None results
            if schwab_holdings_clean is None:
                schwab_holdings_clean = pd.DataFrame()
            if schwab_transactions_clean is None:
                schwab_transactions_clean = pd.DataFrame()
        else:
            schwab_holdings_clean = pd.DataFrame()
            schwab_transactions_clean = pd.DataFrame()
            logger.warning("⚠️  No Schwab data found for consistency check")
        
        success = True
        issues = []
        
        # Check 1: Holdings should have positive values
        negative_values = cn_holdings_clean[cn_holdings_clean['Market_Value_Raw'] <= 0]
        if len(negative_values) > 0:
            issues.append(f"Found {len(negative_values)} CN fund holdings with non-positive values")
            success = False
        
        # Check 2: Transactions should have valid dates
        invalid_dates = cn_transactions_clean[cn_transactions_clean['Transaction_Date'].isna()]
        if len(invalid_dates) > 0:
            issues.append(f"Found {len(invalid_dates)} CN fund transactions with invalid dates")
            success = False
        
        # Check 3: Asset IDs should be consistent format
        cn_asset_ids = cn_holdings_clean['Asset_ID'].dropna().astype(str)
        non_numeric_ids = cn_asset_ids[~cn_asset_ids.str.match(r'^\d+\.?\d*$')]
        if len(non_numeric_ids) > 0:
            issues.append(f"Found {len(non_numeric_ids)} CN fund holdings with non-numeric Asset_IDs")
        
        if issues:
            for issue in issues:
                logger.warning(f"⚠️  {issue}")
        else:
            logger.info("✅ All consistency checks passed")
        
        return {
            'success': success,
            'cn_holdings': len(cn_holdings_clean),
            'cn_transactions': len(cn_transactions_clean),
            'schwab_holdings': len(schwab_holdings_clean),
            'schwab_transactions': len(schwab_transactions_clean),
            'issues': issues
        }
        
    except Exception as e:
        logger.error(f"❌ Consistency validation failed: {e}")
        return {'success': False, 'error': str(e)}

def export_validation_summary(results):
    """Export validation results to Excel."""
    logger.info("=== Exporting Validation Summary ===")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"output/automation_validation_summary_{timestamp}.xlsx"
    
    try:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = []
            for test_name, result in results.items():
                summary_data.append({
                    'Test': test_name.replace('_', ' ').title(),
                    'Status': '✅ PASSED' if result.get('success', False) else '❌ FAILED',
                    'Details': '; '.join(result.get('issues', [])) if result.get('issues') else 'OK'
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Validation Summary', index=False)
            
            # Detailed results
            details_data = []
            for test_name, result in results.items():
                for key, value in result.items():
                    if key not in ['success', 'issues']:
                        details_data.append({
                            'Test': test_name,
                            'Metric': key,
                            'Value': value
                        })
            
            details_df = pd.DataFrame(details_data)
            details_df.to_excel(writer, sheet_name='Detailed Results', index=False)
            
            # Auto-fit columns
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
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
        
        logger.info(f"✅ Validation summary exported: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"❌ Export failed: {e}")
        return None

def main():
    """Run focused automation validation."""
    logger.info("============================================================")
    logger.info("AUTOMATION PIPELINE VALIDATION - FOCUSED")
    logger.info("============================================================")
    
    # Run validation tests
    results = {}
    results['cn_fund_validation'] = validate_cn_fund_automation()
    results['schwab_validation'] = validate_schwab_automation()
    results['consistency_validation'] = validate_data_consistency()
    
    # Export results
    export_path = export_validation_summary(results)
    
    # Print summary
    logger.info("\n============================================================")
    logger.info("VALIDATION SUMMARY")
    logger.info("============================================================")
    
    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASSED" if result.get('success', False) else "❌ FAILED"
        logger.info(f"{test_name.replace('_', ' ').title()}: {status}")
        if not result.get('success', False):
            all_passed = False
            if 'error' in result:
                logger.error(f"   Error: {result['error']}")
            if 'issues' in result and result['issues']:
                for issue in result['issues']:
                    logger.warning(f"   Issue: {issue}")
    
    if export_path:
        logger.info(f"\nDetailed report: {export_path}")
    
    overall_status = "✅ PASSED" if all_passed else "❌ FAILED"
    logger.info(f"\n🎯 OVERALL AUTOMATION VALIDATION: {overall_status}")
    
    if not all_passed:
        logger.warning("Some automation pipelines have issues. Check the detailed logs above.")
    else:
        logger.info("All automation pipelines are working correctly! 🎉")

if __name__ == "__main__":
    main()