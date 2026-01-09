"""
Cost Basis Calculator for Investment Portfolio Analysis

This module provides functionality to calculate cost basis, average cost, and unrealized P&L
for individual assets based on their transaction history using FIFO (First-In, First-Out) accounting.

Key features:
- FIFO lot tracking for accurate cost basis calculation
- Support for buy/sell transactions with proper lot management
- Average cost and unrealized P&L computation
- Comprehensive transaction validation and error handling
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
import logging
from .performance_calculator import PerformanceCalculator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# RSU accounting note:
# RSU vesting is treated as compensation income, not investment.
# Only the RETAINED shares (after sell-to-cover for taxes) represent actual investment.
# Cost basis = vest date FMV of retained shares
# Sell-to-cover transactions on vest date are tax payments, not investment sales.

class PurchaseLot:
    """
    Represents a single purchase lot with FIFO tracking capabilities.
    
    A purchase lot tracks shares purchased at a specific price on a specific date,
    and manages partial sales using FIFO (First-In, First-Out) methodology.
    """
    
    def __init__(self, date: pd.Timestamp, quantity: float, price: float, amount_net: float):
        """
        Initialize a purchase lot.
        
        Args:
            date: Purchase date
            quantity: Number of shares/units purchased
            price: Price per share/unit
            amount_net: Net amount paid (after fees)
        """
        self.purchase_date = date
        self.original_quantity = quantity
        self.remaining_quantity = quantity
        self.price_per_unit = price
        self.amount_net = amount_net
        self.cost_basis = amount_net  # Total cost basis for this lot
        
    def sell_shares(self, quantity_to_sell: float) -> Tuple[float, float]:
        """
        Sell shares from this lot using FIFO methodology.
        
        Args:
            quantity_to_sell: Number of shares to sell
            
        Returns:
            Tuple of (actual_quantity_sold, cost_basis_of_sold_shares)
        """
        if quantity_to_sell <= 0:
            return 0.0, 0.0
            
        # Can't sell more than what's remaining
        actual_quantity_sold = min(quantity_to_sell, self.remaining_quantity)
        
        # Calculate cost basis of sold shares using the original price per unit
        # This ensures consistent cost basis calculation regardless of previous sales
        cost_basis_sold = actual_quantity_sold * self.price_per_unit
            
        # Update remaining quantity and cost basis
        self.remaining_quantity -= actual_quantity_sold
        self.cost_basis -= cost_basis_sold
        
        return actual_quantity_sold, cost_basis_sold
    
    def is_empty(self) -> bool:
        """Check if this lot has been fully sold."""
        return self.remaining_quantity <= 1e-8  # Use small epsilon for floating point comparison
    
    def get_remaining_value(self) -> float:
        """Get the remaining cost basis value in this lot."""
        return self.cost_basis


class CostBasisCalculator:
    """
    Calculates cost basis, average cost, and unrealized P&L for a single asset
    using FIFO (First-In, First-Out) lot tracking methodology.
    
    This calculator processes a series of buy and sell transactions chronologically
    and maintains accurate lot-based cost accounting.
    """
    
    def __init__(self, asset_id: str, logger: logging.Logger = None):
        """
        Initialize cost basis calculator for a specific asset.
        
        Args:
            asset_id: Unique identifier for the asset
            logger: Logger instance
        """
        self.asset_id = asset_id
        self.logger = logger or logging.getLogger(__name__)
        self.lots: List[PurchaseLot] = []
        self.total_shares_sold = 0.0
        self.total_realized_profit = 0.0  # Deprecated, use realized_pnl
        self.total_shares_bought = 0.0
        self.total_amount_invested = 0.0
        self.total_amount_received = 0.0
        self.realized_pnl = 0.0
        self.processed_transactions = 0
        
        # Detect if this is Employer RSU for special handling
        self.is_employer_rsu = (asset_id == 'Employer_Stock_A')
        
        # Track sell-to-cover transactions to skip in normal sell processing
        self.sell_to_cover_dates: set = set()
        
    def process_transactions(self, transactions_df: pd.DataFrame) -> None:
        """
        Process all transactions chronologically with FIFO tracking.
        
        For RSU assets, this method implements special handling:
        - RSU_Vest transactions on the same date as Sell transactions are paired
        - The Sell is treated as "sell-to-cover" for tax withholding (typically 45%)
        - Only the retained shares (typically 55%) are added to cost basis
        - The vest date FMV becomes the cost basis for retained shares
        
        Args:
            transactions_df: DataFrame with transaction history (Date, Transaction_Type, Quantity, Price_Unit, Amount_Net)
        """
        if transactions_df.empty:
            logger.warning(f"No transactions to process for {self.asset_id}")
            return
        
        # Define transaction priority (lower number = process first within same date)
        transaction_priority = {
            'RSU_Grant': 1,
            'RSU_Vest': 2,
            'Sell': 3,  # Process sell-to-cover right after vest
            'Buy': 4,
            'Dividend_Reinvest': 5
        }
        
        # Add priority column for sorting within same dates
        transactions_df = transactions_df.copy()
        transactions_df['_priority'] = transactions_df['Transaction_Type'].map(
            lambda x: transaction_priority.get(x, 10)
        )
        
        # Sort by date first, then by priority within same date
        index_name = transactions_df.index.name or 'index'
        if index_name in transactions_df.columns:
            # Date is a column, sort by it
            transactions_df = transactions_df.sort_values([index_name, '_priority'])
        else:
            # Date is the index, sort by index then priority
            transactions_df = transactions_df.reset_index().sort_values([index_name, '_priority']).set_index(index_name)
        
        # Pre-scan for RSU vest + same-date sell pairs to identify sell-to-cover
        if self.is_employer_rsu:
            self._identify_sell_to_cover_transactions(transactions_df)
        
        for date, transaction in transactions_df.iterrows():
            try:
                self._process_single_transaction(date, transaction)
                self.processed_transactions += 1
            except Exception as e:
                logger.error(f"Error processing transaction for {self.asset_id} on {date}: {e}")
                continue
                
        logger.info(f"Processed {self.processed_transactions} transactions for {self.asset_id}")
        self._cleanup_empty_lots()
    
    def _identify_sell_to_cover_transactions(self, transactions_df: pd.DataFrame) -> None:
        """
        Identify sell transactions that are paired with RSU_Vest on the same date.
        These are "sell-to-cover" transactions for tax withholding, not investment sales.
        
        This method stores the net retained shares for each vest date so we can
        create lots with only the retained portion.
        
        Args:
            transactions_df: Sorted transaction DataFrame
        """
        # Store {date: (vested_shares, sold_shares, vest_price_cny)} for RSU processing
        self.rsu_vest_info = {}
        
        # Group transactions by date
        if isinstance(transactions_df.index, pd.DatetimeIndex):
            grouped = transactions_df.groupby(transactions_df.index.date)
        else:
            grouped = transactions_df.groupby('Date')
        
        # Import currency converter for USD to CNY conversion
        from ..data_manager.currency_converter import get_currency_service
        converter = get_currency_service()
        
        for date, group in grouped:
            vest_txns = group[group['Transaction_Type'] == 'RSU_Vest']
            sell_txns = group[group['Transaction_Type'] == 'Sell']
            
            if not vest_txns.empty and not sell_txns.empty:
                # Mark this date's sell as sell-to-cover
                vest_shares = vest_txns['Quantity'].sum()
                sell_shares = abs(sell_txns['Quantity'].sum())
                
                # Extract vest price from amount_net / quantity
                vest_amount_usd = abs(vest_txns['Amount_Net'].sum())
                vest_price_usd = vest_amount_usd / vest_shares if vest_amount_usd > 0 else vest_txns['Price_Unit'].iloc[0]
                
                # Convert USD price to CNY
                currency = vest_txns.iloc[0].get('Currency', 'CNY')
                if currency == 'USD':
                    vest_amount_cny = converter.convert_amount(vest_amount_usd, 'USD', 'CNY', pd.Timestamp(date))
                    vest_price_cny = vest_amount_cny / vest_shares
                else:
                    vest_price_cny = vest_price_usd
                
                self.sell_to_cover_dates.add(pd.Timestamp(date))
                self.rsu_vest_info[pd.Timestamp(date)] = (vest_shares, sell_shares, vest_price_cny)
                
                retained_shares = vest_shares - sell_shares
                logger.info(f"RSU {self.asset_id} {date}: Vest+Sell-to-cover detected - {vest_shares:.2f} vested, {sell_shares:.2f} sold, {retained_shares:.2f} retained @ {vest_price_cny:.2f} CNY/share")
    
    def _process_single_transaction(self, date: pd.Timestamp, transaction: pd.Series) -> None:
        """
        Process a single transaction (buy or sell).
        
        Args:
            date: Transaction date
            transaction: Transaction data series
        """
        transaction_type = transaction.get('Transaction_Type', '').strip()
        quantity = float(transaction.get('Quantity', 0))
        price_unit = float(transaction.get('Price_Unit', 0))
        amount_net = float(transaction.get('Amount_Net', 0))
        
        # Currency conversion: Convert USD amounts to CNY
        currency = transaction.get('Currency', 'CNY')
        if currency == 'USD' and amount_net != 0:
            # Import currency converter
            from ..data_manager.currency_converter import get_currency_service
            converter = get_currency_service()
            # Convert amount_net from USD to CNY using historical rate
            amount_net_cny = converter.convert_amount(abs(amount_net), 'USD', 'CNY', date)
            # Preserve the sign of the original amount
            amount_net = amount_net_cny if amount_net > 0 else -amount_net_cny
            logger.debug(f"{self.asset_id} {date.date()}: Converted {transaction.get('Amount_Net', 0):.2f} USD to {amount_net:.2f} CNY")
        
        # Skip transactions with zero quantity or invalid data
        # EXCEPT for dividend/income transactions with non-zero amount_net
        if quantity == 0 or pd.isna(quantity):
            # For Sell, Dividend_Cash, or Interest transactions with NaN quantity but positive amount_net:
            # These are cash distributions (dividends, interest, returns) that don't affect share count
            # Count the proceeds in total_amount_received but DON'T reduce share count
            if transaction_type in ['Sell', 'Dividend_Cash', 'Interest'] and abs(amount_net) > 1e-6:
                cash_received = abs(amount_net)
                self.total_amount_received += cash_received
                # Treat this as pure income (no cost basis), so it's all realized profit
                self.realized_pnl += cash_received
                logger.info(f"{self.asset_id} {date.date()}: Recorded cash distribution ({transaction_type}) of ¥{cash_received:.2f} with no share reduction")
                return  # Don't process further
            else:
                return
            
        if transaction_type == 'Buy':
            self._process_buy_transaction(date, quantity, price_unit, amount_net)
        elif transaction_type == 'Sell':
            # Check if this is a sell-to-cover transaction that should be ignored
            if self.is_employer_rsu and date in self.sell_to_cover_dates:
                logger.info(f"RSU {self.asset_id} {date.date()}: Skipping sell-to-cover transaction ({abs(quantity):.2f} shares)")
                return
            self._process_sell_transaction(date, quantity, price_unit, amount_net)
        elif transaction_type in ['RSU_Grant', 'RSU_Vest']:
            # RSU Vest: Only add retained shares (after sell-to-cover) to cost basis
            if quantity > 0:
                if self.is_employer_rsu and date in self.sell_to_cover_dates:
                    # This vest has a paired sell-to-cover on same date
                    # Use the pre-calculated retained shares
                    vest_shares, sell_shares, vest_price = self.rsu_vest_info[date]
                    retained_shares = vest_shares - sell_shares
                    retained_cost = retained_shares * vest_price
                    
                    # Create lot with ONLY the retained shares
                    self._process_buy_transaction(date, retained_shares, vest_price, -retained_cost)
                    logger.info(f"RSU {self.asset_id} {date.date()}: Added {retained_shares:.2f} retained shares @ {vest_price:.2f} CNY/share (cost basis: {retained_cost:.2f} CNY)")
                else:
                    # Normal vest without sell-to-cover (or RSU_Grant)
                    self._process_buy_transaction(date, quantity, price_unit, amount_net)
        elif transaction_type in ['Dividend_Cash', 'Dividend_Reinvest', 'Interest']:
            # Handle dividend/interest distributions
            if transaction_type == 'Dividend_Reinvest' and quantity > 0:
                # CRITICAL FIX: Dividend reinvestment represents:
                # 1. A dividend distribution (income/profit) that is
                # 2. Immediately reinvested into new shares
                # 
                # The NEW SHARES should have ZERO cost basis because:
                # - The dividend itself is profit (return OF capital)
                # - No new money was invested by the user
                # - Treating NAV as cost inflates cost basis and hides profit
                #
                # Calculate the dividend VALUE (shares * NAV at reinvestment)
                dividend_value = abs(quantity * price_unit)
                
                # Record dividend as realized profit (income received)
                self.total_amount_received += dividend_value
                self.realized_pnl += dividend_value
                logger.info(f"{self.asset_id} {date.date()}: Dividend reinvested - {quantity:.2f} shares @ ¥{price_unit:.4f} = ¥{dividend_value:.2f} recorded as realized profit")
                
                # Create lot with ZERO cost basis for the reinvested shares
                # This ensures future sells of these shares create proper gains
                self._process_buy_transaction(date, quantity, 0.0, 0.0)
                
            elif transaction_type in ['Dividend_Cash', 'Interest'] and abs(amount_net) > 1e-6:
                # CRITICAL FIX: Dividend_Cash and Interest transactions are pure income
                # They increase total_amount_received and realized_pnl WITHOUT reducing share count
                cash_received = abs(amount_net)
                self.total_amount_received += cash_received
                self.realized_pnl += cash_received
                logger.info(f"{self.asset_id} {date.date()}: Recorded dividend/interest distribution of ¥{cash_received:.2f} with no share reduction")
            # Note: Cash dividends with zero amount don't affect cost basis
        elif transaction_type in ['Adjustment_Buy']:
             self._process_buy_transaction(date, quantity, price_unit, amount_net)
        elif transaction_type in ['Adjustment_Sell', 'Redemption']:
             self._process_sell_transaction(date, quantity, price_unit, amount_net)


    
    def _process_buy_transaction(self, date: pd.Timestamp, quantity: float, 
                               price_unit: float, amount_net: float) -> None:
        """
        Process a buy transaction by creating a new purchase lot.
        
        Args:
            date: Purchase date
            quantity: Shares purchased
            price_unit: Price per share
            amount_net: Net amount invested (negative for outflows)
        """
        # Amount_net for buys should be negative (outflow), but we store cost as positive
        # Handle NaN amount_net by falling back to quantity * price_unit
        if pd.isna(amount_net) or amount_net == 0:
            cost_amount = quantity * price_unit
        else:
            cost_amount = abs(amount_net)
        # Calculate actual price per unit from cost and quantity
        actual_price_per_unit = cost_amount / quantity if quantity > 0 else price_unit
        
        # Create new purchase lot
        lot = PurchaseLot(date, quantity, actual_price_per_unit, cost_amount)
        self.lots.append(lot)
        
        # Update totals
        self.total_shares_bought += quantity
        self.total_amount_invested += cost_amount
        
        logger.debug(f"{self.asset_id} Buy: {quantity:.4f} shares @ {actual_price_per_unit:.2f} per share, cost basis: {cost_amount:.2f}")
    
    def _process_sell_transaction(self, date: pd.Timestamp, quantity: float, 
                                price_unit: float, amount_net: float) -> None:
        """
        Process a sell transaction using FIFO methodology.
        
        Special handling for near-zero quantity sales (e.g., dividend reinvestment redemptions):
        - If quantity is near-zero but amount_net > 0, estimate shares sold from average cost basis
        - This handles automatic conversions where quantity data is lost but proceeds are recorded
        
        Args:
            date: Sale date
            quantity: Shares sold (should be positive)
            price_unit: Sale price per share
            amount_net: Net amount received (positive for inflows)
        """
        quantity_to_sell = abs(quantity)  # Ensure positive quantity
        sale_proceeds = abs(amount_net) if amount_net != 0 else quantity_to_sell * price_unit
        total_cost_basis_sold = 0.0
        
        # Special case: Near-zero quantity but non-zero proceeds (dividend reinvestment redemption, auto-conversion)
        # Estimate the shares sold based on average cost basis of FIFO lots
        if quantity_to_sell < 1e-6 and sale_proceeds > 1e-6:
            # Calculate average cost per share from available lots (FIFO order)
            if self.lots:
                # Use weighted average cost of first few lots (FI FO)
                total_shares_available = sum(lot.remaining_quantity for lot in self.lots)
                total_cost_available = sum(lot.remaining_quantity * lot.price_per_unit for lot in self.lots)
                if total_shares_available > 0:
                    avg_cost_per_share = total_cost_available / total_shares_available
                    # Estimate shares sold from proceeds
                    estimated_shares = sale_proceeds / avg_cost_per_share if avg_cost_per_share > 0 else 0
                    quantity_to_sell = estimated_shares
                    logger.info(f"{self.asset_id} {date.date()}: Estimated {estimated_shares:.2f} shares sold from proceeds ¥{sale_proceeds:.2f} (avg cost: ¥{avg_cost_per_share:.2f}/share)")
        
        # DEBUG: Trace heavy sell logic
        if '1856' in str(self.asset_id):
             logger.info(f"DEBUG {self.asset_id} SELL: Qty={quantity}, Price={price_unit}, Net={amount_net}, Proceeds={sale_proceeds}")

        # Sell shares from lots using FIFO
        remaining_to_sell = quantity_to_sell
        for lot in self.lots:
            if remaining_to_sell <= 0 or lot.is_empty():
                continue
            quantity_sold, cost_basis_sold = lot.sell_shares(remaining_to_sell)
            total_cost_basis_sold += cost_basis_sold
            remaining_to_sell -= quantity_sold
            if remaining_to_sell <= 0:
                break
        
        # Update totals
        self.total_shares_sold += quantity_to_sell
        self.total_amount_received += sale_proceeds
        self.realized_pnl += (sale_proceeds - total_cost_basis_sold)
        
        # Warn if we couldn't sell all requested shares
        if remaining_to_sell > 1e-8:
            logger.warning(f"Could not sell {remaining_to_sell} shares for {self.asset_id} - insufficient holdings")
    
    def _cleanup_empty_lots(self) -> None:
        """Remove lots that have been fully sold."""
        self.lots = [lot for lot in self.lots if not lot.is_empty()]
    
    def get_current_position(self) -> float:
        """Get current number of shares held."""
        return sum(lot.remaining_quantity for lot in self.lots)
    
    def get_total_cost_basis(self) -> float:
        """Get total cost basis of current holdings."""
        return sum(lot.get_remaining_value() for lot in self.lots)
    
    def get_average_cost(self) -> float:
        """Calculate average cost per share of current holdings."""
        current_position = self.get_current_position()
        if current_position <= 0:
            return 0.0
        return self.get_total_cost_basis() / current_position
    
    def get_unrealized_pnl(self, current_market_price: float) -> float:
        """
        Calculate unrealized P&L based on current market price.
        
        Args:
            current_market_price: Current market price per share
            
        Returns:
            Unrealized profit/loss
        """
        current_position = self.get_current_position()
        if current_position <= 0:
            return 0.0
            
        current_market_value = current_position * current_market_price
        total_cost_basis = self.get_total_cost_basis()
        
        return current_market_value - total_cost_basis
    
    def get_summary(self, current_market_price: Optional[float] = None) -> Dict[str, Any]:
        """
        Get comprehensive summary of cost basis analysis.
        
        Args:
            current_market_price: Current market price (optional)
            
        Returns:
            Dictionary with cost basis summary
        """
        current_position = self.get_current_position()
        total_cost_basis = self.get_total_cost_basis()
        average_cost = self.get_average_cost()
        
        summary = {
            'asset_id': self.asset_id,
            'current_position': current_position,
            'total_cost_basis': total_cost_basis,
            'average_cost': average_cost,
            'total_shares_bought': self.total_shares_bought,
            'total_shares_sold': self.total_shares_sold,
            'total_amount_invested': self.total_amount_invested,
            'total_amount_received': self.total_amount_received,
            'realized_pnl': self.realized_pnl,
            'active_lots': len(self.lots),
            'processed_transactions': self.processed_transactions
        }
        
        if current_market_price is not None and current_market_price > 0:
            unrealized_pnl = self.get_unrealized_pnl(current_market_price)
            current_market_value = current_position * current_market_price
            total_return_pct = ((current_market_value + self.total_amount_received - self.total_amount_invested) / 
                              self.total_amount_invested * 100) if self.total_amount_invested > 0 else 0.0
            
            summary.update({
                'current_market_price': current_market_price,
                'current_market_value': current_market_value,
                'unrealized_pnl': unrealized_pnl,
                'total_pnl': self.realized_pnl + unrealized_pnl,
                'total_return_pct': total_return_pct
            })
        

        


        return summary


def calculate_cost_basis_for_portfolio(transactions_df: pd.DataFrame, 
                                     current_prices: Optional[Dict[str, float]] = None) -> Dict[str, Dict[str, Any]]:
    """
    Calculate cost basis for all assets in a portfolio.
    
    Args:
        transactions_df: DataFrame with all transactions, indexed by date
        current_prices: Optional dictionary mapping asset_id to current price
        
    Returns:
        Dictionary mapping asset_id to cost basis summary
    """
    if transactions_df is None or transactions_df.empty:
        logger.warning("No transaction data provided")
        return {}
    
    current_prices = current_prices or {}
    results = {}
    
    # Group transactions by asset
    asset_groups = transactions_df.groupby('Asset_ID')
    
    for asset_id, asset_transactions in asset_groups:
        try:
            calculator = CostBasisCalculator(asset_id)
            calculator.process_transactions(asset_transactions)
            
            current_price = current_prices.get(asset_id)
            summary = calculator.get_summary(current_price)
            results[asset_id] = summary
            
        except Exception as e:
            logger.error(f"Failed to calculate cost basis for {asset_id}: {e}")
            continue
    
    logger.info(f"Calculated cost basis for {len(results)} assets")
    return results


def get_lifetime_asset_performance(transactions_df: pd.DataFrame, 
                                  current_holdings_df: pd.DataFrame = None) -> List[Dict[str, Any]]:
    """
    Get comprehensive performance data for all assets ever held, including sold ones.
    Excludes insurance assets from investment analysis.
    
    Args:
        transactions_df: DataFrame with all transactions
        current_holdings_df: Optional current holdings DataFrame with market values
        
    Returns:
        List of dictionaries with performance data for each asset ever held
    """
    if transactions_df is None or transactions_df.empty:
        logger.warning("No transaction data provided for lifetime performance analysis")
        return []
    
    # Exclude insurance assets from investment analysis
    non_insurance_transactions = transactions_df[
        (~transactions_df['Asset_ID'].str.contains('Ins_', na=False))
    ].copy()
    
    if non_insurance_transactions.empty:
        logger.warning("No non-insurance transaction data for lifetime performance analysis")
        return []
    
    # Build current prices and holdings info
    current_prices = {}
    currently_held_assets = set()
    current_holdings_lookup = {}
    
    if current_holdings_df is not None and not current_holdings_df.empty:
        # Get asset IDs from index (MultiIndex) 
        if hasattr(current_holdings_df.index, 'levels'):
            currently_held_assets = set(current_holdings_df.index.get_level_values('Asset_ID'))
        else:
            # Fallback: look for Asset_ID column
            if 'Asset_ID' in current_holdings_df.columns:
                currently_held_assets = set(current_holdings_df['Asset_ID'].dropna())
        
        # Build prices and holdings lookup
        for idx, holding in current_holdings_df.iterrows():
            if hasattr(idx, '__len__') and len(idx) >= 2:
                asset_id = idx[1]  # Asset_ID from MultiIndex
            else:
                asset_id = holding.get('Asset_ID')
                
            asset_name = holding.get('Asset_Name', asset_id)
            quantity = holding.get('Quantity', 0)
            # FIXED: Use Market_Value_CNY for price since transactions are now converted to CNY
            # at transaction processing level in _process_single_transaction
            market_value_cny = holding.get('Market_Value_CNY', 0)
            
            # Handle assets with NaN or 0 quantity (like Property, Insurance)
            # For these assets, use market value directly without dividing by quantity
            if pd.isna(quantity) or quantity == 0:
                # For non-divisible assets (Property, Insurance), treat as 1 unit
                if asset_id and market_value_cny > 0:
                    currently_held_assets.add(asset_id)
                    current_prices[asset_id] = market_value_cny  # Treat entire value as "unit price"
                    current_holdings_lookup[asset_id] = {
                        'asset_name': asset_name,
                        'current_quantity': 1.0,  # Synthetic quantity
                        'current_market_value': market_value_cny
                    }
            elif asset_id and quantity > 0 and market_value_cny > 0:
                currently_held_assets.add(asset_id)
                # Use Market_Value_CNY for price (converted from USD if needed)
                current_prices[asset_id] = market_value_cny / quantity
                current_holdings_lookup[asset_id] = {
                    'asset_name': asset_name,
                    'current_quantity': quantity,
                    'current_market_value': market_value_cny
                }
    
    # Calculate cost basis for all non-insurance assets
    cost_basis_results = calculate_cost_basis_for_portfolio(non_insurance_transactions, current_prices)
    
    # Load asset taxonomy for classification
    taxonomy_config = {}
    try:
        import yaml
        import os
        config_path = os.path.join(os.getcwd(), 'config', 'asset_taxonomy.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            taxonomy_config = yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Could not load asset taxonomy config: {e}")
    
    # Get comprehensive asset mapping from taxonomy
    asset_class_mapping = taxonomy_config.get('asset_id_mapping', {})
    raw_type_mapping = taxonomy_config.get('raw_type_mapping', {})
    unified_asset_mapping = taxonomy_config.get('asset_mapping', {})  # Fallback (now unified)

    # Build lifetime performance data
    lifetime_performance = []
    
    # Get unique non-insurance assets from transactions (includes sold assets)
    unique_assets = non_insurance_transactions['Asset_ID'].unique()
    
    # Get asset names and types from transactions
    try:
        asset_info = non_insurance_transactions.groupby('Asset_ID').agg({
            'Asset_Name': 'first',
            'Asset_Type_Raw': 'first'
        }).to_dict('index')
    except KeyError:
        # If Asset_Type_Raw doesn't exist, just get Asset_Name
        asset_info = non_insurance_transactions.groupby('Asset_ID').agg({
            'Asset_Name': 'first'
        }).to_dict('index')
        # Add empty Asset_Type_Raw for all assets
        for asset_id in asset_info:
            asset_info[asset_id]['Asset_Type_Raw'] = 'Unknown'
    
    # --- Helper: Initialize unified PerformanceCalculator ---
    performance_calc = PerformanceCalculator()

    for asset_id in unique_assets:
        # Skip insurance assets
        if 'Ins_' in str(asset_id):
            continue
            
        if asset_id in cost_basis_results:
            cb_data = cost_basis_results[asset_id]
            
            # Check if asset is currently held
            is_currently_held = asset_id in currently_held_assets
            current_info = current_holdings_lookup.get(asset_id, {})
            
            # Get asset info from transactions
            asset_data = asset_info.get(asset_id, {})
            asset_name = asset_data.get('Asset_Name', current_info.get('asset_name', asset_id))
            asset_type_raw = asset_data.get('Asset_Type_Raw', 'Unknown')
            
            # Determine asset sub-class using multiple mapping strategies
            asset_sub_class = 'Unknown'
            # Priority 1: explicit asset_id_mapping (ID)
            if asset_id in asset_class_mapping:
                asset_sub_class = asset_class_mapping[asset_id]
            # Priority 2: explicit asset_id_mapping (asset name key)
            elif asset_name in asset_class_mapping:
                asset_sub_class = asset_class_mapping[asset_name]
            # Priority 3: raw_type_mapping
            elif asset_type_raw in raw_type_mapping:
                asset_sub_class = raw_type_mapping[asset_type_raw]
            # Priority 4: unified asset_mapping (can include tickers & names)
            elif asset_id in unified_asset_mapping:
                asset_sub_class = unified_asset_mapping[asset_id]
            elif asset_name in unified_asset_mapping:
                asset_sub_class = unified_asset_mapping[asset_name]
            elif asset_type_raw:
                # Try pattern matching for common types
                type_lower = str(asset_type_raw).lower()
                if any(keyword in type_lower for keyword in ['股票', 'stock', 'equity']):
                    asset_sub_class = '国内股票ETF'
                elif any(keyword in type_lower for keyword in ['指数', 'index', 'etf']):
                    asset_sub_class = '国内股票ETF'
                elif any(keyword in type_lower for keyword in ['混合', 'mixed', 'balanced']):
                    asset_sub_class = '国内股票ETF'  # Most mixed funds are equity-heavy
                elif any(keyword in type_lower for keyword in ['债券', 'bond', 'fixed']):
                    asset_sub_class = '企业债券'
                elif any(keyword in type_lower for keyword in ['货币', 'money', 'cash']):
                    asset_sub_class = '现金'
                elif any(keyword in type_lower for keyword in ['黄金', 'gold', '商品']):
                    asset_sub_class = '黄金'
            
            # Map sub-class to top-level asset class
            sub_class_to_top_level = {
                # 股票 sub-classes
                '国内股票ETF': '股票',
                'CN Equity': '股票',
                'HK ETF': '股票', 
                '港股ETF': '股票', 
                '美国股票ETF': '股票',
                'US Equity': '股票',
                '公司美股RSU': '股票',
                '新兴市场股票': '股票',
                
                # 固定收益 sub-classes
                '国内政府债券': '固定收益',
                'Domestic Government Bonds': '固定收益',
                '美国政府债券': '固定收益',
                'US Government Bonds': '固定收益',
                '企业债券': '固定收益',
                '高收益债券': '固定收益',
                '货币市场': '固定收益',
                '银行理财': '固定收益',
                
                # 房地产 sub-classes
                '住宅地产': '房地产',
                '商业地产': '房地产',
                '房地产信托': '房地产',
                
                # 商品 sub-classes
                '黄金': '商品',
                'Gold': '商品',
                '其他贵金属': '商品',
                '能源': '商品',
                '农产品': '商品',
                
                # 现金 sub-classes
                '现金': '现金',
                'Cash': '现金',
                'Money Market': '现金',
                '活期存款': '现金',
                '定期存款': '现金',
                
                # 另类投资 sub-classes
                '创业投资': '另类投资',
                '加密货币': '另类投资',
                'Cryptocurrency': '另类投资',
                '风险投资': '另类投资',
            }
            
            asset_class = sub_class_to_top_level.get(asset_sub_class, 'Unknown')
            
            # Get transaction date range
            asset_transactions = non_insurance_transactions[non_insurance_transactions['Asset_ID'] == asset_id]
            first_transaction_date = asset_transactions.index.min()
            last_transaction_date = asset_transactions.index.max()
            
            # Calculate holding period
            if pd.notna(first_transaction_date) and pd.notna(last_transaction_date):
                if is_currently_held:
                    holding_period_days = (pd.Timestamp.now() - first_transaction_date).days
                    end_date_str = 'Present'
                else:
                    holding_period_days = (last_transaction_date - first_transaction_date).days
                    end_date_str = last_transaction_date.strftime('%Y-%m-%d')
            else:
                holding_period_days = 0
                end_date_str = 'Unknown'
            
            # Calculate total return
            # Use cost basis calculator data for accurate invested/received amounts
            # This properly handles Buy, RSU_Vest, Dividend_Reinvest, and all transaction types
            
            total_invested = cb_data.get('total_amount_invested', 0.0)
            total_received = cb_data.get('total_amount_received', 0.0)
            realized_pnl = cb_data.get('realized_pnl', 0.0)
            
            # Calculate P/L using cost basis data
            if is_currently_held and current_info.get('current_market_value', 0) > 1e-6:
                current_market_value = current_info.get('current_market_value', 0.0)
                # Get unrealized PnL from cost basis data (calculated with current price)
                unrealized_pnl = cb_data.get('unrealized_pnl', 0.0)
                # If not available, calculate it
                if unrealized_pnl == 0.0 or 'unrealized_pnl' not in cb_data:
                    total_cost_basis = cb_data.get('total_cost_basis', 0.0)
                    unrealized_pnl = current_market_value - total_cost_basis
                total_return_abs = realized_pnl + unrealized_pnl
                logger.debug(f"{asset_id}: Cost basis method - Invested ¥{total_invested:,.2f}, Received ¥{total_received:,.2f}, Current ¥{current_market_value:,.2f}, Total P/L ¥{total_return_abs:,.2f}")
            else:
                # Asset fully sold - all P/L is realized
                total_return_abs = realized_pnl
                unrealized_pnl = 0.0
            
            # CRITICAL FIX: Get asset currency and convert USD values to CNY for display
            # The cost basis calculation now returns values in original currency (USD for US assets)
            asset_currency = 'CNY'  # Default
            if current_holdings_df is not None and not current_holdings_df.empty:
                # Try to find currency from holdings
                if hasattr(current_holdings_df.index, 'levels'):
                    asset_holdings = current_holdings_df[current_holdings_df.index.get_level_values('Asset_ID') == asset_id]
                    if not asset_holdings.empty:
                        asset_currency = asset_holdings.iloc[0].get('Currency', 'CNY')
                else:
                    # Fallback: check from transactions
                    if 'Currency' in asset_transactions.columns:
                        currencies = asset_transactions['Currency'].dropna().unique()
                        if len(currencies) > 0:
                            asset_currency = currencies[0]
            
            # FIXED: Currency conversion now happens at transaction processing level in _process_single_transaction
            # P/L values from cost_basis calculator are already in CNY, no need to convert again
            realized_pnl_cny = realized_pnl
            unrealized_pnl_cny = unrealized_pnl
            total_return_abs_cny = total_return_abs
            
            total_return_pct = (total_return_abs / total_invested * 100) if total_invested > 0 else 0.0
            
            # Prepare cash flows for lifetime XIRR
            xirr_pct = None
            try:
                if not asset_transactions.empty and 'Amount_Net' in asset_transactions.columns:
                    cf_dates = asset_transactions.index.to_list()
                    cf_flows = asset_transactions['Amount_Net'].astype(float).to_list()
                    
                    # FIXED: Convert USD amounts to CNY for XIRR calculation
                    if 'Currency' in asset_transactions.columns:
                        from ..data_manager.currency_converter import get_currency_service
                        converter = get_currency_service()
                        cf_flows_cny = []
                        for idx, (date, amount) in enumerate(zip(cf_dates, cf_flows)):
                            # Handle multiple transactions on same date by using iloc instead of loc
                            currency = asset_transactions.iloc[idx]['Currency'] if 'Currency' in asset_transactions.columns else 'CNY'
                            if currency == 'USD' and amount != 0:
                                # Convert USD to CNY
                                amount_cny = converter.convert_amount(abs(amount), 'USD', 'CNY', date)
                                cf_flows_cny.append(amount_cny if amount > 0 else -amount_cny)
                            else:
                                cf_flows_cny.append(amount)
                        cf_flows = cf_flows_cny
                    
                    # If still holding, append current market value as terminal inflow at 'now'
                    if is_currently_held and current_info.get('current_market_value', 0) > 1e-6:
                        cf_dates.append(pd.Timestamp.now())
                        cf_flows.append(current_info.get('current_market_value', 0.0))
                    
                    # Use PerformanceCalculator for unified XIRR calculation
                    xirr_result = performance_calc.calculate_xirr(cf_dates, cf_flows, context_id=str(asset_id))
                    xirr_pct = xirr_result.get('xirr')  # Extract the XIRR percentage value
            except Exception as e:
                logger.warning(f"Failed to calculate XIRR for {asset_id}: {e}")
                xirr_pct = None

            # Build performance record
            performance_record = {
                'asset_id': asset_id,
                'asset_name': asset_name,
                'asset_class': asset_class,
                'asset_sub_class': asset_sub_class,
                'asset_type_raw': asset_type_raw,
                'is_currently_held': is_currently_held,
                'first_transaction_date': first_transaction_date,
                'last_transaction_date': last_transaction_date,
                'end_date_str': end_date_str,
                'holding_period_days': holding_period_days,
                'total_shares_bought': cb_data.get('total_shares_bought', 0.0),
                'total_shares_sold': cb_data.get('total_shares_sold', 0.0),
                'current_position': cb_data.get('current_position', 0.0),
                'total_amount_invested': total_invested,
                'total_amount_received': cb_data.get('total_amount_received', 0.0),
                # Use CNY-converted values for HTML display
                'realized_pnl': realized_pnl_cny,
                'unrealized_pnl': unrealized_pnl_cny,
                'total_pnl': total_return_abs_cny,
                'current_market_value': current_info.get('current_market_value', 0.0),
                'cost_basis_total': cb_data.get('total_cost_basis', 0.0),
                'average_cost': cb_data.get('average_cost', 0.0),
                'total_return_pct': total_return_pct,  # Simple total ROI (%)
                # Annualized XIRR if computable; fallback to simple total return pct
                'total_return_pct_calc': xirr_pct if xirr_pct is not None else total_return_pct,
                'xirr_pct': xirr_pct,
                'total_return_amount': total_return_abs_cny  # Use CNY-converted value
            }
                
            lifetime_performance.append(performance_record)
    
    # Sort by total return amount descending for better presentation
    lifetime_performance.sort(key=lambda x: x['total_return_amount'], reverse=True)
    
    logger.info(f"Generated lifetime performance data for {len(lifetime_performance)} assets")
    
    return lifetime_performance


def get_gains_analysis(transactions_df: pd.DataFrame, 
                      current_holdings_df: pd.DataFrame = None,
                      include_subclass_breakdown: bool = False) -> Dict[str, float]:
    """
    Calculate portfolio-wide realized and unrealized gains analysis.
    
    Realized gains: From assets that have been sold (fully or partially)
    Unrealized gains: From assets that are currently held in the portfolio
    
    Args:
        transactions_df: DataFrame with all transactions
        current_holdings_df: Optional current holdings DataFrame with market values
        include_subclass_breakdown: bool: Whether to include sub-class level breakdown
        
    Returns:
        Dictionary with total realized gains, unrealized gains, and total gains
        If include_subclass_breakdown=True, also includes 'subclass_breakdown' key
    """
    if transactions_df is None or transactions_df.empty:
        logger.warning("No transaction data provided for gains analysis")
        return {
            "realized_gains": 0.0,
            "unrealized_gains": 0.0,
            "total_gains": 0.0
        }
    
    # Exclude insurance assets and funds with known data issues from investment analysis
    # 004863 (泰康现金管家货币C): Money market bridge fund with missing buy transactions
    EXCLUDED_ASSET_IDS = ['4863', '004863']
    non_insurance_transactions = transactions_df[
        (~transactions_df['Asset_ID'].str.contains('Ins_', na=False)) &
        (~transactions_df['Asset_ID'].astype(str).isin(EXCLUDED_ASSET_IDS))
    ].copy()
    
    if non_insurance_transactions.empty:
        logger.warning("No non-insurance transaction data for gains analysis")
        return {
            "realized_gains": 0.0,
            "unrealized_gains": 0.0,
            "total_gains": 0.0
        }
    
    # Build current holdings set and prices dictionary
    currently_held_assets = set()
    current_prices = {}
    if current_holdings_df is not None and not current_holdings_df.empty:
        # Get asset IDs from index (MultiIndex) 
        if hasattr(current_holdings_df.index, 'levels'):
            currently_held_assets = set(current_holdings_df.index.get_level_values('Asset_ID'))
        else:
            # Fallback: look for Asset_ID column
            if 'Asset_ID' in current_holdings_df.columns:
                currently_held_assets = set(current_holdings_df['Asset_ID'].dropna())
        
        # Build prices dictionary using Market_Value_Raw to preserve original currency
        for idx, holding in current_holdings_df.iterrows():
            if hasattr(idx, '__len__') and len(idx) >= 2:
                asset_id = idx[1]  # Asset_ID from MultiIndex
            else:
                asset_id = holding.get('Asset_ID')
                
            quantity = holding.get('Quantity', 0)
            # FIXED: Use Market_Value_CNY since transactions are now converted to CNY
            market_value_cny = holding.get('Market_Value_CNY', 0)
            
            if asset_id and quantity > 0 and market_value_cny > 0:
                current_prices[asset_id] = market_value_cny / quantity
    
    # Calculate cost basis for all non-insurance assets
    cost_basis_results = calculate_cost_basis_for_portfolio(non_insurance_transactions, current_prices)
    
    # Get FX rate for USD to CNY conversion
    fx_rate = 7.11  # Default FX rate
    if current_holdings_df is not None and not current_holdings_df.empty:
        # Try to get FX rate from holdings
        if 'FX_Rate' in current_holdings_df.columns:
            fx_rates = current_holdings_df['FX_Rate'].dropna()
            if not fx_rates.empty:
                fx_rate = fx_rates.iloc[0]
    
    # Aggregate portfolio-wide gains with proper realized/unrealized classification
    total_realized_gains = 0.0
    total_unrealized_gains = 0.0
    
    # Sub-class breakdown tracking (if requested)
    subclass_breakdown = {}
    
    for asset_id, cb_data in cost_basis_results.items():
        # Skip insurance assets
        if 'Ins_' in str(asset_id):
            continue
        
        # Detect if this is a USD asset by checking holdings Currency field
        currency = 'CNY'  # Default to CNY
        if current_holdings_df is not None:
            for idx, holding in current_holdings_df.iterrows():
                holding_asset_id = None
                if hasattr(idx, '__len__') and len(idx) >= 2:
                    holding_asset_id = idx[1]
                else:
                    holding_asset_id = holding.get('Asset_ID')
                
                if holding_asset_id == asset_id:
                    currency = holding.get('Currency', 'CNY')
                    break
        
        # Get P/L values (already in CNY after transaction-level conversion)
        realized_pnl = cb_data.get('realized_pnl', 0.0)
        unrealized_pnl = 0.0
        if asset_id in currently_held_assets:
            unrealized_pnl = cb_data.get('unrealized_pnl', 0.0)
        
        # FIXED: P/L values are already in CNY (transactions converted at processing level)
        # No need to convert again based on currency
        realized_pnl_cny = realized_pnl
        unrealized_pnl_cny = unrealized_pnl
        
        # Aggregate in CNY
        total_realized_gains += realized_pnl_cny
        total_unrealized_gains += unrealized_pnl_cny
        
        # If sub-class breakdown requested, classify and aggregate
        if include_subclass_breakdown:
            try:
                # Get asset name from holdings or transactions
                asset_name = None
                
                # First try current holdings
                if current_holdings_df is not None:
                    for idx, holding in current_holdings_df.iterrows():
                        holding_asset_id = None
                        if hasattr(idx, '__len__') and len(idx) >= 2:
                            holding_asset_id = idx[1]
                        else:
                            holding_asset_id = holding.get('Asset_ID')
                        
                        if holding_asset_id == asset_id:
                            asset_name = holding.get('Asset_Name', str(asset_id))
                            break
                
                # Fallback to transaction data if not found in holdings
                if not asset_name:
                    asset_transactions = non_insurance_transactions[
                        non_insurance_transactions['Asset_ID'] == asset_id
                    ]
                    if not asset_transactions.empty:
                        asset_name = asset_transactions.iloc[0].get('Asset_Name', str(asset_id))
                
                # Classify using taxonomy system
                if asset_name:
                    from ..portfolio_lib.taxonomy_manager import TaxonomyManager
                    taxonomy_manager = TaxonomyManager()
                    
                    # Get asset mapping
                    asset_mapping = taxonomy_manager.config.get('asset_mapping', {})
                    
                    if asset_name in asset_mapping:
                        sub_class = asset_mapping[asset_name]
                    else:
                        sub_class = taxonomy_manager._get_asset_sub_class(asset_name)
                    
                    # Initialize sub-class if not exists
                    if sub_class not in subclass_breakdown:
                        subclass_breakdown[sub_class] = {
                            'realized_gains': 0.0,
                            'unrealized_gains': 0.0,
                            'total_gains': 0.0
                        }
                    
                    # Add to sub-class totals (using CNY-converted values)
                    subclass_breakdown[sub_class]['realized_gains'] += realized_pnl_cny
                    subclass_breakdown[sub_class]['unrealized_gains'] += unrealized_pnl_cny
                    subclass_breakdown[sub_class]['total_gains'] += (realized_pnl_cny + unrealized_pnl_cny)
                    
            except Exception as e:
                logger.warning(f"Error classifying asset {asset_id} for sub-class breakdown: {e}")
                # Add to 'Unknown' category as fallback
                if 'Unknown' not in subclass_breakdown:
                    subclass_breakdown['Unknown'] = {
                        'realized_gains': 0.0,
                        'unrealized_gains': 0.0,
                        'total_gains': 0.0
                    }
                subclass_breakdown['Unknown']['realized_gains'] += realized_pnl_cny
                subclass_breakdown['Unknown']['unrealized_gains'] += unrealized_pnl_cny
                subclass_breakdown['Unknown']['total_gains'] += (realized_pnl_cny + unrealized_pnl_cny)
    
    total_gains = total_realized_gains + total_unrealized_gains
    
    logger.info(f"Portfolio gains analysis: Realized={total_realized_gains:.2f}, Unrealized={total_unrealized_gains:.2f}, Total={total_gains:.2f}")
    
    result = {
        "realized_gains": total_realized_gains,
        "unrealized_gains": total_unrealized_gains,
        "total_gains": total_gains
    }
    
    # Add sub-class breakdown if requested
    if include_subclass_breakdown:
        result["subclass_breakdown"] = subclass_breakdown
        logger.info(f"Sub-class breakdown includes {len(subclass_breakdown)} categories")
    
    return result


def enrich_holdings_with_cost_basis(holdings_df: pd.DataFrame, 
                                   cost_basis_results: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    """
    Enrich holdings DataFrame with cost basis information.
    
    Args:
        holdings_df: Holdings DataFrame with Asset_ID column
        cost_basis_results: Results from calculate_cost_basis_for_portfolio
        
    Returns:
        Holdings DataFrame enriched with cost basis columns
    """
    if holdings_df is None or holdings_df.empty:
        return holdings_df
    
    enriched_df = holdings_df.copy()
    
    # Initialize new columns
    enriched_df['Cost_Basis_Total'] = 0.0
    enriched_df['Average_Cost'] = 0.0
    enriched_df['Unrealized_PnL'] = 0.0
    enriched_df['Total_Shares_Bought'] = 0.0
    enriched_df['Total_Shares_Sold'] = 0.0
    enriched_df['Realized_PnL'] = 0.0
    
    # Enrich each holding with cost basis data
    for idx, holding in enriched_df.iterrows():
        asset_id = holding.get('Asset_ID')
        if asset_id in cost_basis_results:
            cb_data = cost_basis_results[asset_id]
            
            enriched_df.loc[idx, 'Cost_Basis_Total'] = cb_data.get('total_cost_basis', 0.0)
            enriched_df.loc[idx, 'Average_Cost'] = cb_data.get('average_cost', 0.0)
            enriched_df.loc[idx, 'Unrealized_PnL'] = cb_data.get('unrealized_pnl', 0.0)
            enriched_df.loc[idx, 'Total_Shares_Bought'] = cb_data.get('total_shares_bought', 0.0)
            enriched_df.loc[idx, 'Total_Shares_Sold'] = cb_data.get('total_shares_sold', 0.0)
            enriched_df.loc[idx, 'Realized_PnL'] = cb_data.get('realized_pnl', 0.0)
    
    return enriched_df
