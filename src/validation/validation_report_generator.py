"""
Validation Report Generator

Creates human-readable validation reports with clear status indicators,
comparison tables, and investigation guidance for manual review.

Author: Personal Investment System
Date: November 2, 2025
"""

import os
import sys
from typing import Dict, List, Any
from datetime import datetime

# Add project root to path first
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class ValidationReportGenerator:
    """
    Generate comprehensive, human-readable validation reports.
    
    Creates detailed reports with:
    - Executive summary with color-coded status
    - Detailed comparison tables
    - Investigation paths for discrepancies
    - Prioritized action recommendations
    """
    
    def __init__(self):
        """Initialize the validation report generator."""
        self.status_symbols = {
            'PASS': '✅',
            'WARNING': '⚠️',
            'FAIL': '❌',
            'ERROR': '🚫',
            'PASS_WITH_ISSUES': '⚡'
        }
        
        self.severity_symbols = {
            'CRITICAL': '🔴',
            'HIGH': '🟠', 
            'MEDIUM': '🟡',
            'LOW': '🟢',
            'WARNING': '⚠️'
        }
    
    def generate_comprehensive_report(
        self,
        validation_results: Dict[str, Any],
        output_file: str = None
    ) -> str:
        """
        Generate a comprehensive validation report.
        
        Args:
            validation_results: Complete validation results dictionary
            output_file: Optional file path to save the report
            
        Returns:
            The complete report as a string
        """
        report_lines = []
        
        # Header
        report_lines.extend(self._generate_header())
        
        # Executive Summary
        report_lines.extend(self._generate_executive_summary(validation_results))
        
        # Detailed Validation Results
        report_lines.extend(self._generate_detailed_results(validation_results))
        
        # Issues Summary
        report_lines.extend(self._generate_issues_summary(validation_results))
        
        # Investigation Guide
        report_lines.extend(self._generate_investigation_guide(validation_results))
        
        # Action Plan
        report_lines.extend(self._generate_action_plan(validation_results))
        
        # Footer
        report_lines.extend(self._generate_footer(validation_results))
        
        # Join all lines
        report = '\n'.join(report_lines)
        
        # Save to file if requested
        if output_file:
            self._save_report(report, output_file)
        
        return report
    
    def _generate_header(self) -> List[str]:
        """Generate report header."""
        return [
            "=" * 80,
            "🔍 PERSONAL INVESTMENT SYSTEM - DATA VALIDATION REPORT",
            "=" * 80,
            f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "Validation Framework Version: 1.0",
            ""
        ]
    
    def _generate_executive_summary(self, results: Dict[str, Any]) -> List[str]:
        """Generate executive summary section."""
        summary = results.get('summary', {})
        metadata = results.get('metadata', {})
        
        overall_status = summary.get('overall_status', 'UNKNOWN')
        status_symbol = self.status_symbols.get(overall_status, '❓')
        
        total_issues = summary.get('total_issues', 0)
        issue_breakdown = summary.get('issue_breakdown', {})
        duration = metadata.get('duration_seconds', 0)
        
        lines = [
            "📋 EXECUTIVE SUMMARY",
            "=" * 40,
            f"Overall Status: {status_symbol} {overall_status}",
            f"Total Issues Found: {total_issues}",
            f"Validation Duration: {duration:.2f} seconds",
            f"Sections Completed: {summary.get('sections_completed', 0)}",
            "",
            "Issue Breakdown:",
        ]
        
        # Add issue breakdown with symbols
        for severity, count in issue_breakdown.items():
            if count > 0:
                symbol = self.severity_symbols.get(severity, '•')
                lines.append(f"  {symbol} {severity}: {count}")
        
        if total_issues == 0:
            lines.append("  🎉 No issues found!")
        
        # Quick priority summary
        critical_count = issue_breakdown.get('CRITICAL', 0)
        high_count = issue_breakdown.get('HIGH', 0)
        
        lines.append("")
        if critical_count > 0:
            lines.append(f"⚠️  URGENT: {critical_count} critical issues require immediate attention")
        elif high_count > 0:
            lines.append(f"⚠️  PRIORITY: {high_count} high-priority issues need resolution")
        else:
            lines.append("ℹ️  No urgent issues detected")
        
        lines.append("")
        return lines
    
    def _generate_detailed_results(self, results: Dict[str, Any]) -> List[str]:
        """Generate detailed validation results section."""
        lines = [
            "📊 DETAILED VALIDATION RESULTS",
            "=" * 50,
            ""
        ]
        
        validation_results = results.get('validation_results', {})
        
        for section_name, section_data in validation_results.items():
            lines.append(f"🔍 {section_name}")
            lines.append("-" * (len(section_name) + 4))
            
            if isinstance(section_data, dict):
                # Process each subsection
                for subsection_name, subsection_data in section_data.items():
                    lines.extend(self._format_subsection_results(subsection_name, subsection_data))
                    lines.append("")
            
            lines.append("")
        
        return lines
    
    def _format_subsection_results(self, name: str, data: Dict[str, Any]) -> List[str]:
        """Format individual subsection results."""
        if not isinstance(data, dict):
            return [f"  {name}: {data}"]
        
        status = data.get('status', 'UNKNOWN')
        status_symbol = self.status_symbols.get(status, '❓')
        
        lines = [f"  {status_symbol} {name.title().replace('_', ' ')}: {status}"]
        
        # Add checks performed
        checks = data.get('checks_performed', [])
        if checks:
            lines.append(f"    Checks: {', '.join(checks)}")
        
        # Add issues found
        issues = data.get('issues_found', [])
        if issues:
            lines.append("    Issues:")
            for issue in issues[:3]:  # Limit to first 3 issues
                lines.append(f"      • {issue}")
            if len(issues) > 3:
                lines.append(f"      • ... and {len(issues) - 3} more")
        
        # Add summary statistics
        summary = data.get('summary', {})
        if summary and isinstance(summary, dict):
            key_metrics = []
            for key, value in summary.items():
                if key != 'note':  # Skip implementation notes
                    key_metrics.append(f"{key.replace('_', ' ').title()}: {value}")
            
            if key_metrics:
                lines.append(f"    Summary: {', '.join(key_metrics[:2])}")  # Show first 2 metrics
        
        return lines
    
    def _generate_issues_summary(self, results: Dict[str, Any]) -> List[str]:
        """Generate issues summary section."""
        issues = results.get('issues', [])
        
        if not issues:
            return [
                "🎉 ISSUES SUMMARY",
                "=" * 30,
                "No issues detected!",
                ""
            ]
        
        lines = [
            "⚠️  ISSUES SUMMARY",
            "=" * 30,
            ""
        ]
        
        # Group issues by severity
        issues_by_severity = {}
        for issue in issues:
            severity = issue.get('severity', 'UNKNOWN')
            if severity not in issues_by_severity:
                issues_by_severity[severity] = []
            issues_by_severity[severity].append(issue)
        
        # Display issues by severity (highest first)
        severity_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'WARNING']
        
        for severity in severity_order:
            if severity in issues_by_severity:
                severity_issues = issues_by_severity[severity]
                symbol = self.severity_symbols.get(severity, '•')
                
                lines.append(f"{symbol} {severity} Issues ({len(severity_issues)})")
                lines.append("-" * (len(severity) + 20))
                
                for i, issue in enumerate(severity_issues[:5]):  # Show top 5 per severity
                    issue_id = issue.get('issue_id', 'UNKNOWN')
                    description = issue.get('description', 'No description')
                    check_name = issue.get('check_name', 'Unknown Check')
                    
                    lines.append(f"  {i+1}. [{issue_id}] {description}")
                    lines.append(f"     Check: {check_name}")
                    
                    suggestion = issue.get('suggestion', '')
                    if suggestion:
                        lines.append(f"     Suggestion: {suggestion}")
                    lines.append("")
                
                if len(severity_issues) > 5:
                    lines.append(f"     ... and {len(severity_issues) - 5} more {severity.lower()} issues")
                    lines.append("")
        
        return lines
    
    def _generate_investigation_guide(self, results: Dict[str, Any]) -> List[str]:
        """Generate investigation guide section."""
        issues = results.get('issues', [])
        
        lines = [
            "🔍 INVESTIGATION GUIDE",
            "=" * 40,
            ""
        ]
        
        if not issues:
            lines.extend([
                "No issues require investigation.",
                ""
            ])
            return lines
        
        # Focus on critical and high-priority issues for investigation guide
        critical_high_issues = [
            issue for issue in issues 
            if issue.get('severity') in ['CRITICAL', 'HIGH']
        ]
        
        if not critical_high_issues:
            lines.extend([
                "No critical or high-priority issues require immediate investigation.",
                "Review medium and low priority issues in the Issues Summary section.",
                ""
            ])
            return lines
        
        for i, issue in enumerate(critical_high_issues[:3], 1):  # Top 3 issues
            lines.extend(self._format_investigation_steps(i, issue))
        
        if len(critical_high_issues) > 3:
            lines.append(f"... and {len(critical_high_issues) - 3} more issues requiring investigation")
            lines.append("")
        
        return lines
    
    def _format_investigation_steps(self, issue_num: int, issue: Dict[str, Any]) -> List[str]:
        """Format investigation steps for a specific issue."""
        issue_id = issue.get('issue_id', 'UNKNOWN')
        severity = issue.get('severity', 'UNKNOWN')
        description = issue.get('description', 'No description')
        check_name = issue.get('check_name', 'Unknown Check')
        suggestion = issue.get('suggestion', 'No suggestion provided')
        details = issue.get('details', {})
        
        severity_symbol = self.severity_symbols.get(severity, '•')
        
        lines = [
            f"Issue #{issue_num}: {description}",
            f"Priority: {severity_symbol} {severity}",
            f"Issue ID: {issue_id}",
            f"Check: {check_name}",
            "",
            "Investigation Steps:",
            f"1. {suggestion}",
        ]
        
        # Add specific investigation steps based on issue type
        if 'XIRR' in issue_id:
            lines.extend([
                "2. Check cash flow data completeness and accuracy",
                "3. Verify transaction dates and amounts",
                "4. Compare with golden test cases if available",
                "5. Review PerformanceCalculator logs for calculation details"
            ])
        elif 'CLASSIFICATION' in issue_id or 'MAPPING' in issue_id:
            lines.extend([
                "2. Review asset_taxonomy.yaml for missing mappings",
                "3. Check asset name consistency between data sources",
                "4. Verify fund name mappings for CN funds",
                "5. Update taxonomy configuration as needed"
            ])
        elif 'CURRENCY' in issue_id:
            lines.extend([
                "2. Check USD transaction processing logic",
                "3. Verify historical exchange rates",
                "4. Review CurrencyConverter service logs",
                "5. Validate conversion accuracy with manual calculations"
            ])
        else:
            lines.extend([
                "2. Review relevant data processing logic",
                "3. Check input data quality and format",
                "4. Verify calculation methods and formulas",
                "5. Test with known good data sets"
            ])
        
        # Add relevant file locations if available in details
        if details:
            lines.append("")
            lines.append("Relevant Details:")
            for key, value in details.items():
                if isinstance(value, (list, dict)):
                    lines.append(f"  {key}: {type(value).__name__} with {len(value)} items")
                else:
                    lines.append(f"  {key}: {value}")
        
        lines.append("")
        lines.append("-" * 60)
        lines.append("")
        
        return lines
    
    def _generate_action_plan(self, results: Dict[str, Any]) -> List[str]:
        """Generate prioritized action plan section."""
        issues = results.get('issues', [])
        
        lines = [
            "📋 PRIORITIZED ACTION PLAN",
            "=" * 45,
            ""
        ]
        
        if not issues:
            lines.extend([
                "🎉 No actions required - all validations passed!",
                ""
            ])
            return lines
        
        # Group actions by priority
        critical_actions = [i for i in issues if i.get('severity') == 'CRITICAL']
        high_actions = [i for i in issues if i.get('severity') == 'HIGH']
        medium_low_actions = [i for i in issues if i.get('severity') in ['MEDIUM', 'LOW', 'WARNING']]
        
        # High Priority Actions
        if critical_actions:
            lines.append("🔴 HIGH PRIORITY (Fix Immediately):")
            for i, action in enumerate(critical_actions, 1):
                lines.append(f"{i}. {action.get('description')}")
                lines.append(f"   Action: {action.get('suggestion')}")
                lines.append("   Time Estimate: Immediate (Critical)")
                lines.append("")
        
        # Medium Priority Actions
        if high_actions:
            lines.append("🟠 MEDIUM PRIORITY (Fix This Week):")
            for i, action in enumerate(high_actions, 1):
                lines.append(f"{i}. {action.get('description')}")
                lines.append(f"   Action: {action.get('suggestion')}")
                lines.append("   Time Estimate: 1-2 hours")
                lines.append("")
        
        # Low Priority Actions
        if medium_low_actions:
            lines.append("🟡 LOW PRIORITY (Fix Next Sprint):")
            for i, action in enumerate(medium_low_actions[:3], 1):  # Top 3 only
                lines.append(f"{i}. {action.get('description')}")
                lines.append(f"   Action: {action.get('suggestion')}")
                lines.append("")
            
            if len(medium_low_actions) > 3:
                lines.append(f"   ... and {len(medium_low_actions) - 3} more low-priority items")
                lines.append("")
        
        return lines
    
    def _generate_footer(self, results: Dict[str, Any]) -> List[str]:
        """Generate report footer."""
        metadata = results.get('metadata', {})
        
        return [
            "=" * 80,
            "📊 VALIDATION SUMMARY",
            "=" * 80,
            f"Validation completed at: {metadata.get('validation_date', 'Unknown')}",
            f"Total execution time: {metadata.get('duration_seconds', 0):.2f} seconds",
            f"Framework version: {metadata.get('validator_version', 'Unknown')}",
            f"Configuration: {metadata.get('config_path', 'Unknown')}",
            "",
            "For detailed technical information, check the system logs.",
            "For assistance with issue resolution, consult the investigation guide above.",
            "",
            "=" * 80
        ]
    
    def _save_report(self, report: str, file_path: str) -> None:
        """
        Save report to file.
        
        Args:
            report: The complete report string
            file_path: Path where to save the report
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(f"✅ Validation report saved to: {file_path}")
            
        except Exception as e:
            print(f"❌ Failed to save validation report: {e}")
    
    def generate_quick_summary(self, validation_results: Dict[str, Any]) -> str:
        """
        Generate a quick summary for console output.
        
        Args:
            validation_results: Complete validation results
            
        Returns:
            Short summary string suitable for console display
        """
        summary = validation_results.get('summary', {})
        overall_status = summary.get('overall_status', 'UNKNOWN')
        total_issues = summary.get('total_issues', 0)
        issue_breakdown = summary.get('issue_breakdown', {})
        
        status_symbol = self.status_symbols.get(overall_status, '❓')
        
        lines = [
            f"🔍 Validation Status: {status_symbol} {overall_status}",
            f"   Total Issues: {total_issues}"
        ]
        
        if total_issues > 0:
            critical = issue_breakdown.get('CRITICAL', 0)
            high = issue_breakdown.get('HIGH', 0)
            
            if critical > 0:
                lines.append(f"   🔴 Critical: {critical}")
            if high > 0:
                lines.append(f"   🟠 High: {high}")
        
        return '\n'.join(lines)


def main():
    """Test the validation report generator."""
    # Create sample validation results for testing
    sample_results = {
        'metadata': {
            'validation_date': '2025-11-02 15:30:00',
            'duration_seconds': 45.67,
            'validator_version': '1.0',
            'config_path': 'config/settings.yaml'
        },
        'summary': {
            'overall_status': 'WARNING',
            'total_issues': 3,
            'issue_breakdown': {
                'CRITICAL': 0,
                'HIGH': 1,
                'MEDIUM': 2,
                'LOW': 0,
                'WARNING': 0
            },
            'sections_completed': 3,
            'initialization_success': True
        },
        'validation_results': {
            'Source Data Validation': {
                'holdings_accuracy': {
                    'status': 'PASS',
                    'checks_performed': ['Required columns', 'Null values'],
                    'issues_found': [],
                    'summary': {'total_assets': 47, 'total_value_cny': 5481213}
                },
                'transactions_accuracy': {
                    'status': 'WARNING',
                    'checks_performed': ['Column validation', 'Type validation'],
                    'issues_found': ['2 unknown transaction types'],
                    'summary': {'total_transactions': 1234}
                }
            }
        },
        'issues': [
            {
                'issue_id': 'XIRR_UNREASONABLE_Employer_Stock_A',
                'severity': 'HIGH',
                'check_name': 'XIRR Calculation Validation',
                'description': 'Unreasonable XIRR value for Employer_Stock_A',
                'details': {'asset_name': 'Employer_Stock_A', 'xirr_value': 1250.5},
                'suggestion': 'Review transaction data and calculation method for this asset'
            }
        ]
    }
    
    generator = ValidationReportGenerator()
    
    # Generate full report
    report = generator.generate_comprehensive_report(sample_results)
    print(report)
    
    # Generate quick summary
    print("\n" + "="*50)
    print("QUICK SUMMARY:")
    print("="*50)
    summary = generator.generate_quick_summary(sample_results)
    print(summary)


if __name__ == "__main__":
    main()