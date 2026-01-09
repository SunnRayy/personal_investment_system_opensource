"""
Core Validation Checks (MVP - Core 5)

Implements the five essential validation checks for data quality assurance:
1. Classification/Mapping Integrity
2. Structural Schema Integrity
3. Referential Consistency
4. Transaction Economic Sign Coherence
5. Portfolio Reconciliation
"""

from typing import List, Optional
import pandas as pd
import numpy as np
from ..reporter import ValidationIssue


def check_unmapped_assets(
    holdings_df: pd.DataFrame,
    taxonomy_manager: Optional[object] = None
) -> List[ValidationIssue]:
    """
    Check for unmapped or partially mapped assets in holdings.
    
    Args:
        holdings_df: DataFrame containing current holdings with Asset_ID and optional Sub_Class
        taxonomy_manager: Optional TaxonomyManager instance for lookup validation
        
    Returns:
        List of ValidationIssue objects for any unmapped assets found
    """
    issues = []
    
    if holdings_df is None or holdings_df.empty:
        issues.append(ValidationIssue(
            issue_id='MAPPING_NO_DATA',
            severity='WARNING',
            check_name='Classification/Mapping Integrity',
            description='No holdings data available for mapping validation',
            details={},
            suggestion='Ensure holdings data is loaded correctly'
        ))
        return issues
    
    # Null Sub_Class severity scaling by portfolio value impact
    if 'Sub_Class' in holdings_df.columns:
        null_subclass = holdings_df[holdings_df['Sub_Class'].isna()]
        if not null_subclass.empty:
            total_value = holdings_df['Market_Value_CNY'].sum() if 'Market_Value_CNY' in holdings_df.columns else None
            unmapped_value = null_subclass['Market_Value_CNY'].sum() if 'Market_Value_CNY' in null_subclass.columns else None
            ratio = (unmapped_value / total_value) if (total_value and total_value != 0 and unmapped_value is not None) else None
            if ratio is not None:
                if ratio > 0.25:
                    severity = 'CRITICAL'
                elif ratio > 0.05:
                    severity = 'MAJOR'
                else:
                    severity = 'WARNING'
            else:
                severity = 'MAJOR'
            asset_ids = null_subclass['Asset_ID'].tolist() if 'Asset_ID' in null_subclass.columns else []
            ratio_text = 'unknown ratio' if ratio is None else f'{ratio:.1%}'
            issues.append(ValidationIssue(
                issue_id='MAPPING_NULL_SUBCLASS',
                severity=severity,
                check_name='Classification/Mapping Integrity',
                description=f'Found {len(null_subclass)} assets with null Sub_Class ({ratio_text})',
                details={
                    'count': len(null_subclass),
                    'affected_assets': asset_ids[:10],
                    'unmapped_value': unmapped_value,
                    'total_value': total_value,
                    'value_ratio': None if ratio is None else f'{ratio:.2%}'
                },
                suggestion='Add taxonomy mapping or enrich classification pipeline'
            ))
    
    # If taxonomy_manager is provided, validate lookups
    if taxonomy_manager is not None and 'Asset_ID' in holdings_df.columns:
        failed_lookups = []
        for asset_id in holdings_df['Asset_ID'].unique():
            try:
                # Try to get asset classification
                if hasattr(taxonomy_manager, 'get_asset_class'):
                    result = taxonomy_manager.get_asset_class(asset_id)
                    if result is None or pd.isna(result):
                        failed_lookups.append(asset_id)
            except Exception:
                failed_lookups.append(asset_id)
        
        if failed_lookups:
            issues.append(ValidationIssue(
                issue_id='MAPPING_TAXONOMY_MISS',
                severity='CRITICAL',
                check_name='Classification/Mapping Integrity',
                description=f'Taxonomy lookup failed for {len(failed_lookups)} assets',
                details={
                    'count': len(failed_lookups),
                    'affected_assets': failed_lookups[:10]
                },
                suggestion='Add missing asset mappings to asset_taxonomy.yaml'
            ))
    
    return issues


