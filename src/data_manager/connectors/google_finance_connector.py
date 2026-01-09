"""
Google Finance Connector - Real-time market data fetching.

Provides lightweight, fast, and reliable access to Google Finance data
without requiring API keys or complex authentication.

Author: Personal Investment System
Date: November 5, 2025
"""

import requests
import logging
import re
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class GoogleFinanceConnector:
    """
    Connector for Google Finance market data.
    
    Fetches real-time exchange rates and stock prices from Google Finance.
    No API key required, fast response times (< 1 second typical).
    """
    
    def __init__(self, timeout: float = 5.0, cache_duration_seconds: int = 3600):
        """
        Initialize Google Finance connector.
        
        Args:
            timeout: HTTP request timeout in seconds
            cache_duration_seconds: Cache validity period (default: 1 hour)
        """
        self.timeout = timeout
        self.cache_duration = timedelta(seconds=cache_duration_seconds)
        self.base_url = "https://www.google.com/finance/quote"
        self.cache: Dict[str, Dict[str, Any]] = {}
        
        logger.debug(f"GoogleFinanceConnector initialized (timeout={timeout}s, cache={cache_duration_seconds}s)")
    
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Get real-time exchange rate from Google Finance.
        
        Args:
            from_currency: Source currency code (e.g., 'USD')
            to_currency: Target currency code (e.g., 'CNY')
            
        Returns:
            Exchange rate as float, or None if fetch fails
            
        Example:
            >>> connector = GoogleFinanceConnector()
            >>> rate = connector.get_exchange_rate('USD', 'CNY')
            >>> print(f"1 USD = {rate} CNY")
        """
        cache_key = f"FX_{from_currency}_{to_currency}"
        
        # Check cache
        if self._is_cache_valid(cache_key):
            cached_rate = self.cache[cache_key]['value']
            logger.debug(f"Using cached {from_currency}/{to_currency} rate: {cached_rate:.4f}")
            return cached_rate
        
        # Fetch from Google Finance
        try:
            url = f"{self.base_url}/{from_currency}-{to_currency}"
            logger.debug(f"Fetching {from_currency}/{to_currency} from: {url}")
            
            response = requests.get(url, timeout=self.timeout, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            rate = self._parse_exchange_rate(response.text)
            
            if rate is not None:
                # Cache the result
                self.cache[cache_key] = {
                    'value': rate,
                    'timestamp': datetime.now()
                }
                logger.info(f"✓ Fetched {from_currency}/{to_currency} rate: {rate:.4f}")
                return rate
            else:
                logger.warning(f"Failed to parse {from_currency}/{to_currency} rate from Google Finance")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching {from_currency}/{to_currency} from Google Finance")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching {from_currency}/{to_currency}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {from_currency}/{to_currency}: {e}")
            return None
    
    def get_stock_price(self, symbol: str, exchange: str = "NASDAQ") -> Optional[float]:
        """
        Get real-time stock price from Google Finance.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AMZN')
            exchange: Exchange code (e.g., 'NASDAQ', 'NYSE')
            
        Returns:
            Stock price as float, or None if fetch fails
            
        Example:
            >>> connector = GoogleFinanceConnector()
            >>> price = connector.get_stock_price('AMZN', 'NASDAQ')
            >>> print(f"AMZN: ${price:.2f}")
        """
        cache_key = f"STOCK_{symbol}_{exchange}"
        
        # Check cache
        if self._is_cache_valid(cache_key):
            cached_price = self.cache[cache_key]['value']
            logger.debug(f"Using cached {symbol}:{exchange} price: ${cached_price:.2f}")
            return cached_price
        
        # Fetch from Google Finance
        try:
            url = f"{self.base_url}/{symbol}:{exchange}"
            logger.debug(f"Fetching {symbol}:{exchange} from: {url}")
            
            response = requests.get(url, timeout=self.timeout, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            price = self._parse_stock_price(response.text)
            
            if price is not None:
                # Cache the result
                self.cache[cache_key] = {
                    'value': price,
                    'timestamp': datetime.now()
                }
                logger.info(f"✓ Fetched {symbol}:{exchange} price: ${price:.2f}")
                return price
            else:
                logger.warning(f"Failed to parse {symbol}:{exchange} price from Google Finance")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching {symbol}:{exchange} from Google Finance")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching {symbol}:{exchange}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {symbol}:{exchange}: {e}")
            return None
    
    def _parse_exchange_rate(self, html: str) -> Optional[float]:
        """Parse exchange rate from Google Finance HTML."""
        try:
            # Look for data-last-price attribute (most reliable)
            match = re.search(r'data-last-price="([\d.,]+)"', html)
            if match:
                rate_str = match.group(1).replace(',', '')
                return float(rate_str)
            
            # Fallback: Look for price in meta tags
            match = re.search(r'<meta content="([\d.,]+)"[^>]*property="og:price:amount"', html)
            if match:
                rate_str = match.group(1).replace(',', '')
                return float(rate_str)
            
            # Fallback: Look for div with specific class
            match = re.search(r'class="YMlKec fxKbKc"[^>]*>([\d.,]+)</div>', html)
            if match:
                rate_str = match.group(1).replace(',', '')
                return float(rate_str)
            
            logger.warning("Could not find exchange rate in HTML with any known pattern")
            return None
            
        except (ValueError, AttributeError) as e:
            logger.error(f"Error parsing exchange rate: {e}")
            return None
    
    def _parse_stock_price(self, html: str) -> Optional[float]:
        """Parse stock price from Google Finance HTML."""
        try:
            # Same parsing logic as exchange rate (Google Finance uses consistent format)
            match = re.search(r'data-last-price="([\d.,]+)"', html)
            if match:
                price_str = match.group(1).replace(',', '')
                return float(price_str)
            
            # Fallback patterns
            match = re.search(r'<meta content="([\d.,]+)"[^>]*property="og:price:amount"', html)
            if match:
                price_str = match.group(1).replace(',', '')
                return float(price_str)
            
            match = re.search(r'class="YMlKec fxKbKc"[^>]*>([\d.,]+)</div>', html)
            if match:
                price_str = match.group(1).replace(',', '')
                return float(price_str)
            
            logger.warning("Could not find stock price in HTML with any known pattern")
            return None
            
        except (ValueError, AttributeError) as e:
            logger.error(f"Error parsing stock price: {e}")
            return None
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached value is still valid."""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key]['timestamp']
        age = datetime.now() - cached_time
        
        return age < self.cache_duration
    
    def clear_cache(self):
        """Clear all cached data."""
        self.cache.clear()
        logger.debug("Google Finance cache cleared")


# Module-level singleton instance
_google_finance_connector: Optional[GoogleFinanceConnector] = None


def get_google_finance_connector() -> GoogleFinanceConnector:
    """
    Get or create singleton Google Finance connector instance.
    
    Returns:
        GoogleFinanceConnector instance
    """
    global _google_finance_connector
    
    if _google_finance_connector is None:
        _google_finance_connector = GoogleFinanceConnector()
    
    return _google_finance_connector
