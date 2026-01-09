"""
System state detection for first-run and demo mode handling.

This module provides detection of the current system state to enable:
- First-run onboarding flow for new installations
- Demo mode for exploring the system with sample data
- User data mode for normal operation with real data

Usage:
    from src.web_app.system_state import get_system_state, is_first_run, is_demo_mode
    
    if is_first_run():
        return redirect(url_for('onboarding.index'))
"""

import os
from enum import Enum
from pathlib import Path
from typing import Optional
import sqlite3
import logging

logger = logging.getLogger(__name__)


class SystemState(Enum):
    """Possible system states."""
    FIRST_RUN = "first_run"      # No data, fresh installation
    DEMO_MODE = "demo_mode"      # Running with demo data
    USER_DATA = "user_data"      # Real user data loaded
    MIXED_MODE = "mixed_mode"    # Demo data + some user data


class SystemStateManager:
    """Manages system state detection and transitions."""

    def __init__(
        self, 
        data_dir: Optional[str] = None, 
        db_path: Optional[str] = None
    ):
        """
        Initialize the state manager.
        
        Args:
            data_dir: Path to data directory. Uses DATA_DIR env var or 'data' as default.
            db_path: Path to database file. Uses DB_PATH env var or 'data/investment_system.db' as default.
        """
        self.data_dir = Path(data_dir or os.environ.get('DATA_DIR', 'data'))
        self.db_path = Path(db_path or os.environ.get('DB_PATH', 'data/investment_system.db'))
        self.user_uploads_dir = self.data_dir / 'user_uploads'
        self.demo_data_dir = self.data_dir / 'demo_source'

        # Cache state to avoid repeated file/database checks
        self._cached_state: Optional[SystemState] = None

    def detect_state(self, force_refresh: bool = False) -> SystemState:
        """
        Detect current system state.

        Args:
            force_refresh: If True, bypass cache and re-detect state.

        Returns:
            SystemState enum value indicating current state.
        """
        # Check environment override first (highest priority)
        env_state = os.environ.get('SYSTEM_STATE')
        if env_state:
            try:
                return SystemState(env_state)
            except ValueError:
                logger.warning(f"Invalid SYSTEM_STATE value: {env_state}")

        # Check demo mode flag
        if os.environ.get('DEMO_MODE', 'false').lower() == 'true':
            return SystemState.DEMO_MODE

        # Return cached if available
        if self._cached_state is not None and not force_refresh:
            return self._cached_state

        # Detect based on data
        has_user_data = self._has_user_data()
        has_db_data = self._has_database_data()

        if has_user_data or has_db_data:
            self._cached_state = SystemState.USER_DATA
        else:
            self._cached_state = SystemState.FIRST_RUN

        logger.info(f"System state detected: {self._cached_state.value}")
        return self._cached_state

    def _has_user_data(self) -> bool:
        """Check if user has uploaded any data files."""
        if not self.user_uploads_dir.exists():
            return False

        data_files = (
            list(self.user_uploads_dir.glob('*.csv')) +
            list(self.user_uploads_dir.glob('*.xlsx')) +
            list(self.user_uploads_dir.glob('*.xls'))
        )

        return len(data_files) > 0

    def _has_database_data(self) -> bool:
        """Check if database has user transactions."""
        if not self.db_path.exists():
            return False

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Check if transactions table exists and has data
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master
                WHERE type='table' AND name='transactions'
            """)
            has_table = cursor.fetchone()[0] > 0

            if has_table:
                cursor.execute("SELECT COUNT(*) FROM transactions LIMIT 1")
                has_data = cursor.fetchone()[0] > 0
            else:
                has_data = False

            conn.close()
            return has_data

        except Exception as e:
            logger.warning(f"Error checking database: {e}")
            return False

    def is_first_run(self) -> bool:
        """Check if this is the first run."""
        return self.detect_state() == SystemState.FIRST_RUN

    def is_demo_mode(self) -> bool:
        """Check if running in demo mode."""
        return self.detect_state() == SystemState.DEMO_MODE

    def has_demo_data(self) -> bool:
        """Check if demo data is available."""
        if not self.demo_data_dir.exists():
            return False
        
        # Check if directory has any files
        demo_files = list(self.demo_data_dir.glob('*'))
        return len(demo_files) > 0

    def enable_demo_mode(self):
        """Enable demo mode."""
        os.environ['DEMO_MODE'] = 'true'
        self._cached_state = SystemState.DEMO_MODE
        logger.info("Demo mode enabled")

    def disable_demo_mode(self):
        """Disable demo mode and re-detect state."""
        os.environ['DEMO_MODE'] = 'false'
        self._cached_state = None  # Force re-detection
        logger.info("Demo mode disabled")

    def clear_cache(self):
        """Clear cached state to force re-detection."""
        self._cached_state = None


# Global instance
_state_manager: Optional[SystemStateManager] = None


def get_state_manager() -> SystemStateManager:
    """Get or create the global state manager instance."""
    global _state_manager
    if _state_manager is None:
        _state_manager = SystemStateManager()
    return _state_manager


def get_system_state() -> SystemState:
    """
    Get current system state.
    
    Returns:
        SystemState enum value.
    """
    return get_state_manager().detect_state()


def is_first_run() -> bool:
    """
    Check if this is first run (no user data).
    
    Returns:
        True if no user data exists.
    """
    return get_state_manager().is_first_run()


def is_demo_mode() -> bool:
    """
    Check if running in demo mode.
    
    Returns:
        True if DEMO_MODE=true or system is in demo state.
    """
    return get_state_manager().is_demo_mode()


def has_demo_data() -> bool:
    """
    Check if demo data is available.
    
    Returns:
        True if demo data directory exists and has files.
    """
    return get_state_manager().has_demo_data()