def check_required_schema(
    holdings_df: Optional[pd.DataFrame] = None,
    transactions_df: Optional[pd.DataFrame] = None,
    balance_sheet_df: Optional[pd.DataFrame] = None
) -> List[ValidationIssue]:
    """
    Check that required columns exist and have proper data types.
    
    Validates schema requirements for holdings, transactions, and balance sheet data.
    Checks for missing columns and excessive null values in critical numeric fields.
    
    Args:
        holdings_df: Holdings DataFrame to validate
        transactions_df: Transactions DataFrame to validate
        balance_sheet_df: Balance sheet DataFrame to validate
        
    Returns:
        List of ValidationIssue objects for any schema violations
    """
    issues = []
    
    # Define REQUIRED columns per table (strict minimal set) – optional fields removed to reduce false positives
    # Rationale:
    #   - Sub_Class may legitimately be populated progressively (treat as mapping quality, not schema)
    #   - Category often absent in normalized balance sheet structures derived from wide asset columns
    #   - Date fields may reside in the index; treat index names as satisfying requirement
    required_cols = {
        'holdings': ['Asset_ID', 'Asset_Name', 'Market_Value_CNY'],
        # Date requirement handled flexibly (Date OR Transaction_Date OR index level named Date/Snapshot_Date)
        'transactions': ['Asset_ID', 'Transaction_Type', 'Amount_Net', 'Date'],
        # Balance sheet frequently wide with date index; no hard column requirements
        'balance_sheet': []
    }
    
    # Define critical numeric columns that shouldn't be >20% null
    numeric_cols = {
        'holdings': ['Market_Value_CNY', 'Quantity'],
        'transactions': ['Amount_Net', 'Quantity'],
        'balance_sheet': []
    }
    
    tables = {
        'holdings': holdings_df,
        'transactions': transactions_df,
        'balance_sheet': balance_sheet_df
    }
    
    for table_name, df in tables.items():
        if df is None or df.empty:
            issues.append(ValidationIssue(
                issue_id=f'SCHEMA_NO_{table_name.upper()}_DATA',
                severity='WARNING',
                check_name='Structural Schema Integrity',
                description=f'No {table_name} data available for schema validation',
                details={'table': table_name},
                suggestion=f'Ensure {table_name} data is loaded correctly'
            ))
            continue
        
        # Build available field universe (columns + index names)
        index_names = []
        if isinstance(df.index, pd.MultiIndex):
            index_names = [n for n in df.index.names if n]
        else:
            if df.index.name:
                index_names = [df.index.name]
        available_fields = set(df.columns.tolist() + index_names)

        missing_cols: List[str] = []
        for col in required_cols[table_name]:
            # Flexible date satisfaction logic
            if col == 'Date':
                date_aliases = {'Date', 'Transaction_Date', 'Snapshot_Date'}
                if not (date_aliases & available_fields):
                    missing_cols.append('Date')
                continue
            if col not in available_fields:
                missing_cols.append(col)

        if missing_cols:
            # Severity rules: CRITICAL only if core identifier/value columns missing
            if table_name == 'holdings':
                core_missing = any(m in {'Asset_ID', 'Market_Value_CNY'} for m in missing_cols)
                severity = 'CRITICAL' if core_missing else 'MAJOR'
            elif table_name == 'transactions':
                core_missing = any(m in {'Asset_ID', 'Transaction_Type', 'Amount_Net', 'Date'} for m in missing_cols)
                severity = 'CRITICAL' if core_missing else 'MAJOR'
            else:  # balance_sheet currently has no strict required columns
                severity = 'MAJOR'

            issues.append(ValidationIssue(
                issue_id='SCHEMA_MISSING_COL',
                severity=severity,
                check_name='Structural Schema Integrity',
                description=f'Missing required fields in {table_name} (considering columns + index levels)',
                details={
                    'table': table_name,
                    'missing_fields': missing_cols,
                    'available_columns': df.columns.tolist()[:20],
                    'index_names': index_names
                },
                suggestion='Add missing fields or ensure they appear either as columns or index levels (Date may reside in index).'
            ))
        
        # Check numeric column types and null ratios
        for col in numeric_cols[table_name]:
            if col not in df.columns:
                continue
            
            # Check if column is numeric
            if not pd.api.types.is_numeric_dtype(df[col]):
                non_numeric_count = df[col].apply(lambda x: not isinstance(x, (int, float, np.integer, np.floating)) and not pd.isna(x)).sum()
                if non_numeric_count > 0:
                    issues.append(ValidationIssue(
                        issue_id='SCHEMA_NON_NUMERIC',
                        severity='MAJOR',
                        check_name='Structural Schema Integrity',
                        description=f'Column {col} in {table_name} contains non-numeric values',
                        details={
                            'table': table_name,
                            'column': col,
                            'non_numeric_count': int(non_numeric_count),
                            'dtype': str(df[col].dtype)
                        },
                        suggestion=f'Convert {col} to numeric type or clean non-numeric values'
                    ))
            
            # Check null ratio
            null_ratio = df[col].isna().sum() / len(df)
            if null_ratio > 0.20:
                issues.append(ValidationIssue(
                    issue_id='SCHEMA_HIGH_NULL_RATIO',
                    severity='MAJOR',
                    check_name='Structural Schema Integrity',
                    description=f'Column {col} in {table_name} has high null ratio',
                    details={
                        'table': table_name,
                        'column': col,
                        'null_ratio': f'{null_ratio:.1%}',
                        'null_count': int(df[col].isna().sum()),
                        'total_rows': len(df)
                    },
                    suggestion=f'Investigate why {col} has >20% missing values'
                ))
    
    return issues


