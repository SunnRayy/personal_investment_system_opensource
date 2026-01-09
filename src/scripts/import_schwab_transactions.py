
import os
import sys
import logging
import hashlib
from decimal import Decimal
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.database.connector import DatabaseConnector
from src.database.models import Transaction
from src.data_manager.manager import DataManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('import_schwab_transactions')

def generate_transaction_id(row: pd.Series) -> str:
    """Generate unique transaction ID consistently with Migrator."""
    source = 'Schwab_CSV'
    asset_id = str(row.get('Asset_ID', 'UNKNOWN')).strip()
    txn_date = str(row.get('Transaction_Date', ''))[:10]
    txn_type = str(row.get('Transaction_Type', 'UNKNOWN'))
    amount = abs(float(row.get('Amount_Net', 0)))
    
    base_id = f"{source}_{asset_id}_{txn_date}_{txn_type}_{amount:.2f}"
    
    # Add hash for uniqueness
    row_str = str(row.to_dict())
    hash_suffix = hashlib.md5(row_str.encode()).hexdigest()[:8]
    
    return f"{base_id}_{hash_suffix}"

def import_schwab_transactions():
    """Reads Schwab transactions from DataManager and syncs to DB."""
    
    # 1. Initialize DataManager in Excel mode to read CSVs
    logger.info("Initializing DataManager to read Schwab CSVs...")
    dm = DataManager(force_mode='excel')
    transactions_df = dm.get_transactions()
    
    if transactions_df is None or transactions_df.empty:
        logger.error("No transactions found in DataManager!")
        return
    
    # Filter for Schwab transactions
    # In manager.py, we set default asset_type='Schwab US Investment' for Schwab transactions
    # But let's check standard columns or specific assets SGOV, IBIT
    
    target_assets = ['SGOV', 'IBIT']
    logger.info(f"Filtering for assets: {target_assets}")
    
    # Also include any that look like Schwab (Currency USD, etc)
    schwab_txns = transactions_df[
        (transactions_df['Asset_ID'].isin(target_assets)) | 
        (transactions_df['Currency'] == 'USD')
    ].copy()
    
    logger.info(f"Found {len(schwab_txns)} potential Schwab transactions.")
    
    if schwab_txns.empty:
        logger.warning("No matching transactions found.")
        return

    # 2. Connect to DB
    db_path = 'data/investment_system.db'
    connector = DatabaseConnector(database_path=db_path)
    session = connector.session
    
    added_count = 0
    skipped_count = 0
    
    # 3. Iterate and Insert
    for idx, row in schwab_txns.iterrows():
        try:
            asset_id = str(row['Asset_ID']).strip()
            
            # Skip if not target assets (optional, but let's be safe and sync all Schwab)
            # Actually, let's sync ALL Schwab transactions found
            
            # Generate ID
            txn_id = generate_transaction_id(row)
            
            # Check existence
            existing = session.query(Transaction).filter_by(transaction_id=txn_id).first()
            if existing:
                skipped_count += 1
                continue
            
            # Convert values
            amount_net = Decimal(str(row.get('Amount_Net', 0)))
            price = Decimal(str(row.get('Price_Unit', 0)))
            shares = Decimal(str(row.get('Quantity', 0)))
            
            # Handle timestamps (Date is the Index)
            txn_date = idx
            
            if pd.isna(txn_date):
                logger.warning(f"Row {idx} has invalid Index Date. Skipping.")
                continue

            try:
                if isinstance(txn_date, pd.Timestamp):
                    txn_date = txn_date.date()
                elif isinstance(txn_date, str):
                    txn_date = datetime.strptime(txn_date, '%Y-%m-%d').date()
            except Exception as e:
                logger.warning(f"Row {idx} invalid date format '{txn_date}': {e}. Skipping.")
                continue
            
            new_txn = Transaction(
                transaction_id=txn_id,
                date=txn_date,
                asset_id=asset_id,
                asset_name=row.get('Asset_Name'),
                transaction_type=row.get('Transaction_Type'),
                shares=abs(shares), 
                price=abs(price), 
                amount=amount_net, 
                currency=row.get('Currency', 'USD'),
                exchange_rate=None, 
                source='Schwab_CSV'
            )
            
            # Fix shares sign if DataManager didn't
            new_txn.shares = Decimal(str(row.get('Quantity', 0)))
            
            session.add(new_txn)
            added_count += 1
            print(f"Adding: {txn_date} {asset_id} {row['Transaction_Type']} {shares} @ {price}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error processing row {idx}: {e}")
            continue
    
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Commit failed: {e}")
        return

    logger.info(f"Import Complete: Added {added_count}, Skipped {skipped_count}")
    
    # 4. Cleanup Synthetic Adjustments for these assets
    if added_count > 0:
        logger.info("Cleaning up old synthetic ADJ transactions for affected assets...")
        
        # Identify affected assets
        affected_assets = schwab_txns['Asset_ID'].unique()
        
        deleted_count = 0
        for asset_id in affected_assets:
            # Find ADJ transactions
            adjs = session.query(Transaction).filter(
                Transaction.asset_id == asset_id,
                Transaction.transaction_id.like('ADJ_%')
            ).all()
            
            for adj in adjs:
                session.delete(adj)
                deleted_count += 1
                print(f"  Deleted synthetic adjustment: {adj.transaction_id} for {asset_id}")
        
        session.commit()
        logger.info(f"Cleanup Complete: Deleted {deleted_count} synthetic transactions.")

if __name__ == "__main__":
    import_schwab_transactions()
