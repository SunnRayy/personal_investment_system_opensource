"""RSU Monitor Module

Monitors RSU vesting schedules and generates actionable alerts based on
upcoming or recent vesting events.

Author: Personal Investment System
Date: 2025-10-12
"""

import os
import yaml
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class RSUMonitor:
    """
    RSU (Restricted Stock Unit) vesting schedule monitor.
    
    Loads vesting schedule from YAML configuration and generates alerts
    for actionable events based on vesting dates.
    """
    
    def __init__(self, config_path: str = 'config/rsu_schedule.yaml'):
        """
        Initialize RSU Monitor with vesting schedule configuration.
        
        Args:
            config_path: Path to RSU schedule YAML file
        """
        self.config_path = config_path
        self.vesting_events = []
        self.logger = logging.getLogger(__name__)
        
        self._load_schedule()
    
    def _load_schedule(self) -> None:
        """Load RSU vesting schedule from YAML configuration."""
        if not os.path.exists(self.config_path):
            self.logger.warning(f"RSU schedule file not found: {self.config_path}")
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            self.vesting_events = config.get('vesting_events', [])
            
            # Convert string dates to datetime objects
            for event in self.vesting_events:
                if 'vesting_date' in event and isinstance(event['vesting_date'], str):
                    event['vesting_date'] = datetime.strptime(event['vesting_date'], '%Y-%m-%d').date()
            
            self.logger.info(f"Loaded {len(self.vesting_events)} RSU vesting events from {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Error loading RSU schedule: {e}")
            self.vesting_events = []
    
    def get_actionable_alerts(self, 
                            lookback_days: int = 30, 
                            lookahead_days: int = 30) -> List[Dict[str, Any]]:
        """
        Get list of actionable RSU vesting alerts.
        
        Identifies vesting events that:
        - Have occurred within the last `lookback_days` days (recent vests)
        - Will occur within the next `lookahead_days` days (upcoming vests)
        
        Args:
            lookback_days: Number of days to look back for recent vests
            lookahead_days: Number of days to look ahead for upcoming vests
            
        Returns:
            List of alert dictionaries, each containing:
                - vesting_date: Date of vesting
                - shares: Number of shares
                - asset_id: Asset identifier
                - plan: Planned action
                - status: 'vested' or 'upcoming'
                - days_ago: Days since vesting (negative if upcoming)
        """
        today = datetime.now().date()
        alerts = []
        
        for event in self.vesting_events:
            vesting_date = event.get('vesting_date')
            if not vesting_date:
                continue
            
            # Calculate days difference
            days_diff = (today - vesting_date).days
            
            # Check if within alert window
            is_recent_vest = 0 <= days_diff <= lookback_days
            is_upcoming_vest = -lookahead_days <= days_diff < 0
            
            if is_recent_vest or is_upcoming_vest:
                alert = {
                    'vesting_date': vesting_date,
                    'shares': event.get('shares', 0),
                    'asset_id': event.get('asset_id', 'Unknown'),
                    'plan': event.get('plan', 'No plan specified'),
                    'status': 'vested' if days_diff >= 0 else 'upcoming',
                    'days_ago': days_diff
                }
                alerts.append(alert)
        
        # Sort by vesting date (most recent/nearest first)
        alerts.sort(key=lambda x: abs(x['days_ago']))
        
        return alerts
    
    def get_all_events(self) -> List[Dict[str, Any]]:
        """
        Get all RSU vesting events from the schedule.
        
        Returns:
            List of all vesting events
        """
        return self.vesting_events.copy()
    
    def get_upcoming_vests_count(self, days: int = 90) -> int:
        """
        Count upcoming vests within specified number of days.
        
        Args:
            days: Number of days to look ahead
            
        Returns:
            Count of upcoming vests
        """
        today = datetime.now().date()
        count = 0
        
        for event in self.vesting_events:
            vesting_date = event.get('vesting_date')
            if vesting_date and 0 <= (vesting_date - today).days <= days:
                count += 1
        
        return count