def check_referential_integrity(
    holdings_df: Optional[pd.DataFrame] = None,
    transactions_df: Optional[pd.DataFrame] = None
) -> List[ValidationIssue]:
    """
    Check referential consistency between holdings and transactions.
    
    Validates that:
    - Every Asset_ID in transactions appears in holdings (or is fully liquidated)
    - Holdings without transaction history are flagged as warnings
    
    Args:
        holdings_df: Holdings DataFrame with Asset_ID column
        transactions_df: Transactions DataFrame with Asset_ID column
        
    Returns:
        List of ValidationIssue objects for any referential inconsistencies
    """
    issues = []
    
    if holdings_df is None or holdings_df.empty:
        issues.append(ValidationIssue(
            issue_id='REFERENTIAL_NO_HOLDINGS',
            severity='WARNING',
            check_name='Referential Consistency',
            description='No holdings data available for referential integrity check',
            details={},
            suggestion='Ensure holdings data is loaded correctly'
        ))
        return issues
    
    if transactions_df is None or transactions_df.empty:
        issues.append(ValidationIssue(
            issue_id='REFERENTIAL_NO_TRANSACTIONS',
            severity='INFO',
            check_name='Referential Consistency',
            description='No transactions data available for referential integrity check',
            details={},
            suggestion='If this is a new portfolio, this is expected'
        ))
        return issues
    
    # Get unique Asset_IDs
    holdings_assets = set(holdings_df['Asset_ID'].unique()) if 'Asset_ID' in holdings_df.columns else set()
    txn_assets = set(transactions_df['Asset_ID'].unique()) if 'Asset_ID' in transactions_df.columns else set()
    
    if not holdings_assets or not txn_assets:
        return issues
    
    # Check for orphan transactions (in transactions but not in holdings)
    orphan_txn_assets = txn_assets - holdings_assets
    if orphan_txn_assets:
        # Check if these are fully liquidated (net position = 0)
        if 'Amount_Net' in transactions_df.columns:
            truly_orphan = []
            for asset in orphan_txn_assets:
                asset_txns = transactions_df[transactions_df['Asset_ID'] == asset]
                net_amount = asset_txns['Amount_Net'].sum()
                # If net amount is close to zero, it might be fully liquidated
                if abs(net_amount) > 0.01:  # Tolerance for floating point
                    truly_orphan.append(asset)
            
            if truly_orphan:
                issues.append(ValidationIssue(
                    issue_id='REFERENTIAL_ORPHAN_TXN',
                    severity='CRITICAL',
                    check_name='Referential Consistency',
                    description=f'Found {len(truly_orphan)} assets in transactions without holdings',
                    details={
                        'count': len(truly_orphan),
                        'orphan_assets': list(truly_orphan)[:10]
                    },
                    suggestion='These assets may need position reconciliation or data correction'
                ))
        else:
            issues.append(ValidationIssue(
                issue_id='REFERENTIAL_ORPHAN_TXN',
                severity='CRITICAL',
                check_name='Referential Consistency',
                description=f'Found {len(orphan_txn_assets)} assets in transactions without holdings',
                details={
                    'count': len(orphan_txn_assets),
                    'orphan_assets': list(orphan_txn_assets)[:10]
                },
                suggestion='Verify if these positions are liquidated or if data is missing'
            ))
    
    # Check for orphan holdings (in holdings but not in transactions)
    orphan_holdings = holdings_assets - txn_assets
    if orphan_holdings:
        # This is a WARNING - might be normal for newly added assets or synthetic holdings
        # Flag as suspicious if it's a large portion or uses generic naming patterns
        suspicious = [a for a in orphan_holdings if isinstance(a, str) and ('_' not in a or a.startswith('Asset_'))]
        
        if suspicious:
            issues.append(ValidationIssue(
                issue_id='REFERENTIAL_ORPHAN_HOLDING',
                severity='WARNING',
                check_name='Referential Consistency',
                description=f'Found {len(suspicious)} holdings without transaction history',
                details={
                    'count': len(suspicious),
                    'suspicious_holdings': list(suspicious)[:10],
                    'note': 'Assets with generic naming patterns or missing transaction history'
                },
                suggestion='Verify these are legitimate holdings and consider adding historical transactions'
            ))
    
    return issues


