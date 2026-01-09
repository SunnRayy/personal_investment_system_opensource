"""
Validation Issue Reporter

Defines the ValidationIssue data structure and report generation functionality.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any
from datetime import datetime
import os


@dataclass
class ValidationIssue:
    """
    Represents a single data quality issue found during validation.
    
    Attributes:
        issue_id: Unique identifier for the type of issue (e.g., 'SCHEMA_MISSING_COL')
        severity: Issue severity level ('CRITICAL', 'MAJOR', 'WARNING', 'INFO')
        check_name: Name of the validation check that found this issue
        description: Human-readable description of the issue
        details: Dictionary containing specific details about the issue
        suggestion: Actionable recommendation to fix the issue
    """
    issue_id: str
    severity: str
    check_name: str
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    suggestion: str = ""


def generate_report(issues: List[ValidationIssue], output_path: str) -> None:
    """
    Generate a formatted Markdown validation report.
    
    Args:
        issues: List of ValidationIssue objects to include in the report
        output_path: File path where the report should be saved
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Count issues by severity
    severity_counts = {
        'CRITICAL': 0,
        'MAJOR': 0,
        'WARNING': 0,
        'INFO': 0
    }
    
    for issue in issues:
        severity = issue.severity.upper()
        if severity in severity_counts:
            severity_counts[severity] += 1
    
    # Generate report content
    report_lines = [
        "# Data Validation Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
        "| Severity | Count |",
        "|----------|-------|",
        f"| CRITICAL | {severity_counts['CRITICAL']} |",
        f"| MAJOR    | {severity_counts['MAJOR']} |",
        f"| WARNING  | {severity_counts['WARNING']} |",
        f"| INFO     | {severity_counts['INFO']} |",
        "",
        f"**Total Issues Found:** {len(issues)}",
        "",
    ]
    
    if not issues:
        report_lines.extend([
            "## Status",
            "",
            "✅ **No issues found (Core 5 clean).**",
            "",
            "All validation checks passed successfully.",
            ""
        ])
    else:
        # Group issues by severity
        issues_by_severity = {
            'CRITICAL': [],
            'MAJOR': [],
            'WARNING': [],
            'INFO': []
        }
        
        for issue in issues:
            severity = issue.severity.upper()
            if severity in issues_by_severity:
                issues_by_severity[severity].append(issue)
        
        # Report issues by severity
        for severity in ['CRITICAL', 'MAJOR', 'WARNING', 'INFO']:
            severity_issues = issues_by_severity[severity]
            if not severity_issues:
                continue
            
            report_lines.extend([
                f"## {severity} Issues ({len(severity_issues)})",
                ""
            ])
            
            for i, issue in enumerate(severity_issues, 1):
                report_lines.extend([
                    f"### {i}. {issue.check_name}",
                    "",
                    f"**Issue ID:** `{issue.issue_id}`",
                    "",
                    f"**Description:** {issue.description}",
                    ""
                ])
                
                # Add details if present
                if issue.details:
                    report_lines.append("**Details:**")
                    report_lines.append("")
                    for key, value in issue.details.items():
                        # Format value appropriately
                        if isinstance(value, list):
                            if len(value) > 5:
                                # Show first 5 items and count
                                value_str = ", ".join(str(v) for v in value[:5])
                                value_str += f" ... ({len(value)} total)"
                            else:
                                value_str = ", ".join(str(v) for v in value)
                        else:
                            value_str = str(value)
                        report_lines.append(f"- **{key}:** {value_str}")
                    report_lines.append("")
                
                # Add suggestion if present
                if issue.suggestion:
                    report_lines.extend([
                        f"**Suggested Fix:** {issue.suggestion}",
                        ""
                    ])
                
                report_lines.append("---")
                report_lines.append("")
    
    # Add footer
    report_lines.extend([
        "## Next Steps",
        "",
        "1. Address CRITICAL issues immediately - these may cause system failures",
        "2. Review and fix MAJOR issues - these indicate significant data quality problems",
        "3. Consider fixing WARNING issues - these may indicate configuration or data entry issues",
        "4. Review INFO items - these are informational and may not require action",
        ""
    ])
    
    # Write report to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f"✅ Validation report generated: {output_path}")
