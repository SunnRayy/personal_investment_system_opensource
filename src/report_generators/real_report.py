#!/usr/bin/env python3
"""
Real HTML Report Generator - Integration with Investment System
This script generates HTML reports using actual data from the investment system modules.
"""

import os
import sys
import json
import logging
import time
import math
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Tuple, TYPE_CHECKING, Optional
from src.localization import _
from src.localization.config_loader import LocalizedConfigLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import modular report builders
from src.report_builders.chart_builders import (
    build_portfolio_growth_percentage_data,
    build_cash_flow_data,
    build_twr_data,
    build_drawdown_data,
    build_allocation_from_holdings
)
from src.report_builders.performance_builders import (
    aggregate_performance_by_top_level,
    aggregate_performance_by_sub_class
)
from src.report_builders.rebalancing_builder import (
    build_rebalancing_analysis
)
from src.report_builders.table_builder import (
    build_holdings_table_direct
)
from src.report_builders.tier_analysis_builder import build_tier_analysis

# PHASE 2.4: Import UnifiedDataPreparer and ValidationService
from src.report_builders.unified_data_preparer import UnifiedDataPreparer
from src.report_builders.validation_service import ValidationService  # noqa: F401 (imported for side-effects/logging config)
from src.report_generators.markdown_context_generator import MarkdownContextGenerator

if TYPE_CHECKING:
    from src.data_manager.manager import DataManager
    from src.portfolio_lib.data_integration import PortfolioAnalysisManager
    from src.portfolio_lib.taxonomy_manager import TaxonomyManager
    from src.financial_analysis.analyzer import FinancialAnalyzer
    from src.financial_analysis.cash_flow_forecaster import CashFlowForecaster

def validate_gains_consistency(
    gains_analysis_data: Dict[str, Any],
    lifetime_performance_data: List[Dict[str, Any]],
    tolerance: float = 1000.0
) -> List[Dict[str, Any]]:
    """
    Cross-validate gains calculations between two methods.
    Logs warnings if discrepancies exceed tolerance.
    
    Phase 4 Task 4.2: Data validation checkpoint to ensure consistency
    between get_realized_unrealized_gains() and get_lifetime_asset_performance().
    
    Args:
        gains_analysis_data: Dictionary from get_realized_unrealized_gains()
        lifetime_performance_data: List of dicts from get_lifetime_asset_performance()
        tolerance: Maximum allowed difference in CNY (default: ¥1000)
        
    Returns:
        List of discrepancy dictionaries (empty if all consistent)
    """
    discrepancies = []
    
    # Extract sub-class breakdown from gains_analysis
    subclass_breakdown = gains_analysis_data.get('subclass_breakdown', {})
    
    if not subclass_breakdown:
        logger.info("ℹ️  No sub-class breakdown available for validation")
        return discrepancies
    
    # Aggregate lifetime performance by sub-class
    lifetime_by_subclass = {}
    for asset in lifetime_performance_data:
        sub_class = asset.get('sub_class', 'Unknown')
        if sub_class not in lifetime_by_subclass:
            lifetime_by_subclass[sub_class] = {
                'realized_gains': 0.0,
                'unrealized_gains': 0.0,
                'total_gains': 0.0
            }
        
        lifetime_by_subclass[sub_class]['realized_gains'] += asset.get('realized_gains', 0.0)
        lifetime_by_subclass[sub_class]['unrealized_gains'] += asset.get('unrealized_gains', 0.0)
        lifetime_by_subclass[sub_class]['total_gains'] += asset.get('total_gains', 0.0)
    
    # Compare sub-class totals
    all_subclasses = set(list(subclass_breakdown.keys()) + list(lifetime_by_subclass.keys()))
    
    for sub_class in all_subclasses:
        gains_total = subclass_breakdown.get(sub_class, {}).get('total_gains', 0.0)
        lifetime_total = lifetime_by_subclass.get(sub_class, {}).get('total_gains', 0.0)
        
        diff = abs(gains_total - lifetime_total)
        
        if diff > tolerance:
            discrepancies.append({
                'sub_class': sub_class,
                'gains_analysis_total': gains_total,
                'lifetime_performance_total': lifetime_total,
                'difference': diff,
                'difference_pct': (diff / max(abs(gains_total), abs(lifetime_total), 1.0)) * 100
            })
    
    # Log results
    if discrepancies:
        logger.warning(f"⚠️  Gains calculation discrepancies detected ({len(discrepancies)} sub-classes):")
        for disc in discrepancies[:5]:  # Show first 5
            logger.warning(
                f"  - {disc['sub_class']}: "
                f"Method1=¥{disc['gains_analysis_total']:,.0f}, "
                f"Method2=¥{disc['lifetime_performance_total']:,.0f}, "
                f"Δ¥{disc['difference']:,.0f} ({disc['difference_pct']:.1f}%)"
            )
        if len(discrepancies) > 5:
            logger.warning(f"  ... and {len(discrepancies) - 5} more")
    else:
        logger.info(f"✅ Gains calculation validation: All {len(all_subclasses)} sub-classes consistent (tolerance: ¥{tolerance:,.0f})")
    
    return discrepancies


def _sanitize_numeric_list(values: List[Any]) -> List[Optional[float]]:
    """Convert NaN/inf values in a numeric list to ``None`` for JSON safety."""
    sanitized: List[Optional[float]] = []
    for value in values:
        if value is None:
            sanitized.append(None)
            continue
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            sanitized.append(None)
            continue
        if math.isfinite(numeric_value):
            sanitized.append(round(numeric_value, 2))
        else:
            sanitized.append(None)
    return sanitized