def check_transaction_signs(
    transactions_df: Optional[pd.DataFrame] = None
) -> List[ValidationIssue]:
    """
    Check transaction sign conventions.
    
    Validates that transaction types follow proper sign conventions:
    - Buys, Premium, Reinvest, Fees: Amount_Net < 0 (outflows)
    - Sells, Dividend, Interest: Amount_Net > 0 (inflows)
    
    Args:
        transactions_df: Transactions DataFrame with Transaction_Type and Amount_Net columns
        
    Returns:
        List of ValidationIssue objects for any sign convention violations
    """
    issues = []
    
    if transactions_df is None or transactions_df.empty:
        issues.append(ValidationIssue(
            issue_id='SIGN_NO_DATA',
            severity='INFO',
            check_name='Transaction Sign Coherence',
            description='No transactions data available for sign validation',
            details={},
            suggestion='If this is expected, no action needed'
        ))
        return issues
    
    if 'Transaction_Type' not in transactions_df.columns or 'Amount_Net' not in transactions_df.columns:
        issues.append(ValidationIssue(
            issue_id='SIGN_MISSING_COLUMNS',
            severity='WARNING',
            check_name='Transaction Sign Coherence',
            description='Required columns missing for sign validation',
            details={
                'available_columns': transactions_df.columns.tolist()[:20]
            },
            suggestion='Ensure transactions data includes Transaction_Type and Amount_Net'
        ))
        return issues
    
    # Define expected signs
    should_be_negative = ['Buy', 'Premium', 'Reinvest', 'Fee', 'Contribution', 'Transfer_Out']
    should_be_positive = ['Sell', 'Dividend', 'Interest', 'Distribution', 'Transfer_In']
    
    # Track violations
    violations = []
    
    for idx, row in transactions_df.iterrows():
        txn_type = row['Transaction_Type']
        amount = row['Amount_Net']
        
        # Skip if amount is null or zero
        if pd.isna(amount) or amount == 0:
            continue
        
        # Check negative convention
        if txn_type in should_be_negative and amount > 0:
            violations.append({
                'index': idx,
                'asset_id': row.get('Asset_ID', 'Unknown'),
                'type': txn_type,
                'amount': amount,
                'date': row.get('Date', 'Unknown'),
                'expected': 'negative'
            })
        
        # Check positive convention
        if txn_type in should_be_positive and amount < 0:
            violations.append({
                'index': idx,
                'asset_id': row.get('Asset_ID', 'Unknown'),
                'type': txn_type,
                'amount': amount,
                'date': row.get('Date', 'Unknown'),
                'expected': 'positive'
            })
    
    if violations:
        violation_ratio = len(violations) / len(transactions_df)
        
        # Determine severity based on ratio and absolute count
        if violation_ratio > 0.02 or len(violations) > 5:
            severity = 'CRITICAL'
        elif violation_ratio > 0.002:
            severity = 'MAJOR'
        else:
            severity = 'WARNING'
        
        issues.append(ValidationIssue(
            issue_id='SIGN_CONVENTION_VIOLATION',
            severity=severity,
            check_name='Transaction Sign Coherence',
            description=f'Found {len(violations)} transactions with incorrect sign conventions',
            details={
                'violation_count': len(violations),
                'total_transactions': len(transactions_df),
                'violation_ratio': f'{violation_ratio:.2%}',
                'sample_violations': violations[:5]
            },
            suggestion='Review and correct transaction signs to match convention: outflows negative, inflows positive'
        ))
    
    return issues


