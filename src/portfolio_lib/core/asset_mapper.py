# portfolio_lib/core/asset_mapper.py
"""
Asset classification and mapping module.

Handles mapping raw asset names to standardized asset classes (both top-level
and sub-level) based on a provided taxonomy configuration.
"""

import pandas as pd
import numpy as np # <--- Import NumPy
from typing import Dict, List, Tuple, Callable, Any, Optional, Set

# Module-level variable to store the loaded taxonomy
_TAXONOMY: Optional[Dict[str, Any]] = None
# Module-level caches for mapping results
_memo_sub_class: Dict[str, str] = {}
_memo_top_class: Dict[str, str] = {}


# --- Taxonomy Initialization ---

def initialize_mapper_taxonomy(taxonomy_data: Dict[str, Any]):
    """
    Initializes the module-level taxonomy configuration and clears caches.

    Args:
        taxonomy_data: The loaded asset taxonomy dictionary.
    """
    global _TAXONOMY, _memo_sub_class, _memo_top_class
    if not isinstance(taxonomy_data, dict):
        raise TypeError("taxonomy_data must be a dictionary.")
    _TAXONOMY = taxonomy_data
    _memo_sub_class.clear()
    _memo_top_class.clear()
    required_keys = ['asset_mapping', 'pattern_mapping', 'special_categories',
                     'sub_classes', 'top_level_classes']
    if not all(key in _TAXONOMY for key in required_keys):
        print("Warning: Taxonomy data might be missing some required keys.")
    print("Asset taxonomy initialized successfully in asset_mapper.")

def _get_taxonomy() -> Dict[str, Any]:
    """Internal helper to safely access the initialized taxonomy."""
    if _TAXONOMY is None:
        raise ValueError(
            "Asset taxonomy has not been initialized. "
            "Call initialize_mapper_taxonomy(loaded_taxonomy_data) first."
        )
    return _TAXONOMY

# --- Internal Mapping Logic Functions ---
# (Keep _map_asset_to_sub_class_internal and _map_asset_to_top_class_internal as is - ID: asset_mapper_py_v3)
def _map_asset_to_sub_class_internal(asset_name: str) -> str:
    global _memo_sub_class
    if asset_name in _memo_sub_class:
        return _memo_sub_class[asset_name]
    taxonomy = _get_taxonomy()
    asset_mapping = taxonomy.get('asset_mapping', {})
    pattern_mapping = taxonomy.get('pattern_mapping', {})
    if asset_name in asset_mapping:
        result = asset_mapping[asset_name]
        _memo_sub_class[asset_name] = result
        return result
    for pattern, mapped_class in pattern_mapping.items():
        if pattern in asset_name:
            result = mapped_class
            _memo_sub_class[asset_name] = result
            return result
    result = '其他_子类'
    _memo_sub_class[asset_name] = result
    return result