def _sanitize_forecast_data_for_json(forecast_data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all numeric forecast series are serializable before JSON export."""
    numeric_fields = [
        'income_forecast', 'income_lower', 'income_upper',
        'expenses_forecast', 'expenses_lower', 'expenses_upper',
        'investments_forecast', 'investments_lower', 'investments_upper',
        'net_cash_flow', 'net_cash_flow_lower', 'net_cash_flow_upper'
    ]

    for field in numeric_fields:
        if field in forecast_data:
            forecast_data[field] = _sanitize_numeric_list(forecast_data.get(field, []))

    return forecast_data


def classify_asset_using_taxonomy(asset_name: str, asset_type: str, taxonomy_manager: 'TaxonomyManager') -> Tuple[str, str]:
    """
    Classify asset using the official taxonomy system with proper sub-class to top-level mapping.
    
    Enhanced to check explicit fund name mappings first before falling back to pattern matching.
    This prevents incorrect classification of medical sector funds as insurance.
    
    Args:
        asset_name: Name of the asset
        asset_type: Type/category of the asset (from Asset_Type_Raw)
        taxonomy_manager: TaxonomyManager instance
        
    Returns:
        Tuple of (top_level_class, sub_class) in English for display
    """
    # Use centralized TaxonomyManager for classification
    # This prioritizes Database rules, then falls back to YAML
    sub_class, top_level_class = taxonomy_manager.get_asset_classification(asset_name, asset_type)
    
    # Handle 'Unknown' or None
    if not top_level_class or top_level_class == 'Unknown':
        top_level_class = 'Other'
    if not sub_class:
        sub_class = 'Other'
    
    # Return localized strings for display
    # If the strings are already localized by TaxonomyManager (via config), 
    # _() will just return them (or translate them if they match a msgid)
    return _(top_level_class), _(sub_class)


def is_placeholder_asset(asset_id: str | None, asset_name: str | None) -> bool:
    """Determine if an asset row represents a balance-sheet placeholder/aggregate that
    should NOT appear in detailed holdings tables or individual performance lists.

    This centralizes logic so filtering is consistent across performance aggregation
    and holdings table generation.

    Args:
        asset_id: The Asset_ID (usually DataFrame index) identifying the asset
        asset_name: Raw asset name from the holdings data

    Returns:
        True if this is a placeholder aggregate asset and should be skipped.
    """
    if asset_id is None and asset_name is None:
        return False
    placeholder_ids = {"Fund_US_Placeholder"}
    placeholder_names_raw = {"Fund_US_Placeholder"}
    # Formatted display names that might already have been applied elsewhere
    placeholder_display_names = {"US Fund Portfolio", "US Fund Portfolio (Aggregate)"}
    return (
        (asset_id in placeholder_ids) or
        (asset_name in placeholder_names_raw) or
        (asset_name in placeholder_display_names)
    )


def generate_capital_allocation_suggestion(rebalancing_analysis: Dict) -> Dict:
    """
    Generate capital allocation suggestion based on rebalancing analysis.
    Identifies the asset class with the largest negative drift (most under-allocated).
    
    Args:
        rebalancing_analysis: Dictionary containing 'top_level_table' rebalancing analysis
        
    Returns:
        Dictionary with 'target_class' (Chinese), 'target_class_en' (English),
        'drift' (percentage points), and 'is_rebalanceable' (bool)
    """
    # FIX: Use correct key 'top_level_table' from rebalancing_builder
    top_level_data = rebalancing_analysis.get('top_level_table', [])
    
    # Find the most under-allocated rebalanceable class
    most_underallocated = None
    largest_negative_drift = 0
    
    for item in top_level_data:
        if not item.get('is_rebalanceable', False):
            continue
        
        drift = item.get('drift', 0)
        if drift < largest_negative_drift:
            largest_negative_drift = drift
            most_underallocated = item
    
    if most_underallocated:
        # The asset_class field can be in either Chinese or English depending on data source
        # Map bidirectionally to ensure we have both versions
        english_to_chinese = {
            'Equity': 'Equity',
            'Fixed Income': 'Fixed Income',
            'Cash': 'Cash',
            'Commodities': 'Commodities',
            'Alternative': 'Alternative',
            'Real Estate': 'Real Estate',
            'Insurance': 'Insurance'
        }
        
        # Create reverse mapping (Chinese to English)
        chinese_to_english = {v: k for k, v in english_to_chinese.items()}
        
        asset_class_value = most_underallocated.get('asset_class', '')
        
        # Determine if input is Chinese or English and get both versions
        if asset_class_value in chinese_to_english:
            # Input is Chinese
            asset_class_cn = asset_class_value
            asset_class_en = chinese_to_english.get(asset_class_value, asset_class_value)
        else:
            # Input is English (or unknown)
            asset_class_en = asset_class_value
            asset_class_cn = english_to_chinese.get(asset_class_value, asset_class_value)
        
        return {
            'target_class': asset_class_cn,
            'target_class_en': asset_class_en,
            'drift': abs(largest_negative_drift),
            'is_rebalanceable': True,
            'current_pct': most_underallocated.get('current_pct', 0),
            'target_pct': most_underallocated.get('target_pct', 0)
        }
    
    # No under-allocated classes found
    return {
        'target_class': None,
        'target_class_en': None,
        'drift': 0,
        'is_rebalanceable': False
    }


def format_asset_name_for_display(asset_name: str) -> str:
    """
    Format asset names for better display in reports by replacing placeholder names.
    
    Args:
        asset_name: Original asset name from data
        
    Returns:
        str: Formatted name for display
    """
    # Replace placeholder names with user-friendly names
    name_replacements = {
        'Fund_US_Placeholder': 'US Fund Portfolio',
    }
    
    return name_replacements.get(asset_name, asset_name)

# Note: aggregate_performance_by_top_level moved to src/report_builders/performance_builders.py
# Note: aggregate_performance_by_sub_class moved to src/report_builders/performance_builders.py

def aggregate_performance_by_sub_class_PLACEHOLDER(individual_assets):
    """
    Aggregate individual asset performance data into sub-class summaries.
    Only aggregates assets with real XIRR data; shows "N/A" if no real data available.
    
    Args:
        individual_assets: List of dictionaries with asset performance data
        
    Returns:
        List of dictionaries with sub-class performance summaries
    """
    sub_class_groups = {}
    
    for asset in individual_assets:
        sub_class = asset.get('sub_class', 'Unknown')
        
        if sub_class not in sub_class_groups:
            sub_class_groups[sub_class] = {
                'class_name': sub_class,
                'total_market_value': 0,
                'weighted_xirr_sum': 0,
                'total_weight_with_xirr': 0,
                'has_any_real_xirr': False,
                'approximated_count': 0,
                'total_count': 0
            }
        
        market_value = asset.get('market_value', 0)
        xirr = asset.get('xirr')
        has_real_xirr = asset.get('has_real_xirr', False)
        xirr_metadata = asset.get('xirr_metadata', {})
        
        group = sub_class_groups[sub_class]
        group['total_market_value'] += market_value
        group['total_count'] += 1
        
        # Track approximation metadata
        if xirr_metadata.get('is_approximated', True):
            group['approximated_count'] += 1
        
        # Only include in XIRR calculation if real data is available
        if has_real_xirr and xirr is not None:
            group['weighted_xirr_sum'] += xirr * market_value
            group['total_weight_with_xirr'] += market_value
            group['has_any_real_xirr'] = True
    
    # Calculate total portfolio value for percentage calculations
    total_portfolio_value = sum(group['total_market_value'] for group in sub_class_groups.values())
    
    # Calculate weighted average XIRR and portfolio percentage for each group
    result = []
    for group in sub_class_groups.values():
        # Only calculate XIRR if we have real data
        if group['has_any_real_xirr'] and group['total_weight_with_xirr'] > 0:
            weighted_avg_xirr = group['weighted_xirr_sum'] / group['total_weight_with_xirr']
        else:
            weighted_avg_xirr = None  # Will display as "N/A"
            
        portfolio_percentage = (group['total_market_value'] / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
        
        # Calculate approximation percentage
        approximation_percentage = (group['approximated_count'] / group['total_count'] * 100) if group['total_count'] > 0 else 100
        
        result.append({
            'class_name': group['class_name'],
            'market_value': group['total_market_value'],
            'xirr': weighted_avg_xirr,
            'portfolio_percentage': portfolio_percentage,
            'metadata': {
                'approximated_count': group['approximated_count'],
                'total_count': group['total_count'],
                'approximation_percentage': approximation_percentage,
                'show_warning': approximation_percentage > 50 or weighted_avg_xirr is None
            }
        })
    
    return sorted(result, key=lambda x: x['xirr'] if x['xirr'] is not None else -999, reverse=True)

def generate_sample_data():
    """Generate sample data for testing purposes."""
    pass

def get_real_data():
    """Get real data from the system."""

# Note: Chart building functions (build_portfolio_growth_data, build_cash_flow_data, 
# build_forecast_data, build_twr_data, build_drawdown_data) moved to 
# src/report_builders/chart_builders.py

def main():
    """Generate HTML report using real investment system data."""
    start_time = time.perf_counter()
    
    # Add the project root to the Python path
    # Go up two directories from src/report_generators/ to reach project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)
    
    try:
        # Stage 1: Import modules
        stage_start = time.perf_counter()
        # Import investment system modules
        from src.data_manager.manager import DataManager
        from src.portfolio_lib.data_integration import PortfolioAnalysisManager
        from src.portfolio_lib.taxonomy_manager import TaxonomyManager
        from src.financial_analysis.analyzer import FinancialAnalyzer
        from src.html_reporter.reporter import HTMLReporter
        logger.info(f"Module imports completed in {time.perf_counter() - stage_start:.2f}s")
        
        # Stage 2: Load data
        logger.info("🔄 Loading real investment data...")
        stage_start = time.perf_counter()
        
        # Initialize core components
        config_path = 'config/settings.yaml'
        data_manager = DataManager(config_path=config_path)
        
        # Load actual data
        logger.info("📊 Processing portfolio data...")
        current_holdings = data_manager.get_holdings(latest_only=True)
        balance_sheet = data_manager.get_balance_sheet()
        logger.info(f"Data loading completed in {time.perf_counter() - stage_start:.2f}s")
        
        # Get latest total portfolio value from holdings (includes ALL assets: property, insurance, investments)
        # NOTE: Balance sheet Total_Assets_Calc_CNY only includes liquid assets, not fixed assets like property
        total_portfolio_value = 0
        if current_holdings is not None and not current_holdings.empty:
            # Check which value column is available
            if 'Market_Value_CNY' in current_holdings.columns:
                total_portfolio_value = current_holdings['Market_Value_CNY'].sum()
            elif 'Market_Value_Raw' in current_holdings.columns:
                total_portfolio_value = current_holdings['Market_Value_Raw'].sum()
                logger.warning("Using Market_Value_Raw instead of Market_Value_CNY")
            logger.info(f"✅ Total Portfolio Value from holdings (all assets): ¥{total_portfolio_value:,.0f}")
        
        # Fallback: Use balance sheet if holdings not available (shouldn't happen)
        if total_portfolio_value == 0 and balance_sheet is not None and not balance_sheet.empty:
            latest_balance = balance_sheet.iloc[-1]
            if 'Total_Assets_Calc_CNY' in balance_sheet.columns:
                total_portfolio_value = latest_balance.get('Total_Assets_Calc_CNY', 0)
                logger.warning(f"⚠️ Using balance sheet Total_Assets_Calc_CNY (liquid assets only): ¥{total_portfolio_value:,.0f}")
            elif 'Net_Worth_Calc_CNY' in balance_sheet.columns:
                total_portfolio_value = latest_balance.get('Net_Worth_Calc_CNY', 0)
                logger.warning(f"⚠️ Using balance sheet Net_Worth_Calc_CNY: ¥{total_portfolio_value:,.0f}")
            
        if total_portfolio_value == 0:
            logger.warning("⚠️  Could not determine portfolio value - using placeholder")
        
        # Calculate last month change (month-over-month percentage)
        last_month_change = 0.0
        if balance_sheet is not None and not balance_sheet.empty and len(balance_sheet) >= 2:
            try:
                # Get the latest two months of data
                latest_value = balance_sheet.iloc[-1].get('Total_Assets_Calc_CNY', 0) or balance_sheet.iloc[-1].get('Net_Worth_Calc_CNY', 0)
                previous_value = balance_sheet.iloc[-2].get('Total_Assets_Calc_CNY', 0) or balance_sheet.iloc[-2].get('Net_Worth_Calc_CNY', 0)
                
                if previous_value > 0 and latest_value > 0:
                    last_month_change = ((latest_value - previous_value) / previous_value) * 100
                    logger.info(f"Calculated last month change: {last_month_change:+.2f}% (¥{latest_value:,.0f} vs ¥{previous_value:,.0f})")
            except Exception as e:
                logger.warning(f"Could not calculate last month change: {e}")
        
        # Get real-time rates from Google Finance for System Status display
        # This uses Phase 1 Google Finance integration for current market data
        usd_cny_rate = None
        employer_stock_price_usd = None
        try:
            from src.data_manager.connectors.google_finance_connector import get_google_finance_connector
            connector = get_google_finance_connector()
            
            # Get real-time USD/CNY exchange rate
            usd_cny_rate = connector.get_exchange_rate('USD', 'CNY')
            if usd_cny_rate:
                logger.info(f"✓ Real-time USD/CNY rate from Google Finance: {usd_cny_rate:.4f}")
            
            # Get real-time AMZN stock price
            employer_stock_price_usd = connector.get_stock_price('AMZN')
            if employer_stock_price_usd:
                logger.info(f"✓ Real-time employer stock price from Google Finance: ${employer_stock_price_usd:.2f}")
                
        except Exception as e:
            logger.warning(f"Could not fetch real-time rates from Google Finance: {e}")
            # Fallback to Excel data if Google Finance fails
            if balance_sheet is not None and not balance_sheet.empty:
                try:
                    latest_row = balance_sheet.iloc[-1]
                    if 'Ref_USD_FX_Rate' in balance_sheet.columns:
                        usd_cny_rate = latest_row.get('Ref_USD_FX_Rate')
                        logger.info(f"Fallback: Using USD/CNY rate from Excel: {usd_cny_rate:.4f}")
                    if 'Ref_Employer_Stock_Price_USD' in balance_sheet.columns:
                        employer_stock_price_usd = latest_row.get('Ref_Employer_Stock_Price_USD')
                        logger.info(f"Fallback: Using employer stock price from Excel: ${employer_stock_price_usd:.2f}")
                except Exception as fallback_error:
                    logger.warning(f"Fallback to Excel data also failed: {fallback_error}")
        
        # Initialize portfolio analysis
        portfolio_manager = PortfolioAnalysisManager()
        
        # Get locale from environment or default to 'en'
        locale = os.environ.get('LOCALE', 'en')
        taxonomy_manager = TaxonomyManager(locale=locale)
        
        # Get real financial metrics (pass config directory)
        financial_analyzer = FinancialAnalyzer(config_dir='config')
        
        # Stage 3: Calculate metrics
        logger.info("💰 Calculating financial metrics...")
        stage_start = time.perf_counter()
        
        # Build real data dictionary
        real_data = build_real_data_dict(
            data_manager, 
            portfolio_manager, 
            taxonomy_manager, 
            financial_analyzer,
            current_holdings,
            total_portfolio_value,
            last_month_change,
            usd_cny_rate,
            employer_stock_price_usd
        )
        logger.info(f"Metrics calculation completed in {time.perf_counter() - stage_start:.2f}s")
        
        # Stage 4: Generate modular reports (HTML)
        stage_start = time.perf_counter()
        output_dir = 'output'
        
        # Initialize HTMLReporter and generate all 4 reports
        reporter = HTMLReporter()
        output_files = reporter.generate_reports(real_data, output_dir)
        
        logger.info(f"Report generation completed in {time.perf_counter() - stage_start:.2f}s")
        
        # Stage 5: Generate Markdown context file
        try:
            md_start = time.perf_counter()
            # Consolidate priority actions for markdown (top 7)
            consolidated_actions = reporter.consolidate_priority_actions(
                strategic_directive=real_data.get('strategic_directive') or {},
                recommendations=real_data.get('recommendations', []),
                alt_assets_recommendations=real_data.get('alt_assets_recommendations', []),
                rebalancing_data=real_data.get('rebalancing_data', {})
            )
            md_generator = MarkdownContextGenerator()
            md_content = md_generator.generate_markdown(real_data, consolidated_actions)
            
            # Add date suffix to filename (YYYYMMDD)
            date_str = datetime.now().strftime("%Y%m%d")
            markdown_filename = f'Personal_Investment_Analysis_Context_{date_str}.md'
            markdown_path = os.path.join(output_dir, markdown_filename)
            
            md_generator.save_to_file(md_content, markdown_path)
            logger.info(f"Markdown generation completed in {time.perf_counter() - md_start:.2f}s")
        except Exception as e:
            logger.warning(f"Markdown generation failed: {e}")
            markdown_path = None
        
        total_time = time.perf_counter() - start_time
        
        # Calculate total report size
        total_size_kb = 0
        for filename, filepath in output_files.items():
            if os.path.exists(filepath):
                size_kb = os.path.getsize(filepath) / 1024
                total_size_kb += size_kb
                logger.info(f'   ✅ {filename}: {size_kb:.1f} KB')
        
        logger.info(f'✅ All modular reports generated in: {output_dir}/')
        logger.info(f'📊 Total report size: {total_size_kb:.1f} KB')
        logger.info(f'📂 Generated {len(output_files)} HTML files: {", ".join(output_files.keys())}')
        logger.info(f'⏱️  Total execution time: {total_time:.2f}s')
        logger.info('📈 Reports include actual data from your investment system:')
        logger.info('   - Real portfolio values and metrics')
        logger.info('   - Actual asset allocation from your holdings')
        logger.info('   - Live classification from asset taxonomy')
        logger.info('   - Current financial performance indicators')
        if markdown_path:
            logger.info(f'📝 Markdown context generated: {markdown_path}')
        
        # Return status dictionary
        return {
            'success': True,
            'report_files': output_files,
            'total_size_kb': total_size_kb,
            'execution_time_s': total_time,
            'timestamp': datetime.now(),
            'markdown_path': markdown_path
        }
        
    except ImportError as e:
        logger.error(f'❌ Error importing investment system modules: {e}')
        logger.info('💡 Make sure all required modules are properly installed and configured.')
        return {
            'success': False,
            'error': f'Import error: {e}',
            'report_path': None
        }
    except Exception as e:
        logger.error(f'❌ Error generating real report: {e}')
        logger.info('💡 Check your Excel data files and configuration.')
        return {
            'success': False,
            'error': f'Generation error: {e}',
            'report_path': None
        }


def _calculate_sharpe_ratio_from_balance_sheet(data_manager: 'DataManager', 
                                               risk_free_rate: float = 0.035) -> str:
    """
    Calculate Sharpe ratio from balance sheet data with rolling period options.
    
    Args:
        data_manager: DataManager instance
        risk_free_rate: Annual risk-free rate (default 3.5%)
        
    Returns:
        String representation of Sharpe ratio (e.g., "1.23") or "N/A" if calculation fails
    """
    try:
        from src.financial_analysis.metrics import FinancialMetrics
        
        # Get balance sheet data
        balance_sheet = data_manager.get_balance_sheet()
        
        if balance_sheet is None or balance_sheet.empty:
            logger.warning("⚠️  Balance sheet is empty, cannot calculate Sharpe ratio")
            return "N/A"
        
        # Check if we have the required column
        if 'Total_Assets_Calc_CNY' not in balance_sheet.columns:
            logger.warning("⚠️  Total_Assets_Calc_CNY column not found in balance sheet")
            return "N/A"
        
        # Calculate period-to-period returns
        portfolio_values = balance_sheet['Total_Assets_Calc_CNY'].dropna()
        
        if len(portfolio_values) < 3:
            logger.warning(f"⚠️  Insufficient data points ({len(portfolio_values)}) to calculate Sharpe ratio")
            return "N/A"
        
        # Calculate simple returns (percentage change)
        returns = portfolio_values.pct_change().dropna()
        
        if len(returns) < 2:
            logger.warning("⚠️  Insufficient return data to calculate Sharpe ratio")
            return "N/A"
        
        # Initialize FinancialMetrics class and calculate Sharpe ratio
        metrics = FinancialMetrics(risk_free_rate=risk_free_rate)
        sharpe_ratio = metrics.calculate_sharpe_ratio(
            return_series=returns,
            risk_free_rate=risk_free_rate
        )
        
        # Log detailed calculation information
        logger.info("📊 Sharpe Ratio Calculation Details:")
        logger.info(f"  - Data points: {len(portfolio_values)}")
        logger.info(f"  - Return periods: {len(returns)}")
        logger.info(f"  - Mean return: {returns.mean():.4f}")
        logger.info(f"  - Return volatility: {returns.std():.4f}")
        logger.info(f"  - Risk-free rate: {risk_free_rate:.4f}")
        logger.info(f"  - Sharpe Ratio: {sharpe_ratio:.4f}")
        
        # Return formatted string
        if pd.notna(sharpe_ratio) and sharpe_ratio != 0.0:
            return f"{sharpe_ratio:.2f}"
        else:
            logger.warning("⚠️  Sharpe ratio calculation returned 0 or NaN")
            return "N/A"
            
    except Exception as e:
        logger.error(f"❌ Error calculating Sharpe ratio: {e}")
        import traceback
        traceback.print_exc()
        return "N/A"


def build_real_data_dict(
    data_manager: 'DataManager',
    portfolio_manager: 'PortfolioAnalysisManager', 
    taxonomy_manager: 'TaxonomyManager',
    financial_analyzer: 'FinancialAnalyzer',
    current_holdings: Any,
    total_portfolio_value: float,
    last_month_change: float,
    usd_cny_rate: float = None,
    employer_stock_price_usd: float = None,
    active_risk_profile: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build the data dictionary using real investment system data.
    
    Args:
        data_manager: DataManager instance
        portfolio_manager: PortfolioAnalysisManager instance
        taxonomy_manager: TaxonomyManager instance
        financial_analyzer: FinancialAnalyzer instance
        current_holdings: Current holdings DataFrame
        total_portfolio_value: Total portfolio value from balance sheet
        last_month_change: Month-over-month portfolio value change percentage
        usd_cny_rate: Current USD/CNY exchange rate
        employer_stock_price_usd: Current AMZN stock price in USD
        active_risk_profile: Optional override for risk profile name
        
    Returns:
        Dictionary containing real financial data for the HTML template
    """
    
    logger.info("🔍 Processing real portfolio metrics...")
    
    # Format total portfolio value
    total_portfolio_value_str = f"{total_portfolio_value:,.0f}" if total_portfolio_value else "0"
    
    # Calculate real financial metrics using passed FinancialAnalyzer
    try:
        logger.info("📊 Calculating real XIRR and financial metrics...")
        
        # Use the passed financial_analyzer instance to get real XIRR
        investment_results = financial_analyzer.analyze_investments('config')
        
        # Extract portfolio XIRR with metadata
        portfolio_xirr = investment_results.get('asset_performance', {}).get('portfolio_xirr')
        portfolio_xirr_metadata = investment_results.get('asset_performance', {}).get('portfolio_xirr_metadata', {})
        
        if portfolio_xirr is not None and pd.notna(portfolio_xirr):
            overall_xirr_str = f"{portfolio_xirr:.2f}"
            logger.info(f"✅ Real Portfolio XIRR calculated: {overall_xirr_str}%")
            
            # Extract metadata for transparency
            xirr_is_approximated = portfolio_xirr_metadata.get('is_approximated', False)
            xirr_method_used = portfolio_xirr_metadata.get('method_used', 'unknown')
            xirr_confidence = portfolio_xirr_metadata.get('confidence', 'unknown')
            
            if xirr_is_approximated:
                logger.warning(f"⚠️  Portfolio XIRR is approximated using method: {xirr_method_used}")
        else:
            overall_xirr_str = "N/A"
            xirr_is_approximated = True  # N/A is considered approximated
            xirr_method_used = "unavailable"
            xirr_confidence = "low"
            logger.warning("⚠️  Portfolio XIRR calculation returned None")
        
        # Get comprehensive lifetime asset performance data
        logger.info("📈 Calculating lifetime asset performance...")
        lifetime_performance_data = financial_analyzer.get_lifetime_asset_performance()
        logger.info(f"✅ Lifetime performance data calculated for {len(lifetime_performance_data)} assets")
        
        # Get realized vs unrealized gains analysis with detailed breakdown
        logger.info("💰 Calculating realized vs unrealized gains...")
        gains_analysis_data = financial_analyzer.get_realized_unrealized_gains()
        logger.info(f"✅ Gains analysis: Realized=¥{gains_analysis_data['realized_gains']:,.0f}, "
              f"Unrealized=¥{gains_analysis_data['unrealized_gains']:,.0f}, "
              f"Total=¥{gains_analysis_data['total_gains']:,.0f}")
        
        # Get asset-level gains breakdown for enhanced tables using builder
        logger.info("💰 Calculating asset-level gains breakdown...")
        from src.report_builders.kpi_builders import build_gains_analysis_data
        asset_gains_data = build_gains_analysis_data(data_manager, current_holdings)
        
        # Phase 4 Task 4.2: Validate gains calculation consistency
        logger.info("🔍 Validating gains calculation consistency...")
        gains_discrepancies = validate_gains_consistency(
            gains_analysis_data,
            lifetime_performance_data,
            tolerance=1000.0  # ¥1000 tolerance
        )
        if gains_discrepancies:
            logger.warning(f"⚠️  Found {len(gains_discrepancies)} sub-classes with calculation discrepancies")
        else:
            logger.info("✅ All gains calculations are consistent across methods")
            
        # Calculate real Sharpe ratio from balance sheet data
        logger.info("📊 Calculating Sharpe ratio from balance sheet data...")
        sharpe_ratio_str = _calculate_sharpe_ratio_from_balance_sheet(data_manager)
        logger.info(f"✅ Sharpe ratio calculated: {sharpe_ratio_str}")
        
        # TODO: Calculate real Max Drawdown in future enhancement
        max_drawdown_str = "-12.3"  # Placeholder - will be calculated in future enhancement
        
        # Store investment results for later use in performance tables
        investment_analysis_results = investment_results
        
        # Calculate additional balance sheet metrics using builder
        from src.report_builders.kpi_builders import build_kpi_metrics
        kpi_metrics = build_kpi_metrics(data_manager, current_holdings)
        total_liability_str = kpi_metrics['total_liability_str']
        total_net_assets_str = kpi_metrics['total_net_assets_str']
        total_liquid_portfolio_str = kpi_metrics['total_liquid_portfolio_str']
        
    except Exception as e:
        logger.warning(f"⚠️  Warning: Could not calculate real metrics: {e}")
        import traceback
        traceback.print_exc()
        overall_xirr_str = "N/A"
        sharpe_ratio_str = "N/A" 
        max_drawdown_str = "N/A"
        investment_analysis_results = None
        # Fallback data for new features
        lifetime_performance_data = []
        # Preserve existing gains_analysis_data if available, otherwise use fallback
        if 'gains_analysis_data' not in locals():
            gains_analysis_data = {
                "realized_gains": 0.0,
                "unrealized_gains": 0.0,
                "total_gains": 0.0,
                "status": "error",
                "subclass_breakdown": {}
            }
        asset_gains_data = {}
        # Fallback data for new balance sheet metrics
        total_liability_str = "0"
        total_net_assets_str = "0"
        total_liquid_portfolio_str = "0"
    
    # Process asset allocation
    logger.info("📊 Processing asset allocation...")
    
    try:
        if current_holdings is not None and not current_holdings.empty:
            logger.debug(f"Processing {len(current_holdings)} holdings for allocation...")
            
            # Convert holdings to list of dictionaries for classification
            holdings_list = current_holdings.reset_index().to_dict('records')
            logger.debug(f"Sample holding record: {holdings_list[0] if holdings_list else 'None'}")
            
            # For now, build simple allocation from holdings directly without taxonomy
            # since classify_holdings method is not available
            top_level_allocation, sub_class_allocation = build_allocation_from_holdings(current_holdings)
            
            # Build holdings table data (will be updated later with XIRR data)
            holdings_table = []  # Will be built later after individual_asset_performance is ready
            
        else:
            logger.warning("⚠️  No holdings data available")
            # Fallback to basic data
            top_level_allocation = {"labels": ["Unknown"], "values": [total_portfolio_value]}
            sub_class_allocation = {"labels": ["Unknown"], "values": [total_portfolio_value]}
            holdings_table = []
        
    except Exception as e:
        logger.warning(f"⚠️  Error processing allocations: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to basic data
        top_level_allocation = {"labels": ["Unknown"], "values": [total_portfolio_value]}
        sub_class_allocation = {"labels": ["Unknown"], "values": [total_portfolio_value]}
        holdings_table = []
    
    # Build portfolio growth data
    logger.info("📈 Building portfolio growth chart data...")
    portfolio_growth_json = build_portfolio_growth_percentage_data(data_manager)
    
    # Extract latest Portfolio Growth value for KPI display
    try:
        growth_data = json.loads(portfolio_growth_json)
        if growth_data.get('growth_values') and len(growth_data['growth_values']) > 0:
            latest_portfolio_growth = growth_data['growth_values'][-1]
            portfolio_growth_str = f"{latest_portfolio_growth:.2f}"
            logger.info(f"✅ Latest Portfolio Growth: {portfolio_growth_str}%")
        else:
            portfolio_growth_str = "N/A"
            logger.warning("⚠️  No Portfolio Growth data available")
    except Exception as e:
        logger.error(f"❌ Failed to extract Portfolio Growth value: {e}")
        portfolio_growth_str = "N/A"
    
    # Build cash flow data
    logger.info("💰 Building cash flow chart data...")
    cash_flow_json = build_cash_flow_data(data_manager)
    
    # Initialize forecast_json with fallback value
    forecast_json = '{"dates": [], "income_forecast": [], "expenses_forecast": [], "investments_forecast": [], "net_cash_flow": [], "message": "Forecast not generated"}'
    
    # Build forecast data with 90% confidence intervals (balanced performance/accuracy)
    try:
        logger.info("📅 Generating 12-month financial forecast (90% confidence level)...")
        forecast_start = time.perf_counter()
        
        # Import forecaster
        from src.financial_analysis.cash_flow_forecaster import CashFlowForecaster
        
        # Initialize forecaster with data manager
        forecaster = CashFlowForecaster(data_manager)
        
        # Fetch and process historical data
        logger.debug("  Fetching historical monthly cash flow data...")
        forecaster.fetch_and_process_historical_data()
        
        # Fit SARIMA models
        logger.debug("  Fitting SARIMA models...")
        forecaster.fit_sarima_models(seasonal_period=12)
        
        # Generate forecast with 90% confidence intervals (alpha=0.10)
        logger.debug("  Generating forecasts with 90% CI...")
        forecast_df = forecaster.forecast(periods=12, alpha=0.10, confidence_level='90')
        
        # Convert to JSON for template (using keys expected by template)
        forecast_data = {
            'dates': [date.strftime('%Y-%m-%d') for date in forecast_df.index],
            'income_forecast': forecast_df['Income_Forecast'].round(2).tolist(),
            'income_lower': forecast_df['Income_Lower_CI'].round(2).tolist(),
            'income_upper': forecast_df['Income_Upper_CI'].round(2).tolist(),
            'expenses_forecast': forecast_df['Expenses_Forecast'].round(2).tolist(),
            'expenses_lower': forecast_df['Expenses_Lower_CI'].round(2).tolist(),
            'expenses_upper': forecast_df['Expenses_Upper_CI'].round(2).tolist(),
            'investments_forecast': forecast_df['Investment_Forecast'].round(2).tolist(),
            'investments_lower': forecast_df['Investment_Lower_CI'].round(2).tolist(),
            'investments_upper': forecast_df['Investment_Upper_CI'].round(2).tolist(),
            'net_cash_flow': forecast_df['Net_Cash_Flow_Forecast'].round(2).tolist(),
            'net_cash_flow_lower': forecast_df['Net_Cash_Flow_Lower_CI'].round(2).tolist(),
            'net_cash_flow_upper': forecast_df['Net_Cash_Flow_Upper_CI'].round(2).tolist(),
            'confidence_level': '90',
            'method': 'SARIMA'
        }
        forecast_data = _sanitize_forecast_data_for_json(forecast_data)
        forecast_json = json.dumps(forecast_data, allow_nan=False)
        
        forecast_time = time.perf_counter() - forecast_start
        logger.info(f"✅ 12-month forecast completed in {forecast_time:.2f}s")
        
    except Exception as e:
        logger.warning(f"⚠️  Could not generate forecast: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to empty forecast
        forecast_json = '{"dates": [], "income_forecast": [], "expenses_forecast": [], "investments_forecast": [], "net_cash_flow": [], "message": "Forecast generation failed"}'
    
    # Build TWR data
    logger.info("📈 Building Time-Weighted Return data...")
    twr_json = build_twr_data(data_manager)
    
    # Extract latest TWR value for KPI display
    try:
        twr_data = json.loads(twr_json)
        if twr_data.get('twr_values') and len(twr_data['twr_values']) > 0:
            latest_twr = twr_data['twr_values'][-1]
            twr_str = f"{latest_twr:.2f}"
            twr_cash_flow_adjusted = twr_data.get('cash_flow_adjusted', False)
            logger.info(f"✅ Latest True TWR: {twr_str}% (Cash flow adjusted: {twr_cash_flow_adjusted})")
        else:
            twr_str = "N/A"
            twr_cash_flow_adjusted = False
            logger.warning("⚠️  No TWR data available")
    except Exception as e:
        logger.error(f"❌ Failed to extract TWR value: {e}")
        twr_str = "N/A"
        twr_cash_flow_adjusted = False
    
    # Build Drawdown data
    logger.debug("📉 Building Portfolio Drawdown History data...")
    drawdown_json = build_drawdown_data(data_manager)
    
    # Calculate dual-timeframe metrics (lifetime vs 12-month)
    logger.info("📊 Calculating dual-timeframe metrics (lifetime vs 12-month)...")
    try:
        # Prepare lifetime metrics dictionary with correct keys
        lifetime_metrics = {
            'xirr': overall_xirr_str,
            'sharpe_ratio': sharpe_ratio_str,
            'twr': twr_str,
            'portfolio_growth': portfolio_growth_str
        }
        
        # Get 12-month metrics from financial analyzer
        dual_metrics = financial_analyzer.get_dual_timeframe_metrics(lifetime_metrics, config_dir='config')
        
        # Add portfolio_growth to lifetime results (not calculated in dual_timeframe_metrics)
        dual_metrics['lifetime']['portfolio_growth'] = portfolio_growth_str
        # Note: 12-month growth is now calculated in dual_timeframe_metrics.py
        
        logger.info("✅ Dual-timeframe metrics calculated")
        logger.info(f"   Lifetime - XIRR: {dual_metrics['lifetime']['xirr']}, Sharpe: {dual_metrics['lifetime']['sharpe']}")
        logger.info(f"   12-Month - XIRR: {dual_metrics['trailing_12m']['xirr']}, Sharpe: {dual_metrics['trailing_12m']['sharpe']}, Growth: {dual_metrics['trailing_12m']['portfolio_growth']}, TWR: {dual_metrics['trailing_12m']['twr']}")
    except Exception as e:
        logger.warning(f"⚠️  Could not calculate dual-timeframe metrics: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to single timeframe
        dual_metrics = {
            'lifetime': {
                'xirr': overall_xirr_str,
                'sharpe': sharpe_ratio_str,
                'portfolio_growth': portfolio_growth_str,
                'twr': twr_str
            },
            'trailing_12m': {
                'xirr': "N/A",
                'sharpe': "N/A",
                'portfolio_growth': "N/A",
                'twr': "N/A"
            }
        }
    
    # Build performance aggregation data
    logger.info("📊 Building performance aggregation tables...")
    # Create individual asset performance list using real XIRR values from financial analysis
    # Build individual asset performance using builder
    from src.report_builders.kpi_builders import build_individual_asset_performance
    individual_asset_performance, xirr_diagnostics = build_individual_asset_performance(
        current_holdings,
        investment_analysis_results,
        taxonomy_manager,
        is_placeholder_asset,
        classify_asset_using_taxonomy,
        lifetime_performance_data  # UNIFIED: Pass cost_basis.py data as single source of truth
    )
    
    # Get special categories for later use in allocation logic
    special_categories = taxonomy_manager.config.get('special_categories', [])

    # Compact summary metrics for diagnostics (only success/warning/error counts)
    xirr_summary_counts = {k: len(v) for k, v in xirr_diagnostics.items() if k in ['success', 'warning', 'error']}

    # Build adjusted denominator excluding non-investable / non-performance assets
    non_investable_patterns = ['Deposit_', 'Cash_', 'Ins_', 'Pension_', 'Property_', 'Fund_US_Placeholder']
    def is_investable(asset_entry: dict) -> bool:
        aid = str(asset_entry.get('asset_id') or '')
        aname = str(asset_entry.get('asset_name') or '')
        target = aid + '|' + aname
        return not any(pat in target for pat in non_investable_patterns)

    # Collect assets considered in denominator (success+warning+error but filtered)
    filtered_assets = []
    for status_key in ['success', 'warning', 'error']:
        for entry in xirr_diagnostics.get(status_key, []):
            if is_investable(entry):
                filtered_assets.append((status_key, entry))

    denom = len(filtered_assets)
    raw_total = sum(xirr_summary_counts.values())
    xirr_summary_counts['total_tracked_raw'] = raw_total
    xirr_summary_counts['total_tracked_investable'] = denom
    if denom > 0:
        success_investable = len([1 for s,e in filtered_assets if s == 'success'])
        xirr_summary_counts['success_pct'] = round(100 * success_investable / denom, 1)
    else:
        xirr_summary_counts['success_pct'] = 0.0
    # Provide context counts for transparency
    xirr_summary_counts['excluded_non_investable'] = raw_total - denom
    
    # Aggregate performance data
    top_level_performance = aggregate_performance_by_top_level(individual_asset_performance)
    sub_class_performance = aggregate_performance_by_sub_class(individual_asset_performance)
    
    # Add XIRR and P&L data to current_holdings for recommendation engine and Tier Analysis
    # CRITICAL FIX: Use lifetime_performance_data (authoritative source) instead of individual_asset_performance
    # to ensure Dashboard and Action Compass show consistent XIRR values
    if current_holdings is not None and not current_holdings.empty and lifetime_performance_data:
        # Create lookups from lifetime_performance_data (same source as Dashboard)
        xirr_lookup = {}
        realized_pnl_lookup = {}
        unrealized_pnl_lookup = {}
        total_pnl_lookup = {}
        
        for perf in lifetime_performance_data:
            # Use Asset_Name for mapping as it's the index in some contexts, but Asset_ID is safer if available
            asset_name = perf.get('asset_name')
            
            if asset_name:
                xirr_lookup[asset_name] = perf.get('xirr_pct')
                realized_pnl_lookup[asset_name] = perf.get('realized_pnl', 0.0)
                unrealized_pnl_lookup[asset_name] = perf.get('unrealized_pnl', 0.0)
                total_pnl_lookup[asset_name] = perf.get('total_pnl', 0.0)
        
        # Add columns to holdings DataFrame using Asset_Name
        if 'Asset_Name' in current_holdings.columns:
            # Map XIRR for both usages (Recommendation Engine uses 'XIRR', Tier Analysis uses 'Lifetime_XIRR')
            current_holdings['XIRR'] = current_holdings['Asset_Name'].map(xirr_lookup)
            current_holdings['Lifetime_XIRR'] = current_holdings['XIRR']
            
            # Map P&L
            current_holdings['Realized_PnL'] = current_holdings['Asset_Name'].map(realized_pnl_lookup).fillna(0.0)
            current_holdings['Unrealized_PnL'] = current_holdings['Asset_Name'].map(unrealized_pnl_lookup).fillna(0.0)
            current_holdings['Total_PnL'] = current_holdings['Asset_Name'].map(total_pnl_lookup).fillna(0.0)
            
            xirr_count = current_holdings['XIRR'].notna().sum()
            logger.debug(f"Added XIRR and P&L columns to holdings: {xirr_count}/{len(current_holdings)} assets enriched")
        else:
            logger.warning("Asset_Name column not found in current_holdings, cannot add XIRR/P&L columns")
    
    # Add Unrealized_Gains column from asset_gains_data for recommendation engine
    # CRITICAL FIX: Use actual unrealized gains instead of calculating with wrong formula
    if current_holdings is not None and not current_holdings.empty and asset_gains_data:
        # Create unrealized gains lookup dictionary from asset_gains_data (same source as Dashboard)
        unrealized_gains_lookup = {}
        total_gains_lookup = {}
        for asset_name, gains_data in asset_gains_data.items():
            unrealized_gains_lookup[asset_name] = gains_data.get('unrealized_gains', 0.0)
            total_gains_lookup[asset_name] = gains_data.get('total_gains', 0.0)
        
        # Add Unrealized_Gains and Total_Gains columns to holdings DataFrame
        if 'Asset_Name' in current_holdings.columns:
            current_holdings['Unrealized_Gains'] = current_holdings['Asset_Name'].map(unrealized_gains_lookup)
            current_holdings['Total_Gains'] = current_holdings['Asset_Name'].map(total_gains_lookup)
            gains_count = current_holdings['Unrealized_Gains'].notna().sum()
            logger.debug(f"Added Unrealized_Gains and Total_Gains columns: {gains_count}/{len(current_holdings)} assets with gains data (from asset_gains_data)")
        else:
            logger.warning("Asset_Name column not found in current_holdings, cannot add Unrealized_Gains column")
    
    # Add Asset_Sub_Class column to holdings for rebalanceability filtering
    if current_holdings is not None and not current_holdings.empty:
        if 'Asset_Name' in current_holdings.columns and 'Asset_Type_Raw' in current_holdings.columns:
            # Apply classification to each holding
            sub_class_list = []
            for idx, holding in current_holdings.iterrows():
                asset_name = str(holding.get('Asset_Name', ''))
                asset_type = str(holding.get('Asset_Type_Raw', ''))
                top_class, sub_class = classify_asset_using_taxonomy(asset_name, asset_type, taxonomy_manager)
                sub_class_list.append(sub_class)
            
            current_holdings['Asset_Sub_Class'] = sub_class_list
            logger.debug(f"Added Asset_Sub_Class column to {len(current_holdings)} holdings")
        else:
            logger.warning("Asset_Name or Asset_Type_Raw columns not found, cannot add Asset_Sub_Class")
    
    # Build holdings table with XIRR information after performance data is ready
    # Phase 5 Task 5.4: Pass lifetime_performance_data (authoritative source) for P/L columns
    if current_holdings is not None and not current_holdings.empty:
        holdings_table = build_holdings_table_direct(
            current_holdings, 
            individual_asset_performance,
            lifetime_performance_data  # Phase 5: Pass lifetime performance data for P/L columns
        )
    else:
        holdings_table = []
    
    # PHASE 7.4.2: Fetch market thermometer and detect regime BEFORE rebalancing analysis
    # (moved from line 849 to ensure market_regime is available for dynamic target application)
    logger.info("🌡️  Fetching market thermometer indicators...")
    
    # Initialize all variables in outer scope to avoid NameError if exception occurs
    market_regime = None
    gold_analysis = {}
    gold_weighted = {'total_score': 0.0, 'recommendation': 'Unknown', 'breakdown': {}, 'status': 'error'}
    crypto_analysis = {}
    btc_weighted = {'total_score': 0.0, 'recommendation': 'Unknown', 'breakdown': {}, 'status': 'error'}
    eth_weighted = {'total_score': 0.0, 'recommendation': 'Unknown', 'breakdown': {}, 'status': 'error'}
    
    try:
        from src.investment_optimization.macro_analyzer import MacroAnalyzer
        from src.investment_optimization.indicator_regime_detector import IndicatorRegimeDetector
        
        market_regime = None  # Initialize to avoid UnboundLocalError
        macro_analyzer = MacroAnalyzer()
        market_thermometer = macro_analyzer.get_market_thermometer()
        logger.info("✅ Market thermometer data fetched successfully")
        
        # Fetch gold volatility indicators and recommendation
        logger.info("🏅 Fetching gold indicators and generating recommendation...")
        try:
            gold_analysis = macro_analyzer.get_gold_analysis()
            if gold_analysis.get('status') == 'success':
                logger.info(f"✅ Gold analysis complete - Recommendation: {gold_analysis['recommendation'].get('recommendation')}")
            else:
                logger.warning(f"⚠️  Gold analysis failed: {gold_analysis.get('error_message')}")
            
            # PHASE 3: Calculate Gold weighted score
            logger.info("🏅 Phase 3: Calculating Gold weighted scoring...")
            gold_weighted = macro_analyzer.calculate_gold_weighted_score()
            logger.info(f"✅ Gold weighted score: {gold_weighted.get('total_score', 0):.1f} → {gold_weighted.get('recommendation', 'Hold')}")
            
        except Exception as gold_err:
            logger.warning(f"⚠️  Gold analysis error: {gold_err}")
            gold_analysis = {'status': 'error', 'error_message': str(gold_err), 'indicators': {}, 'recommendation': {}}
            gold_weighted = {'total_score': 0.0, 'recommendation': 'Unknown', 'breakdown': {}, 'status': 'error'}
        
        # PHASE 2.4: Fetch crypto indicators and recommendations (BTC & ETH)
        logger.info("₿ Fetching crypto indicators and generating BTC/ETH recommendations...")
        try:
            crypto_analysis = macro_analyzer.get_crypto_analysis()
            if crypto_analysis.get('status') == 'success':
                btc_rec = crypto_analysis.get('btc_recommendation', {}).get('recommendation', 'N/A')
                eth_rec = crypto_analysis.get('eth_recommendation', {}).get('recommendation', 'N/A')
                logger.info(f"✅ Crypto analysis complete - BTC: {btc_rec}, ETH: {eth_rec}")
            else:
                logger.warning(f"⚠️  Crypto analysis failed: {crypto_analysis.get('error_message')}")
            
            # PHASE 3: Calculate Crypto weighted scores (using indicators from analysis)
            logger.info("₿ Phase 3: Calculating Crypto weighted scoring...")
            # Extract indicator data from crypto_analysis
            btc_vol_result = crypto_analysis.get('indicators', {}).get('btc_volatility', {'status': 'error', 'value': None})
            eth_vol_result = crypto_analysis.get('indicators', {}).get('eth_volatility', {'status': 'error', 'value': None})
            btc_eth_ratio_result = crypto_analysis.get('indicators', {}).get('btc_eth_ratio', {'status': 'error', 'value': None})
            btc_dominance_result = crypto_analysis.get('indicators', {}).get('btc_dominance', {'status': 'error', 'value': None})
            btc_qqq_ratio_result = crypto_analysis.get('indicators', {}).get('btc_qqq_ratio', {'status': 'error', 'value': None})
            crypto_fng_result = crypto_analysis.get('indicators', {}).get('crypto_fear_greed', {'status': 'error', 'value': None})
            
            # Calculate weighted scores for BTC and ETH (with asset-specific score inversions)
            btc_weighted = macro_analyzer.calculate_crypto_weighted_score(
                btc_vol_result, eth_vol_result, btc_eth_ratio_result,
                btc_dominance_result, btc_qqq_ratio_result, crypto_fng_result,
                asset_type='BTC'
            )
            eth_weighted = macro_analyzer.calculate_crypto_weighted_score(
                btc_vol_result, eth_vol_result, btc_eth_ratio_result,
                btc_dominance_result, btc_qqq_ratio_result, crypto_fng_result,
                asset_type='ETH'
            )
            logger.info(f"✅ BTC weighted score: {btc_weighted.get('total_score', 0):.1f} → {btc_weighted.get('recommendation', 'Hold')}")
            logger.info(f"✅ ETH weighted score: {eth_weighted.get('total_score', 0):.1f} → {eth_weighted.get('recommendation', 'Hold')}")
            
        except Exception as crypto_err:
            logger.warning(f"⚠️  Crypto analysis error: {crypto_err}")
            crypto_analysis = {
                'status': 'error', 
                'error_message': str(crypto_err), 
                'indicators': {},
                'btc_recommendation': {},
                'eth_recommendation': {}
            }
            btc_weighted = {'total_score': 0.0, 'recommendation': 'Unknown', 'breakdown': {}, 'status': 'error'}
            eth_weighted = {'total_score': 0.0, 'recommendation': 'Unknown', 'breakdown': {}, 'status': 'error'}
        
        # PHASE 3: Detect market regime using indicators
        logger.info("🎯 Detecting market regime...")
        regime_detector = IndicatorRegimeDetector()
        market_regime = regime_detector.detect_regime(market_thermometer)
        logger.info(f"✅ Market regime detected: {market_regime.get('regime_name_cn', 'N/A')} ({market_regime.get('regime_name', 'N/A')})")
        
    except Exception as e:
        logger.warning(f"⚠️  Failed to fetch market thermometer data: {e}")
        # Provide fallback data so report still generates
        market_thermometer = {
            'shiller_pe': {'value': None, 'zone': 'Unknown', 'level': -1, 'status': 'error', 'error_message': str(e)},
            'fear_greed': {'value': None, 'zone': 'Unknown', 'level': -1, 'status': 'error', 'error_message': str(e)},
            'vix': {'value': None, 'zone': 'Unknown', 'level': -1, 'status': 'error', 'error_message': str(e)},
            'buffett_us': {'value': None, 'zone': 'Unknown', 'level': -1, 'status': 'error', 'error_message': str(e)},
            'buffett_china': {'value': None, 'zone': 'Unknown', 'level': -1, 'status': 'error', 'error_message': str(e)},
            'buffett_japan': {'value': None, 'zone': 'Unknown', 'level': -1, 'status': 'error', 'error_message': str(e)},
            'buffett_europe': {'value': None, 'zone': 'Unknown', 'level': -1, 'status': 'error', 'error_message': str(e)},
            'last_updated': datetime.now().isoformat()
        }
        
        # Fallback regime detection (will likely use default regime)
        try:
            regime_detector = IndicatorRegimeDetector()
            market_regime = regime_detector.detect_regime(market_thermometer)
            logger.info("✅ Using default market regime due to fetch error")
        except Exception as regime_err:
            logger.error(f"❌ Failed to detect fallback regime: {regime_err}")
            market_regime = None
    
    # Sprint 4: Build rebalancing analysis (SIMPLIFIED: uses Risk Profile only, no market regime override)
    # Market regime is still used for recommendations, but rebalancing uses pure Risk Profile settings
    logger.debug(f"🎯 Sprint 4: Building rebalancing recommendations... (Profile: {active_risk_profile or 'Default'})")
    rebalancing_data = build_rebalancing_analysis(
        current_holdings, 
        market_regime=None,  # Disabled: Action Compass now purely reflects Logic Studio settings
        taxonomy_manager=taxonomy_manager,
        active_risk_profile=active_risk_profile
    )
    
    # Build Tier Analysis data with P&L (for Markdown Context Report)
    logger.info("📊 Building Tier Analysis with P&L data...")
    tier_analysis = build_tier_analysis(
        holdings_df=current_holdings,
        taxonomy_manager=taxonomy_manager,
        total_portfolio_value=None # Let builder calculate rebalanceable value
    )
    
    # Action Compass: Generate capital allocation suggestion
    logger.debug("🧭 Action Compass: Generating capital allocation suggestion...")
    capital_allocation_suggestion = generate_capital_allocation_suggestion(rebalancing_data)
    
    # Action Compass: Generate proportional allocation (Phase 1 Enhancement)
    logger.debug("🧭 Action Compass: Calculating proportional allocation...")
    proportional_allocation = {}
    sub_class_breakdowns = []
    try:
        from src.recommendation_engine.allocation_optimizer import ProportionalAllocationOptimizer
        from src.recommendation_engine.sub_class_analyzer import SubClassAnalyzer
        
        # Use a reference capital amount for pre-calculation (e.g., 100K CNY)
        reference_capital = 100000
        
        optimizer = ProportionalAllocationOptimizer()
        proportional_result = optimizer.calculate_proportional_allocation(
            new_capital=reference_capital,
            rebalancing_data=rebalancing_data,
            strategy='drift_weighted',
            min_allocation_pct=10.0
        )
        
        if proportional_result.get('allocations'):
            total_impact = proportional_result.get('total_impact', {})
            proportional_allocation = {
                'allocations': proportional_result['allocations'],
                'reference_capital': reference_capital,
                'rebalanceable_value': rebalancing_data.get('rebalanceable_value', 0),
                'total_drift_before': total_impact.get('current_total_drift', 0),
                'total_drift_after': total_impact.get('new_total_drift', 0),
                'total_drift_improvement': total_impact.get('drift_reduction', 0)
            }
            
            # Generate sub-class breakdowns for each allocated class
            analyzer = SubClassAnalyzer()
            for allocation in proportional_result['allocations']:
                asset_class = allocation['asset_class']
                allocation_amount = allocation['amount']
                
                sub_breakdown = analyzer.generate_sub_class_breakdown(
                    target_asset_class=asset_class,
                    allocation_amount=allocation_amount,
                    rebalancing_data=rebalancing_data
                )
                
                if sub_breakdown.get('sub_allocations'):
                    sub_class_breakdowns.append(sub_breakdown)
            
            logger.info(f"Generated proportional allocation for {len(proportional_result['allocations'])} asset classes")
        else:
            logger.info("No proportional allocation generated (portfolio balanced)")
    except Exception as e:
        logger.warning(f"Could not generate proportional allocation: {e}")
        proportional_allocation = {}
        sub_class_breakdowns = []
    
    # Add proportional_allocation to rebalancing_data for recommendation engine
    if proportional_allocation and proportional_allocation.get('allocations'):
        rebalancing_data['proportional_allocation'] = proportional_allocation['allocations']
        rebalancing_data['reference_capital'] = proportional_allocation.get('reference_capital', 100000)
        logger.debug(f"Added {len(proportional_allocation['allocations'])} proportional allocations to rebalancing_data")
    
    # Action Compass: Generate RSU alerts
    logger.debug("🧭 Action Compass: Checking RSU vesting schedule...")
    try:
        from src.risk_management.rsu_monitor import RSUMonitor
        rsu_monitor = RSUMonitor()
        rsu_alerts = rsu_monitor.get_actionable_alerts(lookback_days=30, lookahead_days=30)
        logger.info(f"Found {len(rsu_alerts)} actionable RSU alerts")
    except Exception as e:
        logger.warning(f"Could not load RSU alerts: {e}")
        rsu_alerts = []
    
    # PHASE 7.4.2 NOTE: Market regime detection moved to before rebalancing analysis (see line ~768)
    # This ensures dynamic targets are applied during rebalancing drift calculation
    
    # Action Compass: Generate Phase 2 Multi-Dimensional Recommendations
    logger.debug("🧭 Action Compass Phase 2: Generating multi-dimensional recommendations...")
    recommendations = []
    recommendation_stats = {}
    strategic_directive = None  # Initialize here to avoid NameError if try block fails
    try:
        from src.recommendation_engine.recommendation_engine import RecommendationEngine
        
        # Initialize recommendation engine
        rec_engine = RecommendationEngine()
        
        # Prepare performance data dictionary
        performance_dict = {
            'portfolio_xirr': portfolio_xirr if 'portfolio_xirr' in locals() else None,
            'overall_xirr_str': overall_xirr_str
        }
        
        # DEBUG: Log market_regime contents before passing to RecommendationEngine
        if market_regime:
            logger.info(f"🔍 DEBUG market_regime keys: {list(market_regime.keys())}")
            logger.info(f"🔍 DEBUG market_regime.regime_name: {market_regime.get('regime_name')}")
            strategic_recs = market_regime.get('strategic_recommendations', [])
            logger.info(f"🔍 DEBUG market_regime.strategic_recommendations count: {len(strategic_recs)}")
        else:
            logger.warning("🔍 DEBUG: market_regime is None!")
        
        # ACTION COMPASS V2.0 PHASE 1: Generate all recommendations and strategic directive
        result = rec_engine.generate_all_recommendations(
            rebalancing_data=rebalancing_data,
            holdings_df=current_holdings,
            performance_data=performance_dict,
            portfolio_value=total_portfolio_value,
            market_regime=market_regime  # PHASE 3: Pass detected regime
        )
        
        # Extract recommendations and strategic directive
        recommendations = result.get('recommendations', []) if isinstance(result, dict) else result
        strategic_directive = result.get('strategic_directive') if isinstance(result, dict) else None
        
        # DEBUG: Log strategic_directive result
        logger.info(f"🔍 DEBUG strategic_directive is: {'POPULATED' if strategic_directive else 'None'}")
        
        # Calculate recommendation statistics
        if recommendations:
            recommendation_stats = {
                'total_count': len(recommendations),
                'high_priority_count': sum(1 for r in recommendations if r.get('priority', 0) >= 80),
                'total_potential_impact': sum(
                    r.get('impact', {}).get('dollar_value', 0) 
                    for r in recommendations
                ),
                'avg_priority': sum(r.get('priority', 0) for r in recommendations) / len(recommendations)
            }
            logger.info(
                f"Generated {len(recommendations)} recommendations "
                f"({recommendation_stats['high_priority_count']} high priority)"
            )
            if strategic_directive:
                logger.info(f"✅ Strategic Directive: {strategic_directive.get('core_objective_cn', 'N/A')}")
        else:
            logger.info("No recommendations generated (portfolio in good state)")
    except Exception as e:
        logger.warning(f"Could not generate Phase 2 recommendations: {e}")
        logger.debug("Recommendation generation error details:", exc_info=True)
        recommendations = []
        recommendation_stats = {}
    
    # Calculate insurance value for portfolio differences explanation
    insurance_value = 0
    if current_holdings is not None and not current_holdings.empty:
        for idx, holding in current_holdings.iterrows():
            asset_name = holding.get('Asset_Name', 'Unknown')
            asset_type = holding.get('Asset_Type_Raw', 'Unknown')
            market_value = holding.get('Market_Value_CNY', 0) or 0

            # Use taxonomy classification to identify insurance assets
            top_level, sub_class = classify_asset_using_taxonomy(asset_name, asset_type, taxonomy_manager)
            
            # Check if it's an insurance asset (same logic as performance exclusion)
            english_to_chinese = {'Insurance': 'Insurance', 'Real Estate': 'Real Estate'}
            chinese_top_level = english_to_chinese.get(top_level, top_level)
            is_insurance = chinese_top_level in special_categories or sub_class == 'Insurance Products'
            
            if is_insurance:
                insurance_value += market_value
    
    
    # Build final data dictionary
    real_data = {
        # Report metadata
        'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        
        # KPI Metrics
        'total_portfolio_value': total_portfolio_value_str,
        'total_portfolio_value_numeric': total_portfolio_value,  # For template calculations
        'total_liability': total_liability_str,
        'total_net_assets': total_net_assets_str,
        'total_liquid_portfolio': total_liquid_portfolio_str,
        'overall_xirr': overall_xirr_str,
        'portfolio_growth': portfolio_growth_str,  # Portfolio Growth (includes cash flows)
        'true_twr': twr_str,  # True Time-Weighted Return (cash flow adjusted)
        'twr_cash_flow_adjusted': twr_cash_flow_adjusted,
        'sharpe_ratio': sharpe_ratio_str,
        'last_month_change': last_month_change,  # Month-over-month portfolio change
        
        # Dual-timeframe metrics (lifetime vs 12-month)
        'dual_metrics': dual_metrics,
        
        # Market Thermometer Data
        'market_thermometer': market_thermometer,
        
        # Gold Volatility Analysis (Phase 1.2: Alternative Assets)
        'gold_analysis': gold_analysis,
        
        # PHASE 2.4: Crypto Volatility Analysis (BTC & ETH)
        'crypto_analysis': crypto_analysis,
        
        # PHASE 3: Alternative Assets Weighted Recommendations (Gold, BTC, ETH)
        'alt_assets_recommendations': [
            {
                'asset_name': 'Gold',
                'recommendation': gold_analysis.get('recommendation', {}),
                'weighted_data': gold_weighted
            },
            {
                'asset_name': 'Bitcoin (BTC)',
                'recommendation': crypto_analysis.get('btc_recommendation', {}),
                'weighted_data': btc_weighted
            },
            {
                'asset_name': 'Ethereum (ETH)',
                'recommendation': crypto_analysis.get('eth_recommendation', {}),
                'weighted_data': eth_weighted
            }
        ],
        
        # PHASE 3: Market Regime Data (for Action Compass display)
        'market_regime': market_regime,
        
        # XIRR Metadata for transparency (Phase 3 enhancement)
        'xirr_metadata': {
            'is_approximated': xirr_is_approximated,
            'method_used': xirr_method_used,
            'confidence': xirr_confidence,
            'show_warning': xirr_is_approximated or overall_xirr_str == "N/A"
        },
        
        # Portfolio value differences explanation
        'insurance_value': insurance_value,
        
        # Allocation data (JSON strings for Chart.js)
        'top_level_allocation_json': json.dumps(top_level_allocation),
        'sub_class_allocation_json': json.dumps(sub_class_allocation),
        
        # Performance Chart Data (JSON strings for Chart.js)
        'top_level_performance_json': json.dumps({
            "labels": [item['class_name'] for item in top_level_performance if item['xirr'] is not None],
            "values": [item['xirr'] for item in top_level_performance if item['xirr'] is not None]
        }),
        'sub_class_performance_json': json.dumps({
            "labels": [item['class_name'] for item in sub_class_performance if item['xirr'] is not None],
            "values": [item['xirr'] for item in sub_class_performance if item['xirr'] is not None]
        }),
        
        # Sprint 3: Historical Performance data
        'portfolio_growth_json': portfolio_growth_json,
        'cash_flow_json': cash_flow_json,
        'forecast_json': forecast_json,  # Forecast disabled for performance
        'twr_json': twr_json,  # Time-Weighted Return data
        'drawdown_json': drawdown_json,  # Portfolio Drawdown History data
        'top_level_performance': top_level_performance,
        'sub_class_performance': sub_class_performance,
        
        # Sprint 4: Rebalancing Analysis
        'rebalancing_data': rebalancing_data,
        'tier_analysis': tier_analysis,  # Add Tier Analysis data
        
        
        # Action Compass: Capital Allocation Suggestion
        'capital_allocation_suggestion': capital_allocation_suggestion, # This line must be present
        
        # Action Compass: Proportional Allocation (Phase 1 Enhancement)
        'proportional_allocation': proportional_allocation,
        'sub_class_breakdowns': sub_class_breakdowns,
        
        # Action Compass: RSU Alerts
        'rsu_alerts': rsu_alerts, # This line must be present
        
        # Action Compass Phase 2: Multi-Dimensional Recommendations
        'recommendations': recommendations,
        'recommendation_stats': recommendation_stats,
        
        # ACTION COMPASS V2.0 PHASE 1: Strategic Directive
        'strategic_directive': strategic_directive,
        
        # Holdings table
        'holdings': holdings_table,

        # XIRR diagnostics for lightweight HTML table
        'xirr_summary_counts': xirr_summary_counts,
        'xirr_diagnostics': xirr_diagnostics,
        
        # New Feature: Lifetime Asset Performance
        'lifetime_performance_data': lifetime_performance_data,
        
        # New Feature: Realized vs Unrealized Gains
        'gains_analysis_data': gains_analysis_data,
        'asset_gains_data': asset_gains_data
    }
    
    # PHASE 2.4: Run UnifiedDataPreparer validation (Option A: Conservative)
    # This runs validation alongside existing calculations without replacing them
    logger.info("🔍 PHASE 2.4: Running UnifiedDataPreparer validation...")
    try:
        # Initialize UnifiedDataPreparer
        unified_preparer = UnifiedDataPreparer(
            data_manager=data_manager,
            portfolio_manager=portfolio_manager,
            taxonomy_manager=taxonomy_manager,
            financial_analyzer=financial_analyzer
        )
        
        # Prepare validation data (this runs 7-step pipeline)
        validation_start = time.perf_counter()
        validated_data = unified_preparer.prepare_all_report_data()
        validation_time = time.perf_counter() - validation_start
        
        # Extract validation report and checksums
        validation_report = validated_data.get('validation_report', {})
        checksums = validated_data.get('checksums', {})
        
        # Log validation results
        overall_status = validation_report.get('overall_status', 'UNKNOWN')
        summary = validation_report.get('summary', {})
        
        if overall_status == 'PASS':
            logger.info(f"   ✅ VALIDATION PASSED: All {summary.get('total_checks', 0)} checks passed ({validation_time:.2f}s)")
        elif overall_status == 'WARN':
            logger.warning(f"   ⚠️  VALIDATION WARNING: {summary.get('warnings', 0)} warnings found ({validation_time:.2f}s)")
        elif overall_status == 'FAIL':
            logger.error(f"   ❌ VALIDATION FAILED: {summary.get('failures', 0)} failures found ({validation_time:.2f}s)")
            # Log details of failures
            for check in validation_report.get('checks', []):
                if check.get('status') == 'FAIL':
                    logger.error(f"      • {check.get('check')}: {check.get('message')}")
        
        # Log validation results
        logger.info(f"✅ UnifiedDataPreparer validation completed in {validation_time:.2f}s")
        logger.info(f"   - Checksum match: {validation_report.get('checksum_match', False)}")
        logger.info(f"   - Missing keys: {len(validation_report.get('missing_keys', []))}")
        
        # Add validation data to real_data dictionary
        real_data['validation_report'] = validation_report
        real_data['checksums'] = checksums
        
        logger.debug(f"   Checksums: {checksums}")

        # Merge Tier Analysis data into real_data (Phase 6 Feature)
        if 'tier_analysis' in validated_data:
            real_data['tier_analysis'] = validated_data['tier_analysis']
            logger.info("✅ Merged tier_analysis data into real_data")
        
    except Exception as e:
        logger.warning(f"⚠️  UnifiedDataPreparer validation failed: {e}")
        import traceback
        traceback.print_exc()
        # Add empty validation data so templates don't break
        real_data['validation_report'] = {
            'overall_status': 'ERROR',
            'summary': {
                'total_checks': 0,
                'passed': 0,
                'warnings': 0,
                'failures': 0
            },
            'checks': [],
            'error_message': str(e)
        }
        real_data['checksums'] = {}
    
    # Add reference rates for System Status display
    real_data['usd_cny_rate'] = usd_cny_rate
    real_data['employer_stock_price_usd'] = employer_stock_price_usd
    
    return real_data


def build_allocation_data(classified_holdings: List[Dict]) -> tuple:
    """Build allocation data for charts from classified holdings."""
    
    # Aggregate by top-level categories
    top_level_agg = {}
    sub_class_agg = {}
    
    for holding in classified_holdings:
        # Get values
        market_value = holding.get('Market_Value_CNY', 0) or 0
        level_1 = holding.get('Level_1', 'Unknown')
        level_2 = holding.get('Level_2', 'Unknown')
        
        # Aggregate top-level
        if level_1 in top_level_agg:
            top_level_agg[level_1] += market_value
        else:
            top_level_agg[level_1] = market_value
            
        # Aggregate sub-class
        if level_2 in sub_class_agg:
            sub_class_agg[level_2] += market_value
        else:
            sub_class_agg[level_2] = market_value
    
    # Convert to chart format
    top_level_allocation = {
        "labels": list(top_level_agg.keys()),
        "values": list(top_level_agg.values())
    }
    
    sub_class_allocation = {
        "labels": list(sub_class_agg.keys()),
        "values": list(sub_class_agg.values())
    }
    
    return top_level_allocation, sub_class_allocation


def build_holdings_table(classified_holdings: List[Dict]) -> List[Dict[str, str]]:
    """Build holdings table data from classified holdings."""
    
    holdings_table = []
    total_value = sum(holding.get('Market_Value_CNY', 0) or 0 for holding in classified_holdings)
    
    for holding in classified_holdings:
        asset_name = holding.get('Asset_Name', holding.get('asset_name', 'Unknown'))
        asset_class = holding.get('Level_2', holding.get('Level_1', 'Unknown'))
        market_value = holding.get('Market_Value_CNY', 0) or 0
        
        # Calculate percentage
        portfolio_percentage = (market_value / total_value * 100) if total_value > 0 else 0
        
        # Determine status
        if holding.get('Level_1') == 'Unknown' or holding.get('Level_2') == 'Unknown':
            status = 'Unmapped'
        elif 'Real Estate' in str(asset_class) and ('Primary' in str(asset_name) or '房产' in str(asset_name)):
            status = 'Non-Rebalanceable'
        else:
            status = 'Active'
        
        holdings_table.append({
            'asset_name': asset_name,
            'asset_class': asset_class,
            'market_value': f"{market_value:,.0f}",
            'portfolio_percentage': f"{portfolio_percentage:.1f}",
            'status': status
        })
    
    # Sort by market value (descending)
    holdings_table.sort(key=lambda x: float(x['market_value'].replace(',', '')), reverse=True)
    
    return holdings_table


def generate_reports_for_markdown_only():
    """
    Generate only the data needed for markdown context generation.
    
    This is a lightweight version of main() that skips HTML generation and returns
    just the real_data dictionary and consolidated_actions needed for markdown.
    
    Returns:
        Tuple of (real_data dict, consolidated_actions list)
    """
    logger.info("📊 Generating data for markdown context...")
    
    # Add the project root to the Python path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)
    
    # Import investment system modules
    from src.data_manager.manager import DataManager
    from src.portfolio_lib.data_integration import PortfolioAnalysisManager
    from src.portfolio_lib.taxonomy_manager import TaxonomyManager
    from src.financial_analysis.analyzer import FinancialAnalyzer
    from src.html_reporter.reporter import HTMLReporter
    
    # Initialize core components
    config_path = 'config/settings.yaml'
    data_manager = DataManager(config_path=config_path)
    
    # Load actual data
    current_holdings = data_manager.get_holdings(latest_only=True)
    balance_sheet = data_manager.get_balance_sheet()
    
    # Get latest total portfolio value
    total_portfolio_value = 0
    if balance_sheet is not None and not balance_sheet.empty:
        latest_balance = balance_sheet.iloc[-1]
        if 'Total_Assets_Calc_CNY' in balance_sheet.columns:
            total_portfolio_value = latest_balance.get('Total_Assets_Calc_CNY', 0)
        elif 'Net_Worth_Calc_CNY' in balance_sheet.columns:
            total_portfolio_value = latest_balance.get('Net_Worth_Calc_CNY', 0)
    
    if total_portfolio_value == 0 and current_holdings is not None:
        if 'Market_Value_CNY' in current_holdings.columns:
            total_portfolio_value = current_holdings['Market_Value_CNY'].sum()
        elif 'Market_Value_Raw' in current_holdings.columns:
            total_portfolio_value = current_holdings['Market_Value_Raw'].sum()
    
    # Calculate last month change
    last_month_change = 0.0
    if balance_sheet is not None and not balance_sheet.empty and len(balance_sheet) >= 2:
        latest_value = balance_sheet.iloc[-1].get('Total_Assets_Calc_CNY', 0) or balance_sheet.iloc[-1].get('Net_Worth_Calc_CNY', 0)
        previous_value = balance_sheet.iloc[-2].get('Total_Assets_Calc_CNY', 0) or balance_sheet.iloc[-2].get('Net_Worth_Calc_CNY', 0)
        if previous_value > 0 and latest_value > 0:
            last_month_change = ((latest_value - previous_value) / previous_value) * 100
    
    # Initialize managers
    portfolio_manager = PortfolioAnalysisManager()
    taxonomy_manager = TaxonomyManager()
    financial_analyzer = FinancialAnalyzer()
    
    # Build real data dictionary (reuse existing function)
    real_data = build_real_data_dict(
        data_manager=data_manager,
        portfolio_manager=portfolio_manager,
        taxonomy_manager=taxonomy_manager,
        financial_analyzer=financial_analyzer,
        current_holdings=current_holdings,
        total_portfolio_value=total_portfolio_value,
        last_month_change=last_month_change
    )
    
    # Consolidate priority actions
    reporter = HTMLReporter()
    consolidated_actions = reporter.consolidate_priority_actions(
        strategic_directive=real_data.get('strategic_directive') or {},
        recommendations=real_data.get('recommendations', []),
        alt_assets_recommendations=real_data.get('alt_assets_recommendations', []),
        rebalancing_data=real_data.get('rebalancing_data', {})
    )
    
    logger.info("✅ Data preparation complete")
    return real_data, consolidated_actions


if __name__ == '__main__':
    sys.exit(main())
