#!/usr/bin/env python3
"""
Data Quality Audit Script - Validates transaction files before migration.
Compares balance sheet static values vs transaction-derived holdings.

Created: 2025-11-04
Purpose: Pre-migration validation and discrepancy report

Usage:
    python scripts/audit_transaction_completeness.py
    Output: output/data_quality_audit_report.json
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.data_manager.manager import DataManager


def audit_cn_funds(dm: DataManager) -> Dict:
    """Audit CN Fund transaction data completeness"""
    print("\n🔍 Auditing CN Funds...")
    
    holdings = dm.get_holdings()
    transactions = dm.get_transactions()
    balance_sheet = dm.get_balance_sheet()
    
    # Filter CN Fund data (6-digit fund codes)
    fund_holdings = holdings[holdings.index.get_level_values('Asset_ID').str.isdigit() & 
                              (holdings.index.get_level_values('Asset_ID').str.len() == 6)]
    fund_txns = transactions[transactions['Asset_ID'].str.isdigit() & 
                             (transactions['Asset_ID'].str.len() == 6)]
    
    # Calculate total value from transaction-based holdings
    transaction_total = fund_holdings['Market_Value_CNY'].sum()
    
    # Get balance sheet value for comparison
    bs_value = None
    if 'Asset_Invest_FundA_Value' in balance_sheet.columns:
        bs_value = balance_sheet['Asset_Invest_FundA_Value'].iloc[-1]
    
    # Calculate holdings from transactions
    calculated_holdings = fund_txns.groupby('Asset_ID')['Quantity'].sum()
    
    # Compare to actual holdings
    discrepancies = []
    for asset_id in fund_holdings.index.get_level_values('Asset_ID').unique():
        try:
            actual_data = fund_holdings.xs(asset_id, level='Asset_ID')
            actual = actual_data['Quantity'].iloc[-1]
            calculated = calculated_holdings.get(asset_id, 0)
            diff_pct = abs((calculated - actual) / actual * 100) if actual else 0
            
            if diff_pct > 1.0:  # >1% discrepancy
                discrepancies.append({
                    'asset_id': asset_id,
                    'asset_name': actual_data['Asset_Name'].iloc[0],
                    'actual_qty': float(actual),
                    'calculated_qty': float(calculated),
                    'diff_pct': float(diff_pct),
                    'market_value_cny': float(actual_data['Market_Value_CNY'].iloc[0])
                })
        except Exception as e:
            print(f"  ⚠️  Error processing fund {asset_id}: {e}")
    
    status = 'PASS' if not discrepancies else 'WARNING'
    
    result = {
        'asset_type': 'CN_Funds',
        'total_assets': len(fund_holdings.index.get_level_values('Asset_ID').unique()),
        'total_transactions': len(fund_txns),
        'transaction_total_value': float(transaction_total),
        'balance_sheet_value': float(bs_value) if pd.notna(bs_value) else None,
        'value_diff_pct': float(abs((transaction_total - bs_value) / bs_value * 100)) if bs_value and pd.notna(bs_value) else None,
        'discrepancies': discrepancies,
        'status': status
    }
    
    print(f"  ✓ Found {result['total_assets']} CN Fund assets")
    print(f"  ✓ Transaction total: ¥{transaction_total:,.2f}")
    if bs_value and pd.notna(bs_value):
        print(f"  ✓ Balance sheet value: ¥{bs_value:,.2f}")
        print(f"  ✓ Difference: {result['value_diff_pct']:.2f}%")
    print(f"  ✓ Status: {status}")
    
    return result


def audit_schwab_holdings(dm: DataManager) -> Dict:
    """Audit Schwab transaction data completeness"""
    print("\n🔍 Auditing Schwab Holdings...")
    
    holdings = dm.get_holdings()
    transactions = dm.get_transactions()
    balance_sheet = dm.get_balance_sheet()
    
    # Filter Schwab data (USD currency + known tickers)
    schwab_tickers = ['AMZN', 'VOO', 'VTI', 'BND', 'VEA', 'VXUS']
    schwab_holdings = holdings[holdings.index.get_level_values('Asset_ID').isin(schwab_tickers)]
    schwab_txns = transactions[transactions['Asset_ID'].isin(schwab_tickers)]
    
    # Check for placeholder
    placeholder_holdings = holdings[holdings.index.get_level_values('Asset_ID').str.contains('Fund_US_Placeholder', na=False)]
    has_placeholder = not placeholder_holdings.empty
    
    # Calculate total value from transaction-based holdings
    transaction_total_usd = schwab_holdings['Market_Value_Raw'].sum() if not schwab_holdings.empty else 0
    transaction_total_cny = schwab_holdings['Market_Value_CNY'].sum() if not schwab_holdings.empty else 0
    
    # Get balance sheet value for comparison
    bs_value_usd = None
    if 'Asset_Invest_USFund_Value_USD' in balance_sheet.columns:
        bs_value_usd = balance_sheet['Asset_Invest_USFund_Value_USD'].iloc[-1]
    
    status = 'PASS' if not has_placeholder and len(schwab_holdings) > 0 else 'WARNING'
    
    result = {
        'asset_type': 'Schwab_US_Investments',
        'total_assets': len(schwab_holdings.index.get_level_values('Asset_ID').unique()),
        'total_transactions': len(schwab_txns),
        'transaction_total_value_usd': float(transaction_total_usd),
        'transaction_total_value_cny': float(transaction_total_cny),
        'balance_sheet_value_usd': float(bs_value_usd) if pd.notna(bs_value_usd) else None,
        'value_diff_pct': float(abs((transaction_total_usd - bs_value_usd) / bs_value_usd * 100)) if bs_value_usd and pd.notna(bs_value_usd) else None,
        'has_placeholder': has_placeholder,
        'status': status
    }
    
    print(f"  ✓ Found {result['total_assets']} Schwab assets")
    print(f"  ✓ Transaction total: ${transaction_total_usd:,.2f} (¥{transaction_total_cny:,.2f})")
    if bs_value_usd and pd.notna(bs_value_usd):
        print(f"  ✓ Balance sheet value: ${bs_value_usd:,.2f}")
        print(f"  ✓ Difference: {result['value_diff_pct']:.2f}%")
    if has_placeholder:
        print(f"  ⚠️  WARNING: Found placeholder 'Fund_US_Placeholder' - indicates balance sheet source")
    print(f"  ✓ Status: {status}")
    
    return result


def audit_gold_holdings(dm: DataManager) -> Dict:
    """Audit Gold transaction data completeness"""
    print("\n🔍 Auditing Gold Holdings...")
    
    holdings = dm.get_holdings()
    transactions = dm.get_transactions()
    balance_sheet = dm.get_balance_sheet()
    
    # Filter Gold data
    gold_holdings = holdings[holdings.index.get_level_values('Asset_ID').str.contains('Gold|gold', case=False, na=False)]
    gold_txns = transactions[transactions['Asset_ID'].str.contains('Gold|gold', case=False, na=False)]
    
    # Calculate total value from transaction-based holdings
    transaction_total = gold_holdings['Market_Value_CNY'].sum() if not gold_holdings.empty else 0
    
    # Get balance sheet value for comparison
    bs_value = None
    if 'Asset_Invest_Gold_Value' in balance_sheet.columns:
        bs_value = balance_sheet['Asset_Invest_Gold_Value'].iloc[-1]
    
    # Check units
    correct_units = gold_holdings['Unit'].isin(['Gram', 'Shares']).all() if not gold_holdings.empty else True
    
    status = 'PASS' if correct_units and len(gold_holdings) > 0 else 'WARNING'
    
    result = {
        'asset_type': 'Gold_Holdings',
        'total_assets': len(gold_holdings.index.get_level_values('Asset_ID').unique()),
        'total_transactions': len(gold_txns),
        'transaction_total_value': float(transaction_total),
        'balance_sheet_value': float(bs_value) if pd.notna(bs_value) else None,
        'value_diff_pct': float(abs((transaction_total - bs_value) / bs_value * 100)) if bs_value and pd.notna(bs_value) else None,
        'correct_units': bool(correct_units),  # Convert numpy.bool_ to Python bool
        'status': status
    }
    
    print(f"  ✓ Found {result['total_assets']} Gold assets")
    print(f"  ✓ Transaction total: ¥{transaction_total:,.2f}")
    if bs_value and pd.notna(bs_value):
        print(f"  ✓ Balance sheet value: ¥{bs_value:,.2f}")
        print(f"  ✓ Difference: {result['value_diff_pct']:.2f}%")
    print(f"  ✓ Correct units (Gram/Shares): {correct_units}")
    print(f"  ✓ Status: {status}")
    
    return result


def audit_rsu_holdings(dm: DataManager) -> Dict:
    """Audit RSU transaction data completeness"""
    print("\n🔍 Auditing RSU Holdings...")
    
    holdings = dm.get_holdings()
    transactions = dm.get_transactions()
    balance_sheet = dm.get_balance_sheet()
    
    # Filter RSU data
    rsu_holdings = holdings[holdings.index.get_level_values('Asset_ID').str.contains('RSU', na=False)]
    rsu_txns = transactions[transactions['Asset_ID'].str.contains('RSU', na=False)]
    
    # Calculate total value from transaction-based holdings
    transaction_total_usd = rsu_holdings['Market_Value_Raw'].sum() if not rsu_holdings.empty else 0
    transaction_total_cny = rsu_holdings['Market_Value_CNY'].sum() if not rsu_holdings.empty else 0
    
    # Get balance sheet value for comparison
    bs_value_usd = None
    if 'Asset_Invest_RSU_Value_USD' in balance_sheet.columns:
        bs_value_usd = balance_sheet['Asset_Invest_RSU_Value_USD'].iloc[-1]
    
    # Check units
    correct_units = rsu_holdings['Unit'].eq('Shares').all() if not rsu_holdings.empty else True
    
    status = 'PASS' if correct_units and len(rsu_holdings) > 0 else 'WARNING'
    
    result = {
        'asset_type': 'Amazon_RSU',
        'total_assets': len(rsu_holdings.index.get_level_values('Asset_ID').unique()),
        'total_transactions': len(rsu_txns),
        'transaction_total_value_usd': float(transaction_total_usd),
        'transaction_total_value_cny': float(transaction_total_cny),
        'balance_sheet_value_usd': float(bs_value_usd) if pd.notna(bs_value_usd) else None,
        'value_diff_pct': float(abs((transaction_total_usd - bs_value_usd) / bs_value_usd * 100)) if bs_value_usd and pd.notna(bs_value_usd) else None,
        'correct_units': bool(correct_units),  # Convert numpy.bool_ to Python bool
        'status': status
    }
    
    print(f"  ✓ Found {result['total_assets']} RSU assets")
    print(f"  ✓ Transaction total: ${transaction_total_usd:,.2f} (¥{transaction_total_cny:,.2f})")
    if bs_value_usd and pd.notna(bs_value_usd):
        print(f"  ✓ Balance sheet value: ${bs_value_usd:,.2f}")
        print(f"  ✓ Difference: {result['value_diff_pct']:.2f}%")
    print(f"  ✓ Correct units (Shares): {correct_units}")
    print(f"  ✓ Status: {status}")
    
    return result


def audit_duplicates(dm: DataManager) -> Dict:
    """Check for duplicate holdings"""
    print("\n🔍 Auditing for Duplicate Holdings...")
    
    holdings = dm.get_holdings()
    
    # Check for duplicates
    duplicates = holdings.index.duplicated(keep=False)
    duplicate_count = duplicates.sum()
    
    duplicate_assets = []
    if duplicate_count > 0:
        duplicate_entries = holdings[duplicates].sort_index()
        for idx in duplicate_entries.index.unique():
            dup_data = duplicate_entries.loc[idx]
            if isinstance(dup_data, pd.Series):
                dup_data = dup_data.to_frame().T
            duplicate_assets.append({
                'snapshot_date': str(idx[0]),
                'asset_id': str(idx[1]),
                'count': len(dup_data),
                'asset_names': dup_data['Asset_Name'].tolist() if 'Asset_Name' in dup_data else []
            })
    
    result = {
        'audit_type': 'Duplicate_Holdings',
        'total_duplicates': int(duplicate_count),
        'duplicate_assets': duplicate_assets,
        'status': 'FAIL' if duplicate_count > 0 else 'PASS'
    }
    
    print(f"  ✓ Total holdings: {len(holdings)}")
    print(f"  ✓ Duplicates found: {duplicate_count}")
    print(f"  ✓ Status: {result['status']}")
    
    return result


def main():
    """Run complete data quality audit"""
    print("=" * 70)
    print("DATA QUALITY AUDIT - Pre-Migration Validation")
    print("=" * 70)
    print(f"Audit Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Purpose: Validate transaction files before data consolidation migration")
    
    # Initialize DataManager
    print("\nInitializing DataManager...")
    dm = DataManager(config_path='config/settings.yaml')
    
    # Run all audits
    results = [
        audit_cn_funds(dm),
        audit_schwab_holdings(dm),
        audit_gold_holdings(dm),
        audit_rsu_holdings(dm),
        audit_duplicates(dm)
    ]
    
    # Create report
    report = {
        'audit_date': datetime.now().isoformat(),
        'audit_version': '1.0',
        'purpose': 'Pre-migration validation for data consolidation',
        'results': results,
        'summary': {
            'total_audits': len(results),
            'passed': sum(1 for r in results if r.get('status') == 'PASS'),
            'warnings': sum(1 for r in results if r.get('status') == 'WARNING'),
            'failed': sum(1 for r in results if r.get('status') == 'FAIL')
        }
    }
    
    # Save report
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'data_quality_audit_report.json')
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 70)
    print("AUDIT SUMMARY")
    print("=" * 70)
    print(f"Total Audits: {report['summary']['total_audits']}")
    print(f"✅ Passed: {report['summary']['passed']}")
    print(f"⚠️  Warnings: {report['summary']['warnings']}")
    print(f"❌ Failed: {report['summary']['failed']}")
    print(f"\nReport saved to: {output_file}")
    
    # Print recommendations
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    
    if report['summary']['failed'] > 0:
        print("❌ MIGRATION NOT RECOMMENDED")
        print("   - Critical issues detected (duplicates or data integrity problems)")
        print("   - Fix issues before proceeding with migration")
    elif report['summary']['warnings'] > 0:
        print("⚠️  MIGRATION REQUIRES REVIEW")
        print("   - Minor discrepancies detected")
        print("   - Review audit report before proceeding")
    else:
        print("✅ MIGRATION READY")
        print("   - All validations passed")
        print("   - Safe to proceed with data consolidation")
    
    print("\nNext steps:")
    print("1. Review detailed report: output/data_quality_audit_report.json")
    print("2. If approved, run: python scripts/create_migration_snapshot.py")
    print("3. Then proceed with migration implementation")
    
    return report['summary']['failed'] == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