def _map_asset_to_top_class_internal(asset_name: str) -> str:
    """
    Maps an asset name to its top-level asset class using the taxonomy.
    Uses memoization for performance.
    
    Args:
        asset_name: The asset name or ID to map.
        
    Returns:
        Top-level asset class name.
    """
    global _memo_top_class
    if asset_name in _memo_top_class:
        return _memo_top_class[asset_name]
    
    taxonomy = _get_taxonomy()
    special_categories = set(taxonomy.get('special_categories', []))
    sub_classes_map = taxonomy.get('sub_classes', {})
    top_level_classes = set(taxonomy.get('top_level_classes', []))
    
    # Default keyword-based mapping if sub-class mapping fails
    keyword_guesses: List[Tuple[str, str]] = taxonomy.get('keyword_guesses', [
        ('股', '股票'), ('基金', '股票'), ('ETF', '股票'), ('RSU', '股票'),
        ('债', '固定收益'), ('理财', '固定收益'), ('养老金', '固定收益'), ('货币', '固定收益'),
        ('黄金', '商品'),
        ('现金', '现金'), ('存款', '现金'),
        ('房', '房地产'),
        ('保险', '保险')
    ])
    
    # Get the sub-class first
    sub_class = _map_asset_to_sub_class_internal(asset_name)
    
    # Special categories are directly used as top-level classes
    if sub_class in special_categories:
        result = sub_class
        _memo_top_class[asset_name] = result
        return result
    
    # If sub-class mapping failed, try keyword-based guessing
    if sub_class == '其他_子类':
        for keyword, guessed_class in keyword_guesses:
            if keyword in asset_name:
                if guessed_class in top_level_classes or guessed_class in special_categories:
                    result = guessed_class
                    _memo_top_class[asset_name] = result
                    return result
        
        # No keyword match found, use default
        result = '其他'
        _memo_top_class[asset_name] = result
        return result
    
    # Map sub-class to top-level class using the taxonomy structure
    for top_class, subs in sub_classes_map.items():
        if sub_class in subs:
            result = top_class
            _memo_top_class[asset_name] = result
            return result
    
    # If the sub-class is already a top-level class, use it directly
    if sub_class in top_level_classes:
        result = sub_class
        _memo_top_class[asset_name] = result
        return result
    
    # Fallback if no mapping found
    print(f"Warning: Sub-class '{sub_class}' (from asset '{asset_name}') not found in top-level or special categories. Classifying top-level as '其他'.")
    result = '其他'
    _memo_top_class[asset_name] = result
    return result


# --- Public Interface Functions ---

def create_asset_class_mapper() -> Tuple[Callable[[str], str], Callable[[str], str]]:
    """
    Creates and returns functions for mapping asset names to classes.
    Returns the internal mapping functions defined at the module level.
    """
    _get_taxonomy() # Ensure initialized
    return _map_asset_to_sub_class_internal, _map_asset_to_top_class_internal

