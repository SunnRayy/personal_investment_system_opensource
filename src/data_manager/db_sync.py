
import logging
import os
import yaml
import pandas as pd
from typing import Optional
from src.database import get_session, Asset
from src.data_manager.readers import read_schwab_data

logger = logging.getLogger(__name__)

def sync_assets_to_db():
    """
    Reads assets from:
    1. Schwab CSVs
    2. Funding Excel
    And inserts missing assets into the SQLite database.
    This ensures the Web App (DB-backed) sees assets from the file-based pipeline.
    """
    session = get_session()
    added_count = 0
    
    try:
        # --- 1. Sync Schwab Assets ---
        logger.info("Syncing Schwab Assets to DB...")
        
        # Load config safely
        config_path = 'config/settings.yaml'
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            schwab_data = read_schwab_data(config)
            schwab_holdings = schwab_data.get('holdings')
            
            if schwab_holdings is not None and not schwab_holdings.empty:
                logger.info(f"Found {len(schwab_holdings)} Schwab holdings to check.")
                
                for _, row in schwab_holdings.iterrows():
                    # Try standard cleaned names first, then raw Schwab names
                    asset_id = row.get('Asset_ID') or row.get('Symbol')
                    asset_name = row.get('Asset_Name') or row.get('Description')
                    asset_type = row.get('Asset_Type_Raw') or row.get('Security Type', 'US Equity')
                    
                    if not asset_id:
                        continue
                    
                    # Normalize
                    asset_id = str(asset_id).strip()
                    if asset_name:
                         asset_name = str(asset_name).strip()
                                        
                    # Check DB
                    existing = session.query(Asset).filter_by(asset_id=asset_id).first()
                    if not existing:
                        logger.info(f"Adding New Asset to DB: {asset_id} - {asset_name}")
                        new_asset = Asset(
                            asset_id=asset_id,
                            asset_name=asset_name,
                            asset_type=asset_type
                        )
                        session.add(new_asset)
                        added_count += 1
        else:
            logger.warning(f"Config file not found: {config_path}")
        
        # --- 2. Sync Global Markets Assets (Funding Excel) ---
        logger.info("Syncing Global Markets Assets to DB...")
        fund_file = config.get('data_files', {}).get('fund_transactions', {}).get('path', 'data/funding_transactions.xlsx')
        if os.path.exists(fund_file):
            try:
                # Try standard sheet names first, then Chinese names as fallback
                df = None
                for sheet_name in ['Holdings', '基金持仓汇总']:
                    try:
                        df = pd.read_excel(fund_file, sheet_name=sheet_name)
                        break
                    except:
                        continue
                if df is not None and not df.empty:
                    logger.info(f"Found {len(df)} Global Markets holdings to check.")
                    for _, row in df.iterrows():
                        # Handle varied column names
                        asset_id = row.get('Asset_ID') or row.get('Symbol') or row.get('基金代码')
                        asset_name = row.get('Asset_Name') or row.get('Name') or row.get('基金名称')
                        asset_type = row.get('Asset_Type') or row.get('Type') or row.get('基金类型', 'CN Fund')
                        
                        if not asset_id:
                            continue
                            
                        # Normalize ID
                        asset_id = str(asset_id).strip()
                        if asset_name:
                             asset_name = str(asset_name).strip()
                        
                        existing = session.query(Asset).filter_by(asset_id=asset_id).first()
                        if not existing:
                            logger.info(f"Adding New Asset to DB: {asset_id} - {asset_name}")
                            new_asset = Asset(
                                asset_id=asset_id,
                                asset_name=asset_name,
                                asset_type=asset_type
                            )
                            session.add(new_asset)
                            added_count += 1
            except Exception as e:
                logger.error(f"Error checking Global Markets funds: {e}")
        
        # --- 3. Sync RSU Assets ---
        logger.info("Syncing RSU Assets to DB...")
        rsu_file = config.get('data_files', {}).get('rsu_transactions', {}).get('path', 'data/RSU_transactions.xlsx')
        if os.path.exists(rsu_file):
            try:
                for sheet_name in ['Transactions', 'transactions']:
                    try:
                        df = pd.read_excel(rsu_file, sheet_name=sheet_name)
                        break
                    except:
                        df = None
                        continue
                if df is not None and not df.empty:
                    # Get unique asset names from transactions
                    asset_col = 'Asset_Name' if 'Asset_Name' in df.columns else 'Asset'
                    if asset_col in df.columns:
                        unique_assets = df[asset_col].dropna().unique()
                        for asset_name in unique_assets:
                            asset_id = str(asset_name).strip()
                            existing = session.query(Asset).filter_by(asset_id=asset_id).first()
                            if not existing:
                                logger.info(f"Adding New RSU Asset to DB: {asset_id}")
                                new_asset = Asset(
                                    asset_id=asset_id,
                                    asset_name=asset_name,
                                    asset_type='RSU'
                                )
                                session.add(new_asset)
                                added_count += 1
            except Exception as e:
                logger.error(f"Error checking RSU assets: {e}")
        
        # --- 4. Sync Gold Assets ---
        logger.info("Syncing Gold Assets to DB...")
        gold_file = config.get('data_files', {}).get('gold_transactions', {}).get('path', 'data/Gold_transactions.xlsx')
        if os.path.exists(gold_file):
            try:
                for sheet_name in ['Holdings', 'holdings']:
                    try:
                        df = pd.read_excel(gold_file, sheet_name=sheet_name)
                        break
                    except:
                        df = None
                        continue
                if df is not None and not df.empty:
                    asset_col = 'Asset_Name' if 'Asset_Name' in df.columns else 'Name'
                    if asset_col in df.columns:
                        unique_assets = df[asset_col].dropna().unique()
                        for asset_name in unique_assets:
                            asset_id = str(asset_name).strip()
                            existing = session.query(Asset).filter_by(asset_id=asset_id).first()
                            if not existing:
                                logger.info(f"Adding New Gold Asset to DB: {asset_id}")
                                new_asset = Asset(
                                    asset_id=asset_id,
                                    asset_name=asset_name,
                                    asset_type='Gold'
                                )
                                session.add(new_asset)
                                added_count += 1
            except Exception as e:
                logger.error(f"Error checking Gold assets: {e}")
        
        if added_count > 0:
            session.commit()
            logger.info(f"✅ Successfully synced {added_count} new assets to the database.")
            return True
        else:
            logger.info("No new assets found to sync.")
            return True
            
    except Exception as e:
        session.rollback()
        logger.error(f"Asset Sync failed: {e}")
        return False
    finally:
        session.close()

