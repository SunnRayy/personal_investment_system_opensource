#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Asset Taxonomy Auto-Updater Script

This script helps automate the process of updating the asset_taxonomy.yaml file
by extracting unmapped assets from portfolio analysis logs and suggesting 
appropriate mappings based on name patterns.

Usage:
    python auto_update_taxonomy.py --log_file path/to/log_file.txt
    
Or run directly without arguments to analyze the console output manually:
    python auto_update_taxonomy.py
"""

import os
import re
import yaml
import argparse
import sys
from typing import Dict, List, Tuple, Set, Optional

# Default paths
DEFAULT_YAML_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    'config', 'asset_taxonomy.yaml'
)

# Regex patterns to extract unmapped assets from logs
UNMAPPED_PATTERN = r"Unmapped: (\S+) \(([^)]+)\) = ([0-9,.]+) -> '其他'"

# Pattern-based classification rules
CLASSIFICATION_RULES = [
    # Format: (pattern, sub_class, description)
    # Stock funds - domestic
    (r'指数', '国内股票ETF', '指数基金/Index Fund'),
    (r'沪深300|上证50|中证500|中证800|创业板', '国内股票ETF', 'Chinese Index Fund'),
    (r'股票', '国内股票ETF', '股票基金/Stock Fund'),
    (r'混合', '国内股票ETF', '混合型基金/Mixed Fund'),
    (r'增强', '国内股票ETF', '指数增强/Enhanced Index'),
    (r'价值|成长|红利', '国内股票ETF', '投资风格基金/Style Fund'),
    
    # Stock funds - international
    (r'QDII|海外|国际|全球', '美国股票ETF', '海外基金/International Fund'),
    (r'美国|纳斯达克|标普500|道琼斯', '美国股票ETF', '美国市场基金/US Market Fund'),
    (r'亚太|日本|欧洲', '美国股票ETF', '区域基金/Regional Fund'),
    (r'新兴市场', '新兴市场股票', '新兴市场基金/Emerging Market Fund'),
    
    # Fixed income
    (r'债券', '企业债券', '债券型基金/Bond Fund'),
    (r'货币|理财债券', '货币市场', '货币市场基金/Money Market Fund'),
    (r'理财', '银行理财', '银行理财产品/Bank Wealth Management'),
    (r'国债|政府债券', '国内政府债券', '国债基金/Government Bond'),
    (r'信用债|企业债', '企业债券', '企业债基金/Corporate Bond'),
    (r'高收益债', '高收益债券', '高收益债券/High Yield Bond'),
    
    # Cash & deposits
    (r'^Cash', '现金', '现金/Cash'),
    (r'^Deposit|存款', '活期存款', '存款/Deposit'),
    
    # Others
    (r'养老金|Pension', '国内政府债券', '养老金/Pension Fund'),
    (r'黄金|Gold', '黄金', '黄金资产/Gold Assets'),
    (r'房产|地产|Property', '住宅地产', '房地产/Real Estate'),
    (r'保险|Ins_', '保险', '保险/Insurance'),
    (r'ETF', '国内股票ETF', 'ETF基金'),  # Generic ETF - place at end as fallback
    
    # RSU/Stock compensation
    (r'RSU|Amazon|AMZN', '公司美股RSU', '股权激励/RSU')
]


def load_yaml_taxonomy(yaml_path: str) -> Dict:
    """Load the asset taxonomy YAML file."""
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading YAML file: {e}")
        return {}


def save_yaml_taxonomy(taxonomy: Dict, yaml_path: str) -> bool:
    """Save the updated asset taxonomy YAML file."""
    # Create a backup first
    backup_path = f"{yaml_path}.bak"
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            with open(backup_path, 'w', encoding='utf-8') as backup:
                backup.write(f.read())
        
        # Now save the updated file
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(taxonomy, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return True
    except Exception as e:
        print(f"Error saving YAML file: {e}")
        return False


def extract_unmapped_assets_from_log(log_content: str) -> List[Tuple[str, str, float]]:
    """Extract unmapped assets from log content."""
    unmapped_assets = []
    for match in re.finditer(UNMAPPED_PATTERN, log_content):
        asset_id = match.group(1)
        asset_name = match.group(2)
        asset_value = float(match.group(3).replace(',', ''))
        unmapped_assets.append((asset_id, asset_name, asset_value))
    return unmapped_assets


def suggest_mapping(asset_id: str, asset_name: str) -> str:
    """Suggest appropriate asset class mapping based on ID and name."""
    # Check each classification rule
    for pattern, sub_class, _ in CLASSIFICATION_RULES:
        if re.search(pattern, asset_id, re.IGNORECASE) or re.search(pattern, asset_name, re.IGNORECASE):
            return sub_class
    
    # Default to 'Other' if no pattern matches
    return '其他_子类'


def update_taxonomy_with_new_assets(
    taxonomy: Dict, 
    unmapped_assets: List[Tuple[str, str, float]]
) -> Dict:
    """Update the taxonomy with new asset mappings."""
    # Get the existing asset_mapping dictionary
    asset_mapping = taxonomy.get('asset_mapping', {})
    
    # Track number of updates
    updates_count = 0
    
    # Process each unmapped asset
    for asset_id, asset_name, _ in unmapped_assets:
        if asset_id not in asset_mapping:
            suggested_class = suggest_mapping(asset_id, asset_name)
            if suggested_class != '其他_子类':
                # Add to asset_mapping
                asset_mapping[asset_id] = suggested_class
                updates_count += 1
                print(f"Added mapping: {asset_id} ({asset_name}) -> {suggested_class}")
    
    # Update the taxonomy
    taxonomy['asset_mapping'] = asset_mapping
    print(f"Added {updates_count} new mappings to the taxonomy.")
    
    return taxonomy


def read_log_file(log_path: str) -> str:
    """Read log file content."""
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading log file: {e}")
        return ""


def manual_input_mode() -> str:
    """Get log content from manual input."""
    print("Please paste the debug output containing unmapped assets (press Ctrl+D when finished):")
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    return "\n".join(lines)


def main():
    """Main function to process logs and update taxonomy."""
    parser = argparse.ArgumentParser(description='Automatically update asset_taxonomy.yaml with new mappings.')
    parser.add_argument('--log_file', type=str, help='Path to the log file containing unmapped assets')
    parser.add_argument('--yaml_file', type=str, default=DEFAULT_YAML_PATH, help='Path to the asset_taxonomy.yaml file')
    args = parser.parse_args()
    
    # Load taxonomy
    taxonomy = load_yaml_taxonomy(args.yaml_file)
    if not taxonomy:
        print(f"Could not load taxonomy from {args.yaml_file}. Exiting.")
        return
    
    # Get log content
    if args.log_file:
        log_content = read_log_file(args.log_file)
    else:
        log_content = manual_input_mode()
    
    # Extract unmapped assets
    unmapped_assets = extract_unmapped_assets_from_log(log_content)
    if not unmapped_assets:
        print("No unmapped assets found in the log content.")
        return
    
    print(f"Found {len(unmapped_assets)} unmapped assets.")
    
    # Update taxonomy
    updated_taxonomy = update_taxonomy_with_new_assets(taxonomy, unmapped_assets)
    
    # Confirm before saving
    save_confirm = input("Save updates to taxonomy file? (y/n): ").lower()
    if save_confirm == 'y':
        if save_yaml_taxonomy(updated_taxonomy, args.yaml_file):
            print(f"Taxonomy file updated successfully: {args.yaml_file}")
            print(f"Backup saved as: {args.yaml_file}.bak")
        else:
            print("Failed to update taxonomy file.")
    else:
        print("Update canceled.")


if __name__ == "__main__":
    main()