# --- MODIFIED map_assets_to_standardized_classes ---
def map_assets_to_standardized_classes(
    raw_holdings: Dict[str, float],
    debug: bool = False
) -> Dict[str, Any]:
    """
    Maps raw asset names to standardized top-level AND sub-level classes.

    Aggregates values for each class type and provides detailed mapping info.
    Skips special categories, invalid values, and assets mapped to '其他'.

    Args:
        raw_holdings: Dictionary of raw asset names and their values.
        debug: If True, prints detailed logging during the mapping process.

    Returns:
        A dictionary containing:
        - 'top_level': {top_class: aggregated_value} for standard top-level classes.
        - 'sub_level': {sub_class: aggregated_value} for standard sub-level classes.
        - 'mapping_details': {'mapped_assets': [], 'skipped_assets': [], 'unmapped_assets': []}.
    """
    taxonomy = _get_taxonomy()
    map_to_sub_class, map_to_top_class = create_asset_class_mapper()
    special_categories: Set[str] = set(taxonomy.get('special_categories', []))

    # Initialize dictionaries for both levels
    mapped_holdings_top: Dict[str, float] = {}
    mapped_holdings_sub: Dict[str, float] = {} # <-- Added sub-level dictionary
    mapping_details: Dict[str, List[Tuple[Any, ...]]] = {
        'mapped_assets': [], # (asset, value, sub_class, top_class)
        'skipped_assets': [], # (asset, value, reason)
        'unmapped_assets': []  # (asset, value) -> mapped to '其他' top-level
    }

    if not isinstance(raw_holdings, dict):
        print("Error: raw_holdings must be a dictionary.")
        # Return the expected structure even on error
        return {'top_level': {}, 'sub_level': {}, 'mapping_details': mapping_details}

    for asset, value in raw_holdings.items():
        # Validate and convert value
        try:
            if pd.isna(value): numeric_value = 0.0
            else: numeric_value = float(value)
        except (ValueError, TypeError):
             mapping_details['skipped_assets'].append((asset, value, 'Invalid value type'))
             if debug: print(f"Skipping asset '{asset}': Invalid value type '{type(value)}'")
             continue

        # Skip non-positive values
        if numeric_value <= 0:
            mapping_details['skipped_assets'].append((asset, value, 'Invalid value (<= 0 or NaN)'))
            if debug and numeric_value == 0: print(f"Skipping asset '{asset}': Zero value")
            continue

        # Perform mapping
        sub_class = map_to_sub_class(asset)
        top_class = map_to_top_class(asset) # Top class derived from sub_class logic

        # Skip special categories (based on top_class result)
        if top_class in special_categories:
            mapping_details['skipped_assets'].append((asset, numeric_value, f'Special Category ({top_class})'))
            if debug: print(f"Skipping special category asset: '{asset}' ({numeric_value:,.0f}) - {top_class}")
            continue

        # Handle unmapped ('其他') assets - log but do not include in aggregations
        # Check both top and sub level results for 'Other' status
        if top_class == '其他' or sub_class == '其他_子类':
            mapping_details['unmapped_assets'].append((asset, numeric_value))
            if debug: print(f"Warning: Could not map '{asset}' ({numeric_value:,.0f}) to standard class. Top='{top_class}', Sub='{sub_class}'. Categorized as '其他'.")
            continue

        # --- Add to aggregations ---
        mapping_details['mapped_assets'].append((asset, numeric_value, sub_class, top_class))
        # Aggregate by Top Level
        mapped_holdings_top[top_class] = mapped_holdings_top.get(top_class, 0.0) + numeric_value
        # Aggregate by Sub Level
        mapped_holdings_sub[sub_class] = mapped_holdings_sub.get(sub_class, 0.0) + numeric_value # <-- Aggregate sub-level


    # --- Debug Summary (Optional) ---
    if debug:
        total_mapped_value_top = sum(mapped_holdings_top.values())
        total_mapped_value_sub = sum(mapped_holdings_sub.values()) # Should be the same
        skipped_count = len(mapping_details['skipped_assets'])
        unmapped_count = len(mapping_details['unmapped_assets'])
        mapped_count = len(mapping_details['mapped_assets'])

        print("\n--- Asset Mapping Debug Summary ---")
        print(f"Total raw assets processed: {len(raw_holdings)}")
        print(f"Assets mapped to standard classes: {mapped_count}")
        print(f"Assets skipped (special/invalid): {skipped_count}")
        print(f"Assets categorized as '其他' (unmapped): {unmapped_count}")

        # Display details of skipped/unmapped assets if any
        if skipped_count > 0:
            print("\nSkipped Assets:")
            for a, v, r in mapping_details['skipped_assets'][:10]: print(f"  - '{a}' ({v}): {r}")
            if skipped_count > 10: print(f"    ... and {skipped_count - 10} more")
        if unmapped_count > 0:
            print("\nUnmapped Assets (categorized as '其他'):")
            for a, v in mapping_details['unmapped_assets'][:10]: print(f"  - '{a}' ({v:,.0f})")
            if unmapped_count > 10: print(f"    ... and {unmapped_count - 10} more")

        # Print Top-Level Aggregation
        print(f"\nAggregated Holdings by Top-Level Class (Total Value: {total_mapped_value_top:,.0f}):")
        if total_mapped_value_top > 0:
            all_top_classes = taxonomy.get('top_level_classes', [])
            # Sort keys for consistent display
            for category in sorted(mapped_holdings_top.keys()):
                value = mapped_holdings_top[category]
                percentage = (value / total_mapped_value_top) * 100
                print(f"  {category}: {value:,.0f} ({percentage:.1f}%)")
        else:
            print("  No holdings mapped to standard top-level categories or total value is zero.")

        # Print Sub-Level Aggregation
        print(f"\nAggregated Holdings by Sub-Level Class (Total Value: {total_mapped_value_sub:,.0f}):")
        if total_mapped_value_sub > 0:
             # Sort keys for consistent display
            for category in sorted(mapped_holdings_sub.keys()):
                value = mapped_holdings_sub[category]
                # Calculate percentage based on total_top for consistency
                percentage = (value / total_mapped_value_top) * 100
                print(f"  {category}: {value:,.0f} ({percentage:.1f}%)")
        else:
             print("  No holdings mapped to standard sub-level categories or total value is zero.")

        print("--- End Asset Mapping Debug Summary ---")
    # --- End Debug Summary ---

    # Return the new structure
    return {
        'top_level': mapped_holdings_top,
        'sub_level': mapped_holdings_sub,
        'mapping_details': mapping_details
    }

