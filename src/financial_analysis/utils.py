import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd
import platform
import os
import logging
import yaml # <-- Import YAML library

# Configure logging for utility functions
logger = logging.getLogger(__name__)

# --- Currency Formatting ---

def currency_formatter(x, pos):
    """
    Formats a number into a currency string (e.g., 1.2K, 3.5M, 500).

    Args:
        x (float): The number to format.
        pos: The position (required by Matplotlib FuncFormatter, often unused).

    Returns:
        str: The formatted currency string.
    """
    if pd.isna(x): # Now pd is defined
        return "" # Handle NaN values gracefully
    if abs(x) >= 1e6:
        return f'{x/1e6:.1f}M'
    elif abs(x) >= 1e3:
        return f'{x/1e3:.1f}K'
    else:
        return f'{x:.0f}'

# Create a reusable FuncFormatter instance
CURRENCY_FORMAT = FuncFormatter(currency_formatter)

# Add this new function to your utils.py
def format_currency(value, currency_symbol='¥', decimals=2):
    """
    Formats a numerical value into a standard currency string.
    Example: 12345.67 -> "¥12,345.67"

    Args:
        value: The number to format.
        currency_symbol (str): The currency symbol to prepend.
        decimals (int): The number of decimal places.

    Returns:
        str: The formatted currency string, or an empty string for invalid input.
    """
    if value is None or pd.isna(value):  # pd.isna handles None, np.nan, etc.
        return ""
    try:
        return f"{currency_symbol}{value:,.{decimals}f}"
    except (TypeError, ValueError):
        # Fallback for any unexpected type that can't be formatted
        return str(value)

# --- Plotting Font Setup ---

