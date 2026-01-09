from flask import render_template, request, jsonify, current_app
from werkzeug.utils import secure_filename
import pandas as pd
import os
from datetime import datetime
from sqlalchemy import or_
from src.database import get_session, StagingTransaction, Transaction, Asset, ImportHistory
from . import data_workbench_bp
from .data_mapper import (
    detect_column_mapping, normalize_transaction_type, 
    clean_currency_value, parse_flexible_date, normalize_asset_id,
    detect_file_source, detect_currency
)

ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

import logging

logger = logging.getLogger(__name__)

@data_workbench_bp.route('/')
def index():
    return render_template('data_workbench/index.html')

@data_workbench_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Save to a temporary location outside the source tree
        # Project root is two levels up from web_app blueprints
        project_root = os.path.abspath(os.path.join(current_app.root_path, '..', '..'))
        upload_folder = os.path.join(project_root, 'data', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        logger.info(f"File saved to {filepath}")
        
        try:
            # Process the file
            result = process_upload(filepath, filename)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

def process_upload(filepath, filename):
    session = get_session()
    try:
        dfs = {}
        if filepath.endswith('.csv'):
            dfs['default'] = pd.read_csv(filepath)
        else:
            # Read all sheets
            dfs = pd.read_excel(filepath, sheet_name=None)
            
        logger.info(f"Read file {filename} with {len(dfs)} sheets: {list(dfs.keys())}")
        
        # Find the best sheet to process
        target_df = None
        detected_source = 'unknown'
        
        # Priority: Check for known sources in all sheets
        for sheet_name, df in dfs.items():
            # Basic normalization of columns
            df.columns = [str(c).strip() for c in df.columns]
            
            source = detect_file_source(df)
            logger.info(f"Sheet '{sheet_name}' detected as: {source}")
            
            if source != 'unknown':
                # If we found a valid source, use this sheet
                # Special handling for Chinese Funds: prefer sheets with transaction data
                if source == 'chinese_fund':
                    if '业务类型' in df.columns or 'Transaction_Type' in df.columns:
                        target_df = df
                        detected_source = source
                        break # Found a good transaction sheet
                    elif target_df is None:
                        # Keep as backup if we don't find a better one
                        target_df = df
                        detected_source = source
                # Special handling for Gold: prefer sheets with transaction data
                elif source == 'gold':
                    if '交易类型' in df.columns or 'Transaction_Type' in df.columns:
                        target_df = df
                        detected_source = source
                        break # Found a good transaction sheet
                    elif target_df is None:
                        target_df = df
                        detected_source = source
                elif target_df is None:
                    target_df = df
                    detected_source = source
        
        # If no known source found, use the first sheet (or 'default' for CSV)
        if target_df is None:
            first_sheet = list(dfs.keys())[0]
            target_df = dfs[first_sheet]
            target_df.columns = [str(c).strip() for c in target_df.columns]
            detected_source = detect_file_source(target_df)
            logger.info(f"No specific source matched. Using first sheet '{first_sheet}' as {detected_source}")

        df = target_df
        file_source = detected_source
        
        logger.info(f"Processing sheet with shape: {df.shape}, Source: {file_source}")
        logger.info(f"Columns: {df.columns.tolist()}")
        
        # Auto-detect column mapping
        column_map = detect_column_mapping(df.columns.tolist())
        logger.info(f"Column mapping: {column_map}")
        
        # Detect currency
        detected_currency = detect_currency(file_source, df, column_map)
        logger.info(f"Detected currency: {detected_currency}")
        
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        count = 0
        valid_count = 0
        error_count = 0
        skipped_count = 0
        
        for idx, row in df.iterrows():
            # Extract values using smart mapper
            date_val = parse_flexible_date(row.get(column_map.get('date'))) if 'date' in column_map else None
            asset_id_val = normalize_asset_id(row.get(column_map.get('asset_id'))) if 'asset_id' in column_map else None
            asset_name_val = str(row.get(column_map.get('asset_name'))).strip() if 'asset_name' in column_map and pd.notna(row.get(column_map.get('asset_name'))) else None
            
            # Get and normalize transaction type
            raw_txn_type = row.get(column_map.get('transaction_type')) if 'transaction_type' in column_map else None
            transaction_type_val = normalize_transaction_type(raw_txn_type)
            
            # Skip non-investment transactions (transfers, etc.)
            if transaction_type_val is None:
                skipped_count += 1
                logger.debug(f"Skipped row {idx + 1}: non-investment transaction ({raw_txn_type})")
                continue
            
            # Extract numeric values with cleaning
            amount_val = clean_currency_value(row.get(column_map.get('amount'))) if 'amount' in column_map else None
            shares_val = clean_currency_value(row.get(column_map.get('shares'))) if 'shares' in column_map else None
            price_val = clean_currency_value(row.get(column_map.get('price'))) if 'price' in column_map else None
            fees_val = clean_currency_value(row.get(column_map.get('fees'))) if 'fees' in column_map else None
            
            # Create StagingTransaction
            st = StagingTransaction(
                batch_id=batch_id,
                row_number=idx + 1,
                status='PENDING',
                raw_data=row.to_json(),
                date=date_val.date() if date_val else None,
                asset_id=asset_id_val,
                asset_name=asset_name_val,
                transaction_type=transaction_type_val,
                amount=amount_val,
                shares=shares_val,
                price=price_val,
                currency=detected_currency,
                source=filename
            )
            
            # Validation
            errors = []
            if not st.date:
                errors.append("Missing Date")
            if not st.asset_id:
                errors.append("Missing Asset ID")
            
            if errors:
                st.status = 'ERROR'
                st.validation_errors = errors
                error_count += 1
            else:
                # Check if asset exists
                asset = session.query(Asset).filter_by(asset_id=st.asset_id).first()
                if not asset:
                    st.status = 'ERROR'
                    st.validation_errors = ["Unknown Asset ID"]
                    error_count += 1
                else:
                    st.status = 'VALID'
                    valid_count += 1
            
            session.add(st)
            count += 1
        
        logger.info(f"Processed {count} rows, skipped {skipped_count} non-investment transactions")
        
        # Create ImportHistory record
        file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        import_record = ImportHistory(
            batch_id=batch_id,
            filename=filename,
            file_size=file_size,
            total_rows=count,
            valid_rows=valid_count,
            error_rows=error_count,
            status='uploaded'
        )
        session.add(import_record)
        
        session.commit()
        logger.info(f"Committed {count} records to staging and created import history")
        
        # Return detailed metadata for UI display
        return {
            'message': f'File processed successfully. {count} records imported.',
            'total_rows': count,
            'valid_rows': valid_count,
            'error_rows': error_count,
            'skipped_rows': skipped_count,
            'file_source': file_source,
            'detected_currency': detected_currency,
            'column_mapping': column_map,
            'batch_id': batch_id
        }
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error in process_upload: {e}")
        raise e
    finally:
        session.close()

@data_workbench_bp.route('/api/staging-data')
def get_staging_data():
    session = get_session()
    try:
        staging_txns = session.query(StagingTransaction).all()
        data = []
        for txn in staging_txns:
            data.append({
                'id': txn.id,
                'batch_id': txn.batch_id,
                'row_number': txn.row_number,
                'status': txn.status,
                'validation_errors': txn.validation_errors,
                'date': txn.date.isoformat() if txn.date else None,
                'asset_id': txn.asset_id,
                'asset_name': txn.asset_name,
                'transaction_type': txn.transaction_type,
                'amount': float(txn.amount) if txn.amount else None,
                'shares': float(txn.shares) if txn.shares else None,
                'price': float(txn.price) if txn.price else None,
                'currency': txn.currency,
                'source': txn.source
            })
        return jsonify(data)
    finally:
        session.close()

@data_workbench_bp.route('/api/promote', methods=['POST'])
def promote_data():
    session = get_session()
    try:
        # Get all VALID records
        valid_records = session.query(StagingTransaction).filter_by(status='VALID').all()
        
        promoted_count = 0
        for record in valid_records:
            # Create Transaction
            txn = Transaction(
                transaction_id=f"txn_{record.batch_id}_{record.row_number}", # Simple ID generation
                date=record.date,
                asset_id=record.asset_id,
                asset_name=record.asset_name,
                transaction_type=record.transaction_type,
                shares=record.shares,
                price=record.price,
                amount=record.amount,
                currency=record.currency,
                source=record.source,
                created_by='data_workbench'
            )
            session.add(txn)
            
            # Update Staging record
            record.status = 'PROMOTED'
            promoted_count += 1
            
        # Update ImportHistory records for affected batches
        if promoted_count > 0:
            # Get unique batch_ids from promoted records
            batch_ids = set(r.batch_id for r in valid_records)
            for batch_id in batch_ids:
                import_record = session.query(ImportHistory).filter_by(batch_id=batch_id).first()
                if import_record:
                    # Count how many from this batch were promoted
                    batch_promoted_count = sum(1 for r in valid_records if r.batch_id == batch_id)
                    import_record.promoted_rows = batch_promoted_count
                    import_record.promoted_at = datetime.utcnow()
                    import_record.status = 'promoted'
            
        session.commit()
        return jsonify({'message': f'Successfully promoted {promoted_count} records'})
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@data_workbench_bp.route('/api/clear', methods=['POST'])
def clear_staging():
    session = get_session()
    try:
        # Get all batch_ids before clearing
        staging_records = session.query(StagingTransaction).all()
        batch_ids = set(r.batch_id for r in staging_records)
        
        # Update ImportHistory for all batches
        for batch_id in batch_ids:
            import_record = session.query(ImportHistory).filter_by(batch_id=batch_id).first()
            if import_record:
                import_record.status = 'cleared'
                import_record.cleared_at = datetime.utcnow()
        
        # Clear staging transactions
        session.query(StagingTransaction).delete()
        session.commit()
        return jsonify({'message': 'Staging area cleared'})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@data_workbench_bp.route('/api/search-assets', methods=['GET'])
def search_assets():
    """Search for assets by name or ID (for mapping unknown assets)"""
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify([])
    
    session = get_session()
    try:
        # Search by asset name or asset_id (case-insensitive)
        assets = session.query(Asset).filter(
            or_(
                Asset.asset_name.ilike(f'%{query}%'),
                Asset.asset_id.ilike(f'%{query}%')
            )
        ).limit(20).all()
        
        results = [{
            'asset_id': asset.asset_id,
            'asset_name': asset.asset_name,
            'asset_type': asset.asset_type,
            'asset_class': asset.asset_class
        } for asset in assets]
        
        logger.info(f"Search for '{query}' returned {len(results)} results")
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error searching assets: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@data_workbench_bp.route('/api/resolve-error', methods=['POST'])
def resolve_error():
    """Resolve a staging error by mapping to an existing asset"""
    data = request.json
    staging_id = data.get('staging_id')
    asset_id = data.get('asset_id')
    
    if not staging_id or not asset_id:
        return jsonify({'error': 'Missing required fields'}), 400
    
    session = get_session()
    try:
        # Verify asset exists
        asset = session.query(Asset).filter_by(asset_id=asset_id).first()
        if not asset:
            return jsonify({'error': 'Asset not found'}), 404
        
        # Update staging transaction
        staging_txn = session.query(StagingTransaction).filter_by(id=staging_id).first()
        if not staging_txn:
            return jsonify({'error': 'Staging transaction not found'}), 404
        
        staging_txn.asset_id = asset_id
        staging_txn.asset_name = asset.asset_name
        staging_txn.status = 'VALID'
        staging_txn.validation_errors = []
        
        session.commit()
        
        logger.info(f"Resolved staging ID {staging_id} with asset {asset_id}")
        return jsonify({
            'message': 'Error resolved successfully',
            'staging_id': staging_id,
            'asset_id': asset_id
        })
    except Exception as e:
        session.rollback()
        logger.error(f"Error resolving staging error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@data_workbench_bp.route('/api/create-asset', methods=['POST'])
def create_asset():
    """Create a new asset and resolve staging error"""
    data = request.json
    staging_id_input = data.get('staging_id')
    asset_name = data.get('asset_name', '').strip()
    asset_type = data.get('asset_type', 'Other').strip()
    asset_class = data.get('asset_class', '').strip()
    
    if not staging_id_input or not asset_name:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Handle staging_id as list or single value
    staging_ids = staging_id_input if isinstance(staging_id_input, list) else [staging_id_input]
    
    session = get_session()
    try:
        # Generate asset_id from name
        asset_id = asset_name.replace(' ', '_').replace('.', '')
        
        # Check if asset already exists
        existing = session.query(Asset).filter_by(asset_id=asset_id).first()
        if existing:
            # If asset exists, we can still proceed to link the staging transactions to it
            pass
        else:
            # Create new asset
            new_asset = Asset(
                asset_id=asset_id,
                asset_name=asset_name,
                asset_type=asset_type,
                asset_class=asset_class if asset_class else None
            )
            session.add(new_asset)
        
        # Update staging transactions
        updated_count = 0
        for s_id in staging_ids:
            staging_txn = session.query(StagingTransaction).filter_by(id=s_id).first()
            if staging_txn:
                staging_txn.asset_id = asset_id
                staging_txn.asset_name = asset_name
                staging_txn.status = 'VALID'
                staging_txn.validation_errors = []
                updated_count += 1
        
        if updated_count == 0:
             return jsonify({'error': 'No staging transactions found'}), 404

        session.commit()
        
        logger.info(f"Created/Linked asset {asset_id} and resolved {updated_count} staging records")
        return jsonify({
            'message': 'Asset created and error resolved successfully',
            'staging_id': staging_ids[0], # Return first ID for compatibility
            'asset_id': asset_id,
            'updated_count': updated_count
        })
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating asset: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@data_workbench_bp.route('/api/batch-resolve-error', methods=['POST'])
def batch_resolve_error():
    """Resolve multiple staging errors by mapping to the same asset"""
    data = request.json
    staging_ids = data.get('staging_ids', [])
    asset_id = data.get('asset_id')
    
    if not staging_ids or not asset_id:
        return jsonify({'error': 'Missing required fields'}), 400
    
    if not isinstance(staging_ids, list):
        return jsonify({'error': 'staging_ids must be an array'}), 400
    
    session = get_session()
    try:
        # Verify asset exists
        asset = session.query(Asset).filter_by(asset_id=asset_id).first()
        if not asset:
            return jsonify({'error': 'Asset not found'}), 404
        
        # Update all staging transactions
        updated_count = 0
        for staging_id in staging_ids:
            staging_txn = session.query(StagingTransaction).filter_by(id=staging_id).first()
            if staging_txn and staging_txn.status == 'ERROR':
                staging_txn.asset_id = asset_id
                staging_txn.asset_name = asset.asset_name
                staging_txn.status = 'VALID'
                staging_txn.validation_errors = []
                updated_count += 1
        
        session.commit()
        
        logger.info(f"Batch resolved {updated_count} staging records with asset {asset_id}")
        return jsonify({
            'message': f'Successfully resolved {updated_count} records',
            'updated_count': updated_count,
            'asset_id': asset_id
        })
    except Exception as e:
        session.rollback()
        logger.error(f"Error in batch resolve: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@data_workbench_bp.route('/api/import-history', methods=['GET'])
def get_import_history():
    """Get all import history records for audit trail"""
    session = get_session()
    try:
        # Get all import history, ordered by most recent first
        history_records = session.query(ImportHistory).order_by(ImportHistory.uploaded_at.desc()).all()
        
        data = []
        for record in history_records:
            data.append({
                'id': record.id,
                'batch_id': record.batch_id,
                'filename': record.filename,
                'file_size': record.file_size,
                'total_rows': record.total_rows,
                'valid_rows': record.valid_rows,
                'error_rows': record.error_rows,
                'promoted_rows': record.promoted_rows,
                'status': record.status,
                'uploaded_at': record.uploaded_at.isoformat() if record.uploaded_at else None,
                'promoted_at': record.promoted_at.isoformat() if record.promoted_at else None,
                'cleared_at': record.cleared_at.isoformat() if record.cleared_at else None,
                'notes': record.notes
            })
        
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching import history: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()