def sync_balance_sheet_to_db():
    """
    Syncs Balance Sheet data from Excel (Financial Summary) to the SQLite database.
    This ensures the 'parity' check uses fresh data.
    """
    from src.database.models import BalanceSheet
    from src.data_manager.cleaners import BALANCE_SHEET_COL_MAP
    import yaml
    
    logger.info("Syncing Balance Sheet to DB...")
    session = get_session()
    
    try:
        # 1. Load Config to get correct path
        config_path = 'config/settings.yaml'
        if not os.path.exists(config_path):
            logger.warning("Config file not found.")
            return False
            
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        bs_config = config.get('data_files', {}).get('financial_summary', {})
        file_path = bs_config.get('path')
        sheet_name = bs_config.get('sheets', {}).get('balance_sheet', '资产负债')
        
        if not file_path or not os.path.exists(file_path):
            logger.warning(f"Balance sheet file not found at: {file_path}")
            return False
            
        # 2. Read Raw Excel
        # CRITICAL: Header is on Row 3 (Index 3), so data starts Row 4.
        try:
            bs_df = pd.read_excel(file_path, sheet_name=sheet_name, header=3, index_col=0)
        except Exception as e:
            logger.error(f"Failed to read Balance Sheet Excel: {e}")
            return False
        
        count = 0
        skipped_cols = set()
        
        for date_val, row in bs_df.iterrows():
            if pd.isna(date_val):
                continue
                
            try:
                # Ensure date is valid
                snapshot_date = pd.to_datetime(date_val).date()
            except:
                continue
            
            # Iterate through mapped columns only
            # We iterate through the ROW to find matching columns in our map
            for col_name, value in row.items():
                col_str = str(col_name).strip()
                
                # Check mapping
                if col_str not in BALANCE_SHEET_COL_MAP:
                    skipped_cols.add(col_str)
                    continue
                    
                standard_line_item = BALANCE_SHEET_COL_MAP[col_str]
                
                # Clean value
                if pd.isna(value):
                    continue
                try:
                    # Simple clean for now, assume mostly numeric if mapped
                    if isinstance(value, str):
                        value = value.replace('¥', '').replace(',', '').strip()
                    amount_val = float(value)
                except:
                    continue
                    
                # DB Upsert
                existing = session.query(BalanceSheet).filter_by(
                    snapshot_date=snapshot_date,
                    line_item=standard_line_item
                ).first()
                
                if existing:
                    # Fix: Handle Decimal vs Float comparison
                    existing_val = float(existing.amount) if existing.amount is not None else 0.0
                    if abs(existing_val - amount_val) > 0.01:
                        existing.amount = amount_val
                        count += 1
                else:
                    new_bs_item = BalanceSheet(
                        snapshot_date=snapshot_date,
                        line_item=standard_line_item,
                        amount=amount_val,
                        currency='CNY' # Default to CNY, but some might be USD ideally?
                        # Note: The MAP has _USD suffix for some assets.
                        # Ideally we should store currency separately, but for now strict consistency:
                        # If mapped name has _USD, maybe we set currency='USD'?
                        # Let's keep it simple: Store raw amount. 
                        # HoldingsCalculator logic handles _USD suffix interpretation.
                    )
                    # Improvement: Parse currency from ID
                    if standard_line_item.endswith('_USD'):
                        new_bs_item.currency = 'USD'
                    
                    session.add(new_bs_item)
                    count += 1
        
        session.commit()
        logger.info(f"✅ Synced {count} Balance Sheet items to DB.")
        
        # 3. Propagate to Holding Table (Snapshot)
        # In DB Mode, the system queries the 'Holding' table, not 'BalanceSheet'.
        # We must transform BS items into Holding entries for the report to see them.
        sync_bs_to_holdings(session, snapshot_date)
        
        return True
        
    except Exception as e:
        session.rollback()
        logger.error(f"Balance Sheet Sync failed: {e}")
        return False
    finally:
        session.close()

