"""
Time Series Utilities Module

This module provides standardized time-series handling functions for consistent
date processing, gap detection, interpolation, and stability analysis across
the entire investment system.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class TimeSeriesProcessor:
    """
    Centralized processor for all time-series operations in the investment system.
    Provides consistent handling of dates, gaps, validation, and transformations.
    """
    
    def __init__(self, frequency: str = 'M', fill_method: str = 'ffill'):
        """
        Initialize the time-series processor.
        
        Args:
            frequency: Default frequency for resampling ('D', 'W', 'M', 'Q', 'Y')
            fill_method: Default method for filling gaps ('ffill', 'bfill', 'interpolate')
        """
        self.frequency = frequency
        self.fill_method = fill_method
        self.logger = logging.getLogger(__name__)
    
    def standardize_datetime_index(self, df: pd.DataFrame, 
                                 date_column: Optional[str] = None,
                                 frequency: Optional[str] = None,
                                 sort: bool = True) -> pd.DataFrame:
        """
        Standardize datetime index for consistent time-series processing.
        
        Args:
            df: DataFrame to standardize
            date_column: Name of date column to use as index (if not already index)
            frequency: Target frequency for resampling
            sort: Whether to sort by date index
            
        Returns:
            DataFrame with standardized datetime index
        """
        try:
            df_copy = df.copy()
            
            # Set date column as index if specified
            if date_column and date_column in df_copy.columns:
                df_copy[date_column] = pd.to_datetime(df_copy[date_column], errors='coerce')
                df_copy = df_copy.set_index(date_column)
            
            # Ensure index is datetime
            if not isinstance(df_copy.index, pd.DatetimeIndex):
                try:
                    df_copy.index = pd.to_datetime(df_copy.index, errors='coerce')
                except Exception as e:
                    self.logger.warning(f"Failed to convert index to datetime: {e}")
                    return df
            
            # Remove invalid dates
            df_copy = df_copy[df_copy.index.notna()]
            
            # Sort by date if requested
            if sort:
                df_copy = df_copy.sort_index()
            
            # Remove duplicate index entries (keep last)
            if df_copy.index.duplicated().any():
                duplicates_count = df_copy.index.duplicated().sum()
                self.logger.warning(f"Removing {duplicates_count} duplicate date entries")
                df_copy = df_copy[~df_copy.index.duplicated(keep='last')]
            
            # Resample to target frequency if specified
            if frequency:
                df_copy = self._safe_resample(df_copy, frequency)
            
            # Set standard index name
            df_copy.index.name = 'Date'
            
            self.logger.debug(f"Standardized datetime index: {len(df_copy)} records, "
                            f"range {df_copy.index.min()} to {df_copy.index.max()}")
            
            return df_copy
            
        except Exception as e:
            self.logger.error(f"Error standardizing datetime index: {e}")
            return df
    
    def detect_time_gaps(self, df: pd.DataFrame, 
                        expected_frequency: str = 'M',
                        tolerance_days: int = 7) -> Dict[str, Any]:
        """
        Detect gaps in time-series data and provide gap analysis.
        
        Args:
            df: DataFrame with datetime index
            expected_frequency: Expected frequency ('D', 'W', 'M', 'Q', 'Y')
            tolerance_days: Tolerance for gap detection in days
            
        Returns:
            Dictionary with gap analysis results
        """
        try:
            if not isinstance(df.index, pd.DatetimeIndex) or len(df) < 2:
                return {'error': 'Invalid or insufficient datetime index'}
            
            # Calculate expected frequency in days
            freq_days = {
                'D': 1, 'W': 7, 'M': 30, 'Q': 90, 'Y': 365
            }.get(expected_frequency.upper(), 30)
            
            # Calculate actual gaps
            time_diffs = df.index.to_series().diff().dropna()
            gap_days = time_diffs.dt.days
            
            # Identify significant gaps
            expected_threshold = freq_days + tolerance_days
            significant_gaps = gap_days[gap_days > expected_threshold]
            
            # Calculate statistics
            results = {
                'total_periods': len(df),
                'date_range': {
                    'start': df.index.min(),
                    'end': df.index.max(),
                    'span_days': (df.index.max() - df.index.min()).days
                },
                'gap_analysis': {
                    'total_gaps': len(time_diffs),
                    'significant_gaps': len(significant_gaps),
                    'average_gap_days': gap_days.mean(),
                    'max_gap_days': gap_days.max(),
                    'gap_threshold_days': expected_threshold
                },
                'data_quality': {
                    'completeness_ratio': 1 - (len(significant_gaps) / max(len(time_diffs), 1)),
                    'is_regular': len(significant_gaps) == 0,
                    'frequency_consistency': gap_days.std() / gap_days.mean() if gap_days.mean() > 0 else 0
                }
            }
            
            # Add gap details if significant gaps exist
            if len(significant_gaps) > 0:
                gap_details = []
                for i, gap_size in significant_gaps.items():
                    gap_start = df.index[df.index.get_loc(i) - 1] if df.index.get_loc(i) > 0 else df.index[0]
                    gap_details.append({
                        'gap_start': gap_start,
                        'gap_end': i,
                        'gap_days': gap_size
                    })
                results['gap_details'] = gap_details
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error detecting time gaps: {e}")
            return {'error': str(e)}
    
    def fill_time_gaps(self, df: pd.DataFrame, 
                      method: str = 'interpolate',
                      frequency: str = 'M',
                      limit: Optional[int] = None) -> pd.DataFrame:
        """
        Fill gaps in time-series data using specified method.
        
        Args:
            df: DataFrame with datetime index
            method: Fill method ('ffill', 'bfill', 'interpolate', 'zero')
            frequency: Target frequency for filling
            limit: Maximum number of consecutive periods to fill
            
        Returns:
            DataFrame with filled gaps
        """
        try:
            if not isinstance(df.index, pd.DatetimeIndex):
                self.logger.warning("DataFrame does not have datetime index")
                return df
            
            df_filled = df.copy()
            
            # Create complete date range
            full_range = pd.date_range(
                start=df_filled.index.min(),
                end=df_filled.index.max(),
                freq=frequency
            )
            
            # Reindex to full range
            df_filled = df_filled.reindex(full_range)
            
            # Apply filling method
            if method == 'interpolate':
                # Use time-aware interpolation
                df_filled = df_filled.interpolate(method='time', limit=limit)
            elif method == 'ffill':
                df_filled = df_filled.fillna(method='ffill', limit=limit)
            elif method == 'bfill':
                df_filled = df_filled.fillna(method='bfill', limit=limit)
            elif method == 'zero':
                df_filled = df_filled.fillna(0)
            else:
                self.logger.warning(f"Unknown fill method: {method}, using interpolate")
                df_filled = df_filled.interpolate(method='time', limit=limit)
            
            # Log filling results
            filled_count = df_filled.isna().sum().sum() - df.isna().sum().sum()
            if filled_count > 0:
                self.logger.info(f"Filled {abs(filled_count)} missing values using {method}")
            
            return df_filled
            
        except Exception as e:
            self.logger.error(f"Error filling time gaps: {e}")
            return df
    
    def validate_time_series_integrity(self, df: pd.DataFrame, 
                                     expected_frequency: str = 'M',
                                     min_periods: int = 2) -> Dict[str, Any]:
        """
        Comprehensive validation of time-series data integrity.
        
        Args:
            df: DataFrame to validate
            expected_frequency: Expected data frequency
            min_periods: Minimum required periods
            
        Returns:
            Dictionary with validation results
        """
        try:
            results = {
                'is_valid': True,
                'errors': [],
                'warnings': [],
                'statistics': {}
            }
            
            # Check if DataFrame exists and has data
            if df is None or df.empty:
                results['is_valid'] = False
                results['errors'].append("DataFrame is None or empty")
                return results
            
            # Check datetime index
            if not isinstance(df.index, pd.DatetimeIndex):
                results['is_valid'] = False
                results['errors'].append("Index is not DatetimeIndex")
                return results
            
            # Check minimum periods
            if len(df) < min_periods:
                results['is_valid'] = False
                results['errors'].append(f"Insufficient data: {len(df)} < {min_periods}")
                return results
            
            # Check for null dates
            null_dates = df.index.isna().sum()
            if null_dates > 0:
                results['warnings'].append(f"Found {null_dates} null dates")
            
            # Check chronological order
            if not df.index.is_monotonic_increasing:
                results['warnings'].append("Data is not in chronological order")
            
            # Analyze gaps
            gap_analysis = self.detect_time_gaps(df, expected_frequency)
            if 'error' not in gap_analysis:
                results['statistics']['gap_analysis'] = gap_analysis
                
                # Add warnings for significant gaps
                if gap_analysis['gap_analysis']['significant_gaps'] > 0:
                    results['warnings'].append(
                        f"Found {gap_analysis['gap_analysis']['significant_gaps']} significant time gaps"
                    )
            
            # Check data quality
            total_nulls = df.isnull().sum().sum()
            total_values = df.size
            null_ratio = total_nulls / total_values if total_values > 0 else 0
            
            results['statistics']['data_quality'] = {
                'total_records': len(df),
                'total_nulls': total_nulls,
                'null_ratio': null_ratio,
                'date_range_days': (df.index.max() - df.index.min()).days
            }
            
            if null_ratio > 0.5:
                results['warnings'].append(f"High null ratio: {null_ratio:.2%}")
            
            # Set overall validation status
            results['is_valid'] = len(results['errors']) == 0
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error validating time-series integrity: {e}")
            return {
                'is_valid': False,
                'errors': [str(e)],
                'warnings': [],
                'statistics': {}
            }
    
    def calculate_rolling_metrics(self, series: pd.Series,
                                windows: List[int] = [7, 30, 90],
                                metrics: List[str] = ['mean', 'std', 'min', 'max']) -> pd.DataFrame:
        """
        Calculate rolling metrics for time-series analysis.
        
        Args:
            series: Time-series data
            windows: List of window sizes for rolling calculations
            metrics: List of metrics to calculate
            
        Returns:
            DataFrame with rolling metrics
        """
        try:
            if not isinstance(series.index, pd.DatetimeIndex):
                self.logger.warning("Series does not have datetime index")
                return pd.DataFrame()
            
            results = {}
            
            for window in windows:
                for metric in metrics:
                    col_name = f'{metric}_{window}d'
                    
                    if metric == 'mean':
                        results[col_name] = series.rolling(window=window, min_periods=1).mean()
                    elif metric == 'std':
                        results[col_name] = series.rolling(window=window, min_periods=1).std()
                    elif metric == 'min':
                        results[col_name] = series.rolling(window=window, min_periods=1).min()
                    elif metric == 'max':
                        results[col_name] = series.rolling(window=window, min_periods=1).max()
                    elif metric == 'median':
                        results[col_name] = series.rolling(window=window, min_periods=1).median()
                    elif metric == 'sum':
                        results[col_name] = series.rolling(window=window, min_periods=1).sum()
            
            return pd.DataFrame(results, index=series.index)
            
        except Exception as e:
            self.logger.error(f"Error calculating rolling metrics: {e}")
            return pd.DataFrame()
    
    def detect_outliers(self, series: pd.Series, 
                       method: str = 'iqr',
                       threshold: float = 1.5) -> Dict[str, Any]:
        """
        Detect outliers in time-series data.
        
        Args:
            series: Time-series data
            method: Detection method ('iqr', 'zscore', 'modified_zscore')
            threshold: Threshold for outlier detection
            
        Returns:
            Dictionary with outlier analysis
        """
        try:
            if series.empty:
                return {'error': 'Empty series'}
            
            clean_series = series.dropna()
            if len(clean_series) == 0:
                return {'error': 'No valid data after removing NaN'}
            
            outliers_mask = pd.Series(False, index=series.index)
            
            if method == 'iqr':
                Q1 = clean_series.quantile(0.25)
                Q3 = clean_series.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
                outliers_mask = (series < lower_bound) | (series > upper_bound)
                
            elif method == 'zscore':
                z_scores = np.abs((clean_series - clean_series.mean()) / clean_series.std())
                outliers_mask = z_scores > threshold
                
            elif method == 'modified_zscore':
                median = clean_series.median()
                mad = np.median(np.abs(clean_series - median))
                modified_z_scores = 0.6745 * (clean_series - median) / mad
                outliers_mask = np.abs(modified_z_scores) > threshold
            
            outliers = series[outliers_mask]
            
            return {
                'method': method,
                'threshold': threshold,
                'outlier_count': len(outliers),
                'outlier_percentage': (len(outliers) / len(clean_series)) * 100,
                'outlier_dates': outliers.index.tolist(),
                'outlier_values': outliers.tolist(),
                'outliers_mask': outliers_mask
            }
            
        except Exception as e:
            self.logger.error(f"Error detecting outliers: {e}")
            return {'error': str(e)}
    
    def _safe_resample(self, df: pd.DataFrame, frequency: str) -> pd.DataFrame:
        """
        Safely resample dataframe to target frequency.
        
        Args:
            df: DataFrame to resample
            frequency: Target frequency
            
        Returns:
            Resampled DataFrame
        """
        try:
            # Map frequency to pandas offset
            freq_map = {
                'D': 'D', 'W': 'W', 'M': 'ME', 'Q': 'QE', 'Y': 'YE'
            }
            pandas_freq = freq_map.get(frequency.upper(), frequency)
            
            # Resample numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            other_cols = df.select_dtypes(exclude=[np.number]).columns
            
            resampled_parts = []
            
            if len(numeric_cols) > 0:
                resampled_numeric = df[numeric_cols].resample(pandas_freq).last()
                resampled_parts.append(resampled_numeric)
            
            if len(other_cols) > 0:
                resampled_other = df[other_cols].resample(pandas_freq).last()
                resampled_parts.append(resampled_other)
            
            if resampled_parts:
                return pd.concat(resampled_parts, axis=1)
            else:
                return df
                
        except Exception as e:
            self.logger.warning(f"Error resampling to {frequency}: {e}")
            return df


def standardize_time_series(df: pd.DataFrame, 
                          date_column: Optional[str] = None,
                          frequency: str = 'M',
                          fill_gaps: bool = True) -> pd.DataFrame:
    """
    Convenience function for standardizing time-series data.
    
    Args:
        df: DataFrame to standardize
        date_column: Date column name
        frequency: Target frequency
        fill_gaps: Whether to fill time gaps
        
    Returns:
        Standardized DataFrame
    """
    processor = TimeSeriesProcessor(frequency=frequency)
    
    # Standardize datetime index
    df_standard = processor.standardize_datetime_index(df, date_column, frequency)
    
    # Fill gaps if requested
    if fill_gaps and len(df_standard) > 0:
        df_standard = processor.fill_time_gaps(df_standard, frequency=frequency)
    
    # Ensure index name is set
    if df_standard.index.name != 'Date':
        df_standard.index.name = 'Date'
    
    return df_standard


def validate_financial_time_series(df: pd.DataFrame, 
                                 expected_frequency: str = 'M',
                                 asset_columns: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Specialized validation for financial time-series data.
    
    Args:
        df: Financial DataFrame to validate
        expected_frequency: Expected data frequency
        asset_columns: Columns containing asset values
        
    Returns:
        Validation results with financial-specific checks
    """
    processor = TimeSeriesProcessor()
    
    # Basic time-series validation
    results = processor.validate_time_series_integrity(df, expected_frequency)
    
    # Financial-specific validations
    if asset_columns:
        financial_issues = []
        
        for col in asset_columns:
            if col not in df.columns:
                continue
                
            # Check for negative values where inappropriate
            if col.lower().startswith(('asset', 'value', 'market')):
                negative_count = (df[col] < 0).sum()
                if negative_count > 0:
                    financial_issues.append(f"{col}: {negative_count} negative values")
            
            # Check for extreme outliers
            outlier_analysis = processor.detect_outliers(df[col])
            if 'outlier_percentage' in outlier_analysis and outlier_analysis['outlier_percentage'] > 10:
                financial_issues.append(f"{col}: {outlier_analysis['outlier_percentage']:.1f}% outliers")
        
        if financial_issues:
            results['warnings'].extend(financial_issues)
    
    return results
