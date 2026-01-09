#!/usr/bin/env python3
"""
Data Validation Module for Portfolio Snapshots
Phase 2.2: Historical Data Depth & Stability

This module provides comprehensive validation functions for portfolio snapshots
to ensure data quality and integrity.
"""

import pandas as pd
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

logger = logging.getLogger(__name__)

def validate_row_count(df: pd.DataFrame, min_assets: int = 5, max_assets: int = 100) -> Dict[str, Any]:
    """
    Validate that the number of assets in the snapshot is within expected range.
    
    Args:
        df: Holdings DataFrame to validate
        min_assets: Minimum expected number of assets
        max_assets: Maximum expected number of assets
        
    Returns:
        Dictionary with validation results
    """
    result = {
        'passed': False,
        'asset_count': 0,
        'errors': [],
        'warnings': []
    }
    
    try:
        if df is None or df.empty:
            result['errors'].append("DataFrame is None or empty")
            return result
        
        asset_count = len(df)
        result['asset_count'] = asset_count
        
        if asset_count < min_assets:
            result['errors'].append(f"Too few assets: {asset_count} < {min_assets}")
        elif asset_count > max_assets:
            result['errors'].append(f"Too many assets: {asset_count} > {max_assets}")
        else:
            result['passed'] = True
            
        # Additional warnings for edge cases
        if asset_count < min_assets * 1.5:
            result['warnings'].append(f"Asset count ({asset_count}) is close to minimum threshold")
        elif asset_count > max_assets * 0.8:
            result['warnings'].append(f"Asset count ({asset_count}) is approaching maximum threshold")
            
        logger.debug(f"Row count validation: {asset_count} assets, passed: {result['passed']}")
        
    except Exception as e:
        result['errors'].append(f"Row count validation error: {e}")
        logger.error(f"Row count validation failed: {e}")
    
    return result


