#!/usr/bin/env python3
"""
Create Quarterly Historical Snapshots from Actual Balance Sheet Data

This script creates quarterly holdings snapshots spanning 36-48 months using 
actual balance sheet data from Financial Summary_new.xlsx.

Focus: Generate proper historical test data to enable multi-timeframe analysis
"""

import sys
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_holdings_from_balance_sheet(balance_row, snapshot_date):
    """
    Create holdings records from a balance sheet row.
    
    Args:
        balance_row: Single row from balance sheet DataFrame
        snapshot_date: Date for the snapshot
        
    Returns:
        List of holding records
    """
    holdings = []
    
    # Define major asset categories from balance sheet
    asset_mappings = {
        # Cash and Deposits (CNY)
        'Asset_Cash_CNY': {'name': 'Cash_CNY', 'type': 'Cash'},
        'Asset_Bank_Account_A': {'name': 'BOC_Deposit_CNY', 'type': 'Deposit'},
        'Asset_Deposit_CMB_CNY': {'name': 'CMB_Deposit_CNY', 'type': 'Deposit'},
        'Asset_Deposit_BOB_CNY': {'name': 'BOB_Deposit_CNY', 'type': 'Deposit'},
        
        # Deposits (USD converted to CNY)
        'Asset_Deposit_Chase_CNY': {'name': 'Chase_Deposit_USD', 'type': 'Deposit'},
        'Asset_Deposit_Discover_CNY': {'name': 'Discover_Deposit_USD', 'type': 'Deposit'},
        
        # Investment Assets
        'Asset_Invest_Funds_Value_CNY': {'name': 'Funds_Portfolio', 'type': 'Fund'},
        'Asset_Invest_USFund_Value_CNY': {'name': 'US_Fund_Portfolio', 'type': 'US_Fund'},
        'Asset_Invest_RSU_Value_CNY': {'name': 'Employer_Stock_A', 'type': 'RSU'},
        'Asset_Invest_Gold_Value_CNY': {'name': 'Gold_Holdings', 'type': 'Gold'},
        'Asset_Insurance_Cash_CNY': {'name': 'Insurance_Cash_Value', 'type': 'Insurance'},
        'Asset_Property_Lanjun_CNY': {'name': 'Property_Residential_A', 'type': 'Property'},
        
        # Optional assets (if present)
        'Asset_Invest_BankWealth_Value_CNY': {'name': 'Bank_Wealth', 'type': 'Bank_Product'},
        'Asset_Invest_Pension_Value_CNY': {'name': 'Pension_Fund', 'type': 'Pension'},
    }
    
    snapshot_ts = pd.Timestamp(snapshot_date)
    
    for col_name, asset_info in asset_mappings.items():
        if col_name in balance_row.index:
            value = balance_row[col_name]
            
            # Skip if value is NaN, 0, or very small
            if pd.isna(value) or abs(value) < 1:
                continue
                
            holding = {
                'Snapshot_Date': snapshot_ts,
                'Asset_ID': asset_info['name'],
                'Asset_Name': asset_info['name'],
                'Asset_Type_Raw': asset_info['type'],
                'Quantity': 1.0,  # For value-based assets like real estate, cash
                'Unit': 'Value',
                'Cost_Price_Unit': float('nan'),
                'Market_Price_Unit': float(value),
                'Market_Value_Raw': float(value),
                'Currency': 'CNY',
                'Account': float('nan'),
                'Insurance_CashValue_CNY': float('nan'),
                'FX_Rate': 0.0,  # Already converted to CNY
                'Market_Value_CNY': float(value),
                'Created_At': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'DataManager_Version': '1.2'
            }
            
            holdings.append(holding)
    
    return holdings

def main():
    """Main execution function."""
    print("🔧 Creating Quarterly Historical Snapshots from Actual Data")
    print("=" * 60)
    
    try:
        # Initialize DataManager to get balance sheet data
        from .manager import DataManager
        
        logger.info("Initializing DataManager to access balance sheet data...")
        # Get config path relative to this module's location
        current_dir = Path(__file__).parent
        config_path = current_dir.parent.parent / 'config' / 'settings.yaml'
        dm = DataManager(str(config_path))
        balance_sheet = dm.get_balance_sheet()
        
        logger.info(f"Balance sheet loaded: {balance_sheet.shape}")
        logger.info(f"Date range: {balance_sheet.index.min()} to {balance_sheet.index.max()}")
        
        # Generate quarterly dates over the last 48 months
        end_date = balance_sheet.index.max()
        start_date = end_date - pd.DateOffset(months=48)
        
        logger.info(f"Target period: {start_date} to {end_date}")
        
        # Create quarterly date range
        quarterly_dates = pd.date_range(
            start=start_date,
            end=end_date,
            freq='QE'  # Quarter end
        )
        
        logger.info(f"Generating {len(quarterly_dates)} quarterly snapshots")
        logger.info(f"Date range: {quarterly_dates[0]} to {quarterly_dates[-1]}")
        
        # Prepare output directory
        output_dir = Path('data/historical_snapshots')
        output_dir.mkdir(exist_ok=True)
        
        snapshots_created = 0
        
        for target_date in quarterly_dates:
            # Find closest available balance sheet data
            available_dates = balance_sheet.index
            closest_dates = available_dates[available_dates <= target_date]
            
            if len(closest_dates) == 0:
                logger.warning(f"No data available for {target_date.strftime('%Y-%m-%d')}")
                continue
                
            closest_date = closest_dates.max()
            logger.info(f"Creating snapshot for {target_date.strftime('%Y-%m-%d')} using data from {closest_date.strftime('%Y-%m-%d')}")
            
            # Get balance sheet row
            balance_row = balance_sheet.loc[closest_date]
            
            # Create holdings from balance sheet
            holdings_data = create_holdings_from_balance_sheet(balance_row, target_date)
            
            if not holdings_data:
                logger.warning(f"No holdings created for {target_date.strftime('%Y-%m-%d')}")
                continue
            
            # Convert to DataFrame
            holdings_df = pd.DataFrame(holdings_data)
            
            # Create filename
            snapshot_filename = f"holdings_snapshot_{target_date.strftime('%Y%m%d')}.xlsx"
            snapshot_path = output_dir / snapshot_filename
            
            # Save to Excel (matching existing format)
            with pd.ExcelWriter(snapshot_path, engine='openpyxl') as writer:
                holdings_df.to_excel(writer, sheet_name='Holdings_Snapshot', index=False)
            
            logger.info(f"✅ Created: {snapshot_filename} ({len(holdings_data)} holdings)")
            snapshots_created += 1
        
        print("=" * 60)
        print(f"✅ SUCCESS: Created {snapshots_created} quarterly snapshots")
        print(f"📁 Location: {output_dir.absolute()}")
        print(f"📅 Coverage: {quarterly_dates[0].strftime('%Y-%m-%d')} to {quarterly_dates[-1].strftime('%Y-%m-%d')}")
        print(f"⏱️  Span: {len(quarterly_dates)} quarters ({len(quarterly_dates)*3} months)")
        
        if snapshots_created >= 12:  # 3+ years
            print("🎉 Excellent! Now you have sufficient historical data for multi-timeframe analysis!")
        else:
            print("⚠️  Limited snapshots created - may need more historical balance sheet data")
            
    except Exception as e:
        logger.error(f"Script failed: {e}")
        import traceback
        traceback.print_exc()
        print(f"\n❌ FAILED: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
