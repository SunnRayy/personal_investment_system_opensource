# File path: src/portfolio_lib/price_service.py
"""
Price Service - Unified price data management.

Provides a single interface for fetching asset prices from multiple sources:
1. Database (market_data_nav table for CN funds)
2. External APIs (yfinance for US stocks/ETFs)
3. Holdings table (manual price overrides from last snapshot)
4. Excel fallback (for assets without database records)

This service abstracts the complexity of multi-source price data
and provides a consistent API for HoldingsCalculator and other modules.
"""

import logging
import pandas as pd
import time
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, Dict, Tuple, List

from src.database.base import get_session
from src.database.models import Holding


class PriceService:
    """
    Unified price service for fetching asset prices from multiple sources.
    
    Price source priority:
    1. Manual override (if provided)
    2. Database market_data_nav table (for CN funds with API integration)
    3. External API (yfinance for US stocks)
    4. Latest holdings table (manual prices from snapshot)
    5. None (if unavailable)
    """
    
    def __init__(self, db_session=None, data_manager=None):
        """
        Initialize price service.
        
        Args:
            db_session: SQLAlchemy session (optional, creates new if None)
            data_manager: DataManager instance for Excel fallback (optional)
        """
        self.logger = logging.getLogger(__name__)
        self.session = db_session or get_session()
        self.data_manager = data_manager
        
        # Cache for prices to avoid repeated queries
        self._price_cache: Dict[Tuple[str, date], Optional[Decimal]] = {}
        # Cache for assets where API fetch failed (to avoid retries)
        self._api_unavailable_cache = set()
        
    def get_latest_price(self, asset_id: str, as_of_date: Optional[date] = None) -> Optional[Decimal]:
        """
        Get the latest price for an asset as of a specific date.
        
        Args:
            asset_id: Standardized asset identifier
            as_of_date: Date to get price for (defaults to today)
            
        Returns:
            Price as Decimal, or None if unavailable
        """
        if as_of_date is None:
            as_of_date = date.today()
            
        # Check cache first
        cache_key = (asset_id, as_of_date)
        if cache_key in self._price_cache:
            return self._price_cache[cache_key]
        
        # Try each source in priority order
        price = None
        source = "unavailable"
        
        # 1. Check market_data_nav table (CN funds with API)
        price, source = self._get_price_from_nav_table(asset_id, as_of_date)
        
        # 2. Schwab CSV Fallback (Prioritized over API)
        if price is None and self.data_manager:
            price, source = self._get_price_from_schwab_csv(asset_id, as_of_date)

        # 3. Try external API (yfinance for US stocks)
        # DISABLED by user request due to rate limits
        # if price is None and cache_key not in self._api_unavailable_cache:
        #     price, source = self._get_price_from_api(asset_id, as_of_date)
        #     if price is None:
        #         self._api_unavailable_cache.add(cache_key)
        
        # 4. Google Finance Fallback (Scraper)
        if price is None:
            price, source = self._get_price_from_google_finance(asset_id)
            if price is None:
                pass

        # 5. Fall back to latest holdings table
        if price is None:
            price, source = self._get_price_from_holdings(asset_id, as_of_date)
        
        # 6. Excel fallback (via DataManager general holdings)
        if price is None and self.data_manager:
            price, source = self._get_price_from_excel(asset_id)
        
        # Cache the result
        self._price_cache[cache_key] = price
        
        if price is not None:
            self.logger.debug(f"Price for {asset_id} on {as_of_date}: {price} (source: {source})")
        else:
            # Only log warning if it's not a known manual asset (like Insurance/Gold which might not have prices yet)
            self.logger.debug(f"No price available for {asset_id} on {as_of_date}")
        
        return price
    
    def get_batch_latest_prices(self, asset_ids: list, as_of_date: Optional[date] = None) -> Dict[str, Optional[Decimal]]:
        """
        Get latest prices for multiple assets (batch operation for efficiency).
        
        Args:
            asset_ids: List of asset identifiers
            as_of_date: Date to get prices for (defaults to today)
            
        Returns:
            Dictionary mapping asset_id to price (or None if unavailable)
        """
        if as_of_date is None:
            as_of_date = date.today()
        
        prices = {}
        
        # 1. Identify US stocks for batch API fetch
        us_stocks = [aid for aid in asset_ids if self._is_us_stock(aid)]
        other_assets = [aid for aid in asset_ids if aid not in us_stocks]
        
        # 2. Batch fetch US stocks
        if us_stocks:
            self.logger.info(f"Batch fetching prices for {len(us_stocks)} US stocks...")
            
            # Check cache first to avoid re-fetching known assets
            uncached_stocks = [aid for aid in us_stocks if (aid, as_of_date) not in self._price_cache and (aid, as_of_date) not in self._api_unavailable_cache]
            
            # DISABLED API batch fetch
            # if uncached_stocks:
            #     api_prices = self._get_batch_prices_from_api(uncached_stocks, as_of_date)
            #     prices.update(api_prices)
            #     
            #     # Update caches
            #     for aid in uncached_stocks:
            #         price = api_prices.get(aid)
            #         if price is not None:
            #             self._price_cache[(aid, as_of_date)] = price
            #         else:
            #             # Mark as unavailable in API so we don't retry individually
            #             self._api_unavailable_cache.add((aid, as_of_date))
            
            # Retrieve from cache for all US stocks
            for aid in us_stocks:
                if (aid, as_of_date) in self._price_cache:
                    prices[aid] = self._price_cache[(aid, as_of_date)]
        
        # 3. Fetch others one by one (will use cache if available)
        for asset_id in other_assets:
            prices[asset_id] = self.get_latest_price(asset_id, as_of_date)
            
        # 4. Fill in missing US stocks (fallback to other sources)
        # get_latest_price will skip API check because we added to _api_unavailable_cache
        for asset_id in us_stocks:
            if asset_id not in prices or prices[asset_id] is None:
                prices[asset_id] = self.get_latest_price(asset_id, as_of_date)
                
        return prices

    def _is_us_stock(self, asset_id: str) -> bool:
        """Check if asset ID looks like a US stock ticker (alphabetic, 1-5 chars)."""
        # Exclude known non-stock prefixes if any, but for now assume simple tickers
        return asset_id.isalpha() and 1 <= len(asset_id) <= 5

    def _get_batch_prices_from_api(self, asset_ids: List[str], as_of_date: date) -> Dict[str, Optional[Decimal]]:
        """
        Batch fetch prices from yfinance.
        """
        results = {aid: None for aid in asset_ids}
        try:
            import yfinance as yf
            
            # Fetch history around the date
            start_date = as_of_date - timedelta(days=7)
            end_date = as_of_date + timedelta(days=1)
            
            # yf.download is more efficient for batch
            # auto_adjust=True to get actual price
            data = yf.download(
                asset_ids, 
                start=start_date, 
                end=end_date, 
                group_by='ticker',
                auto_adjust=True,
                progress=False,
                threads=True
            )
            
            if data.empty:
                return results
                
            # Process each ticker
            for asset_id in asset_ids:
                try:
                    # Handle single ticker vs multi-ticker structure
                    if len(asset_ids) == 1:
                        ticker_data = data
                    else:
                        if asset_id not in data.columns.levels[0]:
                            continue
                        ticker_data = data[asset_id]
                    
                    # Filter by date
                    valid_prices = ticker_data[ticker_data.index.date <= as_of_date]
                    
                    if not valid_prices.empty and 'Close' in valid_prices.columns:
                        price = valid_prices['Close'].iloc[-1]
                        if pd.notna(price):
                            results[asset_id] = Decimal(str(price))
                except Exception as e:
                    self.logger.debug(f"Error processing batch data for {asset_id}: {e}")
                    
        except ImportError:
            self.logger.warning("yfinance not installed")
        except Exception as e:
            self.logger.error(f"Batch API fetch failed: {e}")
            
        return results
    
    def _get_price_from_nav_table(self, asset_id: str, as_of_date: date) -> Tuple[Optional[Decimal], str]:
        """
        Fetch price from market_data_nav table (CN funds with NAV data).
        
        Returns:
            Tuple of (price, source_name)
        """
        try:
            # Import here to avoid circular dependency
            from ..database.models import MarketDataNAV
            
            # Query the most recent NAV <= as_of_date
            result = self.session.query(MarketDataNAV).filter(
                MarketDataNAV.asset_id == asset_id,
                MarketDataNAV.date <= as_of_date
            ).order_by(MarketDataNAV.date.desc()).first()
            
            if result:
                return Decimal(str(result.nav)), "market_data_nav"
        except ImportError:
            # market_data_nav table might not exist yet
            self.logger.debug("market_data_nav table not found in models")
        except Exception as e:
            self.logger.debug(f"Error fetching price from NAV table for {asset_id}: {e}")
        
        return None, "unavailable"
    
    def _get_price_from_api(self, asset_id: str, as_of_date: date) -> Tuple[Optional[Decimal], str]:
        """
        Fetch price from external API (yfinance for US stocks/ETFs).
        
        Returns:
            Tuple of (price, source_name)
        """
        try:
            # Only try API for assets with ticker-like IDs (US stocks)
            if not self._is_us_stock(asset_id):
                return None, "unavailable"
            
            import yfinance as yf
            import time
            
            # Simple retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    ticker = yf.Ticker(asset_id)
                    # Get historical data around the target date
                    start_date = as_of_date - timedelta(days=7)
                    end_date = as_of_date + timedelta(days=1)
                    
                    hist = ticker.history(start=start_date.isoformat(), end=end_date.isoformat())
                    
                    if not hist.empty:
                        # Get the closest date <= as_of_date
                        valid_prices = hist[hist.index.date <= as_of_date]
                        if not valid_prices.empty:
                            price = valid_prices['Close'].iloc[-1]
                            return Decimal(str(price)), "yfinance_api"
                    break # If successful or empty but no error, break
                except Exception as e:
                    if "Too Many Requests" in str(e) and attempt < max_retries - 1:
                        time.sleep(1 * (attempt + 1)) # Exponential backoff
                        continue
                    self.logger.warning(f"API fetch failed for {asset_id} after retries: {e}")
                    
        except ImportError:
            self.logger.debug("yfinance not installed, skipping API price fetch")
        except Exception as e:
            self.logger.debug(f"Error fetching price from API for {asset_id}: {e}")
        
        return None, "unavailable"

    def _get_price_from_google_finance(self, asset_id: str) -> Tuple[Optional[Decimal], str]:
        """
        Fetch price from Google Finance via web scraping (fallback for yfinance).
        """
        try:
            # Only try for US stocks
            if not self._is_us_stock(asset_id):
                return None, "unavailable"

            import requests
            from bs4 import BeautifulSoup
            
            # Try common exchanges
            exchanges = ['NYSEARCA', 'NASDAQ', 'NYSE']
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
            }
            
            for exchange in exchanges:
                url = f"https://www.google.com/finance/quote/{asset_id}:{exchange}"
                try:
                    response = requests.get(url, headers=headers, timeout=5)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        # The price is usually in a div with class "YMlKec fxKbKc"
                        price_div = soup.find('div', {'class': 'YMlKec fxKbKc'})
                        if price_div:
                            price_str = price_div.text.replace('$', '').replace(',', '')
                            return Decimal(price_str), f"google_finance_{exchange}"
                except Exception:
                    continue
                    
        except ImportError:
            self.logger.debug("requests or bs4 not installed, skipping Google Finance fetch")
        except Exception as e:
            self.logger.debug(f"Error fetching price from Google Finance for {asset_id}: {e}")
            
        return None, "unavailable"

    def _get_price_from_schwab_csv(self, asset_id: str, as_of_date: date) -> Tuple[Optional[Decimal], str]:
        """
        Fetch price directly from cleaned Schwab CSV data in DataManager.
        This is a robust fallback when API fails.
        """
        try:
            if self.data_manager is None:
                return None, "unavailable"
                
            # Access cleaned Schwab holdings directly
            schwab_df = self.data_manager.cleaned_data.get('schwab_holdings')
            
            if schwab_df is None or schwab_df.empty:
                return None, "unavailable"
                
            # Filter for asset
            asset_rows = schwab_df[schwab_df['Asset_ID'] == asset_id]
            
            if asset_rows.empty:
                return None, "unavailable"
                
            # Sort by date if available, otherwise take the first one
            # Schwab CSV usually represents a single snapshot
            if 'Snapshot_Date' in asset_rows.columns:
                asset_rows = asset_rows.sort_values('Snapshot_Date')
                
            latest_row = asset_rows.iloc[-1]
            
            if 'Market_Price_Unit' in latest_row and pd.notna(latest_row['Market_Price_Unit']):
                return Decimal(str(latest_row['Market_Price_Unit'])), "schwab_csv_fallback"
                
        except Exception as e:
            self.logger.debug(f"Error fetching price from Schwab CSV for {asset_id}: {e}")
            
        return None, "unavailable"
    
    def _get_price_from_holdings(self, asset_id: str, as_of_date: date) -> Tuple[Optional[Decimal], str]:
        """
        Fetch price from holdings table (manual prices from latest snapshot).
        
        Returns:
            Tuple of (price, source_name)
        """
        try:
            # Query the most recent holding <= as_of_date
            result = self.session.query(Holding).filter(
                Holding.asset_id == asset_id,
                Holding.snapshot_date <= as_of_date,
                Holding.current_price.isnot(None)
            ).order_by(Holding.snapshot_date.desc()).first()
            
            if result and result.current_price:
                return Decimal(str(result.current_price)), "holdings_table"
        except Exception as e:
            self.logger.debug(f"Error fetching price from holdings for {asset_id}: {e}")
        
        return None, "unavailable"
    
    def _get_price_from_excel(self, asset_id: str) -> Tuple[Optional[Decimal], str]:
        """
        Fetch price from Excel data via DataManager (fallback).
        
        Returns:
            Tuple of (price, source_name)
        """
        try:
            if self.data_manager is None:
                return None, "unavailable"
            
            # Get latest holdings from Excel
            holdings_df = self.data_manager.get_holdings()
            
            if holdings_df.empty:
                return None, "unavailable"
            
            # Filter for the specific asset
            if 'Asset_ID' in holdings_df.index.names:
                # MultiIndex: (Date, Asset_ID)
                asset_holdings = holdings_df.xs(asset_id, level='Asset_ID', drop_level=False)
            else:
                # Single index
                asset_holdings = holdings_df[holdings_df.get('Asset_ID') == asset_id]
            
            if asset_holdings.empty:
                return None, "unavailable"
            
            # Get the most recent price
            latest = asset_holdings.iloc[-1]
            price_col = 'Market_Price_Unit' if 'Market_Price_Unit' in latest else 'current_price'
            
            if price_col in latest and pd.notna(latest[price_col]):
                return Decimal(str(latest[price_col])), "excel_fallback"
        except Exception as e:
            self.logger.debug(f"Error fetching price from Excel for {asset_id}: {e}")
        
        return None, "unavailable"
    
    def clear_cache(self):
        """Clear the price cache (useful when data is updated)."""
        self._price_cache.clear()
        self.logger.debug("Price cache cleared")
