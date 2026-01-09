"""
Currency Converter Module

This module provides currency conversion functionality with historical exchange rates
and in-memory caching to optimize performance during single analysis runs.

Author: Ray's Personal Investment System
Date: November 5, 2025
"""

import pandas as pd
from typing import Dict, Optional, Tuple, Any
import logging
from datetime import timedelta
import time
import threading

# Configure logging
logger = logging.getLogger(__name__)

try:
    from forex_python.converter import CurrencyRates
    FOREX_AVAILABLE = True
except ImportError:
    logger.warning("forex-python not available. Currency conversion will use fallback rates.")
    FOREX_AVAILABLE = False

# Import Google Finance connector
try:
    from .connectors.google_finance_connector import get_google_finance_connector
    GOOGLE_FINANCE_AVAILABLE = True
except ImportError:
    logger.warning("Google Finance connector not available.")
    GOOGLE_FINANCE_AVAILABLE = False


class CurrencyConverterService:
    """
    Currency conversion service with historical exchange rates and caching.
    
    This service provides historical currency conversion with in-memory caching
    to avoid redundant API calls during analysis runs. Includes performance
    optimizations and Excel-based static rate fallback support.
    """
    
    def __init__(self, excel_rates: Optional[pd.Series] = None, use_excel_fallback: bool = True, 
                 prefer_excel: bool = False, enable_forex_api: bool = False, 
                 enable_google_finance: bool = True):
        """
        Initialize the currency converter service.
        
        Args:
            excel_rates: Optional pd.Series with DatetimeIndex containing USD/CNY rates from Excel
            use_excel_fallback: If True, use Excel rates as fallback before hardcoded rates
            prefer_excel: If True, try Excel BEFORE Google Finance (default: False for Google Finance first)
            enable_forex_api: If True, enable forex-python API calls (may be slow/unreliable)
            enable_google_finance: If True, enable Google Finance for latest rates (default: True)
        """
        self.cache: Dict[Tuple[str, str, str], float] = {}  # (from_currency, to_currency, date_str) -> rate
        self.currency_rates = CurrencyRates() if FOREX_AVAILABLE else None
        self.excel_rates = excel_rates  # Store Excel rates for fallback
        self.use_excel_fallback = use_excel_fallback
        self.prefer_excel = prefer_excel  # Try Excel first if True
        self.enable_forex_api = enable_forex_api  # Disable slow API by default
        self.enable_google_finance = enable_google_finance and GOOGLE_FINANCE_AVAILABLE  # New: Google Finance
        
        # Performance tracking
        self.api_call_count = 0
        self.total_api_time = 0.0
        self.failed_api_calls = 0
        self.excel_fallback_count = 0
        self.hardcoded_fallback_count = 0
        self.timeout_count = 0
        self.google_finance_call_count = 0  # NEW
        self.google_finance_success_count = 0  # NEW
        
        # Performance optimization settings
        self.max_alternative_attempts = 2  # REDUCED from 8 to 2 (only try ±1 day)
        self.api_timeout = 5.0  # 5 second hard timeout per API call
        self.max_total_api_time = 30.0  # Max 30 seconds total for all API calls
        
        # Fallback rates for common currency pairs (used when Excel and forex-python are not available)
        self.fallback_rates = {
            ('USD', 'CNY'): 7.11,  # Current approximate rate
            ('CNY', 'USD'): 1/7.11,
            ('EUR', 'CNY'): 7.85,  # Approximate
            ('CNY', 'EUR'): 1/7.85,
            ('HKD', 'CNY'): 0.91,  # Approximate
            ('CNY', 'HKD'): 1/0.91,
        }
        
        if excel_rates is not None:
            logger.info(f"CurrencyConverterService initialized with {len(excel_rates)} Excel rates "
                       f"(prefer_excel={prefer_excel}, google_finance={enable_google_finance}, forex_api={enable_forex_api})")
        else:
            logger.info(f"CurrencyConverterService initialized (no Excel rates, "
                       f"google_finance={enable_google_finance}, forex_api={enable_forex_api})")
    
    def get_historical_rate(self, from_currency: str, to_currency: str, date: pd.Timestamp) -> Optional[float]:
        """
        Get historical exchange rate for a specific date with caching.
        
        For recent dates (< 7 days old), uses Google Finance for latest rate.
        For older historical dates, uses Excel data or fallback rates.
        
        Args:
            from_currency: Source currency code (e.g., 'USD')
            to_currency: Target currency code (e.g., 'CNY')
            date: Date for which to get the exchange rate
            
        Returns:
            Exchange rate as float, or None if rate cannot be determined
        """
        # Handle same currency case
        if from_currency == to_currency:
            return 1.0
        
        # Convert date to string for caching
        date_str = date.strftime('%Y-%m-%d')
        cache_key = (from_currency, to_currency, date_str)
        
        # Check cache first
        if cache_key in self.cache:
            logger.debug(f"Using cached rate for {from_currency}/{to_currency} on {date_str}: {self.cache[cache_key]}")
            return self.cache[cache_key]
        
        rate = None
        
        # NEW: For recent dates (< 7 days), try Google Finance first
        days_old = (pd.Timestamp.now() - date).days
        if self.enable_google_finance and days_old < 7 and not self.prefer_excel:
            try:
                connector = get_google_finance_connector()
                self.google_finance_call_count += 1
                rate = connector.get_exchange_rate(from_currency, to_currency)
                
                if rate is not None:
                    self.google_finance_success_count += 1
                    logger.info(f"✓ Google Finance (recent date {date_str}) {from_currency}/{to_currency}: {rate:.4f}")
                    self.cache[cache_key] = rate
                    return rate
            except Exception as e:
                logger.debug(f"Google Finance error for {from_currency}/{to_currency} on {date_str}: {e}")
        
        # STRATEGY 1: Try Excel FIRST if prefer_excel=True (recommended for historical data)
        if self.prefer_excel or days_old >= 7:  # Always use Excel for old dates
            rate = self._get_excel_fallback_rate(from_currency, to_currency, date)
            if rate is not None:
                logger.debug(f"Using Excel rate (historical) for {from_currency}/{to_currency} on {date_str}: {rate:.4f}")
                # Cache and return immediately
                self.cache[cache_key] = rate
                return rate
        
        # STRATEGY 2: Try forex API if enabled (disabled by default due to performance issues)
        if FOREX_AVAILABLE and self.currency_rates and self.enable_forex_api:
            try:
                # Try to get rate for the exact date with timeout
                rate = self._fetch_rate_from_api_with_timeout(from_currency, to_currency, date)
                
                if rate is None:
                    # Try alternative dates if exact date fails
                    rate = self._try_alternative_dates(from_currency, to_currency, date)
                    
            except Exception as e:
                logger.warning(f"API call failed for {from_currency}/{to_currency} on {date_str}: {e}\")")
                rate = None
        
        # STRATEGY 3: Use fallback rates (Excel if not tried yet, then hardcoded)
        if rate is None:
            rate = self._get_fallback_rate(from_currency, to_currency, date)
            if rate:
                source = "Excel" if not self.prefer_excel and self.excel_fallback_count > 0 else "hardcoded"
                logger.info(f"Using {source} fallback rate for {from_currency}/{to_currency}: {rate}")
        
        # Cache the result (even if None)
        if rate is not None:
            self.cache[cache_key] = rate
            logger.debug(f"Cached rate for {from_currency}/{to_currency} on {date_str}: {rate}")
        
        return rate
    
    def get_latest_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Get latest/current exchange rate (for real-time data).
        
        Priority order:
        1. Google Finance (if enabled and not prefer_excel)
        2. Excel rates (if prefer_excel or Google Finance disabled)
        3. Hardcoded fallback rates
        
        Args:
            from_currency: Source currency code (e.g., 'USD')
            to_currency: Target currency code (e.g., 'CNY')
            
        Returns:
            Latest exchange rate as float, or None if rate cannot be determined
        """
        # Handle same currency case
        if from_currency == to_currency:
            return 1.0
        
        # Priority 1: Google Finance (if enabled and not prefer_excel)
        if self.enable_google_finance and not self.prefer_excel:
            try:
                connector = get_google_finance_connector()
                self.google_finance_call_count += 1
                rate = connector.get_exchange_rate(from_currency, to_currency)
                
                if rate is not None:
                    self.google_finance_success_count += 1
                    logger.info(f"✓ Google Finance {from_currency}/{to_currency}: {rate:.4f}")
                    return rate
                else:
                    logger.warning(f"Google Finance failed for {from_currency}/{to_currency}, trying fallbacks")
            except Exception as e:
                logger.warning(f"Google Finance error for {from_currency}/{to_currency}: {e}")
        
        # Priority 2: Excel fallback (most recent rate)
        if self.use_excel_fallback and self.excel_rates is not None:
            try:
                if not self.excel_rates.empty:
                    latest_rate = self.excel_rates.iloc[-1]
                    if pd.notna(latest_rate) and latest_rate > 0:
                        self.excel_fallback_count += 1
                        logger.info(f"Using Excel latest rate for {from_currency}/{to_currency}: {latest_rate:.4f}")
                        return float(latest_rate)
            except Exception as e:
                logger.warning(f"Error accessing Excel rates: {e}")
        
        # Priority 3: Hardcoded fallback
        pair = (from_currency, to_currency)
        if pair in self.fallback_rates:
            self.hardcoded_fallback_count += 1
            rate = self.fallback_rates[pair]
            logger.info(f"Using hardcoded fallback rate for {from_currency}/{to_currency}: {rate:.4f}")
            return rate
        
        logger.error(f"No rate source available for {from_currency}/{to_currency}")
        return None
    
    def _fetch_rate_from_api_with_timeout(self, from_currency: str, to_currency: str, date: pd.Timestamp) -> Optional[float]:
        """
        Fetch exchange rate from forex-python API with HARD timeout enforcement.
        
        Uses threading to enforce timeout since forex-python doesn't support it directly.
        This prevents API calls from taking 200+ seconds.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            date: Date for rate lookup
            
        Returns:
            Exchange rate or None if fetch fails or times out
        """
        # Check if we've exceeded total time budget
        if self.total_api_time >= self.max_total_api_time:
            logger.warning(f"Exceeded total API time budget ({self.total_api_time:.1f}s >= {self.max_total_api_time}s). "
                          "Skipping further API calls.")
            return None
        
        self.api_call_count += 1
        start_time = time.time()
        result = [None]  # Use list to share result between threads
        
        def fetch_in_thread():
            try:
                date_obj = date.to_pydatetime() if hasattr(date, 'to_pydatetime') else date
                result[0] = self.currency_rates.get_rate(from_currency, to_currency, date_obj)
            except Exception as e:
                logger.debug(f"API fetch error: {e}")
                result[0] = None
        
        # Run API call in thread with timeout
        thread = threading.Thread(target=fetch_in_thread, daemon=True)
        thread.start()
        thread.join(timeout=self.api_timeout)
        
        elapsed = time.time() - start_time
        self.total_api_time += elapsed
        
        if thread.is_alive():
            # Timeout occurred
            self.timeout_count += 1
            self.failed_api_calls += 1
            logger.warning(f"API call #{self.api_call_count} TIMED OUT after {self.api_timeout}s "
                          f"for {from_currency}/{to_currency} on {date.date()}")
            return None
        
        rate = result[0]
        if rate is not None:
            logger.debug(f"API call #{self.api_call_count}: {from_currency}/{to_currency} = {rate} "
                        f"on {date.date()} ({elapsed:.2f}s)")
        else:
            self.failed_api_calls += 1
            logger.debug(f"API call #{self.api_call_count} FAILED after {elapsed:.2f}s")
        
        return rate
    
    def _try_alternative_dates(self, from_currency: str, to_currency: str, base_date: pd.Timestamp) -> Optional[float]:
        """
        Try alternative dates around the base date if exact date fails.
        
        PERFORMANCE OPTIMIZATION: Reduced from 8 attempts to 2 (only ±1 day).
        This reduces worst-case API calls by 75%.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            base_date: Original date that failed
            
        Returns:
            Exchange rate or None if all alternatives fail
        """
        # CRITICAL CHANGE: Only try ±1 day (was ±1, ±2, ±3, ±7 days = 8 attempts)
        # This is a 75% reduction in API calls for failed date lookups
        for days_offset in [1, -1][:self.max_alternative_attempts]:
            try:
                alt_date = base_date + timedelta(days=days_offset)
                rate = self._fetch_rate_from_api_with_timeout(from_currency, to_currency, alt_date)
                if rate is not None:
                    logger.debug(f"Found rate using alternative date {alt_date.strftime('%Y-%m-%d')}: {rate}")
                    return rate
            except Exception:
                continue
        
        return None
    
    def _get_excel_fallback_rate(self, from_currency: str, to_currency: str, date: pd.Timestamp) -> Optional[float]:
        """
        Get exchange rate from Excel data (Ref_USD_FX_Rate column).
        
        This uses the static rates stored in your Excel file's monthly sheet.
        Priority: Exact date > Nearest date (within 30 days).
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            date: Date for rate lookup
            
        Returns:
            Exchange rate from Excel or None if not available
        """
        if not self.use_excel_fallback or self.excel_rates is None or self.excel_rates.empty:
            return None
        
        # Currently only supports USD/CNY from Excel
        if not ((from_currency == 'USD' and to_currency == 'CNY') or 
                (from_currency == 'CNY' and to_currency == 'USD')):
            return None
        
        try:
            # Try exact date first
            if date in self.excel_rates.index:
                rate = self.excel_rates.loc[date]
                if pd.notna(rate) and rate > 0:
                    self.excel_fallback_count += 1
                    if from_currency == 'CNY' and to_currency == 'USD':
                        rate = 1.0 / rate
                    logger.debug(f"Using Excel rate for {from_currency}/{to_currency} on {date.date()}: {rate:.4f}")
                    return float(rate)
            
            # Try nearest date within 30 days
            date_diff = abs(self.excel_rates.index - date)
            if len(date_diff) > 0:
                nearest_idx = date_diff.argmin()
                min_diff = date_diff[nearest_idx]
                
                if min_diff <= pd.Timedelta(days=30):
                    nearest_date = self.excel_rates.index[nearest_idx]
                    rate = self.excel_rates.iloc[nearest_idx]
                    
                    if pd.notna(rate) and rate > 0:
                        self.excel_fallback_count += 1
                        if from_currency == 'CNY' and to_currency == 'USD':
                            rate = 1.0 / rate
                        logger.debug(f"Using Excel rate from {nearest_date.date()} (±{min_diff.days} days) "
                                   f"for {from_currency}/{to_currency}: {rate:.4f}")
                        return float(rate)
        
        except Exception as e:
            logger.debug(f"Error retrieving Excel fallback rate: {e}")
        
        return None
    
    def _get_fallback_rate(self, from_currency: str, to_currency: str, date: pd.Timestamp = None) -> Optional[float]:
        """
        Get fallback exchange rate with priority: Excel data > Hardcoded rates.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            date: Optional date for Excel lookup
            
        Returns:
            Fallback exchange rate or None if not available
        """
        # Priority 1: Try Excel rates if date provided
        if date is not None:
            excel_rate = self._get_excel_fallback_rate(from_currency, to_currency, date)
            if excel_rate is not None:
                return excel_rate
        
        # Priority 2: Hardcoded rates
        # Check direct mapping
        key = (from_currency, to_currency)
        if key in self.fallback_rates:
            self.hardcoded_fallback_count += 1
            return self.fallback_rates[key]
        
        # Check inverse mapping
        inverse_key = (to_currency, from_currency)
        if inverse_key in self.fallback_rates:
            self.hardcoded_fallback_count += 1
            return 1.0 / self.fallback_rates[inverse_key]
        
        logger.warning(f"No fallback rate available for {from_currency}/{to_currency}")
        return None
    
    def convert_amount(self, amount: float, from_currency: str, to_currency: str, date: pd.Timestamp) -> Optional[float]:
        """
        Convert an amount from one currency to another for a specific date.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            date: Date for conversion rate lookup
            
        Returns:
            Converted amount or None if conversion fails
        """
        if amount == 0:
            return 0.0
        
        rate = self.get_historical_rate(from_currency, to_currency, date)
        if rate is None:
            logger.error(f"Cannot convert {amount} {from_currency} to {to_currency}: no rate available")
            return None
        
        converted = amount * rate
        logger.debug(f"Converted {amount} {from_currency} to {converted:.2f} {to_currency} (rate: {rate})")
        return converted
    
    def clear_cache(self):
        """Clear the exchange rate cache."""
        self.cache.clear()
        logger.info("Currency conversion cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get statistics about the current cache."""
        return {
            'total_cached_rates': len(self.cache),
            'unique_currency_pairs': len(set((key[0], key[1]) for key in self.cache.keys()))
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get detailed performance statistics."""
        avg_api_time = self.total_api_time / self.api_call_count if self.api_call_count > 0 else 0
        success_rate = (self.api_call_count - self.failed_api_calls) / self.api_call_count if self.api_call_count > 0 else 0
        
        return {
            'total_api_calls': self.api_call_count,
            'failed_api_calls': self.failed_api_calls,
            'timeout_count': self.timeout_count,
            'success_rate': success_rate,
            'total_api_time_seconds': self.total_api_time,
            'avg_api_time_seconds': avg_api_time,
            'excel_fallback_count': self.excel_fallback_count,
            'hardcoded_fallback_count': self.hardcoded_fallback_count,
            'cache_size': len(self.cache),
            'cache_hit_rate': len(self.cache) / max(1, self.api_call_count + self.excel_fallback_count + self.hardcoded_fallback_count),
            'forex_api_enabled': self.enable_forex_api,
            'prefer_excel': self.prefer_excel
        }


# Global instance for easy access
_currency_service = None

def initialize_currency_service(excel_rates: Optional[pd.Series] = None, 
                               use_excel_fallback: bool = True,
                               prefer_excel: bool = True,
                               enable_forex_api: bool = False) -> CurrencyConverterService:
    """
    Initialize the global currency converter service with Excel rates.
    
    This should be called by DataManager during initialization to provide
    Excel-based fallback rates.
    
    Args:
        excel_rates: Optional pd.Series with DatetimeIndex containing USD/CNY rates from Excel
        use_excel_fallback: If True, use Excel rates as fallback before hardcoded rates
        prefer_excel: If True, try Excel BEFORE API calls (recommended, default=True)
        enable_forex_api: If True, enable slow forex-python API calls (default=False for performance)
        
    Returns:
        The initialized currency service
    """
    global _currency_service
    _currency_service = CurrencyConverterService(
        excel_rates=excel_rates, 
        use_excel_fallback=use_excel_fallback,
        prefer_excel=prefer_excel,
        enable_forex_api=enable_forex_api
    )
    return _currency_service

def get_currency_service() -> CurrencyConverterService:
    """
    Get the global currency converter service instance.
    
    If not initialized, creates a new instance without Excel rates.
    For best performance, call initialize_currency_service() first with Excel rates.
    """
    global _currency_service
    if _currency_service is None:
        logger.warning("Currency service not initialized with Excel rates. Using hardcoded fallbacks only.")
        _currency_service = CurrencyConverterService()
    return _currency_service

def get_historical_rate(from_currency: str, to_currency: str, date: pd.Timestamp) -> Optional[float]:
    """
    Convenience function to get historical exchange rate.
    
    Args:
        from_currency: Source currency code (e.g., 'USD')
        to_currency: Target currency code (e.g., 'CNY') 
        date: Date for which to get the exchange rate
        
    Returns:
        Exchange rate as float, or None if rate cannot be determined
    """
    service = get_currency_service()
    return service.get_historical_rate(from_currency, to_currency, date)

def convert_amount(amount: float, from_currency: str, to_currency: str, date: pd.Timestamp) -> Optional[float]:
    """
    Convenience function to convert currency amount.
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code
        to_currency: Target currency code  
        date: Date for conversion rate lookup
        
    Returns:
        Converted amount or None if conversion fails
    """
    service = get_currency_service()
    return service.convert_amount(amount, from_currency, to_currency, date)