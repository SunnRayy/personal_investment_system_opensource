"""
Validation Engine

Orchestrates all validation checks and generates comprehensive validation reports.
"""

import logging
from typing import List, Optional
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.data_manager.manager import DataManager
from src.portfolio_lib.taxonomy_manager import TaxonomyManager
from .reporter import ValidationIssue, generate_report
from .checks.core_checks import (
    check_unmapped_assets,
    check_required_schema,
    check_referential_integrity,
    check_transaction_signs,
    check_portfolio_reconciliation
)


class ValidationEngine:
    """
    Coordinates execution of all validation checks and report generation.
    
    The ValidationEngine loads portfolio data through the DataManager and
    TaxonomyManager, runs all MVP validation checks, and generates a
    comprehensive validation report.
    """
    
    def __init__(self, config_path: str = 'config/settings.yaml'):
        """
        Initialize the ValidationEngine.
        
        Args:
            config_path: Path to system configuration file
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.issues: List[ValidationIssue] = []
        self.data_manager: Optional[DataManager] = None
        self.taxonomy_manager: Optional[TaxonomyManager] = None
        
    def _load_data(self) -> bool:
        """
        Load portfolio data through DataManager.
        
        Returns:
            True if data loaded successfully, False otherwise
        """
        try:
            self.logger.info("Loading portfolio data...")
            self.data_manager = DataManager(config_path=self.config_path)
            self.taxonomy_manager = TaxonomyManager()
            self.logger.info("✅ Data loaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to load data: {str(e)}")
            self.issues.append(ValidationIssue(
                issue_id='ENGINE_DATA_LOAD_FAILED',
                severity='CRITICAL',
                check_name='Data Loading',
                description='Failed to load portfolio data',
                details={'error': str(e)},
                suggestion='Check configuration file and data file paths'
            ))
            return False
    
    def run_all_checks(self) -> int:
        """
        Execute all validation checks.
        
        Runs all MVP Core 5 validation checks and collects issues.
        
        Returns:
            Number of issues found
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting Data Validation")
        self.logger.info("=" * 60)
        
        # Load data first
        if not self._load_data():
            return len(self.issues)
        
        # Get dataframes
        try:
            holdings_df = self.data_manager.get_holdings()
            transactions_df = self.data_manager.get_transactions()
            balance_sheet_df = self.data_manager.get_balance_sheet()
        except Exception as e:
            self.logger.error(f"❌ Failed to retrieve dataframes: {str(e)}")
            self.issues.append(ValidationIssue(
                issue_id='ENGINE_DATAFRAME_ACCESS_FAILED',
                severity='CRITICAL',
                check_name='Data Access',
                description='Failed to access data structures',
                details={'error': str(e)},
                suggestion='Verify DataManager implementation and data structure'
            ))
            return len(self.issues)
        
        # Run Check 1: Unmapped Assets
        self.logger.info("\n[1/5] Running Classification/Mapping Integrity check...")
        try:
            check_issues = check_unmapped_assets(holdings_df, self.taxonomy_manager)
            self.issues.extend(check_issues)
            self.logger.info(f"  → Found {len(check_issues)} issues")
        except Exception as e:
            self.logger.error(f"  → Check failed: {str(e)}")
            self.issues.append(ValidationIssue(
                issue_id='CHECK_UNMAPPED_FAILED',
                severity='MAJOR',
                check_name='Classification/Mapping Integrity',
                description='Check execution failed',
                details={'error': str(e)},
                suggestion='Review check implementation'
            ))
        
        # Run Check 2: Schema Integrity
        self.logger.info("\n[2/5] Running Structural Schema Integrity check...")
        try:
            check_issues = check_required_schema(holdings_df, transactions_df, balance_sheet_df)
            self.issues.extend(check_issues)
            self.logger.info(f"  → Found {len(check_issues)} issues")
        except Exception as e:
            self.logger.error(f"  → Check failed: {str(e)}")
            self.issues.append(ValidationIssue(
                issue_id='CHECK_SCHEMA_FAILED',
                severity='MAJOR',
                check_name='Structural Schema Integrity',
                description='Check execution failed',
                details={'error': str(e)},
                suggestion='Review check implementation'
            ))
        
        # Run Check 3: Referential Integrity
        self.logger.info("\n[3/5] Running Referential Consistency check...")
        try:
            check_issues = check_referential_integrity(holdings_df, transactions_df)
            self.issues.extend(check_issues)
            self.logger.info(f"  → Found {len(check_issues)} issues")
        except Exception as e:
            self.logger.error(f"  → Check failed: {str(e)}")
            self.issues.append(ValidationIssue(
                issue_id='CHECK_REFERENTIAL_FAILED',
                severity='MAJOR',
                check_name='Referential Consistency',
                description='Check execution failed',
                details={'error': str(e)},
                suggestion='Review check implementation'
            ))
        
        # Run Check 4: Transaction Signs
        self.logger.info("\n[4/5] Running Transaction Sign Coherence check...")
        try:
            check_issues = check_transaction_signs(transactions_df)
            self.issues.extend(check_issues)
            self.logger.info(f"  → Found {len(check_issues)} issues")
        except Exception as e:
            self.logger.error(f"  → Check failed: {str(e)}")
            self.issues.append(ValidationIssue(
                issue_id='CHECK_SIGNS_FAILED',
                severity='MAJOR',
                check_name='Transaction Sign Coherence',
                description='Check execution failed',
                details={'error': str(e)},
                suggestion='Review check implementation'
            ))
        
        # Run Check 5: Portfolio Reconciliation
        self.logger.info("\n[5/5] Running Portfolio Reconciliation check...")
        try:
            check_issues = check_portfolio_reconciliation(holdings_df, balance_sheet_df)
            self.issues.extend(check_issues)
            self.logger.info(f"  → Found {len(check_issues)} issues")
        except Exception as e:
            self.logger.error(f"  → Check failed: {str(e)}")
            self.issues.append(ValidationIssue(
                issue_id='CHECK_RECONCILIATION_FAILED',
                severity='MAJOR',
                check_name='Portfolio Reconciliation',
                description='Check execution failed',
                details={'error': str(e)},
                suggestion='Review check implementation'
            ))
        
        # Summary
        self.logger.info("\n" + "=" * 60)
        self.logger.info(f"Validation Complete: {len(self.issues)} total issues found")
        
        # Count by severity
        severity_counts = {
            'CRITICAL': sum(1 for i in self.issues if i.severity == 'CRITICAL'),
            'MAJOR': sum(1 for i in self.issues if i.severity == 'MAJOR'),
            'WARNING': sum(1 for i in self.issues if i.severity == 'WARNING'),
            'INFO': sum(1 for i in self.issues if i.severity == 'INFO')
        }
        
        for severity, count in severity_counts.items():
            if count > 0:
                self.logger.info(f"  {severity}: {count}")
        
        self.logger.info("=" * 60)
        
        return len(self.issues)
    
    def generate_report(self, output_dir: str = 'output') -> str:
        """
        Generate validation report.
        
        Args:
            output_dir: Directory where report should be saved
            
        Returns:
            Path to generated report file
        """
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate report
        output_path = os.path.join(output_dir, 'validation_report.md')
        generate_report(self.issues, output_path)
        
        self.logger.info(f"\n📄 Report saved to: {output_path}")
        
        return output_path
    
    def has_critical_issues(self) -> bool:
        """
        Check if any CRITICAL issues were found.
        
        Returns:
            True if there are CRITICAL issues, False otherwise
        """
        return any(issue.severity == 'CRITICAL' for issue in self.issues)
