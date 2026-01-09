import sys
import os
import pandas as pd
import logging
from datetime import datetime

# Ensure project root is in path
project_root = os.getcwd()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.database import get_session
from src.database.models import Holding, Asset
from src.data_manager.manager import DataManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def allow_multiple_snapshots(df):
    """
    Given a dataframe of all history, yields (date, sub_df) for each snapshot.
    """
    # Reset index to ensure fields are columns
    df_reset = df.reset_index()
    
    # Identify Date column
    date_col = 'Snapshot_Date' if 'Snapshot_Date' in df_reset.columns else 'Date'
    if date_col not in df_reset.columns:
        # Fallback search
        for col in df_reset.columns:
            if 'date' in col.lower():
                date_col = col
                break
    
    if date_col not in df_reset.columns:
        raise ValueError(f"Could not find date column in dataframe. Columns: {df_reset.columns}")
        
    logger.info(f"Grouping by date column: {date_col}")
    
    # Ensure date column is datetime
    df_reset[date_col] = pd.to_datetime(df_reset[date_col])
    
    for date_val, group in df_reset.groupby(date_col):
        yield date_val, group

def populate_history():
    print("\n=== POPULATING DATABASE HISTORY FROM EXCEL SNAPSHOTS ===\n")
    
    # 1. Load History from Excel Pipeline
    logger.info("Initializing DataManager in EXCEL mode to read full history...")
    dm = DataManager(config_path="config/settings.yaml", force_mode='excel')
    
    logger.info("Fetching full historical holdings...")
    full_history = dm.get_holdings(latest_only=False)
    
    if full_history is None or full_history.empty:
        logger.error("❌ No history found from Excel pipeline!")
        return

    record_count = len(full_history)
    logger.info(f"✅ Loaded {record_count} total historical records.")
    
    # 2. Iterate and Upsert
    session = get_session()
    
    # Pre-fetch existing assets to prevent FK errors
    existing_assets = {a.asset_id for a in session.query(Asset.asset_id).all()}
    logger.info(f"Loaded {len(existing_assets)} existing assets from DB.")
    
    total_added = 0
    total_updated = 0
    snapshots_processed = 0
    new_assets_count = 0
    
    try:
        for snapshot_date, group in allow_multiple_snapshots(full_history):
            # Normalize date
            if hasattr(snapshot_date, 'date'):
                snapshot_date = snapshot_date.date()
            else:
                 snapshot_date = pd.to_datetime(snapshot_date).date()
            
            snapshots_processed += 1
            # logger.info(f"Processing snapshot: {snapshot_date} ({len(group)} records)")
            
            # Fetch existing for this date to support upsert
            existing_holdings = session.query(Holding).filter_by(snapshot_date=snapshot_date).all()
            existing_map = {h.asset_id: h for h in existing_holdings}
            processed_in_this_batch = set()
            
            for _, row in group.iterrows():
                asset_id = row.get('Asset_ID')
                if not asset_id: continue
                asset_id = str(asset_id)
                asset_name = str(row.get('Asset_Name', asset_id))
                
                # Deduplication within batch
                if asset_id in processed_in_this_batch:
                    continue
                processed_in_this_batch.add(asset_id)
                
                # Check existance of Asset
                if asset_id not in existing_assets:
                    # Create missing asset
                    new_asset = Asset(
                        asset_id=asset_id,
                        asset_name=asset_name,
                        asset_type='Unknown' # Default
                    )
                    session.add(new_asset)
                    existing_assets.add(asset_id)
                    new_assets_count += 1
                
                def safe_float(val):
                    try:
                        return float(val) if pd.notnull(val) else 0.0
                    except:
                        return 0.0
                        
                shares = safe_float(row.get('Quantity'))
                price = safe_float(row.get('Market_Price_Unit'))
                market_val = safe_float(row.get('Market_Value_CNY'))
                cost_basis = safe_float(row.get('Cost_Basis_CNY'))
                currency = str(row.get('Currency', 'CNY'))
                
                if asset_id in existing_map:
                    # Update
                    h = existing_map[asset_id]
                    h.shares = shares
                    h.current_price = price
                    h.market_value = market_val
                    h.cost_basis = cost_basis
                    h.currency = currency
                    total_updated += 1
                else:
                    # Insert
                    new_h = Holding(
                        snapshot_date=snapshot_date,
                        asset_id=asset_id,
                        asset_name=asset_name,
                        shares=shares,
                        current_price=price,
                        market_value=market_val,
                        cost_basis=cost_basis,
                        currency=currency,
                        unrealized_pnl=market_val - cost_basis
                    )
                    session.add(new_h)
                    total_added += 1
            
            if snapshots_processed % 10 == 0:
                print(f"Processed {snapshots_processed} snapshots...")
                session.commit() # Commit periodically
            
        session.commit()
        print(f"\n✅ DONE! Processed {snapshots_processed} snapshots.")
        print(f"   Added {new_assets_count} new Assets to master table.")
        print(f"   Added: {total_added} holding records")
        print(f"   Updated: {total_updated} holding records")
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Failed to populate history: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    populate_history()
