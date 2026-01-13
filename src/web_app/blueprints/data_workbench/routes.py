from flask import render_template, request, jsonify, current_app
from werkzeug.utils import secure_filename
import pandas as pd
import os
import uuid
from datetime import datetime
from sqlalchemy import or_
from src.database import get_session, StagingTransaction, Transaction, Asset, ImportHistory, ImportSession
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

@data_workbench_bp.route('/wizard')
def wizard():
    """
    Render the multi-step import wizard.
    """
    # Create a new session ID if one doesn't exist?
    # For now, just render the template. JS will handle session creation.
    return render_template('data_workbench/wizard.html')

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


# =============================================================================
# IMPORT WIZARD API ENDPOINTS (Multi-step flow)
# =============================================================================

@data_workbench_bp.route('/api/imports', methods=['POST'])
def create_import_session():
    """
    Step 1: Create a new import wizard session.
    
    POST /workbench/api/imports
    Body: { "type": "transactions" | "holdings" | "accounts" }
    """
    data = request.json or {}
    import_type = data.get('type', 'transactions')
    
    if import_type not in ('transactions', 'holdings', 'accounts'):
        return jsonify({'error': 'Invalid import type. Use: transactions, holdings, accounts'}), 400
    
    session_db = get_session()
    try:
        # Create new import session
        import_session = ImportSession(
            id=str(uuid.uuid4()),
            import_type=import_type,
            current_step=1,
            status='pending'
        )
        session_db.add(import_session)
        session_db.commit()
        
        logger.info(f"Created import session {import_session.id} for type {import_type}")
        
        return jsonify({
            'import_id': import_session.id,
            'type': import_type,
            'step': 1,
            'status': 'pending'
        }), 201
    except Exception as e:
        session_db.rollback()
        logger.error(f"Error creating import session: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session_db.close()


@data_workbench_bp.route('/api/imports/<import_id>', methods=['GET'])
def get_import_session(import_id):
    """Get current state of an import session."""
    session_db = get_session()
    try:
        import_session = session_db.query(ImportSession).filter_by(id=import_id).first()
        if not import_session:
            return jsonify({'error': 'Import session not found'}), 404
        
        return jsonify({
            'import_id': import_session.id,
            'type': import_session.import_type,
            'step': import_session.current_step,
            'status': import_session.status,
            'filename': import_session.filename,
            'detected_headers': import_session.detected_headers,
            'column_mapping': import_session.column_mapping,
            'total_rows': import_session.total_rows,
            'valid_rows': import_session.valid_rows,
            'error_rows': import_session.error_rows,
            'created_at': import_session.created_at.isoformat() if import_session.created_at else None
        })
    finally:
        session_db.close()


@data_workbench_bp.route('/api/imports/<import_id>/upload', methods=['POST'])
def wizard_upload_file(import_id):
    """
    Step 2: Upload file and get preview with auto-detected column mapping.
    
    POST /workbench/api/imports/{id}/upload
    Body: multipart form with 'file'
    """
    session_db = get_session()
    try:
        # Find import session
        import_session = session_db.query(ImportSession).filter_by(id=import_id).first()
        if not import_session:
            return jsonify({'error': 'Import session not found'}), 404
        
        if import_session.status == 'completed':
            return jsonify({'error': 'Import session already completed'}), 400
        
        # Validate file
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Use: xlsx, xls, csv'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        project_root = os.path.abspath(os.path.join(current_app.root_path, '..', '..'))
        upload_folder = os.path.join(project_root, 'data', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, f"{import_id}_{filename}")
        file.save(filepath)
        
        logger.info(f"Wizard: File saved to {filepath}")
        
        # Parse file
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            # Read first sheet only
            df = pd.read_excel(filepath, sheet_name=0)
        
        df.columns = [str(c).strip() for c in df.columns]
        headers = df.columns.tolist()
        
        # Get preview (first 5 rows)
        preview_rows = df.head(5).fillna('').to_dict('records')
        
        # Auto-detect column mapping
        detected_mapping = detect_column_mapping(headers)
        
        # Update session
        import_session.filename = filename
        import_session.file_path = filepath
        import_session.detected_headers = headers
        import_session.preview_data = preview_rows
        import_session.total_rows = len(df)
        import_session.column_mapping = detected_mapping
        import_session.current_step = 2
        import_session.status = 'processing'
        
        session_db.commit()
        
        return jsonify({
            'import_id': import_id,
            'step': 2,
            'filename': filename,
            'headers': headers,
            'total_rows': len(df),
            'preview': preview_rows,
            'detected_mapping': detected_mapping
        })
    except Exception as e:
        session_db.rollback()
        logger.error(f"Error in wizard upload: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session_db.close()


@data_workbench_bp.route('/api/imports/<import_id>/configure', methods=['POST'])
def wizard_configure(import_id):
    """
    Step 3: Configure column mapping and formats.
    
    POST /workbench/api/imports/{id}/configure
    Body: {
        "column_mapping": { "date": "Trade Date", "amount": "Total", ... },
        "date_format": "MM/DD/YYYY",
        "number_format": "us"
    }
    """
    session_db = get_session()
    try:
        import_session = session_db.query(ImportSession).filter_by(id=import_id).first()
        if not import_session:
            return jsonify({'error': 'Import session not found'}), 404
        
        data = request.json or {}
        
        # Update configuration
        if 'column_mapping' in data:
            import_session.column_mapping = data['column_mapping']
        if 'date_format' in data:
            import_session.date_format = data['date_format']
        if 'number_format' in data:
            import_session.number_format = data['number_format']
        
        import_session.current_step = 3
        session_db.commit()
        
        return jsonify({
            'import_id': import_id,
            'step': 3,
            'status': 'configured',
            'column_mapping': import_session.column_mapping
        })
    except Exception as e:
        session_db.rollback()
        logger.error(f"Error in wizard configure: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session_db.close()


@data_workbench_bp.route('/api/imports/<import_id>/validate', methods=['POST'])
def wizard_validate(import_id):
    """
    Step 4: Validate data and identify errors.
    
    POST /workbench/api/imports/{id}/validate
    """
    session_db = get_session()
    try:
        import_session = session_db.query(ImportSession).filter_by(id=import_id).first()
        if not import_session:
            return jsonify({'error': 'Import session not found'}), 404
        
        if not import_session.file_path or not os.path.exists(import_session.file_path):
            return jsonify({'error': 'No file uploaded'}), 400
        
        # Re-parse file
        filepath = import_session.file_path
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath, sheet_name=0)
        
        df.columns = [str(c).strip() for c in df.columns]
        column_map = import_session.column_mapping or {}
        
        valid_count = 0
        error_count = 0
        errors = []
        
        preview_rows = []
        
        for idx, row in df.iterrows():
            row_errors = []
            
            # Validate date
            date_col = column_map.get('date')
            if date_col and date_col in row:
                date_val = parse_flexible_date(row.get(date_col))
                if not date_val:
                    row_errors.append({'field': 'date', 'message': 'Invalid date format'})
            else:
                row_errors.append({'field': 'date', 'message': 'Missing date'})
            
            # Validate asset_id
            asset_col = column_map.get('asset_id')
            if asset_col and asset_col in row:
                asset_id = normalize_asset_id(row.get(asset_col))
                if asset_id:
                    # Check if asset exists
                    asset = session_db.query(Asset).filter_by(asset_id=asset_id).first()
                    if not asset:
                        row_errors.append({'field': 'asset_id', 'message': f'Unknown asset: {asset_id}'})
            
            if row_errors:
                error_count += 1
                errors.append({
                    'row': idx + 1,
                    'errors': row_errors
                })
            else:
                valid_count += 1
            
            if len(preview_rows) < 100:
                row_data = {k: str(row.get(v, '')) for k, v in column_map.items() if v}
                preview_rows.append({
                    'index': idx + 1,
                    'data': row_data,
                    'errors': [e['message'] for e in row_errors],
                    'valid': not bool(row_errors)
                })
        
        # Update session
        import_session.valid_rows = valid_count
        import_session.error_rows = error_count
        import_session.validation_errors = errors
        import_session.current_step = 4
        
        session_db.commit()
        
        return jsonify({
            'import_id': import_id,
            'step': 4,
            'total_rows': len(df),
            'valid_rows': valid_count,
            'error_rows': error_count,
            'errors': errors[:50],  # Limit errors returned in summary
            'preview_rows': preview_rows # Limit to 100 for table display
        })
    except Exception as e:
        session_db.rollback()
        logger.error(f"Error in wizard validate: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session_db.close()


@data_workbench_bp.route('/api/imports/<import_id>/update-row', methods=['POST'])
def wizard_update_row(import_id):
    """
    Update a single cell in the uploaded file (for fixing errors).
    POST /workbench/api/imports/{id}/update-row
    Body: { "row_index": 1, "field": "amount", "value": "100.00" }
    """
    session_db = get_session()
    try:
        data = request.json
        row_idx = int(data.get('row_index')) - 1 # 1-based to 0-based
        field = data.get('field') # mapped field name (e.g. 'amount')
        value = data.get('value')
        
        import_session = session_db.query(ImportSession).filter_by(id=import_id).first()
        if not import_session or not import_session.file_path:
            return jsonify({'error': 'Session not found'}), 404
            
        # Load File
        filepath = import_session.file_path
        is_csv = filepath.endswith('.csv')
        
        if is_csv:
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
            
        # Map logical field to actual column name
        col_map = import_session.column_mapping or {}
        actual_col = col_map.get(field)
        
        if not actual_col:
            return jsonify({'error': f'Field {field} is not mapped'}), 400
            
        if actual_col not in df.columns:
             return jsonify({'error': f'Column {actual_col} not found in file'}), 400
             
        # Update Value
        df.at[row_idx, actual_col] = value
        
        # Save back to file
        if is_csv:
            df.to_csv(filepath, index=False)
        else:
            df.to_excel(filepath, index=False)
            
        # Re-validate this specific row (lightweight validation)
        row = df.iloc[row_idx]
        row_errors = []
        
        # Basic validation reuse
        if field == 'date':
             val = parse_flexible_date(value)
             if not val: row_errors.append('Invalid date format')
        elif field == 'asset_id':
             aid = normalize_asset_id(value)
             asset = session_db.query(Asset).filter_by(asset_id=aid).first()
             if not asset: row_errors.append(f'Unknown asset: {aid}')
             
        return jsonify({
            'success': True, 
            'row_index': data.get('row_index'),
            'new_errors': row_errors
        })

    except Exception as e:
        logger.error(f"Error updating row: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session_db.close()


@data_workbench_bp.route('/api/imports/<import_id>/publish', methods=['POST'])
def wizard_publish(import_id):
    """
    Step 5: Publish valid rows to production.
    
    POST /workbench/api/imports/{id}/publish
    """
    session_db = get_session()
    try:
        import_session = session_db.query(ImportSession).filter_by(id=import_id).first()
        if not import_session:
            return jsonify({'error': 'Import session not found'}), 404
        
        if import_session.status == 'completed':
            return jsonify({'error': 'Import already completed'}), 400
        
        if not import_session.file_path or not os.path.exists(import_session.file_path):
            return jsonify({'error': 'No file to publish'}), 400
        
        # Re-parse and import valid rows
        filepath = import_session.file_path
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath, sheet_name=0)
        
        df.columns = [str(c).strip() for c in df.columns]
        column_map = import_session.column_mapping or {}
        
        batch_id = f"wizard_{import_id[:8]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        imported_count = 0
        
        for idx, row in df.iterrows():
            # Parse fields
            date_val = parse_flexible_date(row.get(column_map.get('date'))) if column_map.get('date') else None
            asset_id_val = normalize_asset_id(row.get(column_map.get('asset_id'))) if column_map.get('asset_id') else None
            
            if not date_val or not asset_id_val:
                continue  # Skip invalid rows
            
            # Check asset exists
            asset = session_db.query(Asset).filter_by(asset_id=asset_id_val).first()
            if not asset:
                continue
            
            # Get other fields
            raw_txn_type = row.get(column_map.get('transaction_type')) if column_map.get('transaction_type') else None
            transaction_type_val = normalize_transaction_type(raw_txn_type) or 'Buy'
            amount_val = clean_currency_value(row.get(column_map.get('amount'))) if column_map.get('amount') else None
            shares_val = clean_currency_value(row.get(column_map.get('shares'))) if column_map.get('shares') else None
            price_val = clean_currency_value(row.get(column_map.get('price'))) if column_map.get('price') else None
            
            # Create Transaction
            txn = Transaction(
                transaction_id=f"txn_{batch_id}_{idx}",
                date=date_val.date() if hasattr(date_val, 'date') else date_val,
                asset_id=asset_id_val,
                asset_name=asset.asset_name,
                transaction_type=transaction_type_val,
                shares=shares_val,
                price=price_val,
                amount=amount_val,
                currency='CNY',
                source=import_session.filename,
                created_by='import_wizard'
            )
            session_db.add(txn)
            imported_count += 1
        
        # Update session
        import_session.batch_id = batch_id
        import_session.imported_count = imported_count
        import_session.current_step = 5
        import_session.status = 'completed'
        import_session.completed_at = datetime.utcnow()
        
        # Create ImportHistory record
        import_record = ImportHistory(
            batch_id=batch_id,
            filename=import_session.filename,
            total_rows=import_session.total_rows or 0,
            valid_rows=import_session.valid_rows or 0,
            error_rows=import_session.error_rows or 0,
            promoted_rows=imported_count,
            status='promoted',
            promoted_at=datetime.utcnow()
        )
        session_db.add(import_record)
        
        session_db.commit()
        
        logger.info(f"Wizard import completed: {imported_count} records imported")
        
        return jsonify({
            'import_id': import_id,
            'step': 5,
            'status': 'completed',
            'imported_count': imported_count,
            'batch_id': batch_id
        })
    except Exception as e:
        session_db.rollback()
        logger.error(f"Error in wizard publish: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session_db.close()


@data_workbench_bp.route('/api/imports/<import_id>', methods=['DELETE'])
def cancel_import_session(import_id):
    """Cancel/abandon an import session."""
    session_db = get_session()
    try:
        import_session = session_db.query(ImportSession).filter_by(id=import_id).first()
        if not import_session:
            return jsonify({'error': 'Import session not found'}), 404
        
        # Delete uploaded file if exists
        if import_session.file_path and os.path.exists(import_session.file_path):
            os.remove(import_session.file_path)
        
        # Mark as abandoned
        import_session.status = 'abandoned'
        session_db.commit()
        
        return jsonify({'message': 'Import session cancelled', 'import_id': import_id})
    except Exception as e:
        session_db.rollback()
        logger.error(f"Error cancelling import: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session_db.close()

