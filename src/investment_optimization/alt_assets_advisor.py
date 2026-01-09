"""
Alternative Assets Advisor Module

This module provides buy/sell recommendations for alternative assets (gold, crypto) based on
volatility indicators and relative value metrics. It implements a multi-indicator scoring system
that combines various market signals to generate actionable investment advice.

Core Functions:
- calculate_gold_score(): Analyzes 3 gold indicators (GVZ, Gold/Silver ratio, S&P 500/Gold ratio)
- calculate_crypto_scores(): Analyzes crypto indicators (BTC/ETH volatility, ratios)
- score_to_recommendation(): Maps numeric scores to 5-level recommendations

Scoring System:
- Each indicator contributes -1 (bullish), 0 (neutral), or +1 (bearish)
- Total score range: -3 to +3
- Recommendation levels: Strong Buy, Buy, Hold, Sell, Strong Sell

Author: Investment System
Created: 2025-10-29
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class AltAssetsAdvisor:
    """
    Alternative assets investment advisor using multi-indicator scoring system.
    
    This class analyzes volatility indicators and relative value metrics to provide
    buy/sell recommendations for gold and cryptocurrencies. It loads configuration
    from YAML files and applies threshold-based scoring logic.
    """
    
    def __init__(self, config_path: str = 'config/alt_assets_indicators.yaml'):
        """
        Initialize the advisor with configuration.
        
        Args:
            config_path: Path to YAML configuration file with indicator thresholds
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.config = self._load_config()
        
        # Extract gold indicator thresholds for easy access
        self.gold_config = self.config.get('gold_indicators', {})
        self.crypto_config = self.config.get('crypto_indicators', {})
        self.general_config = self.config.get('general', {})
        
        self.logger.info("AltAssetsAdvisor initialized with config from %s", config_path)
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML file."""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                self.logger.error("Config file not found: %s", self.config_path)
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            self.logger.info("Configuration loaded successfully from %s", self.config_path)
            return config
            
        except Exception as e:
            self.logger.error("Failed to load configuration: %s", str(e))
            raise
    
    def calculate_gold_score(
        self,
        gvz: Optional[float] = None,
        gold_silver_ratio: Optional[float] = None,
        sp500_gold_ratio: Optional[float] = None
    ) -> Dict:
        """
        Calculate gold investment score based on 3 indicators.
        
        Scoring Logic:
        - Each indicator contributes -1 (bullish), 0 (neutral), or +1 (bearish)
        - GVZ: High volatility = fear = contrarian buy signal (-1)
        - Gold/Silver: Low ratio = gold cheap = buy signal (-1)
        - S&P 500/Gold: High ratio = stocks expensive = gold buy signal (-1)
        
        Args:
            gvz: Cboe Gold Volatility Index (5-100, typical 10-50)
            gold_silver_ratio: Gold price / Silver price (40-150, typical 55-85)
            sp500_gold_ratio: S&P 500 level / Gold oz price (0.5-3.5, typical 1.5-2.5)
        
        Returns:
            Dictionary with:
            - total_score: Float from -3 to +3
            - recommendation: String (Strong Buy, Buy, Hold, Sell, Strong Sell)
            - indicator_scores: Dict with individual contributions
            - indicator_signals: Dict with individual recommendations
            - analysis_timestamp: ISO timestamp
            - missing_indicators: List of indicators with None values
        """
        self.logger.info("Calculating gold score - GVZ: %s, Gold/Silver: %s, S&P/Gold: %s",
                        gvz, gold_silver_ratio, sp500_gold_ratio)
        
        # Track missing indicators
        missing = []
        if gvz is None:
            missing.append('gvz')
        if gold_silver_ratio is None:
            missing.append('gold_silver_ratio')
        if sp500_gold_ratio is None:
            missing.append('sp500_gold_ratio')
        
        # Score each indicator (-1, 0, +1)
        gvz_score = self._score_gvz(gvz) if gvz is not None else 0
        gold_silver_score = self._score_gold_silver_ratio(gold_silver_ratio) if gold_silver_ratio is not None else 0
        sp500_gold_score = self._score_sp500_gold_ratio(sp500_gold_ratio) if sp500_gold_ratio is not None else 0
        
        # Calculate total score
        total_score = gvz_score + gold_silver_score + sp500_gold_score
        
        # Get recommendation
        recommendation, description = self._score_to_recommendation(total_score)
        
        # Get individual signal interpretations
        gvz_signal = self._gvz_to_signal(gvz) if gvz is not None else 'N/A'
        gold_silver_signal = self._gold_silver_to_signal(gold_silver_ratio) if gold_silver_ratio is not None else 'N/A'
        sp500_gold_signal = self._sp500_gold_to_signal(sp500_gold_ratio) if sp500_gold_ratio is not None else 'N/A'
        
        result = {
            'total_score': total_score,
            'recommendation': recommendation,
            'description': description,
            'indicator_scores': {
                'gvz': gvz_score,
                'gold_silver_ratio': gold_silver_score,
                'sp500_gold_ratio': sp500_gold_score
            },
            'indicator_signals': {
                'gvz': gvz_signal,
                'gold_silver_ratio': gold_silver_signal,
                'sp500_gold_ratio': sp500_gold_signal
            },
            'indicator_values': {
                'gvz': gvz,
                'gold_silver_ratio': gold_silver_ratio,
                'sp500_gold_ratio': sp500_gold_ratio
            },
            'missing_indicators': missing,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        self.logger.info("Gold analysis complete - Score: %.1f, Recommendation: %s",
                        total_score, recommendation)
        
        return result
    
    def _score_gvz(self, gvz: float) -> int:
        """
        Score GVZ (Gold Volatility Index).
        
        Logic: High volatility = fear = contrarian buy signal
        - GVZ > 35: Strong buy (-1)
        - GVZ 28-35: Buy (-1)
        - GVZ 15-28: Hold (0)
        - GVZ 10-15: Sell (+1)
        - GVZ < 10: Strong sell (+1)
        """
        thresholds = self.gold_config.get('gvz', {})
        strong_buy = thresholds.get('strong_buy_threshold', 35)
        buy = thresholds.get('buy_threshold', 28)
        sell = thresholds.get('sell_threshold', 15)
        strong_sell = thresholds.get('strong_sell_threshold', 10)
        
        if gvz >= strong_buy:
            return -1  # Extreme fear = buy opportunity
        elif gvz >= buy:
            return -1  # High volatility = buy
        elif gvz >= sell:
            return 0   # Normal volatility = hold
        elif gvz >= strong_sell:
            return 1   # Low volatility = complacency = sell
        else:
            return 1   # Extreme complacency = sell
    
    def _score_gold_silver_ratio(self, ratio: float) -> int:
        """
        Score Gold/Silver ratio.
        
        Logic: Low ratio = gold cheap relative to silver = buy signal
        - Ratio < 55: Strong buy (-1)
        - Ratio 55-70: Buy (-1)
        - Ratio 70-85: Hold (0)
        - Ratio 85-95: Sell (+1)
        - Ratio > 95: Strong sell (+1)
        """
        thresholds = self.gold_config.get('gold_silver_ratio', {})
        strong_buy = thresholds.get('strong_buy_threshold', 55)
        buy = thresholds.get('buy_threshold', 70)
        sell = thresholds.get('sell_threshold', 85)
        strong_sell = thresholds.get('strong_sell_threshold', 95)
        
        if ratio < strong_buy:
            return -1  # Gold very cheap
        elif ratio < buy:
            return -1  # Gold moderately cheap
        elif ratio < sell:
            return 0   # Normal range
        elif ratio < strong_sell:
            return 1   # Gold moderately expensive
        else:
            return 1   # Gold very expensive
    
    def _score_sp500_gold_ratio(self, ratio: float) -> int:
        """
        Score S&P 500/Gold ratio.
        
        Logic: High ratio = stocks expensive relative to gold = gold buy signal
        - Ratio < 1.5: Strong sell gold (+1) - stocks cheap
        - Ratio 1.5-1.7: Sell gold (+1)
        - Ratio 1.7-2.2: Hold (0)
        - Ratio 2.2-2.5: Buy gold (-1) - stocks expensive
        - Ratio > 2.5: Strong buy gold (-1)
        """
        thresholds = self.gold_config.get('sp500_gold_ratio', {})
        strong_buy = thresholds.get('strong_buy_threshold', 1.5)
        buy = thresholds.get('buy_threshold', 1.7)
        sell = thresholds.get('sell_threshold', 2.2)
        strong_sell = thresholds.get('strong_sell_threshold', 2.5)
        
        if ratio < strong_buy:
            return 1   # Stocks very cheap = don't buy gold
        elif ratio < buy:
            return 1   # Stocks moderately cheap
        elif ratio < sell:
            return 0   # Normal range
        elif ratio < strong_sell:
            return -1  # Stocks moderately expensive = buy gold
        else:
            return -1  # Stocks very expensive = strong buy gold
    
    def _score_to_recommendation(self, score: float) -> Tuple[str, str]:
        """
        Map numeric score to recommendation level.
        
        Args:
            score: Total score from -3 to +3
        
        Returns:
            Tuple of (recommendation, description)
        """
        scoring_config = self.gold_config.get('scoring', {}).get('score_to_recommendation', {})
        
        # Default mappings if config is missing
        if score <= -2:
            rec_config = scoring_config.get('strong_buy', {})
            return ('Strong Buy', rec_config.get('description', 'Strong bullish signals'))
        elif score <= -0.5:
            rec_config = scoring_config.get('buy', {})
            return ('Buy', rec_config.get('description', 'Bullish signals'))
        elif score <= 0.5:
            rec_config = scoring_config.get('hold', {})
            return ('Hold', rec_config.get('description', 'Neutral signals'))
        elif score <= 1.5:
            rec_config = scoring_config.get('sell', {})
            return ('Sell', rec_config.get('description', 'Bearish signals'))
        else:
            rec_config = scoring_config.get('strong_sell', {})
            return ('Strong Sell', rec_config.get('description', 'Strong bearish signals'))
    
    def _gvz_to_signal(self, gvz: float) -> str:
        """Convert GVZ value to signal string."""
        thresholds = self.gold_config.get('gvz', {})
        strong_buy = thresholds.get('strong_buy_threshold', 35)
        buy = thresholds.get('buy_threshold', 28)
        sell = thresholds.get('sell_threshold', 15)
        strong_sell = thresholds.get('strong_sell_threshold', 10)
        
        if gvz >= strong_buy:
            return 'Strong Buy (Extreme Fear)'
        elif gvz >= buy:
            return 'Buy (High Volatility)'
        elif gvz >= sell:
            return 'Hold (Normal)'
        elif gvz >= strong_sell:
            return 'Sell (Complacency)'
        else:
            return 'Strong Sell (Extreme Complacency)'
    
    def _gold_silver_to_signal(self, ratio: float) -> str:
        """Convert Gold/Silver ratio to signal string."""
        thresholds = self.gold_config.get('gold_silver_ratio', {})
        strong_buy = thresholds.get('strong_buy_threshold', 55)
        buy = thresholds.get('buy_threshold', 70)
        sell = thresholds.get('sell_threshold', 85)
        strong_sell = thresholds.get('strong_sell_threshold', 95)
        
        if ratio < strong_buy:
            return 'Strong Buy (Gold Very Cheap)'
        elif ratio < buy:
            return 'Buy (Gold Moderately Cheap)'
        elif ratio < sell:
            return 'Hold (Normal Range)'
        elif ratio < strong_sell:
            return 'Sell (Gold Moderately Expensive)'
        else:
            return 'Strong Sell (Gold Very Expensive)'
    
    def _sp500_gold_to_signal(self, ratio: float) -> str:
        """Convert S&P 500/Gold ratio to signal string."""
        thresholds = self.gold_config.get('sp500_gold_ratio', {})
        strong_buy = thresholds.get('strong_buy_threshold', 1.5)
        buy = thresholds.get('buy_threshold', 1.7)
        sell = thresholds.get('sell_threshold', 2.2)
        strong_sell = thresholds.get('strong_sell_threshold', 2.5)
        
        if ratio < strong_buy:
            return 'Strong Sell Gold (Stocks Very Cheap)'
        elif ratio < buy:
            return 'Sell Gold (Stocks Moderately Cheap)'
        elif ratio < sell:
            return 'Hold (Normal Range)'
        elif ratio < strong_sell:
            return 'Buy Gold (Stocks Moderately Expensive)'
        else:
            return 'Strong Buy Gold (Stocks Very Expensive)'
    
    # ==================== CRYPTO SCORING METHODS (Phase 2) ====================
    
    def calculate_crypto_score(
        self,
        crypto_type: str,  # 'btc' or 'eth'
        volatility: Optional[float] = None,
        btc_eth_ratio: Optional[float] = None,
        btc_dominance: Optional[float] = None
    ) -> Dict:
        """
        Calculate crypto investment score for BTC or ETH.
        
        Scoring Logic (3 indicators):
        - Volatility: High vol = fear = contrarian buy (-1), Low vol = complacency = sell (+1)
        - BTC/ETH Ratio: For BTC - low ratio = cheap = buy (-1), For ETH - high ratio = cheap = buy (-1)
        - BTC Dominance: For BTC - low dom = undervalued = buy (-1), For ETH - high dom = cheap = buy (-1)
        
        Args:
            crypto_type: 'btc' or 'eth'
            volatility: 30-day annualized volatility percentage (5-300%)
            btc_eth_ratio: BTC price / ETH price (10-35, typical 15-25)
            btc_dominance: BTC market cap / Total crypto market cap percentage (30-70%, typical 40-60%)
        
        Returns:
            Dictionary with total_score, recommendation, indicator_scores, signals, and analysis details
        """
        crypto_type = crypto_type.lower()
        if crypto_type not in ['btc', 'eth']:
            raise ValueError(f"Invalid crypto_type: {crypto_type}. Must be 'btc' or 'eth'.")
        
        self.logger.info(f"Calculating {crypto_type.upper()} score - vol: {volatility}, BTC/ETH: {btc_eth_ratio}, BTC dom: {btc_dominance}")
        
        # Track individual indicator contributions
        indicator_scores = {}
        indicator_signals = {}
        indicator_values = {}
        missing_indicators = []
        
        # 1. Volatility scoring (same logic for both BTC and ETH, different thresholds)
        if volatility is not None:
            vol_key = f'{crypto_type}_volatility'
            indicator_values[vol_key] = volatility
            indicator_scores[vol_key] = self._score_crypto_volatility(volatility, crypto_type)
            indicator_signals[vol_key] = self._crypto_volatility_to_signal(volatility, crypto_type)
        else:
            missing_indicators.append(f'{crypto_type}_volatility')
        
        # 2. BTC/ETH Ratio scoring (inverted logic for BTC vs ETH)
        if btc_eth_ratio is not None:
            indicator_values['btc_eth_ratio'] = btc_eth_ratio
            indicator_scores['btc_eth_ratio'] = self._score_btc_eth_ratio(btc_eth_ratio, crypto_type)
            indicator_signals['btc_eth_ratio'] = self._btc_eth_ratio_to_signal(btc_eth_ratio, crypto_type)
        else:
            missing_indicators.append('btc_eth_ratio')
        
        # 3. BTC Dominance scoring (inverted logic for BTC vs ETH)
        if btc_dominance is not None:
            indicator_values['btc_dominance'] = btc_dominance
            indicator_scores['btc_dominance'] = self._score_btc_dominance(btc_dominance, crypto_type)
            indicator_signals['btc_dominance'] = self._btc_dominance_to_signal(btc_dominance, crypto_type)
        else:
            missing_indicators.append('btc_dominance')
        
        # Calculate total score
        total_score = sum(indicator_scores.values())
        
        # Map to recommendation
        recommendation = self._score_to_recommendation(total_score)
        
        result = {
            'total_score': round(total_score, 1),
            'recommendation': recommendation,
            'indicator_scores': indicator_scores,
            'indicator_signals': indicator_signals,
            'indicator_values': indicator_values,
            'missing_indicators': missing_indicators,
            'analysis_timestamp': datetime.now().isoformat(),
            'crypto_type': crypto_type.upper()
        }
        
        self.logger.info(f"{crypto_type.upper()} analysis complete - Score: {total_score:.1f}, Recommendation: {recommendation}")
        
        return result
    
    def _score_crypto_volatility(self, volatility: float, crypto_type: str) -> int:
        """
        Score crypto volatility indicator (contrarian: high vol = buy, low vol = sell).
        
        Returns: -1 (bullish), 0 (neutral), or +1 (bearish)
        """
        config_key = f'{crypto_type}_volatility'
        thresholds = self.crypto_config.get(config_key, {})
        
        strong_buy = thresholds.get('strong_buy_threshold', 80)
        buy = thresholds.get('buy_threshold', 60)
        sell = thresholds.get('sell_threshold', 25)
        strong_sell = thresholds.get('strong_sell_threshold', 20)
        
        # Contrarian logic: High volatility = fear = buy opportunity
        if volatility >= strong_buy:
            return -1  # Strong buy (extreme fear)
        elif volatility >= buy:
            return -1  # Buy (elevated fear)
        elif volatility <= strong_sell:
            return +1  # Strong sell (extreme complacency)
        elif volatility <= sell:
            return +1  # Sell (complacency)
        else:
            return 0   # Hold (normal volatility)
    
    def _score_btc_eth_ratio(self, ratio: float, crypto_type: str) -> int:
        """
        Score BTC/ETH ratio (inverted logic for BTC vs ETH).
        
        For BTC: Low ratio = BTC cheap = buy (-1), High ratio = BTC expensive = sell (+1)
        For ETH: Low ratio = ETH expensive = sell (+1), High ratio = ETH cheap = buy (-1)
        
        Returns: -1 (bullish), 0 (neutral), or +1 (bearish)
        """
        thresholds = self.crypto_config.get('btc_eth_ratio', {})
        
        strong_buy = thresholds.get('strong_buy_threshold', 12)
        buy = thresholds.get('buy_threshold', 15)
        sell = thresholds.get('sell_threshold', 22)
        strong_sell = thresholds.get('strong_sell_threshold', 25)
        
        if crypto_type == 'btc':
            # For BTC: Lower ratio = cheaper BTC = buy
            if ratio < strong_buy:
                return -1  # Strong buy (BTC very cheap)
            elif ratio < buy:
                return -1  # Buy (BTC moderately cheap)
            elif ratio > strong_sell:
                return +1  # Strong sell (BTC very expensive)
            elif ratio > sell:
                return +1  # Sell (BTC moderately expensive)
            else:
                return 0   # Hold
        else:  # ETH
            # For ETH: Higher ratio = cheaper ETH = buy (inverted)
            if ratio > strong_sell:
                return -1  # Strong buy (ETH very cheap)
            elif ratio > sell:
                return -1  # Buy (ETH moderately cheap)
            elif ratio < strong_buy:
                return +1  # Strong sell (ETH very expensive)
            elif ratio < buy:
                return +1  # Sell (ETH moderately expensive)
            else:
                return 0   # Hold
    
    def _score_btc_dominance(self, dominance: float, crypto_type: str) -> int:
        """
        Score BTC dominance (inverted logic for BTC vs ETH).
        
        For BTC: Low dom = BTC undervalued = buy (-1), High dom = BTC overvalued = sell (+1)
        For ETH: Low dom = Alts expensive = sell (+1), High dom = Alts cheap = buy (-1)
        
        Returns: -1 (bullish), 0 (neutral), or +1 (bearish)
        """
        thresholds = self.crypto_config.get('btc_dominance', {})
        
        strong_buy = thresholds.get('strong_buy_threshold', 35)
        buy = thresholds.get('buy_threshold', 42)
        sell = thresholds.get('sell_threshold', 55)
        strong_sell = thresholds.get('strong_sell_threshold', 60)
        
        if crypto_type == 'btc':
            # For BTC: Lower dominance = BTC undervalued = buy
            if dominance < strong_buy:
                return -1  # Strong buy (extreme alt season, BTC cheap)
            elif dominance < buy:
                return -1  # Buy (alt season, BTC undervalued)
            elif dominance > strong_sell:
                return +1  # Strong sell (extreme BTC dominance)
            elif dominance > sell:
                return +1  # Sell (BTC dominance high)
            else:
                return 0   # Hold
        else:  # ETH
            # For ETH: Higher dominance = Alts cheap = buy (inverted)
            if dominance > strong_sell:
                return -1  # Strong buy (extreme BTC dom, alts very cheap)
            elif dominance > sell:
                return -1  # Buy (BTC dom high, alts cheap)
            elif dominance < strong_buy:
                return +1  # Strong sell (extreme alt season)
            elif dominance < buy:
                return +1  # Sell (alt season, alts expensive)
            else:
                return 0   # Hold
    
    def _crypto_volatility_to_signal(self, volatility: float, crypto_type: str) -> str:
        """Convert crypto volatility to human-readable signal."""
        config_key = f'{crypto_type}_volatility'
        thresholds = self.crypto_config.get(config_key, {})
        
        strong_buy = thresholds.get('strong_buy_threshold', 80)
        buy = thresholds.get('buy_threshold', 60)
        sell = thresholds.get('sell_threshold', 25)
        strong_sell = thresholds.get('strong_sell_threshold', 20)
        
        if volatility >= strong_buy:
            return 'Strong Buy (Extreme Fear)'
        elif volatility >= buy:
            return 'Buy (Elevated Uncertainty)'
        elif volatility <= strong_sell:
            return 'Strong Sell (Extreme Complacency)'
        elif volatility <= sell:
            return 'Sell (Low Volatility)'
        else:
            return 'Hold (Normal)'
    
    def _btc_eth_ratio_to_signal(self, ratio: float, crypto_type: str) -> str:
        """Convert BTC/ETH ratio to human-readable signal."""
        thresholds = self.crypto_config.get('btc_eth_ratio', {})
        
        strong_buy = thresholds.get('strong_buy_threshold', 12)
        buy = thresholds.get('buy_threshold', 15)
        sell = thresholds.get('sell_threshold', 22)
        strong_sell = thresholds.get('strong_sell_threshold', 25)
        
        if crypto_type == 'btc':
            if ratio < strong_buy:
                return 'Strong Buy (BTC Very Cheap)'
            elif ratio < buy:
                return 'Buy (BTC Moderately Cheap)'
            elif ratio > strong_sell:
                return 'Strong Sell (BTC Very Expensive)'
            elif ratio > sell:
                return 'Sell (BTC Moderately Expensive)'
            else:
                return 'Hold (Normal Range)'
        else:  # ETH
            if ratio > strong_sell:
                return 'Strong Buy (ETH Very Cheap)'
            elif ratio > sell:
                return 'Buy (ETH Moderately Cheap)'
            elif ratio < strong_buy:
                return 'Strong Sell (ETH Very Expensive)'
            elif ratio < buy:
                return 'Sell (ETH Moderately Expensive)'
            else:
                return 'Hold (Normal Range)'
    
    def _btc_dominance_to_signal(self, dominance: float, crypto_type: str) -> str:
        """Convert BTC dominance to human-readable signal."""
        thresholds = self.crypto_config.get('btc_dominance', {})
        
        strong_buy = thresholds.get('strong_buy_threshold', 35)
        buy = thresholds.get('buy_threshold', 42)
        sell = thresholds.get('sell_threshold', 55)
        strong_sell = thresholds.get('strong_sell_threshold', 60)
        
        if crypto_type == 'btc':
            if dominance < strong_buy:
                return 'Strong Buy (Extreme Alt Season)'
            elif dominance < buy:
                return 'Buy (Alt Season)'
            elif dominance > strong_sell:
                return 'Strong Sell (Extreme BTC Dominance)'
            elif dominance > sell:
                return 'Sell (High BTC Dominance)'
            else:
                return 'Hold (Normal)'
        else:  # ETH
            if dominance > strong_sell:
                return 'Strong Buy (Alts Very Cheap)'
            elif dominance > sell:
                return 'Buy (Alts Cheap)'
            elif dominance < strong_buy:
                return 'Strong Sell (Extreme Alt Season)'
            elif dominance < buy:
                return 'Sell (Alt Season Ending)'
            else:
                return 'Hold (Normal)'
    
    # ==================== END CRYPTO SCORING METHODS ====================


# Convenience function for standalone use
def analyze_gold_indicators(
    gvz: Optional[float] = None,
    gold_silver_ratio: Optional[float] = None,
    sp500_gold_ratio: Optional[float] = None,
    config_path: str = 'config/alt_assets_indicators.yaml'
) -> Dict:
    """
    Convenience function to analyze gold indicators without instantiating class.
    
    Args:
        gvz: Cboe Gold Volatility Index
        gold_silver_ratio: Gold price / Silver price
        sp500_gold_ratio: S&P 500 level / Gold oz price
        config_path: Path to configuration file
    
    Returns:
        Dictionary with score, recommendation, and analysis details
    """
    advisor = AltAssetsAdvisor(config_path=config_path)
    return advisor.calculate_gold_score(gvz, gold_silver_ratio, sp500_gold_ratio)

