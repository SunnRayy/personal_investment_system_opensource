"""
Locale-aware configuration loader.

Loads YAML config files with locale suffix (e.g., asset_taxonomy.en.yaml).
Falls back to base file if locale-specific file doesn't exist.
"""

import os
from typing import Any, Dict, Optional

import yaml


class LocalizedConfigLoader:
    """Load configuration files with locale awareness."""
    
    def __init__(self, config_dir: str, locale: str = 'en'):
        self.config_dir = config_dir
        self.locale = locale
    
    def load(self, config_name: str) -> Dict[str, Any]:
        """
        Load a configuration file with locale fallback.
        
        Args:
            config_name: Base name without extension (e.g., 'asset_taxonomy')
        
        Returns:
            Loaded configuration dictionary
        
        Lookup order:
            1. config_name.{locale}.yaml (e.g., asset_taxonomy.en.yaml)
            2. config_name.yaml (fallback)
        """
        # 1. Try locales subdirectory
        locale_path_subdir = os.path.join(
            self.config_dir, 'locales', f"{config_name}.{self.locale}.yaml"
        )
        if os.path.exists(locale_path_subdir):
            return self._load_yaml(locale_path_subdir)

        # 2. Try same directory
        locale_path_flat = os.path.join(
            self.config_dir, f"{config_name}.{self.locale}.yaml"
        )
        if os.path.exists(locale_path_flat):
            return self._load_yaml(locale_path_flat)
        
        # 3. Fall back to base config
        base_path = os.path.join(self.config_dir, f"{config_name}.yaml")
        if os.path.exists(base_path):
            return self._load_yaml(base_path)
        
        raise FileNotFoundError(
            f"Config not found: {config_name}"
        )
    
    def _load_yaml(self, path: str) -> Dict[str, Any]:
        """Load and parse a YAML file."""
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def set_locale(self, locale: str) -> None:
        """Change the current locale."""
        self.locale = locale