# --- MODIFIED extract_and_map_holdings ---
def extract_and_map_holdings(
    balance_df: pd.DataFrame,
    debug: bool = False
) -> Dict[str, Any]: # Return type changed to Any to accommodate the new structure
    """
    Extracts current holdings from the latest balance sheet data and maps them
    to standardized top-level AND sub-level asset classes.

    Args:
        balance_df: DataFrame containing balance sheet data (time series).
                    Assumes index is datetime-like and rows are sorted chronologically.
        debug: If True, prints detailed logging during extraction and mapping.

    Returns:
        A dictionary containing 'top_level' holdings, 'sub_level' holdings,
        and 'mapping_details'. Returns empty dicts if extraction fails.
        Example: {'top_level': {...}, 'sub_level': {...}, 'mapping_details': {...}}
    """
    taxonomy = _get_taxonomy() # Ensure taxonomy is loaded

    empty_result = {'top_level': {}, 'sub_level': {}, 'mapping_details': {
        'mapped_assets': [], 'skipped_assets': [], 'unmapped_assets': []
    }}

    if not isinstance(balance_df, pd.DataFrame) or balance_df.empty:
        print("Error: Balance sheet DataFrame is empty or not a DataFrame.")
        return empty_result

    try:
        latest_data = balance_df.iloc[-1]
        latest_date = latest_data.name
    except IndexError:
        print("Error: Cannot get latest data from empty DataFrame.")
        return empty_result

    raw_holdings: Dict[str, float] = {}
    # Use keywords from taxonomy if defined, otherwise use default
    asset_keywords: List[str] = taxonomy.get('asset_identification_keywords',
        ['投资资产', '固定资产', 'RMB', '美元', '存款', '现金', 'Private_Equity_Investment_A', '股票', '基金', '理财', '黄金', '保险', '房产']
    )

    if debug:
        print(f"\n--- Extracting Holdings from Latest Balance Sheet ({latest_date}) ---")
        print(f"Identifying assets using keywords: {', '.join(asset_keywords)}")

    for col in balance_df.columns:
        if any(keyword in col for keyword in asset_keywords):
            value = latest_data.get(col) # Use .get() for safety
            # Store raw value, mapping function will handle conversion/filtering
            # Check for NaN explicitly here before adding to raw_holdings
            if pd.notna(value):
                raw_holdings[col] = value
            # else: # Optional: Debugging for NaN values found
            #     if debug: print(f"Debug: Skipping NaN value for column '{col}'")


    if not raw_holdings:
         print("Warning: No raw asset holdings could be extracted based on keywords.")
         return empty_result

    if debug:
        # Calculate raw total carefully, handling potential non-float values initially
        # Use np.number for robust check
        raw_total = sum(float(v) for v in raw_holdings.values() if pd.notna(v) and isinstance(v, (int, float, np.number)))
        print(f"Extracted {len(raw_holdings)} raw assets candidates with total raw numeric value: {raw_total:,.2f}")

    # Use the enhanced mapping function which now returns the nested structure
    mapping_result = map_assets_to_standardized_classes(raw_holdings, debug=debug)

    return mapping_result # Return the full result dictionary

# --- Enhanced Asset Mapping Functions for Holdings DataFrame ---

