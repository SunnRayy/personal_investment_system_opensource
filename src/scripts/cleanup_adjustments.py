
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.database.connector import DatabaseConnector
from src.database.models import Transaction

def cleanup_adjustments():
    db_path = 'data/investment_system.db'
    connector = DatabaseConnector(database_path=db_path)
    session = connector.session
    
    print("Cleaning up Adjustment Transactions...")
    adjustments = session.query(Transaction).filter(Transaction.transaction_id.like('ADJ_%')).all()
    
    if not adjustments:
        print("No adjustments found to clean.")
    else:
        print(f"Found {len(adjustments)} adjustments. Deleting...")
        for t in adjustments:
            session.delete(t)
        session.commit()
        print("Cleanup complete.")

if __name__ == "__main__":
    cleanup_adjustments()
