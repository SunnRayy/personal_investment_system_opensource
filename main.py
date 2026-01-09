#!/usr/bin/env python3
"""
Personal Investment System - Unified Command Center

This is the single entry point for all system operations.
Replaces multiple run_*.py scripts with a unified CLI interface.

Usage:
    python main.py --help                    # Show all commands
    python main.py run-all                   # Run comprehensive analysis
    python main.py generate-report           # Generate HTML report only
    python main.py update-global-data        # Update Global Markets data
    python main.py create-snapshots          # Create portfolio snapshots
"""

import os
import sys
import logging
import click
from datetime import datetime
from pathlib import Path

# Set up project root and imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


# =============================================================================
# Helper Functions from run_comprehensive_analysis.py
# =============================================================================

def setup_logging(verbose=False):
    """Configure logging for the comprehensive analysis."""
    # Set root logger level
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create formatters
    detailed_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    simple_formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    # File handler - detailed, captures everything
    file_handler = logging.FileHandler('logs/comprehensive_analysis.log', mode='a')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler - simpler, only shows warnings and above unless verbose
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO if verbose else logging.WARNING)
    console_handler.setFormatter(simple_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture everything at root level
    root_logger.handlers.clear()  # Clear any existing handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Suppress overly verbose loggers
    logging.getLogger('src.financial_analysis.performance_calculator').setLevel(logging.WARNING)
    logging.getLogger('src.portfolio_lib.taxonomy_manager').setLevel(logging.WARNING)
    logging.getLogger('src.data_manager').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)


def get_fund_file_path():
    """Get fund file path from settings.yaml."""
    import yaml
    try:
        with open('config/settings.yaml', 'r') as f:
            config = yaml.safe_load(f)
        return config.get('data_files', {}).get('fund_transactions', {}).get('path', 'data/funding_transactions.xlsx')
    except:
        return 'data/funding_transactions.xlsx'


def test_global_markets_automation(logger):
    """Test Global Markets automation pipeline."""
    try:
        from src.data_manager.readers import read_raw_fund_sheets
        from src.data_manager.cleaners import process_raw_holdings, process_raw_transactions
        
        fund_file_path = get_fund_file_path()
        
        if not os.path.exists(fund_file_path):
            logger.warning(f"⚠️  Global Markets file not found: {fund_file_path}")
            return False
        
        raw_holdings, raw_transactions = read_raw_fund_sheets(fund_file_path)
        
        if raw_holdings is None or raw_transactions is None:
            logger.error("❌ Failed to read raw fund data")
            return False
        
        processed_holdings = process_raw_holdings(raw_holdings)
        processed_transactions = process_raw_transactions(raw_transactions)
        
        logger.info(f"✅ Global Markets validation: {len(processed_holdings)} holdings, {len(processed_transactions)} transactions")
        return len(processed_holdings) > 0
        
    except Exception as e:
        logger.error(f"❌ Global Markets automation test failed: {e}")
        return False