def sync_bs_to_holdings(session, snapshot_date):
    """
    Transforms BalanceSheet items for a given date into Holding entries.
    This ensures that Assets tracked in the Balance Sheet (Cash, Property, etc.)
    appear in the 'Holdings' report query.
    """
    from src.database.models import BalanceSheet, Holding, Asset
    
    # Mapping: BalanceSheet.line_item -> Asset.asset_id
    # Derived from src.portfolio_lib.holdings_calculator.bs_mapping
    # We must REVERSE the mapping to find the Asset ID.
    BS_TO_ASSET_ID = {
        'Asset_Invest_BankWealth_Value': 'BankWealth_招行',
        'Asset_Invest_Pension_Value': 'Pension_Personal',
        'Asset_Fixed_Property_Value': 'Property_Residential_A',
        'Asset_Bank_Account_A': 'Bank_Account_A',
        'Asset_Deposit_BOB_CNY': 'Deposit_BOB_CNY',
        'Asset_Deposit_CMB_CNY': 'Deposit_CMB_CNY',
        'Asset_Deposit_BOC_USD': 'Deposit_BOC_USD',
        'Asset_Deposit_Chase_USD': 'Deposit_Chase_USD',
        'Asset_Deposit_Discover_USD': 'Deposit_Discover_USD',
    }
    
    # Hardcoded FX for normalization only (Refine to use DB source if needed)
    FX_USD_CNY = 7.05 
    
    logger.info(f"Propagating Balance Sheet data to Holdings for {snapshot_date}...")
    
    bs_items = session.query(BalanceSheet).filter_by(snapshot_date=snapshot_date).all()
    count = 0
    
    for item in bs_items:
        if item.line_item not in BS_TO_ASSET_ID:
            continue
            
        asset_id = BS_TO_ASSET_ID[item.line_item]
        
        # Calculate Market Value in CNY
        # DatabaseConnector expects 'Market_Value_CNY' in the query alias
        market_val = float(item.amount)
        currency = 'CNY'
        
        if '_USD' in item.line_item or item.currency == 'USD':
            market_val = market_val * FX_USD_CNY
            currency = 'USD' # We store original currency metadata, but val is CNY? 
            # Wait, Holding schema: market_value, currency. 
            # If we store market_value as CNY, set currency='CNY' to match value?
            # Or store converted value and 'USD' label?
            # Let's check typical Holding usage. 
            # If we want total portfolio sum: sum(market_value). So market_value MUST be CNY (base).
            currency = 'CNY' # Normalize to Base Currency for reporting aggregation
        
        # Upsert Holding
        existing_holding = session.query(Holding).filter_by(
            snapshot_date=snapshot_date,
            asset_id=asset_id
        ).first()
        
        # Fetch Asset Name if possible
        asset_name = asset_id
        asset_record = session.query(Asset).filter_by(asset_id=asset_id).first()
        if asset_record:
            asset_name = asset_record.asset_name
            
        if existing_holding:
            existing_holding.market_value = market_val
            existing_holding.shares = float(item.amount) if currency == 'USD' else 1.0 # Store original amount in shares?
            # For cash/deposits, shares concept is weak.
            # Just ensure market_value is correct.
        else:
            new_holding = Holding(
                snapshot_date=snapshot_date,
                asset_id=asset_id,
                asset_name=asset_name,
                shares=float(item.amount), # Treats raw amount as 'units'
                current_price=1.0 if currency == 'CNY' else FX_USD_CNY,
                market_value=market_val,
                currency=currency,
                cost_basis=market_val, # Assume cost = value for cash/fixed assets
                unrealized_pnl=0.0
            )
            session.add(new_holding)
        count += 1
        
    session.commit()
    logger.info(f"✅ Propagated {count} Balance Sheet items to Holding table.")

