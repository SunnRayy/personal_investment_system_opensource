
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.database.connector import DatabaseConnector
from src.database.models import Transaction

def check_sgov():
    db_path = 'data/investment_system.db'
    connector = DatabaseConnector(database_path=db_path)
    session = connector.session
    
    print("Checking SGOV Transactions:")
    txns = session.query(Transaction).filter_by(asset_id='SGOV').all()
    if not txns:
        print("No transactions found for SGOV.")
    else:
        for t in txns:
            print(f"ID: {t.id} Type: {t.transaction_type} Shares: {t.shares} Amount: {t.amount} Date: {t.date}")

if __name__ == "__main__":
    check_sgov()
