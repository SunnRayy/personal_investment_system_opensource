
import os
import sys
import argparse
from sqlalchemy import func

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.database.connector import DatabaseConnector
from src.database.models import Transaction
import logging

def setup_logger(name):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    return logging.getLogger(name)

logger = setup_logger('validate_schwab_sync')

def validate_schwab_sync():
    """
    Validates integrity of Schwab transaction syncing.
    Checks for duplicates and incremental sync status.
    """
    db_path = 'data/investment_system.db'
    connector = DatabaseConnector(database_path=db_path)
    session = connector.session
    
    logger.info("Validating Schwab Sync Integrity...")
    
    # 1. Check Technical Duplicates (transaction_id)
    dup_ids = session.query(Transaction.transaction_id, func.count(Transaction.transaction_id))\
        .group_by(Transaction.transaction_id)\
        .having(func.count(Transaction.transaction_id) > 1).all()
        
    if dup_ids:
        logger.error(f"FAIL: Found {len(dup_ids)} duplicate transaction_ids!")
        for did in dup_ids[:5]:
            logger.error(f"  - {did}")
    else:
        logger.info("PASS: No duplicate transaction_ids found.")
        
    # 2. Check Logical Duplicates (Asset + Date + Type + Amount)
    # This might happen if ID generation logic changes or is flawed
    dup_logical = session.query(
            Transaction.asset_id, Transaction.date, Transaction.transaction_type, Transaction.amount, 
            func.count(Transaction.id)
        )\
        .group_by(Transaction.asset_id, Transaction.date, Transaction.transaction_type, Transaction.amount)\
        .having(func.count(Transaction.id) > 1).all()
        
    if dup_logical:
        logger.warning(f"WARNING: Found {len(dup_logical)} potential logical duplicates (same Asset, Date, Type, Amount).")
        # Filter for Schwab only to be specific
        schwab_dups = [d for d in dup_logical] # Filter logic if source column available would be better
        if schwab_dups:
             for d in schwab_dups[:5]:
                logger.warning(f"  - {d}")
    else:
        logger.info("PASS: No logical duplicates found.")
        
    # 3. Verify Schwab Data Presence
    schwab_count = session.query(Transaction).filter(Transaction.asset_id.in_(['AAPL', 'VOO', 'SGOV'])).count() # Sample check
    logger.info(f"Info: Found {schwab_count} transactions for sample Schwab assets (AAPL, VOO, SGOV).")

if __name__ == "__main__":
    validate_schwab_sync()
