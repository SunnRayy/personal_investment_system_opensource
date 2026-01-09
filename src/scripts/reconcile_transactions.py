
import os
import sys
import argparse
import logging
from datetime import datetime, date
from decimal import Decimal
import pandas as pd
from sqlalchemy import func
from typing import List, Dict

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.database.connector import DatabaseConnector
from src.database.models import Asset, Transaction, Holding

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('reconcile_transactions')

def reconcile_transactions(execute: bool = False, verify_only: bool = False):
    """
    Reconciles 'Transaction' history with 'Holding' snapshots.
    Generates 'Adjustment' transactions to bridge the gap.
    """
    db_path = 'data/investment_system.db'
    connector = DatabaseConnector(database_path=db_path)
    session = connector.session
    
    logger.info(f"Starting Reconciliation (Execute: {execute}, Verify: {verify_only})")
    
    # 1. Get All Assets
    assets = session.query(Asset).all()
    logger.info(f"Found {len(assets)} assets to check.")
    
    adjustments = []
    stats = {'checked': 0, 'gaps_found': 0, 'adjustments_created': 0}
    
    # Precision threshold
    THRESHOLD = Decimal('0.000001')
    
    print(f"\n{'Asset ID':<15} {'Asset Name':<30} {'Snapshot':>12} {'Txn Sum':>12} {'Gap':>12} {'Action':<15}")
    print("-" * 100)
    
    for asset in assets:
        # Filter exclusions
        if asset.asset_id.startswith('Property_') or asset.asset_id.startswith('Ins_'):
            continue
            
        # 2. Get Snapshot for Target Date
        # Use valid global max date to determine "Current Reality".
        # If an asset is missing from the Latest Snapshot, it implies 0 shares (Closed Position).
        
        target_date = session.query(func.max(Holding.snapshot_date)).scalar()
        if not target_date:
            logger.error("No snapshots found in DB. Cannot reconcile.")
            return

        snapshot = session.query(Holding).filter_by(asset_id=asset.asset_id, snapshot_date=target_date).first()
        
        snapshot_shares = 0.0
        snapshot_currency = 'CNY'
        snapshot_market_value = 0.0
        
        if snapshot:
            snapshot_shares = float(snapshot.shares) if snapshot.shares is not None else 0.0
            snapshot_currency = snapshot.currency
            snapshot_market_value = float(snapshot.market_value) if snapshot.market_value else 0.0
        else:
            # If checking verify_only, we might want to be careful.
            # But for full reconciliation, missing in latest snapshot = 0.
            # We look for ANY previous snapshot to guess currency if needed.
            prev_snap = session.query(Holding).filter_by(asset_id=asset.asset_id).first()
            if prev_snap:
                snapshot_currency = prev_snap.currency
        
        # 3. Get Transaction Sum
        
        # 3. Get Transaction Sum
        # Note: Transaction direction is handled by sign conventions in data usually, 
        # but let's check how they are stored. 
        # Typically Buy is +, Sell is -. 
        # Let's verify if we need to sum logic or just raw numeric column assuming it's signed.
        # Based on cleaners.py: Quantity is signed (+ for Buy, - for Sell).
        # We assume database stores signed 'shares'.
        
        txn_sum_result = session.query(func.sum(Transaction.shares))\
            .filter_by(asset_id=asset.asset_id).scalar()
            
        txn_shares = float(txn_sum_result) if txn_sum_result is not None else 0.0
        
        # 4. Calculate Gap
        gap = snapshot_shares - txn_shares
        
        stats['checked'] += 1
        
        if abs(gap) > float(THRESHOLD):
            stats['gaps_found'] += 1
            action = "None"
            
            if verify_only:
                action = "MISMATCH"
            else:
                # 5. Generate Adjustment
                txn_type = 'Adjustment_Buy' if gap > 0 else 'Adjustment_Sell'
                action = f"{txn_type}"
                
                # IDEMPOTENCY CHECK: Skip if we already have an adjustment for this asset today
                # This prevents duplicate adjustments when run-all is executed multiple times
                existing_adj = session.query(Transaction).filter(
                    Transaction.asset_id == asset.asset_id,
                    Transaction.transaction_id.like('ADJ_%'),
                    Transaction.date == date.today()
                ).first()
                
                if existing_adj:
                    action = f"SKIP (exists)"
                    print(f"{asset.asset_id:<15} {asset.asset_name[:28]:<30} {snapshot_shares:>12.4f} {txn_shares:>12.4f} {gap:>12.4f} {action:<15}")
                    continue
                
                # Calculate implicit price from snapshot to avoid 0-cost/100% profit issues
                # and to ensure fallback valuation works if PriceService fails
                # Calculate implicit price from snapshot to avoid 0-cost/100% profit issues
                # and to ensure fallback valuation works if PriceService fails
                implied_price = Decimal(0)
                # If we have a snapshot with value, use it. 
                if snapshot_shares != 0 and snapshot_market_value != 0:
                    implied_price = Decimal(str(snapshot_market_value)) / Decimal(str(snapshot_shares))
                else:
                    # Closing position or opening from scratch?
                    # If closing (gap < 0), price matters less for "Value" (it's 0), but matters for PnL.
                    # We should try to use the latest known price?
                    # For now, 0 or 1 is 'okay' for Adjustment_Sell as it just removes quantity.
                    # But ideally we use last known price.
                    pass
                
                amount = Decimal(gap) * implied_price
                
                
                # Check Last Transaction Date to ensure we don't backdate before acquisition
                last_txn_date = session.query(func.max(Transaction.date)).filter_by(asset_id=asset.asset_id).scalar()
                
                # Default to today, but if last txn is in future (unlikely) or we want to be safe...
                # Actually, simply using 'today' is safest for "Current Adjustment".
                # Backdating to Jan 1 caused issues where we sold assets before we bought them (e.g. 16901 bought in Oct 2025).
                # To ensure it affects "current" holdings correctly and respects FIFO:
                # Place adjustment at CURRENT time (today).
                adj_date = date.today()
                
                # If we really wanted to backdate for YTD reports, we'd need complex logic. 
                # For now, correctness of *current* balance is priority.
                
                # Currency/Price Fix for USD Assets (SGOV)
                # Snapshot Market Value is likely in CNY (normalized).
                # If asset is USD, we need to convert implied_price (CNY) -> USD.
                fx_rate = Decimal(1)
                
                if snapshot_currency == 'USD':
                    # === 3-TIER FX RATE FETCH ===
                    # 1. Google Finance (Primary - Real-time)
                    # 2. Excel DataManager (Fallback - Historical)
                    # 3. Hardcoded 7.05 (Last Resort)
                    
                    fx_rate = None
                    
                    # TIER 1: Try Google Finance
                    try:
                        import requests
                        from bs4 import BeautifulSoup
                        
                        url = "https://www.google.com/finance/quote/USD-CNY"
                        headers = {'User-Agent': 'Mozilla/5.0'}
                        response = requests.get(url, headers=headers, timeout=5)
                        
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            # Google Finance structure: Price is in a div with class "YMlKec fxKbKc"
                            price_div = soup.find('div', class_='YMlKec fxKbKc')
                            if price_div:
                                price_text = price_div.text.strip().replace(',', '')
                                fx_rate = Decimal(price_text)
                                logger.info(f"Using Google Finance FX rate: {fx_rate}")
                    except Exception as e:
                        logger.debug(f"Google Finance FX fetch failed: {e}")
                    
                    # TIER 2: Try Excel (DataManager)
                    if fx_rate is None:
                        try:
                            from src.data_manager.manager import DataManager
                            dm = DataManager()
                            if dm.fx_rates is not None and not dm.fx_rates.empty:
                                latest_fx = dm.fx_rates.iloc[-1]
                                fx_rate = Decimal(str(float(latest_fx)))
                                logger.info(f"Using Excel FX rate: {fx_rate}")
                        except Exception as e:
                            logger.debug(f"Excel FX fetch failed: {e}")
                    
                    # TIER 3: Hardcoded fallback
                    if fx_rate is None:
                        fx_rate = Decimal('7.05')
                        logger.warning(f"All FX sources failed. Using hardcoded fallback: {fx_rate}")
                    
                    # If implied_price is in CNY (from snapshot MV), convert to USD.
                    # implied_price (CNY) / FX = implied_price (USD)
                    implied_price = implied_price / fx_rate
                    amount = amount / fx_rate 
                
                # Update Exchange Rate in txn
                
                adj_txn = Transaction(
                    transaction_id=f"ADJ_{asset.asset_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    date=adj_date,
                    asset_id=asset.asset_id,
                    asset_name=asset.asset_name,
                    transaction_type=txn_type,
                    shares=Decimal(gap), 
                    price=implied_price, 
                    # Amount: Buy is cash OUTFLOW (negative), Sell is INFLOW (positive)
                    # gap > 0 = Adjustment_Buy (more shares needed), amount should be negative
                    # gap < 0 = Adjustment_Sell (less shares needed), amount should be positive
                    amount=-abs(amount) if gap > 0 else abs(amount), 
                    currency=snapshot_currency or 'CNY',
                    exchange_rate=fx_rate if snapshot_currency == 'USD' else None,
                    source='Reconciliation_Script'
                )
                adjustments.append(adj_txn)
            
            print(f"{asset.asset_id:<15} {asset.asset_name[:28]:<30} {snapshot_shares:>12.4f} {txn_shares:>12.4f} {gap:>12.4f} {action:<15}")
        
    print("-" * 100)
    print(f"Stats: Checked {stats['checked']}, Gaps {stats['gaps_found']}, Proposed Adjustments {len(adjustments)}")
    
    if verify_only:
        if stats['gaps_found'] == 0:
            logger.info("VERIFICATION PASSED: No discrepancies found.")
            return True
        else:
            logger.error(f"VERIFICATION FAILED: {stats['gaps_found']} discrepancies found.")
            return False
            
    if adjustments:
        if execute:
            logger.info(f"Committing {len(adjustments)} adjustments to database...")
            session.add_all(adjustments)
            session.commit()
            logger.info("DONE.")
        else:
            logger.info("Dry Run Mode: No changes made. Use --execute to commit.")
    else:
        logger.info("No adjustments needed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Reconcile Transactions with Holdings Snapshots')
    parser.add_argument('--execute', action='store_true', help='Execute changes and write to DB')
    parser.add_argument('--verify', action='store_true', help='Verify parity only, do not propose changes')
    
    args = parser.parse_args()
    
    reconcile_transactions(execute=args.execute, verify_only=args.verify)