def extract_and_map_holdings_from_df(
    holdings_df: pd.DataFrame,
    debug: bool = False
) -> Dict[str, Any]:
    """
    Maps assets from a holdings DataFrame (from data_manager) to asset classes.

    Args:
        holdings_df: A MultiIndex DataFrame with (Snapshot_Date, Asset_ID/Ticker) as index
                    and columns including Market_Value_CNY, Asset_Type_Raw, etc.
        debug: Whether to print debugging information.

    Returns:
        A dictionary containing mapped holdings information:
        - 'top_level': Dict mapping top-level categories to total values.
        - 'sub_level': Dict mapping sub-level categories to total values.
        - 'mapping_details': Dict with lists of mapped, unmapped, and skipped assets.
    """
    if holdings_df is None or holdings_df.empty:
        print("Error: Empty or None holdings DataFrame provided.")
        return {'top_level': {}, 'sub_level': {}, 'mapping_details': {
            'mapped_assets': [], 'unmapped_assets': [], 'skipped_assets': []
        }}

    # Ensure taxonomy is initialized
    _get_taxonomy()

    if debug:
        print("\n--- Extracting and Mapping Holdings from DataFrame ---")
        print(f"Input holdings_df shape: {holdings_df.shape}")
        if isinstance(holdings_df.index, pd.MultiIndex):
            print(f"Holdings MultiIndex levels: {holdings_df.index.names}")
        print(f"Holdings Columns: {holdings_df.columns.tolist()}")

    # Check if it's a MultiIndex DataFrame and get the latest snapshot
    if not isinstance(holdings_df.index, pd.MultiIndex):
        print("Warning: Expected a MultiIndex DataFrame for holdings_df. Attempting to proceed.")
        latest_holdings = holdings_df.copy()
    else:
        # Get the latest snapshot date
        try:
            snapshot_dates = holdings_df.index.get_level_values('Snapshot_Date').unique()
            latest_date = max(snapshot_dates)
            if debug:
                print(f"Available snapshot dates: {snapshot_dates.tolist()}")
                print(f"Using latest snapshot date: {latest_date}")
            latest_holdings = holdings_df.xs(latest_date, level='Snapshot_Date')
        except Exception as e:
            print(f"Error extracting latest snapshot: {e}. Using all data.")
            latest_holdings = holdings_df.copy()

    # Initialize results
    top_level_holdings = {}
    sub_level_holdings = {}
    mapped_assets = []
    unmapped_assets = []
    skipped_assets = []

    # Process each asset in the holdings
    for idx, row in latest_holdings.iterrows():
        # In a MultiIndex, idx might be a tuple or a single value depending on how we've processed the DataFrame
        asset_id = idx if not isinstance(idx, tuple) else idx[0]  # Assumes Asset_ID is the first level after Snapshot_Date
        
        # Get asset information
        asset_name = row.get('Asset_Name', asset_id)  # Use Asset_Name if available, else use asset_id
        asset_type_raw = row.get('Asset_Type_Raw', '')
        market_value = row.get('Market_Value_CNY', 0.0)
        
        # Skip assets with no value or negative value (could be an error)
        if market_value <= 0:
            if debug:
                print(f"Skipping asset with no/negative value: {asset_id}, value: {market_value}")
            skipped_assets.append((asset_id, asset_name, 'No/negative value'))
            continue

        # Map to asset classes
        try:
            # Try to use asset_id for mapping first, then fall back to asset_name
            sub_class = _map_asset_to_sub_class_internal(asset_id)
            if sub_class == '其他_子类' and asset_name and asset_name != asset_id:
                sub_class = _map_asset_to_sub_class_internal(asset_name)
            
            top_class = _map_asset_to_top_class_internal(asset_id)
            if top_class == '其他资产_未映射' and asset_name and asset_name != asset_id:
                top_class = _map_asset_to_top_class_internal(asset_name)
            
            # Handle unmapped case
            if sub_class == '其他_子类' or top_class == '其他资产_未映射':
                unmapped_assets.append((asset_id, asset_name, market_value))
                if debug:
                    print(f"Unmapped asset: {asset_id} ('{asset_name}'), Type: {asset_type_raw}, Value: {market_value}")
            else:
                mapped_assets.append((asset_id, asset_name, sub_class, top_class, market_value))
                if debug:
                    print(f"Mapped asset: {asset_id} ('{asset_name}') -> {sub_class} -> {top_class}, Value: {market_value}")
            
            # Update running totals
            top_level_holdings[top_class] = top_level_holdings.get(top_class, 0) + market_value
            sub_level_holdings[sub_class] = sub_level_holdings.get(sub_class, 0) + market_value
            
        except Exception as e:
            print(f"Error mapping asset {asset_id}: {e}")
            unmapped_assets.append((asset_id, asset_name, market_value))

    # Print summary
    if debug:
        total_value = sum(top_level_holdings.values())
        print(f"\n--- Holdings Mapping Summary ---")
        print(f"Total holdings value: {total_value:,.2f}")
        print(f"Mapped {len(mapped_assets)} assets to {len(top_level_holdings)} top-level and {len(sub_level_holdings)} sub-level categories.")
        print(f"Unmapped assets: {len(unmapped_assets)}")
        print(f"Skipped assets: {len(skipped_assets)}")

    return {
        'top_level': top_level_holdings,
        'sub_level': sub_level_holdings,
        'mapping_details': {
            'mapped_assets': mapped_assets,
            'unmapped_assets': unmapped_assets,
            'skipped_assets': skipped_assets
        }
    }