def test_schwab_automation(logger):
    """Test Schwab CSV automation pipeline."""
    try:
        from src.data_manager.readers import read_schwab_data
        import yaml
        
        with open('config/settings.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        schwab_data = read_schwab_data(config)
        holdings = schwab_data.get('holdings')
        transactions = schwab_data.get('transactions')
        
        if holdings is None and transactions is None:
            logger.warning("⚠️  No Schwab CSV files found")
            return True
        
        holdings_count = len(holdings) if holdings is not None else 0
        transactions_count = len(transactions) if transactions is not None else 0
        logger.info(f"✅ Schwab validation: {holdings_count} holdings, {transactions_count} transactions")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Schwab automation test failed: {e}")
        return False


def validate_schwab_data(logger):
    """Validate that Schwab CSV files are available and readable."""
    logger.info("📊 Validating Schwab CSV data availability...")
    
    try:
        from src.data_manager.readers import read_schwab_data
        import yaml
        
        with open('config/settings.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        schwab_data = read_schwab_data(config)
        holdings = schwab_data.get('holdings')
        transactions = schwab_data.get('transactions')
        
        if holdings is not None or transactions is not None:
            holdings_count = len(holdings) if holdings is not None else 0
            transactions_count = len(transactions) if transactions is not None else 0
            logger.info(f"✅ Schwab data found: {holdings_count} holdings, {transactions_count} transactions")
            return True
        else:
            logger.warning("⚠️  No Schwab CSV files found - continuing with existing data")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error validating Schwab data: {e}")
        return False


def load_existing_processed_data(logger, fund_file_path):
    """
    Load existing processed transaction data when raw paste sheets are empty.
    
    Args:
        logger: Logger instance
        fund_file_path: Path to the fund data Excel file
        
    Returns:
        Tuple of (holdings_df, transactions_df) from processed sheets, or (None, None) if unavailable
    """
    try:
        import pandas as pd
        
        holdings_df = None
        transactions_df = None
        
        try:
            # Try to read existing processed holdings sheet (基金持仓汇总)
            holdings_df = pd.read_excel(fund_file_path, sheet_name='基金持仓汇总')
            if not holdings_df.empty:
                logger.info(f"⚠️  Using existing processed holdings data ({len(holdings_df)} records)")
            else:
                holdings_df = None
        except Exception as e:
            logger.debug(f"Could not load existing processed holdings: {e}")
        
        try:
            # Try to read existing processed transactions sheet (基金交易记录)
            transactions_df = pd.read_excel(fund_file_path, sheet_name='基金交易记录')
            if not transactions_df.empty:
                logger.info(f"⚠️  Using existing processed transactions data ({len(transactions_df)} records)")
            else:
                transactions_df = None
        except Exception as e:
            logger.debug(f"Could not load existing processed transactions: {e}")
        
        return holdings_df, transactions_df
        
    except Exception as e:
        logger.debug(f"Error loading existing processed data: {e}")
        return None, None


def run_fund_data_update_logic(logger):
    """Run Global Markets data update automation.
    
    If raw paste sheets (raw_holdings_paste, raw_transactions_paste) are empty or missing,
    gracefully continues with existing processed transaction data instead of failing.
    This allows the system to remain functional when users haven't provided new data.
    """
    logger.info("🏦 Step 1: Running Global Markets Data Update...")
    
    try:
        from src.data_manager.readers import read_raw_fund_sheets
        from src.data_manager.cleaners import process_raw_holdings, process_raw_transactions
        from src.data_manager.fund_data_writer import write_processed_fund_data
        
        fund_file_path = get_fund_file_path()
        if not os.path.exists(fund_file_path):
            logger.warning(f"⚠️  Fund data file not found: {fund_file_path}")
            return False
        
        logger.info("Processing raw fund data from paste sheets...")
        raw_holdings, raw_transactions = read_raw_fund_sheets(fund_file_path)
        
        # If raw data is not available, gracefully use existing processed data
        if raw_holdings is None or raw_transactions is None:
            logger.warning("⚠️  Raw paste sheets are empty or unavailable")
            logger.info("Attempting to use existing processed transaction data...")
            
            existing_holdings, existing_transactions = load_existing_processed_data(logger, fund_file_path)
            
            # Also try demo-style sheet names (Holdings/Transactions)
            if existing_holdings is None:
                try:
                    import pandas as pd
                    existing_holdings = pd.read_excel(fund_file_path, sheet_name='Holdings')
                    if not existing_holdings.empty:
                        logger.info(f"✅ Found demo Holdings sheet ({len(existing_holdings)} records)")
                except:
                    pass
            
            if existing_transactions is None:
                try:
                    import pandas as pd
                    existing_transactions = pd.read_excel(fund_file_path, sheet_name='Transactions')
                    if not existing_transactions.empty:
                        logger.info(f"✅ Found demo Transactions sheet ({len(existing_transactions)} records)")
                except:
                    pass
            
            if existing_holdings is not None or existing_transactions is not None:
                logger.info("✅ Proceeding with existing processed data (no new data to update)")
                return True
            else:
                logger.error("❌ No raw paste data and no existing processed data available")
                return False
        
        # Process raw data if available
        processed_holdings = process_raw_holdings(raw_holdings)
        processed_transactions = process_raw_transactions(raw_transactions)
        
        logger.info(f"Processed {len(processed_holdings)} holdings and {len(processed_transactions)} transactions")
        
        # CRITICAL FIX: Write processed data back to Excel
        logger.info("Writing processed data to Excel...")
        persist_success = write_processed_fund_data(
            fund_file_path,
            processed_holdings,
            processed_transactions,
            logger
        )
        
        if not persist_success:
            logger.error("❌ Failed to persist processed fund data to Excel")
            return False
        
        # Verify the complete pipeline including persistence
        logger.info("Verifying fund data update success...")
        if test_global_markets_automation(logger):
            logger.info("✅ Global Markets data update completed successfully")
            return True
        else:
            logger.error(f"❌ Global Markets data update failed verification")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error during CN fund data update: {e}")
        return False


def run_data_validation(logger):
    """Run basic data validation checks."""
    logger.info("🔍 Step 2: Running Data Validation...")
    
    try:
        logger.info("Testing Global Markets automation...")
        cn_result = test_global_markets_automation(logger)
        
        logger.info("Testing Schwab automation...")
        schwab_result = test_schwab_automation(logger)
        
        schwab_data_result = validate_schwab_data(logger)
        
        overall_success = cn_result and schwab_result and schwab_data_result
        
        if overall_success:
            logger.info("✅ Data validation completed successfully")
        else:
            logger.warning("⚠️  Some validation checks failed - proceeding with caution")
        
        return overall_success
        
    except Exception as e:
        logger.error(f"❌ Error during data validation: {e}")
        return False


def generate_comprehensive_report_logic(logger, output_dir="output"):
    """Generate the comprehensive financial report."""
    logger.info("📈 Step 3: Generating Comprehensive Financial Report...")
    
    try:
        from src.report_generators.real_report import main as generate_real_report_main
        
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info("Processing portfolio data and generating report...")
        
        result = generate_real_report_main()
        
        if isinstance(result, dict):
            success = result.get('success', False)
            
            if success:
                # Handle new modular report format (multiple files)
                report_files = result.get('report_files', {})
                total_size = result.get('total_size_kb', 0)
                
                if report_files:
                    logger.info(f"✅ Generated {len(report_files)} modular reports ({total_size:.1f} KB total)")
                    for filename in report_files.keys():
                        logger.info(f"   - {filename}")
                    # Return path to landing page as primary report
                    landing_page = os.path.join(output_dir, 'index.html')
                    return True, landing_page, total_size
                
                # Fallback: check for legacy single report path
                report_path = result.get('report_path')
                if report_path and os.path.exists(report_path):
                    report_size = result.get('report_size_kb', 0)
                    logger.info(f"✅ Financial report generated successfully: {report_path} ({report_size:.1f} KB)")
                    return True, report_path, report_size
            
            # If we get here, something went wrong
            error = result.get('error', 'Unknown error')
            logger.error(f"❌ Report generation failed: {error}")
            return False, None, 0
        else:
            # Legacy format: no dict returned
            report_path = os.path.join(output_dir, "real_investment_report.html")
            if os.path.exists(report_path):
                file_size = os.path.getsize(report_path) / 1024
                logger.info(f"✅ Financial report generated successfully: {report_path} ({file_size:.1f} KB)")
                return True, report_path, file_size
            else:
                logger.error("❌ Report file not found after generation")
                return False, None, 0
            
    except Exception as e:
        logger.error(f"❌ Error during report generation: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False, None, 0


def print_summary(logger, fund_update_success, validation_success, report_success, report_path, report_size_kb, start_time):
    """Print a comprehensive summary of the analysis run."""
    end_time = datetime.now()
    duration = end_time - start_time
    
    # Print summary with clear visual separation
    print("\n" + "="*70)
    print("  COMPREHENSIVE FINANCIAL ANALYSIS SUMMARY")
    print("="*70)
    print(f"  📅 Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  ⏱️  Duration: {duration.total_seconds():.1f}s")
    print("")
    
    print("  📊 Component Status:")
    print(f"     Global Markets Data Update: {'✅ SUCCESS' if fund_update_success else '❌ FAILED'}")
    print(f"     Data Validation:        {'✅ SUCCESS' if validation_success else '⚠️  WARNING'}")
    print(f"     Report Generation:      {'✅ SUCCESS' if report_success else '❌ FAILED'}")
    print("")
    
    if report_success and report_path:
        print(f"  📈 Main Report: {report_path}")
        print(f"  📦 Total Size: {report_size_kb:.1f} KB")
        print("")
        print("  🌐 Open output/index.html in your browser to view the analysis")
    
    overall_success = fund_update_success and report_success
    print("  " + "-"*66)
    if overall_success:
        print("  🎉 OVERALL STATUS: ✅ SUCCESS")
        print("  Your comprehensive financial analysis is ready!")
    else:
        print("  ⚠️  OVERALL STATUS: ❌ ISSUES DETECTED")
        print("  Check logs/comprehensive_analysis.log for details")
    print("="*70 + "\n")


# =============================================================================
# CLI Commands
# =============================================================================

@click.group()
@click.version_option(version='1.0.0', prog_name='Personal Investment System')
def cli():
    """
    Personal Investment System - Unified Command Center
    
    A comprehensive financial analysis and portfolio optimization system.
    """
    pass


@cli.command(name='run-all')
@click.option('--skip-fund-update', is_flag=True, 
              help='Skip Global Markets data update (use existing data)')
@click.option('--skip-validation', is_flag=True,
              help='Skip data validation checks')
@click.option('--output-dir', default='output',
              help='Output directory for reports (default: output/)')
@click.option('--verbose', is_flag=True,
              help='Enable verbose logging')
def run_all(skip_fund_update, skip_validation, output_dir, verbose):
    """
    Run comprehensive financial analysis pipeline.
    
    This command automates the complete workflow:
    1. Updates Global Markets data from raw paste sheets
    2. Processes latest Schwab CSV files automatically
    3. Generates comprehensive financial report with real data
    
    This replaces the need to run multiple scripts manually.
    """
    # Setup logging
    os.makedirs('logs', exist_ok=True)
    logger = setup_logging(verbose)
    
    start_time = datetime.now()
    
    # Print initial banner to console (not to logger to avoid duplication)
    print("\n" + "="*70)
    print("  🚀 COMPREHENSIVE FINANCIAL ANALYSIS")
    print("="*70)
    print(f"  Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("  Progress will be logged to: logs/comprehensive_analysis.log")
    print("="*70 + "\n")
    
    logger.info("🚀 Starting Comprehensive Financial Analysis Pipeline")
    logger.info(f"📅 Analysis started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize results
    fund_update_success = True
    validation_success = True
    report_success = False
    report_path = None
    report_size_kb = 0.0
    
    try:
        # Step 1: CN Fund Data Update
        if not skip_fund_update:
            print("  [1/3] Updating Global Markets data...")
            fund_update_success = run_fund_data_update_logic(logger)
            print(f"        {'✅ Success' if fund_update_success else '❌ Failed'}")
        else:
            print("  [1/3] Skipping Global Markets data update")
            logger.info("⏭️  Skipping Global Markets data update (--skip-fund-update)")
            
        # Step 1b: Sync Assets & Balance Sheet to DB
        try:
            from src.data_manager.db_sync import (
                sync_assets_to_db, 
                sync_balance_sheet_to_db, 
                sync_full_holdings_snapshot,
                sync_monthly_data_to_db
            )
            
            print("  [1.5/3] Syncing assets & balance sheet to database...")
            sync_result = sync_assets_to_db()
            bs_sync_result = sync_balance_sheet_to_db()
            monthly_sync_result = sync_monthly_data_to_db()
            
            # CRITICAL: Populate Holding table with full snapshot (Funds, Stocks, RSU, BS)
            print("  [1.6/3] Snapshotting full portfolio to Holding table...")
            full_snapshot_result = sync_full_holdings_snapshot()
            
            status = "✅ Success" if (sync_result and bs_sync_result and monthly_sync_result and full_snapshot_result) else "⚠️  Partial Success"
            print(f"        {status}")
        except Exception as e:
            logger.error(f"Failed to sync to DB: {e}")
            print("        ❌ Failed (See logs)")
            
        # Step 1.7: Reconcile Transactions (Full DB Mode)
        try:
            from src.scripts.reconcile_transactions import reconcile_transactions
            print("  [1.7/3] Reconciling transactions with holdings...")
            # Run in Execute mode to fix gaps automatically
            reconcile_transactions(execute=True, verify_only=False)
            print("        ✅ Reconciliation complete")
        except Exception as e:
            logger.error(f"Reconciliation failed: {e}")
            print("        ❌ Reconciliation failed (See logs)")
            
        # Step 1c: Auto-Tag Asssets (Populate Metadata)
        try:
            from src.database import get_session
            from src.logic_layer.auto_tagger import AutoTagger
            
            print("  [1.6/3] Running Auto-Classification...")
            session = get_session()
            tagger = AutoTagger(session)
            count = tagger.process_all_assets()
            print(f"        ✅ Updated metadata for {count} assets")
            session.close()
        except Exception as e:
            logger.error(f"Auto-Tagging failed: {e}")
            print("        ⚠️  Auto-Tagging failed (See logs)")
        
        # Step 2: Data Validation
        if not skip_validation:
            print("  [2/3] Validating data integrity...")
            validation_success = run_data_validation(logger)
            print(f"        {'✅ Success' if validation_success else '⚠️  Warnings'}")
        else:
            print("  [2/3] Skipping data validation")
            logger.info("⏭️  Skipping data validation (--skip-validation)")
        
        # Step 3: Generate Report
        if fund_update_success or skip_fund_update:
            print("  [3/3] Generating financial reports...")
            report_success, report_path, report_size_kb = generate_comprehensive_report_logic(logger, output_dir)
            print(f"        {'✅ Success' if report_success else '❌ Failed'}")
        else:
            print("  [3/3] Skipping report generation (data update failed)")
            logger.error("❌ Skipping report generation due to critical data update failures")
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error during analysis: {e}")
        sys.exit(1)
    finally:
        print_summary(logger, fund_update_success, validation_success, report_success, 
                     report_path, report_size_kb, start_time)
    
    sys.exit(0 if (fund_update_success and report_success) else 1)


@cli.command(name='generate-report')
@click.option('--output-dir', default='output',
              help='Output directory for reports (default: output/)')
def generate_report(output_dir):
    """
    Generate HTML financial report from existing data.
    
    Creates a comprehensive HTML report using current portfolio data.
    Use this when you've already updated your data and just need a fresh report.
    """
    from src.report_generators.real_report import main as generate_real_report_main
    
    os.makedirs(output_dir, exist_ok=True)
    
    click.echo("📈 Generating comprehensive financial report...")
    
    try:
        result = generate_real_report_main()
        
        if isinstance(result, dict):
            success = result.get('success', False)
            
            if success:
                # Handle new modular report format
                report_files = result.get('report_files', {})
                total_size = result.get('total_size_kb', 0)
                
                if report_files:
                    click.echo(f"✅ Generated {len(report_files)} modular reports (Total: {total_size:.1f} KB):")
                    for filename in report_files.keys():
                        click.echo(f"   - {filename}")
                    click.echo(f"📂 Open output/index.html to view reports")
                    sys.exit(0)
                else:
                    # Fallback for legacy single report
                    report_path = result.get('report_path')
                    if report_path:
                        report_size = result.get('report_size_kb', 0)
                        click.echo(f"✅ Report generated successfully: {report_path} ({report_size:.1f} KB)")
                        sys.exit(0)
            
            error = result.get('error', 'Unknown error')
            click.echo(f"❌ Report generation failed: {error}", err=True)
            sys.exit(1)
        else:
            report_path = os.path.join(output_dir, "real_investment_report.html")
            if os.path.exists(report_path):
                file_size = os.path.getsize(report_path) / 1024
                click.echo(f"✅ Report generated: {report_path} ({file_size:.1f} KB)")
                sys.exit(0)
            else:
                click.echo("❌ Report file not found after generation", err=True)
                sys.exit(1)
                
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command(name='run-web')
@click.option('--port', default=5000, help='Port to run the web server on')
@click.option('--debug', is_flag=True, help='Run in debug mode')
def run_web(port, debug):
    """
    Launch the Web Management Interface.
    
    Starts the Flask application for managing transactions, assets, and viewing the dashboard.
    """
    try:
        from src.web_app import create_app
        
        click.echo(f"🚀 Starting Web Management Interface on port {port}...")
        click.echo(f"📊 Dashboard available at: http://127.0.0.1:{port}/dashboard/")
        
        app = create_app()
        app.run(host='127.0.0.1', port=port, debug=debug)
        
    except Exception as e:
        click.echo(f"❌ Failed to start web app: {e}", err=True)
        sys.exit(1)


@cli.command(name='update-global-data')
@click.option('--dry-run', is_flag=True,
              help='Show what would be updated without making changes')
def update_funds(dry_run):
    """
    Update Global Markets data from raw paste sheets.
    
    Processes raw fund data pasted into Excel sheets and updates historical data.
    This operation is idempotent and can be run multiple times safely.
    """
    import pandas as pd
    from typing import Optional, Tuple
    from src.data_manager.readers import read_raw_fund_sheets
    from src.data_manager.cleaners import process_raw_holdings, process_raw_transactions
    from src.database.base import get_session
    from src.database.models import MarketDataNAV
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    FUND_DATA_FILE = get_fund_file_path()
    
    # Helper function: load_existing_historical_data
    def load_existing_historical_data() -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """Load existing historical data from the Excel file."""
        try:
            if not os.path.exists(FUND_DATA_FILE):
                logger.error(f"Fund data file not found: {FUND_DATA_FILE}")
                return None, None
            
            historical_holdings = None
            try:
                historical_holdings = pd.read_excel(FUND_DATA_FILE, sheet_name='基金持仓汇总')
                logger.info(f"Loaded {len(historical_holdings)} existing holdings records")
            except Exception as e:
                logger.warning(f"Could not load existing holdings data: {e}")
            
            historical_transactions = None
            try:
                historical_transactions = pd.read_excel(FUND_DATA_FILE, sheet_name='基金交易记录')
                logger.info(f"Loaded {len(historical_transactions)} existing transaction records")
            except Exception as e:
                logger.warning(f"Could not load existing transactions data: {e}")
            
            return historical_holdings, historical_transactions
        except Exception as e:
            logger.error(f"Critical error loading historical data: {e}")
            return None, None
    
    # Helper function: identify_new_transactions
    def identify_new_transactions(processed_transactions: pd.DataFrame, 
                                historical_transactions: Optional[pd.DataFrame]) -> pd.DataFrame:
        """Identify new transactions that don't exist in historical data."""
        if historical_transactions is None or historical_transactions.empty:
            logger.info("No existing transaction history, all processed transactions are new")
            return processed_transactions
        
        try:
            processed_copy = processed_transactions.copy()
            historical_copy = historical_transactions.copy()
            
            if 'Transaction_Date' in processed_copy.columns:
                processed_copy['Transaction_Date'] = pd.to_datetime(processed_copy['Transaction_Date'])
            
            if 'Transaction_Date' in historical_copy.columns:
                historical_copy['Transaction_Date'] = pd.to_datetime(historical_copy['Transaction_Date'])
            elif '交易日期' in historical_copy.columns:
                historical_copy['Transaction_Date'] = pd.to_datetime(historical_copy['交易日期'])
            
            if 'Transaction_Date' in historical_copy.columns:
                valid_dates = historical_copy['Transaction_Date'].dropna()
                if not valid_dates.empty:
                    latest_historical_date = valid_dates.max()
                    logger.info(f"Latest historical transaction date: {latest_historical_date.strftime('%Y-%m-%d')}")
                    
                    new_transactions = processed_copy[
                        processed_copy['Transaction_Date'] > latest_historical_date
                    ]
                    
                    logger.info(f"Found {len(new_transactions)} new transactions to add")
                    return new_transactions
                else:
                    logger.warning("No valid dates in historical data, treating all as new")
                    return processed_copy
            else:
                logger.warning("Could not find Transaction_Date in historical data, treating all as new")
                return processed_copy
        except Exception as e:
            logger.error(f"Error identifying new transactions: {e}")
            return pd.DataFrame()
    
    # Helper function: update_excel_file
    def update_excel_file(updated_holdings: Optional[pd.DataFrame], 
                         updated_transactions: Optional[pd.DataFrame]) -> bool:
        """Update the Excel file with new holdings and transaction data."""
        try:
            with pd.ExcelWriter(FUND_DATA_FILE, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                
                if updated_holdings is not None and not updated_holdings.empty:
                    holdings_columns_map = {
                        'Asset_ID': '基金代码',
                        'Asset_Name': '基金名称', 
                        'Asset_Type_Raw': '基金类型',
                        'Snapshot_Date': '净值日期',
                        'Market_Price_Unit': '单位净值',
                        'Quantity': '持有份额',
                        'Market_Value_Raw': '参考市值'
                    }
                    
                    holdings_for_excel = updated_holdings.rename(columns=holdings_columns_map)
                    holdings_for_excel.to_excel(writer, sheet_name='基金持仓汇总', index=False)
                    logger.info(f"Updated 基金持仓汇总 sheet with {len(holdings_for_excel)} records")
                
                if updated_transactions is not None and not updated_transactions.empty:
                    transactions_columns_map = {
                        'Transaction_Date': '交易日期',
                        'Asset_ID': '基金代码',
                        'Asset_Name': '基金名称',
                        'Transaction_Type_Raw': '操作类型',
                        'Amount_Gross': '交易金额',
                        'Quantity': '交易份额', 
                        'Price_Unit': '交易时基金单位净值',
                        'Commission_Fee': '手续费'
                    }
                    
                    available_cols = {k: v for k, v in transactions_columns_map.items() if k in updated_transactions.columns}
                    transactions_for_excel = updated_transactions.rename(columns=available_cols)
                    
                    expected_excel_cols = ['交易日期', '基金代码', '基金名称', '操作类型', '交易金额', '交易份额', '交易时基金单位净值', '手续费', '交易原因']
                    for col in expected_excel_cols:
                        if col not in transactions_for_excel.columns:
                            if col == '交易原因':
                                transactions_for_excel[col] = '自动导入'
                            else:
                                transactions_for_excel[col] = None
                    
                    transactions_for_excel = transactions_for_excel[expected_excel_cols]
                    transactions_for_excel.to_excel(writer, sheet_name='基金交易记录', index=False)
                    logger.info(f"Updated 基金交易记录 sheet with {len(transactions_for_excel)} records")
            
            logger.info("Successfully updated Excel file")
            return True
        except Exception as e:
            logger.error(f"Error updating Excel file: {e}")
            return False

    # Helper function: update_database_nav
    def update_database_nav(holdings_df: pd.DataFrame) -> bool:
        """Update MarketDataNAV table with latest NAVs from holdings."""
        if holdings_df is None or holdings_df.empty:
            return False
            
        try:
            session = get_session()
            count = 0
            
            for _, row in holdings_df.iterrows():
                asset_id = row.get('Asset_ID')
                nav_date = row.get('Snapshot_Date')
                nav_price = row.get('Market_Price_Unit')
                
                if not asset_id or not nav_date or pd.isna(nav_price):
                    continue
                    
                # Convert date if needed
                if isinstance(nav_date, str):
                    nav_date = datetime.strptime(nav_date, '%Y-%m-%d').date()
                elif isinstance(nav_date, datetime):
                    nav_date = nav_date.date()
                    
                # Check if record exists
                existing = session.query(MarketDataNAV).filter(
                    MarketDataNAV.asset_id == asset_id,
                    MarketDataNAV.date == nav_date
                ).first()
                
                if existing:
                    existing.nav = float(nav_price)
                    existing.source = 'fund_sheet_update'
                    # MarketDataNAV has no updated_at column
                else:
                    new_nav = MarketDataNAV(
                        asset_id=asset_id,
                        date=nav_date,
                        nav=float(nav_price),
                        source='fund_sheet_update',
                        created_at=datetime.now()
                    )
                    session.add(new_nav)
                count += 1
                
            session.commit()
            logger.info(f"✅ Updated MarketDataNAV with {count} records")
            return True
            
        except Exception as e:
            logger.error(f"Error updating database NAVs: {e}")
            session.rollback()
            return False
    
    # Main logic
    if dry_run:
        click.echo("🔍 Running in DRY RUN mode - no changes will be made")
    
    logger.info("=== Starting Fund Data Update Process ===")
    click.echo("🏦 Starting Global Markets data update...")
    
    try:
        if not os.path.exists(FUND_DATA_FILE):
            click.echo(f"❌ Fund data file not found: {FUND_DATA_FILE}", err=True)
            sys.exit(1)
        
        # Step 1: Read raw data
        logger.info("Step 1: Reading raw data from paste sheets...")
        click.echo("Reading raw fund data...")
        raw_holdings, raw_transactions = read_raw_fund_sheets(FUND_DATA_FILE)
        
        if raw_holdings is None and raw_transactions is None:
            logger.warning("No raw data found in paste sheets. Nothing to process.")
            click.echo("⚠️ No raw data found in paste sheets")
            sys.exit(0)
        
        # Step 2: Process the raw data
        logger.info("Step 2: Processing raw data...")
        click.echo("Processing fund data...")
        
        processed_holdings = None
        if raw_holdings is not None:
            logger.info("Processing raw holdings data...")
            processed_holdings = process_raw_holdings(raw_holdings)
            if processed_holdings is not None:
                logger.info(f"Successfully processed {len(processed_holdings)} holdings records")
                
                # Update Database NAVs
                if not dry_run:
                    click.echo("Updating database NAVs...")
                    update_database_nav(processed_holdings)
        
        processed_transactions = None
        if raw_transactions is not None:
            logger.info("Processing raw transactions data...")
            processed_transactions = process_raw_transactions(raw_transactions)
            if processed_transactions is not None:
                logger.info(f"Successfully processed {len(processed_transactions)} transaction records")
        
        # Step 3: Load existing historical data
        logger.info("Step 3: Loading existing historical data...")
        historical_holdings, historical_transactions = load_existing_historical_data()
        
        # Step 4: Identify new transactions and prepare updates
        logger.info("Step 4: Identifying new data and preparing updates...")
        
        updated_holdings = processed_holdings
        updated_transactions = historical_transactions
        
        if processed_transactions is not None:
            new_transactions = identify_new_transactions(processed_transactions, historical_transactions)
            
            if not new_transactions.empty:
                if historical_transactions is not None and not historical_transactions.empty:
                    historical_copy = historical_transactions.copy()
                    
                    if '交易日期' in historical_copy.columns:
                        column_mapping = {
                            '交易日期': 'Transaction_Date',
                            '基金代码': 'Asset_ID',
                            '基金名称': 'Asset_Name',
                            '操作类型': 'Transaction_Type_Raw',
                            '交易金额': 'Amount_Gross',
                            '交易份额': 'Quantity',
                            '交易时基金单位净值': 'Price_Unit',
                            '手续费': 'Commission_Fee',
                            '交易原因': 'Transaction_Reason'
                        }
                        rename_map = {k: v for k, v in column_mapping.items() if k in historical_copy.columns}
                        historical_copy = historical_copy.rename(columns=rename_map)
                    
                    if 'Transaction_Date' in historical_copy.columns:
                        historical_copy['Transaction_Date'] = pd.to_datetime(historical_copy['Transaction_Date'])
                    if 'Transaction_Date' in new_transactions.columns:
                        new_transactions['Transaction_Date'] = pd.to_datetime(new_transactions['Transaction_Date'])
                    
                    updated_transactions = pd.concat([historical_copy, new_transactions], ignore_index=True)
                    updated_transactions = updated_transactions.sort_values(by='Transaction_Date').reset_index(drop=True)
                    logger.info(f"Combined {len(historical_copy)} historical + {len(new_transactions)} new = {len(updated_transactions)} total transactions")
                else:
                    updated_transactions = new_transactions
                    logger.info(f"No historical transactions, using {len(new_transactions)} new transactions")
            else:
                logger.info("No new transactions to add")
        
        # Step 5: Update the Excel file
        logger.info("Step 5: Updating Excel file...")
        
        if dry_run:
            logger.info("🔍 DRY RUN: Skipping file write")
            if updated_holdings is not None:
                click.echo(f"🔍 Would update holdings: {len(updated_holdings)} records")
            if updated_transactions is not None:
                click.echo(f"🔍 Would update transactions: {len(updated_transactions)} records")
            success = True
        else:
            success = update_excel_file(updated_holdings, updated_transactions)
        
        if success:
            logger.info("=== Fund Data Update Process Completed Successfully ===")
            click.echo("✅ Fund data update completed")
            if processed_holdings is not None:
                click.echo(f"✅ Holdings updated: {len(processed_holdings)} records")
            if processed_transactions is not None:
                new_count = len(identify_new_transactions(processed_transactions, historical_transactions))
                click.echo(f"✅ New transactions added: {new_count} records")
            sys.exit(0)
        else:
            logger.error("=== Fund Data Update Process Failed ===")
            click.echo("❌ Fund data update failed", err=True)
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Critical error in main process: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command(name='create-snapshots')
@click.option('--frequency', type=click.Choice(['weekly', 'monthly', 'biweekly']), 
              default='weekly',
              help='Frequency of snapshot creation')
@click.option('--start-date', type=str, default=None,
              help='Start date for snapshot range (YYYY-MM-DD)')
@click.option('--end-date', type=str, default=None,
              help='End date for snapshot range (YYYY-MM-DD), defaults to today')
@click.option('--dry-run', is_flag=True,
              help='Show what would be created without making changes')
def create_snapshots(frequency, start_date, end_date, dry_run):
    """
    Create historical snapshots for portfolio analysis.
    
    Generates snapshots of portfolio data at regular intervals (weekly/monthly).
    Snapshots are stored in data/historical_snapshots/ directory.
    """
    import pandas as pd
    from datetime import datetime, timedelta
    from typing import List, Dict, Any, Optional
    from src.data_manager.manager import DataManager
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('data/snapshot_automation.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    
    class SnapshotAutomator:
        """
        Automated system for creating historical portfolio snapshots at regular intervals.
        """
        
        def __init__(self, frequency: str = 'weekly', config_path: str = 'config/settings.yaml'):
            """
            Initialize the snapshot automation system.
            
            Args:
                frequency: 'weekly', 'biweekly', or 'monthly'
                config_path: Path to the configuration file
            """
            self.frequency = frequency
            self.config_path = config_path
            self.data_manager = None
            self.logger = logging.getLogger(__name__)
            
            # Statistics tracking
            self.stats = {
                'total_snapshots_created': 0,
                'total_snapshots_failed': 0,
                'snapshots_validated': 0,
                'validation_failures': 0,
                'start_time': None,
                'end_time': None
            }
            
        def _load_current_data(self) -> None:
            """Initialize DataManager and load current data."""
            try:
                self.logger.info(f"Initializing DataManager with config: {self.config_path}")
                self.data_manager = DataManager(config_path=self.config_path)
                
                # Load balance sheet and holdings to ensure data is available
                balance_sheet = self.data_manager.get_balance_sheet()
                holdings = self.data_manager.get_current_holdings()
                
                self.logger.info(f"Loaded balance sheet with {len(balance_sheet)} rows")
                self.logger.info(f"Loaded holdings with {len(holdings)} assets")
                
            except Exception as e:
                self.logger.error(f"Error loading current data: {e}")
                raise
                
        def get_last_snapshot_date(self) -> Optional[datetime]:
            """
            Find the most recent snapshot date from existing files.
            
            Returns:
                datetime object of the most recent snapshot, or None if no snapshots exist
            """
            snapshot_dir = 'data/historical_snapshots'
            
            if not os.path.exists(snapshot_dir):
                self.logger.info("No snapshot directory found")
                return None
                
            snapshot_files = [f for f in os.listdir(snapshot_dir) 
                            if f.startswith('snapshot_') and f.endswith('.csv')]
            
            if not snapshot_files:
                self.logger.info("No existing snapshots found")
                return None
                
            # Extract dates from filenames (format: snapshot_YYYYMMDD.csv)
            dates = []
            for filename in snapshot_files:
                try:
                    date_str = filename.replace('snapshot_', '').replace('.csv', '')
                    date_obj = datetime.strptime(date_str, '%Y%m%d')
                    dates.append(date_obj)
                except ValueError:
                    self.logger.warning(f"Could not parse date from filename: {filename}")
                    continue
                    
            if dates:
                last_date = max(dates)
                self.logger.info(f"Most recent snapshot date: {last_date.strftime('%Y-%m-%d')}")
                return last_date
                
            return None
            
        def determine_snapshot_dates(self, start_date: Optional[str] = None, 
                                     end_date: Optional[str] = None) -> List[datetime]:
            """
            Determine which snapshot dates to create based on frequency and existing snapshots.
            
            Args:
                start_date: Optional start date (YYYY-MM-DD)
                end_date: Optional end date (YYYY-MM-DD), defaults to today
                
            Returns:
                List of datetime objects representing snapshot dates to create
            """
            # Parse end date or use today
            if end_date:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            else:
                end_dt = datetime.now()
                
            # Determine start date
            if start_date:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                last_snapshot = self.get_last_snapshot_date()
                if last_snapshot:
                    # Start from the day after the last snapshot
                    start_dt = last_snapshot + timedelta(days=1)
                else:
                    # Default to 1 year ago if no snapshots exist
                    start_dt = end_dt - timedelta(days=365)
                    
            self.logger.info(f"Date range: {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}")
            
            # Generate snapshot dates based on frequency
            snapshot_dates = []
            current_date = start_dt
            
            if self.frequency == 'weekly':
                interval = timedelta(weeks=1)
            elif self.frequency == 'biweekly':
                interval = timedelta(weeks=2)
            elif self.frequency == 'monthly':
                # For monthly, we'll use 30 days as approximation
                interval = timedelta(days=30)
            else:
                raise ValueError(f"Invalid frequency: {self.frequency}")
                
            while current_date <= end_dt:
                snapshot_dates.append(current_date)
                current_date += interval
                
            self.logger.info(f"Generated {len(snapshot_dates)} snapshot dates with {self.frequency} frequency")
            return snapshot_dates
            
        def create_snapshot(self, snapshot_date: datetime) -> bool:
            """
            Create a single snapshot file for the specified date.
            
            Args:
                snapshot_date: Date for the snapshot
                
            Returns:
                True if snapshot was created successfully, False otherwise
            """
            try:
                # Format the date for filename
                date_str = snapshot_date.strftime('%Y%m%d')
                snapshot_filename = f"snapshot_{date_str}.csv"
                snapshot_path = os.path.join('data/historical_snapshots', snapshot_filename)
                
                # Check if snapshot already exists
                if os.path.exists(snapshot_path):
                    self.logger.info(f"Snapshot already exists: {snapshot_filename}")
                    return True
                    
                # Get current portfolio data
                balance_sheet = self.data_manager.get_balance_sheet()
                
                # Create snapshot dataframe
                snapshot_data = balance_sheet.copy()
                snapshot_data['Snapshot_Date'] = snapshot_date.strftime('%Y-%m-%d')
                
                # Ensure directory exists
                os.makedirs('data/historical_snapshots', exist_ok=True)
                
                # Save snapshot
                snapshot_data.to_csv(snapshot_path, index=False)
                
                self.logger.info(f"✓ Created snapshot: {snapshot_filename} ({len(snapshot_data)} rows)")
                self.stats['total_snapshots_created'] += 1
                return True
                
            except Exception as e:
                self.logger.error(f"✗ Failed to create snapshot for {snapshot_date.strftime('%Y-%m-%d')}: {e}")
                self.stats['total_snapshots_failed'] += 1
                return False
                
        def validate_snapshot(self, snapshot_date: datetime) -> bool:
            """
            Validate that a snapshot was created correctly.
            
            Args:
                snapshot_date: Date of the snapshot to validate
                
            Returns:
                True if snapshot is valid, False otherwise
            """
            try:
                date_str = snapshot_date.strftime('%Y%m%d')
                snapshot_path = os.path.join('data/historical_snapshots', f"snapshot_{date_str}.csv")
                
                if not os.path.exists(snapshot_path):
                    self.logger.error(f"Snapshot file not found: {snapshot_path}")
                    self.stats['validation_failures'] += 1
                    return False
                    
                # Read and validate snapshot
                snapshot_data = pd.read_csv(snapshot_path)
                
                # Basic validation checks
                if len(snapshot_data) == 0:
                    self.logger.error(f"Snapshot is empty: {snapshot_path}")
                    self.stats['validation_failures'] += 1
                    return False
                    
                required_columns = ['Asset_ID', 'Asset_Name', 'Market_Value']
                missing_columns = [col for col in required_columns if col not in snapshot_data.columns]
                
                if missing_columns:
                    self.logger.error(f"Snapshot missing required columns {missing_columns}: {snapshot_path}")
                    self.stats['validation_failures'] += 1
                    return False
                    
                self.logger.info(f"✓ Validated snapshot: {date_str}")
                self.stats['snapshots_validated'] += 1
                return True
                
            except Exception as e:
                self.logger.error(f"Error validating snapshot for {snapshot_date.strftime('%Y-%m-%d')}: {e}")
                self.stats['validation_failures'] += 1
                return False
                
        def run_automation(self, start_date: Optional[str] = None, 
                          end_date: Optional[str] = None,
                          dry_run: bool = False) -> Dict[str, Any]:
            """
            Run the full snapshot automation workflow.
            
            Args:
                start_date: Optional start date (YYYY-MM-DD)
                end_date: Optional end date (YYYY-MM-DD)
                dry_run: If True, only simulate without creating files
                
            Returns:
                Dictionary with statistics and results
            """
            self.stats['start_time'] = datetime.now()
            
            self.logger.info("=" * 80)
            self.logger.info("SNAPSHOT AUTOMATION STARTED")
            self.logger.info(f"Frequency: {self.frequency}")
            self.logger.info(f"Dry run: {dry_run}")
            self.logger.info("=" * 80)
            
            try:
                # Load current data
                self._load_current_data()
                
                # Determine which snapshots to create
                snapshot_dates = self.determine_snapshot_dates(start_date, end_date)
                
                if not snapshot_dates:
                    self.logger.info("No snapshots to create")
                    return self._get_final_summary()
                    
                self.logger.info(f"Will create {len(snapshot_dates)} snapshots")
                
                # Create snapshots
                for snapshot_date in snapshot_dates:
                    if dry_run:
                        self.logger.info(f"[DRY RUN] Would create snapshot for {snapshot_date.strftime('%Y-%m-%d')}")
                        self.stats['total_snapshots_created'] += 1
                    else:
                        success = self.create_snapshot(snapshot_date)
                        if success:
                            # Validate the snapshot
                            self.validate_snapshot(snapshot_date)
                            
                return self._get_final_summary()
                
            except Exception as e:
                self.logger.error(f"Fatal error in automation: {e}")
                return self._get_final_summary()
                
        def _get_final_summary(self) -> Dict[str, Any]:
            """Generate final summary statistics."""
            self.stats['end_time'] = datetime.now()
            
            if self.stats['start_time']:
                duration = self.stats['end_time'] - self.stats['start_time']
                self.stats['duration_seconds'] = duration.total_seconds()
                
            self.logger.info("=" * 80)
            self.logger.info("SNAPSHOT AUTOMATION COMPLETED")
            self.logger.info(f"Snapshots created: {self.stats['total_snapshots_created']}")
            self.logger.info(f"Snapshots failed: {self.stats['total_snapshots_failed']}")
            self.logger.info(f"Snapshots validated: {self.stats['snapshots_validated']}")
            self.logger.info(f"Validation failures: {self.stats['validation_failures']}")
            if 'duration_seconds' in self.stats:
                self.logger.info(f"Duration: {self.stats['duration_seconds']:.2f} seconds")
            self.logger.info("=" * 80)
            
            return self.stats.copy()
    
    # Main logic
    if dry_run:
        click.echo("🔍 Running in DRY RUN mode - no changes will be made")
    
    click.echo(f"📸 Starting snapshot creation ({frequency} frequency)...")
    
    try:
        # Initialize automator
        automator = SnapshotAutomator(frequency=frequency, config_path='config/settings.yaml')
        
        # Run automation
        results = automator.run_automation(
            start_date=start_date,
            end_date=end_date,
            dry_run=dry_run
        )
        
        # Print summary
        click.echo("\n" + "="*60)
        click.echo("📊 SNAPSHOT CREATION SUMMARY")
        click.echo("="*60)
        click.echo(f"✅ Snapshots created: {results['total_snapshots_created']}")
        click.echo(f"❌ Snapshots failed: {results['total_snapshots_failed']}")
        click.echo(f"✓ Snapshots validated: {results['snapshots_validated']}")
        click.echo(f"✗ Validation failures: {results['validation_failures']}")
        if 'duration_seconds' in results:
            click.echo(f"⏱️ Duration: {results['duration_seconds']:.2f} seconds")
        click.echo("="*60)
        
        if results['total_snapshots_failed'] > 0 or results['validation_failures'] > 0:
            click.echo("\n⚠️ Some snapshots failed or had validation issues", err=True)
            sys.exit(1)
        else:
            click.echo("\n✅ All snapshots created and validated successfully")
            sys.exit(0)
            
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command(name='validate-data')
@click.option('--output-dir', default='output',
              help='Output directory for validation report (default: output/)')
@click.option('--verbose', is_flag=True,
              help='Enable verbose logging')
def validate_data(output_dir, verbose):
    """
    Run data quality validation checks.
    
    Executes comprehensive data validation checks (Project Cornerstone):
    - Classification/Mapping Integrity
    - Structural Schema Integrity
    - Referential Consistency
    - Transaction Sign Coherence
    - Portfolio Reconciliation
    
    Generates a detailed validation report in Markdown format.
    Exit code 1 if CRITICAL issues found, 0 otherwise.
    """
    # Setup logging
    os.makedirs('logs', exist_ok=True)
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/validation.log', mode='a')
        ]
    )
    
    click.echo("🔍 Starting Data Quality Validation")
    click.echo("="*60)
    
    try:
        # Import validation engine
        from src.validation.engine import ValidationEngine
        
        # Initialize engine
        engine = ValidationEngine(config_path='config/settings.yaml')
        
        # Run all checks
        total_issues = engine.run_all_checks()
        
        # Generate report
        report_path = engine.generate_report(output_dir=output_dir)
        
        # Print summary
        click.echo("\n" + "="*60)
        click.echo("📊 VALIDATION SUMMARY")
        click.echo("="*60)
        
        if total_issues == 0:
            click.echo("✅ No issues found (Core 5 clean)")
            click.echo(f"📄 Report: {report_path}")
            sys.exit(0)
        else:
            # Count by severity
            severity_counts = {
                'CRITICAL': sum(1 for i in engine.issues if i.severity == 'CRITICAL'),
                'MAJOR': sum(1 for i in engine.issues if i.severity == 'MAJOR'),
                'WARNING': sum(1 for i in engine.issues if i.severity == 'WARNING'),
                'INFO': sum(1 for i in engine.issues if i.severity == 'INFO')
            }
            
            click.echo(f"Total Issues: {total_issues}")
            for severity, count in severity_counts.items():
                if count > 0:
                    icon = '🔴' if severity == 'CRITICAL' else '🟡' if severity == 'MAJOR' else '⚠️' if severity == 'WARNING' else 'ℹ️'
                    click.echo(f"  {icon} {severity}: {count}")
            
            click.echo(f"\n📄 Detailed report: {report_path}")
            click.echo("="*60)
            
            # Exit with code 1 if CRITICAL issues found
            if engine.has_critical_issues():
                click.echo("\n❌ CRITICAL issues detected - please review and fix", err=True)
                sys.exit(1)
            else:
                click.echo("\n⚠️ Issues found but none are CRITICAL")
                sys.exit(0)
                
    except Exception as e:
        click.echo(f"❌ Validation failed: {e}", err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


@cli.command(name='generate-context')
@click.option('--output-dir', default='output',
              help='Output directory for markdown context file (default: output/)')
@click.option('--verbose', is_flag=True,
              help='Enable verbose logging')
def generate_context(output_dir, verbose):
    """
    Generate markdown context file for LLM analysis.
    
    Creates a comprehensive markdown document with portfolio state, performance,
    market environment, and holdings data optimized for LLM consumption.
    This file can be pasted into Claude/GPT-4 for intelligent portfolio analysis.
    """
    # Setup logging
    os.makedirs('logs', exist_ok=True)
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/markdown_generation.log', mode='a')
        ]
    )
    
    click.echo("📄 Generating Markdown Context for LLM Analysis")
    click.echo("="*60)
    
    try:
        from src.report_generators.real_report import generate_reports_for_markdown_only
        from src.report_generators.markdown_context_generator import MarkdownContextGenerator
        
        # Generate the underlying data needed for markdown
        click.echo("📊 Collecting portfolio data...")
        real_data, consolidated_actions = generate_reports_for_markdown_only()
        
        # Generate markdown
        click.echo("✍️  Generating markdown context...")
        md_generator = MarkdownContextGenerator()
        md_content = md_generator.generate_markdown(real_data, consolidated_actions)
        
        # Save to file
        os.makedirs(output_dir, exist_ok=True)
        markdown_path = os.path.join(output_dir, 'Personal_Investment_Analysis_Context.md')
        md_generator.save_to_file(md_content, markdown_path)
        
        # Get file size
        file_size = os.path.getsize(markdown_path) / 1024
        
        click.echo("\n" + "="*60)
        click.echo("✅ Markdown Context Generated Successfully")
        click.echo("="*60)
        click.echo(f"📄 File: {markdown_path}")
        click.echo(f"📊 Size: {file_size:.1f} KB")
        click.echo(f"🤖 Ready for LLM analysis (Claude, GPT-4, etc.)")
        click.echo("\nNext steps:")
        click.echo("1. Open the markdown file")
        click.echo("2. Copy the entire content")
        click.echo("3. Paste into your preferred LLM")
        click.echo("4. Ask for portfolio analysis and recommendations")
        
        sys.exit(0)
        
    except Exception as e:
        click.echo(f"❌ Markdown generation failed: {e}", err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


@cli.command(name='validate-comprehensive')
@click.option('--output-dir', default='output/validation',
              help='Output directory for validation reports (default: output/validation/)')
@click.option('--source-only', is_flag=True,
              help='Validate source data accuracy only')
@click.option('--calculations-only', is_flag=True,
              help='Validate financial calculations only')
@click.option('--consistency-only', is_flag=True,
              help='Validate cross-output consistency only')
@click.option('--generate-report', is_flag=True,
              help='Generate detailed human-readable validation report')
@click.option('--include-base-checks', is_flag=True, default=True,
              help='Include base validation engine checks (enabled by default)')
@click.option('--verbose', is_flag=True,
              help='Enable verbose logging')
def validate_comprehensive(output_dir, source_only, calculations_only, consistency_only, 
                          generate_report, include_base_checks, verbose):
    """
    Run comprehensive data validation for 100% accuracy verification.
    
    Validates:
    - Source data accuracy against Excel files
    - Financial calculations (XIRR, profit/loss, returns, Sharpe ratios)
    - Currency conversions and asset classifications
    - Cross-output consistency between HTML and markdown reports
    
    Examples:
        python main.py validate-comprehensive                    # Full validation
        python main.py validate-comprehensive --source-only      # Source data only
        python main.py validate-comprehensive --generate-report  # With detailed report
        python main.py validate-comprehensive --verbose          # With debug logging
    """
    # Setup logging
    os.makedirs('logs', exist_ok=True)
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/comprehensive_validation.log', mode='a')
        ]
    )
    
    click.echo("🔍 COMPREHENSIVE DATA VALIDATION")
    click.echo("="*80)
    
    try:
        # Import comprehensive validation components
        from src.validation.comprehensive_validator import ComprehensiveValidator
        from src.validation.validation_report_generator import ValidationReportGenerator
        
        # Initialize validator
        validator = ComprehensiveValidator(config_path='config/settings.yaml')
        
        # Determine validation scope
        if source_only:
            click.echo("📊 Running source data validation only...")
            results = {'validation_results': {'Source Data Validation': validator.validate_source_data_accuracy()}}
            # Add minimal metadata
            results['metadata'] = {
                'validation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'duration_seconds': 0,
                'validator_version': '1.0',
                'config_path': validator.config_path
            }
            results['summary'] = {'overall_status': 'PARTIAL', 'total_issues': 0, 'sections_completed': 1}
            results['issues'] = []
        elif calculations_only:
            click.echo("🧮 Running financial calculations validation only...")
            results = {'validation_results': {'Calculation Validation': validator.validate_calculation_accuracy()}}
            # Add minimal metadata
            results['metadata'] = {
                'validation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'duration_seconds': 0,
                'validator_version': '1.0',
                'config_path': validator.config_path
            }
            results['summary'] = {'overall_status': 'PARTIAL', 'total_issues': 0, 'sections_completed': 1}
            results['issues'] = []
        elif consistency_only:
            click.echo("🔄 Running cross-output consistency validation only...")
            results = {'validation_results': {'Consistency Validation': validator.validate_cross_output_consistency()}}
            # Add minimal metadata
            results['metadata'] = {
                'validation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'duration_seconds': 0,
                'validator_version': '1.0',
                'config_path': validator.config_path
            }
            results['summary'] = {'overall_status': 'PARTIAL', 'total_issues': 0, 'sections_completed': 1}
            results['issues'] = []
        else:
            click.echo("🎯 Running full comprehensive validation pipeline...")
            results = validator.validate_full_pipeline(include_base_checks=include_base_checks)
        
        # Generate report if requested
        if generate_report:
            click.echo(f"\n📄 Generating detailed validation report...")
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate comprehensive report
            report_generator = ValidationReportGenerator()
            report_path = os.path.join(output_dir, f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            report_content = report_generator.generate_comprehensive_report(results, report_path)
            
            click.echo(f"✅ Detailed report saved to: {report_path}")
        
        # Display quick summary
        click.echo("\n" + "="*80)
        click.echo("📊 VALIDATION SUMMARY")
        click.echo("="*80)
        
        summary = results.get('summary', {})
        overall_status = summary.get('overall_status', 'UNKNOWN')
        total_issues = summary.get('total_issues', 0)
        issue_breakdown = summary.get('issue_breakdown', {})
        
        # Status symbol mapping
        status_symbols = {
            'PASS': '✅',
            'WARNING': '⚠️',
            'FAIL': '❌',
            'ERROR': '🚫',
            'PASS_WITH_ISSUES': '⚡',
            'PARTIAL': 'ℹ️',
            'UNKNOWN': '❓'
        }
        
        status_symbol = status_symbols.get(overall_status, '❓')
        click.echo(f"Overall Status: {status_symbol} {overall_status}")
        click.echo(f"Total Issues: {total_issues}")
        
        if total_issues > 0:
            click.echo("\nIssue Breakdown:")
            severity_symbols = {
                'CRITICAL': '🔴',
                'HIGH': '🟠',
                'MEDIUM': '🟡',
                'LOW': '🟢',
                'WARNING': '⚠️'
            }
            
            for severity, count in issue_breakdown.items():
                if count > 0:
                    symbol = severity_symbols.get(severity, '•')
                    click.echo(f"  {symbol} {severity}: {count}")
        
        # Display execution time
        duration = results.get('metadata', {}).get('duration_seconds', 0)
        click.echo(f"\nExecution Time: {duration:.2f} seconds")
        
        # Determine exit code
        critical_issues = issue_breakdown.get('CRITICAL', 0)
        high_issues = issue_breakdown.get('HIGH', 0)
        
        if critical_issues > 0:
            click.echo(f"\n❌ CRITICAL issues detected - immediate attention required!", err=True)
            if not generate_report:
                click.echo("💡 Run with --generate-report for detailed investigation guidance", err=True)
            sys.exit(1)
        elif overall_status == 'FAIL':
            click.echo(f"\n❌ Validation failed - review issues and retry", err=True)
            sys.exit(1)
        elif high_issues > 0:
            click.echo(f"\n⚠️  High-priority issues found - recommend reviewing soon")
            sys.exit(0)
        else:
            click.echo(f"\n✅ Validation completed successfully")
            sys.exit(0)
            
    except Exception as e:
        click.echo(f"❌ Comprehensive validation failed: {e}", err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


@cli.command(name='update-taxonomy')
@click.option('--log-file', type=click.Path(exists=True),
              help='Path to log file containing unmapped assets')
@click.option('--yaml-file', 
              default='config/asset_taxonomy.yaml',
              help='Path to asset_taxonomy.yaml file')
@click.option('--auto-confirm', is_flag=True,
              help='Automatically confirm updates without prompting')
def update_taxonomy(log_file, yaml_file, auto_confirm):
    """
    Update asset_taxonomy.yaml with unmapped assets.
    
    Analyzes unmapped assets from validation logs and suggests appropriate
    classifications based on asset name patterns. Creates a backup before
    updating the taxonomy file.
    
    Examples:
        python main.py update-taxonomy --log-file logs/validation.log
        python main.py update-taxonomy  # Manual input mode
    """
    import yaml
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    click.echo("🔧 Asset Taxonomy Auto-Updater")
    click.echo("="*60)
    
    try:
        # Import the auto-update functions
        from src.portfolio_lib.utils.auto_update_taxonomy import (
            load_yaml_taxonomy,
            save_yaml_taxonomy,
            read_log_file,
            extract_unmapped_assets_from_log,
            update_taxonomy_with_new_assets
        )
        
        # Load taxonomy
        click.echo(f"Loading taxonomy from: {yaml_file}")
        taxonomy = load_yaml_taxonomy(yaml_file)
        if not taxonomy:
            click.echo(f"❌ Could not load taxonomy from {yaml_file}", err=True)
            sys.exit(1)
        
        # Get log content
        if log_file:
            click.echo(f"Reading log file: {log_file}")
            log_content = read_log_file(log_file)
        else:
            click.echo("\n📋 Manual Input Mode")
            click.echo("Paste the debug output containing unmapped assets")
            click.echo("Press Ctrl+D (Unix) or Ctrl+Z (Windows) when finished:\n")
            lines = []
            try:
                while True:
                    line = input()
                    lines.append(line)
            except EOFError:
                pass
            log_content = "\n".join(lines)
        
        # Extract unmapped assets
        click.echo("\n🔍 Analyzing unmapped assets...")
        unmapped_assets = extract_unmapped_assets_from_log(log_content)
        
        if not unmapped_assets:
            click.echo("✅ No unmapped assets found in the log content")
            sys.exit(0)
        
        click.echo(f"Found {len(unmapped_assets)} unmapped assets:\n")
        for asset_name, asset_type, value in unmapped_assets[:10]:
            click.echo(f"  • {asset_name} ({asset_type}) - Value: {value}")
        if len(unmapped_assets) > 10:
            click.echo(f"  ... and {len(unmapped_assets) - 10} more")
        
        # Update taxonomy
        click.echo("\n🤖 Generating classification suggestions...")
        updated_taxonomy = update_taxonomy_with_new_assets(taxonomy, unmapped_assets)
        
        # Confirm before saving
        if not auto_confirm:
            click.echo("\n" + "="*60)
            save_confirm = click.confirm("Save updates to taxonomy file?", default=True)
            if not save_confirm:
                click.echo("❌ Update canceled")
                sys.exit(0)
        
        # Save with backup
        click.echo("\n💾 Saving updates...")
        if save_yaml_taxonomy(updated_taxonomy, yaml_file):
            click.echo(f"✅ Taxonomy file updated successfully: {yaml_file}")
            click.echo(f"💾 Backup saved as: {yaml_file}.bak")
            click.echo("\n📝 Next steps:")
            click.echo("   1. Review the updated taxonomy file")
            click.echo("   2. Run 'python main.py validate-data' to verify")
            click.echo("   3. Run 'python main.py generate-report' to regenerate report")
            sys.exit(0)
        else:
            click.echo("❌ Failed to update taxonomy file", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        import traceback
        click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


@cli.command(name='init-database')
@click.option('--drop-existing', is_flag=True,
              help='⚠️  DANGER: Drop all existing tables before creating (data loss!)')
@click.option('--database-url', default=None,
              help='Custom database URL (default: sqlite:///data/investment_system.db)')
@click.option('--verbose', is_flag=True,
              help='Show SQL statements (useful for debugging)')
def init_database(drop_existing, database_url, verbose):
    """
    Initialize the database by creating all tables.
    
    This command sets up the SQLite database with all required tables
    for the Personal Investment System. Run this once before migrating data.
    
    Examples:
        python main.py init-database
        python main.py init-database --verbose
        python main.py init-database --drop-existing  # ⚠️ Drops all data!
    """
    try:
        click.echo("="*70)
        click.echo("📊 DATABASE INITIALIZATION")
        click.echo("="*70 + "\n")
        
        # Import database modules
        try:
            from src.database.base import init_database as db_init, get_engine
            from sqlalchemy import inspect
        except ImportError as e:
            click.echo(f"❌ Failed to import database modules: {e}", err=True)
            click.echo("\n💡 Hint: Install dependencies: pip install sqlalchemy alembic", err=True)
            sys.exit(1)
        
        # Confirm if dropping existing tables
        if drop_existing:
            click.echo("⚠️  WARNING: --drop-existing flag detected!")
            click.echo("This will DELETE ALL EXISTING DATA in the database.\n")
            if not click.confirm("Are you absolutely sure you want to drop all tables?", default=False):
                click.echo("❌ Operation canceled")
                sys.exit(0)
        
        # Set up logging
        if verbose:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO, format='%(message)s')
        
        # Initialize database
        click.echo(f"📁 Database location: {database_url or 'data/investment_system.db'}")
        click.echo(f"🔨 Creating tables...\n")
        
        db_init(database_url=database_url, drop_existing=drop_existing)
        
        # Verify tables were created
        engine = get_engine(database_url)
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        
        click.echo(f"\n✅ Database initialized successfully!")
        click.echo(f"📊 Created {len(table_names)} tables:\n")
        
        # Group tables by category
        core_tables = ['transactions', 'holdings', 'assets', 'balance_sheets']
        config_tables = ['asset_taxonomy', 'asset_mappings', 'system_settings', 'benchmarks']
        system_tables = ['audit_trail', 'import_log', 'backup_manifest', 'config_history']
        
        click.echo("📦 Core Data Tables:")
        for table in table_names:
            if table in core_tables:
                click.echo(f"   ✓ {table}")
        
        click.echo("\n⚙️  Configuration Tables:")
        for table in table_names:
            if table in config_tables:
                click.echo(f"   ✓ {table}")
        
        click.echo("\n🔧 System Management Tables:")
        for table in table_names:
            if table in system_tables:
                click.echo(f"   ✓ {table}")
        
        click.echo("\n" + "="*70)
        click.echo("📝 Next Steps:")
        click.echo("="*70)
        click.echo("1. Migrate existing Excel data:")
        click.echo("   python main.py migrate-to-database  # (Coming in Week 2)")
        click.echo("\n2. Or inspect the database:")
        click.echo("   Use DBeaver or another SQLite browser")
        click.echo("   Database file: data/investment_system.db")
        click.echo("\n3. Test database connection:")
        click.echo("   python -c 'from src.database import get_session; print(get_session())'")
        click.echo("="*70 + "\n")
        
        sys.exit(0)
        
    except Exception as e:
        click.echo(f"\n❌ Database initialization failed: {e}", err=True)
        if verbose:
            import traceback
            click.echo("\n" + traceback.format_exc(), err=True)
        click.echo("\n💡 Troubleshooting tips:", err=True)
        click.echo("   - Check if data/ directory exists", err=True)
        click.echo("   - Ensure SQLAlchemy is installed: pip install sqlalchemy", err=True)
        click.echo("   - Try with --verbose flag for more details", err=True)
        sys.exit(1)


@cli.command(name='migrate-to-database')
@click.option('--dry-run', is_flag=True, help='Preview migration without making changes')
@click.option('--verbose', is_flag=True, help='Show detailed migration logs')
@click.option('--config', default='config/settings.yaml', help='Path to settings.yaml')
def migrate_to_database(dry_run, verbose, config):
    """
    Migrate Excel data to database.
    
    This command transfers all historical financial data from Excel files
    to the SQLite database, including:
    - Transactions (with automatic deduplication)
    - Holdings (current snapshot)
    - Assets (with taxonomy mapping)
    - Balance sheets
    
    Use --dry-run to preview what will be migrated without making changes.
    """
    import logging
    from src.database import DatabaseMigrator
    
    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(message)s'
    )
    
    click.echo("\n" + "="*70)
    click.echo("📦 EXCEL TO DATABASE MIGRATION")
    click.echo("="*70)
    
    if dry_run:
        click.echo("🔍 Running in DRY RUN mode - no changes will be made")
    
    click.echo(f"\nConfiguration: {config}")
    click.echo("="*70 + "\n")
    
    try:
        # Initialize migrator
        migrator = DatabaseMigrator(config_path=config, dry_run=dry_run)
        
        # Run migration
        summary = migrator.migrate_all()
        
        # Display results
        click.echo("\n" + "="*70)
        click.echo("✅ MIGRATION COMPLETE")
        click.echo("="*70)
        click.echo(f"\nStatus: {summary['status'].upper()}")
        click.echo(f"Time elapsed: {summary['elapsed_seconds']:.2f} seconds")
        click.echo(f"\nRecords processed: {summary['total_records_processed']}")
        click.echo(f"Records inserted: {summary['total_records_inserted']}")
        click.echo(f"Errors: {summary['total_errors']}")
        
        click.echo("\nDetailed Statistics:")
        for entity_type, stats in summary['statistics'].items():
            click.echo(f"  {entity_type:15} → {stats['inserted']:4d} inserted, "
                      f"{stats['skipped']:4d} skipped, {stats['errors']:2d} errors")
        
        if summary['total_errors'] > 0:
            click.echo(f"\n⚠️  {summary['total_errors']} errors occurred during migration")
            if verbose and summary['errors']:
                click.echo("\nError details:")
                for i, error in enumerate(summary['errors'][:10], 1):  # Show first 10
                    click.echo(f"  {i}. {error['type']}: {error.get('asset_id', 'N/A')} - {error['error']}")
                if len(summary['errors']) > 10:
                    click.echo(f"  ... and {len(summary['errors']) - 10} more errors")
        
        if dry_run:
            click.echo("\n🔄 Dry run completed - no changes were made to the database")
            click.echo("\nTo actually migrate data, run:")
            click.echo("   python main.py migrate-to-database")
        else:
            click.echo("\n💾 Data has been migrated to: data/investment_system.db")
            click.echo("\nNext steps:")
            click.echo("   1. Verify data: python main.py generate-report")
            click.echo("   2. Or query database directly with DBeaver/SQLite browser")
        
        click.echo("="*70 + "\n")
        
        sys.exit(0 if summary['total_errors'] == 0 else 1)
        
    except FileNotFoundError as e:
        click.echo(f"\n❌ Configuration file not found: {e}", err=True)
        click.echo("\n💡 Make sure config/settings.yaml exists", err=True)
        sys.exit(1)
        
    except Exception as e:
        click.echo(f"\n❌ Migration failed: {e}", err=True)
        if verbose:
            import traceback
            click.echo("\n" + traceback.format_exc(), err=True)
        click.echo("\n💡 Troubleshooting tips:", err=True)
        click.echo("   - Ensure database is initialized: python main.py init-database", err=True)
        click.echo("   - Check Excel files are accessible in config/settings.yaml", err=True)
        click.echo("   - Try with --dry-run flag to preview without committing", err=True)
        click.echo("   - Use --verbose flag for detailed error logs", err=True)
        sys.exit(1)


@cli.command(name='backup')
@click.option('--note', default='', help='Optional note to append to backup filename')
@click.option('--keep', default=30, help='Number of recent backups to keep (default: 30)')
def backup_database(note, keep):
    """
    Create a backup of the database.
    
    Copies the current database file to data/backups/ with a timestamp.
    Also cleans up old backups, keeping the specified number of recent ones.
    """
    try:
        from src.database.backup_manager import BackupManager
        
        click.echo("="*70)
        click.echo("💾 DATABASE BACKUP")
        click.echo("="*70 + "\n")
        
        manager = BackupManager()
        backup_path = manager.create_backup(note=note)
        
        click.echo("✅ Backup created successfully:")
        click.echo(f"   {backup_path}")
        
        manager.cleanup_old_backups(keep_count=keep)
        click.echo(f"\n🧹 Cleanup complete (keeping last {keep} backups)")
        
        click.echo("\n" + "="*70 + "\n")
        
    except Exception as e:
        click.echo(f"\n❌ Backup failed: {e}", err=True)
        sys.exit(1)


@cli.command(name='generate-wealth-insights')
@click.option('--output-dir', default='output', help='Directory to save the report')
def generate_wealth_insights(output_dir):
    """Generate the Wealth Insights & Goal Tracking Report."""
    # Setup logging
    os.makedirs('logs', exist_ok=True)
    logger = setup_logging()
    
    try:
        from src.report_builders.wealth_insights_builder import WealthInsightsBuilder
        
        logger.info("Generating Wealth Insights Report...")
        builder = WealthInsightsBuilder()
        report_path = builder.generate_report(output_dir=output_dir)
        
        click.echo(click.style(f"✅ Report generated successfully: {report_path}", fg='green'))
        
    except Exception as e:
        logger.error(f"Failed to generate report: {str(e)}")
        click.echo(click.style(f"❌ Error generating report: {str(e)}", fg='red'))
        sys.exit(1)

if __name__ == '__main__':
    cli()
