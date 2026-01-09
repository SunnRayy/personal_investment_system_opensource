
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.database.connector import DatabaseConnector
from src.database.models import Transaction

def check_sell_sign():
    db_path = 'data/investment_system.db'
    connector = DatabaseConnector(database_path=db_path)
    session = connector.session
    
    print("Checking Existing Sell Transactions:")
    # Find a Sell transaction (Fund 100032 had 3 Sells)
    txns = session.query(Transaction).filter(Transaction.transaction_type.like('%Sell%')).limit(5).all()
    if not txns:
        print("No Sell transactions found.")
    else:
        for t in txns:
            print(f"ID: {t.transaction_id} Type: {t.transaction_type} Shares: {t.shares}")

if __name__ == "__main__":
    check_sell_sign()
