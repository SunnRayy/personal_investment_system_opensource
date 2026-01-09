#!/usr/bin/env python3
"""
Macro Analyzer - Market Sentiment Indicators
Fetches and analyzes macroeconomic indicators for market thermometer feature.
"""

import os
import json
import logging
import requests
import pandas as pd
import numpy as np
import yaml
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from time import sleep
from io import BytesIO
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class MacroAnalyzer:
    """
    Fetches and analyzes macroeconomic indicators for market sentiment assessment.
    
    Provides data for the Market Thermometer feature, including:
    - Shiller P/E (CAPE) Ratio
    - CNN Fear & Greed Index
    - Buffett Indicator (Total Market Cap / GDP)
    
    Implements 24-hour caching to minimize API calls.
    """
    
    # Data source URLs
    SHILLER_URL = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"
    GURUFOCUS_SHILLER_URL = "https://www.gurufocus.com/shiller-PE.php"  # GuruFocus Shiller PE (primary)
    FEAR_GREED_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    FEAR_GREED_WEBPAGE_URL = "https://www.cnn.com/markets/fear-and-greed"  # Fallback webpage scraping
    GURUFOCUS_URL = "https://www.gurufocus.com/global-market-valuation.php"  # GuruFocus Buffett data
    FRED_API_BASE = "https://api.stlouisfed.org/fred/series/observations"
    WORLD_BANK_API_BASE = "https://api.worldbank.org/v2/country/{country}/indicator/CM.MKT.LCAP.GD.ZS?format=json&per_page=70&page=1"
    
    # Gold indicator URLs (for Phase 1: Gold Volatility System)
    # PRIMARY: Web scraping URLs (stable and reliable)
    GOOGLE_FINANCE_GVZ_URL = "https://www.google.com/finance/quote/GVZ:INDEXCBOE"  # GVZ scraping
    GOOGLE_FINANCE_SP500_URL = "https://www.google.com/finance/quote/.INX:INDEXSP"  # S&P 500 scraping
    GOOGLE_FINANCE_GLD_URL = "https://www.google.com/finance/quote/GLD:NYSEARCA"  # GLD ETF (1/10 oz gold)
    KITCO_URL = "https://www.kitco.com/"  # Gold/Silver ratio
    
    # Crypto indicator URLs (for Phase 2: Crypto Volatility System)
    COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"  # CoinGecko API
    COINGECKO_BTC_URL = f"{COINGECKO_API_BASE}/simple/price?ids=bitcoin&vs_currencies=usd"  # BTC price
    COINGECKO_ETH_URL = f"{COINGECKO_API_BASE}/simple/price?ids=ethereum&vs_currencies=usd"  # ETH price
    COINGECKO_GLOBAL_URL = f"{COINGECKO_API_BASE}/global"  # BTC dominance
    COINGECKO_BTC_HISTORY_URL = f"{COINGECKO_API_BASE}/coins/bitcoin/market_chart?vs_currency=usd&days=30"  # BTC 30-day price history
    COINGECKO_ETH_HISTORY_URL = f"{COINGECKO_API_BASE}/coins/ethereum/market_chart?vs_currency=usd&days=30"  # ETH 30-day price history
    GOLDPRICE_URL = "https://goldprice.org/"  # Fallback for gold prices
    # DEPRECATED: Yahoo Finance API (rate-limited, unreliable)
    YAHOO_FINANCE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"  # Fallback only
    CBOE_GVZ_URL = "https://cdn.cboe.com/api/global/delayed_quotes/charts/_GVZ.json"  # Fallback (403 Forbidden)
    
    # Timeout for API requests (seconds)
    REQUEST_TIMEOUT = 10
    
    def __init__(self, cache_path: str = 'data/macro_cache.json', cache_ttl_hours: int = 24,
                 config_path: str = 'config/settings.yaml',
                 manual_inputs_path: str = 'config/manual_indicators.json'):
        """
        Initialize MacroAnalyzer with caching configuration.
        
        Args:
            cache_path: Path to cache file (default: 'data/macro_cache.json')
            cache_ttl_hours: Cache time-to-live in hours (default: 24)
            config_path: Path to settings.yaml file (default: 'config/settings.yaml')
            manual_inputs_path: Path to manual indicator overrides (default: 'config/manual_indicators.json')
        """
        self.cache_path = Path(cache_path)
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.manual_inputs_path = Path(manual_inputs_path)
        
        # Additional cache paths for gold and crypto analysis (same TTL)
        self.gold_cache_path = Path('data/gold_cache.json')
        self.crypto_cache_path = Path('data/crypto_cache.json')
        
        # Load FRED API key from config or environment
        self.fred_api_key = self._load_fred_api_key(config_path)
        
        # Ensure cache directory exists
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"MacroAnalyzer initialized with cache at {self.cache_path}, TTL={cache_ttl_hours}h")
    
    def _load_fred_api_key(self, config_path: str) -> Optional[str]:
        """
        Load FRED API key from settings.yaml or environment variable.
        
        Priority: Environment variable > settings.yaml
        
        Args:
            config_path: Path to settings.yaml file
            
        Returns:
            FRED API key or None if not found
        """
        # First try environment variable
        api_key = os.environ.get('FRED_API_KEY')
        if api_key:
            logger.info("Using FRED API key from environment variable")
            return api_key
        
        # Then try settings.yaml
        try:
            logger.debug(f"Attempting to load FRED API key from {config_path}")
            with open(config_path, 'r', encoding='utf-8') as f:
                settings = yaml.safe_load(f)
            
            external_data = settings.get('external_data', {})
            logger.debug(f"external_data keys: {external_data.keys() if external_data else 'None'}")
            
            fred_config = external_data.get('fred', {})
            logger.debug(f"fred config: {fred_config}")
            
            api_key = fred_config.get('api_key')
            if api_key:
                logger.info("Using FRED API key from settings.yaml")
                return api_key
            else:
                logger.warning("FRED API key found in config but value is empty")
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}")
        except Exception as e:
            logger.warning(f"Could not load FRED API key from {config_path}: {e}")
        
        logger.warning("FRED API key not found in environment or config - Buffett Indicator will be unavailable")
        return None
    
    def get_market_thermometer(self) -> Dict[str, Any]:
        """
        Main public method - orchestrates fetching all indicators.
        
        Returns structured dictionary with all indicator data:
        {
            'shiller_pe': {'value': float, 'zone': str, 'level': int, 'status': str, 'error_message': str},
            'fear_greed': {...},
            'vix': {...},  # Alternative sentiment indicator
            'buffett_us': {...},
            'buffett_china': {...},
            'buffett_japan': {...},
            'buffett_europe': {...},
            'last_updated': str (ISO timestamp)
        }
        
        Returns:
            Dictionary containing all market indicators with metadata
        """
        logger.info("Starting market thermometer data fetch")
        
        # Check if manual inputs have been updated (check file modification time)
        manual_inputs_modified = False
        if self.manual_inputs_path.exists():
            manual_mtime = self.manual_inputs_path.stat().st_mtime
            cache_path = Path(self.cache_path)
            if cache_path.exists():
                cache_mtime = cache_path.stat().st_mtime
                if manual_mtime > cache_mtime:
                    manual_inputs_modified = True
                    logger.info("Manual inputs file is newer than cache - cache will be refreshed")
        
        # Check cache first (but skip if manual inputs were updated)
        if not manual_inputs_modified:
            cached_data = self._load_cache()
            if cached_data:
                logger.info("Using cached market thermometer data")
                return cached_data
        
        # Fetch all indicators
        results = {
            'shiller_pe': self._fetch_shiller_pe(),
            'fear_greed': self._fetch_fear_greed(),
            'vix': self._fetch_vix(),
            # For Buffett indicators, use FRED primary and World Bank as fallback (more up-to-date)
            'buffett_us': self._fetch_buffett_indicator('DDDM01USA156NWDB', 'United States', 'USA'),
            'buffett_china': self._fetch_buffett_indicator('DDDM01CNA156NWDB', 'China', 'CHN'),
            'buffett_japan': self._fetch_buffett_indicator('DDDM01JPA156NWDB', 'Japan', 'JPN'),
            'buffett_europe': self._fetch_buffett_indicator('DDDM01GBA156NWDB', 'United Kingdom', 'GBR'),
            'last_updated': datetime.now().isoformat()
        }
        
        # Save to cache
        self._save_cache(results)
        
        # Log summary
        total_indicators = 7
        success_count = sum(1 for key in ['shiller_pe', 'fear_greed', 'vix', 'buffett_us', 'buffett_china', 'buffett_japan', 'buffett_europe']
                           if results[key]['status'] == 'success')
        logger.info(f"Market thermometer fetch complete: {success_count}/{total_indicators} indicators successful")
        
        return results
    
    def get_gold_analysis(self) -> Dict[str, Any]:
        """
        Fetch gold indicators and generate buy/sell recommendation.
        
        This method fetches 3 gold indicators:
        - GVZ (Cboe Gold Volatility Index)
        - Gold/Silver ratio
        - S&P 500/Gold ratio
        
        Then uses AltAssetsAdvisor to generate a scored recommendation.
        Uses 24h cache to avoid repeated API calls.
        
        Returns:
            Dictionary with:
            - indicators: Dict with GVZ, gold_silver_ratio, sp500_gold_ratio
            - recommendation: Dict from AltAssetsAdvisor (score, recommendation, signals)
            - status: 'success' or 'error'
            - error_message: Optional error details
        """
        # Check cache first
        cached_gold = self._load_gold_cache()
        if cached_gold:
            logger.info("Using cached gold analysis data")
            return cached_gold
        
        logger.info("Starting gold indicators analysis (cache miss or expired)")
        
        try:
            # Import advisor (lazy import to avoid circular dependencies)
            from src.investment_optimization.alt_assets_advisor import AltAssetsAdvisor
            
            # Fetch all 3 indicators
            gvz_result = self._fetch_gvz()
            gold_silver_result = self._fetch_gold_silver_ratio()
            sp500_gold_result = self._fetch_sp500_gold_ratio()
            
            # Extract values (None if fetch failed)
            gvz = gvz_result.get('value') if gvz_result.get('status') == 'success' else None
            gold_silver_ratio = gold_silver_result.get('value') if gold_silver_result.get('status') == 'success' else None
            sp500_gold_ratio = sp500_gold_result.get('value') if sp500_gold_result.get('status') == 'success' else None
            
            # Log fetch results
            logger.info(f"Gold indicators fetched - GVZ: {gvz}, Gold/Silver: {gold_silver_ratio}, S&P/Gold: {sp500_gold_ratio}")
            
            # Initialize advisor and calculate score
            advisor = AltAssetsAdvisor(config_path='config/alt_assets_indicators.yaml')
            recommendation = advisor.calculate_gold_score(
                gvz=gvz,
                gold_silver_ratio=gold_silver_ratio,
                sp500_gold_ratio=sp500_gold_ratio
            )
            
            # Compile results
            result = {
                'indicators': {
                    'gvz': gvz_result,
                    'gold_silver_ratio': gold_silver_result,
                    'sp500_gold_ratio': sp500_gold_result
                },
                'recommendation': recommendation,
                'status': 'success',
                'last_updated': datetime.now().isoformat()
            }
            
            logger.info(f"Gold analysis complete - Recommendation: {recommendation.get('recommendation')}, Score: {recommendation.get('total_score')}")
            
            # Save to cache for future requests
            self._save_gold_cache(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in gold analysis: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error_message': str(e),
                'indicators': {},
                'recommendation': {},
                'last_updated': datetime.now().isoformat()
            }
    
    def get_crypto_analysis(self) -> Dict[str, Any]:
        """
        Fetch crypto indicators and generate buy/sell recommendations for BTC and ETH.
        
        This method fetches 6 crypto indicators:
        - BTC 30-day volatility
        - ETH 30-day volatility
        - BTC/ETH price ratio
        - BTC dominance (% of total crypto market cap)
        - BTC/QQQ ratio (crypto vs tech stocks) **NEW in Phase 2**
        - Crypto Fear & Greed Index **NEW in Phase 2**
        
        Then uses AltAssetsAdvisor to generate separate scored recommendations for BTC and ETH.
        
        Returns:
            Dictionary with:
            - indicators: Dict with all 6 indicators
            - btc_recommendation: Dict from AltAssetsAdvisor for BTC
            - eth_recommendation: Dict from AltAssetsAdvisor for ETH
            - market_sentiment: Overall crypto market sentiment summary **NEW in Phase 2**
            - status: 'success' or 'error'
            - error_message: Optional error details
        """
        # Check cache first
        cached_crypto = self._load_crypto_cache()
        if cached_crypto:
            logger.info("Using cached crypto analysis data")
            return cached_crypto
        
        logger.info("Starting crypto indicators analysis (cache miss or expired)")
        
        try:
            # Import advisor (lazy import to avoid circular dependencies)
            from src.investment_optimization.alt_assets_advisor import AltAssetsAdvisor
            
            # Fetch all 6 indicators (Phase 2 adds 2 new ones)
            btc_vol_result = self._fetch_btc_volatility()
            eth_vol_result = self._fetch_eth_volatility()
            btc_eth_ratio_result = self._fetch_btc_eth_ratio()
            btc_dominance_result = self._fetch_btc_dominance()
            # DISABLED FOR PERFORMANCE: btc_qqq_ratio_result = self._fetch_btc_qqq_ratio()
            btc_qqq_ratio_result = {'status': 'disabled', 'value': None, 'message': 'Disabled for performance'}
            crypto_fng_result = self._fetch_crypto_fear_greed()  # **NEW Phase 2**
            
            # Extract values (None if fetch failed)
            btc_volatility = btc_vol_result.get('value') if btc_vol_result.get('status') == 'success' else None
            eth_volatility = eth_vol_result.get('value') if eth_vol_result.get('status') == 'success' else None
            btc_eth_ratio = btc_eth_ratio_result.get('value') if btc_eth_ratio_result.get('status') == 'success' else None
            btc_dominance = btc_dominance_result.get('value') if btc_dominance_result.get('status') == 'success' else None
            
            # Log fetch results
            logger.info(f"Crypto indicators fetched - BTC vol: {btc_volatility}, ETH vol: {eth_volatility}, BTC/ETH: {btc_eth_ratio}, BTC dom: {btc_dominance}")
            
            # **PHASE 3**: Calculate overall crypto market sentiment with weighted scoring
            market_sentiment = self._calculate_crypto_market_sentiment(
                btc_qqq_ratio_result,
                crypto_fng_result,
                btc_vol_result,
                eth_vol_result,
                btc_eth_ratio_result,  # Phase 3 addition
                btc_dominance_result    # Phase 3 addition
            )
            
            # Initialize advisor and calculate scores for both BTC and ETH
            advisor = AltAssetsAdvisor(config_path='config/alt_assets_indicators.yaml')
            
            # Calculate BTC recommendation
            btc_recommendation = advisor.calculate_crypto_score(
                crypto_type='btc',
                volatility=btc_volatility,
                btc_eth_ratio=btc_eth_ratio,
                btc_dominance=btc_dominance
            )
            
            # Calculate ETH recommendation
            eth_recommendation = advisor.calculate_crypto_score(
                crypto_type='eth',
                volatility=eth_volatility,
                btc_eth_ratio=btc_eth_ratio,
                btc_dominance=btc_dominance
            )
            
            # Compile results
            result = {
                'indicators': {
                    'btc_volatility': btc_vol_result,
                    'eth_volatility': eth_vol_result,
                    'btc_eth_ratio': btc_eth_ratio_result,
                    'btc_dominance': btc_dominance_result,
                    'btc_qqq_ratio': btc_qqq_ratio_result,  # **NEW Phase 2**
                    'crypto_fear_greed': crypto_fng_result  # **NEW Phase 2**
                },
                'btc_recommendation': btc_recommendation,
                'eth_recommendation': eth_recommendation,
                'market_sentiment': market_sentiment,  # **NEW Phase 2**
                'status': 'success',
                'last_updated': datetime.now().isoformat()
            }
            
            logger.info(f"Crypto analysis complete - Market: {market_sentiment['overall']}, BTC: {btc_recommendation.get('recommendation')}, ETH: {eth_recommendation.get('recommendation')}")
            
            # Save to cache for future requests
            self._save_crypto_cache(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in crypto analysis: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error_message': str(e),
                'indicators': {},
                'btc_recommendation': {},
                'eth_recommendation': {},
                'market_sentiment': {},  # **NEW Phase 2**
                'last_updated': datetime.now().isoformat()
            }
    
    def _fetch_shiller_pe(self) -> Dict[str, Any]:
        """
        Fetch and classify Shiller P/E (CAPE) ratio.
        
        Tries multiple sources in order:
        1. Manual input override (if enabled)
        2. GuruFocus webpage scraping (primary - daily updates)
        3. Yale University Excel file (fallback)
        
        Returns:
            Dictionary with value, zone, level, status, and optional error_message
        """
        logger.info("Fetching Shiller P/E ratio...")
        
        # Check for manual input override
        manual_result = self._get_manual_input('shiller_pe', self._classify_shiller, "Shiller P/E")
        if manual_result:
            return manual_result
        
        # Try GuruFocus first (most current data)
        gurufocus_result = self._fetch_gurufocus_shiller()
        if gurufocus_result and gurufocus_result.get('status') == 'success':
            return gurufocus_result
        else:
            logger.info("GuruFocus failed for Shiller PE, falling back to Yale data")
        
        # Fallback to Yale data
        try:
            # Download Excel file
            response = requests.get(self.SHILLER_URL, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # Parse Excel file
            # The Shiller data file has CAPE in column 'CAPE' or column index ~10
            df = pd.read_excel(BytesIO(response.content), sheet_name='Data', skiprows=7)
            
            # Get the latest non-null CAPE value
            # Column name may vary - try common variations
            cape_col = None
            for col_name in ['CAPE', 'P/E10', 'Cyclically Adjusted PE Ratio']:
                if col_name in df.columns:
                    cape_col = col_name
                    break
            
            if cape_col is None:
                # Try by position (usually column 10 or 11)
                if len(df.columns) > 10:
                    cape_col = df.columns[10]
                else:
                    raise ValueError("Cannot find CAPE column in Shiller data")
            
            # Get latest CAPE value first
            cape_series = pd.to_numeric(df[cape_col], errors='coerce')
            cape_value = cape_series.dropna().iloc[-1]
            
            # Determine date column (Shiller file typically has 'Date' or 'Year'+'Month')
            date_value = None
            if 'Date' in df.columns:
                date_series = pd.to_datetime(df['Date'], errors='coerce')
                date_value = date_series.dropna().iloc[-1]
            elif {'Year', 'Month'}.issubset(df.columns):
                try:
                    # Get the last row with valid CAPE data
                    last_valid_idx = cape_series.dropna().index[-1]
                    last_row = df.iloc[last_valid_idx]
                    year = int(float(last_row['Year']))
                    month = int(float(last_row['Month']))
                    date_value = datetime(year, month, 1)
                except Exception as e:
                    logger.warning(f"Failed to parse Year/Month from Yale data: {e}")
                    # Use current date as fallback since we can't determine actual date
                    date_value = datetime.now()
            else:
                # No date columns found, use current date
                logger.warning("No date columns found in Yale Shiller data, using current date")
                date_value = datetime.now()
            
            # Classify
            zone, level = self._classify_shiller(cape_value)
            
            logger.info(f"Shiller P/E fetched successfully: {cape_value:.2f} ({zone})")
            
            # Calculate data age for freshness validation
            data_age_days = 0
            data_age_warning = None
            if date_value is not None:
                data_age_days = (datetime.now() - date_value).days
                if data_age_days > 60:  # Shiller data is monthly, warn if >2 months old
                    data_age_warning = f"Data is {data_age_days} days old (last update: {date_value.strftime('%Y-%m-%d')})"
                    logger.warning(f"Shiller P/E data is {data_age_days} days old")

            return {
                'value': float(cape_value),
                'zone': zone,
                'level': level,
                'status': 'success',
                'error_message': None,
                'last_updated': date_value.isoformat() if date_value else datetime.now().isoformat(),
                'data_age_days': data_age_days,
                'data_age_warning': data_age_warning,
                'source': 'Yale (Shiller)'
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch Shiller P/E: {str(e)}")
            return {
                'value': None,
                'zone': 'Unknown',
                'level': -1,
                'status': 'error',
                'error_message': str(e),
                'last_updated': None,
                'data_age_days': None,
                'data_age_warning': None
            }
    
    def _fetch_fear_greed(self) -> Dict[str, Any]:
        """
        Fetch and classify CNN Fear & Greed Index.
        
        Tries multiple sources in order:
        1. Manual input override (if enabled)
        2. CNN JSON API (primary)
        3. CNN webpage scraping (fallback)
        
        Returns:
            Dictionary with value, zone, level, status, and optional error_message
        """
        logger.info("Fetching CNN Fear & Greed Index...")
        
        # Check for manual input override
        manual_result = self._get_manual_input('fear_greed', self._classify_fear_greed, "Fear & Greed")
        if manual_result:
            return manual_result
        
        try:
            # Try JSON API first (primary source)
            # Fetch JSON data
            response = requests.get(self.FEAR_GREED_URL, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract latest score
            # Data structure: {'fear_and_greed': {'score': float, 'rating': str, ...}}
            if 'fear_and_greed' in data:
                score = float(data['fear_and_greed']['score'])
            elif 'score' in data:
                score = float(data['score'])
            else:
                raise ValueError("Cannot find score in Fear & Greed data")
            
            # Classify
            zone, level = self._classify_fear_greed(score)
            
            logger.info(f"Fear & Greed Index fetched from JSON API successfully: {score:.0f} ({zone})")
            
            return {
                'value': float(score),
                'zone': zone,
                'level': level,
                'status': 'success',
                'error_message': None,
                'source': 'CNN JSON API',
                'last_updated': datetime.now().isoformat(),
                'data_age_days': 0  # Real-time data
            }
            
        except Exception as e:
            logger.warning(f"JSON API failed for Fear & Greed Index: {str(e)}, trying webpage scraping...")
            # Fallback to webpage scraping
            webpage_result = self._fetch_fear_greed_webpage()
            if webpage_result.get('status') == 'success':
                return webpage_result
            
            # Both methods failed
            logger.error("Failed to fetch Fear & Greed Index from all sources")
            return {
                'value': None,
                'zone': 'Unknown',
                'level': -1,
                'status': 'error',
                'error_message': f"JSON API: {str(e)}, Webpage: {webpage_result.get('error_message', 'Unknown error')}",
                'last_updated': None,
                'data_age_days': None,
                'data_age_warning': None
            }
    
    def _fetch_vix(self) -> Dict[str, Any]:
        """
        Fetch and classify VIX (CBOE Volatility Index) as alternative sentiment indicator.
        
        VIX measures expected market volatility - inverse of sentiment.
        Checks manual input override first before fetching from FRED.
        
        Returns:
            Dictionary with value, zone, level, status, and optional error_message
        """
        logger.info("Fetching VIX (Volatility Index)...")
        
        # Check for manual input override
        manual_result = self._get_manual_input('vix', self._classify_vix, "VIX")
        if manual_result:
            return manual_result
        
        if not self.fred_api_key:
            logger.warning("FRED API key not configured - VIX unavailable")
            return {
                'value': None,
                'zone': 'Unknown',
                'level': -1,
                'status': 'error',
                'error_message': 'FRED API key not configured'
            }
        
        try:
            # Fetch VIX from FRED
            params = {
                'series_id': 'VIXCLS',  # CBOE Volatility Index: VIX
                'api_key': self.fred_api_key,
                'file_type': 'json',
                'sort_order': 'desc',
                'limit': 1
            }
            response = requests.get(self.FRED_API_BASE, params=params, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            # Extract VIX value and date
            obs = data['observations'][0]
            vix_value = float(obs['value'])
            data_date = obs.get('date')
            
            # Classify (VIX is inverse - low VIX = complacency/greed, high VIX = fear)
            zone, level = self._classify_vix(vix_value)
            
            logger.info(f"VIX fetched successfully: {vix_value:.2f} ({zone})")
            
            # Freshness: warn if older than 1/7/30 days
            data_age_warning = None
            if data_date:
                try:
                    d = datetime.strptime(data_date, '%Y-%m-%d')
                    days_old = (datetime.now() - d).days
                    if days_old > 30:
                        data_age_warning = f"⚠️ Data is {days_old} days old"
                    elif days_old > 7:
                        data_age_warning = f"⚠️ Data is {days_old} days old"
                    elif days_old > 1:
                        data_age_warning = f"⚠️ Data is {days_old} days old"
                except Exception:
                    pass

            return {
                'value': float(vix_value),
                'zone': zone,
                'level': level,
                'status': 'success',
                'error_message': None,
                'date': data_date,
                'data_age_warning': data_age_warning,
                'source': 'FRED (VIXCLS)'
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch VIX: {str(e)}")
            return {
                'value': None,
                'zone': 'Unknown',
                'level': -1,
                'status': 'error',
                'error_message': str(e)
            }
    
    def _fetch_buffett_indicator(self, series_id: str = 'DDDM01USA156NWDB', country_name: str = 'United States', wb_country_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch and classify Buffett Indicator (Market Cap / GDP) for specified country.
        
        Uses multiple sources in order:
        1. Manual input override (if enabled)
        2. GuruFocus webpage scraping (most current, daily updates)
        3. FRED API (may be stale)
        4. World Bank API (fallback when FRED is too stale)
        
        Args:
            series_id: FRED series ID (default: US market cap to GDP)
            country_name: Country name for logging (default: 'United States')
            wb_country_code: 3-letter World Bank country code for fallback (e.g., USA, CHN)
        
        Returns:
            Dictionary with value, zone, level, status, error_message, country, date, data_age_warning, source
        """
        logger.info(f"Fetching Buffett Indicator for {country_name}...")
        
        # Check for manual input override first
        manual_key = {
            'United States': 'buffett_us',
            'China': 'buffett_china',
            'Japan': 'buffett_japan',
            'United Kingdom': 'buffett_europe'
        }.get(country_name)
        
        if manual_key:
            # For manual Buffett input, need a wrapper to pass percentage to classification
            def classify_buffett_percent(value_pct):
                return self._classify_buffett(value_pct / 100.0)
            
            manual_result = self._get_manual_input(manual_key, classify_buffett_percent, f"Buffett ({country_name})")
            if manual_result:
                manual_result['country'] = country_name
                return manual_result
        
        # Try GuruFocus scraping (most current source)
        guru_result = self._fetch_gurufocus_buffett(country_name)
        if guru_result and guru_result.get('status') == 'success':
            return guru_result
        else:
            logger.info(f"GuruFocus failed for {country_name}, falling back to FRED/World Bank")
        
        # Try FRED next
        if not self.fred_api_key:
            logger.warning("FRED API key not configured - Buffett Indicator unavailable")
            # Try World Bank directly if API key missing
            if wb_country_code:
                wb_result = self._fetch_world_bank_buffett(wb_country_code, country_name)
                if wb_result and wb_result.get('status') == 'success':
                    return wb_result
            return {
                'value': None,
                'zone': 'Unknown',
                'level': -1,
                'status': 'error',
                'error_message': 'FRED API key not configured',
                'country': country_name
            }
        
        try:
            # Fetch from FRED
            params = {
                'series_id': series_id,
                'api_key': self.fred_api_key,
                'file_type': 'json',
                'sort_order': 'desc',
                'limit': 1
            }
            response = requests.get(self.FRED_API_BASE, params=params, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            observation = data['observations'][0]
            ratio_pct = float(observation['value'])  # percent value from FRED
            data_date = observation['date']
            
            # Freshness check (annual data)
            data_age_warning = None
            data_age_years: Optional[float] = None
            try:
                d = datetime.strptime(data_date, '%Y-%m-%d')
                days_old = (datetime.now() - d).days
                if days_old > 365:
                    data_age_years = days_old / 365
                    data_age_warning = f"⚠️ Data is {data_age_years:.1f} years old"
            except Exception:
                pass

            # If too old, try World Bank fallback
            if (data_age_years is not None) and (data_age_years >= 2.0) and wb_country_code:
                wb_result = self._fetch_world_bank_buffett(wb_country_code, country_name)
                if wb_result and wb_result.get('status') == 'success':
                    return wb_result
            
            # Classify using ratio (percent/100)
            zone, level = self._classify_buffett(ratio_pct / 100.0)
            logger.info(f"Buffett Indicator ({country_name}) fetched successfully: {ratio_pct:.2f}% as of {data_date} ({zone})")
            return {
                'value': float(ratio_pct),
                'zone': zone,
                'level': level,
                'status': 'success',
                'error_message': None,
                'country': country_name,
                'date': data_date,
                'data_age_warning': data_age_warning,
                'data_age_years': data_age_years,
                'source': 'FRED'
            }
        except Exception as e:
            logger.error(f"Failed to fetch Buffett Indicator for {country_name}: {str(e)}")
            if wb_country_code:
                wb_result = self._fetch_world_bank_buffett(wb_country_code, country_name)
                if wb_result and wb_result.get('status') == 'success':
                    return wb_result
            return {
                'value': None,
                'zone': 'Unknown',
                'level': -1,
                'status': 'error',
                'error_message': str(e),
                'country': country_name
            }
    
    def _fetch_gurufocus_buffett(self, country_name: str) -> Dict[str, Any]:
        """
        Fetch Buffett Indicator from GuruFocus webpage by scraping HTML table.
        
        Scrapes https://www.gurufocus.com/global-market-valuation.php for current Buffett
        Indicator values (Total Market Cap / GDP ratio).
        
        Args:
            country_name: Country to fetch ('United States', 'China', 'Japan', 'United Kingdom')
        
        Returns:
            Dictionary with value, zone, level, status, error_message, country, date, source
        """
        logger.info(f"Fetching Buffett Indicator from GuruFocus for {country_name}...")
        
        try:
            # Fetch webpage
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = requests.get(self.GURUFOCUS_URL, headers=headers, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the table with country data
            # The table has countries in rows with columns: Country, GDP, Current %, Min %, Max %, Years, ETF
            # We need to extract the "Current %" column for the matching country
            
            # Map country names to their display names on GuruFocus
            country_map = {
                'United States': 'USA',
                'China': 'China',
                'Japan': 'Japan',
                'United Kingdom': 'UK'
            }
            
            target_country = country_map.get(country_name, country_name)
            
            # Find the table (it's in the page, look for rows with country data)
            tables = soup.find_all('table')
            buffett_value = None
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:  # Need at least country, gdp, current %
                        # First cell contains country name
                        country_cell = cells[0].get_text(strip=True)
                        if target_country in country_cell:
                            # Third cell (index 2) contains current percentage
                            try:
                                current_pct_text = cells[2].get_text(strip=True)
                                buffett_value = float(current_pct_text.replace('%', '').strip())
                                break
                            except (ValueError, IndexError):
                                continue
                if buffett_value is not None:
                    break
            
            if buffett_value is None:
                raise ValueError(f"Could not find Buffett Indicator for {country_name} in GuruFocus data")
            
            # Classify using ratio (percent/100)
            zone, level = self._classify_buffett(buffett_value / 100.0)
            
            # GuruFocus updates daily, assume current date
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            logger.info(f"GuruFocus Buffett Indicator ({country_name}) fetched successfully: {buffett_value:.2f}% ({zone})")
            
            return {
                'value': float(buffett_value),
                'zone': zone,
                'level': level,
                'status': 'success',
                'error_message': None,
                'country': country_name,
                'date': current_date,
                'data_age_warning': None,
                'source': 'GuruFocus'
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch GuruFocus Buffett Indicator for {country_name}: {str(e)}")
            return {
                'value': None,
                'zone': 'Unknown',
                'level': -1,
                'status': 'error',
                'error_message': str(e),
                'country': country_name
            }
    
    def _fetch_gurufocus_shiller(self) -> Dict[str, Any]:
        """
        Fetch Shiller P/E (CAPE) from GuruFocus webpage by scraping HTML.
        
        Scrapes https://www.gurufocus.com/shiller-PE.php for current Shiller P/E ratio.
        GuruFocus updates this daily, providing more current data than Yale's Excel file.
        
        Returns:
            Dictionary with value, zone, level, status, error_message, date, source
        """
        logger.info("Fetching Shiller P/E from GuruFocus...")
        
        try:
            # Fetch webpage
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = requests.get(self.GURUFOCUS_SHILLER_URL, headers=headers, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # The Shiller PE value is displayed prominently on the page
            # Look for patterns like "Current Shiller PE: 30.81" or similar
            shiller_value = None
            
            # Strategy 1: Look for the main display value (often in a large font near the top)
            # The page typically shows: "Shiller PE Ratio: XX.XX" or "Current: XX.XX"
            text_content = soup.get_text()
            
            # Try to find "Current" or "Shiller PE" followed by a number
            import re
            
            # Pattern 1: "Current: XX.XX" or "Current Shiller PE: XX.XX"
            patterns = [
                r'Current[:\s]+(\d+\.?\d*)',
                r'Shiller\s+PE[:\s]+(\d+\.?\d*)',
                r'CAPE[:\s]+(\d+\.?\d*)',
                r'PE\s+Ratio[:\s]+(\d+\.?\d*)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if matches:
                    # Filter to reasonable Shiller PE values (typically 5-50)
                    valid_matches = [float(m) for m in matches if 5 <= float(m) <= 100]
                    if valid_matches:
                        shiller_value = valid_matches[0]
                        break
            
            if shiller_value is None:
                raise ValueError("Could not extract Shiller P/E value from GuruFocus page")
            
            # Classify using ratio
            zone, level = self._classify_shiller(shiller_value)
            
            # GuruFocus updates daily, assume current date
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            logger.info(f"GuruFocus Shiller P/E fetched successfully: {shiller_value:.2f} ({zone})")
            
            return {
                'value': float(shiller_value),
                'zone': zone,
                'level': level,
                'status': 'success',
                'error_message': None,
                'date': current_date,
                'data_age_warning': None,
                'source': 'GuruFocus'
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch GuruFocus Shiller P/E: {str(e)}")
            return {
                'value': None,
                'zone': 'Unknown',
                'level': -1,
                'status': 'error',
                'error_message': str(e)
            }
    
    def _fetch_fear_greed_webpage(self) -> Dict[str, Any]:
        """
        Fetch CNN Fear & Greed Index by scraping the webpage (fallback method).
        
        Scrapes https://www.cnn.com/markets/fear-and-greed when JSON API fails.
        
        Returns:
            Dictionary with value, zone, level, status, and optional error_message
        """
        logger.info("Fetching Fear & Greed Index from CNN webpage...")
        
        try:
            # Fetch webpage
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = requests.get(self.FEAR_GREED_WEBPAGE_URL, headers=headers, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # Parse HTML - the index value is typically in a prominent display element
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # The Fear & Greed value appears in multiple places, look for numeric values in relevant sections
            # Strategy: Find text that looks like "27" or similar 0-100 values near "Fear" or "Greed" keywords
            
            fear_greed_value = None
            
            # Try to find the main display value - it's often in a large font near the gauge
            # Look for patterns like "27 Previous close" (the current value appears right before "Previous close")
            text_content = soup.get_text()
            
            # Search for pattern: number followed by "Previous close"
            # The webpage structure has: "27 Previous close Extreme Fear23 1 week ago Fear31 1 month ago"
            # We want the first number before "Previous close"
            import re
            
            # First try: Look for explicit "XX Previous close" pattern
            pattern = r'\b(\d{1,3})\s+Previous\s+close'
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            
            if matches:
                fear_greed_value = float(matches[0])
            else:
                # Fallback: Look for numbers near Fear/Greed keywords
                pattern = r'\b(\d{1,3})\s*(?:Extreme Fear|Extreme Greed|Fear|Greed|Neutral)'
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if matches:
                    # Filter to values in 0-100 range
                    valid_matches = [int(m) for m in matches if 0 <= int(m) <= 100]
                    if valid_matches:
                        fear_greed_value = float(valid_matches[0])
            
            if fear_greed_value is None or fear_greed_value < 0 or fear_greed_value > 100:
                raise ValueError("Could not extract valid Fear & Greed Index from webpage")
            
            # Classify
            zone, level = self._classify_fear_greed(fear_greed_value)
            
            logger.info(f"Fear & Greed Index fetched from webpage successfully: {fear_greed_value:.0f} ({zone})")
            
            return {
                'value': float(fear_greed_value),
                'zone': zone,
                'level': level,
                'status': 'success',
                'error_message': None,
                'source': 'CNN Webpage',
                'last_updated': datetime.now().isoformat(),
                'data_age_days': 0  # Real-time data from webpage
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch Fear & Greed Index from webpage: {str(e)}")
            return {
                'value': None,
                'zone': 'Unknown',
                'level': -1,
                'status': 'error',
                'error_message': str(e),
                'last_updated': None,
                'data_age_days': None,
                'data_age_warning': None
            }
    
    # ==================== WEB SCRAPING HELPERS ====================
    
    def _scrape_google_finance(self, url: str, indicator_name: str) -> Optional[float]:
        """
        Helper method to scrape price from Google Finance pages.
        
        Args:
            url: Google Finance URL
            indicator_name: Name for logging (e.g., "GVZ", "S&P 500")
            
        Returns:
            Float price value or None if scraping fails
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            response = requests.get(url, headers=headers, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Google Finance structure: Price is in a div with class "YMlKec fxKbKc"
            # Format: "24.03 0.38%+0.090 Today Oct 28, 3:02:01 PM UTC-5"
            # We need the first number before the space
            
            # Method 1: Look for the main price container
            price_div = soup.find('div', class_='YMlKec fxKbKc')
            if price_div:
                price_text = price_div.get_text(strip=True).split()[0]  # Get first element
                price_text = price_text.replace(',', '').replace('$', '')  # Remove thousand separators and dollar sign
                price = float(price_text)
                logger.info(f"✓ Scraped {indicator_name} from Google Finance: {price}")
                return price
            
            # Method 2: Fallback - search for any div containing price-like pattern
            for div in soup.find_all('div'):
                text = div.get_text(strip=True)
                # Match pattern like "3,974.46" or "6890.89" or "$364.38"
                if text and len(text) < 20:  # Reasonable price length
                    try:
                        # Try to extract first numeric value
                        price_str = text.split()[0].replace(',', '').replace('$', '')  # Strip $ and commas
                        if '.' in price_str or price_str.isdigit():
                            price = float(price_str)
                            # Validate reasonable range
                            if 0.01 < price < 100000:  # Reasonable price range
                                logger.info(f"✓ Scraped {indicator_name} from Google Finance (fallback): {price}")
                                return price
                    except (ValueError, IndexError):
                        continue
            
            logger.error(f"Could not parse {indicator_name} price from Google Finance")
            return None
            
        except Exception as e:
            logger.error(f"Failed to scrape {indicator_name} from Google Finance: {e}")
            return None
    
    # ==================== GOLD INDICATORS (Phase 1) ====================
    
    def _fetch_gold_silver_ratio(self) -> Dict[str, Any]:
        """
        Fetch Gold/Silver ratio by calculating from spot prices using GoldPrice.org API.
        
        Uses GoldPrice.org JSON API for real-time spot prices, then calculates ratio.
        Falls back to Yahoo Finance if API fails.
        
        Returns:
            Dictionary with value, status, last_updated, and metadata
        """
        logger.info("Fetching Gold/Silver ratio from GoldPrice.org API...")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Use GoldPrice.org JSON API - provides XAU (gold) and XAG (silver) spot prices
            api_url = 'https://data-asg.goldprice.org/dbXRates/USD'
            response = requests.get(api_url, headers=headers, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract prices from API response
            # API returns: {"items": [{"xauPrice": 3945.67, "xagPrice": 47.64, ...}]}
            if 'items' not in data or not data['items']:
                raise Exception("Invalid API response structure")
            
            item = data['items'][0]
            gold_price = item.get('xauPrice')
            silver_price = item.get('xagPrice')
            
            if not gold_price or not silver_price:
                raise Exception(f"Missing price data: gold={gold_price}, silver={silver_price}")
            
            # Calculate ratio
            ratio = gold_price / silver_price
            
            # Validate reasonable range (typically 50-100, but can be 40-150 in extremes)
            if not (40 < ratio < 150):
                logger.warning(f"Gold/Silver ratio {ratio:.2f} outside expected range 40-150")
            
            # Get timestamp from API if available
            timestamp = data.get('date', datetime.now().strftime("%b %d %Y, %I:%M:%S %p"))
            
            logger.info(f"✓ Gold/Silver Ratio: {ratio:.2f} (Gold: ${gold_price:.2f}/oz, Silver: ${silver_price:.2f}/oz) [{timestamp}]")
            
            return {
                'value': round(ratio, 2),
                'gold_price': round(gold_price, 2),
                'silver_price': round(silver_price, 2),
                'status': 'success',
                'error_message': None,
                'last_updated': datetime.now().isoformat(),
                'data_age_days': 0,
                'data_age_warning': None,
                'source': 'GoldPrice.org API',
                'api_timestamp': timestamp
            }
            
        except Exception as e:
            logger.warning(f"GoldPrice.org API failed: {str(e)}, trying Yahoo Finance fallback...")
            
            # Fallback to Yahoo Finance
            try:
                import yfinance as yf
                
                # Fetch gold: Try GC=F futures first, then GLD ETF
                try:
                    gold_ticker = yf.Ticker('GC=F')
                    gold_data = gold_ticker.history(period='5d')
                    if gold_data.empty:
                        raise Exception("Gold data empty")
                    gold_price = gold_data['Close'].iloc[-1]
                except Exception:
                    gld_ticker = yf.Ticker('GLD')
                    gld_data = gld_ticker.history(period='5d')
                    if gld_data.empty:
                        raise Exception("Both GC=F and GLD failed")
                    gold_price = gld_data['Close'].iloc[-1] * 10
                
                # Fetch silver: Try SI=F futures first, then SLV ETF
                try:
                    silver_ticker = yf.Ticker('SI=F')
                    silver_data = silver_ticker.history(period='5d')
                    if silver_data.empty:
                        raise Exception("Silver data empty")
                    silver_price = silver_data['Close'].iloc[-1]
                except Exception:
                    slv_ticker = yf.Ticker('SLV')
                    slv_data = slv_ticker.history(period='5d')
                    if slv_data.empty:
                        raise Exception("Both SI=F and SLV failed")
                    silver_price = slv_data['Close'].iloc[-1]
                
                ratio = gold_price / silver_price
                
                logger.info(f"✓ Gold/Silver Ratio (Yahoo Finance fallback): {ratio:.2f}")
                
                return {
                    'value': round(ratio, 2),
                    'gold_price': round(gold_price, 2),
                    'silver_price': round(silver_price, 2),
                    'status': 'success',
                    'error_message': None,
                    'last_updated': datetime.now().isoformat(),
                    'data_age_days': 0,
                    'data_age_warning': None,
                    'source': 'Yahoo Finance (fallback)'
                }
                
            except Exception as yf_error:
                logger.error(f"Both GoldPrice.org API and Yahoo Finance failed: {str(yf_error)}")
                return {
                    'value': None,
                    'status': 'error',
                    'error_message': f"All sources failed. GoldPrice.org: {str(e)}, Yahoo: {str(yf_error)}",
                    'last_updated': None,
                    'data_age_days': None,
                    'data_age_warning': 'Data unavailable - check manual_indicators.json'
                }
    
    def _fetch_sp500_gold_ratio(self) -> Dict[str, Any]:
        """
        Fetch S&P 500/Gold ratio using Google Finance web scraping.
        
        Fetches S&P 500 from .INX:INDEXSP and GLD ETF from GLD:NYSEARCA.
        Note: GLD ETF tracks ~1/10 ounce of gold, so we multiply by 10 to get gold oz equivalent.
        Real-time data during market hours.
        
        Returns:
            Dictionary with value, status, last_updated, and metadata
        """
        logger.info("Fetching S&P 500/Gold ratio from Google Finance...")
        
        try:
            # Scrape S&P 500 level
            sp500_level = self._scrape_google_finance(self.GOOGLE_FINANCE_SP500_URL, "S&P 500")
            if not sp500_level:
                raise Exception("Failed to scrape S&P 500 level")
            
            # Scrape GLD ETF price (GLD tracks approximately 1/10 oz of gold)
            gld_price = self._scrape_google_finance(self.GOOGLE_FINANCE_GLD_URL, "GLD ETF")
            if not gld_price:
                raise Exception("Failed to scrape GLD ETF price")
            
            # Calculate gold equivalent price (GLD * 10 ≈ gold oz price)
            gold_equivalent = gld_price * 10
            
            # Calculate ratio
            ratio = sp500_level / gold_equivalent
            
            logger.info(f"✓ S&P 500/Gold ratio: {ratio:.3f} (S&P: {sp500_level:.2f}, Gold equiv: ${gold_equivalent:.2f})")
            
            return {
                'value': round(ratio, 3),
                'sp500_level': round(sp500_level, 2),
                'gold_price': round(gold_equivalent, 2),
                'gld_etf_price': round(gld_price, 2),
                'status': 'success',
                'error_message': None,
                'last_updated': datetime.now().isoformat(),
                'data_age_days': 0,  # Real-time data
                'data_age_warning': None,
                'source': 'Google Finance'
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch S&P 500/Gold ratio: {str(e)}")
            return {
                'value': None,
                'status': 'error',
                'error_message': f"Google Finance scraping failed: {str(e)}",
                'last_updated': None,
                'data_age_days': None,
                'data_age_warning': 'Data unavailable - check manual_indicators.json'
            }
    
    def _fetch_gvz(self) -> Dict[str, Any]:
        """
        Fetch GVZ (Cboe Gold ETF Volatility Index) using Google Finance web scraping.
        
        GVZ measures the market's expectation of 30-day volatility of gold prices
        by looking at options on the SPDR Gold Shares ETF (GLD).
        
        Primary source: Google Finance (stable web scraping)
        Fallback: Cboe API (often returns 403 Forbidden)
        
        Returns:
            Dictionary with value, status, last_updated, and metadata
        """
        logger.info("Fetching GVZ (Gold Volatility Index) from Google Finance...")
        
        try:
            # PRIMARY: Google Finance web scraping
            gvz_value = self._scrape_google_finance(self.GOOGLE_FINANCE_GVZ_URL, "GVZ")
            
            if gvz_value:
                # Validate reasonable range (GVZ typically 10-50, extreme range 5-100)
                if 5 < gvz_value < 100:
                    logger.info(f"✓ GVZ fetched from Google Finance: {gvz_value:.2f}")
                    return {
                        'value': round(gvz_value, 2),
                        'status': 'success',
                        'error_message': None,
                        'last_updated': datetime.now().isoformat(),
                        'data_age_days': 0,  # Real-time data
                        'data_age_warning': None,
                        'source': 'Google Finance'
                    }
                else:
                    logger.warning(f"GVZ value out of reasonable range: {gvz_value}")
            
            raise Exception("Google Finance scraping returned invalid GVZ value")
            
        except Exception as e:
            logger.warning(f"Google Finance failed for GVZ: {str(e)}, trying Cboe API fallback...")
            
            # FALLBACK: Try Cboe JSON API (often blocked with 403)
            try:
                response = requests.get(self.CBOE_GVZ_URL, timeout=self.REQUEST_TIMEOUT)
                response.raise_for_status()
                data = response.json()
                
                # Extract latest GVZ value from chart data
                if 'data' in data and 'chart' in data['data']:
                    chart_data = data['data']['chart']
                    if chart_data and len(chart_data) > 0:
                        latest_point = chart_data[-1]
                        gvz_value = float(latest_point['y'])
                        
                        logger.info(f"✓ GVZ fetched from Cboe API (fallback): {gvz_value:.2f}")
                        
                        return {
                            'value': round(gvz_value, 2),
                            'status': 'success',
                            'error_message': None,
                            'last_updated': datetime.now().isoformat(),
                            'data_age_days': 0,
                            'data_age_warning': None,
                            'source': 'Cboe API (fallback)'
                        }
                
                raise ValueError("Could not extract GVZ from Cboe API response")
                
            except Exception as cboe_error:
                logger.error(f"Cboe API fallback also failed: {str(cboe_error)}")
                
                # Both sources failed, return error
                logger.error("All GVZ data sources failed (Google Finance + Cboe API)")
                return {
                    'value': None,
                    'status': 'error',
                    'error_message': f"All sources failed. Google Finance: {str(e)}, Cboe API: {str(cboe_error)}",
                    'last_updated': None,
                    'data_age_days': None,
                    'data_age_warning': 'Data unavailable - check manual_indicators.json'
                }
    
    # ==================== CRYPTO INDICATORS (Phase 2) ====================
    
    def _fetch_btc_volatility(self) -> Dict[str, Any]:
        """
        Fetch BTC 30-day historical volatility calculated from CoinGecko price data.
        
        Volatility is calculated as the annualized standard deviation of daily returns.
        
        Returns:
            Dictionary with value (volatility %), status, last_updated, and metadata
        """
        logger.info("Calculating BTC 30-day volatility from CoinGecko price history...")
        
        try:
            import numpy as np
            
            response = requests.get(self.COINGECKO_BTC_HISTORY_URL, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract price data (prices is array of [timestamp, price])
            prices = data['prices']
            price_values = [p[1] for p in prices]
            
            # Calculate daily returns
            returns = []
            for i in range(1, len(price_values)):
                daily_return = (price_values[i] - price_values[i-1]) / price_values[i-1]
                returns.append(daily_return)
            
            # Calculate annualized volatility (standard deviation * sqrt(365))
            returns_array = np.array(returns)
            daily_volatility = np.std(returns_array)
            annualized_volatility = daily_volatility * np.sqrt(365) * 100  # Convert to percentage
            
            # Validate reasonable range (crypto volatility can be 5-300%, typical 20-150%)
            if 5 < annualized_volatility < 300:
                logger.info(f"✓ Calculated BTC volatility from CoinGecko: {annualized_volatility:.2f}% (from {len(returns)} daily returns)")
                return {
                    'value': round(annualized_volatility, 2),
                    'status': 'success',
                    'error_message': None,
                    'last_updated': datetime.now().isoformat(),
                    'data_age_days': 0,
                    'data_age_warning': None,
                    'source': 'CoinGecko API (calculated)',
                    'calculation_method': '30-day annualized volatility'
                }
            else:
                logger.warning(f"BTC volatility out of reasonable range: {annualized_volatility}%")
                raise ValueError(f"Calculated volatility out of range: {annualized_volatility}%")
            
        except Exception as e:
            logger.error(f"BTC volatility calculation failed: {str(e)}")
            return {
                'value': None,
                'status': 'error',
                'error_message': f"Calculation failed: {str(e)}",
                'last_updated': None,
                'data_age_days': None,
                'data_age_warning': 'Data unavailable - check manual_indicators.json',
                'source': None
            }
    
    def _fetch_eth_volatility(self) -> Dict[str, Any]:
        """
        Fetch ETH 30-day historical volatility calculated from CoinGecko price data.
        
        Volatility is calculated as the annualized standard deviation of daily returns.
        
        Returns:
            Dictionary with value (volatility %), status, last_updated, and metadata
        """
        logger.info("Calculating ETH 30-day volatility from CoinGecko price history...")
        
        try:
            import numpy as np
            
            response = requests.get(self.COINGECKO_ETH_HISTORY_URL, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract price data (prices is array of [timestamp, price])
            prices = data['prices']
            price_values = [p[1] for p in prices]
            
            # Calculate daily returns
            returns = []
            for i in range(1, len(price_values)):
                daily_return = (price_values[i] - price_values[i-1]) / price_values[i-1]
                returns.append(daily_return)
            
            # Calculate annualized volatility (standard deviation * sqrt(365))
            returns_array = np.array(returns)
            daily_volatility = np.std(returns_array)
            annualized_volatility = daily_volatility * np.sqrt(365) * 100  # Convert to percentage
            
            # Validate reasonable range (ETH volatility can be 5-400%, typical 30-200%)
            if 5 < annualized_volatility < 400:
                logger.info(f"✓ Calculated ETH volatility from CoinGecko: {annualized_volatility:.2f}% (from {len(returns)} daily returns)")
                return {
                    'value': round(annualized_volatility, 2),
                    'status': 'success',
                    'error_message': None,
                    'last_updated': datetime.now().isoformat(),
                    'data_age_days': 0,
                    'data_age_warning': None,
                    'source': 'CoinGecko API (calculated)',
                    'calculation_method': '30-day annualized volatility'
                }
            else:
                logger.warning(f"ETH volatility out of reasonable range: {annualized_volatility}%")
                raise ValueError(f"Calculated volatility out of range: {annualized_volatility}%")
            
        except Exception as e:
            logger.error(f"ETH volatility calculation failed: {str(e)}")
            return {
                'value': None,
                'status': 'error',
                'error_message': f"Calculation failed: {str(e)}",
                'last_updated': None,
                'data_age_days': None,
                'data_age_warning': 'Data unavailable - check manual_indicators.json',
                'source': None
            }
    
    def _fetch_btc_eth_ratio(self) -> Dict[str, Any]:
        """
        Fetch BTC/ETH price ratio from CoinGecko API.
        
        This ratio indicates relative strength between the two major cryptocurrencies.
        High ratio = BTC outperforming ETH (flight to safety in crypto)
        Low ratio = ETH outperforming BTC (risk-on crypto sentiment)
        
        Returns:
            Dictionary with value, status, last_updated, and metadata
        """
        logger.info("Fetching BTC/ETH ratio from CoinGecko API...")
        
        try:
            # Fetch both prices in one call would be more efficient, but CoinGecko API structure
            # makes it easier to do separate calls for clarity
            
            # Fetch BTC price
            btc_response = requests.get(self.COINGECKO_BTC_URL, timeout=self.REQUEST_TIMEOUT)
            btc_response.raise_for_status()
            btc_data = btc_response.json()
            btc_price = btc_data['bitcoin']['usd']
            
            # Small delay to avoid rate limiting
            sleep(0.2)
            
            # Fetch ETH price
            eth_response = requests.get(self.COINGECKO_ETH_URL, timeout=self.REQUEST_TIMEOUT)
            eth_response.raise_for_status()
            eth_data = eth_response.json()
            eth_price = eth_data['ethereum']['usd']
            
            # Calculate ratio
            btc_eth_ratio = btc_price / eth_price
            
            # Validate reasonable range (historically 10-50, extreme 5-100)
            if 5 < btc_eth_ratio < 100:
                logger.info(f"✓ BTC/ETH ratio from CoinGecko: {btc_eth_ratio:.2f} (BTC: ${btc_price:,.0f}, ETH: ${eth_price:,.0f})")
                return {
                    'value': round(btc_eth_ratio, 2),
                    'status': 'success',
                    'error_message': None,
                    'last_updated': datetime.now().isoformat(),
                    'data_age_days': 0,
                    'data_age_warning': None,
                    'source': 'CoinGecko API',
                    'btc_price': btc_price,
                    'eth_price': eth_price
                }
            else:
                logger.warning(f"BTC/ETH ratio out of reasonable range: {btc_eth_ratio}")
                raise ValueError(f"BTC/ETH ratio out of range: {btc_eth_ratio}")
            
        except Exception as e:
            logger.error(f"BTC/ETH ratio fetch failed: {str(e)}")
            return {
                'value': None,
                'status': 'error',
                'error_message': f"CoinGecko API failed: {str(e)}",
                'last_updated': None,
                'data_age_days': None,
                'data_age_warning': 'Data unavailable - check manual_indicators.json',
                'source': None
            }
    
    def _fetch_btc_dominance(self) -> Dict[str, Any]:
        """
        Fetch BTC dominance (% of total crypto market cap) from CoinGecko API.
        
        BTC dominance indicates risk sentiment in crypto markets:
        High dominance (>50%) = Flight to safety (BTC as crypto reserve asset)
        Low dominance (<40%) = Risk-on sentiment (altcoin season)
        
        Returns:
            Dictionary with value, status, last_updated, and metadata
        """
        logger.info("Fetching BTC dominance from CoinGecko API...")
        
        try:
            response = requests.get(self.COINGECKO_GLOBAL_URL, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract BTC dominance percentage
            btc_dominance = data['data']['market_cap_percentage']['btc']
            
            # Validate reasonable range (historically 35-70%, extreme 20-80%)
            if 20 < btc_dominance < 80:
                logger.info(f"✓ BTC dominance from CoinGecko: {btc_dominance:.2f}%")
                return {
                    'value': round(btc_dominance, 2),
                    'status': 'success',
                    'error_message': None,
                    'last_updated': datetime.now().isoformat(),
                    'data_age_days': 0,
                    'data_age_warning': None,
                    'source': 'CoinGecko API'
                }
            else:
                logger.warning(f"BTC dominance out of reasonable range: {btc_dominance}%")
                raise ValueError(f"BTC dominance out of range: {btc_dominance}%")
            
        except Exception as e:
            logger.error(f"BTC dominance fetch failed: {str(e)}")
            return {
                'value': None,
                'status': 'error',
                'error_message': f"CoinGecko API failed: {str(e)}",
                'last_updated': None,
                'data_age_days': None,
                'data_age_warning': 'Data unavailable - check manual_indicators.json',
                'source': None
            }
    
    def _fetch_btc_qqq_ratio(self) -> Dict[str, Any]:
        """
        Fetch BTC/QQQ ratio to measure crypto vs tech stocks relative performance.
        
        This ratio helps distinguish between:
        - Crypto-specific trends vs general tech/risk appetite
        - Risk-on sentiment (high ratio) vs risk-off (low ratio)
        
        Interpretation:
        - High (>0.30): BTC significantly outperforming tech stocks (crypto market hot)
        - Normal (0.15-0.30): Balanced relative performance
        - Low (<0.15): BTC underperforming tech stocks (crypto market cold)
        
        Data Sources (with fallback):
        1. Yahoo Finance (yfinance) - primary
        2. Google Finance (web scraping) - fallback
        
        Returns:
            Dictionary with value, zone, interpretation, btc_price, qqq_price, status
        """
        logger.info("Calculating BTC/QQQ ratio...")
        
        btc_price = None
        qqq_price = None
        source = None
        
        # Try Yahoo Finance first (primary source)
        try:
            import yfinance as yf
            
            # Fetch BTC-USD price
            btc = yf.Ticker('BTC-USD')
            btc_data = btc.history(period='5d')
            
            if not btc_data.empty:
                btc_price = float(btc_data['Close'].iloc[-1])
            
            # Fetch QQQ price
            qqq = yf.Ticker('QQQ')
            qqq_data = qqq.history(period='5d')
            
            if not qqq_data.empty:
                qqq_price = float(qqq_data['Close'].iloc[-1])
            
            if btc_price and qqq_price:
                source = 'Yahoo Finance (yfinance)'
                logger.info(f"✓ BTC/QQQ prices from Yahoo Finance - BTC: ${btc_price:,.0f}, QQQ: ${qqq_price:.2f}")
            else:
                raise ValueError("Incomplete data from Yahoo Finance")
                
        except Exception as e:
            logger.warning(f"Yahoo Finance failed for BTC/QQQ: {str(e)}, trying Google Finance fallback...")
            
            # Try Google Finance fallback
            try:
                # Get BTC price from CoinGecko (already have this method)
                btc_result = self._fetch_btc_price_coingecko()
                if btc_result.get('status') == 'success':
                    btc_price = btc_result.get('price')
                
                # Scrape QQQ from Google Finance
                qqq_price = self._scrape_google_finance_price('QQQ', 'NASDAQ')
                
                if btc_price and qqq_price:
                    source = 'Google Finance (scraping) + CoinGecko'
                    logger.info(f"✓ BTC/QQQ prices from Google Finance fallback - BTC: ${btc_price:,.0f}, QQQ: ${qqq_price:.2f}")
                else:
                    raise ValueError("Incomplete data from Google Finance fallback")
                    
            except Exception as e2:
                logger.error(f"Both Yahoo Finance and Google Finance failed for BTC/QQQ: {str(e2)}")
                return {
                    'value': None,
                    'zone': 'Unknown',
                    'zone_level': 0,
                    'interpretation': f"Data unavailable from all sources: {str(e2)}",
                    'status': 'error',
                    'error_message': str(e2),
                    'last_updated': None,
                    'data_age_days': None,
                    'source': None
                }
        
        # Calculate ratio
        ratio = btc_price / qqq_price
        
        # Classify zone
        if ratio > 0.30:
            zone = "Hot"
            zone_level = 3
            interpretation = "BTC significantly outperforming tech stocks (risk-on crypto)"
        elif ratio > 0.15:
            zone = "Normal"
            zone_level = 2
            interpretation = "Balanced relative performance"
        else:
            zone = "Cold"
            zone_level = 1
            interpretation = "BTC underperforming tech stocks (risk-off crypto)"
        
        logger.info(f"✓ BTC/QQQ ratio: {ratio:.3f} ({zone}) - BTC: ${btc_price:,.0f}, QQQ: ${qqq_price:.2f}")
        
        return {
            'value': round(ratio, 3),
            'btc_price': round(btc_price, 2),
            'qqq_price': round(qqq_price, 2),
            'zone': zone,
            'zone_level': zone_level,
            'interpretation': interpretation,
            'status': 'success',
            'error_message': None,
            'last_updated': datetime.now().isoformat(),
            'data_age_days': 0,
            'source': source
        }
    
    def _fetch_crypto_fear_greed(self) -> Dict[str, Any]:
        """
        Fetch Crypto Fear & Greed Index from Alternative.me API.
        
        This contrarian indicator measures crypto market sentiment:
        - 0-24: Extreme Fear (potential buying opportunity)
        - 25-44: Fear (caution)
        - 45-55: Neutral
        - 56-75: Greed (consider taking profits)
        - 76-100: Extreme Greed (high risk, potential bubble)
        
        API: https://api.alternative.me/fng/
        Returns last 7 days, we use the most recent value.
        
        Returns:
            Dictionary with value, zone, interpretation, status
        """
        logger.info("Fetching Crypto Fear & Greed Index from Alternative.me API...")
        
        try:
            # Alternative.me Free API - no auth required
            url = "https://api.alternative.me/fng/?limit=1"
            response = requests.get(url, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' not in data or len(data['data']) == 0:
                raise ValueError("No data in API response")
            
            # Extract most recent value
            latest = data['data'][0]
            value = int(latest['value'])
            value_classification = latest['value_classification']  # API provides classification
            timestamp = int(latest['timestamp'])
            
            # Our classification (may differ from API's)
            if value < 25:
                zone = "Extreme Fear"
                zone_level = 1
                interpretation = "Extreme fear - potential buying opportunity (contrarian)"
            elif value < 45:
                zone = "Fear"
                zone_level = 2
                interpretation = "Market fear - caution advised"
            elif value < 56:
                zone = "Neutral"
                zone_level = 3
                interpretation = "Neutral sentiment - balanced market"
            elif value < 76:
                zone = "Greed"
                zone_level = 4
                interpretation = "Market greed - consider taking profits"
            else:
                zone = "Extreme Greed"
                zone_level = 5
                interpretation = "Extreme greed - high risk, potential bubble"
            
            # Calculate data age
            data_age_days = (datetime.now().timestamp() - timestamp) / 86400
            
            logger.info(f"✓ Crypto Fear & Greed Index: {value} ({zone})")
            
            return {
                'value': value,
                'zone': zone,
                'zone_level': zone_level,
                'interpretation': interpretation,
                'api_classification': value_classification,  # Keep API's classification for reference
                'status': 'success',
                'error_message': None,
                'last_updated': datetime.fromtimestamp(timestamp).isoformat(),
                'data_age_days': round(data_age_days, 1),
                'data_age_warning': 'Data may be stale' if data_age_days > 1 else None,
                'source': 'Alternative.me API'
            }
            
        except Exception as e:
            logger.error(f"Crypto Fear & Greed Index fetch failed: {str(e)}")
            return {
                'value': None,
                'zone': 'Unknown',
                'zone_level': 0,
                'interpretation': f"Data unavailable: {str(e)}",
                'status': 'error',
                'error_message': str(e),
                'last_updated': None,
                'data_age_days': None,
                'source': None
            }
    
    # ==================== END CRYPTO INDICATORS ====================
    
    # ==================== PHASE 3: WEIGHTED SCORING SYSTEM ====================
    
    def _score_btc_volatility(self, volatility_pct: float) -> float:
        """
        Score BTC volatility on -2 to +2 scale (contrarian).
        High volatility = fear/opportunity (negative score = buy signal)
        Low volatility = complacency (positive score = sell signal)
        
        Args:
            volatility_pct: Annualized volatility percentage (0-150+)
        
        Returns:
            Score from -2 (extreme volatility, buy) to +2 (extreme complacency, sell)
        """
        if volatility_pct >= 80:
            return -2.0  # Extreme fear, contrarian buy
        elif volatility_pct >= 60:
            return -1.0  # High vol, buy
        elif volatility_pct >= 25:
            return 0.0   # Normal range, hold
        elif volatility_pct >= 20:
            return 1.0   # Low vol, complacency, sell
        else:
            return 2.0   # Extreme complacency, strong sell
    
    def _score_eth_volatility(self, volatility_pct: float) -> float:
        """
        Score ETH volatility on -2 to +2 scale (contrarian).
        ETH typically 1.2-1.5x more volatile than BTC.
        
        Args:
            volatility_pct: Annualized volatility percentage (0-200+)
        
        Returns:
            Score from -2 (extreme volatility, buy) to +2 (extreme complacency, sell)
        """
        if volatility_pct >= 100:
            return -2.0  # Extreme fear, contrarian buy
        elif volatility_pct >= 75:
            return -1.0  # High vol, buy
        elif volatility_pct >= 30:
            return 0.0   # Normal range, hold
        elif volatility_pct >= 25:
            return 1.0   # Low vol, complacency, sell
        else:
            return 2.0   # Extreme complacency, strong sell
    
    def _score_btc_eth_ratio(self, ratio: float) -> float:
        """
        Score BTC/ETH ratio on -2 to +2 scale.
        Lower ratio = BTC cheap vs ETH (negative score = buy BTC signal)
        Higher ratio = BTC expensive vs ETH (positive score = sell BTC signal)
        
        Args:
            ratio: BTC price / ETH price (typical range 10-35)
        
        Returns:
            Score from -2 (BTC very cheap) to +2 (BTC very expensive)
        """
        if ratio < 12:
            return -2.0  # BTC extremely cheap
        elif ratio < 15:
            return -1.0  # BTC moderately cheap
        elif ratio < 22:
            return 0.0   # Normal range
        elif ratio < 25:
            return 1.0   # BTC moderately expensive
        else:
            return 2.0   # BTC extremely expensive
    
    def _score_btc_dominance(self, dominance_pct: float) -> float:
        """
        Score BTC dominance on -2 to +2 scale.
        Low dominance = altcoin season, BTC undervalued (negative score = buy BTC)
        High dominance = BTC flight to safety, BTC overvalued (positive score = sell BTC)
        
        Args:
            dominance_pct: BTC market cap % of total crypto (typical range 30-70%)
        
        Returns:
            Score from -2 (extreme altcoin season) to +2 (extreme BTC dominance)
        """
        if dominance_pct < 35:
            return -2.0  # Extreme altcoin season, buy BTC
        elif dominance_pct < 42:
            return -1.0  # Altcoin season, buy BTC
        elif dominance_pct < 55:
            return 0.0   # Normal range
        elif dominance_pct < 60:
            return 1.0   # High BTC dominance, sell BTC
        else:
            return 2.0   # Extreme BTC dominance, strong sell BTC
    
    def _score_btc_qqq_ratio(self, ratio: float) -> float:
        """
        Score BTC/QQQ ratio on -2 to +2 scale.
        Lower ratio = crypto weak vs tech (negative score = buy signal)
        Higher ratio = crypto strong vs tech (positive score = sell signal)
        
        Args:
            ratio: BTC price / QQQ price (typical range 0.15-0.30)
        
        Returns:
            Score from -2 (crypto very weak) to +2 (crypto very strong)
        """
        if ratio < 0.12:
            return -2.0  # Crypto extremely weak, buy
        elif ratio < 0.15:
            return -1.0  # Crypto moderately weak, buy
        elif ratio <= 0.30:
            return 0.0   # Normal range
        elif ratio <= 0.35:
            return 1.0   # Crypto moderately strong, sell
        else:
            return 2.0   # Crypto extremely strong, strong sell
    
    def _score_crypto_fear_greed(self, value: int) -> float:
        """
        Score Crypto Fear & Greed Index on -2 to +2 scale (contrarian).
        Lower value = fear/buy opportunity (negative score)
        Higher value = greed/sell signal (positive score)
        
        Args:
            value: Fear & Greed Index 0-100
        
        Returns:
            Score from -2 (extreme fear, buy) to +2 (extreme greed, sell)
        """
        if value < 25:
            return -2.0  # Extreme fear, contrarian buy
        elif value < 45:
            return -1.0  # Fear, buy
        elif value <= 55:
            return 0.0   # Neutral, hold
        elif value <= 75:
            return 1.0   # Greed, sell
        else:
            return 2.0   # Extreme greed, contrarian strong sell
    
    def calculate_crypto_weighted_score(
        self,
        btc_vol_result: Dict[str, Any],
        eth_vol_result: Dict[str, Any],
        btc_eth_ratio_result: Dict[str, Any],
        btc_dominance_result: Dict[str, Any],
        btc_qqq_ratio_result: Dict[str, Any],
        crypto_fng_result: Dict[str, Any],
        asset_type: str = 'BTC'
    ) -> Dict[str, Any]:
        """
        Calculate weighted total score for crypto asset (BTC or ETH) using Phase 3 methodology.
        
        Each indicator produces -2 to +2 score, multiplied by weight from config.
        Total weighted score ranges from -10 to +10, mapped to 5-tier recommendations.
        
        For ETH, btc_eth_ratio and btc_dominance scores are INVERTED:
        - High BTC/ETH ratio: bearish for BTC (expensive) but bullish for ETH (cheap)
        - High BTC dominance: bullish for BTC but bearish for ETH (altcoin weakness)
        
        Args:
            btc_vol_result: BTC volatility data with 'value' key
            eth_vol_result: ETH volatility data with 'value' key
            btc_eth_ratio_result: BTC/ETH ratio data with 'value' key
            btc_dominance_result: BTC dominance data with 'value' key
            btc_qqq_ratio_result: BTC/QQQ ratio data with 'value' key
            crypto_fng_result: Crypto Fear & Greed data with 'value' key
            asset_type: 'BTC' or 'ETH' - determines whether to invert certain scores
        
        Returns:
            Dictionary with:
            - total_score: float (-10 to +10)
            - recommendation: str (Strong Buy/Buy/Hold/Sell/Strong Sell)
            - breakdown: Dict[str, Dict] - per-indicator score, weight, weighted score
            - status: str
            - error_message: Optional[str]
        """
        try:
            # Load config file
            config_path = Path('config/alt_assets_indicators.yaml')
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                full_config = yaml.safe_load(f)
            
            config = full_config.get('crypto_indicators', {})
            weights = config.get('weights', {
                'btc_volatility': 0.8,
                'eth_volatility': 0.8,
                'btc_eth_ratio': 0.7,
                'btc_dominance': 0.9,
                'btc_qqq_ratio': 1.0,
                'crypto_fear_greed': 1.2
            })
            
            # Calculate individual scores
            breakdown = {}
            total_weighted_score = 0.0
            missing_indicators = []
            
            # BTC Volatility
            if btc_vol_result.get('status') == 'success' and btc_vol_result.get('value') is not None:
                score = self._score_btc_volatility(btc_vol_result['value'])
                weight = weights['btc_volatility']
                weighted = score * weight
                breakdown['btc_volatility'] = {
                    'value': btc_vol_result['value'],
                    'score': score,
                    'weight': weight,
                    'weighted_score': weighted
                }
                total_weighted_score += weighted
            else:
                missing_indicators.append('BTC Volatility')
            
            # ETH Volatility
            if eth_vol_result.get('status') == 'success' and eth_vol_result.get('value') is not None:
                score = self._score_eth_volatility(eth_vol_result['value'])
                weight = weights['eth_volatility']
                weighted = score * weight
                breakdown['eth_volatility'] = {
                    'value': eth_vol_result['value'],
                    'score': score,
                    'weight': weight,
                    'weighted_score': weighted
                }
                total_weighted_score += weighted
            else:
                missing_indicators.append('ETH Volatility')
            
            # BTC/ETH Ratio
            if btc_eth_ratio_result.get('status') == 'success' and btc_eth_ratio_result.get('value') is not None:
                score = self._score_btc_eth_ratio(btc_eth_ratio_result['value'])
                # INVERT for ETH: High ratio = BTC expensive (bearish BTC, bullish ETH)
                if asset_type == 'ETH':
                    score = -score
                weight = weights['btc_eth_ratio']
                weighted = score * weight
                breakdown['btc_eth_ratio'] = {
                    'value': btc_eth_ratio_result['value'],
                    'score': score,
                    'weight': weight,
                    'weighted_score': weighted
                }
                total_weighted_score += weighted
            else:
                missing_indicators.append('BTC/ETH Ratio')
            
            # BTC Dominance
            if btc_dominance_result.get('status') == 'success' and btc_dominance_result.get('value') is not None:
                score = self._score_btc_dominance(btc_dominance_result['value'])
                # INVERT for ETH: High BTC dominance = bearish for altcoins (ETH)
                if asset_type == 'ETH':
                    score = -score
                weight = weights['btc_dominance']
                weighted = score * weight
                breakdown['btc_dominance'] = {
                    'value': btc_dominance_result['value'],
                    'score': score,
                    'weight': weight,
                    'weighted_score': weighted
                }
                total_weighted_score += weighted
            else:
                missing_indicators.append('BTC Dominance')
            
            # BTC/QQQ Ratio
            if btc_qqq_ratio_result.get('status') == 'success' and btc_qqq_ratio_result.get('value') is not None:
                score = self._score_btc_qqq_ratio(btc_qqq_ratio_result['value'])
                weight = weights['btc_qqq_ratio']
                weighted = score * weight
                breakdown['btc_qqq_ratio'] = {
                    'value': btc_qqq_ratio_result['value'],
                    'score': score,
                    'weight': weight,
                    'weighted_score': weighted
                }
                total_weighted_score += weighted
            else:
                missing_indicators.append('BTC/QQQ Ratio')
            
            # Crypto Fear & Greed
            if crypto_fng_result.get('status') == 'success' and crypto_fng_result.get('value') is not None:
                score = self._score_crypto_fear_greed(crypto_fng_result['value'])
                weight = weights['crypto_fear_greed']
                weighted = score * weight
                breakdown['crypto_fear_greed'] = {
                    'value': crypto_fng_result['value'],
                    'score': score,
                    'weight': weight,
                    'weighted_score': weighted
                }
                total_weighted_score += weighted
            else:
                missing_indicators.append('Crypto Fear & Greed')
            
            # Clamp total score to -10 to +10 range BEFORE mapping to recommendation
            total_weighted_score = max(-10.0, min(10.0, total_weighted_score))
            
            # Map total score to recommendation
            scoring_config = config.get('scoring', {}).get('score_to_recommendation', {})
            recommendation = self._map_score_to_recommendation(total_weighted_score, scoring_config)
            
            result = {
                'total_score': round(total_weighted_score, 2),
                'recommendation': recommendation,
                'breakdown': breakdown,
                'missing_indicators': missing_indicators,
                'status': 'success',
                'error_message': None
            }
            
            logger.info(f"✓ {asset_type} Weighted Score: {result['total_score']}/10 → {recommendation}")
            if missing_indicators:
                logger.warning(f"Missing indicators: {', '.join(missing_indicators)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating crypto weighted score: {str(e)}")
            return {
                'total_score': 0.0,
                'recommendation': 'Unknown',
                'breakdown': {},
                'missing_indicators': [],
                'status': 'error',
                'error_message': str(e)
            }
    
    # ==================== GOLD WEIGHTED SCORING HELPERS ====================
    
    def _score_gvz(self, gvz: float) -> float:
        """
        Score GVZ (Gold Volatility Index) from -2 to +2.
        Range: 5-50 (typical range, can go higher)
        
        Contrarian interpretation:
        - Very low volatility (5-10): Complacency → Sell (-2)
        - Low volatility (10-15): Calm → Slight Sell (-1)
        - Normal volatility (15-25): Neutral → Hold (0)
        - High volatility (25-35): Fear rising → Slight Buy (+1)
        - Very high volatility (35-50+): Extreme fear → Strong Buy (+2)
        
        Gold often benefits from market stress/volatility.
        """
        if gvz is None or np.isnan(gvz):
            return 0.0
        
        if gvz <= 10:
            return -2.0  # Very low volatility, complacency
        elif gvz <= 15:
            return -1.0  # Low volatility
        elif gvz <= 25:
            return 0.0   # Normal volatility
        elif gvz <= 35:
            return 1.0   # High volatility, fear
        else:
            return 2.0   # Extreme volatility, strong fear
    
    def _score_gold_silver_ratio(self, ratio: float) -> float:
        """
        Score Gold/Silver ratio from -2 to +2.
        Range: 40-100 (typical range)
        
        Interpretation:
        - Very low ratio (40-55): Silver expensive/gold cheap → Strong Buy gold (+2)
        - Low ratio (55-65): Balanced toward silver → Slight Buy (+1)
        - Normal ratio (65-75): Neutral → Hold (0)
        - High ratio (75-85): Gold expensive/silver cheap → Slight Sell (-1)
        - Very high ratio (85-100+): Gold very expensive → Strong Sell (-2)
        
        Lower ratio = gold is relatively cheaper = buying opportunity.
        """
        if ratio is None or np.isnan(ratio):
            return 0.0
        
        if ratio <= 55:
            return 2.0   # Gold cheap relative to silver
        elif ratio <= 65:
            return 1.0   # Gold slightly cheap
        elif ratio <= 75:
            return 0.0   # Normal/neutral
        elif ratio <= 85:
            return -1.0  # Gold expensive
        else:
            return -2.0  # Gold very expensive
    
    def _score_sp500_gold_ratio(self, ratio: float) -> float:
        """
        Score S&P500/Gold ratio from -2 to +2.
        Range: 0.5-3.5 (typical range)
        
        Interpretation:
        - Very low ratio (0.5-1.0): Stocks cheap/gold expensive → Sell gold (-2)
        - Low ratio (1.0-1.5): Balanced toward stocks → Slight Sell (-1)
        - Normal ratio (1.5-2.5): Neutral → Hold (0)
        - High ratio (2.5-3.0): Stocks expensive/gold cheap → Slight Buy (+1)
        - Very high ratio (3.0-3.5+): Stocks very expensive → Strong Buy gold (+2)
        
        Higher ratio = stocks expensive relative to gold = gold buying opportunity.
        """
        if ratio is None or np.isnan(ratio):
            return 0.0
        
        if ratio <= 1.0:
            return -2.0  # Gold expensive relative to stocks
        elif ratio <= 1.5:
            return -1.0  # Gold slightly expensive
        elif ratio <= 2.5:
            return 0.0   # Normal/neutral
        elif ratio <= 3.0:
            return 1.0   # Gold attractive
        else:
            return 2.0   # Gold very attractive
    
    def calculate_gold_weighted_score(self) -> Dict[str, Any]:
        """
        Calculate weighted gold investment score using Phase 3 methodology.
        
        Mirrors crypto weighted scoring approach:
        - Load config weights for GVZ, Gold/Silver ratio, S&P/Gold ratio
        - Score each indicator from -2 to +2
        - Apply weights and sum to get total score (-10 to +10)
        - Map to 5-tier recommendation system
        
        Returns:
            dict: {
                'total_score': float (-10 to +10),
                'recommendation': str (Strong Buy/Buy/Hold/Sell/Strong Sell),
                'breakdown': dict of individual indicator scores,
                'missing_indicators': list of unavailable indicators,
                'status': str (success/warning/error),
                'error_message': str or None
            }
        """
        try:
            # Load config
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'config', 'alt_assets_indicators.yaml'
            )
            
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            gold_config = config.get('gold_indicators', {})
            weights = gold_config.get('weights', {
                'gvz': 1.2,
                'gold_silver_ratio': 1.0,
                'sp500_gold_ratio': 0.8
            })
            scoring_config = gold_config.get('weighted_scoring', {})
            
            # Get indicator data
            gold_analysis = self.get_gold_analysis()
            indicators = gold_analysis.get('indicators', {})
            
            # Extract values from nested indicator structure
            gvz = indicators.get('gvz', {}).get('value')
            gold_silver_ratio = indicators.get('gold_silver_ratio', {}).get('value')
            sp500_gold_ratio = indicators.get('sp500_gold_ratio', {}).get('value')
            
            # Calculate individual scores
            breakdown = {}
            missing_indicators = []
            total_score = 0.0
            
            # GVZ score
            if gvz is not None:
                gvz_score = self._score_gvz(gvz)
                weighted_gvz = gvz_score * weights.get('gvz', 1.2)
                breakdown['gvz'] = {
                    'raw_value': gvz,
                    'base_score': gvz_score,
                    'weight': weights.get('gvz', 1.2),
                    'weighted_score': weighted_gvz
                }
                total_score += weighted_gvz
            else:
                missing_indicators.append('gvz')
            
            # Gold/Silver ratio score
            if gold_silver_ratio is not None:
                ratio_score = self._score_gold_silver_ratio(gold_silver_ratio)
                weighted_ratio = ratio_score * weights.get('gold_silver_ratio', 1.0)
                breakdown['gold_silver_ratio'] = {
                    'raw_value': gold_silver_ratio,
                    'base_score': ratio_score,
                    'weight': weights.get('gold_silver_ratio', 1.0),
                    'weighted_score': weighted_ratio
                }
                total_score += weighted_ratio
            else:
                missing_indicators.append('gold_silver_ratio')
            
            # S&P500/Gold ratio score
            if sp500_gold_ratio is not None:
                sp_ratio_score = self._score_sp500_gold_ratio(sp500_gold_ratio)
                weighted_sp_ratio = sp_ratio_score * weights.get('sp500_gold_ratio', 0.8)
                breakdown['sp500_gold_ratio'] = {
                    'raw_value': sp500_gold_ratio,
                    'base_score': sp_ratio_score,
                    'weight': weights.get('sp500_gold_ratio', 0.8),
                    'weighted_score': weighted_sp_ratio
                }
                total_score += weighted_sp_ratio
            else:
                missing_indicators.append('sp500_gold_ratio')
            
            # Clamp total score to -10 to +10 range
            total_score = max(-10.0, min(10.0, total_score))
            
            # Map to recommendation
            score_to_rec = scoring_config.get('score_to_recommendation', {})
            recommendation = 'Hold'  # default
            
            if total_score <= score_to_rec.get('strong_buy', {}).get('max_score', -6):
                recommendation = 'Strong Buy'
            elif total_score <= score_to_rec.get('buy', {}).get('max_score', -3):
                recommendation = 'Buy'
            elif total_score <= score_to_rec.get('hold', {}).get('max_score', 2.99):
                recommendation = 'Hold'
            elif total_score <= score_to_rec.get('sell', {}).get('max_score', 5.99):
                recommendation = 'Sell'
            else:
                recommendation = 'Strong Sell'
            
            # Determine status
            status = 'success'
            error_message = None
            
            if len(missing_indicators) >= 2:
                status = 'warning'
                error_message = f"Multiple indicators missing: {', '.join(missing_indicators)}"
            elif len(missing_indicators) == 1:
                status = 'warning'
                error_message = f"One indicator missing: {missing_indicators[0]}"
            
            result = {
                'total_score': round(total_score, 2),
                'recommendation': recommendation,
                'breakdown': breakdown,
                'missing_indicators': missing_indicators,
                'status': status,
                'error_message': error_message
            }
            
            logger.info(f"Gold weighted score calculated: {total_score:.2f} → {recommendation}")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating gold weighted score: {str(e)}")
            return {
                'total_score': 0.0,
                'recommendation': 'Unknown',
                'breakdown': {},
                'missing_indicators': [],
                'status': 'error',
                'error_message': str(e)
            }
    
    # ==================== END GOLD WEIGHTED SCORING ====================
    
    def _map_score_to_recommendation(self, score: float, scoring_config: Dict) -> str:
        """
        Map weighted total score to recommendation tier.
        
        Uses strict ordering: check from most extreme to least extreme.
        Boundaries are inclusive on both ends per config design.
        
        Args:
            score: Total weighted score (-10 to +10)
            scoring_config: Dict with recommendation thresholds
        
        Returns:
            Recommendation string (Strong Buy/Buy/Hold/Sell/Strong Sell)
        """
        # Default thresholds if config missing
        if not scoring_config:
            if score < -6:
                return "Strong Buy"
            elif score < -3:
                return "Buy"
            elif score < 3:
                return "Hold"
            elif score < 6:
                return "Sell"
            else:
                return "Strong Sell"
        
        # Manual ordered checking for clarity (config dict order isn't guaranteed)
        # Check in specific order to handle overlapping boundaries
        
        # Strong Buy: -10 to -6 (inclusive)
        if 'strong_buy' in scoring_config:
            cfg = scoring_config['strong_buy']
            if cfg['min_score'] <= score <= cfg['max_score']:
                return 'Strong Buy'
        
        # Buy: -6 to -3 (inclusive)  
        if 'buy' in scoring_config:
            cfg = scoring_config['buy']
            if cfg['min_score'] <= score <= cfg['max_score']:
                return 'Buy'
        
        # Hold: -3 to +3 (inclusive)
        if 'hold' in scoring_config:
            cfg = scoring_config['hold']
            if cfg['min_score'] <= score <= cfg['max_score']:
                return 'Hold'
        
        # Sell: +3 to +6 (inclusive)
        if 'sell' in scoring_config:
            cfg = scoring_config['sell']
            if cfg['min_score'] <= score <= cfg['max_score']:
                return 'Sell'
        
        # Strong Sell: +6 to +10 (inclusive)
        if 'strong_sell' in scoring_config:
            cfg = scoring_config['strong_sell']
            if cfg['min_score'] <= score <= cfg['max_score']:
                return 'Strong Sell'
        
        return "Hold"  # Fallback
    
    # ==================== END PHASE 3 WEIGHTED SCORING ====================
    
    def _calculate_crypto_market_sentiment(
        self,
        btc_qqq_ratio_result: Dict[str, Any],
        crypto_fng_result: Dict[str, Any],
        btc_vol_result: Dict[str, Any],
        eth_vol_result: Dict[str, Any],
        btc_eth_ratio_result: Dict[str, Any],
        btc_dominance_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate overall crypto market sentiment using Phase 3 weighted scoring.
        
        Phase 3 Enhancement:
        - Uses weighted scoring system with all 6 indicators
        - Each indicator produces -2 to +2 score × weight
        - Total weighted score -10 to +10 → 5-tier recommendations
        - Preserves Phase 2 qualitative analysis for context
        
        Args:
            btc_qqq_ratio_result: Result from _fetch_btc_qqq_ratio()
            crypto_fng_result: Result from _fetch_crypto_fear_greed()
            btc_vol_result: Result from _fetch_btc_volatility()
            eth_vol_result: Result from _fetch_eth_volatility()
            btc_eth_ratio_result: Result from _fetch_btc_eth_ratio()
            btc_dominance_result: Result from _fetch_btc_dominance()
        
        Returns:
            Dictionary with:
            - overall: str (Strong Buy/Buy/Hold/Sell/Strong Sell from weighted scoring)
            - total_score: float (-10 to +10)
            - weighted_breakdown: Dict (per-indicator scores and weights)
            - rationale: str (explanation of sentiment)
            - key_factors: List[str] (main contributing factors)
            - contrarian_signal: Optional[str] (if extreme sentiment detected)
            - status: str
        """
        try:
            # **PHASE 3**: Calculate weighted score using all 6 indicators
            weighted_result = self.calculate_crypto_weighted_score(
                btc_vol_result=btc_vol_result,
                eth_vol_result=eth_vol_result,
                btc_eth_ratio_result=btc_eth_ratio_result,
                btc_dominance_result=btc_dominance_result,
                btc_qqq_ratio_result=btc_qqq_ratio_result,
                crypto_fng_result=crypto_fng_result
            )
            
            total_score = weighted_result['total_score']
            recommendation = weighted_result['recommendation']
            breakdown = weighted_result['breakdown']
            
            # **PHASE 2 LOGIC PRESERVED**: Generate qualitative context
            # Extract zones and values for narrative
            qqq_zone = btc_qqq_ratio_result.get('zone', 'Unknown')
            fng_zone = crypto_fng_result.get('zone', 'Unknown')
            fng_value = crypto_fng_result.get('value')
            
            btc_vol_zone = btc_vol_result.get('zone', 'Unknown')
            eth_vol_zone = eth_vol_result.get('zone', 'Unknown')
            
            # Initialize sentiment components
            key_factors = []
            contrarian_signal = None
            
            # Analyze BTC/QQQ ratio (crypto-specific strength)
            if qqq_zone == 'Hot':
                key_factors.append("BTC outperforming tech stocks (crypto-specific strength)")
            elif qqq_zone == 'Cold':
                key_factors.append("BTC underperforming tech stocks (risk-off or crypto weakness)")
            
            # Analyze Fear & Greed (sentiment extremes)
            if fng_zone == 'Extreme Fear':
                key_factors.append(f"Extreme Fear detected ({fng_value}/100) - potential buying opportunity")
                contrarian_signal = "Extreme Fear: Contrarian BUY signal"
            elif fng_zone == 'Extreme Greed':
                key_factors.append(f"Extreme Greed detected ({fng_value}/100) - consider taking profits")
                contrarian_signal = "Extreme Greed: Contrarian SELL signal"
            elif fng_zone == 'Fear':
                key_factors.append(f"Fear sentiment ({fng_value}/100) - cautious market")
            elif fng_zone == 'Greed':
                key_factors.append(f"Greed sentiment ({fng_value}/100) - optimistic market")
            
            # Analyze volatility context
            high_vol = (btc_vol_zone == 'High Volatility' or eth_vol_zone == 'High Volatility')
            if high_vol:
                key_factors.append("High volatility - increased risk and opportunity")
            
            # Generate rationale based on weighted score
            if total_score <= -6:
                rationale = "Multiple strong bearish signals detected across indicators. Extreme fear/weakness creates contrarian buying opportunity."
            elif total_score <= -3:
                rationale = "Moderate bearish signals suggest favorable risk/reward for accumulation as market sentiment turns cautious."
            elif total_score <= 3:
                rationale = "Mixed or neutral signals across indicators. No clear directional bias - maintain current positions."
            elif total_score <= 6:
                rationale = "Moderate bullish signals indicate market strength. Consider taking profits as momentum builds."
            else:
                rationale = "Multiple strong bullish signals suggest extreme greed/strength. Contrarian sell opportunity as euphoria peaks."
            
            # Add volatility context
            if high_vol:
                rationale += " High volatility amplifies both risk and opportunity."
            
            return {
                'overall': recommendation,  # Phase 3: Weighted recommendation
                'total_score': total_score,  # Phase 3: -10 to +10 score
                'weighted_breakdown': breakdown,  # Phase 3: Individual indicator contributions
                'rationale': rationale,
                'key_factors': key_factors,
                'contrarian_signal': contrarian_signal,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error calculating crypto market sentiment: {str(e)}")
            return {
                'overall': 'Unknown',
                'total_score': 0.0,
                'weighted_breakdown': {},
                'rationale': f'Unable to calculate sentiment: {str(e)}',
                'key_factors': [],
                'contrarian_signal': None,
                'status': 'error'
            }
    
    # ==================== END GOLD INDICATORS ====================
    
    def _load_manual_inputs(self) -> Dict[str, Any]:
        """
        Load manual indicator overrides from JSON config file.
        
        Returns:
            Dictionary of manual inputs, or empty dict if file doesn't exist
        """
        if not self.manual_inputs_path.exists():
            return {}
        
        try:
            with open(self.manual_inputs_path, 'r', encoding='utf-8') as f:
                manual_data = json.load(f)
            logger.info(f"Loaded manual inputs from {self.manual_inputs_path}")
            return manual_data
        except Exception as e:
            logger.warning(f"Failed to load manual inputs from {self.manual_inputs_path}: {e}")
            return {}
    
    def _get_manual_input(self, indicator_key: str, classification_func, value_name: str = "value") -> Optional[Dict[str, Any]]:
        """
        Check if a manual input override exists for the given indicator.
        
        Manual inputs are used if:
        1. The indicator is enabled
        2. A value and date are provided
        3. The date is within 30 days
        
        Args:
            indicator_key: Key in manual_indicators.json (e.g., 'buffett_us', 'fear_greed')
            classification_func: Function to classify the value (e.g., self._classify_buffett)
            value_name: Name of the indicator for logging
        
        Returns:
            Dictionary with indicator data if manual input is valid, None otherwise
        """
        manual_inputs = self._load_manual_inputs()
        
        if indicator_key not in manual_inputs:
            return None
        
        indicator_config = manual_inputs[indicator_key]
        
        # Check if enabled
        if not indicator_config.get('enabled', False):
            return None
        
        # Check if value and date exist
        value = indicator_config.get('value')
        date_str = indicator_config.get('date')
        
        if value is None or date_str is None:
            logger.warning(f"Manual input for {indicator_key} is enabled but missing value or date")
            return None
        
        # Check date freshness (within 30 days)
        try:
            manual_date = datetime.strptime(date_str, '%Y-%m-%d')
            days_old = (datetime.now() - manual_date).days
            
            if days_old > 30:
                logger.warning(f"Manual input for {indicator_key} is {days_old} days old (> 30 days), ignoring")
                return None
            
            # Classify the value
            zone, level = classification_func(value)
            
            logger.info(f"Using manual input for {indicator_key}: {value} ({zone}) from {date_str}")
            
            # Calculate data age warning
            data_age_warning = None
            if days_old > 2:
                data_age_warning = f"Manual input ({days_old} days old)"
            
            return {
                'value': float(value),
                'zone': zone,
                'level': level,
                'status': 'success',
                'error_message': None,
                'last_updated': manual_date.isoformat(),
                'data_age_days': days_old,
                'data_age_warning': data_age_warning,
                'source': 'Manual Input'
            }
            
        except Exception as e:
            logger.error(f"Failed to process manual input for {indicator_key}: {e}")
            return None
    
    def _classify_shiller(self, value: float) -> Tuple[str, int]:
        """
        Map Shiller P/E value to qualitative zone and risk level.
        
        Zones:
        - < 15: "Extreme Cold" (Level 0) - Extremely undervalued
        - 15-20: "Cold" (Level 1) - Undervalued
        - 20-30: "Normal" (Level 2) - Fair value
        - 30-40: "Hot" (Level 3) - Overvalued
        - > 40: "Extreme Boil" (Level 4) - Extremely overvalued
        
        Args:
            value: Shiller P/E ratio
            
        Returns:
            Tuple of (zone_name, risk_level)
        """
        if value < 15:
            return ("Extreme Cold", 0)
        elif value < 20:
            return ("Cold", 1)
        elif value < 30:
            return ("Normal", 2)
        elif value < 40:
            return ("Hot", 3)
        else:
            return ("Extreme Boil", 4)
    
    def _classify_fear_greed(self, value: float) -> Tuple[str, int]:
        """
        Map Fear & Greed score to qualitative zone and risk level.
        
        Zones:
        - 0-25: "Extreme Fear" (Level 0)
        - 25-45: "Fear" (Level 1)
        - 45-55: "Neutral" (Level 2)
        - 55-75: "Greed" (Level 3)
        - 75-100: "Extreme Greed" (Level 4)
        
        Args:
            value: Fear & Greed score (0-100)
            
        Returns:
            Tuple of (zone_name, risk_level)
        """
        if value < 25:
            return ("Extreme Fear", 0)
        elif value < 45:
            return ("Fear", 1)
        elif value < 55:
            return ("Neutral", 2)
        elif value < 75:
            return ("Greed", 3)
        else:
            return ("Extreme Greed", 4)

    def _fetch_world_bank_buffett(self, wb_country_code: str, country_name: str) -> Dict[str, Any]:
        """
        Fallback: Fetch Market Cap to GDP ratio directly from World Bank API.
        Indicator: CM.MKT.LCAP.GD.ZS (Market capitalization of listed domestic companies, % of GDP)

        Returns a dict matching the Buffett indicator shape.
        """
        try:
            url = self.WORLD_BANK_API_BASE.format(country=wb_country_code)
            payload = None
            last_err = None
            # simple retry with incremental backoff
            for attempt in range(5):
                try:
                    timeout = self.REQUEST_TIMEOUT + attempt * 5
                    response = requests.get(url, timeout=timeout)
                    response.raise_for_status()
                    payload = response.json()
                    break
                except Exception as e:
                    last_err = e
                    logger.warning(f"World Bank request attempt {attempt+1} failed for {country_name}: {e}")
                    sleep(0.75 * (attempt + 1))
            if payload is None:
                raise last_err or RuntimeError("Unknown World Bank request error")
            # payload is [metadata, data]; find first entry with value
            series = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
            # pick freshest non-null by date desc
            latest = None
            try:
                series_sorted = sorted(
                    [s for s in series if s.get('date')],
                    key=lambda s: int(s['date']),
                    reverse=True
                )
            except Exception:
                series_sorted = series
            for item in series_sorted:
                if item.get('value') is not None:
                    latest = item
                    break
            if not latest:
                raise ValueError("World Bank returned no data for CM.MKT.LCAP.GD.ZS")

            ratio_pct = float(latest['value'])
            year = latest.get('date')  # e.g., '2023'
            data_date = f"{year}-01-01" if year else None

            # Freshness
            data_age_warning = None
            data_age_years: Optional[float] = None
            if year:
                try:
                    d = datetime.strptime(data_date, '%Y-%m-%d')
                    days_old = (datetime.now() - d).days
                    if days_old > 365:
                        data_age_years = days_old / 365
                        data_age_warning = f"⚠️ Data is {data_age_years:.1f} years old"
                except Exception:
                    pass

            zone, level = self._classify_buffett(ratio_pct / 100.0)
            logger.info(f"World Bank Buffett ({country_name}) fetched: {ratio_pct:.2f}% as of {data_date} ({zone})")
            return {
                'value': float(ratio_pct),
                'zone': zone,
                'level': level,
                'status': 'success',
                'error_message': None,
                'country': country_name,
                'date': data_date,
                'data_age_warning': data_age_warning,
                'data_age_years': data_age_years,
                'source': 'World Bank'
            }
        except Exception as e:
            logger.error(f"World Bank fallback failed for {country_name}: {e}")
            return {
                'value': None,
                'zone': 'Unknown',
                'level': -1,
                'status': 'error',
                'error_message': str(e),
                'country': country_name
            }
    
    def _classify_vix(self, value: float) -> Tuple[str, int]:
        """
        Map VIX value to qualitative zone and risk level.
        
        VIX measures volatility (inverse of sentiment):
        - Low VIX = Market complacency/greed (higher risk)
        - High VIX = Market fear (lower risk, potential opportunity)
        
        Zones:
        - < 12: "Extreme Complacency" (Level 4) - Very low fear, high risk
        - 12-16: "Low Fear" (Level 3) - Below average volatility
        - 16-20: "Normal" (Level 2) - Average volatility
        - 20-30: "Elevated Fear" (Level 1) - Above average volatility
        - > 30: "Extreme Fear" (Level 0) - Very high volatility, potential opportunity
        
        Args:
            value: VIX value
            
        Returns:
            Tuple of (zone_name, risk_level)
        """
        if value < 12:
            return ("Extreme Complacency", 4)
        elif value < 16:
            return ("Low Fear", 3)
        elif value < 20:
            return ("Normal", 2)
        elif value < 30:
            return ("Elevated Fear", 1)
        else:
            return ("Extreme Fear", 0)
    
    def _classify_buffett(self, value: float) -> Tuple[str, int]:
        """
        Map Buffett Indicator to qualitative zone and risk level.
        
        Zones:
        - < 0.75: "Significantly Undervalued" (Level 0)
        - 0.75-0.90: "Modestly Undervalued" (Level 1)
        - 0.90-1.15: "Fair Value" (Level 2)
        - 1.15-1.40: "Modestly Overvalued" (Level 3)
        - > 1.40: "Significantly Overvalued" (Level 4)
        
        Args:
            value: Buffett Indicator ratio (TMC/GDP)
            
        Returns:
            Tuple of (zone_name, risk_level)
        """
        if value < 0.75:
            return ("Significantly Undervalued", 0)
        elif value < 0.90:
            return ("Modestly Undervalued", 1)
        elif value < 1.15:
            return ("Fair Value", 2)
        elif value < 1.40:
            return ("Modestly Overvalued", 3)
        else:
            return ("Significantly Overvalued", 4)
    
    def _load_cache(self) -> Optional[Dict[str, Any]]:
        """
        Load cached data if file exists and is within TTL.
        
        Returns:
            Cached data dictionary or None if cache invalid/expired
        """
        if not self.cache_path.exists():
            logger.debug("Cache file does not exist")
            return None
        
        try:
            with open(self.cache_path, 'r') as f:
                cached = json.load(f)
            
            # Check timestamp
            last_updated = datetime.fromisoformat(cached['last_updated'])
            if datetime.now() - last_updated > self.cache_ttl:
                logger.info("Cache expired, will fetch fresh data")
                return None
            
            logger.debug(f"Cache valid (age: {datetime.now() - last_updated})")
            return cached
            
        except Exception as e:
            logger.warning(f"Failed to load cache: {str(e)}")
            return None
    
    def _save_cache(self, data: Dict[str, Any]) -> None:
        """
        Save fetched data to cache file.
        
        Args:
            data: Market thermometer data dictionary
        """
        try:
            with open(self.cache_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Cache saved to {self.cache_path}")
        except Exception as e:
            logger.warning(f"Failed to save cache: {str(e)}")
    
    def _load_gold_cache(self) -> Optional[Dict[str, Any]]:
        """Load cached gold analysis data if file exists and is within TTL."""
        if not self.gold_cache_path.exists():
            return None
        
        try:
            with open(self.gold_cache_path, 'r') as f:
                cached = json.load(f)
            
            last_updated = datetime.fromisoformat(cached.get('last_updated', ''))
            if datetime.now() - last_updated > self.cache_ttl:
                logger.debug("Gold cache expired")
                return None
            
            return cached
        except Exception as e:
            logger.warning(f"Failed to load gold cache: {str(e)}")
            return None
    
    def _save_gold_cache(self, data: Dict[str, Any]) -> None:
        """Save gold analysis data to cache file."""
        try:
            with open(self.gold_cache_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Gold cache saved to {self.gold_cache_path}")
        except Exception as e:
            logger.warning(f"Failed to save gold cache: {str(e)}")
    
    def _load_crypto_cache(self) -> Optional[Dict[str, Any]]:
        """Load cached crypto analysis data if file exists and is within TTL."""
        if not self.crypto_cache_path.exists():
            return None
        
        try:
            with open(self.crypto_cache_path, 'r') as f:
                cached = json.load(f)
            
            last_updated = datetime.fromisoformat(cached.get('last_updated', ''))
            if datetime.now() - last_updated > self.cache_ttl:
                logger.debug("Crypto cache expired")
                return None
            
            return cached
        except Exception as e:
            logger.warning(f"Failed to load crypto cache: {str(e)}")
            return None
    
    def _save_crypto_cache(self, data: Dict[str, Any]) -> None:
        """Save crypto analysis data to cache file."""
        try:
            with open(self.crypto_cache_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Crypto cache saved to {self.crypto_cache_path}")
        except Exception as e:
            logger.warning(f"Failed to save crypto cache: {str(e)}")


# Convenience function for direct usage
def get_market_sentiment() -> Dict[str, Any]:
    """
    Convenience function to fetch market sentiment indicators.
    
    Returns:
        Market thermometer data dictionary
    """
    analyzer = MacroAnalyzer()
    return analyzer.get_market_thermometer()
