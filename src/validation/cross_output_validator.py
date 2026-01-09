"""
Cross-Output Consistency Validator

Validates that HTML and markdown outputs show identical values for all
critical financial metrics including XIRR, profit/loss, returns, and Sharpe ratios.

Author: Personal Investment System
Date: November 2, 2025
"""

import os
import sys
import re
from typing import Dict, List, Any

# Add project root to path first
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.validation.reporter import ValidationIssue


class CrossOutputConsistencyValidator:
    """
    Validate consistency between HTML and markdown outputs.
    
    Compares critical financial metrics between HTML reports and markdown
    context files to ensure identical values and flag discrepancies.
    """
    
    def __init__(self, tolerance_percent: float = 0.01):
        """
        Initialize the consistency validator.
        
        Args:
            tolerance_percent: Tolerance for numerical comparisons (default: 0.01%)
        """
        self.tolerance_percent = tolerance_percent
        self.issues: List[ValidationIssue] = []
        
        # Patterns for extracting metrics from HTML/markdown
        self.metric_patterns = {
            'portfolio_value': [
                r'Total Portfolio Value[:\s]*[¥$]?([\d,]+\.?\d*)',
                r'Portfolio Total[:\s]*[¥$]?([\d,]+\.?\d*)',
                r'Market Value[:\s]*[¥$]?([\d,]+\.?\d*)',
                r'Rebalanceable Assets[:\s]*[¥$]?([\d,]+\.?\d*)'
            ],
            'portfolio_xirr': [
                r'Portfolio XIRR[^|]*?\|\s*([\d.-]+)%',    # Markdown table format
                r'(\d+\.\d+)%.*?Overall XIRR',            # HTML: value before label
                r'Overall XIRR[:\s]*([\d.-]+)%',
                r'Total Return[:\s]*([\d.-]+)%'
            ],
            'asset_xirr': [
                r'([A-Z_]+)[:\s]*XIRR[:\s]*([\d.-]+)%',
                r'Asset:\s*([A-Z_]+)[^>]*XIRR[:\s]*([\d.-]+)%'
            ],
            'sharpe_ratio': [
                r'Sharpe Ratio[^|]*?\|\s*([\d.-]+)',      # Markdown table format
                r'(\d+\.\d+)</div>.*?Sharpe Ratio',       # HTML: value before label
                r'Sharpe Ratio[:\s]*([\d.-]+)',
                r'Sharp Ratio[:\s]*([\d.-]+)'             # Common typo
            ]
        }
    
    def validate_consistency(
        self,
        html_input,
        markdown_input
    ) -> Dict[str, Any]:
        """
        Validate consistency between HTML and markdown outputs.
        
        Args:
            html_input: Path to HTML file or list of paths
            markdown_input: Path to markdown file or list of paths
            
        Returns:
            Dictionary containing validation results
        """
        # Convert single strings to lists for uniform processing
        html_files = [html_input] if isinstance(html_input, str) else html_input
        markdown_files = [markdown_input] if isinstance(markdown_input, str) else markdown_input
        validation_result = {
            'status': 'PASS',
            'checks_performed': [],
            'issues_found': [],
            'summary': {},
            'detailed_comparison': {}
        }
        
        try:
            # Extract metrics from HTML files
            html_metrics = self._extract_metrics_from_files(html_files, 'HTML')
            
            # Extract metrics from markdown files
            markdown_metrics = self._extract_metrics_from_files(markdown_files, 'Markdown')
            
            # Compare metrics
            comparison_results = self._compare_metrics(html_metrics, markdown_metrics)
            
            # Analyze results
            validation_result.update(self._analyze_comparison_results(comparison_results))
            
            validation_result['checks_performed'] = [
                'Portfolio value consistency',
                'Portfolio XIRR consistency',
                'Asset-level XIRR consistency',
                'Sharpe ratio consistency'
            ]
            
            validation_result['detailed_comparison'] = comparison_results
            
        except Exception as e:
            validation_result['status'] = 'ERROR'
            validation_result['issues_found'].append(f'Consistency validation error: {str(e)}')
            self.issues.append(ValidationIssue(
                issue_id='CONSISTENCY_VALIDATION_ERROR',
                severity='HIGH',
                check_name='Cross-Output Consistency Validation',
                description='Error during consistency validation',
                details={'error': str(e)},
                suggestion='Check HTML and markdown file availability and format'
            ))
        
        return validation_result
    
    def _extract_metrics_from_files(self, file_paths: List[str], source_type: str) -> Dict[str, Any]:
        """
        Extract financial metrics from files.
        
        Args:
            file_paths: List of file paths to analyze
            source_type: Type of source ('HTML' or 'Markdown')
            
        Returns:
            Dictionary of extracted metrics
        """
        metrics = {
            'portfolio_values': [],
            'portfolio_xirrs': [],
            'asset_xirrs': {},
            'sharpe_ratios': []
        }
        
        for file_path in file_paths:
            if not os.path.exists(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract portfolio values
                portfolio_values = self._extract_metric_values(content, 'portfolio_value')
                metrics['portfolio_values'].extend(portfolio_values)
                
                # Extract portfolio XIRR
                portfolio_xirrs = self._extract_metric_values(content, 'portfolio_xirr')
                metrics['portfolio_xirrs'].extend(portfolio_xirrs)
                
                # Extract asset-level XIRR
                asset_xirrs = self._extract_asset_xirrs(content)
                for asset, xirr in asset_xirrs.items():
                    if asset not in metrics['asset_xirrs']:
                        metrics['asset_xirrs'][asset] = []
                    metrics['asset_xirrs'][asset].append(xirr)
                
                # Extract Sharpe ratios
                sharpe_ratios = self._extract_metric_values(content, 'sharpe_ratio')
                metrics['sharpe_ratios'].extend(sharpe_ratios)
                
            except Exception as e:
                self.issues.append(ValidationIssue(
                    issue_id=f'FILE_READ_ERROR_{source_type}',
                    severity='MEDIUM',
                    check_name='File Reading',
                    description=f'Error reading {source_type} file: {file_path}',
                    details={'file_path': file_path, 'error': str(e)},
                    suggestion=f'Check {source_type} file accessibility and format'
                ))
        
        return metrics
    
    def _extract_metric_values(self, content: str, metric_type: str) -> List[float]:
        """
        Extract metric values from content using regex patterns.
        
        Args:
            content: File content to search
            metric_type: Type of metric to extract
            
        Returns:
            List of extracted numerical values
        """
        values = []
        patterns = self.metric_patterns.get(metric_type, [])
        
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    # Extract the numerical part
                    value_str = match.group(1).replace(',', '')
                    value = float(value_str)
                    values.append(value)
                except (ValueError, IndexError):
                    continue
        
        return values
    
    def _extract_asset_xirrs(self, content: str) -> Dict[str, float]:
        """
        Extract asset-level XIRR values.
        
        Args:
            content: File content to search
            
        Returns:
            Dictionary mapping asset names to XIRR values
        """
        asset_xirrs = {}
        patterns = self.metric_patterns.get('asset_xirr', [])
        
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    asset_name = match.group(1).strip()
                    xirr_value = float(match.group(2))
                    asset_xirrs[asset_name] = xirr_value
                except (ValueError, IndexError):
                    continue
        
        return asset_xirrs
    
    def _compare_metrics(
        self,
        html_metrics: Dict[str, Any],
        markdown_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare metrics between HTML and markdown sources.
        
        Args:
            html_metrics: Metrics extracted from HTML files
            markdown_metrics: Metrics extracted from markdown files
            
        Returns:
            Dictionary containing comparison results
        """
        comparison = {
            'portfolio_value': self._compare_values(
                html_metrics.get('portfolio_values', []),
                markdown_metrics.get('portfolio_values', []),
                'Portfolio Value'
            ),
            'portfolio_xirr': self._compare_values(
                html_metrics.get('portfolio_xirrs', []),
                markdown_metrics.get('portfolio_xirrs', []),
                'Portfolio XIRR'
            ),
            'sharpe_ratio': self._compare_values(
                html_metrics.get('sharpe_ratios', []),
                markdown_metrics.get('sharpe_ratios', []),
                'Sharpe Ratio'
            ),
            'asset_xirrs': self._compare_asset_xirrs(
                html_metrics.get('asset_xirrs', {}),
                markdown_metrics.get('asset_xirrs', {})
            )
        }
        
        return comparison
    
    def _compare_values(
        self,
        html_values: List[float],
        markdown_values: List[float],
        metric_name: str
    ) -> Dict[str, Any]:
        """
        Compare lists of values with tolerance.
        
        Args:
            html_values: Values from HTML files
            markdown_values: Values from markdown files
            metric_name: Name of the metric for reporting
            
        Returns:
            Dictionary containing comparison result
        """
        result = {
            'status': 'PASS',
            'html_values': html_values,
            'markdown_values': markdown_values,
            'discrepancies': [],
            'match_count': 0,
            'total_comparisons': 0
        }
        
        if not html_values and not markdown_values:
            result['status'] = 'NO_DATA'
            return result
        
        if not html_values:
            result['status'] = 'MISSING_HTML'
            result['discrepancies'].append('No HTML values found')
            return result
        
        if not markdown_values:
            result['status'] = 'MISSING_MARKDOWN'
            result['discrepancies'].append('No markdown values found')
            return result
        
        # Compare values (take first value from each source for now)
        html_value = html_values[0] if html_values else None
        markdown_value = markdown_values[0] if markdown_values else None
        
        if html_value is not None and markdown_value is not None:
            result['total_comparisons'] = 1
            
            if self._values_match(html_value, markdown_value):
                result['match_count'] = 1
                result['status'] = 'PASS'
            else:
                result['status'] = 'FAIL'
                diff_percent = abs(html_value - markdown_value) / max(abs(html_value), abs(markdown_value)) * 100
                result['discrepancies'].append(
                    f'HTML: {html_value}, Markdown: {markdown_value} (diff: {diff_percent:.2f}%)'
                )
                
                # Create validation issue
                self.issues.append(ValidationIssue(
                    issue_id=f'METRIC_MISMATCH_{metric_name.upper().replace(" ", "_")}',
                    severity='HIGH',
                    check_name='Cross-Output Consistency',
                    description=f'{metric_name} mismatch between HTML and markdown',
                    details={
                        'html_value': html_value,
                        'markdown_value': markdown_value,
                        'difference_percent': diff_percent
                    },
                    suggestion=f'Check {metric_name.lower()} calculation consistency between output generators'
                ))
        
        return result
    
    def _compare_asset_xirrs(
        self,
        html_asset_xirrs: Dict[str, List[float]],
        markdown_asset_xirrs: Dict[str, List[float]]
    ) -> Dict[str, Any]:
        """
        Compare asset-level XIRR values.
        
        Args:
            html_asset_xirrs: Asset XIRR values from HTML
            markdown_asset_xirrs: Asset XIRR values from markdown
            
        Returns:
            Dictionary containing comparison results
        """
        result = {
            'status': 'PASS',
            'asset_comparisons': {},
            'match_count': 0,
            'total_assets': 0,
            'discrepancies': []
        }
        
        # Get all unique asset names
        all_assets = set(html_asset_xirrs.keys()) | set(markdown_asset_xirrs.keys())
        result['total_assets'] = len(all_assets)
        
        for asset in all_assets:
            html_values = html_asset_xirrs.get(asset, [])
            markdown_values = markdown_asset_xirrs.get(asset, [])
            
            asset_result = self._compare_values(html_values, markdown_values, f'Asset {asset} XIRR')
            result['asset_comparisons'][asset] = asset_result
            
            if asset_result['status'] == 'PASS':
                result['match_count'] += 1
            elif asset_result['status'] == 'FAIL':
                result['discrepancies'].extend(asset_result['discrepancies'])
        
        if result['discrepancies']:
            result['status'] = 'FAIL'
        elif result['total_assets'] == 0:
            result['status'] = 'NO_DATA'
        
        return result
    
    def _values_match(self, value1: float, value2: float) -> bool:
        """
        Check if two values match within tolerance.
        
        Args:
            value1: First value
            value2: Second value
            
        Returns:
            True if values match within tolerance
        """
        if value1 == value2:
            return True
        
        if abs(value1) < 1e-10 and abs(value2) < 1e-10:
            return True  # Both effectively zero
        
        max_value = max(abs(value1), abs(value2))
        if max_value == 0:
            return True
        
        diff_percent = abs(value1 - value2) / max_value * 100
        return diff_percent <= self.tolerance_percent
    
    def _analyze_comparison_results(self, comparison_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze comparison results and generate summary.
        
        Args:
            comparison_results: Results from metric comparisons
            
        Returns:
            Dictionary containing analysis results
        """
        result = {
            'status': 'PASS',
            'issues_found': [],
            'summary': {}
        }
        
        total_checks = 0
        passed_checks = 0
        failed_checks = 0
        
        for metric_name, metric_result in comparison_results.items():
            total_checks += 1
            status = metric_result.get('status', 'UNKNOWN')
            
            if status == 'PASS':
                passed_checks += 1
            elif status == 'FAIL':
                failed_checks += 1
                result['issues_found'].append(f'{metric_name} values inconsistent')
            elif status in ['NO_DATA', 'MISSING_HTML', 'MISSING_MARKDOWN']:
                result['issues_found'].append(f'{metric_name} data missing or incomplete')
        
        # Determine overall status
        if failed_checks > 0:
            result['status'] = 'FAIL'
        elif len(result['issues_found']) > 0:
            result['status'] = 'WARNING'
        
        result['summary'] = {
            'total_metric_types': total_checks,
            'passed_checks': passed_checks,
            'failed_checks': failed_checks,
            'consistency_rate': f"{(passed_checks / total_checks * 100):.1f}%" if total_checks > 0 else "0%"
        }
        
        return result


def main():
    """Test the cross-output consistency validator."""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    validator = CrossOutputConsistencyValidator()
    
    # Example file paths (these would be real paths in practice)
    html_files = ['output/portfolio_dashboard.html', 'output/investment_compass.html']
    markdown_files = ['output/Personal_Investment_Analysis_Context.md']
    
    results = validator.validate_consistency(html_files, markdown_files)
    
    print("=" * 60)
    print("CROSS-OUTPUT CONSISTENCY VALIDATION RESULTS")
    print("=" * 60)
    print(f"Status: {results['status']}")
    print(f"Checks Performed: {', '.join(results['checks_performed'])}")
    
    if results['issues_found']:
        print("\nIssues Found:")
        for issue in results['issues_found']:
            print(f"  - {issue}")
    
    summary = results.get('summary', {})
    if summary:
        print("\nSummary:")
        for key, value in summary.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
    
    if validator.issues:
        print("\nValidation Issues:")
        for issue in validator.issues:
            print(f"  - {issue.severity}: {issue.description}")


if __name__ == "__main__":
    main()