# --- Function to map holdings from data_manager DataFrame ---
def extract_and_map_holdings_from_df(
    holdings_df: pd.DataFrame,
    debug: bool = False
) -> Dict[str, Any]:
    """
    Extracts and maps holdings from a holdings DataFrame obtained from data_manager.
    
    Args:
        holdings_df: DataFrame containing holdings data from data_manager.
        debug: If True, prints detailed logging during the mapping process.
        
    Returns:
        A dictionary containing:
        - 'top_level': {top_class: aggregated_value} for standard top-level classes.
        - 'sub_level': {sub_class: aggregated_value} for standard sub-level classes.
        - 'mapping_details': {'mapped_assets': [], 'skipped_assets': [], 'unmapped_assets': []}.
    """
    print("Extracting and mapping holdings from DataFrame...")
    
    # Initialize mapping details and result structure
    mapping_details = {
        'mapped_assets': [], # (asset_id, asset_name, value, sub_class, top_class)
        'skipped_assets': [], # (asset_id, asset_name, value, reason)
        'unmapped_assets': []  # (asset_id, asset_name, value) -> mapped to '其他' top-level
    }
    
    # Initialize dictionaries for both levels
    mapped_holdings_top = {}
    mapped_holdings_sub = {}
    
    # Check if DataFrame is empty or None
    if holdings_df is None or holdings_df.empty:
        print("Error: holdings_df is empty or None.")
        return {'top_level': {}, 'sub_level': {}, 'mapping_details': mapping_details}
    
    # Get the latest snapshot if we have a MultiIndex
    snapshot_dates = []
    try:
        if isinstance(holdings_df.index, pd.MultiIndex):
            # Extract snapshot dates from the MultiIndex
            snapshot_dates = holdings_df.index.get_level_values('Snapshot_Date').unique()
            if len(snapshot_dates) > 0:
                latest_date = max(snapshot_dates)
                print(f"Using latest snapshot date: {latest_date}")
                
                # Get holdings for the latest date
                holdings_snapshot = holdings_df.xs(latest_date, level='Snapshot_Date')
            else:
                print("No snapshot dates found in holdings_df.")
                return {'top_level': {}, 'sub_level': {}, 'mapping_details': mapping_details}
        else:
            # If not a MultiIndex, use the entire DataFrame
            holdings_snapshot = holdings_df
            print("Using entire holdings_df (not a MultiIndex).")
    except Exception as e:
        print(f"Error extracting snapshot from holdings_df: {e}")
        return {'top_level': {}, 'sub_level': {}, 'mapping_details': mapping_details}
    
    # Check required columns
    required_columns = ['Asset_ID', 'Market_Value_CNY']
    optional_columns = ['Asset_Name', 'Asset_Type']
    
    for col in required_columns:
        if col not in holdings_snapshot.columns and col not in holdings_snapshot.index.names:
            print(f"Error: Required column '{col}' not found in holdings_df.")
            return {'top_level': {}, 'sub_level': {}, 'mapping_details': mapping_details}
    
    # Process each holding
    skipped_assets = []
    unmapped_assets = []
    mapped_assets = []
    
    # Create asset mappers
    map_to_sub_class, map_to_top_class = create_asset_class_mapper()
    
    for idx, row in holdings_snapshot.iterrows():
        # Extract asset information based on DataFrame structure
        asset_id = idx if not isinstance(idx, tuple) else idx[0]  # Handle potential tuple index
        
        if 'Asset_ID' in row:
            asset_id = row['Asset_ID']
        
        asset_name = asset_id  # Default to ID if name not available
        if 'Asset_Name' in row:
            asset_name = row['Asset_Name']
        
        # Extract market value
        market_value = None
        if 'Market_Value_CNY' in row:
            market_value = row['Market_Value_CNY']
        
        # Basic validation
        if market_value is None or pd.isna(market_value) or market_value <= 0:
            skipped_assets.append((asset_id, asset_name, 'No/negative value'))
            continue
        
        # Map to asset classes
        try:
            # Map to sub-class using asset_id
            sub_class = map_to_sub_class(asset_id)
            
            # Map to top-class using asset_id
            top_class = map_to_top_class(asset_id)
            
            # Validate - skip if mapped to '其他' (both levels)
            if top_class == '其他' and sub_class == '其他_子类':
                unmapped_assets.append((asset_id, asset_name, market_value))
                if debug:
                    print(f"Unmapped: {asset_id} ({asset_name}) = {market_value:,.0f} -> '其他'")
            else:
                mapped_assets.append((asset_id, asset_name, market_value, sub_class, top_class))
                
                # Add to top-level aggregation
                if top_class in mapped_holdings_top:
                    mapped_holdings_top[top_class] += market_value
                else:
                    mapped_holdings_top[top_class] = market_value
                
                # Add to sub-level aggregation
                if sub_class in mapped_holdings_sub:
                    mapped_holdings_sub[sub_class] += market_value
                else:
                    mapped_holdings_sub[sub_class] = market_value
                
                if debug:
                    print(f"Mapped: {asset_id} ({asset_name}) = {market_value:,.0f} -> {top_class} (via {sub_class})")
        
        except Exception as e:
            skipped_assets.append((asset_id, asset_name, f'Error: {e}'))
            if debug:
                print(f"Error mapping asset {asset_id} ({asset_name}): {e}")
    
    # Update mapping details
    mapping_details['mapped_assets'] = mapped_assets
    mapping_details['skipped_assets'] = skipped_assets
    mapping_details['unmapped_assets'] = unmapped_assets
    
    # Summary and logging
    if debug:
        total_mapped_value_top = sum(mapped_holdings_top.values())
        print(f"\n--- Mapping Summary ---")
        print(f"Holdings snapshot date(s): {[d.strftime('%Y-%m-%d') for d in snapshot_dates]}")
        mapped_count = len(mapping_details['mapped_assets'])
        print(f"Assets mapped to standard classes: {mapped_count}")
        print(f"Assets skipped: {len(skipped_assets)}")
        print(f"Assets unmapped (classified as '其他'): {len(unmapped_assets)}")
        
        if skipped_assets:
            print("\nSkipped Assets:")
            for asset_info in skipped_assets[:5]:  # Show first 5
                print(f"  {asset_info[0]} ({asset_info[1]}): {asset_info[2]}")
            if len(skipped_assets) > 5:
                print(f"  ... and {len(skipped_assets) - 5} more")
        
        if total_mapped_value_top > 0:
            print(f"\nTotal mapped value: {total_mapped_value_top:,.0f} CNY")
            print("\nTop-level asset allocation:")
            for asset_class, value in sorted(mapped_holdings_top.items(), key=lambda x: x[1], reverse=True):
                print(f"  {asset_class}: {value:,.0f} ({value / total_mapped_value_top:.1%})")
        else:
            print("No assets with positive values were mapped.")
    
    # Return results in the standard structure
    return {
        'top_level': mapped_holdings_top,
        'sub_level': mapped_holdings_sub,
        'mapping_details': mapping_details
    }