def setup_chinese_font():
    """
    Attempts to find and set a suitable Chinese font for Matplotlib plots.
    Sets fallback font if no preferred Chinese font is found.
    Configures Matplotlib parameters for font and minus sign display.
    """
    os_type = platform.system()
    chinese_font = None

    if os_type == "Windows":
        # Common Chinese fonts on Windows
        preferred_fonts = ['SimHei', 'Microsoft YaHei', 'DengXian']
    elif os_type == "Darwin": # macOS
        # Common Chinese fonts on macOS
        preferred_fonts = ['Heiti TC', 'PingFang TC', 'Songti SC', 'STHeiti']
    else: # Linux
        # Common Chinese fonts on Linux (may need installation)
        preferred_fonts = ['WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'Source Han Sans SC']

    # Add a generic fallback
    preferred_fonts.append('Arial Unicode MS') # Often available cross-platform

    installed_fonts = {f.name for f in fm.fontManager.ttflist}
    logger.debug(f"Installed fonts sample: {list(installed_fonts)[:10]}...")

    for font in preferred_fonts:
        if font in installed_fonts:
            chinese_font = font
            break

    if not chinese_font:
        logger.warning(f"⚠️ No preferred Chinese font found from {preferred_fonts}. Charts might not display Chinese characters correctly. Falling back to default sans-serif.")
        # Let Matplotlib use its default sans-serif font
        plt.rcParams['font.family'] = 'sans-serif'
    else:
        logger.info(f"✅ Using Chinese font: {chinese_font}")
        plt.rcParams['font.family'] = chinese_font

    # Ensure correct display of minus signs with Chinese fonts
    plt.rcParams['axes.unicode_minus'] = False
    logger.info("Matplotlib font settings applied.")


# --- NEW: Helper function to load asset taxonomy ---
def load_asset_taxonomy(config_dir: str) -> dict:
    """
    Loads asset taxonomy configuration from the YAML file.

    Args:
        config_dir: Path to the directory containing the asset_taxonomy.yaml file.

    Returns:
        A dictionary containing the loaded taxonomy data, or an empty dictionary if loading fails.
        Includes a pre-calculated '_sub_to_top_level' mapping.
    """
    taxonomy_path = os.path.join(config_dir, 'asset_taxonomy.yaml')
    logger.info(f"Attempting to load asset taxonomy from: {taxonomy_path}")
    if not os.path.exists(taxonomy_path):
        logger.error(f"Asset taxonomy file not found at: {taxonomy_path}")
        return {}

    try:
        with open(taxonomy_path, 'r', encoding='utf-8') as f:
            taxonomy_data = yaml.safe_load(f)
        logger.info("Asset taxonomy loaded successfully.")

        # Basic validation (check if key sections exist)
        required_keys = ['top_level_classes', 'sub_classes', 'asset_mapping', 'special_categories']
        if not all(key in taxonomy_data for key in required_keys):
             logger.warning(f"Asset taxonomy YAML seems incomplete. Missing one of: {required_keys}")
             # Continue anyway, but analysis might fail later

        # Build the sub_to_top_level mapping dynamically
        sub_to_top_level = {}
        if 'sub_classes' in taxonomy_data and isinstance(taxonomy_data['sub_classes'], dict):
             for top_level, sub_list in taxonomy_data['sub_classes'].items():
                  if isinstance(sub_list, list):
                       for sub_class in sub_list:
                            sub_to_top_level[sub_class] = top_level
        taxonomy_data['_sub_to_top_level'] = sub_to_top_level # Store mapping for internal use

        return taxonomy_data
    except yaml.YAMLError as e:
        logger.error(f"Error parsing asset taxonomy YAML file: {e}", exc_info=True)
        return {}
    except Exception as e:
        logger.error(f"Error loading asset taxonomy file: {e}", exc_info=True)
        return {}

# --- NEW: Helper function to map asset class ---
def map_asset_class(holdings_df: pd.DataFrame, taxonomy_data: dict) -> pd.DataFrame:
    """
    Adds 'Asset_Class' (top-level) column to the holdings DataFrame based on taxonomy mapping.
    Uses TaxonomyManager (DB-backed) for classification.

    Args:
        holdings_df: DataFrame with holdings data.
        taxonomy_data: Dictionary loaded from asset_taxonomy.yaml (used for sub->top mapping).

    Returns:
        The holdings DataFrame with an added 'Asset_Class' column.
    """
    if holdings_df is None or holdings_df.empty:
        logger.warning("Holdings DataFrame is empty, cannot map asset class.")
        return holdings_df
        
    # Import TaxonomyManager here to avoid circular imports if any
    from src.portfolio_lib.taxonomy_manager import TaxonomyManager
    
    # Initialize TaxonomyManager (loads DB rules by default)
    # We assume config path can be inferred or default
    tm = TaxonomyManager()
    
    sub_to_top_level = taxonomy_data.get('_sub_to_top_level', {})
    
    # Create a copy to avoid modifying the original DataFrame
    holdings_mapped = holdings_df.copy()
    
    # Identify columns
    asset_name_col = 'Asset_Name' if 'Asset_Name' in holdings_mapped.columns else None
    asset_type_col = 'Asset_Type_Raw' if 'Asset_Type_Raw' in holdings_mapped.columns else ('Asset_Type' if 'Asset_Type' in holdings_mapped.columns else None)
    
    # Function to classify a single row
    def classify_row(row):
        name = row.get(asset_name_col, '') if asset_name_col else ''
        atype = row.get(asset_type_col, 'Unknown') if asset_type_col else 'Unknown'
        
        # Get Sub-Class (Tag) from TaxonomyManager (DB rules)
        sub_class = tm.get_asset_tag(str(name), str(atype))
        
        if sub_class:
            # Map Sub-Class to Top-Level Class
            return sub_to_top_level.get(sub_class, 'Unknown')
        return 'Unknown'

    # Apply classification
    logger.info("Classifying assets using TaxonomyManager (DB Rules)...")
    holdings_mapped['Asset_Class'] = holdings_mapped.apply(classify_row, axis=1)
    
    # Log results
    unknown_count = (holdings_mapped['Asset_Class'] == 'Unknown').sum()
    if unknown_count > 0:
        logger.warning(f"{unknown_count} assets could not be mapped and are assigned 'Unknown' class.")
    else:
        logger.info("All assets successfully mapped.")

    return holdings_mapped
