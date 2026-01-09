"""Data quality health checks for the Personal Investment System."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from src.database.connector import DatabaseConnector
from src.portfolio_lib.taxonomy_manager import TaxonomyManager


@dataclass
class CheckResult:
    """Structured result for a single data-quality check."""

    key: str
    title: str
    severity: str
    description: str
    items: List[Dict[str, Any]]


class DataQualityHealthCheck:
    """Runs portfolio data-quality checks used by the web dashboard."""

    def __init__(
        self,
        *,
        max_price_age_days: int = 5,
        zero_amount_threshold: float = 0.5,
        db_connector: Optional[DatabaseConnector] = None,
        taxonomy_manager: Optional[TaxonomyManager] = None,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.max_price_age_days = max_price_age_days
        self.zero_amount_threshold = zero_amount_threshold
        self.db = db_connector or DatabaseConnector()
        self.taxonomy_manager = taxonomy_manager or TaxonomyManager()

    def run_all_checks(self) -> Dict[str, Any]:
        """Execute all health checks and return a JSON-serializable payload."""
        holdings_latest = self._safe_dataframe(self.db.get_holdings(latest_only=True))
        holdings_history = self._safe_dataframe(self.db.get_holdings(latest_only=False))
        transactions = self._safe_dataframe(self.db.get_transactions())

        checks: List[Optional[CheckResult]] = [
            self._check_missing_prices(holdings_latest),
            self._check_snapshot_recency(holdings_history),
            self._check_classification_gaps(holdings_latest),
            self._check_transaction_anomalies(transactions),
        ]

        serialized_checks = [self._serialize_check(result) for result in checks if result]
        summary = self._build_summary(serialized_checks)

        return {
            'summary': summary,
            'checks': serialized_checks,
        }

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------
    def _check_missing_prices(self, holdings_df: pd.DataFrame) -> Optional[CheckResult]:
        if holdings_df.empty or 'Market_Price_Unit' not in holdings_df.columns:
            return None

        df = holdings_df.reset_index()
        mask = df['Market_Price_Unit'].isna() | (df['Market_Price_Unit'] <= 0)
        issues = df[mask]

        if issues.empty:
            return None

        items = [
            {
                'asset_id': str(row.get('Asset_ID')),
                'asset_name': row.get('Asset_Name'),
                'market_value': self._safe_float(row.get('Market_Value_CNY')),
                'snapshot_date': self._format_date(row.get('Date')),
            }
            for _, row in issues.head(50).iterrows()
        ]

        return CheckResult(
            key='missing_prices',
            title='Missing or Zero Prices',
            severity='high',
            description='Holdings that do not have a current market price recorded.',
            items=items,
        )

    def _check_snapshot_recency(self, holdings_df: pd.DataFrame) -> Optional[CheckResult]:
        if holdings_df.empty:
            return None

        index_names = list(getattr(holdings_df.index, 'names', []) or [])
        latest_date: Optional[pd.Timestamp] = None
        if 'Date' in index_names:
            latest_date = holdings_df.index.get_level_values('Date').max()
        elif 'Date' in holdings_df.columns:
            latest_date = pd.to_datetime(holdings_df['Date']).max()

        if latest_date is None:
            return None

        age_days = (datetime.utcnow().date() - latest_date.date()).days
        if age_days <= self.max_price_age_days:
            return None

        items = [
            {
                'last_snapshot_date': latest_date.date().isoformat(),
                'age_days': age_days,
                'max_allowed_days': self.max_price_age_days,
            }
        ]

        return CheckResult(
            key='stale_snapshot',
            title='Stale Snapshot Date',
            severity='medium',
            description='Latest holdings snapshot is older than the configured freshness window.',
            items=items,
        )

    def _check_classification_gaps(self, holdings_df: pd.DataFrame) -> Optional[CheckResult]:
        if holdings_df.empty:
            return None

        if 'Asset_Class' not in holdings_df.columns:
            return None

        df = holdings_df.reset_index()
        mask = df['Asset_Class'].isna() | (df['Asset_Class'] == '') | (df['Asset_Class'] == 'Unknown')
        issues = df[mask]

        if issues.empty:
            return None

        items = []
        for _, row in issues.head(50).iterrows():
            asset_name = row.get('Asset_Name')
            expected = self.taxonomy_manager.get_benchmark_category_for_asset(asset_name) if asset_name else None
            items.append(
                {
                    'asset_id': str(row.get('Asset_ID')),
                    'asset_name': asset_name,
                    'market_value': self._safe_float(row.get('Market_Value_CNY')),
                    'suggested_category': expected,
                }
            )

        return CheckResult(
            key='classification_gaps',
            title='Unclassified Holdings',
            severity='medium',
            description='Holdings missing Asset_Class metadata and requiring taxonomy updates.',
            items=items,
        )

    def _check_transaction_anomalies(self, transactions_df: pd.DataFrame) -> Optional[CheckResult]:
        if transactions_df.empty:
            return None

        df = transactions_df.reset_index()
        issues: List[Dict[str, Any]] = []

        if 'Amount_Net' in df.columns:
            df['Amount_Net'] = pd.to_numeric(df['Amount_Net'], errors='coerce').fillna(0)
            zero_mask = df['Amount_Net'].abs() < self.zero_amount_threshold
            for _, row in df[zero_mask].head(25).iterrows():
                issues.append(
                    {
                        'database_id': row.get('Database_ID'),
                        'asset_id': row.get('Asset_ID'),
                        'asset_name': row.get('Asset_Name'),
                        'date': self._format_date(row.get('Date')),
                        'reason': 'Net amount is zero',
                    }
                )

        if 'Transaction_Type' in df.columns:
            type_mask = df['Transaction_Type'].isna() | (df['Transaction_Type'] == '')
            for _, row in df[type_mask].head(25).iterrows():
                issues.append(
                    {
                        'database_id': row.get('Database_ID'),
                        'asset_id': row.get('Asset_ID'),
                        'asset_name': row.get('Asset_Name'),
                        'date': self._format_date(row.get('Date')),
                        'reason': 'Missing transaction type',
                    }
                )

        if 'Transaction_Business_ID' in df.columns:
            duplicates = df[df.duplicated('Transaction_Business_ID', keep=False)]
            for _, row in duplicates.head(25).iterrows():
                issues.append(
                    {
                        'database_id': row.get('Database_ID'),
                        'asset_id': row.get('Asset_ID'),
                        'asset_name': row.get('Asset_Name'),
                        'date': self._format_date(row.get('Date')),
                        'reason': 'Duplicate transaction_id',
                    }
                )

        if not issues:
            return None

        return CheckResult(
            key='transaction_anomalies',
            title='Transaction Anomalies',
            severity='high',
            description='Transactions needing review (missing types, zero cash impact, or duplicates).',
            items=issues[:50],
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _safe_dataframe(self, df: Optional[pd.DataFrame]) -> pd.DataFrame:
        return df if df is not None else pd.DataFrame()

    def _safe_float(self, value: Any) -> float:
        try:
            if value is None:
                return 0.0
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _format_date(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        if hasattr(value, 'isoformat'):
            return value.date().isoformat() if hasattr(value, 'date') else value.isoformat()
        try:
            parsed = pd.to_datetime(value)
            return parsed.strftime('%Y-%m-%d')
        except Exception:  # pragma: no cover - best-effort conversion
            return str(value)

    def _serialize_check(self, result: CheckResult) -> Dict[str, Any]:
        payload = asdict(result)
        payload['count'] = len(result.items)
        return payload

    def _build_summary(self, checks: List[Dict[str, Any]]) -> Dict[str, Any]:
        severity_breakdown: Dict[str, int] = {}
        total_issues = 0
        for check in checks:
            count = check.get('count', 0)
            total_issues += count
            severity = check.get('severity', 'info')
            severity_breakdown[severity] = severity_breakdown.get(severity, 0) + count

        return {
            'issues_total': total_issues,
            'severity_breakdown': severity_breakdown,
            'checks_ran': len(checks),
            'generated_at': datetime.utcnow().isoformat(),
        }
