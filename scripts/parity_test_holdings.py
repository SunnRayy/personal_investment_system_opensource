#!/usr/bin/env python3
"""
Holdings Parity Test - Compare Excel vs Database holdings values.

This script validates that HoldingsCalculator produces results matching
the legacy Excel-based DataManager.get_holdings() method.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import logging
import pandas as pd
from datetime import date

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def run_parity_test():
    """Compare Excel holdings vs Database (transaction-derived) holdings."""
    
    print("\n" + "="*70)
    print("  HOLDINGS PARITY TEST: Excel vs Database")
    print("="*70 + "\n")
    
    # 1. Load Excel Holdings (Legacy)
    print("📊 Step 1: Loading Excel-based holdings...")
    from src.data_manager.manager import DataManager
    
    dm = DataManager(config_path='config/settings.yaml')
    excel_holdings = dm.get_holdings(latest_only=True)
    
    if excel_holdings is None or excel_holdings.empty:
        print("❌ No Excel holdings data found!")
        return False
    
    # Handle MultiIndex if present
    if isinstance(excel_holdings.index, pd.MultiIndex):
        excel_holdings = excel_holdings.reset_index()
    
    excel_total = 0
    if 'Market_Value_CNY' in excel_holdings.columns:
        excel_total = excel_holdings['Market_Value_CNY'].sum()
    elif 'Market_Value' in excel_holdings.columns:
        excel_total = excel_holdings['Market_Value'].sum()
    
    print(f"   Excel Total: ¥{excel_total:,.2f} ({len(excel_holdings)} assets)")
    
    # 2. Load Database Holdings (Transaction-Derived)
    print("\n📊 Step 2: Calculating holdings from transactions...")
    from src.portfolio_lib.holdings_calculator import HoldingsCalculator
    from src.portfolio_lib.price_service import PriceService
    
    price_service = PriceService(data_manager=dm)
    hc = HoldingsCalculator(price_service=price_service, data_manager=dm)
    
    try:
        db_holdings = hc.calculate_current_holdings()
    except Exception as e:
        print(f"❌ HoldingsCalculator failed: {e}")
        return False
    
    if db_holdings is None or db_holdings.empty:
        print("⚠️  No DB holdings calculated (possibly no transactions in DB)")
        db_total = 0
    else:
        db_total = db_holdings['Market_Value'].sum() if 'Market_Value' in db_holdings.columns else 0
        print(f"   DB Total: ¥{db_total:,.2f} ({len(db_holdings)} assets)")
    
    # 3. Compare Totals
    print("\n" + "-"*70)
    print("  PARITY COMPARISON")
    print("-"*70)
    
    delta = excel_total - db_total
    delta_pct = (delta / excel_total * 100) if excel_total > 0 else 0
    
    print(f"   Excel Total:    ¥{excel_total:,.2f}")
    print(f"   DB Total:       ¥{db_total:,.2f}")
    print(f"   Delta:          ¥{delta:,.2f} ({delta_pct:.2f}%)")
    
    # 4. Asset-Level Comparison (if both have data)
    if not db_holdings.empty:
        print("\n" + "-"*70)
        print("  ASSET-LEVEL COMPARISON (Top 10 by |Delta|)")
        print("-"*70)
        
        # Prepare comparison DataFrame
        excel_map = {}
        asset_id_col = 'Asset_ID' if 'Asset_ID' in excel_holdings.columns else excel_holdings.index.name
        for _, row in excel_holdings.iterrows():
            aid = row.get('Asset_ID') or row.name
            val = row.get('Market_Value_CNY') or row.get('Market_Value') or 0
            excel_map[str(aid)] = val
        
        db_map = {}
        for _, row in db_holdings.iterrows():
            aid = row.get('Asset_ID')
            val = row.get('Market_Value') or 0
            db_map[str(aid)] = val
        
        # Build comparison table
        all_assets = set(excel_map.keys()) | set(db_map.keys())
        comparison = []
        for aid in all_assets:
            excel_val = excel_map.get(aid, 0)
            db_val = db_map.get(aid, 0)
            delta = excel_val - db_val
            comparison.append({
                'Asset_ID': aid,
                'Excel': excel_val,
                'DB': db_val,
                'Delta': delta,
                'Delta_Abs': abs(delta)
            })
        
        comparison_df = pd.DataFrame(comparison)
        comparison_df = comparison_df.sort_values('Delta_Abs', ascending=False).head(10)
        
        print(comparison_df[['Asset_ID', 'Excel', 'DB', 'Delta']].to_string(index=False))
    
    # 5. Pass/Fail
    print("\n" + "="*70)
    if abs(delta_pct) < 1.0:
        print("  ✅ PARITY TEST PASSED (<1% delta)")
        result = True
    elif abs(delta_pct) < 5.0:
        print("  ⚠️  PARITY TEST WARNING (1-5% delta)")
        result = True
    else:
        print("  ❌ PARITY TEST FAILED (>5% delta)")
        result = False
    print("="*70 + "\n")
    
    return result

if __name__ == "__main__":
    success = run_parity_test()
    sys.exit(0 if success else 1)
