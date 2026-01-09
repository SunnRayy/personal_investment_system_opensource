# portfolio_lib/reporting/generator.py
"""
Module for generating comprehensive analysis reports (Text and HTML).
(Accepts captured image filenames for HTML report)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Set
import os
import html # For escaping text

# --- Formatters (Keep as is) ---
try:
    from ..utils.helpers import currency_formatter
except ImportError:
    print("Warning (reporting.generator): Could not import currency_formatter from utils. Using basic formatting.")
    def _fallback_currency_formatter(x, pos=None):
        if pd.isna(x): return "N/A"
        try: num_x = float(x); return f"{num_x:,.0f}"
        except (ValueError, TypeError): return str(x)
    currency_formatter = _fallback_currency_formatter

def _format_pct(value: Optional[float], precision: int = 1) -> str:
    """Formats a float as a percentage string or returns 'N/A'."""
    if value is None or pd.isna(value) or not isinstance(value, (int, float)):
        return "N/A"
    return f"{value:.{precision}%}"

# --- generate_text_report (Keep as is, including scenario key fixes) ---
def generate_text_report(analysis_results: Dict[str, Any], settings: Dict[str, Any]) -> str:
    """
    Generates a comprehensive text-based analysis report.
    """
    print("\nGenerating Text Report...")
    report_lines: List[str] = []
    reporting_settings = settings.get('reporting', {})
    analysis_params = settings.get('analysis_params', {})
    curr_fmt = lambda x: currency_formatter(x)
    pct_fmt = lambda x, p=1: _format_pct(x, p)

    # --- Data Extraction ---
    actual_holdings = analysis_results.get('actual_holdings', {})
    target_hist = analysis_results.get('target_allocation_historical')
    target_predef = analysis_results.get('target_allocation_predefined')
    drift_hist_df = analysis_results.get('drift_analysis_hist')
    drift_predef_df = analysis_results.get('drift_analysis_predef')
    concentration_risk = analysis_results.get('concentration_risk', {})
    recom_hist = analysis_results.get('recommendations_hist')
    recom_predef = analysis_results.get('recommendations_predef')
    scenarios_hist = analysis_results.get('rebalancing_scenarios_hist')
    scenarios_predef = analysis_results.get('rebalancing_scenarios_predef')
    data_quality = analysis_results.get('data_quality', {})
    timestamp = analysis_results.get('timestamp', 'N/A')
    risk_preference = analysis_results.get('risk_preference', 'N/A')
    mpt_results = analysis_results.get('mpt_results')
    mpt_data_source = analysis_results.get('mpt_data_source', 'N/A')

    # --- Report Sections ---
    report_lines.append("=" * 80)
    report_lines.append(f"资产配置分析报告 (Portfolio Analysis Report)")
    report_lines.append(f"生成时间 (Generated Time): {timestamp}")
    report_lines.append(f"分析风险偏好 (Analysis Risk Profile): {risk_preference}")
    report_lines.append("=" * 80)

    # Data Quality
    report_lines.append("\n📊 数据质量评估 (Data Quality Assessment)")
    report_lines.append(f"  - 历史数据质量评分 (Quality Score): {data_quality.get('quality_score', 0.0):.1f}/10")
    report_lines.append(f"  - 历史数据时间跨度 (Months Used): {data_quality.get('time_span_months', 'N/A')} 月")
    report_lines.append(f"  - 资产类别覆盖率 (Coverage): {pct_fmt(data_quality.get('asset_coverage'), 0)}")
    report_lines.append(f"  - 数据完整性 (Completeness): {pct_fmt(data_quality.get('completeness'))}")
    report_lines.append(f"  - MPT 使用数据源 (MPT Data Source): {mpt_data_source}")
    if not data_quality.get('sufficient_for_mpt'):
        report_lines.append(f"  - 原因 (Reason for Fallback): {data_quality.get('reason', 'N/A')}")

    quality_score = data_quality.get('quality_score', 0.0)
    if quality_score < 7.0:
        report_lines.append("\n⚠️ MPT结果质量警告 (MPT Result Quality Warning)")
        report_lines.append(f"  基于{mpt_data_source}的历史数据计算得出的MPT结果质量评分仅为{quality_score:.1f}/10，")
        report_lines.append("  可能不够稳健或不切合实际。建议主要参考预定义模板目标配置进行决策。")
        report_lines.append(f"  (MPT results based on {mpt_data_source} have a low quality score of {quality_score:.1f}/10.)")
        report_lines.append("  (Please prioritize predefined template recommendations.)")

    # Current Portfolio
    report_lines.append("\n💼 当前投资组合概览 (Current Portfolio Overview)")
    total_value = actual_holdings.get('total', 0.0)
    current_values = actual_holdings.get('values', {})
    current_pcts = actual_holdings.get('percentages', {})
    report_lines.append(f"  - 总价值 (Total Value): {curr_fmt(total_value)}")
    report_lines.append("  - 当前资产配置 (Current Allocation):")
    sorted_current = sorted(current_values.items(), key=lambda item: item[1], reverse=True)
    for category, value in sorted_current:
        percentage = current_pcts.get(category, 0.0)
        report_lines.append(f"    * {category:<10}: {curr_fmt(value):>12} ({pct_fmt(percentage):>6})")

    # Concentration Risk
    report_lines.append("\n⚠️ 集中度风险评估 (Concentration Risk Assessment)")
    report_lines.append(f"  - HHI 指数 (HHI Index): {concentration_risk.get('HHI指数', 0.0):.3f}")
    report_lines.append(f"  - 风险级别 (Risk Level): {concentration_risk.get('集中度风险级别', 'N/A')}")
    report_lines.append(f"  - 最大持仓类别 (Largest Holding): {concentration_risk.get('最大持仓类别', 'N/A')}")
    report_lines.append(f"  - 最大持仓比例 (Largest %): {pct_fmt(concentration_risk.get('最大持仓比例'))}")
    report_lines.append(f"  - 前3大类别占比 (Top 3 %): {pct_fmt(concentration_risk.get('前3大类别占比'))}")
    report_lines.append(f"  - 建议 (Suggestion): {concentration_risk.get('建议', 'N/A')}")

    # Target Allocations & Drift
    report_lines.append("\n🎯 目标配置与偏离分析 (Target Allocations & Drift Analysis)")
    def format_drift_df(df: Optional[pd.DataFrame]) -> str:
        if df is None or df.empty: return "  未能进行偏离分析。(Drift analysis could not be performed.)"
        drift_display = df.copy()
        for col in ['当前配置 (%)', '目标配置 (%)', '绝对偏离 (%)']:
             if col in drift_display.columns: drift_display[col] = drift_display[col].apply(lambda x: pct_fmt(x, 1))
        if '相对偏离 (%)' in drift_display.columns:
            drift_display['相对偏离 (%)'] = drift_display['相对偏离 (%)'].apply(
                lambda x: pct_fmt(x, 1) if pd.notna(x) and np.isfinite(x) else ('+∞' if x > 0 else ('-∞' if x < 0 else 'N/A'))
            )
        return drift_display.to_string()

    report_lines.append("\n  --- 1. 基于历史数据计算的目标 (Target based on Historical Data) ---")
    if target_hist:
        report_lines.append(f"    (数据源 Data Source: {mpt_data_source})")
        sorted_target_hist = sorted(target_hist.items(), key=lambda item: item[1], reverse=True)
        for category, allocation in sorted_target_hist:
             if allocation > 1e-4: report_lines.append(f"    - {category:<10}: {pct_fmt(allocation)}")
        report_lines.append("\n    偏离分析 (Drift Analysis vs Historical Target):")
        report_lines.append(format_drift_df(drift_hist_df))
    else:
        report_lines.append("    未能基于历史/输入数据计算目标配置。(Could not calculate target based on historical/input data.)")

    report_lines.append("\n  --- 2. 基于预定义模板的目标 (Target based on Predefined Template) ---")
    if target_predef:
        report_lines.append(f"    (模板风险偏好 Template Risk Profile: {risk_preference})")
        sorted_target_predef = sorted(target_predef.items(), key=lambda item: item[1], reverse=True)
        for category, allocation in sorted_target_predef:
             if allocation > 1e-4: report_lines.append(f"    - {category:<10}: {pct_fmt(allocation)}")
        report_lines.append("\n    偏离分析 (Drift Analysis vs Predefined Target):")
        report_lines.append(format_drift_df(drift_predef_df))
    else:
        report_lines.append("    未能加载预定义目标配置。(Could not load predefined target allocation.)")

    # Rebalancing Recommendations
    report_lines.append("\n⚖️ 再平衡建议 (Rebalancing Recommendations)")
    threshold = analysis_params.get('rebalancing_threshold', 0.05)
    report_lines.append(f"  (基于偏离阈值 Based on Drift Threshold: {pct_fmt(threshold, 0)})")
    def format_recommendations(recom_dict: Optional[Dict[str, Any]], target_type: str) -> List[str]:
        lines = []
        if recom_dict and recom_dict.get('actions_needed'):
            lines.append(f"\n  --- 建议 (基于 {target_type} 目标) Recommendations (vs {target_type} Target) ---")
            lines.append("    需要执行以下操作 (The following actions are recommended):")
            for action in recom_dict.get('actions', []):
                lines.append(f"    - {action['category']}: {action['action']} {pct_fmt(action['amount_pct'])}")
                lines.append(f"      (当前 Current {pct_fmt(action['current_pct'])} → 目标 Target {pct_fmt(action['target_pct'])})")
        elif recom_dict:
            lines.append(f"\n  --- 建议 (基于 {target_type} 目标) Recommendations (vs {target_type} Target) ---")
            lines.append("    当前配置在合理范围内，无需立即再平衡。(Allocation within threshold.)")
        else:
            lines.append(f"\n  --- 建议 (基于 {target_type} 目标) Recommendations (vs {target_type} Target) ---")
            lines.append("    未能生成再平衡建议。(Could not generate recommendations.)")
        return lines
    report_lines.extend(format_recommendations(recom_hist, "历史/输入数据 Historical/Input"))
    report_lines.extend(format_recommendations(recom_predef, "预定义模板 Predefined"))

    # Rebalancing Scenarios (Using corrected keys)
    report_lines.append("\n⚙️ 再平衡情景分析 (Rebalancing Scenario Analysis)")
    scenario_summary = {}
    if scenarios_predef: scenario_summary = scenarios_predef.get('summary', {})
    elif scenarios_hist: scenario_summary = scenarios_hist.get('summary', {})
    report_lines.append(f"  - 新增投资金额 (New Investment): {curr_fmt(scenario_summary.get('new_investment', 0))}")
    report_lines.append(f"  - 假设交易成本费率 (Assumed Txn Cost Rate): {scenario_summary.get('transaction_cost_rate', 0.0):.3%}")
    report_lines.append(f"  - 假设资本利得税率 (Assumed Tax Rate): {scenario_summary.get('tax_rate', 0.0):.1%}")

    def format_scenarios(scen_dict: Optional[Dict[str, Any]], target_type: str) -> List[str]:
        lines = []
        if not scen_dict:
            lines.append(f"\n  --- 情景分析 (基于 {target_type} 目标) Scenario Analysis (vs {target_type} Target) ---")
            lines.append("    未能进行情景分析。(Could not perform scenario analysis.)")
            return lines

        full_rebal = scen_dict.get('full_rebalancing_adjusted', {}) # Use '_adjusted' key
        new_money_rebal = scen_dict.get('new_money_only_adjusted', {}) # Use '_adjusted' key
        summary = scen_dict.get('summary', {})

        lines.append(f"\n  --- 情景分析 (基于 {target_type} 目标) Scenario Analysis (vs {target_type} Target) ---")
        lines.append("    情景1: 完全再平衡 (调整后) (Scenario 1: Full Rebalancing - Adjusted)")
        lines.append(f"      - 需卖出总额 (Total Sell Value): {curr_fmt(full_rebal.get('total_sell_value', 0))}")
        lines.append(f"      - 需买入总额 (Total Buy Value): {curr_fmt(full_rebal.get('total_buy_value', 0))}")
        lines.append(f"      - 可用资金 (Funds Available): {curr_fmt(full_rebal.get('funds_available', 0))}")
        funding_shortfall = full_rebal.get('funding_shortfall', 0)
        if funding_shortfall > 1e-2: lines.append(f"      - **资金缺口 (Funding Shortfall):** {curr_fmt(funding_shortfall)}")
        else: lines.append(f"      - 资金状态 (Funding Status): 充足 (Sufficient)")
        lines.append(f"      - 预估交易成本 (Est. Txn Costs): {curr_fmt(full_rebal.get('estimated_transaction_costs', 0))}")
        lines.append(f"      - 预估税负影响 (Est. Tax Impact): {curr_fmt(full_rebal.get('estimated_tax_impact', 0))}")

        lines.append("\n    情景2: 仅用新增资金 (调整后) (Scenario 2: New Money Only - Adjusted)")
        if summary.get('new_investment', 0) > 0:
             lines.append(f"      - 可覆盖买入缺口比例 (Buy Gap Coverage): {pct_fmt(new_money_rebal.get('coverage_ratio', 0))}")
             lines.append(f"      - 预估交易成本 (Est. Txn Costs): {curr_fmt(new_money_rebal.get('estimated_transaction_costs', 0))}")
             remaining_gaps = new_money_rebal.get('remaining_buy_gaps', {})
             remaining_gaps_str = ", ".join([f"{k}: {curr_fmt(v)}" for k,v in remaining_gaps.items() if v > 1e-6])
             lines.append(f"      - 剩余买入缺口 (Remaining Buy Gaps): {remaining_gaps_str or '无 (None)'}")
        else:
             lines.append("      未提供新增资金，此情景不适用。(No new investment provided.)")
        return lines

    report_lines.extend(format_scenarios(scenarios_hist, "历史/输入数据 Historical/Input"))
    report_lines.extend(format_scenarios(scenarios_predef, "预定义模板 Predefined"))

    # Implementation Roadmap
    roadmap_scenario = scenarios_predef if scenarios_predef else scenarios_hist
    roadmap_target_type = "预定义模板 Predefined" if scenarios_predef else "历史/输入数据 Historical/Input"
    if roadmap_scenario:
        try:
            from ..analysis.rebalancing import generate_roadmap_text
            roadmap_text = generate_roadmap_text(roadmap_scenario, settings)
            report_lines.append(f"\n--- 实施路线图 (基于 {roadmap_target_type} 调整后情景) ---")
            report_lines.append(roadmap_text)
        except ImportError:
            report_lines.append("\n--- Implementation Roadmap ---")
            report_lines.append("  (Error: Could not generate roadmap text - rebalancing module not found.)")
        except Exception as e:
            report_lines.append("\n--- Implementation Roadmap ---")
            report_lines.append(f"  (Error generating roadmap: {e})")
    else:
        report_lines.append("\n--- Implementation Roadmap ---")
        report_lines.append("  (未能生成路线图，无有效情景分析结果。 No valid scenario results for roadmap.)")

    # Footer
    report_lines.append("\n" + "=" * 80)
    report_lines.append("报告结束 (End of Report)")
    report_lines.append("免责声明：本报告仅供参考，不构成投资建议。投资有风险，决策需谨慎。")
    report_lines.append("(Disclaimer: This report is for informational purposes only and does not constitute investment advice.)")
    report_lines.append("=" * 80)

    print("Text report generation complete.")
    return "\n".join(report_lines)


# --- HTML Report Generation (MODIFIED to use image_filenames dictionary) ---
def generate_html_report(
    analysis_results: Dict[str, Any],
    settings: Dict[str, Any],
    image_filenames: Optional[Dict[str, str]] = None # Accept captured filenames
) -> str:
    """
    Generates a basic HTML report embedding text results and saved chart images.

    Args:
        analysis_results: Dictionary containing results from all analysis steps.
        settings: The loaded configuration dictionary.
        image_filenames: A dictionary mapping descriptive keys (e.g., 'alloc_pie_predef')
                         to the actual sanitized base filenames (without extension)
                         of the saved charts, as captured from plotter.py.
                         Assumes images are saved in the same directory as the HTML file.

    Returns:
        A string containing the generated HTML content.
    """
    print("\nGenerating HTML Report...")
    if image_filenames is None:
        print("Warning: No image filenames provided for HTML report.")
        image_filenames = {} # Use empty dict to avoid errors

    timestamp = analysis_results.get('timestamp', 'N/A')
    risk_preference = analysis_results.get('risk_preference', 'N/A')
    # Regenerate text report content for embedding
    # Consider caching this if performance is an issue
    text_report_content = generate_text_report(analysis_results, settings)
    escaped_text_report = html.escape(text_report_content)

    vis_settings = settings.get('visualization', {})
    img_format = vis_settings.get('chart_format', 'png')

    # --- Helper function to get image source path ---
    def get_img_src(key: str) -> str:
        """
        Constructs the relative image path using the captured base filename.
        Returns an empty string if the key is not found or filename is None/empty.
        """
        filename_base = image_filenames.get(key) # Get captured base filename
        if filename_base:
            return f"{filename_base}.{img_format}" # Construct relative path
        else:
            print(f"  - Image key '{key}' not found in provided filenames.")
            return "" # Return empty string if key not found

    # --- Build HTML Sections for Images (Using captured filenames via get_img_src) ---
    # Note: The keys used here ('alloc_pie_predef', 'drift_hist', etc.) MUST match
    # the keys used when populating the report_image_filenames dictionary in Cell 1.

    alloc_comp_predef_html = f"""
    <div class="chart-container">
        <h4>可调整部分内部配置: 当前 vs 预定义目标</h4>
        <img src="{get_img_src('alloc_pie_predef')}" alt="Allocation Pie Chart (Predefined Target - Rebal Portion)">
        <img src="{get_img_src('alloc_bar_predef')}" alt="Allocation Bar Chart (Predefined Target - Rebal Portion)">
    </div>""" if image_filenames.get('alloc_pie_predef') else "<p><i>预定义目标配置比较图表未生成。(Allocation comparison chart (Predefined) not generated.)</i></p>"

    drift_predef_html = f"""
    <div class="chart-container">
        <h4>可调整资产偏离分析 vs 预定义目标</h4>
        <img src="{get_img_src('drift_predef')}" alt="Drift Analysis Chart (Predefined Target - Rebalanceable)">
    </div>""" if image_filenames.get('drift_predef') else "<p><i>预定义目标偏离分析图表未生成。(Drift analysis chart (Predefined) not generated.)</i></p>"

    alloc_comp_hist_html = f"""
    <div class="chart-container">
        <h4>可调整部分内部配置: 当前 vs 历史目标</h4>
        <img src="{get_img_src('alloc_pie_hist')}" alt="Allocation Pie Chart (Historical Target - Rebal Portion)">
        <img src="{get_img_src('alloc_bar_hist')}" alt="Allocation Bar Chart (Historical Target - Rebal Portion)">
    </div>""" if image_filenames.get('alloc_pie_hist') else "<p><i>历史目标配置比较图表未生成。(Allocation comparison chart (Historical) not generated.)</i></p>" # Added fallback text

    drift_hist_html = f"""
    <div class="chart-container">
        <h4>可调整资产偏离分析 vs 历史目标</h4>
        <img src="{get_img_src('drift_hist')}" alt="Drift Analysis Chart (Historical Target - Rebalanceable)">
    </div>""" if image_filenames.get('drift_hist') else "<p><i>历史目标偏离分析图表未生成。(Drift analysis chart (Historical) not generated.)</i></p>" # Added fallback text

    sub_category_plot_html = f"""
    <div class="chart-container">
        <h4>子类别配置比较 vs 预定义目标</h4>
        <img src="{get_img_src('sub_category_alloc_predef')}" alt="Sub-Category Allocation (Predefined Target)">
    </div>""" if image_filenames.get('sub_category_alloc_predef') else "<p><i>子类别配置图表未生成。(Sub-category allocation chart not generated.)</i></p>"

    correlation_html = f"""
    <div class="chart-container">
        <h4>资产相关性</h4>
        <img src="{get_img_src('correlation')}" alt="Correlation Heatmap">
    </div>""" if image_filenames.get('correlation') else "<p><i>相关性热力图未生成。(Correlation heatmap not generated.)</i></p>"

    frontier_html = f"""
    <div class="chart-container">
        <h4>有效前沿</h4>
        <img src="{get_img_src('frontier')}" alt="Efficient Frontier Plot">
    </div>""" if image_filenames.get('frontier') else "<p><i>有效前沿图表未生成。(Efficient frontier plot not generated.)</i></p>"


    # --- HTML Template (Keep structure and CSS as is) ---
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>资产配置分析报告 - {timestamp}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; margin: 20px; color: #333; background-color: #f9f9f9; }}
        .container {{ max-width: 1000px; margin: 0 auto; background-color: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1, h2, h3, h4 {{ color: #1a1a1a; margin-top: 30px; padding-bottom: 10px; }}
        h1 {{ font-size: 2em; text-align: center; border-bottom: 2px solid #eee; margin-bottom: 20px; }}
        h2 {{ font-size: 1.6em; border-bottom: 1px solid #eee; }}
        h3 {{ font-size: 1.3em; border-bottom: none; color: #0056b3; }}
        h4 {{ font-size: 1.1em; font-weight: bold; text-align: center; margin-bottom: 5px; color: #333; }}
        pre {{ background-color: #f7f7f7; border: 1px solid #ddd; border-radius: 4px; padding: 15px; white-space: pre-wrap; word-wrap: break-word; font-family: Menlo, Monaco, Consolas, "Courier New", monospace; font-size: 0.9em; max-height: 600px; overflow-y: auto; line-height: 1.5; }}
        .chart-container {{ page-break-inside: avoid; margin-bottom: 30px; padding: 20px; border: 1px solid #eee; border-radius: 8px; background-color: #fff; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,0.05); }}
        .chart-container img {{ max-width: 95%; height: auto; display: block; margin: 15px auto; border: 1px solid #ddd; border-radius: 4px; background-color: #fff; /* Ensure white background for transparent PNGs */ }}
        hr {{ border: none; border-top: 1px solid #eee; margin: 40px 0; }}
        p {{ margin-bottom: 10px; }}
        .disclaimer {{ font-size: 0.85em; color: #777; margin-top: 40px; border-top: 1px solid #eee; padding-top: 20px; text-align: center; }}
        .section {{ margin-bottom: 40px; }}
        .fallback-text {{ font-style: italic; color: #888; text-align: center; margin-top: 10px; }}
        /* Improve image container layout for side-by-side plots if needed */
        .chart-pair {{ display: flex; flex-wrap: wrap; justify-content: space-around; align-items: flex-start; }}
        .chart-pair .chart-container {{ flex: 1 1 45%; /* Adjust basis/grow/shrink */ min-width: 300px; margin: 10px; }}

        @media (max-width: 768px) {{
            body {{ margin: 10px; }}
            .container {{ padding: 15px; }}
            h1 {{ font-size: 1.6em; }}
            h2 {{ font-size: 1.4em; }}
            h3 {{ font-size: 1.1em; }}
            .chart-container img {{ max-width: 100%; }}
            .chart-pair .chart-container {{ flex-basis: 100%; }} /* Stack on smaller screens */
        }}
        @media print {{
            body {{ margin: 0.5in; font-size: 10pt; background-color: #fff; }}
            .container {{ box-shadow: none; border: none; padding: 0; margin: 0; }}
            h1, h2, h3, h4 {{ page-break-after: avoid; color: #000; }}
            pre {{ max-height: none; overflow: visible; white-space: pre-wrap; border: 1px solid #ccc; background-color: #fff; }}
            .chart-container {{ border: none; padding: 0; margin-bottom: 15px; box-shadow: none; background-color: #fff; }}
            img {{ max-width: 100% !important; border: 1px solid #ccc; }}
            .disclaimer {{ display: none; }}
            a {{ text-decoration: none; color: #000; }}
            .chart-pair {{ display: block; }} /* Ensure pairs don't try flexbox */
            .chart-pair .chart-container {{ width: 100%; margin: 0 0 15px 0; }}
        }}
    </style>
</head>
<body>
<div class="container">
    <h1>资产配置分析报告 (Portfolio Analysis Report)</h1>
    <p style="text-align: center;"><strong>生成时间 (Generated Time):</strong> {timestamp}</p>
    <p style="text-align: center;"><strong>分析风险偏好 (Analysis Risk Profile):</strong> {risk_preference}</p>
    <hr>

    <div class="section">
        <h2>📊 可视化概览 (Visual Overview)</h2>

        <h3>配置比较 (可调整部分内部)</h3>
        <div class="chart-pair">
             {alloc_comp_predef_html if image_filenames.get('alloc_pie_predef') else '<div class="chart-container"><p class="fallback-text">预定义目标配置比较图表未生成。</p></div>'}
             {alloc_comp_hist_html if image_filenames.get('alloc_pie_hist') else '<div class="chart-container"><p class="fallback-text">历史目标配置比较图表未生成。</p></div>'}
        </div>

        <h3>配置偏离 (可调整部分)</h3>
         <div class="chart-pair">
            {drift_predef_html if image_filenames.get('drift_predef') else '<div class="chart-container"><p class="fallback-text">预定义目标偏离分析图表未生成。</p></div>'}
            {drift_hist_html if image_filenames.get('drift_hist') else '<div class="chart-container"><p class="fallback-text">历史目标偏离分析图表未生成。</p></div>'}
        </div>

        <h3>子类别配置</h3>
        {sub_category_plot_html if image_filenames.get('sub_category_alloc_predef') else '<div class="chart-container"><p class="fallback-text">子类别配置图表未生成。</p></div>'}


        <h3>相关性与有效前沿</h3>
         <div class="chart-pair">
            {correlation_html if image_filenames.get('correlation') else '<div class="chart-container"><p class="fallback-text">相关性热力图未生成。</p></div>'}
            {frontier_html if image_filenames.get('frontier') else '<div class="chart-container"><p class="fallback-text">有效前沿图表未生成。</p></div>'}
        </div>
    </div>

    <hr>

    <div class="section">
        <h2>📄 详细文本报告 (Detailed Text Report)</h2>
        <pre>{escaped_text_report}</pre>
    </div>

    <hr>
    <p class="disclaimer">免责声明：本报告仅供参考，不构成投资建议。投资有风险，决策需谨慎。<br>(Disclaimer: This report is for informational purposes only and does not constitute investment advice.)</p>
</div>
</body>
</html>
"""
    print("HTML report content generated.")
    return html_content