def check_portfolio_reconciliation(
    holdings_df: Optional[pd.DataFrame] = None,
    balance_sheet_df: Optional[pd.DataFrame] = None,
    tolerance: float = 0.015
) -> List[ValidationIssue]:
    """
    Check portfolio value reconciliation between holdings and balance sheet.
    
    Validates that the sum of current holdings market values approximately equals
    the investable assets total from the balance sheet.
    
    Args:
        holdings_df: Holdings DataFrame with Market_Value_CNY column
        balance_sheet_df: Balance sheet DataFrame with investable asset categories
        tolerance: Acceptable deviation percentage (default 1.5%)
        
    Returns:
        List of ValidationIssue objects for any reconciliation mismatches
    """
    issues = []
    
    if holdings_df is None or holdings_df.empty:
        issues.append(ValidationIssue(
            issue_id='RECON_NO_HOLDINGS',
            severity='WARNING',
            check_name='Portfolio Reconciliation',
            description='No holdings data available for reconciliation',
            details={},
            suggestion='Ensure holdings data is loaded correctly'
        ))
        return issues
    
    if balance_sheet_df is None or balance_sheet_df.empty:
        issues.append(ValidationIssue(
            issue_id='RECON_NO_BALANCE_SHEET',
            severity='INFO',
            check_name='Portfolio Reconciliation',
            description='No balance sheet data available for reconciliation',
            details={},
            suggestion='Balance sheet comparison skipped - not required for basic validation'
        ))
        return issues
    
    # Calculate total holdings value
    if 'Market_Value_CNY' not in holdings_df.columns:
        issues.append(ValidationIssue(
            issue_id='RECON_MISSING_MV_COLUMN',
            severity='WARNING',
            check_name='Portfolio Reconciliation',
            description='Market_Value_CNY column missing from holdings',
            details={
                'available_columns': holdings_df.columns.tolist()[:20]
            },
            suggestion='Ensure holdings data includes Market_Value_CNY column'
        ))
        return issues
    
    holdings_total = holdings_df['Market_Value_CNY'].sum()

    investable_categories = [
        'Stock', 'Bond', 'Fund', 'Cash', 'Commodity', 'Crypto',
        '股票', '债券', '基金', '现金', '商品', '加密货币'
    ]

    balance_sheet_total: Optional[float] = None

    # Heuristic 1: Category based
    if 'Category' in balance_sheet_df.columns:
        try:
            investable_rows = balance_sheet_df[
                balance_sheet_df['Category'].astype(str).str.contains(
                    '|'.join(investable_categories), case=False, na=False
                )
            ]
            value_cols = [
                col for col in balance_sheet_df.columns
                if ('value' in col.lower() or 'amount' in col.lower() or '金额' in col)
            ]
            if value_cols and not investable_rows.empty:
                balance_sheet_total = investable_rows[value_cols[0]].sum()
        except Exception:
            balance_sheet_total = None

    # Heuristic 2: Column prefixes (last row snapshot)
    if balance_sheet_total is None:
        candidate_cols = [
            c for c in balance_sheet_df.columns
            if c.startswith(('Asset_Invest_', 'Asset_Cash_', 'Asset_Deposit_', 'Asset_Fixed_'))
        ]
        
        # Filter out redundant calculated columns to avoid double-counting
        filtered_cols = []
        for c in candidate_cols:
            # Skip _FromUSD/_FromCNY columns (auto-generated by calculators)
            if '_FromUSD' in c or '_FromCNY' in c:
                continue
            # Skip Chase/Discover CNY columns (duplicates of USD columns)
            if c in ['Asset_Deposit_Chase_CNY', 'Asset_Deposit_Discover_CNY']:
                continue
            filtered_cols.append(c)
        
        if filtered_cols:
            try:
                last_row = balance_sheet_df.iloc[-1]
                numeric_values = []
                for c in filtered_cols:
                    val = last_row.get(c)
                    try:
                        val_f = float(val)
                        if not np.isnan(val_f) and abs(val_f) > 1e-9:
                            numeric_values.append(val_f)
                    except Exception:
                        continue
                if numeric_values:
                    balance_sheet_total = sum(numeric_values)
            except Exception:
                balance_sheet_total = None

    if balance_sheet_total is None or pd.isna(balance_sheet_total):
        issues.append(ValidationIssue(
            issue_id='RECON_CANNOT_EXTRACT_BS_TOTAL',
            severity='INFO',
            check_name='Portfolio Reconciliation',
            description='Could not extract investable assets total from balance sheet',
            details={
                'holdings_total': f'{holdings_total:,.2f}',
                'balance_sheet_structure': 'Unable to identify investable asset categories'
            },
            suggestion='Verify balance sheet structure matches expected format'
        ))
        return issues
    
    # Calculate deviation
    deviation = abs(holdings_total - balance_sheet_total)
    deviation_pct = deviation / balance_sheet_total if balance_sheet_total != 0 else float('inf')
    
    if deviation_pct > tolerance:
        severity = 'CRITICAL' if deviation_pct > 0.03 else 'MAJOR'
        
        issues.append(ValidationIssue(
            issue_id='RECON_VALUE_MISMATCH',
            severity=severity,
            check_name='Portfolio Reconciliation',
            description='Holdings total does not match balance sheet investable assets',
            details={
                'holdings_total': f'{holdings_total:,.2f}',
                'balance_sheet_total': f'{balance_sheet_total:,.2f}',
                'deviation': f'{deviation:,.2f}',
                'deviation_pct': f'{deviation_pct:.2%}',
                'tolerance': f'{tolerance:.2%}'
            },
            suggestion='Investigate discrepancy - check for missing holdings or data timing issues'
        ))
    
    return issues
