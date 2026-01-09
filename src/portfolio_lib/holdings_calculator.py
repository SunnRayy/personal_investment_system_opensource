# File path: src/portfolio_lib/holdings_calculator.py
"""
Holdings Calculator - Calculate current holdings from transaction history.

Provides transaction-based holdings calculation using FIFO cost basis,
eliminating the need for manual holdings snapshots. This is the core
of the Excel-to-Database migration strategy.

Key features:
- Aggregates transactions to compute net holdings
- FIFO cost basis calculation for unrealized P&L
- Integration with PriceService for current market values
- Support for corporate actions (future)
"""

import logging
import pandas as pd
from datetime import date
from decimal import Decimal
from typing import Optional, Dict, List, Tuple
from collections import deque

from src.database.base import get_session
from src.database.models import Transaction, Asset
from .price_service import PriceService


class HoldingsCalculator:
    """
    Calculate holdings from transaction history with FIFO cost basis.
    
    Replaces the need for manual holdings snapshots by computing positions
    from transaction records stored in the database.
    """
    
    def __init__(self, db_session=None, price_service=None, data_manager=None):
        """
        Initialize holdings calculator.
        
        Args:
            db_session: SQLAlchemy session (optional, creates new if None)
            price_service: PriceService instance (optional, creates new if None)
            data_manager: DataManager for Excel fallback (optional)
        """
        self.logger = logging.getLogger(__name__)
        self.session = db_session or get_session()
        self.price_service = price_service or PriceService(self.session, data_manager)
        
    def calculate_current_holdings(self, as_of_date: Optional[date] = None) -> pd.DataFrame:
        """
        Calculate current holdings from all transactions up to a specific date.
        
        Args:
            as_of_date: Date to calculate holdings for (defaults to today)
            
        Returns:
            DataFrame with columns:
            - Asset_ID, Asset_Name, Asset_Type, Asset_Class
            - Quantity (shares held)
            - Cost_Basis (total cost in CNY)
            - Average_Cost (cost per share)
            - Current_Price (from PriceService)
            - Market_Value (Quantity × Current_Price)
            - Unrealized_PnL (Market_Value - Cost_Basis)
            - Unrealized_PnL_Pct (percentage gain/loss)
            - Currency
        """
        if as_of_date is None:
            as_of_date = date.today()
        
        self.logger.info(f"Calculating holdings as of {as_of_date}...")
        
        # 1. Fetch all transactions up to as_of_date
        transactions_df = self._get_transactions_up_to_date(as_of_date)
        
        if transactions_df.empty:
            self.logger.warning("No transactions found")
            return pd.DataFrame()
        
        # Batch fetch prices to optimize performance and avoid API rate limits
        unique_assets = transactions_df['Asset_ID'].unique().tolist()
        self.logger.info(f"Fetching prices for {len(unique_assets)} assets...")
        self.price_service.get_batch_latest_prices(unique_assets, as_of_date)
        
        # 2. Calculate holdings per asset with FIFO cost basis
        holdings_data = []
        
        for asset_id in unique_assets:
            asset_txns = transactions_df[transactions_df['Asset_ID'] == asset_id].copy()
            
            holding = self._calculate_asset_holding(asset_id, asset_txns, as_of_date)
            
            if holding and holding['Quantity'] > 0:
                holdings_data.append(holding)
        
        # Convert holdings_data to a dict for easier lookup during BS sync
        current_holdings_map = {h['Asset_ID']: h for h in holdings_data}

        # 3. Balance Sheet Sync (Manual Assets)
        # Map Asset_ID to Balance Sheet Line Item
        bs_mapping = {
            'BankWealth_招行': ('Asset_Invest_BankWealth_Value', 'CNY'),
            'Pension_Personal': ('Asset_Invest_Pension_Value', 'CNY'),
            'Property_Residential_A': ('Asset_Fixed_Property_Value', 'CNY'),
            # Cash and Deposits (CNY)
            'Cash_CNY': ('Asset_Cash_CNY', 'CNY'),  # Fixed: was 'Asset_Deposit_Cash_CNY'
            'Bank_Account_A': ('Asset_Bank_Account_A', 'CNY'),
            'Deposit_BOB_CNY': ('Asset_Deposit_BOB_CNY', 'CNY'),
            'Deposit_CMB_CNY': ('Asset_Deposit_CMB_CNY', 'CNY'),
            # USD Deposits (BS stores RAW USD - need FX conversion)
            'Deposit_BOC_USD': ('Asset_Deposit_BOC_USD', 'USD'),
            'Deposit_Chase_USD': ('Asset_Deposit_Chase_USD', 'USD'),
            'Deposit_Discover_USD': ('Asset_Deposit_Discover_USD', 'USD'),
        }
        
        # Get FX rate for USD -> CNY conversion
        usd_cny_rate = 7.05  # Default fallback
        try:
            from src.database.models import BalanceSheet
            from sqlalchemy import func
            latest_bs_date = self.session.query(func.max(BalanceSheet.snapshot_date)).scalar()
            if latest_bs_date:
                fx_item = self.session.query(BalanceSheet).filter(
                    BalanceSheet.snapshot_date == latest_bs_date,
                    BalanceSheet.line_item == 'Ref_USD_FX_Rate'
                ).first()
                if fx_item and fx_item.amount:
                    usd_cny_rate = float(fx_item.amount)
        except Exception as e:
            self.logger.warning(f"Could not fetch FX rate: {e}")
        
        try:
            from src.database.models import BalanceSheet, Holding
            from sqlalchemy import func
            # Get latest balance sheet snapshot
            latest_bs_date = self.session.query(func.max(BalanceSheet.snapshot_date)).scalar()
            
            if latest_bs_date:
                bs_line_items = [v[0] for v in bs_mapping.values()]
                bs_items = self.session.query(BalanceSheet).filter(
                    BalanceSheet.snapshot_date == latest_bs_date,
                    BalanceSheet.line_item.in_(bs_line_items)
                ).all()
                
                bs_data = {item.line_item: item.amount for item in bs_items}
                
                for asset_id, (line_item, currency) in bs_mapping.items():
                    amount = bs_data.get(line_item)
                    if amount is not None and amount > 0:
                        # Apply FX conversion for USD assets
                        if currency == 'USD':
                            amount_cny = float(amount) * usd_cny_rate
                            fx_rate = usd_cny_rate
                        else:
                            amount_cny = float(amount)
                            fx_rate = 1.0
                        
                        # Fetch asset metadata
                        asset = self.session.query(Asset).filter(Asset.asset_id == asset_id).first()
                        asset_name = asset.asset_name if asset else asset_id
                        asset_type = asset.asset_type if asset else 'Manual'
                        asset_class = asset.asset_class if asset else 'Other'
                        
                        current_holdings_map[asset_id] = {
                            'Asset_ID': asset_id,
                            'Asset_Name': asset_name,
                            'Asset_Type': asset_type,
                            'Asset_Class': asset_class,
                            'Quantity': 1.0,
                            'Cost_Basis': amount_cny,
                            'Average_Cost': amount_cny,
                            'Current_Price': amount_cny,
                            'Market_Value': amount_cny,
                            'Unrealized_PnL': 0.0,
                            'Unrealized_PnL_Pct': 0.0,
                            'Currency': 'CNY',
                            'Exchange_Rate': fx_rate,
                            'Source': 'BalanceSheet'
                        }
                        self.logger.info(f"Synced {asset_id} from Balance Sheet: {amount_cny:.2f}")

            # 4. Holdings Snapshot Sync REMOVED for Full DB Mode (Phase 10)
            # We now rely on reconciled transactions (Section 1) acting as the source of truth.
            
            # 5. Stale Filter REMOVED
            # FIFO logic handles zero-quantity assets automatically.
                             
        except Exception as e:
            self.logger.error(f"Error syncing with Balance Sheet/Holdings: {e}")

        # 6. Create holdings DataFrame from the combined data
        if not current_holdings_map:
            self.logger.warning("No active holdings found after transaction and balance sheet sync.")
            return pd.DataFrame()
        
        holdings_df = pd.DataFrame(list(current_holdings_map.values()))
        
        # 7. Calculate total portfolio value
        total_value = holdings_df['Market_Value'].sum()
        holdings_df['Weight'] = holdings_df['Market_Value'] / total_value
        
        self.logger.info(f"Calculated {len(holdings_df)} holdings with total value: ¥{total_value:,.2f}")
        
        return holdings_df
    
    def _get_transactions_up_to_date(self, as_of_date: date) -> pd.DataFrame:
        """
        Fetch all transactions from database up to a specific date.
        
        Returns:
            DataFrame with transaction data including asset metadata
        """
        try:
            # Query transactions with asset metadata
            from sqlalchemy import select
            
            statement = (
                select(
                    Transaction.id,
                    Transaction.date,
                    Transaction.asset_id,
                    Transaction.asset_name,
                    Transaction.transaction_type,
                    Transaction.shares,
                    Transaction.price,
                    Transaction.amount,
                    Transaction.currency,
                    Transaction.exchange_rate,
                    Asset.asset_type,
                    Asset.asset_class,
                    Asset.asset_subclass,
                )
                .join(Asset, Transaction.asset_id == Asset.asset_id)
                .where(Transaction.date <= as_of_date)
                .order_by(Transaction.date)
            )
            
            # Execute query
            with self.session.bind.connect() as connection:
                df = pd.read_sql(statement, connection)
            
            # Rename columns for consistency
            df = df.rename(columns={
                'asset_id': 'Asset_ID',
                'asset_name': 'Asset_Name',
                'transaction_type': 'Transaction_Type',
                'shares': 'Quantity',
                'price': 'Price_Unit',
                'amount': 'Amount_Net',
                'currency': 'Currency',
                'exchange_rate': 'Exchange_Rate',
                'asset_type': 'Asset_Type',
                'asset_class': 'Asset_Class',
                'asset_subclass': 'Asset_SubClass',
            })
            
            df['date'] = pd.to_datetime(df['date'])
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching transactions: {e}")
            raise
    
    def _calculate_asset_holding(
        self, 
        asset_id: str, 
        transactions: pd.DataFrame,
        as_of_date: date
    ) -> Optional[Dict]:
        """
        Calculate holding for a single asset using FIFO cost basis.
        
        Args:
            asset_id: Asset identifier
            transactions: DataFrame of transactions for this asset
            as_of_date: Date to calculate holding for
            
        Returns:
            Dictionary with holding details, or None if no holding
        """
        if transactions.empty:
            return None
        
        # Get asset metadata from first transaction
        asset_name = transactions.iloc[0]['Asset_Name']
        asset_type = transactions.iloc[0].get('Asset_Type', 'Unknown')
        asset_class = transactions.iloc[0].get('Asset_Class', 'Unknown')
        currency = transactions.iloc[0].get('Currency', 'CNY')
        
        # Enrich Asset_Type using taxonomy if database value is None/Unknown
        if not asset_type or asset_type == 'Unknown' or pd.isna(asset_type):
            try:
                from src.portfolio_lib.taxonomy_manager import TaxonomyManager
                taxonomy = TaxonomyManager()
                sub_class = taxonomy._get_asset_sub_class(asset_name)
                if sub_class and sub_class != 'Other':
                    asset_type = sub_class
                    self.logger.debug(f"Enriched Asset_Type for {asset_id} ({asset_name}): {asset_type}")
            except Exception as e:
                self.logger.warning(f"Could not enrich Asset_Type for {asset_id}: {e}")
        
        # Calculate FIFO cost basis
        quantity, cost_basis = self._calculate_fifo_cost_basis(transactions)
        
        if quantity <= 0:
            return None
        
        # Get current price from PriceService
        current_price = self.price_service.get_latest_price(asset_id, as_of_date)
        
        if current_price is None:
            self.logger.warning(f"No price available for {asset_id}, using cost basis")
            current_price = cost_basis / quantity if quantity > 0 else Decimal(0)
        
        # Calculate market value and P&L
        market_value = Decimal(quantity) * current_price
        
        # Currency Conversion (USD -> CNY)
        # TODO: Fetch real-time exchange rate from DataManager
        exchange_rate = Decimal('1.0')
        if currency == 'USD':
            exchange_rate = Decimal('7.05')  # Updated to match Excel FX rate
            market_value = market_value * exchange_rate
            # Note: Cost basis is already in CNY (converted during FIFO calculation)
            
        unrealized_pnl = market_value - cost_basis
        try:
            unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > Decimal(0) else Decimal(0)
        except Exception:
            # Handle NaN/Infinity/Invalid decimal states
            unrealized_pnl_pct = Decimal(0)
        average_cost = cost_basis / Decimal(quantity) if quantity > 0 else Decimal(0)

        
        return {
            'Asset_ID': asset_id,
            'Asset_Name': asset_name,
            'Asset_Type': asset_type,
            'Asset_Class': asset_class,
            'Quantity': float(quantity),
            'Cost_Basis': float(cost_basis),
            'Average_Cost': float(average_cost),
            'Current_Price': float(current_price),
            'Market_Value': float(market_value),
            'Unrealized_PnL': float(unrealized_pnl),
            'Unrealized_PnL_Pct': float(unrealized_pnl_pct),
            'Currency': currency,
            'Exchange_Rate': float(exchange_rate)
        }
    
    def _calculate_fifo_cost_basis(self, transactions: pd.DataFrame) -> Tuple[Decimal, Decimal]:
        """
        Calculate FIFO cost basis from transaction history.
        
        FIFO (First-In-First-Out) algorithm:
        - Buys are added to a queue with (quantity, unit_cost)
        - Sells remove from the front of the queue
        - Cost basis is the sum of remaining lots
        
        Args:
            transactions: DataFrame with Transaction_Type, Quantity, Price_Unit, Amount_Net
            
        Returns:
            Tuple of (net_quantity, total_cost_basis)
        """
        # Initialize FIFO queue: each entry is (quantity, unit_cost)
        fifo_queue: deque = deque()
        
        # Sort transactions: by date, then buys before sells (on same day)
        # This ensures vests are processed before same-day sells
        def txn_sort_key(row):
            txn_type = row['Transaction_Type']
            # Buys/Vests get priority 0, Sells get priority 1
            type_priority = 0 if txn_type in ['Buy', 'RSU_Vest', 'Dividend_Reinvest', 'Transfer_In', 'Adjustment_Buy'] else 1
            return (row['date'], type_priority)
        
        sorted_txns = transactions.sort_values(by=['date'], key=lambda x: x)
        sorted_txns = sorted_txns.assign(_sort_priority=sorted_txns['Transaction_Type'].apply(
            lambda t: 0 if t in ['Buy', 'RSU_Vest', 'Dividend_Reinvest', 'Transfer_In', 'Adjustment_Buy'] else 1
        )).sort_values(by=['date', '_sort_priority']).drop(columns=['_sort_priority'])
        
        # Process transactions in chronological order (buys before sells on same day)
        for _, txn in sorted_txns.iterrows():
            txn_type = txn['Transaction_Type']
            quantity = Decimal(str(txn.get('Quantity', 0) or 0))
            amount = Decimal(str(txn.get('Amount_Net', 0) or 0))
            
            # Normalize to CNY if needed
            exchange_rate = Decimal(str(txn.get('Exchange_Rate', 1) or 1))
            amount_cny = amount * exchange_rate
            
            if txn_type in ['Buy', 'RSU_Vest', 'Dividend_Reinvest', 'Adjustment_Buy']:
                # Add to FIFO queue
                if quantity > 0:
                    unit_cost = abs(amount_cny) / quantity
                    fifo_queue.append((quantity, unit_cost))
                    
            elif txn_type in ['Sell', 'Transfer_Out', 'Adjustment_Sell']:
                # Remove from FIFO queue
                remaining_to_sell = abs(quantity)
                
                while remaining_to_sell > 0 and fifo_queue:
                    lot_qty, lot_cost = fifo_queue[0]
                    
                    if lot_qty <= remaining_to_sell:
                        # Sell entire lot
                        fifo_queue.popleft()
                        remaining_to_sell -= lot_qty
                    else:
                        # Partial sell
                        fifo_queue[0] = (lot_qty - remaining_to_sell, lot_cost)
                        remaining_to_sell = Decimal(0)
                
                if remaining_to_sell > 0:
                    self.logger.warning(
                        f"Sell quantity exceeds available shares for {txn['Asset_ID']} on {txn['date']}"
                    )
            
            # Ignore other transaction types (Dividend_Cash, etc.)
        
        # Calculate final position
        net_quantity = sum(qty for qty, _ in fifo_queue)
        cost_basis = sum(qty * cost for qty, cost in fifo_queue)
        
        return net_quantity, cost_basis
    
    def calculate_historical_holdings(
        self, 
        dates: List[date]
    ) -> Dict[date, pd.DataFrame]:
        """
        Calculate holdings for multiple historical dates (batch operation).
        
        Args:
            dates: List of dates to calculate holdings for
            
        Returns:
            Dictionary mapping date to holdings DataFrame
        """
        holdings_history = {}
        
        for target_date in sorted(dates):
            self.logger.info(f"Calculating holdings for {target_date}...")
            holdings_df = self.calculate_current_holdings(target_date)
            holdings_history[target_date] = holdings_df
        
        return holdings_history
