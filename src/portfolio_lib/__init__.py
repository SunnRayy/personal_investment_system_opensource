# portfolio_lib/__init__.py
print("Initializing portfolio_lib package...") # Optional: for debug

# Import necessary functions/classes to make them available at the package level
from .config_loader import load_config

# Correct the function name being imported here:
from .core.asset_mapper import (
    initialize_mapper_taxonomy, # <-- Corrected name
    extract_and_map_holdings,
    map_assets_to_standardized_classes,
    create_asset_class_mapper # Also good to expose this if needed directly
)

# Phase 6: System Unification - Holdings Calculator & Price Service
from .holdings_calculator import HoldingsCalculator
from .price_service import PriceService

# You can add other key imports from other modules here as needed
# Example:
# from .core.mpt import AssetAllocationModel
# from .visualization.plotter import PortfolioVisualizer
# from .analysis.engine import PortfolioAnalysisEngine

__all__ = [
    'load_config',
    'initialize_mapper_taxonomy',
    'extract_and_map_holdings',
    'map_assets_to_standardized_classes',
    'create_asset_class_mapper',
    'HoldingsCalculator',
    'PriceService',
]

print("portfolio_lib package initialized.")

