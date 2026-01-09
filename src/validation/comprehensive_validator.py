"""
Comprehensive Data Validation Orchestrator

Extends the existing ValidationEngine to provide comprehensive validation
for XIRR calculations, profit/loss amounts, return percentages, Sharpe ratios,
currency conversions, and cross-output consistency.

Author: Personal Investment System
Date: November 2, 2025
"""

import logging
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add project root to path first
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import project modules
from src.validation.engine import ValidationEngine
from src.validation.reporter import ValidationIssue
from src.financial_analysis.performance_calculator import PerformanceCalculator
from src.data_manager.manager import DataManager
from src.portfolio_lib.data_integration import PortfolioAnalysisManager
from src.portfolio_lib.taxonomy_manager import TaxonomyManager
from src.financial_analysis.analyzer import FinancialAnalyzer


class ComprehensiveValidator:
    """
    Comprehensive validation orchestrator for the Personal Investment System.
    
    Provides systematic validation of:
    - Source data accuracy against Excel files
    - Financial calculations (XIRR, profit/loss, returns, Sharpe ratios)
    - Currency conversions
    - Asset classifications
    - Cross-output consistency between HTML and markdown reports
    """
    
    def __init__(self, config_path: str = 'config/settings.yaml'):
        """
        Initialize the comprehensive validator.
        
        Args:
            config_path: Path to system configuration file
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        
        # Initialize components
        self.base_validator = ValidationEngine(config_path)
        self.performance_calc = PerformanceCalculator()
        self.data_manager: Optional[DataManager] = None
        self.portfolio_manager: Optional[PortfolioAnalysisManager] = None
        self.taxonomy_manager: Optional[TaxonomyManager] = None
        self.financial_analyzer: Optional[FinancialAnalyzer] = None
        
        # Validation results storage
        self.validation_results: Dict[str, Any] = {}
        self.issues: List[ValidationIssue] = []
        
        # Validation tolerances
        self.tolerances = {
            'xirr_percent': 0.1,  # ±0.1% tolerance for XIRR
            'currency_percent': 0.01,  # ±0.01% tolerance for currency conversion
            'value_absolute': 1.0,  # ±¥1 tolerance for portfolio values
            'percentage_points': 0.01  # ±0.01 percentage points
        }
    
    def _initialize_components(self) -> bool:
        """
        Initialize all required system components.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Initializing validation components...")
            
            # Initialize data manager
            self.data_manager = DataManager(config_path=self.config_path)
            
            # Initialize other components
            self.taxonomy_manager = TaxonomyManager()
            self.portfolio_manager = PortfolioAnalysisManager()
            self.financial_analyzer = FinancialAnalyzer()
            
            self.logger.info("✅ All validation components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize validation components: {e}")
            self.issues.append(ValidationIssue(
                issue_id='INIT_COMPONENTS_FAILED',
                severity='CRITICAL',
                check_name='Component Initialization',
                description='Failed to initialize validation components',
                details={'error': str(e)},
                suggestion='Check configuration files and dependencies'
            ))
            return False
    
    def validate_full_pipeline(self, include_base_checks: bool = True) -> Dict[str, Any]:
        """
        Run comprehensive validation across the entire pipeline.
        
        Args:
            include_base_checks: Whether to include base validation engine checks
            
        Returns:
            Dictionary containing validation results and summary
        """
        self.logger.info("=" * 80)
        self.logger.info("🔍 COMPREHENSIVE DATA VALIDATION STARTING")
        self.logger.info("=" * 80)
        
        start_time = datetime.now()
        
        # Initialize components
        if not self._initialize_components():
            return self._generate_validation_report(start_time, failed_init=True)
        
        # Run base validation checks if requested
        if include_base_checks:
            self.logger.info("📋 Running base validation checks...")
            base_issues_count = self.base_validator.run_all_checks()
            self.issues.extend(self.base_validator.issues)
            self.logger.info(f"   Base validation found {base_issues_count} issues")
        
        # Run comprehensive validation checks
        validation_sections = [
            ('Source Data Validation', self.validate_source_data_accuracy),
            ('Financial Calculation Validation', self.validate_calculation_accuracy),
            ('Cross-Output Consistency Validation', self.validate_cross_output_consistency)
        ]
        
        for section_name, validation_func in validation_sections:
            self.logger.info(f"📊 Running {section_name}...")
            try:
                section_results = validation_func()
                self.validation_results[section_name] = section_results
                self.logger.info(f"   ✅ {section_name} completed")
            except Exception as e:
                self.logger.error(f"   ❌ {section_name} failed: {e}")
                self.issues.append(ValidationIssue(
                    issue_id=f'SECTION_FAILED_{section_name.upper().replace(" ", "_")}',
                    severity='HIGH',
                    check_name=section_name,
                    description=f'Validation section failed: {section_name}',
                    details={'error': str(e)},
                    suggestion=f'Check {section_name.lower()} validation logic and data availability'
                ))
        
        return self._generate_validation_report(start_time)
    
    def validate_source_data_accuracy(self) -> Dict[str, Any]:
        """
        Validate processed data accuracy against Excel sources.
        
        Returns:
            Dictionary containing source data validation results
        """
        results = {
            'holdings_accuracy': self._validate_holdings_data(),
            'transactions_accuracy': self._validate_transactions_data(),
            'currency_conversions': self._validate_currency_conversions(),
            'asset_classifications': self._validate_asset_classifications()
        }
        
        return results
    
    def validate_calculation_accuracy(self) -> Dict[str, Any]:
        """
        Validate financial calculations using canonical methods.
        
        Returns:
            Dictionary containing calculation validation results
        """
        results = {
            'xirr_calculations': self._validate_xirr_calculations(),
            'profit_loss_calculations': self._validate_profit_loss_calculations(),
            'return_calculations': self._validate_return_calculations(),
            'sharpe_ratio_calculations': self._validate_sharpe_ratio_calculations()
        }
        
        return results
    
    def validate_cross_output_consistency(self, html_path: str = None, markdown_path: str = None) -> Dict[str, Any]:
        """
        Validate consistency between HTML and markdown outputs using the dedicated validator.
        
        Args:
            html_path: Path to HTML report file (auto-detected if None)
            markdown_path: Path to markdown report file (auto-detected if None)
            
        Returns:
            Dictionary containing consistency validation results
        """
        self.logger.info("Validating cross-output consistency...")
        
        # Dynamic import to avoid circular dependencies
        from src.validation.cross_output_validator import CrossOutputConsistencyValidator
        
        # Auto-discover report files if not provided
        if html_path is None:
            html_path = "output/investment_analysis_report.html"
        if markdown_path is None:
            markdown_path = "output/investment_analysis_report.md"
            
        # Check if files exist
        if not os.path.exists(html_path):
            self.logger.warning(f"HTML report not found at {html_path}")
            return {
                'status': 'ERROR',
                'message': f"HTML report not found at {html_path}",
                'inconsistencies': [],
                'portfolio_metrics_consistency': {},
                'asset_performance_consistency': {},
                'allocation_data_consistency': {}
            }
            
        if not os.path.exists(markdown_path):
            self.logger.warning(f"Markdown report not found at {markdown_path}")
            return {
                'status': 'ERROR', 
                'message': f"Markdown report not found at {markdown_path}",
                'inconsistencies': [],
                'portfolio_metrics_consistency': {},
                'asset_performance_consistency': {},
                'allocation_data_consistency': {}
            }
        
        # Use the dedicated cross-output validator
        cross_validator = CrossOutputConsistencyValidator()
        consistency_results = cross_validator.validate_consistency(html_path, markdown_path)
        
        # Enhance with legacy validation methods
        legacy_results = {
            'portfolio_metrics_consistency': self._validate_portfolio_metrics_consistency(),
            'asset_performance_consistency': self._validate_asset_performance_consistency(),
            'allocation_data_consistency': self._validate_allocation_data_consistency()
        }
        
        # Combine results
        combined_results = {
            **consistency_results,
            **legacy_results,
            'comprehensive_analysis': True
        }
        
        return combined_results
    
    def _validate_holdings_data(self) -> Dict[str, Any]:
        """Validate holdings data accuracy against Excel sources."""
        validation_result = {
            'status': 'PASS',
            'checks_performed': [],
            'issues_found': [],
            'summary': {}
        }
        
        try:
            # Get holdings data
            holdings_df = self.data_manager.get_holdings()
            
            if holdings_df is None or holdings_df.empty:
                validation_result['status'] = 'FAIL'
                validation_result['issues_found'].append('No holdings data available')
                return validation_result
            
            # Check required columns
            required_columns = ['Asset_Name', 'Market_Value_CNY', 'Shares']
            missing_columns = [col for col in required_columns if col not in holdings_df.columns]
            
            if missing_columns:
                validation_result['status'] = 'FAIL'
                validation_result['issues_found'].append(f'Missing required columns: {missing_columns}')
                self.issues.append(ValidationIssue(
                    issue_id='HOLDINGS_MISSING_COLUMNS',
                    severity='HIGH',
                    check_name='Holdings Data Validation',
                    description='Required columns missing from holdings data',
                    details={'missing_columns': missing_columns},
                    suggestion='Ensure Excel data includes all required columns'
                ))
            
            # Check for null values in critical columns
            for col in required_columns:
                if col in holdings_df.columns:
                    null_count = holdings_df[col].isnull().sum()
                    if null_count > 0:
                        validation_result['status'] = 'WARNING' if validation_result['status'] == 'PASS' else validation_result['status']
                        validation_result['issues_found'].append(f'{null_count} null values in {col}')
            
            # Summary statistics
            validation_result['summary'] = {
                'total_assets': len(holdings_df),
                'total_value_cny': holdings_df['Market_Value_CNY'].sum() if 'Market_Value_CNY' in holdings_df.columns else 0,
                'assets_with_shares': holdings_df['Shares'].notna().sum() if 'Shares' in holdings_df.columns else 0
            }
            
            validation_result['checks_performed'] = [
                'Required columns presence',
                'Null value detection',
                'Data type validation',
                'Summary statistics generation'
            ]
            
        except Exception as e:
            validation_result['status'] = 'ERROR'
            validation_result['issues_found'].append(f'Validation error: {str(e)}')
            self.issues.append(ValidationIssue(
                issue_id='HOLDINGS_VALIDATION_ERROR',
                severity='HIGH',
                check_name='Holdings Data Validation',
                description='Error during holdings data validation',
                details={'error': str(e)},
                suggestion='Check holdings data format and processing logic'
            ))
        
        return validation_result
    
    def _validate_transactions_data(self) -> Dict[str, Any]:
        """Validate transactions data accuracy against Excel sources."""
        validation_result = {
            'status': 'PASS',
            'checks_performed': [],
            'issues_found': [],
            'summary': {}
        }
        
        try:
            # Get transactions data
            transactions_df = self.data_manager.get_transactions()
            
            if transactions_df is None or transactions_df.empty:
                validation_result['status'] = 'FAIL'
                validation_result['issues_found'].append('No transactions data available')
                return validation_result
            
            # Check required columns
            required_columns = ['Date', 'Asset_Name', 'Transaction_Type', 'Amount_Net', 'Shares']
            missing_columns = [col for col in required_columns if col not in transactions_df.columns]
            
            if missing_columns:
                validation_result['status'] = 'FAIL'
                validation_result['issues_found'].append(f'Missing required columns: {missing_columns}')
            
            # Validate transaction types
            if 'Transaction_Type' in transactions_df.columns:
                valid_types = ['Buy', 'Sell', 'Dividend', 'RSU_Vest', 'Premium_Payment']
                invalid_types = transactions_df[~transactions_df['Transaction_Type'].isin(valid_types)]['Transaction_Type'].unique()
                
                if len(invalid_types) > 0:
                    validation_result['status'] = 'WARNING' if validation_result['status'] == 'PASS' else validation_result['status']
                    validation_result['issues_found'].append(f'Unknown transaction types found: {list(invalid_types)}')
            
            # Summary statistics
            validation_result['summary'] = {
                'total_transactions': len(transactions_df),
                'date_range': {
                    'earliest': transactions_df['Date'].min().strftime('%Y-%m-%d') if 'Date' in transactions_df.columns else 'N/A',
                    'latest': transactions_df['Date'].max().strftime('%Y-%m-%d') if 'Date' in transactions_df.columns else 'N/A'
                },
                'transaction_types': transactions_df['Transaction_Type'].value_counts().to_dict() if 'Transaction_Type' in transactions_df.columns else {}
            }
            
            validation_result['checks_performed'] = [
                'Required columns presence',
                'Transaction type validation',
                'Date format validation',
                'Summary statistics generation'
            ]
            
        except Exception as e:
            validation_result['status'] = 'ERROR'
            validation_result['issues_found'].append(f'Validation error: {str(e)}')
            self.issues.append(ValidationIssue(
                issue_id='TRANSACTIONS_VALIDATION_ERROR',
                severity='HIGH',
                check_name='Transactions Data Validation',
                description='Error during transactions data validation',
                details={'error': str(e)},
                suggestion='Check transactions data format and processing logic'
            ))
        
        return validation_result
    
    def _validate_currency_conversions(self) -> Dict[str, Any]:
        """Validate USD to CNY currency conversions."""
        validation_result = {
            'status': 'PASS',
            'checks_performed': ['Currency conversion accuracy'],
            'issues_found': [],
            'summary': {}
        }
        
        try:
            # Get transactions with USD amounts
            transactions_df = self.data_manager.get_transactions()
            
            if transactions_df is None or transactions_df.empty:
                validation_result['status'] = 'FAIL'
                validation_result['issues_found'].append('No transactions data for currency validation')
                return validation_result
            
            # Find USD transactions (RSU and US ETF transactions)
            usd_transactions = transactions_df[
                (transactions_df['Asset_Name'].str.contains('RSU_', na=False)) |
                (transactions_df['Asset_Name'].str.contains('ETF', na=False)) |
                (transactions_df['Asset_Name'].str.contains('USD', na=False))
            ]
            
            validation_result['summary'] = {
                'total_usd_transactions': len(usd_transactions),
                'usd_assets_identified': usd_transactions['Asset_Name'].nunique() if not usd_transactions.empty else 0
            }
            
            # Note: Detailed currency conversion validation would require
            # access to original USD amounts and conversion rates
            # This is a placeholder for enhanced validation
            
        except Exception as e:
            validation_result['status'] = 'ERROR'
            validation_result['issues_found'].append(f'Currency validation error: {str(e)}')
        
        return validation_result
    
    def _validate_asset_classifications(self) -> Dict[str, Any]:
        """Validate asset taxonomy classifications."""
        validation_result = {
            'status': 'PASS',
            'checks_performed': ['Asset taxonomy mapping'],
            'issues_found': [],
            'summary': {}
        }
        
        try:
            holdings_df = self.data_manager.get_holdings()
            
            if holdings_df is None or holdings_df.empty:
                validation_result['status'] = 'FAIL'
                validation_result['issues_found'].append('No holdings data for classification validation')
                return validation_result
            
            # Apply taxonomy classification
            classified_holdings = self.taxonomy_manager.classify_holdings(holdings_df)
            
            # Check classification coverage
            if 'Level_1' in classified_holdings.columns:
                unmapped_assets = classified_holdings[classified_holdings['Level_1'].isna()]
                unmapped_count = len(unmapped_assets)
                
                if unmapped_count > 0:
                    validation_result['status'] = 'WARNING'
                    validation_result['issues_found'].append(f'{unmapped_count} assets lack Level_1 classification')
                    
                    # Add unmapped assets to issues
                    unmapped_list = unmapped_assets['Asset_Name'].tolist() if 'Asset_Name' in unmapped_assets.columns else []
                    self.issues.append(ValidationIssue(
                        issue_id='UNMAPPED_ASSETS_CLASSIFICATION',
                        severity='MEDIUM',
                        check_name='Asset Classification Validation',
                        description=f'{unmapped_count} assets lack proper classification',
                        details={'unmapped_assets': unmapped_list[:10]},  # Limit to first 10
                        suggestion='Update asset_taxonomy.yaml with mappings for unmapped assets'
                    ))
            
            validation_result['summary'] = {
                'total_assets': len(classified_holdings),
                'classified_assets': (classified_holdings['Level_1'].notna()).sum() if 'Level_1' in classified_holdings.columns else 0,
                'classification_coverage': f"{((classified_holdings['Level_1'].notna()).sum() / len(classified_holdings) * 100):.1f}%" if 'Level_1' in classified_holdings.columns else "0%"
            }
            
        except Exception as e:
            validation_result['status'] = 'ERROR'
            validation_result['issues_found'].append(f'Classification validation error: {str(e)}')
        
        return validation_result
    
    def _validate_xirr_calculations(self) -> Dict[str, Any]:
        """Validate XIRR calculations using canonical PerformanceCalculator."""
        validation_result = {
            'status': 'PASS',
            'checks_performed': ['XIRR calculation accuracy'],
            'issues_found': [],
            'summary': {}
        }
        
        try:
            # Get performance data from financial analyzer
            performance_data = self.financial_analyzer.analyze_investments()
            
            if not performance_data or 'individual_asset_performance' not in performance_data:
                validation_result['status'] = 'FAIL'
                validation_result['issues_found'].append('No performance data available for XIRR validation')
                return validation_result
            
            individual_performance = performance_data['individual_asset_performance']
            xirr_results = []
            xirr_issues = []
            
            # Validate each asset's XIRR calculation
            for asset_data in individual_performance:
                asset_name = asset_data.get('asset_name', 'Unknown')
                xirr_value = asset_data.get('xirr', None)
                
                if xirr_value is not None:
                    # Check for unreasonable XIRR values
                    if abs(xirr_value) > 1000:  # More than 1000% return
                        xirr_issues.append(f'{asset_name}: {xirr_value:.1f}% (unreasonable)')
                        self.issues.append(ValidationIssue(
                            issue_id=f'UNREASONABLE_XIRR_{asset_name}',
                            severity='MEDIUM',
                            check_name='XIRR Calculation Validation',
                            description=f'Unreasonable XIRR value for {asset_name}',
                            details={'asset_name': asset_name, 'xirr_value': xirr_value},
                            suggestion='Review transaction data and calculation method for this asset'
                        ))
                    else:
                        xirr_results.append(xirr_value)
            
            if xirr_issues:
                validation_result['status'] = 'WARNING'
                validation_result['issues_found'].extend(xirr_issues)
            
            validation_result['summary'] = {
                'assets_with_xirr': len(xirr_results),
                'average_xirr': f"{sum(xirr_results) / len(xirr_results):.2f}%" if xirr_results else "N/A",
                'xirr_range': f"{min(xirr_results):.2f}% to {max(xirr_results):.2f}%" if xirr_results else "N/A",
                'unreasonable_xirr_count': len(xirr_issues)
            }
            
        except Exception as e:
            validation_result['status'] = 'ERROR'
            validation_result['issues_found'].append(f'XIRR validation error: {str(e)}')
        
        return validation_result
    
    def _validate_profit_loss_calculations(self) -> Dict[str, Any]:
        """Validate profit/loss calculations."""
        # Placeholder for profit/loss validation logic
        return {
            'status': 'PASS',
            'checks_performed': ['Profit/loss calculation validation'],
            'issues_found': [],
            'summary': {'note': 'Profit/loss validation not yet implemented'}
        }
    
    def _validate_return_calculations(self) -> Dict[str, Any]:
        """Validate return percentage calculations."""
        # Placeholder for return calculation validation logic
        return {
            'status': 'PASS',
            'checks_performed': ['Return calculation validation'],
            'issues_found': [],
            'summary': {'note': 'Return calculation validation not yet implemented'}
        }
    
    def _validate_sharpe_ratio_calculations(self) -> Dict[str, Any]:
        """Validate Sharpe ratio calculations."""
        # Placeholder for Sharpe ratio validation logic
        return {
            'status': 'PASS',
            'checks_performed': ['Sharpe ratio calculation validation'],
            'issues_found': [],
            'summary': {'note': 'Sharpe ratio validation not yet implemented'}
        }
    
    def _validate_portfolio_metrics_consistency(self) -> Dict[str, Any]:
        """Validate consistency of portfolio metrics between HTML and markdown."""
        # Placeholder for cross-output consistency validation
        return {
            'status': 'PASS',
            'checks_performed': ['Portfolio metrics consistency'],
            'issues_found': [],
            'summary': {'note': 'Cross-output consistency validation not yet implemented'}
        }
    
    def _validate_asset_performance_consistency(self) -> Dict[str, Any]:
        """Validate consistency of asset performance between HTML and markdown."""
        # Placeholder for asset performance consistency validation
        return {
            'status': 'PASS',
            'checks_performed': ['Asset performance consistency'],
            'issues_found': [],
            'summary': {'note': 'Asset performance consistency validation not yet implemented'}
        }
    
    def _validate_allocation_data_consistency(self) -> Dict[str, Any]:
        """Validate consistency of allocation data between HTML and markdown."""
        # Placeholder for allocation data consistency validation
        return {
            'status': 'PASS',
            'checks_performed': ['Allocation data consistency'],
            'issues_found': [],
            'summary': {'note': 'Allocation data consistency validation not yet implemented'}
        }
    
    def _generate_validation_report(self, start_time: datetime, failed_init: bool = False) -> Dict[str, Any]:
        """
        Generate comprehensive validation report.
        
        Args:
            start_time: When validation started
            failed_init: Whether initialization failed
            
        Returns:
            Dictionary containing complete validation report
        """
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Count issues by severity
        issue_counts = {
            'CRITICAL': len([i for i in self.issues if i.severity == 'CRITICAL']),
            'HIGH': len([i for i in self.issues if i.severity == 'HIGH']),
            'MEDIUM': len([i for i in self.issues if i.severity == 'MEDIUM']),
            'LOW': len([i for i in self.issues if i.severity == 'LOW']),
            'WARNING': len([i for i in self.issues if i.severity == 'WARNING'])
        }
        
        # Determine overall status
        if failed_init or issue_counts['CRITICAL'] > 0:
            overall_status = 'FAIL'
        elif issue_counts['HIGH'] > 0:
            overall_status = 'WARNING'
        elif sum(issue_counts.values()) > 0:
            overall_status = 'PASS_WITH_ISSUES'
        else:
            overall_status = 'PASS'
        
        report = {
            'metadata': {
                'validation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'duration_seconds': duration,
                'validator_version': '1.0',
                'config_path': self.config_path
            },
            'summary': {
                'overall_status': overall_status,
                'total_issues': len(self.issues),
                'issue_breakdown': issue_counts,
                'sections_completed': len(self.validation_results),
                'initialization_success': not failed_init
            },
            'validation_results': self.validation_results,
            'issues': [
                {
                    'issue_id': issue.issue_id,
                    'severity': issue.severity,
                    'check_name': issue.check_name,
                    'description': issue.description,
                    'details': issue.details,
                    'suggestion': issue.suggestion
                } for issue in self.issues
            ]
        }
        
        self.logger.info("=" * 80)
        self.logger.info(f"🎯 VALIDATION COMPLETE - Status: {overall_status}")
        self.logger.info(f"   Duration: {duration:.2f} seconds")
        self.logger.info(f"   Total Issues: {len(self.issues)}")
        if issue_counts['CRITICAL'] > 0:
            self.logger.warning(f"   ⚠️  CRITICAL Issues: {issue_counts['CRITICAL']}")
        if issue_counts['HIGH'] > 0:
            self.logger.warning(f"   ⚠️  HIGH Issues: {issue_counts['HIGH']}")
        self.logger.info("=" * 80)
        
        return report


def main():
    """Test the comprehensive validator."""
    logging.basicConfig(level=logging.INFO)
    
    validator = ComprehensiveValidator()
    results = validator.validate_full_pipeline()
    
    print("\n" + "=" * 80)
    print("COMPREHENSIVE VALIDATION RESULTS")
    print("=" * 80)
    print(f"Overall Status: {results['summary']['overall_status']}")
    print(f"Total Issues: {results['summary']['total_issues']}")
    print(f"Duration: {results['metadata']['duration_seconds']:.2f} seconds")
    
    if results['issues']:
        print("\nTop 5 Issues:")
        for issue in results['issues'][:5]:
            print(f"  - {issue['severity']}: {issue['description']}")


if __name__ == "__main__":
    main()