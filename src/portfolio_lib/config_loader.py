# portfolio_lib/config_loader.py
"""
Configuration loader module.

Provides functions for loading configuration from YAML files.
The main function `load_config` is designed to be called with specific paths
and returns separate dictionaries for settings and taxonomy.
"""

import os
import yaml
from typing import Dict, Any, Tuple, Optional

# --- Helper Function ---

def load_yaml(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Load a YAML file and return its contents as a dictionary.

    Args:
        file_path: Absolute path to the YAML file.

    Returns:
        Dictionary containing the YAML file contents, or None if loading fails.

    Raises:
        FileNotFoundError: If the file doesn't exist (caught internally).
        yaml.YAMLError: If the file contains invalid YAML (caught internally).
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if not isinstance(data, dict):
                 print(f"Warning: YAML file did not load as a dictionary: {file_path}")
                 return None
            return data
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {file_path}")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file {file_path}: {str(e)}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred loading YAML {file_path}: {e}")
        return None

# --- Main Loading Function ---

def load_settings_config(settings_path: str) -> Optional[Dict[str, Any]]:
    """
    Loads configuration settings from the specified YAML file path.

    Args:
        settings_path (str): Absolute path to the settings YAML file.

    Returns:
        Dictionary containing the settings data, or None if loading fails.
    """
    print(f"Attempting to load settings from: {settings_path}")
    settings_data = load_yaml(settings_path)
    if settings_data is not None:
        print("Settings loaded successfully.")
    else:
        print("Failed to load settings.")
    return settings_data

def load_asset_taxonomy_config(taxonomy_path: str) -> Optional[Dict[str, Any]]:
    """
    Loads asset taxonomy from the specified YAML file path.

    Args:
        taxonomy_path (str): Absolute path to the asset taxonomy YAML file.

    Returns:
        Dictionary containing the taxonomy data, or None if loading fails.
    """
    print(f"Attempting to load taxonomy from: {taxonomy_path}")
    taxonomy_data = load_yaml(taxonomy_path)
    if taxonomy_data is not None:
        print("Asset taxonomy loaded successfully.")
    else:
        print("Failed to load asset taxonomy.")
    return taxonomy_data

def load_config(
    settings_path: str = 'config/settings.yaml',
    taxonomy_path: str = 'config/asset_taxonomy.yaml'
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Loads configuration settings and asset taxonomy from specified YAML file paths.

    Determines the absolute paths based on the location of this script within
    the project structure.

    Args:
        settings_path (str): Relative path from the project root
                             (e.g., 'personal_portfolio_analyzer') to the settings YAML file.
        taxonomy_path (str): Relative path from the project root
                             to the asset taxonomy YAML file.

    Returns:
        tuple: A tuple containing two dictionaries: (settings_data, taxonomy_data).
               Returns (None, None) if loading of either file fails.
    """
    # Determine project root based on this file's location
    # This file is in src/portfolio_lib/, so we need to go up two levels to get to project root
    current_dir = os.path.dirname(os.path.abspath(__file__))  # src/portfolio_lib/
    src_dir = os.path.dirname(current_dir)  # src/
    project_root = os.path.dirname(src_dir)  # project root

    # Construct absolute paths
    abs_settings_path = os.path.join(project_root, settings_path)
    abs_taxonomy_path = os.path.join(project_root, taxonomy_path)

    print(f"Attempting to load settings from: {abs_settings_path}")
    print(f"Attempting to load taxonomy from: {abs_taxonomy_path}")

    settings_data = load_yaml(abs_settings_path)
    taxonomy_data = load_yaml(abs_taxonomy_path)

    if settings_data is not None:
        print("Settings loaded successfully.")
    else:
        print("Failed to load settings.")

    if taxonomy_data is not None:
        print("Asset taxonomy loaded successfully.")
    else:
        print("Failed to load asset taxonomy.")

    # The check 'if settings and taxonomy:' in the notebook will handle
    # cases where one or both are None.
    return settings_data, taxonomy_data


def load_single_config(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Load a single configuration file from an absolute path.
    
    Args:
        file_path: Absolute path to the YAML configuration file.
        
    Returns:
        Dictionary containing the configuration data, or None if loading fails.
    """
    return load_yaml(file_path)


# --- Potentially Obsolete Helper Functions (kept for reference/internal use) ---

def get_config_path(file_name: str) -> str:
    """
    Get the full path to a configuration file relative to this script's location.
    Note: This file is in src/portfolio_lib/, so config is two levels up.

    Args:
        file_name: The name of the configuration file (e.g., 'settings.yaml').

    Returns:
        The calculated full path to the configuration file.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))  # src/portfolio_lib/
    src_dir = os.path.dirname(current_dir)  # src/
    project_root = os.path.dirname(src_dir)  # project root
    config_dir = os.path.join(project_root, 'config')
    return os.path.join(config_dir, file_name)

def load_asset_taxonomy() -> Optional[Dict[str, Any]]:
    """
    Loads the asset taxonomy configuration using the relative path logic.
    Prefer calling the main `load_config` function instead.

    Returns:
        Dictionary containing the asset taxonomy configuration, or None on failure.
    """
    file_path = get_config_path('asset_taxonomy.yaml')
    return load_yaml(file_path) # load_yaml now expects absolute path, adjust if using this

def load_settings() -> Optional[Dict[str, Any]]:
    """
    Loads the application settings configuration using the relative path logic.
    Prefer calling the main `load_config` function instead.

    Returns:
        Dictionary containing the application settings configuration, or None on failure.
    """
    file_path = get_config_path('settings.yaml')
    return load_yaml(file_path) # load_yaml now expects absolute path, adjust if using this

