
from src.database import get_session, Transaction, Asset
from sqlalchemy import select

session = get_session()
# Query distinct transaction types for assets where type is 'CN Fund' (or similar)
stmt = (
    select(Transaction.transaction_type, Asset.asset_type, Transaction.source)
    .join(Asset)
    .where(Asset.asset_type.like('%Fund%'))
    .distinct()
)
results = session.execute(stmt).all()

print("Distinct Transaction Types for Funds:")
for row in results:
    print(row)

# Also check specific fund 100032 if it has any dividends
stmt_100032 = (
    select(Transaction.transaction_type, Transaction.amount)
    .where(Transaction.asset_id == '100032')
)
results_100032 = session.execute(stmt_100032).all()
print(f"\nTransactions for 100032 ({len(results_100032)} total):")
types_count = {}
for row in results_100032:
    types_count[row.transaction_type] = types_count.get(row.transaction_type, 0) + 1
print(types_count)