def sync_full_holdings_snapshot():
    """
    Calculates the full portfolio snapshot using the legacy/Excel pipeline
    and saves the result to the Database 'Holding' table.
    
    This ensures that assets calculated on-the-fly (RSUs, Schwab Stocks)
    and file-based assets (Funds) are all present in the Database for reporting.
    """
    from src.data_manager.manager import DataManager
    from src.database.models import Holding, Asset
    from src.database.base import get_session
    from datetime import datetime
    
    logger.info("📸 Starting Full Holdings Snapshot Sync...")
    
    # 1. Get Data from Excel Pipeline
    # Force Excel mode to use calculation logic
    dm = DataManager(force_mode='excel') 
    metrics_df = dm.get_holdings(latest_only=True)
    
    if metrics_df is None or metrics_df.empty:
        logger.warning("⚠️ No holdings data calculated from Excel pipeline. Skipping snapshot.")
        return False
        
    session = get_session()
    count = 0
    updated = 0
    
    try:
        # 2. Iterate and Upsert to DB
        logger.info(f"DataFrame Index Type: {type(metrics_df.index)}")
        logger.info(f"DataFrame Index Names: {metrics_df.index.names}")
        logger.info(f"DataFrame Columns: {metrics_df.columns.tolist()}")

        # We use the max date from the dataframe as the snapshot date
        # Handle MultiIndex
        if isinstance(metrics_df.index, pd.MultiIndex):
            # Fix: Index name is 'Snapshot_Date' based on manager.get_holdings output
            idx_name = 'Snapshot_Date' if 'Snapshot_Date' in metrics_df.index.names else 'Date'
            try:
                snapshot_date = metrics_df.index.get_level_values(idx_name).max()
            except KeyError:
                # Fallback if neither found (shouldn't happen given debug)
                snapshot_date = datetime.now().date()
        else:
            if 'Date' in metrics_df.columns:
                 snapshot_date = metrics_df['Date'].max()
            else:
                 snapshot_date = datetime.now().date()

        if pd.isna(snapshot_date):
            snapshot_date = datetime.now().date()
        else:
            # Normalize to date object if timestamp
            if hasattr(snapshot_date, 'date'):
                 snapshot_date = snapshot_date.date()
            
        logger.info(f"Syncing snapshot for date: {snapshot_date}")
        
        # Get existing holdings for this date to support upsert/update
        existing_holdings = session.query(Holding).filter_by(snapshot_date=snapshot_date).all()
        existing_map = {h.asset_id: h for h in existing_holdings}
        
        # Reset index to access Asset_ID easily if it's in index
        df_reset = metrics_df.reset_index()
        
        for _, row in df_reset.iterrows():
            asset_id = row.get('Asset_ID')
            if not asset_id:
                continue
                
            # Extract standard fields
            asset_name = row.get('Asset_Name', asset_id)
            shares = row.get('Quantity', 0.0)
            
            # Helper to safely float
            def safe_float(val):
                try:
                    return float(val) if pd.notnull(val) else 0.0
                except:
                    return 0.0
            
            price = safe_float(row.get('Market_Price_Unit', 0.0))
            market_val = safe_float(row.get('Market_Value_CNY', 0.0))
            cost_basis = safe_float(row.get('Cost_Basis_CNY', 0.0))
            currency = row.get('Currency', 'CNY')
            
            # Upsert
            if asset_id in existing_map:
                h = existing_map[asset_id]
                h.shares = safe_float(shares)
                h.current_price = price
                h.market_value = market_val
                h.currency = str(currency)
                if cost_basis:
                    h.cost_basis = cost_basis
                updated += 1
            else:
                new_h = Holding(
                    snapshot_date=snapshot_date,
                    asset_id=str(asset_id),
                    asset_name=str(asset_name),
                    shares=safe_float(shares),
                    current_price=price,
                    market_value=market_val,
                    cost_basis=cost_basis,
                    currency=str(currency),
                    unrealized_pnl=market_val - cost_basis
                )
                session.add(new_h)
                count += 1
        
        # Delete stale holdings that exist in DB but NOT in source Excel
        source_asset_ids = set(df_reset['Asset_ID'].dropna().astype(str))
        deleted = 0
        for asset_id, holding in existing_map.items():
            if asset_id not in source_asset_ids:
                session.delete(holding)
                deleted += 1
                logger.info(f"🗑️ Deleting stale holding: {asset_id}")
                
        session.commit()
        logger.info(f"✅ Full Snapshot Sync Complete: Added {count}, Updated {updated}, Deleted {deleted} records for {snapshot_date}.")
        return True
        
    except Exception as e:
        session.rollback()
        logger.error(f"Full Snapshot Sync Failed: {e}")
        return False
    finally:
        session.close()

