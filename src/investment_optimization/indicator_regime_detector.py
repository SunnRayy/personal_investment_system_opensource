#!/usr/bin/env python3
"""
Market Regime Detector (Indicator-Based) - Identifies current market regime based on macro indicators.

This module evaluates macroeconomic indicators from the Market Thermometer to determine
the active market regime and generate dynamic asset allocation targets.

NOTE: This is different from the HMM-based market_regime_detector.py. This module uses
rule-based indicator thresholds (Shiller PE, Fear & Greed, Buffett Indicators) to determine
market regimes for tactical asset allocation adjustments.

Author: Personal Investment System
Date: October 19, 2025
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class IndicatorRegimeDetector:
    """
    Detects current market regime based on Market Thermometer indicators.
    
    Evaluates macroeconomic indicators against predefined scenarios to determine
    the active market regime and generate dynamic asset allocation targets.
    
    The detector implements a priority-based matching system where regimes are
    evaluated in order of priority (1 = highest). The first regime whose conditions
    are satisfied becomes the active regime.
    
    Supported Regimes:
    - Maximum Defense (最高防御): Bubble conditions - reduce risk
    - Cautious Rotation (谨慎轮动): Regional divergence - rotate geographically
    - Maximum Offense (全力进攻): Crisis conditions - maximize exposure
    - Benchmark Cruising (基准巡航): Normal conditions - follow baseline strategy
    """
    
    def __init__(self, config_path: str = 'config/market_regimes.yaml'):
        """
        Initialize IndicatorRegimeDetector with configuration.
        
        Args:
            config_path: Path to market regimes configuration file
        """
        self.config_path = Path(config_path)
        self.regimes = self._load_regimes()
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"IndicatorRegimeDetector initialized with {len(self.regimes)} regimes")
    
    def _load_regimes(self) -> List[Dict]:
        """
        Load regimes from YAML configuration file.
        
        Returns:
            List of regime dictionaries sorted by priority (ascending)
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML is invalid
            ValueError: If configuration structure is invalid
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Market regimes config not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            regimes = config.get('regimes', [])
            
            if not regimes:
                raise ValueError("No regimes defined in configuration")
            
            # Validate each regime has required fields
            for regime in regimes:
                required_fields = ['name', 'name_cn', 'priority', 'conditions']
                missing = [f for f in required_fields if f not in regime]
                if missing:
                    raise ValueError(f"Regime '{regime.get('name', 'Unknown')}' missing fields: {missing}")
            
            # Sort by priority (ascending - check priority 1 first)
            regimes_sorted = sorted(regimes, key=lambda r: r['priority'])
            
            logger.info(f"Loaded {len(regimes_sorted)} market regimes")
            for regime in regimes_sorted:
                logger.debug(f"  [{regime['priority']}] {regime['name']} ({regime['name_cn']})")
            
            return regimes_sorted
            
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in {self.config_path}: {e}")
        except Exception as e:
            raise ValueError(f"Error loading market regimes config: {e}")
    
    def detect_regime(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect active market regime from Market Thermometer data.
        
        Args:
            market_data: Output from MacroAnalyzer.get_market_thermometer()
                Expected structure:
                {
                    'shiller_pe': {'value': float, 'level': int, 'zone': str, 'status': str},
                    'fear_greed': {'value': float, 'level': int, 'zone': str, 'status': str},
                    'vix': {'value': float, 'level': int, 'zone': str, 'status': str},
                    'buffett_us': {'value': float, 'level': int, 'zone': str, 'status': str},
                    'buffett_china': {'value': float, 'level': int, 'zone': str, 'status': str},
                    'buffett_japan': {'value': float, 'level': int, 'zone': str, 'status': str},
                    'buffett_europe': {'value': float, 'level': int, 'zone': str, 'status': str},
                    'last_updated': str
                }
        
        Returns:
            Dictionary with regime information:
            {
                'regime_name': str,
                'regime_name_cn': str,
                'description': str,
                'description_cn': str,
                'priority': int,
                'matched_conditions': dict,
                'dynamic_targets': dict or None,
                'strategic_recommendations': list[dict],
                'detection_timestamp': str,
                'market_data_snapshot': dict
            }
        """
        self.logger.info("=" * 80)
        self.logger.info("Detecting market regime...")
        self.logger.info("=" * 80)
        
        # Log current market indicators
        self.logger.info("Current Market Indicators:")
        for indicator in ['shiller_pe', 'fear_greed', 'buffett_us', 'buffett_china']:
            if indicator in market_data and market_data[indicator].get('value') is not None:
                data = market_data[indicator]
                self.logger.info(f"  {indicator}: {data['value']:.1f} ({data.get('zone', 'Unknown')})")
        
        # Iterate through regimes in priority order
        for regime in self.regimes:
            self.logger.debug(f"Checking regime: {regime['name']} (Priority {regime['priority']})")
            
            conditions_met, matched_conditions = self._check_regime_conditions(regime, market_data)
            
            if conditions_met:
                self.logger.info(f"✅ MATCH: {regime['name']} ({regime['name_cn']})")
                self.logger.info(f"   Matched conditions: {matched_conditions}")
                
                return self._build_regime_output(regime, matched_conditions, market_data)
        
        # Should never reach here due to default regime, but handle gracefully
        self.logger.warning("No regime matched (unexpected) - returning default regime")
        default_regime = next((r for r in self.regimes if r.get('conditions', {}).get('default')), self.regimes[-1])
        return self._build_regime_output(default_regime, {'default': True}, market_data)
    
    def _check_regime_conditions(self, regime: Dict, market_data: Dict) -> Tuple[bool, Dict]:
        """
        Check if all conditions for a regime are satisfied.
        
        Args:
            regime: Regime configuration dictionary
            market_data: Market indicator data
        
        Returns:
            Tuple of (conditions_met: bool, matched_conditions: dict)
        """
        conditions = regime.get('conditions', {})
        matched_conditions = {}
        
        # Handle default regime (always matches)
        if conditions.get('default'):
            return (True, {'default': True})
        
        # Check each condition group
        for condition_key, condition_spec in conditions.items():
            if condition_key == 'default':
                continue
            
            # Handle special condition types
            if condition_key == 'valuation_or':
                # OR logic: at least ONE condition must be true
                is_met, details = self._check_or_condition(condition_spec, market_data)
                if not is_met:
                    return (False, {})
                matched_conditions[condition_key] = details
                
            elif condition_key == 'regional_divergence':
                # AND logic: BOTH conditions must be true
                is_met, details = self._check_and_condition(condition_spec, market_data)
                if not is_met:
                    return (False, {})
                matched_conditions[condition_key] = details
                
            else:
                # Standard indicator condition (min_value, max_value)
                is_met, details = self._check_indicator_condition(condition_key, condition_spec, market_data)
                if not is_met:
                    return (False, {})
                matched_conditions[condition_key] = details
        
        return (True, matched_conditions)
    
    def _check_or_condition(self, condition_spec: Dict, market_data: Dict) -> Tuple[bool, Dict]:
        """
        Check OR logic condition: at least ONE sub-condition must be true.
        
        Args:
            condition_spec: Dictionary with indicator conditions
            market_data: Market indicator data
            
        Returns:
            Tuple of (is_met: bool, details: dict)
        """
        details = {}
        any_met = False
        
        for indicator, spec in condition_spec.items():
            is_met, indicator_details = self._check_indicator_condition(indicator, spec, market_data)
            details[indicator] = indicator_details
            if is_met:
                any_met = True
        
        return (any_met, details)
    
    def _check_and_condition(self, condition_spec: Dict, market_data: Dict) -> Tuple[bool, Dict]:
        """
        Check AND logic condition: ALL sub-conditions must be true.
        
        Args:
            condition_spec: Dictionary with indicator conditions
            market_data: Market indicator data
            
        Returns:
            Tuple of (is_met: bool, details: dict)
        """
        details = {}
        all_met = True
        
        for indicator, spec in condition_spec.items():
            is_met, indicator_details = self._check_indicator_condition(indicator, spec, market_data)
            details[indicator] = indicator_details
            if not is_met:
                all_met = False
        
        return (all_met, details)
    
    def _check_indicator_condition(
        self, 
        indicator: str, 
        spec: Dict, 
        market_data: Dict
    ) -> Tuple[bool, Dict]:
        """
        Check a single indicator condition (min_value, max_value).
        
        Args:
            indicator: Indicator name (e.g., 'shiller_pe', 'fear_greed')
            spec: Condition specification with min_value and/or max_value
            market_data: Market indicator data
            
        Returns:
            Tuple of (is_met: bool, details: dict)
        """
        if indicator not in market_data:
            self.logger.warning(f"Indicator {indicator} not found in market data")
            return (False, {'error': 'indicator_missing'})
        
        indicator_data = market_data[indicator]
        value = indicator_data.get('value')
        
        # Handle missing or error values
        if value is None or indicator_data.get('status') == 'error':
            self.logger.warning(f"Indicator {indicator} has no value or error status")
            return (False, {'error': 'no_value', 'status': indicator_data.get('status')})
        
        # Check min_value condition
        if 'min_value' in spec:
            min_value = spec['min_value']
            if value < min_value:
                return (False, {'value': value, 'min_value': min_value, 'met': False})
        
        # Check max_value condition
        if 'max_value' in spec:
            max_value = spec['max_value']
            if value > max_value:
                return (False, {'value': value, 'max_value': max_value, 'met': False})
        
        # All conditions met
        details = {'value': value, 'met': True}
        if 'min_value' in spec:
            details['min_value'] = spec['min_value']
        if 'max_value' in spec:
            details['max_value'] = spec['max_value']
        
        return (True, details)
    
    def _build_regime_output(
        self, 
        regime: Dict, 
        matched_conditions: Dict, 
        market_data: Dict
    ) -> Dict[str, Any]:
        """
        Build the output dictionary for a matched regime.
        
        Args:
            regime: Matched regime configuration
            matched_conditions: Conditions that triggered this regime
            market_data: Market indicator data snapshot
            
        Returns:
            Complete regime output dictionary
        """
        return {
            'regime_name': regime['name'],
            'regime_name_cn': regime['name_cn'],
            'description': regime.get('description', ''),
            'description_cn': regime.get('description_cn', ''),
            'priority': regime['priority'],
            'matched_conditions': matched_conditions,
            'matched_conditions': matched_conditions,
            'target_modifiers': regime.get('target_modifiers'),
            'dynamic_targets': regime.get('dynamic_targets'), # Kept for backward compatibility if needed
            'strategic_recommendations': regime.get('strategic_recommendations', []),
            'detection_timestamp': datetime.now().isoformat(),
            'market_data_snapshot': {
                'shiller_pe': market_data.get('shiller_pe', {}).get('value'),
                'fear_greed': market_data.get('fear_greed', {}).get('value'),
                'buffett_us': market_data.get('buffett_us', {}).get('value'),
                'buffett_china': market_data.get('buffett_china', {}).get('value'),
                'last_updated': market_data.get('last_updated')
            }
        }


# Convenience function for direct usage
def detect_market_regime(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to detect market regime.
    
    Args:
        market_data: Market thermometer data from MacroAnalyzer
        
    Returns:
        Detected regime information
    """
    detector = IndicatorRegimeDetector()
    return detector.detect_regime(market_data)
