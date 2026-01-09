# Market Data Connector
# src/data_manager/connectors/market_data_connector.py

"""
Market Data Integration for Personal Investment System.
Provides functionality to connect with market data providers for real-time and historical prices.

Supports multiple providers:
- Yahoo Finance (default, free)
- Alpha Vantage (API key required)
- IEX Cloud (API key required)
"""

import pandas as pd
from typing import Dict, Optional, Any, List
import logging
import requests
import time

logger = logging.getLogger(__name__)


class MarketDataConnector:
    """
    Connector for market data from various providers.
    Provides standardized interface for retrieving price and market data.
    """
    
    def __init__(self, provider: str = 'yahoo', config: Optional[Dict[str, Any]] = None):
        """
        Initialize market data connector.
        
        Args:
            provider: Data provider ('yahoo', 'alphavantage', 'iex')
            config: Provider-specific configuration
        """
        self.provider = provider.lower()
        self.config = config or {}
        self.api_key = self.config.get('api_key')
        self.rate_limit = self.config.get('rate_limit', 1.0)  # seconds between requests
        self.last_request_time = 0
        
        # Provider-specific settings
        self._setup_provider()
    
    def _setup_provider(self):
        """Setup provider-specific configurations."""
        if self.provider == 'yahoo':
            self.base_url = 'https://query1.finance.yahoo.com/v8/finance/chart'
            self.requires_api_key = False
        elif self.provider == 'alphavantage':
            self.base_url = 'https://www.alphavantage.co/query'
            self.requires_api_key = True
        elif self.provider == 'iex':
            self.base_url = 'https://cloud.iexapis.com/stable'
            self.requires_api_key = True
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
        
        if self.requires_api_key and not self.api_key:
            logger.warning(f"API key required for {self.provider} but not provided")
    
    def _rate_limit_request(self):
        """Implement rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get current prices for a list of symbols.
        
        Args:
            symbols: List of ticker symbols
            
        Returns:
            Dictionary mapping symbols to current prices
        """
        prices = {}
        
        for symbol in symbols:
            try:
                self._rate_limit_request()
                price = self._get_single_price(symbol)
                if price is not None:
                    prices[symbol] = price
                    
            except Exception as e:
                logger.error(f"Error fetching price for {symbol}: {e}")
                continue
        
        return prices
    
    def _get_single_price(self, symbol: str) -> Optional[float]:
        """Get current price for a single symbol."""
        if self.provider == 'yahoo':
            return self._get_yahoo_price(symbol)
        elif self.provider == 'alphavantage':
            return self._get_alphavantage_price(symbol)
        elif self.provider == 'iex':
            return self._get_iex_price(symbol)
        else:
            return None
    
    def _get_yahoo_price(self, symbol: str) -> Optional[float]:
        """Get price from Yahoo Finance."""
        try:
            # Placeholder implementation for Yahoo Finance
            # In real implementation, would use yfinance library or direct API calls
            logger.info(f"Fetching Yahoo Finance price for {symbol} (placeholder)")
            
            # Return sample price for development
            sample_prices = {
                'AAPL': 150.00,
                'MSFT': 250.00,
                'SPY': 400.00,
                'TSLA': 800.00
            }
            
            return sample_prices.get(symbol, 100.00)  # Default price if symbol not found
            
        except Exception as e:
            logger.error(f"Yahoo Finance API error for {symbol}: {e}")
            return None
    
    def _get_alphavantage_price(self, symbol: str) -> Optional[float]:
        """Get price from Alpha Vantage."""
        if not self.api_key:
            logger.error("Alpha Vantage API key required")
            return None
        
        try:
            # Placeholder implementation for Alpha Vantage
            logger.info(f"Fetching Alpha Vantage price for {symbol} (placeholder)")
            return 100.00  # Placeholder price
            
        except Exception as e:
            logger.error(f"Alpha Vantage API error for {symbol}: {e}")
            return None
    
    def _get_iex_price(self, symbol: str) -> Optional[float]:
        """Get price from IEX Cloud."""
        if not self.api_key:
            logger.error("IEX Cloud API key required")
            return None
        
        try:
            # Placeholder implementation for IEX Cloud
            logger.info(f"Fetching IEX Cloud price for {symbol} (placeholder)")
            return 100.00  # Placeholder price
            
        except Exception as e:
            logger.error(f"IEX Cloud API error for {symbol}: {e}")
            return None
    
    def get_historical_prices(self, 
                            symbol: str, 
                            start_date: pd.Timestamp,
                            end_date: pd.Timestamp,
                            frequency: str = 'daily') -> Optional[pd.DataFrame]:
        """
        Get historical price data for a symbol.
        
        Args:
            symbol: Ticker symbol
            start_date: Start date for historical data
            end_date: End date for historical data
            frequency: Data frequency ('daily', 'weekly', 'monthly')
            
        Returns:
            DataFrame with historical price data (OHLCV format)
        """
        try:
            self._rate_limit_request()
            
            if self.provider == 'yahoo':
                return self._get_yahoo_historical(symbol, start_date, end_date, frequency)
            elif self.provider == 'alphavantage':
                return self._get_alphavantage_historical(symbol, start_date, end_date, frequency)
            elif self.provider == 'iex':
                return self._get_iex_historical(symbol, start_date, end_date, frequency)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    def _get_yahoo_historical(self, symbol: str, start_date: pd.Timestamp, end_date: pd.Timestamp, frequency: str) -> pd.DataFrame:
        """Get historical data from Yahoo Finance."""
        logger.info(f"Fetching Yahoo Finance historical data for {symbol}")
        
        try:
            # Try to use yfinance library if available
            try:
                import yfinance as yf
                
                # Fetch real data using yfinance
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=start_date, end=end_date)
                
                if not hist.empty:
                    # yfinance returns data in the correct format already
                    logger.info(f"Successfully fetched real data for {symbol}: {len(hist)} data points")
                    return hist
                else:
                    logger.warning(f"No data returned from yfinance for {symbol}")
                    
            except ImportError:
                logger.info("yfinance not available, using synthetic data")
            except Exception as e:
                logger.warning(f"yfinance error for {symbol}: {e}, falling back to synthetic data")
        
        except Exception as e:
            logger.error(f"Error in Yahoo Finance data fetch: {e}")
        
        # Fallback to synthetic data
        logger.info(f"Generating synthetic historical data for {symbol}")
        return self._generate_synthetic_data(symbol, start_date, end_date)
    
    def _generate_synthetic_data(self, symbol: str, start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
        """Generate synthetic but realistic market data for development."""
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Skip weekends for market data
        date_range = [d for d in date_range if d.weekday() < 5]
        
        if not date_range:
            return pd.DataFrame()
        
        # Generate sample OHLCV data with realistic patterns
        import numpy as np
        np_random = np.random.RandomState(hash(symbol) % 2**32)  # Consistent seed based on symbol
        
        # Base price and volatility by asset type
        base_prices = {
            'VT': 100.0,     # Global equity ETF
            'BNDW': 50.0,    # Global bond ETF  
            'VNQ': 90.0,     # Real estate ETF
            'DJP': 25.0,     # Commodities ETF
            'SHY': 84.0      # Short treasury ETF
        }
        
        volatilities = {
            'VT': 0.015,     # 1.5% daily vol for equity
            'BNDW': 0.005,   # 0.5% daily vol for bonds
            'VNQ': 0.018,    # 1.8% daily vol for real estate
            'DJP': 0.020,    # 2.0% daily vol for commodities
            'SHY': 0.002     # 0.2% daily vol for cash
        }
        
        base_price = base_prices.get(symbol, 100.0)
        daily_vol = volatilities.get(symbol, 0.015)
        
        prices = []
        current_price = base_price
        
        for i, trade_date in enumerate(date_range):
            # Add some trend and mean reversion
            trend = 0.0005 if symbol in ['VT', 'VNQ'] else 0.0001  # Slight upward bias for equity
            mean_reversion = -0.1 * (current_price - base_price) / base_price  # Mean revert to base
            
            # Daily return with trend, mean reversion, and volatility
            daily_return = trend + mean_reversion * 0.01 + np_random.normal(0, daily_vol)
            current_price *= (1 + daily_return)
            
            # Generate OHLC from close price with realistic intraday movement
            intraday_vol = daily_vol * 0.5
            high = current_price * (1 + abs(np_random.normal(0, intraday_vol)))
            low = current_price * (1 - abs(np_random.normal(0, intraday_vol)))
            open_price = current_price * (1 + np_random.normal(0, intraday_vol * 0.5))
            
            # Ensure OHLC logic (High >= max(Open, Close), Low <= min(Open, Close))
            high = max(high, open_price, current_price)
            low = min(low, open_price, current_price)
            
            # Realistic volume based on symbol type
            base_volume = {
                'VT': 2000000,
                'BNDW': 500000,
                'VNQ': 1000000,
                'DJP': 800000,
                'SHY': 1500000
            }.get(symbol, 1000000)
            
            volume = int(np_random.uniform(base_volume * 0.5, base_volume * 2.0))
            
            prices.append({
                'Open': open_price,
                'High': high,
                'Low': low,
                'Close': current_price,
                'Volume': volume
            })
        
        df = pd.DataFrame(prices, index=date_range)
        df.index.name = 'Date'
        
        logger.info(f"Generated {len(df)} synthetic data points for {symbol}")
        return df
    
    def _get_alphavantage_historical(self, symbol: str, start_date: pd.Timestamp, end_date: pd.Timestamp, frequency: str) -> pd.DataFrame:
        """Get historical data from Alpha Vantage."""
        logger.info(f"Fetching Alpha Vantage historical data for {symbol} (placeholder)")
        return pd.DataFrame()  # Placeholder
    
    def _get_iex_historical(self, symbol: str, start_date: pd.Timestamp, end_date: pd.Timestamp, frequency: str) -> pd.DataFrame:
        """Get historical data from IEX Cloud."""
        logger.info(f"Fetching IEX Cloud historical data for {symbol} (placeholder)")
        return pd.DataFrame()  # Placeholder
    
    def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get company information for a symbol.
        
        Args:
            symbol: Ticker symbol
            
        Returns:
            Dictionary with company information
        """
        try:
            self._rate_limit_request()
            
            # Placeholder implementation
            logger.info(f"Fetching company info for {symbol} (placeholder)")
            
            sample_info = {
                'symbol': symbol,
                'company_name': f"{symbol} Corporation",
                'sector': 'Technology',
                'industry': 'Software',
                'market_cap': 1000000000,
                'employees': 50000,
                'description': f"Sample description for {symbol}",
                'last_updated': pd.Timestamp.now()
            }
            
            return sample_info
            
        except Exception as e:
            logger.error(f"Error fetching company info for {symbol}: {e}")
            return None
    
    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Convert currency using current exchange rates.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code (e.g., 'USD')
            to_currency: Target currency code (e.g., 'CNY')
            
        Returns:
            Converted amount or None if conversion fails
        """
        if from_currency == to_currency:
            return amount
        
        try:
            # Placeholder implementation
            # In real implementation, would fetch current exchange rates
            logger.info(f"Converting {amount} {from_currency} to {to_currency} (placeholder)")
            
            # Sample exchange rates
            rates = {
                ('USD', 'CNY'): 7.2,
                ('CNY', 'USD'): 1/7.2,
                ('EUR', 'USD'): 1.1,
                ('USD', 'EUR'): 1/1.1
            }
            
            rate = rates.get((from_currency, to_currency))
            if rate:
                return amount * rate
            else:
                logger.warning(f"Exchange rate not available for {from_currency} to {to_currency}")
                return None
                
        except Exception as e:
            logger.error(f"Currency conversion error: {e}")
            return None
