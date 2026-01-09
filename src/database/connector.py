# File path: src/database/connector.py
"""
Database connector for reading investment data.

Provides high-level query methods for DataManager to read from database
instead of Excel files. Maintains API compatibility with existing DataFrame structure.
"""

import logging
import pandas as pd
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .base import get_session
from .models import Transaction, Holding, Asset, BalanceSheet


class DatabaseConnector:
    """
    High-level database query interface for DataManager.
    
    Converts database ORM models to pandas DataFrames with the same structure
    as Excel-based data, ensuring zero changes needed in downstream code.
    """
    
    def __init__(self, database_path: Optional[str] = None):
        """
        Initialize database connector.
        
        Args:
            database_path: Path to SQLite database (optional, uses default if None)
        """
        self.logger = logging.getLogger(__name__)
        self.session = get_session()  # Uses default database path from base.py
        self.engine = self.session.bind
        
        # Cache for holdings to avoid repeated queries
        self._holdings_cache = {}

    def _read_sql(self, statement) -> pd.DataFrame:
        """Execute a SQLAlchemy statement and return a DataFrame."""
        if self.engine is None:
            raise RuntimeError("Database engine is not initialized")

        with self.engine.connect() as connection:
            df = pd.read_sql(statement, connection)

        return df
        
    def clear_cache(self):
        """Clear internal caches."""
        self._holdings_cache.clear()
        self.logger.debug("DatabaseConnector cache cleared")
        
    def get_transactions(self) -> pd.DataFrame:
        """
        Fetch all transactions from database as DataFrame with asset metadata.
        
        Returns DataFrame with same structure as Excel-based get_transactions():
        - Indexed by Date
        - Columns: Asset_ID, Asset_Name, Transaction_Type, Quantity, Price_Unit, Amount_Net, Currency
        - PLUS asset metadata: Asset_Type, Asset_Class, Asset_SubClass for classification
        """
        self.logger.info("Fetching transactions from database with asset metadata...")
        
        try:
            statement = (
                select(
                    Transaction.id.label('Database_ID'),
                    Transaction.transaction_id.label('Transaction_Business_ID'),
                    Transaction.date.label('Date'),
                    Transaction.asset_id.label('Asset_ID'),
                    Transaction.asset_name.label('Asset_Name'),
                    Transaction.transaction_type.label('Transaction_Type'),
                    Transaction.shares.label('Quantity'),
                    Transaction.price.label('Price_Unit'),
                    Transaction.amount.label('Amount_Net'),
                    Transaction.currency.label('Currency'),
                    Asset.asset_type.label('Asset_Type'),
                    Asset.asset_type.label('Asset_Type_Raw'),
                    Asset.asset_class.label('Asset_Class'),
                    Asset.asset_subclass.label('Asset_SubClass'),
                )
                .join(Asset, Transaction.asset_id == Asset.asset_id)
                .order_by(Transaction.date)
            )

            df = self._read_sql(statement)

            if df.empty:
                self.logger.warning("No transactions found in database")
                return df

            df['Date'] = pd.to_datetime(df['Date'])
            df = df.set_index('Date').sort_index()

            self.logger.info("Loaded %s transactions from database", len(df))
            return df

        except Exception as e:
            self.logger.error(f"Error fetching transactions from database: {e}")
            raise
    
    def get_holdings(self, latest_only: bool = True) -> pd.DataFrame:
        """
        Fetch holdings from database as DataFrame with asset metadata.
        
        Args:
            latest_only: If True, return only latest snapshot; if False, return all snapshots
            
        Returns DataFrame with same structure as Excel-based get_holdings():
        - MultiIndex: (Date, Asset_ID)
        - Columns: Asset_Name, Quantity, Market_Price_Unit, Market_Value_CNY, Cost_Price_Unit, Currency
        - PLUS asset metadata: Asset_Type, Asset_Class, Asset_SubClass, Risk_Level
        """
        # Check cache first
        if latest_only in self._holdings_cache:
            return self._holdings_cache[latest_only].copy()
            
        self.logger.info(f"Fetching holdings from database with asset metadata (latest_only={latest_only})...")
        
        try:
            statement = (
                select(
                    Holding.snapshot_date.label('Date'),
                    Holding.asset_id.label('Asset_ID'),
                    Holding.asset_name.label('Asset_Name'),
                    Holding.shares.label('Quantity'),
                    Holding.current_price.label('Market_Price_Unit'),
                    Holding.market_value.label('Market_Value_CNY'),
                    Holding.cost_basis.label('Cost_Price_Unit'),
                    Holding.currency.label('Currency'),
                    Asset.asset_type.label('Asset_Type'),
                    Asset.asset_type.label('Asset_Type_Raw'),
                    Asset.asset_class.label('Asset_Class'),
                    Asset.asset_subclass.label('Asset_SubClass'),
                    Asset.risk_level.label('Risk_Level'),
                )
                .join(Asset, Holding.asset_id == Asset.asset_id)
                .order_by(Holding.snapshot_date, Holding.asset_id)
            )

            if latest_only:
                # Use GLOBAL latest snapshot date (not per-asset)
                # This ensures we only return current holdings, not stale historical assets
                global_latest = self.session.query(func.max(Holding.snapshot_date)).scalar()
                if global_latest:
                    statement = statement.where(Holding.snapshot_date == global_latest)
                    self.logger.info(f"Using global latest snapshot: {global_latest}")
                else:
                    self.logger.warning("No holdings found in database")
                    return pd.DataFrame()
            else:
                self.logger.info("Fetching ALL historical holdings")

            df = self._read_sql(statement)

            if df.empty:
                self.logger.warning("No holdings found in database")
                return df

            df['Date'] = pd.to_datetime(df['Date'])
            df = df.set_index(['Date', 'Asset_ID']).sort_index()

            self.logger.info("Loaded %s holdings from database", len(df))
            
            # Cache the result
            self._holdings_cache[latest_only] = df.copy()
            
            return df

        except Exception as e:
            self.logger.error(f"Error fetching holdings from database: {e}")
            raise
    
    def get_assets(self) -> pd.DataFrame:
        """
        Fetch asset metadata from database.
        
        Returns DataFrame with columns:
        - Asset_ID, Asset_Name, Asset_Type, Asset_Class, Asset_Subclass, Is_Active
        """
        self.logger.info("Fetching assets from database...")
        
        try:
            assets = self.session.query(Asset).filter_by(is_active=True).all()
            
            if not assets:
                self.logger.warning("No assets found in database")
                return pd.DataFrame()
            
            data = []
            for asset in assets:
                data.append({
                    'Asset_ID': asset.asset_id,
                    'Asset_Name': asset.asset_name,
                    'Asset_Type': asset.asset_type,
                    'Asset_Class': asset.asset_class,
                    'Asset_Subclass': asset.asset_subclass,
                    'Is_Active': asset.is_active,
                })
            
            df = pd.DataFrame(data)
            
            self.logger.info(f"Loaded {len(df)} assets from database")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching assets from database: {e}")
            raise
    
    def get_balance_sheet(self) -> pd.DataFrame:
        """
        Fetch balance sheet data from database.
        
        Returns DataFrame with Date index and columns for each line_item.
        Structure matches Excel-based balance sheet format.
        """
        self.logger.info("Fetching balance sheet from database...")
        
        try:
            balance_sheet_records = self.session.query(BalanceSheet).all()
            
            if not balance_sheet_records:
                self.logger.warning("No balance sheet data found in database")
                return pd.DataFrame()
            
            # Group by snapshot_date and pivot to wide format
            data = {}
            for record in balance_sheet_records:
                date_key = record.snapshot_date
                if date_key not in data:
                    data[date_key] = {}
                data[date_key][record.line_item] = float(record.amount) if record.amount else 0.0
            
            # Convert to DataFrame
            df = pd.DataFrame.from_dict(data, orient='index')
            df.index = pd.to_datetime(df.index)
            df.index.name = 'Date'
            
            # Sort by date
            df = df.sort_index()
            
            self.logger.info(f"Loaded balance sheet with {len(df)} date snapshots")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching balance sheet from database: {e}")
            raise
    
    def get_transaction_by_id(self, transaction_id: int) -> Optional[dict]:
        """
        Fetch a single transaction by its primary key ID.
        
        Args:
            transaction_id: The database primary key ID
            
        Returns:
            Dictionary with transaction details or None if not found
        """
        try:
            txn = self.session.query(Transaction).filter(Transaction.id == transaction_id).first()
            
            if not txn:
                return None
                
            return {
                'id': txn.id,
                'date': txn.date.isoformat() if txn.date else None,
                'asset_id': txn.asset_id,
                'asset_name': txn.asset_name,
                'transaction_type': txn.transaction_type,
                'shares': float(txn.shares) if txn.shares is not None else None,
                'price': float(txn.price) if txn.price is not None else None,
                'amount': float(txn.amount) if txn.amount is not None else None,
                'currency': txn.currency,
                'exchange_rate': float(txn.exchange_rate) if txn.exchange_rate is not None else None,
                'source': txn.source
            }
        except Exception as e:
            self.logger.error(f"Error fetching transaction {transaction_id}: {e}")
            raise

    def add_asset(self, data: dict) -> bool:
        """
        Add a new asset to the database.
        
        Args:
            data: Dictionary containing asset fields
            
        Returns:
            True if successful
        """
        self.logger.info(f"Adding new asset {data.get('asset_id')}")
        
        try:
            new_asset = Asset(
                asset_id=data['asset_id'],
                asset_name=data['asset_name'],
                asset_type=data.get('asset_type'),
                asset_class=data.get('asset_class'),
                asset_subclass=data.get('asset_subclass'),
                risk_level=data.get('risk_level'),
                is_active=True
            )
            
            self.session.add(new_asset)
            self.session.commit()
            return True
            
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error adding asset: {e}")
            raise

    def add_transaction(self, data: dict) -> int:
        """
        Add a new transaction to the database.
        
        Args:
            data: Dictionary containing transaction fields
            
        Returns:
            ID of the newly created transaction
        """
        self.logger.info(f"Adding new transaction for asset {data.get('asset_id')}")
        
        try:
            # Generate a transaction_id hash if not provided
            if 'transaction_id' not in data:
                import hashlib
                # Create a unique hash based on content
                unique_str = f"{data.get('date')}_{data.get('asset_id')}_{data.get('transaction_type')}_{data.get('amount')}_{datetime.now().timestamp()}"
                data['transaction_id'] = hashlib.md5(unique_str.encode()).hexdigest()
            
            new_txn = Transaction(
                transaction_id=data['transaction_id'],
                date=pd.to_datetime(data['date']).date(),
                asset_id=data['asset_id'],
                asset_name=data['asset_name'],
                transaction_type=data['transaction_type'],
                shares=data.get('shares'),
                price=data.get('price'),
                amount=data['amount'],
                currency=data.get('currency', 'CNY'),
                exchange_rate=data.get('exchange_rate'),
                source=data.get('source', 'Manual_Web'),
                created_by='web_user'
            )
            
            self.session.add(new_txn)
            self.session.commit()
            
            self.logger.info(f"Successfully added transaction {new_txn.id}")
            return new_txn.id
            
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error adding transaction: {e}")
            raise

    def update_transaction(self, txn_id: int, data: dict) -> bool:
        """
        Update an existing transaction.
        
        Args:
            txn_id: The database primary key ID
            data: Dictionary containing fields to update
            
        Returns:
            True if successful
        """
        self.logger.info(f"Updating transaction {txn_id}")
        
        try:
            txn = self.session.query(Transaction).filter(Transaction.id == txn_id).first()
            
            if not txn:
                self.logger.warning(f"Transaction {txn_id} not found for update")
                return False
            
            # Update fields
            if 'date' in data:
                txn.date = pd.to_datetime(data['date']).date()
            if 'asset_id' in data:
                txn.asset_id = data['asset_id']
            if 'asset_name' in data:
                txn.asset_name = data['asset_name']
            if 'transaction_type' in data:
                txn.transaction_type = data['transaction_type']
            if 'shares' in data:
                txn.shares = data['shares']
            if 'price' in data:
                txn.price = data['price']
            if 'amount' in data:
                txn.amount = data['amount']
            if 'currency' in data:
                txn.currency = data['currency']
            if 'exchange_rate' in data:
                txn.exchange_rate = data['exchange_rate']
            if 'source' in data:
                txn.source = data['source']
                
            txn.updated_at = datetime.utcnow()
            
            self.session.commit()
            self.logger.info(f"Successfully updated transaction {txn_id}")
            return True
            
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error updating transaction {txn_id}: {e}")
            raise

    def delete_transaction(self, txn_id: int) -> bool:
        """
        Delete a transaction.
        
        Args:
            txn_id: The database primary key ID
            
        Returns:
            True if successful
        """
        self.logger.info(f"Deleting transaction {txn_id}")
        
        try:
            txn = self.session.query(Transaction).filter(Transaction.id == txn_id).first()
            
            if not txn:
                self.logger.warning(f"Transaction {txn_id} not found for deletion")
                return False
                
            self.session.delete(txn)
            self.session.commit()
            
            self.logger.info(f"Successfully deleted transaction {txn_id}")
            return True
            
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error deleting transaction {txn_id}: {e}")
            raise
    
    def get_asset(self, asset_id: str) -> Optional[dict]:
        """
        Get asset details by ID.
        
        Args:
            asset_id: The asset ID to look up
            
        Returns:
            Dictionary of asset details or None if not found
        """
        try:
            asset = self.session.query(Asset).filter(Asset.asset_id == asset_id).first()
            if asset:
                return {
                    'asset_id': asset.asset_id,
                    'asset_name': asset.asset_name,
                    'asset_type': asset.asset_type,
                    'asset_class': asset.asset_class,
                    'risk_level': asset.risk_level
                }
            return None
        except Exception as e:
            self.logger.error(f"Error fetching asset {asset_id}: {e}")
            return None

    def close(self):
        """Close database session."""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