def sync_monthly_data_to_db():
    """
    Syncs Monthly Income & Expense data from Excel to SQLite 'monthly_financial_snapshots'.
    Aggregates granular columns from 'Monthly Income & Expense' sheet into model fields.
    """
    from src.database.models import MonthlyFinancialSnapshot
    from src.data_manager.cleaners import clean_monthly_income_expense, MONTHLY_COL_MAP
    import yaml
    
    logger.info("📅 Syncing Monthly Financial Data to DB...")
    session = get_session()
    
    try:
        # 1. Load Config
        config_path = 'config/settings.yaml'
        # Default fallback if config fails
        file_path_default = "data/Financial Summary.xlsx"
        sheet_name_default = "Monthly Income & Expense"
        
        file_path = file_path_default
        sheet_name = sheet_name_default
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            bs_config = config.get('data_files', {}).get('financial_summary', {})
            file_path = bs_config.get('path', file_path_default)
            sheet_name = bs_config.get('sheets', {}).get('monthly_income_expense', sheet_name_default)
            
        if not os.path.exists(file_path):
            logger.warning(f"Financial Summary file not found at: {file_path}")
            return False
            
        # 2. Read Raw Excel
        # CRITICAL: Header is on Row 3 (Index 3) usually for this file structure
        try:
            df_raw = pd.read_excel(file_path, sheet_name=sheet_name, header=3)
        except Exception as e:
            logger.error(f"Failed to read Monthly sheet: {e}")
            return False
            
        # 3. Clean Data (Standardize columns and dates)
        df_clean = clean_monthly_income_expense(df_raw, {})
        
        if df_clean is None or df_clean.empty:
            logger.warning("No valid monthly data found.")
            return False
            
        # 4. Map & Upsert
        count = 0
        updated = 0
        
        # Field Mapping: Granular Cleaned Col -> Model Field
        # Note: USD columns need FX conversion using that row's Ref_USD_FX_Rate
        FIELD_MAP = {
            # Income
            'salary_income': ['Income_Salary_CNY', 'Income_Reimbursement_CNY', 'Income_Benefit_CNY', 'Income_HousingFund_CNY'],
            'rsu_income': ['Income_RSU_CNY', 'Income_RSU_USD'], # USD Special handling
            'investment_income': ['Income_Passive_Unknown_CNY', 'Income_Passive_FundRedemption_CNY', 'Income_Passive_BankWealth_CNY', 'Income_Passive_GoldSale_CNY'],
            'other_income': ['Income_Other_CNY'],
            
            # Expense
            'housing_expense': ['Expense_Housing_CNY', 'Outflow_Loan_Mortgage_CNY'], # Mortgage is mostly housing expense
            'living_expense': ['Expense_Food_CNY', 'Expense_Transport_CNY', 'Expense_Apparel_CNY', 'Expense_Electronics_CNY', 'Expense_FamilyTemp_CNY'],
            'healthcare_expense': ['Expense_HealthFitness_CNY', 'Outflow_Insurance_Pingan_CNY', 'Outflow_Insurance_Amazon_CNY', 'Outflow_Insurance_Alipay_CNY'],
            'entertainment_expense': ['Expense_Travel_CNY', 'Expense_Entertainment_CNY'],
            'other_expense': ['Expense_WorkRelated_CNY'],
            
            # Investment Outflow (Not in Total Expense)
            'investment_expense': ['Outflow_Invest_BankWealth_CNY', 'Outflow_Invest_Private_Equity_Investment_A_CNY', 'Outflow_Invest_Fund_TT_CNY', 'Outflow_Invest_Fund_Schwab_CNY', 'Outflow_Invest_Fund_Schwab_USD', 'Outflow_Invest_Gold_Paper_CNY', 'Outflow_Invest_GoldETF_CNY']
        }
        
        for date_val, row in df_clean.iterrows():
            snapshot_date = date_val.date()
            
            # Get FX Rate for this month
            fx_val = row.get('Ref_USD_FX_Rate')
            if pd.isna(fx_val):
                fx_rate = 7.0
            else:
                try:
                    fx_rate = float(fx_val)
                    if fx_rate == 0: fx_rate = 7.0
                except:
                    fx_rate = 7.0
            
            # Helper to sum fields
            def sum_fields(fields):
                total = 0.0
                for col in fields:
                    val = row.get(col, 0.0)
                    if pd.isna(val):
                        val = 0.0
                    try:
                        val = float(val)
                    except:
                        val = 0.0
                        
                    if col.endswith('_USD'):
                        val *= fx_rate
                    total += val
                return total

            # Compute Model Values
            data = {}
            for model_field, cols in FIELD_MAP.items():
                data[model_field] = sum_fields(cols)
                
            # Derived Totals
            data['total_income'] = data['salary_income'] + data['rsu_income'] + data['investment_income'] + data['other_income']
            
            # Total Expense (Excluding Investment Outflow)
            data['total_expense'] = (data['housing_expense'] + data['living_expense'] + 
                                   data['healthcare_expense'] + data['entertainment_expense'] + 
                                   data['other_expense'])
                                   
            data['net_savings'] = data['total_income'] - data['total_expense']
            
            if data['total_income'] > 0:
                data['savings_rate'] = (data['net_savings'] / data['total_income']) * 100.0
            else:
                data['savings_rate'] = 0.0
                
            # Upsert
            existing = session.query(MonthlyFinancialSnapshot).filter_by(snapshot_date=snapshot_date).first()
            if existing:
                # Update fields
                existing.salary_income = data['salary_income']
                existing.rsu_income = data['rsu_income']
                existing.investment_income = data['investment_income']
                existing.other_income = data['other_income']
                existing.total_income = data['total_income']
                
                existing.housing_expense = data['housing_expense']
                existing.living_expense = data['living_expense']
                existing.healthcare_expense = data['healthcare_expense']
                existing.entertainment_expense = data['entertainment_expense']
                existing.other_expense = data['other_expense']
                existing.investment_expense = data['investment_expense']
                existing.total_expense = data['total_expense']
                
                existing.net_savings = data['net_savings']
                existing.savings_rate = data['savings_rate']
                updated += 1
            else:
                new_snap = MonthlyFinancialSnapshot(
                    snapshot_date=snapshot_date,
                    **data,
                    currency='CNY'
                )
                session.add(new_snap)
                count += 1
                
        session.commit()
        logger.info(f"✅ Synced Monthly Data: Added {count}, Updated {updated} records.")
        return True
        
    except Exception as e:
        session.rollback()
        logger.error(f"Monthly Sync Failed: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False
    finally:
        session.close()
