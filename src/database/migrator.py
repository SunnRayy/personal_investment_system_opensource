# File path: src/database/migrator.py
"""
Database migration tool for transferring Excel data to SQLite database.

This module handles the migration of historical financial data from Excel files
to the database, including:
- Transactions (with deduplication)
- Holdings (snapshot management)
- Assets (with taxonomy mapping)
- Balance sheets
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .base import get_session, get_engine
from .models import (
    Transaction, Holding, Asset, BalanceSheet,
    AssetTaxonomy, AssetMapping, ImportLog, AuditTrail
)
from ..data_manager.manager import DataManager


class DatabaseMigrator:
    """
    Migrates Excel-based financial data to database.
    
    Features:
    - Transaction deduplication using transaction_id
    - Asset metadata enrichment with taxonomy mapping
    - Holdings snapshot management
    - Balance sheet migration
    - Comprehensive audit trail
    - Rollback capability on errors
    """
    
    def __init__(self, config_path: str = 'config/settings.yaml', dry_run: bool = False):
        """
        Initialize migrator.
        
        Args:
            config_path: Path to settings.yaml
            dry_run: If True, no database changes are made
        """
        self.config_path = config_path
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)
        
        # Initialize DataManager
        # IMPORTANT: We need DataManager to read from Excel, not DB
        # So we force 'excel' mode to ensure we load source data
        self.data_manager = DataManager(config_path=config_path, force_mode='excel')
        
        # Migration statistics
        self.stats = {
            'transactions': {'total': 0, 'inserted': 0, 'skipped': 0, 'errors': 0},
            'holdings': {'total': 0, 'inserted': 0, 'skipped': 0, 'errors': 0},
            'assets': {'total': 0, 'inserted': 0, 'skipped': 0, 'errors': 0},
            'balance_sheets': {'total': 0, 'inserted': 0, 'skipped': 0, 'errors': 0},
        }
        
        # Error tracking
        self.errors: List[Dict[str, Any]] = []
    
    def migrate_all(self) -> Dict[str, Any]:
        """
        Execute complete migration of all data.
        
        Returns:
            Dictionary with migration results and statistics
        """
        self.logger.info("=" * 80)
        self.logger.info(f"Starting database migration {'(DRY RUN)' if self.dry_run else ''}")
        self.logger.info("=" * 80)
        
        start_time = datetime.now()
        session = get_session()
        
        try:
            # Step 1: Migrate assets first (required for foreign keys)
            self.logger.info("\n📦 Step 1/4: Migrating Assets...")
            self._migrate_assets(session)
            
            # Step 2: Migrate transactions
            self.logger.info("\n💰 Step 2/4: Migrating Transactions...")
            self._migrate_transactions(session)
            
            # Step 3: Migrate holdings
            self.logger.info("\n📊 Step 3/4: Migrating Holdings...")
            self._migrate_holdings(session)
            
            # Step 4: Migrate balance sheets
            self.logger.info("\n📋 Step 4/4: Migrating Balance Sheets...")
            self._migrate_balance_sheets(session)
            
            # Commit if not dry run
            if not self.dry_run:
                session.commit()
                self.logger.info("\n✅ Migration committed to database")
                
                # Log import record
                self._log_import(session, 'Success')
            else:
                session.rollback()
                self.logger.info("\n🔄 Dry run complete - no changes committed")
            
            elapsed = datetime.now() - start_time
            
            # Generate summary
            summary = self._generate_summary(elapsed)
            
            return summary
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"\n❌ Migration failed: {str(e)}")
            
            if not self.dry_run:
                self._log_import(session, 'Failed', error_log=str(e))
            
            raise
            
        finally:
            session.close()
    
    def _migrate_assets(self, session: Session) -> None:
        """Migrate asset metadata with taxonomy mapping."""
        # Collect assets from multiple sources
        all_assets = []
        
        # Source 1: Assets from transactions
        transactions_df = self.data_manager.get_transactions()
        if transactions_df is not None and not transactions_df.empty:
            # Reset index to access Date column
            txn_with_date = transactions_df.reset_index()
            if 'index' in txn_with_date.columns:
                txn_with_date = txn_with_date.rename(columns={'index': 'Date'})
            
            txn_assets = txn_with_date[['Asset_ID', 'Asset_Name']].copy()
            # Handle Asset_Type (might be Asset_Type_Raw in Excel)
            if 'Asset_Type' in txn_with_date.columns:
                txn_assets['Asset_Type'] = txn_with_date['Asset_Type']
            elif 'Asset_Type_Raw' in txn_with_date.columns:
                txn_assets['Asset_Type'] = txn_with_date['Asset_Type_Raw']
            else:
                txn_assets['Asset_Type'] = 'Unknown'
            all_assets.append(txn_assets)
        
        # Source 2: Assets from holdings (may include items without transactions)
        holdings_df = self.data_manager.get_holdings(latest_only=True)
        if holdings_df is not None and not holdings_df.empty:
            # Reset multi-index to get Asset_ID
            holdings_flat = holdings_df.reset_index()
            if 'level_1' in holdings_flat.columns:
                holdings_flat = holdings_flat.rename(columns={'level_1': 'Asset_ID'})
            
            holding_assets = holdings_flat[['Asset_ID', 'Asset_Name']].copy()
            holding_assets['Asset_Type'] = holdings_flat.get('Asset_Type_Raw', 'Unknown')
            all_assets.append(holding_assets)
        
        if not all_assets:
            self.logger.warning("No asset data found in transactions or holdings")
            return
        
        # Combine and deduplicate assets
        combined_assets = pd.concat(all_assets, ignore_index=True)
        asset_data = combined_assets.drop_duplicates(subset=['Asset_ID'])
        asset_data = asset_data.dropna(subset=['Asset_ID'])
        
        self.stats['assets']['total'] = len(asset_data)
        
        for idx, row in asset_data.iterrows():
            try:
                asset_id = self._normalize_asset_id(row['Asset_ID'])
                asset_name = row['Asset_Name']
                asset_type = row.get('Asset_Type', 'Unknown')
                
                # Check if asset already exists
                existing = session.query(Asset).filter_by(asset_id=asset_id).first()
                
                if existing:
                    self.stats['assets']['skipped'] += 1
                    continue
                
                # Get taxonomy info from asset classification
                asset_class, asset_subclass, risk_level = self._infer_asset_taxonomy(asset_id, asset_name, asset_type)
                
                # Create asset record
                asset = Asset(
                    asset_id=asset_id,
                    asset_name=asset_name,
                    asset_type=asset_type,
                    asset_class=asset_class,
                    asset_subclass=asset_subclass,
                    risk_level=risk_level,
                    is_active=True
                )
                
                if not self.dry_run:
                    session.add(asset)
                
                self.stats['assets']['inserted'] += 1
                
                if self.stats['assets']['inserted'] % 10 == 0:
                    self.logger.info(f"  Processed {self.stats['assets']['inserted']} assets...")
                
            except Exception as e:
                self.stats['assets']['errors'] += 1
                self.errors.append({
                    'type': 'asset',
                    'asset_id': row.get('Asset_ID'),
                    'error': str(e)
                })
                self.logger.error(f"  Error migrating asset {row.get('Asset_ID')}: {str(e)}")
        
        self.logger.info(f"✓ Assets: {self.stats['assets']['inserted']} inserted, "
                        f"{self.stats['assets']['skipped']} skipped, "
                        f"{self.stats['assets']['errors']} errors")
    
    def _migrate_transactions(self, session: Session) -> None:
        """Migrate transactions with deduplication."""
        transactions_df = self.data_manager.get_transactions()
        
        if transactions_df is None or transactions_df.empty:
            self.logger.warning("No transactions data found")
            return
        
        # CRITICAL FIX: transactions_df uses date as INDEX, not as a column
        # Reset index to make date accessible as a column
        transactions_df_with_date = transactions_df.reset_index()
        if 'index' in transactions_df_with_date.columns:
            # Rename the index column to Date if it's the datetime index
            transactions_df_with_date = transactions_df_with_date.rename(columns={'index': 'Date'})
        
        self.stats['transactions']['total'] = len(transactions_df_with_date)
        
        for idx, row in transactions_df_with_date.iterrows():
            try:
                # Generate unique transaction_id
                transaction_id = self._generate_transaction_id(row)
                
                # Check for duplicate
                existing = session.query(Transaction).filter_by(transaction_id=transaction_id).first()
                
                if existing:
                    self.stats['transactions']['skipped'] += 1
                    continue
                
                # Convert pandas types to Python/SQL types
                # Date is now accessible as 'Date' column after reset_index()
                txn_date = self._convert_to_date(row.get('Date'))
                shares = self._convert_to_decimal(row.get('Quantity'))
                price = self._convert_to_decimal(row.get('Price_Unit'))
                amount = self._convert_to_decimal(row.get('Amount_Net'))
                
                # Create transaction record
                transaction = Transaction(
                    transaction_id=transaction_id,
                    date=txn_date,
                    asset_id=self._normalize_asset_id(row.get('Asset_ID')),
                    asset_name=row.get('Asset_Name'),
                    transaction_type=row.get('Transaction_Type'),
                    shares=shares,
                    price=price,
                    amount=amount,
                    currency=row.get('Currency', 'CNY'),
                    source=self._determine_source(row),
                    created_by='migration'
                )
                
                if not self.dry_run:
                    session.add(transaction)
                
                self.stats['transactions']['inserted'] += 1
                
                if self.stats['transactions']['inserted'] % 100 == 0:
                    self.logger.info(f"  Processed {self.stats['transactions']['inserted']} transactions...")
                
            except Exception as e:
                self.stats['transactions']['errors'] += 1
                self.errors.append({
                    'type': 'transaction',
                    'date': row.get('Date'),
                    'asset': row.get('Asset_Name'),
                    'error': str(e)
                })
                self.logger.error(f"  Error migrating transaction: {str(e)}")
        
        self.logger.info(f"✓ Transactions: {self.stats['transactions']['inserted']} inserted, "
                        f"{self.stats['transactions']['skipped']} skipped, "
                        f"{self.stats['transactions']['errors']} errors")
    
    def _migrate_holdings(self, session: Session) -> None:
        """Migrate holdings as snapshots.
        
        Note: Database stores one holding per unique Asset_ID, aggregating sub-policies
        (e.g., insurance products with multiple sub-types). Excel may have multiple rows
        per Asset_ID for detailed breakdowns, but database sums Market_Value_CNY by Asset_ID.
        """
        holdings_df = self.data_manager.get_holdings(latest_only=True)
        
        if holdings_df is None or holdings_df.empty:
            self.logger.warning("No holdings data found")
            return
        
        # CRITICAL: holdings_df uses MultiIndex (Date, Asset_ID)
        # Reset index to make these accessible as columns
        holdings_df_flat = holdings_df.reset_index()
        
        # Rename index columns appropriately
        if 'level_0' in holdings_df_flat.columns:
            holdings_df_flat = holdings_df_flat.rename(columns={'level_0': 'Snapshot_Date', 'level_1': 'Asset_ID'})
        
        # Aggregate by (Snapshot_Date, Asset_ID) to handle insurance sub-policies
        # Sum Market_Value_CNY for sub-policies, keep first Asset_Name
        holdings_aggregated = holdings_df_flat.groupby(['Snapshot_Date', 'Asset_ID']).agg({
            'Asset_Name': 'first',
            'Quantity': 'sum',  # Sum shares/policies
            'Market_Price_Unit': 'mean',  # Average price (or could use 'first')
            'Market_Value_CNY': 'sum',  # CRITICAL: Sum total value across sub-policies
            'Cost_Price_Unit': 'mean',
            'Currency': 'first'
        }).reset_index()
        
        self.stats['holdings']['total'] = len(holdings_aggregated)
        self.logger.info(f"  Aggregated {len(holdings_df_flat)} Excel rows into {len(holdings_aggregated)} unique holdings")
        
        for idx, row in holdings_aggregated.iterrows():
            try:
                # Extract date and asset_id from the flattened columns
                snapshot_date = self._convert_to_date(row.get('Snapshot_Date'))
                asset_id = self._normalize_asset_id(row.get('Asset_ID'))
                
                # Check for duplicate (same date + asset)
                existing = session.query(Holding).filter_by(
                    snapshot_date=snapshot_date,
                    asset_id=asset_id
                ).first()
                
                if existing:
                    self.stats['holdings']['skipped'] += 1
                    continue
                
                # Convert values - use actual column names from DataManager
                shares = self._convert_to_decimal(row.get('Quantity'))  # Changed from Current_Shares
                current_price = self._convert_to_decimal(row.get('Market_Price_Unit'))  # Changed from Current_Price
                market_value = self._convert_to_decimal(row.get('Market_Value_CNY'))
                cost_basis = self._convert_to_decimal(row.get('Cost_Price_Unit'))  # Approximate
                unrealized_pnl = None  # Not directly available, can be calculated
                
                # Create holding record
                holding = Holding(
                    snapshot_date=snapshot_date,
                    asset_id=asset_id,
                    asset_name=row.get('Asset_Name'),
                    shares=shares,
                    current_price=current_price,
                    market_value=market_value,
                    cost_basis=cost_basis,
                    unrealized_pnl=unrealized_pnl,
                    currency=row.get('Currency', 'CNY')
                )
                
                if not self.dry_run:
                    session.add(holding)
                
                self.stats['holdings']['inserted'] += 1
                
            except Exception as e:
                self.stats['holdings']['errors'] += 1
                self.errors.append({
                    'type': 'holding',
                    'asset_id': asset_id if 'asset_id' in locals() else 'unknown',
                    'error': str(e)
                })
                self.logger.error(f"  Error migrating holding {asset_id if 'asset_id' in locals() else row.get('Asset_Name')}: {str(e)}")
        
        self.logger.info(f"✓ Holdings: {self.stats['holdings']['inserted']} inserted, "
                        f"{self.stats['holdings']['skipped']} skipped, "
                        f"{self.stats['holdings']['errors']} errors")
    
    def _migrate_balance_sheets(self, session: Session) -> None:
        """Migrate ALL balance sheet historical snapshots (not just latest)."""
        balance_sheet_df = self.data_manager.get_balance_sheet()
        
        if balance_sheet_df is None or balance_sheet_df.empty:
            self.logger.warning("No balance sheet data found")
            return
        
        # Balance sheet DataFrame has Date as index, line items as columns
        # Migrate ALL historical snapshots, not just the latest
        
        if not isinstance(balance_sheet_df.index, pd.DatetimeIndex):
            self.logger.warning("Balance sheet index is not DatetimeIndex, skipping migration")
            return
        
        total_records = len(balance_sheet_df) * len(balance_sheet_df.columns)
        self.stats['balance_sheets']['total'] = total_records
        self.logger.info(f"Migrating {len(balance_sheet_df)} balance sheet snapshots with {len(balance_sheet_df.columns)} line items each")
        
        # Iterate over ALL date snapshots
        for snapshot_datetime in balance_sheet_df.index:
            snapshot_date = self._convert_to_date(snapshot_datetime)
            row_data = balance_sheet_df.loc[snapshot_datetime]
            
            # Each column is a line item
            for line_item, amount in row_data.items():
                try:
                    # Skip if line_item is not a string (might be timestamp)
                    if not isinstance(line_item, str):
                        continue
                
                    # --- FILTERING LOGIC ---
                    # Skip calculated columns (_FromUSD, _FromCNY) to avoid duplicates
                    if '_FromUSD' in line_item or '_FromCNY' in line_item:
                        self.stats['balance_sheets']['skipped'] += 1
                        continue
                        
                    # Skip Chase/Discover CNY columns (duplicates of USD columns)
                    if line_item in ['Asset_Deposit_Chase_CNY', 'Asset_Deposit_Discover_CNY']:
                        self.stats['balance_sheets']['skipped'] += 1
                        continue
                    # -----------------------

                    amount_decimal = self._convert_to_decimal(amount)
                    
                    # Skip zero or null amounts
                    if amount_decimal is None or amount_decimal == 0:
                        self.stats['balance_sheets']['skipped'] += 1
                        continue
                    
                    # Infer category from line item name
                    category, subcategory = self._infer_balance_sheet_category(line_item)
                    
                    # Detect currency
                    currency = 'USD' if line_item.endswith('_USD') else 'CNY'
                    
                    # Create balance sheet record
                    balance_sheet = BalanceSheet(
                        snapshot_date=snapshot_date,
                        category=category,
                        subcategory=subcategory,
                        line_item=line_item,
                        amount=amount_decimal,
                        currency=currency
                    )
                    
                    if not self.dry_run:
                        session.add(balance_sheet)
                    
                    self.stats['balance_sheets']['inserted'] += 1
                    
                except Exception as e:
                    self.stats['balance_sheets']['errors'] += 1
                    self.errors.append({
                        'type': 'balance_sheet',
                        'line_item': str(line_item),
                        'error': str(e)
                    })
                    self.logger.error(f"  Error migrating balance sheet {line_item}: {str(e)}")
        
        self.logger.info(f"✓ Balance Sheets: {self.stats['balance_sheets']['inserted']} inserted, "
                        f"{self.stats['balance_sheets']['skipped']} skipped, "
                        f"{self.stats['balance_sheets']['errors']} errors")
    
    # Helper methods
    
    def _generate_transaction_id(self, row: pd.Series) -> str:
        """
        Generate unique transaction ID.
        
        Format: {source}_{asset_id}_{date}_{type}_{amount}_{sequence}
        """
        source = self._determine_source(row)
        asset_id = self._normalize_asset_id(row.get('Asset_ID', 'UNKNOWN'))
        txn_date = str(row.get('Transaction_Date', ''))[:10]  # YYYY-MM-DD
        txn_type = str(row.get('Transaction_Type', 'UNKNOWN'))
        amount = abs(float(row.get('Amount_Net', 0)))
        
        # Create base ID
        base_id = f"{source}_{asset_id}_{txn_date}_{txn_type}_{amount:.2f}"
        
        # Add hash of full row to ensure uniqueness for same-day same-amount transactions
        import hashlib
        row_str = str(row.to_dict())
        hash_suffix = hashlib.md5(row_str.encode()).hexdigest()[:8]
        
        return f"{base_id}_{hash_suffix}"
    
    def _determine_source(self, row: pd.Series) -> str:
        """Determine data source from row."""
        # Check for source indicators
        if 'Source' in row and pd.notna(row['Source']):
            return str(row['Source'])
        
        # Infer from asset type or other fields
        asset_id = str(row.get('Asset_ID', ''))
        
        if 'RSU' in asset_id:
            return 'Manual_RSU'
        elif 'Schwab' in str(row.get('Account', '')):
            return 'Schwab_CSV'
        else:
            return 'CN_Fund_Excel'
    
    def _infer_asset_taxonomy(self, asset_id: str, asset_name: str, asset_type: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Infer asset_class, asset_subclass, and risk_level using the actual taxonomy system.
        Uses portfolio_lib asset_mapper for consistent classification.
        """
        try:
            # Import and initialize taxonomy mapper
            from ..portfolio_lib.core.asset_mapper import initialize_mapper_taxonomy, _map_asset_to_top_class_internal, _map_asset_to_sub_class_internal
            import yaml
            
            # Load taxonomy once (static/module-level, so only first call loads it)
            if not hasattr(self, '_taxonomy_initialized'):
                taxonomy_path = self.config_path.replace('settings.yaml', 'asset_taxonomy.yaml')
                with open(taxonomy_path, 'r', encoding='utf-8') as f:
                    taxonomy = yaml.safe_load(f)
                initialize_mapper_taxonomy(taxonomy)
                self._taxonomy_initialized = True
            
            # Use asset_name for classification (more descriptive than ID)
            asset_for_mapping = asset_name if asset_name else asset_id
            
            # Get classification from taxonomy
            asset_class = _map_asset_to_top_class_internal(asset_for_mapping)
            asset_subclass = _map_asset_to_sub_class_internal(asset_for_mapping)
            
            # Infer risk level based on asset class
            risk_level = 'Medium'
            if asset_class == 'Equity':
                risk_level = 'High'
            elif asset_class == 'Fixed_Income':
                risk_level = 'Low'
            elif asset_class == 'Cash':
                risk_level = 'Low'
            elif asset_class == 'Alternative':
                risk_level = 'High'
            elif asset_class == 'Insurance':
                risk_level = 'Low'
            
            return asset_class, asset_subclass, risk_level
            
        except Exception as e:
            self.logger.warning(f"Error inferring taxonomy for {asset_name}: {e}")
            # Fallback to basic inference
            asset_id_lower = asset_id.lower()
            if 'rsu' in asset_id_lower:
                return 'Equity', 'US_Stock', 'High'
            elif 'gold' in asset_id_lower:
                return 'Alternative', 'Gold', 'Medium'
            elif 'ins_' in asset_id_lower:
                return 'Insurance', 'Life', 'Low'
            return None, None, None
    
    def _infer_balance_sheet_category(self, line_item: str) -> Tuple[str, str]:
        """Infer balance sheet category and subcategory."""
        line_lower = line_item.lower()
        
        if 'asset' in line_lower or '资产' in line_item:
            return 'Asset', 'Investments'
        elif 'liability' in line_lower or '负债' in line_item:
            return 'Liability', 'Loans'
        else:
            return 'Asset', 'Other'
    
    def _convert_to_date(self, value: Any) -> Optional[date]:
        """Convert various date formats to Python date."""
        if pd.isna(value):
            return None
        
        if isinstance(value, date):
            return value
        
        if isinstance(value, datetime):
            return value.date()
        
        if isinstance(value, pd.Timestamp):
            return value.date()
        
        if isinstance(value, str):
            try:
                return pd.to_datetime(value).date()
            except:
                return None
        
        return None
    
    def _convert_to_decimal(self, value: Any) -> Optional[Decimal]:
        """Convert numeric values to Decimal for database storage."""
        if pd.isna(value):
            return None
        
        try:
            return Decimal(str(value))
        except:
            return None

    def _normalize_asset_id(self, asset_id: Any) -> str:
        """Normalize asset ID to string, removing .0 suffix if present."""
        if pd.isna(asset_id):
            return "UNKNOWN"
        
        s_id = str(asset_id).strip()
        if s_id.endswith('.0'):
            return s_id[:-2]
        return s_id
    
    def _log_import(self, session: Session, status: str, error_log: Optional[str] = None) -> None:
        """Log import operation to database."""
        import_log = ImportLog(
            source_file='Excel (DataManager)',
            source_type='Migration',
            records_imported=sum(s['inserted'] for s in self.stats.values()),
            records_updated=0,
            records_failed=sum(s['errors'] for s in self.stats.values()),
            error_log=error_log,
            imported_by='migration_tool',
            status=status,
            can_rollback=True
        )
        session.add(import_log)
        session.commit()
    
    def _generate_summary(self, elapsed) -> Dict[str, Any]:
        """Generate migration summary report."""
        total_processed = sum(s['total'] for s in self.stats.values())
        total_inserted = sum(s['inserted'] for s in self.stats.values())
        total_errors = sum(s['errors'] for s in self.stats.values())
        
        summary = {
            'status': 'success' if total_errors == 0 else 'completed_with_errors',
            'dry_run': self.dry_run,
            'elapsed_seconds': elapsed.total_seconds(),
            'total_records_processed': total_processed,
            'total_records_inserted': total_inserted,
            'total_errors': total_errors,
            'statistics': self.stats,
            'errors': self.errors
        }
        
        # Print summary
        self.logger.info("\n" + "=" * 80)
        self.logger.info("MIGRATION SUMMARY")
        self.logger.info("=" * 80)
        self.logger.info(f"Status: {summary['status'].upper()}")
        self.logger.info(f"Elapsed time: {elapsed.total_seconds():.2f} seconds")
        self.logger.info(f"Total records: {total_processed}")
        self.logger.info(f"Successfully inserted: {total_inserted}")
        self.logger.info(f"Errors: {total_errors}")
        self.logger.info("\nDetails:")
        for entity_type, stats in self.stats.items():
            self.logger.info(f"  {entity_type}: {stats['inserted']}/{stats['total']} "
                           f"(skipped: {stats['skipped']}, errors: {stats['errors']})")
        
        if self.errors:
            self.logger.info(f"\n⚠️  {len(self.errors)} errors occurred. See errors list for details.")
        
        return summary