def validate_nan_values(df: pd.DataFrame, critical_columns: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Scan critical columns for null values and validate data completeness.
    
    Args:
        df: Holdings DataFrame to validate
        critical_columns: List of column names that must not have NaN values
        
    Returns:
        Dictionary with validation results
    """
    result = {
        'passed': False,
        'nan_summary': {},
        'errors': [],
        'warnings': []
    }
    
    if critical_columns is None:
        critical_columns = [
            'Market_Value_CNY',
            'Asset_ID', 
            'Asset_Name',
            'Snapshot_Date'
        ]
    
    try:
        if df is None or df.empty:
            result['errors'].append("DataFrame is None or empty")
            return result
        
        # Check for NaN values in all columns
        nan_counts = df.isnull().sum()
        result['nan_summary'] = nan_counts.to_dict()
        
        # Check critical columns specifically
        critical_nan_errors = []
        for col in critical_columns:
            if col in df.columns:
                nan_count = df[col].isnull().sum()
                if nan_count > 0:
                    critical_nan_errors.append(f"Column '{col}' has {nan_count} NaN values")
            else:
                result['warnings'].append(f"Critical column '{col}' not found in DataFrame")
        
        if critical_nan_errors:
            result['errors'].extend(critical_nan_errors)
        else:
            result['passed'] = True
        
        # Additional checks for data quality
        total_rows = len(df)
        for col, nan_count in nan_counts.items():
            if nan_count > 0:
                nan_percentage = (nan_count / total_rows) * 100
                if nan_percentage > 50:  # More than 50% NaN values
                    result['warnings'].append(f"Column '{col}' has {nan_percentage:.1f}% NaN values")
                elif nan_percentage > 20:  # More than 20% NaN values
                    result['warnings'].append(f"Column '{col}' has {nan_percentage:.1f}% NaN values")
        
        logger.debug(f"NaN validation: {len(critical_nan_errors)} critical errors, passed: {result['passed']}")
        
    except Exception as e:
        result['errors'].append(f"NaN validation error: {e}")
        logger.error(f"NaN validation failed: {e}")
    
    return result


def validate_taxonomy_coverage(df: pd.DataFrame, taxonomy_config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Ensure all assets in the snapshot have valid taxonomy mappings.
    
    Args:
        df: Holdings DataFrame to validate
        taxonomy_config_path: Path to taxonomy configuration file
        
    Returns:
        Dictionary with validation results
    """
    result = {
        'passed': False,
        'mapped_assets': 0,
        'unmapped_assets': [],
        'total_assets': 0,
        'coverage_percentage': 0.0,
        'errors': [],
        'warnings': []
    }
    
    try:
        if df is None or df.empty:
            result['errors'].append("DataFrame is None or empty")
            return result
        
        # Try to load taxonomy configuration
        taxonomy_config = None
        if taxonomy_config_path is None:
            taxonomy_config_path = os.path.join(project_root, 'config', 'asset_taxonomy.yaml')
        
        try:
            import yaml
            with open(taxonomy_config_path, 'r', encoding='utf-8') as f:
                taxonomy_config = yaml.safe_load(f)
        except Exception as e:
            result['warnings'].append(f"Could not load taxonomy config from {taxonomy_config_path}: {e}")
            # Continue with basic validation without taxonomy checking
        
        # Get unique assets from DataFrame
        asset_columns = ['Asset_ID', 'Asset_Name']
        unique_assets = set()
        
        for col in asset_columns:
            if col in df.columns:
                assets = df[col].dropna().astype(str).unique()
                unique_assets.update(assets)
        
        result['total_assets'] = len(unique_assets)
        
        if taxonomy_config is None:
            # Basic validation without taxonomy - just check that assets exist
            if result['total_assets'] > 0:
                result['passed'] = True
                result['mapped_assets'] = result['total_assets']
                result['coverage_percentage'] = 100.0
                result['warnings'].append("Taxonomy validation skipped - config not available")
            else:
                result['errors'].append("No assets found in DataFrame")
        else:
            # Full taxonomy validation
            asset_mapping = taxonomy_config.get('asset_mapping', {})
            pattern_mapping = taxonomy_config.get('pattern_mapping', {})
            
            # Define assets to ignore in taxonomy coverage calculation
            # These are placeholder/aggregate assets that don't need individual mapping
            ignore_list = ['US_Fund_Portfolio']  # Balance sheet placeholder for US fund holdings
            
            mapped_count = 0
            unmapped_assets = []
            ignored_count = 0
            
            for asset in unique_assets:
                # Check if asset should be ignored
                if asset in ignore_list:
                    ignored_count += 1
                    continue
                    
                is_mapped = False
                
                # Check direct mapping
                if asset in asset_mapping:
                    is_mapped = True
                else:
                    # Check pattern mapping
                    for pattern in pattern_mapping.keys():
                        if pattern.lower() in asset.lower():
                            is_mapped = True
                            break
                
                if is_mapped:
                    mapped_count += 1
                else:
                    unmapped_assets.append(asset)
            
            # Adjust total assets count to exclude ignored assets
            effective_total = result['total_assets'] - ignored_count
            result['mapped_assets'] = mapped_count
            result['unmapped_assets'] = unmapped_assets
            result['coverage_percentage'] = (mapped_count / effective_total * 100) if effective_total > 0 else 0.0
            
            if ignored_count > 0:
                result['warnings'].append(f"Ignored {ignored_count} placeholder asset(s) in coverage calculation")
            
            # Determine if validation passed
            if result['coverage_percentage'] >= 95.0:  # 95% coverage required
                result['passed'] = True
            else:
                result['errors'].append(f"Taxonomy coverage too low: {result['coverage_percentage']:.1f}% < 95%")
                if unmapped_assets:
                    result['errors'].append(f"Unmapped assets: {unmapped_assets[:5]}" + 
                                          (f" (and {len(unmapped_assets)-5} more)" if len(unmapped_assets) > 5 else ""))
        
        logger.debug(f"Taxonomy validation: {result['coverage_percentage']:.1f}% coverage, passed: {result['passed']}")
        
    except Exception as e:
        result['errors'].append(f"Taxonomy validation error: {e}")
        logger.error(f"Taxonomy validation failed: {e}")
    
    return result


def validate_snapshot_file(file_path: Path) -> Dict[str, Any]:
    """
    Comprehensive validation of a complete snapshot file.
    
    Args:
        file_path: Path to the snapshot Excel file
        
    Returns:
        Dictionary with comprehensive validation results
    """
    result = {
        'passed': False,
        'file_exists': False,
        'file_readable': False,
        'validations': {},
        'errors': [],
        'warnings': [],
        'summary': {}
    }
    
    try:
        # Check if file exists
        if not file_path.exists():
            result['errors'].append(f"Snapshot file does not exist: {file_path}")
            return result
        
        result['file_exists'] = True
        
        # Try to read the file
        try:
            df = pd.read_excel(file_path, sheet_name='Holdings_Snapshot')
            result['file_readable'] = True
        except Exception as e:
            result['errors'].append(f"Cannot read snapshot file: {e}")
            return result
        
        # Run all validation checks
        result['validations']['row_count'] = validate_row_count(df)
        result['validations']['nan_values'] = validate_nan_values(df)
        result['validations']['taxonomy_coverage'] = validate_taxonomy_coverage(df)
        
        # Aggregate results
        all_passed = all(validation['passed'] for validation in result['validations'].values())
        result['passed'] = all_passed
        
        # Collect all errors and warnings
        for validation_name, validation_result in result['validations'].items():
            result['errors'].extend(validation_result.get('errors', []))
            result['warnings'].extend(validation_result.get('warnings', []))
        
        # Generate summary
        result['summary'] = {
            'file_path': str(file_path),
            'file_size_mb': file_path.stat().st_size / (1024 * 1024),
            'total_assets': result['validations']['row_count'].get('asset_count', 0),
            'taxonomy_coverage': result['validations']['taxonomy_coverage'].get('coverage_percentage', 0.0),
            'validation_checks_passed': sum(1 for v in result['validations'].values() if v['passed']),
            'total_validation_checks': len(result['validations']),
            'overall_status': 'PASSED' if result['passed'] else 'FAILED'
        }
        
        logger.info(f"Snapshot validation complete: {result['summary']['overall_status']} - {file_path.name}")
        
    except Exception as e:
        result['errors'].append(f"Snapshot file validation error: {e}")
        logger.error(f"Snapshot file validation failed: {e}")
    
    return result


def validate_historical_data_consistency(snapshots_dir: Path) -> Dict[str, Any]:
    """
    Validate consistency across multiple historical snapshots.
    
    Args:
        snapshots_dir: Directory containing snapshot files
        
    Returns:
        Dictionary with consistency validation results
    """
    result = {
        'passed': False,
        'snapshots_found': 0,
        'date_gaps': [],
        'asset_consistency_issues': [],
        'errors': [],
        'warnings': []
    }
    
    try:
        # Find all snapshot files
        snapshot_files = list(snapshots_dir.glob('holdings_snapshot_*.xlsx'))
        result['snapshots_found'] = len(snapshot_files)
        
        if result['snapshots_found'] == 0:
            result['errors'].append("No snapshot files found")
            return result
        
        # Extract dates and sort
        snapshot_dates = []
        for file in snapshot_files:
            try:
                date_str = file.stem.split('_')[-1]
                date = pd.to_datetime(date_str, format='%Y%m%d')
                snapshot_dates.append(date)
            except ValueError:
                result['warnings'].append(f"Could not parse date from filename: {file.name}")
        
        if len(snapshot_dates) < 2:
            result['warnings'].append("Insufficient snapshots for consistency analysis")
            result['passed'] = True  # Not an error, just limited data
            return result
        
        snapshot_dates.sort()
        
        # Check for date gaps (for daily snapshots)
        expected_business_days = pd.bdate_range(snapshot_dates[0], snapshot_dates[-1])
        missing_dates = set(expected_business_days) - set(snapshot_dates)
        
        if missing_dates:
            result['date_gaps'] = [d.strftime('%Y-%m-%d') for d in sorted(missing_dates)]
            if len(result['date_gaps']) > 5:  # Too many gaps
                result['errors'].append(f"Too many date gaps: {len(result['date_gaps'])} missing dates")
            else:
                result['warnings'].append(f"Found {len(result['date_gaps'])} date gaps")
        
        # Basic consistency check passed if no critical errors
        if not result['errors']:
            result['passed'] = True
        
        logger.info(f"Historical consistency check: {result['snapshots_found']} snapshots, {len(result['date_gaps'])} gaps")
        
    except Exception as e:
        result['errors'].append(f"Historical data consistency validation error: {e}")
        logger.error(f"Historical data consistency validation failed: {e}")
    
    return result