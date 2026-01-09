"""
Markdown Context Generator

Generates a comprehensive, LLM-friendly markdown document capturing the
portfolio state, performance metrics, market environment, risk analysis,
cash flow history/forecast status, and system recommendations.

This is intentionally aligned with the HTML report's data source:
the unified `real_data` dictionary built in `real_report.py` to guarantee
consistency between markdown and HTML outputs.

Usage pattern:
    generator = MarkdownContextGenerator()
    md = generator.generate_markdown(real_data, consolidated_actions)
    generator.save_to_file(md, "output/Personal_Investment_Analysis_Context.md")

Notes:
- Gracefully handles missing fields by showing N/A where appropriate
- Avoids duplicating heavy computations; relies on values already present
- Keeps formatting AI-friendly (simple tables and bullet points)
"""

from __future__ import annotations
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


class MarkdownContextGenerator:
    """Generate a markdown context document from the real_data dict.

    All functions include type hints and docstrings and are safe against
    missing keys to ensure robust generation across environments.
    """

    currency_symbol = "¥"

    # ------------------------- formatting helpers ------------------------- #
    def format_currency(self, value: Any, precision: int = 0) -> str:
        """Format CNY currency values with thousands separator.

        Args:
            value: Number or string convertible to float
            precision: Decimal places

        Returns:
            Formatted currency string like "¥1,234" or "¥1,234.56"
        """
        try:
            if value in (None, "", "N/A"):
                return f"{self.currency_symbol}0"
            if isinstance(value, str):
                # Strip any prior currency formatting
                value = value.replace(",", "").replace(self.currency_symbol, "")
            num = float(value)
            fmt = f"{{:,.{precision}f}}".format(num)
            return f"{self.currency_symbol}{fmt}"
        except Exception:
            return f"{self.currency_symbol}{value}"

    def format_pct(self, value: Any, precision: int = 1, already_percent: bool = True) -> str:
        """Format a percentage value.

        Args:
            value: Number or string representing a percent. If numeric and
                   already_percent=False, will multiply by 100 first.
            precision: Decimal places
            already_percent: Whether the numeric value is already in percent
                              units (e.g., 12.3 for 12.3%). If False, assumes
                              a decimal (e.g., 0.123) and multiplies by 100.

        Returns:
            Formatted percent string like "12.3%" or "N/A"
        """
        try:
            if value in (None, "", "N/A"):
                return "N/A"
            if isinstance(value, str):
                # Accept strings like "4.12" or "4.12%" and normalize
                v = value.strip().rstrip("%")
                num = float(v)
            else:
                num = float(value)
            if not already_percent:
                num *= 100.0
            return f"{num:.{precision}f}%"
        except Exception:
            return "N/A"

    def format_xirr(self, value: Any) -> str:
        """Format XIRR values accommodating various input types.

        Accepts numeric (either decimal or percent) or string (possibly "N/A").
        Heuristic: if abs(value) <= 1.0, treat as decimal, else as percent.
        """
        if value in (None, "", "N/A"):
            return "N/A"
        try:
            if isinstance(value, str):
                v = value.strip().rstrip("%")
                num = float(v)
            else:
                num = float(value)
            if abs(num) <= 1.0:
                # likely decimal
                num *= 100.0
            return f"{num:.2f}%"
        except Exception:
            return "N/A"

    def generate_markdown_table(self, headers: List[str], rows: List[List[Any]]) -> str:
        """Generate a markdown table from headers and rows.

        Args:
            headers: Column headers
            rows: 2D row values

        Returns:
            Markdown string for the table
        """
        header_row = "| " + " | ".join(headers) + " |"
        separator = "|" + "|".join(["-" * (len(h) + 2) for h in headers]) + "|"
        data_rows = ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
        return "\n".join([header_row, separator] + data_rows)

    def safe_get(self, data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
        """Safely extract nested dictionary values.

        Args:
            data: Source dict
            keys: Path of keys to traverse
            default: Default if not found

        Returns:
            Extracted value or default
        """
        cur: Any = data
        for k in keys:
            if not isinstance(cur, dict) or k not in cur:
                return default
            cur = cur[k]
        return cur

    # --------------------------- core generation --------------------------- #
    def generate_markdown(
        self,
        real_data: Dict[str, Any],
        consolidated_actions: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Build the markdown content string based on the provided real_data.

        Args:
            real_data: Unified data dict produced by real_report.py
            consolidated_actions: Optional precomputed top priority actions

        Returns:
            Full markdown document as a string
        """
        lines: List[str] = []

        # Header
        gen_time = real_data.get("generation_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        data_as_of = gen_time.split(" ")[0]
        lines.append("# Personal Investment Analysis Context")
        lines.append(f"Generated: {gen_time}")
        lines.append(f"Data as of: {data_as_of}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # ============= 1. Portfolio State =============
        lines.append("## 1. Portfolio State")
        lines.append("")

        # 1.1 Current Holdings Overview
        rebalanceable = self.safe_get(real_data, "rebalancing_data", "rebalanceable_value", default=0.0)
        non_rebalanceable = self.safe_get(real_data, "rebalancing_data", "non_rebalanceable_value", default=0.0)
        last_month_change = real_data.get("last_month_change", 0.0)
        lines.append("### 1.1 Current Holdings Overview")
        lines.append("")
        lines.append(f"Rebalanceable Assets: {self.format_currency(rebalanceable)}")
        lines.append(f"Last Month Change: {self.format_pct(last_month_change, precision=2, already_percent=True)}")
        lines.append("")
        if non_rebalanceable:
            lines.append("Non-Rebalanceable Assets (excluded from analysis):")
            lines.append(f"- Total: {self.format_currency(non_rebalanceable)}")
            lines.append("")

        # 1.2 Asset Allocation (Top Level)
        lines.append("### 1.2 Asset Allocation (Top Level)")
        top_rows: List[List[Any]] = []
        top_table = self.safe_get(real_data, "rebalancing_data", "top_level_table", default=[]) or []
        # Filter out non-rebalanceable asset classes entirely (e.g., 保险, 房地产)
        for item in top_table:
            if not item.get("is_rebalanceable", False):
                continue
            name = item.get("asset_class", "?")
            cur_val = self.format_currency(item.get("current_value", 0))
            cur_pct = self.format_pct(item.get("current_pct", 0), precision=1, already_percent=True)
            tgt_pct = self.format_pct(item.get("target_pct", 0), precision=1, already_percent=True)
            drift = self.format_pct(item.get("drift", 0), precision=1, already_percent=True)
            gap_cny_val = (item.get("target_value", 0) or 0) - (item.get("current_value", 0) or 0)
            gap_cny = ("+" if gap_cny_val >= 0 else "-") + self.format_currency(abs(gap_cny_val))
            status = "Increase" if gap_cny_val > 0 else ("Reduce" if gap_cny_val < 0 else "Aligned")
            top_rows.append([name, cur_val, cur_pct, tgt_pct, drift, gap_cny, status])
        if top_rows:
            lines.append(self.generate_markdown_table(
                ["Asset Class", "Current Value", "Current %", "Target %", "Gap (%)", "Gap (CNY)", "Status"],
                top_rows
            ))
            lines.append("")

        # 1.3 Sub-Asset Class Breakdown (include ALL, filtered to rebalanceable only)
        sub_rows: List[List[Any]] = []
        sub_table = self.safe_get(real_data, "rebalancing_data", "sub_level_table", default=[]) or []
        # Include all sub-classes but only those under rebalanceable parents
        sub_table_sorted = sorted(sub_table, key=lambda x: abs(x.get("drift", 0)), reverse=True)
        for item in sub_table_sorted:
            if not item.get("is_rebalanceable", False):
                continue
            sub_rows.append([
                item.get("asset_class", "?"),
                item.get("sub_category", "?"),
                self.format_currency(item.get("current_value", 0)),
                self.format_pct(item.get("current_pct", 0), precision=1, already_percent=True),
                self.format_pct(item.get("target_pct", 0), precision=1, already_percent=True),
                self.format_pct(item.get("drift", 0), precision=1, already_percent=True)
            ])
        if sub_rows:
            lines.append("### 1.3 Sub-Asset Class Breakdown (All Rebalanceable)")
            lines.append(self.generate_markdown_table(
                ["Top Class", "Sub-Class", "Value", "% of Base", "Target %", "Drift"],
                sub_rows
            ))
            lines.append("")

        # 1.4 Asset Tier Allocation
        lines.append("### 1.4 Asset Tier Allocation")
        tier_analysis = real_data.get("tier_analysis", {})
        tier_table = tier_analysis.get("tier_table", [])
        
        tier_rows: List[List[Any]] = []
        if tier_table:
            # Sort tiers to ensure correct order
            tier_dict = {t['tier_key']: t for t in tier_table}
            display_order = ['tier_1_core', 'tier_2_diversification', 'tier_3_trading', 'unclassified']
            
            for key in display_order:
                t = tier_dict.get(key)
                if not t:
                    continue
                
                # Format drift
                drift_val = t.get('drift', 0)
                drift_str = self.format_pct(drift_val, precision=1, already_percent=False) # incoming is raw difference e.g., 5.0 for 5%? Wait, let's check builder.
                # In tier_analysis_builder.py: drift = current_pct - target_pct (items are already scaled 0-100? No, let's check builder again)
                # Builder: current_pct = val/total * 100. target_pct = target * 100. drift = current - target.
                # So they are already in 0-100 scale.
                
                # Markdown format_pct helper assumes:
                # if already_percent=True: 12.3 -> "12.3%"
                # if already_percent=False: 0.123 -> "12.3%"
                
                # Our tier values are already 0-100.
                
                tier_rows.append([
                    t.get('tier_name', key),
                    self.format_currency(t.get('current_value', 0)),
                    f"{t.get('current_pct', 0):.1f}%",
                    f"{t.get('target_pct', 0):.0f}%",
                    f"{drift_val:+.1f}%",
                    self.format_currency(t.get('total_pnl', 0)),
                    f"{self.format_currency(t.get('realized_pnl', 0))} / {self.format_currency(t.get('unrealized_pnl', 0))}",
                    f"{t.get('weighted_xirr', 0):.2f}%",
                    t.get('asset_count', 0)
                ])
                
            if tier_rows:
                lines.append(self.generate_markdown_table(
                    ["Tier", "Value", "Current %", "Target %", "Drift", "Total Profit", "Realized / Unrealized", "XIRR", "Assets"],
                    tier_rows
                ))
                lines.append("")
                lines.append("*Percentages calculated against Investment Assets (Rebalanceable Value) only.*")
                lines.append("*Note: '未分类 (Unclassified)' primarily contains unmapped Cash and Deposit accounts.*")
            else:
                lines.append("No tier analysis data available.")
        else:
             lines.append("No tier analysis data available.")
        lines.append("")

        # ============= 2. Performance Metrics =============
        lines.append("## 2. Performance Metrics")
        lines.append("")

        # 2.1 Overall Portfolio Performance
        overall_xirr = self.format_xirr(real_data.get("overall_xirr"))
        portfolio_growth = real_data.get("portfolio_growth", "N/A")
        true_twr = real_data.get("true_twr", "N/A")
        sharpe = real_data.get("sharpe_ratio", "N/A")
        
        lines.append("### 2.1 Overall Portfolio Performance (Lifetime)")
        lines.append(self.generate_markdown_table(
            ["Metric", "Value", "Description"],
            [
                ["Portfolio XIRR (Since Inception)", overall_xirr, "Annualized return including all cash flows"],
                ["Portfolio Growth", f"{portfolio_growth}%" if portfolio_growth != "N/A" else "N/A", "Cumulative return including deposits/withdrawals"],
                ["True TWR", f"{true_twr}%" if true_twr != "N/A" else "N/A", "Time-weighted return (cash flow adjusted)"],
                ["Sharpe Ratio", sharpe, "Risk-adjusted return metric"]
            ]
        ))
        lines.append("")

        # 2.1a Dual-Timeframe Performance Comparison (Lifetime vs 12-Month)
        dual_metrics = real_data.get("dual_metrics", {})
        if dual_metrics:
            lifetime_metrics = dual_metrics.get("lifetime", {})
            trailing_12m = dual_metrics.get("trailing_12m", {})
            
            if lifetime_metrics or trailing_12m:
                lines.append("### 2.1a Dual-Timeframe Performance Comparison")
                lines.append("")
                
                # Lifetime metrics
                if lifetime_metrics:
                    lines.append("#### Lifetime Performance (Since 2018)")
                    lifetime_xirr = self.format_xirr(lifetime_metrics.get("xirr"))
                    lifetime_growth = lifetime_metrics.get("portfolio_growth", "N/A")
                    lifetime_twr = lifetime_metrics.get("twr", "N/A")
                    lifetime_sharpe = lifetime_metrics.get("sharpe", "N/A")
                    
                    lines.append(self.generate_markdown_table(
                        ["Metric", "Value"],
                        [
                            ["XIRR", lifetime_xirr],
                            ["Portfolio Growth", f"{lifetime_growth}%" if lifetime_growth != "N/A" else "N/A"],
                            ["True TWR", f"{lifetime_twr}%" if lifetime_twr != "N/A" else "N/A"],
                            ["Sharpe Ratio", lifetime_sharpe]
                        ]
                    ))
                    lines.append("")
                
                # 12-Month metrics
                if trailing_12m:
                    lines.append("#### Trailing 12-Month Performance")
                    m12_xirr = trailing_12m.get("xirr", "N/A")
                    m12_growth = trailing_12m.get("portfolio_growth", "N/A")
                    m12_twr = trailing_12m.get("twr", "N/A")
                    m12_sharpe = trailing_12m.get("sharpe", "N/A")
                    
                    lines.append(self.generate_markdown_table(
                        ["Metric", "Value", "Note"],
                        [
                            ["XIRR", m12_xirr, "Limited by transaction data within 12-month window"],
                            ["Portfolio Growth", f"{m12_growth}%" if m12_growth != "N/A" else "N/A", "Simple return over period"],
                            ["True TWR", f"{m12_twr}%" if m12_twr != "N/A" else "N/A", "Adjusted for cash flow timing"],
                            ["Sharpe Ratio", m12_sharpe, "Risk-adjusted performance"]
                        ]
                    ))
                    lines.append("")
                    
                    # Interpretation
                    lines.append("**Interpretation:**")
                    lines.append("- **Lifetime vs 12-Month Comparison:** Compares long-term investment performance against recent performance.")
                    lines.append("- **Growth vs TWR Difference:** If TWR < Growth, significant net inflows occurred during the period.")
                    lines.append("- **12-Month XIRR Limitation:** Due to limited transaction history within 12 months, 999% often indicates insufficient data.")
                    lines.append("")

        # 2.2 Asset Class Performance (if available)
        top_perf = real_data.get("top_level_performance", []) or []
        if top_perf:
            perf_rows: List[List[Any]] = []
            for p in top_perf:
                cls = p.get("class_name", p.get("asset_class", "?"))
                # Exclude Real Estate from this section per requirement
                if str(cls) in {"Real Estate", "房地产"}:
                    continue
                perf_rows.append([
                    cls,
                    self.format_xirr(p.get("xirr")) if p.get("xirr") is not None else "N/A",
                    f"{p.get('portfolio_percentage', 0):.1f}%"
                ])
            if perf_rows:
                lines.append("### 2.2 Asset Class Performance (weighted XIRR where available)")
                lines.append(self.generate_markdown_table(["Asset Class", "XIRR", "% of Portfolio"], perf_rows))
                lines.append("")

        # ============= 3. Market Environment =============
        lines.append("## 3. Market Environment")
        lines.append("")
        regime = real_data.get("market_regime", {}) or {}
        market_snapshot = {}
        if regime:
            lines.append("### 3.1 Market Indicators (Raw Data)")
            # Pull numeric indicators from regime snapshot first
            market_snapshot = regime.get('market_data_snapshot', {}) or {}
        if not market_snapshot:
            # Fallback to market_thermometer structure if available
            thermo = real_data.get('market_thermometer', {}) or {}
            market_snapshot = {
                'shiller_pe': self.safe_get(thermo, 'shiller_pe', 'value'),
                'fear_greed': self.safe_get(thermo, 'fear_greed', 'value'),
                'vix': self.safe_get(thermo, 'vix', 'value'),
                'buffett_us': self.safe_get(thermo, 'buffett_us', 'value'),
                'buffett_china': self.safe_get(thermo, 'buffett_china', 'value'),
                'buffett_japan': self.safe_get(thermo, 'buffett_japan', 'value'),
                'buffett_europe': self.safe_get(thermo, 'buffett_europe', 'value'),
                'last_updated': thermo.get('last_updated')
            }
            lines.append("### 3.1 Market Indicators (Raw Data)")
        # Render numeric indicators (Thermometer core + Gold + Crypto)
        indicator_rows: List[List[Any]] = []
        # 3.1.a Equity/Macro indicators
        if market_snapshot:
            indicator_rows.append(["席勒市盈率 (Shiller P/E)", market_snapshot.get('shiller_pe', 'N/A')])
            indicator_rows.append(["恐惧与贪婪指数 (Fear & Greed)", market_snapshot.get('fear_greed', 'N/A')])
            indicator_rows.append(["VIX 波动率 (VIX)", market_snapshot.get('vix', 'N/A')])
            indicator_rows.append(["巴菲特指标-美国 (Buffett US)", market_snapshot.get('buffett_us', 'N/A')])
            indicator_rows.append(["巴菲特指标-中国 (Buffett China)", market_snapshot.get('buffett_china', 'N/A')])
            indicator_rows.append(["巴菲特指标-日本 (Buffett Japan)", market_snapshot.get('buffett_japan', 'N/A')])
            indicator_rows.append(["巴菲特指标-欧洲(英) (Buffett Europe)", market_snapshot.get('buffett_europe', 'N/A')])
            if market_snapshot.get('last_updated'):
                indicator_rows.append(["数据更新时间 (Last Updated)", market_snapshot.get('last_updated')])
        
        # 3.1.b Gold indicators from gold_analysis
        gold_analysis = real_data.get('gold_analysis', {}) or {}
        gold_ind = gold_analysis.get('indicators', {}) if isinstance(gold_analysis, dict) else {}
        if gold_ind:
            gvz_val = self.safe_get(gold_ind, 'gvz', 'value')
            gs_val = self.safe_get(gold_ind, 'gold_silver_ratio', 'value')
            spg_val = self.safe_get(gold_ind, 'sp500_gold_ratio', 'value')
            if gvz_val is not None:
                indicator_rows.append(["GVZ 黄金波动率 (GVZ)", gvz_val])
            if gs_val is not None:
                indicator_rows.append(["金银比 (Gold/Silver)", gs_val])
            if spg_val is not None:
                indicator_rows.append(["标普500/黄金 比值 (S&P/Gold)", spg_val])
            if gold_analysis.get('last_updated'):
                indicator_rows.append(["黄金指标更新时间 (Gold Last Updated)", gold_analysis.get('last_updated')])

        # 3.1.c Crypto indicators from crypto_analysis
        crypto_analysis = real_data.get('crypto_analysis', {}) or {}
        crypto_ind = crypto_analysis.get('indicators', {}) if isinstance(crypto_analysis, dict) else {}
        if crypto_ind:
            fng_val = self.safe_get(crypto_ind, 'crypto_fear_greed', 'value')
            btcqqq_val = self.safe_get(crypto_ind, 'btc_qqq_ratio', 'value')
            btc_vol = self.safe_get(crypto_ind, 'btc_volatility', 'value')
            eth_vol = self.safe_get(crypto_ind, 'eth_volatility', 'value')
            btc_eth = self.safe_get(crypto_ind, 'btc_eth_ratio', 'value')
            btc_dom = self.safe_get(crypto_ind, 'btc_dominance', 'value')
            if fng_val is not None:
                indicator_rows.append(["加密恐惧与贪婪 (Crypto F&G)", fng_val])
            if btcqqq_val is not None:
                indicator_rows.append(["BTC/QQQ 比值", btcqqq_val])
            if btc_vol is not None:
                indicator_rows.append(["BTC 30日波动率 (%)", btc_vol])
            if eth_vol is not None:
                indicator_rows.append(["ETH 30日波动率 (%)", eth_vol])
            if btc_eth is not None:
                indicator_rows.append(["BTC/ETH 比值", btc_eth])
            if btc_dom is not None:
                indicator_rows.append(["BTC 市值占比 (Dominance %)", btc_dom])
            if crypto_analysis.get('last_updated'):
                indicator_rows.append(["加密指标更新时间 (Crypto Last Updated)", crypto_analysis.get('last_updated')])

        if indicator_rows:
            lines.append(self.generate_markdown_table(["Indicator", "Value"], indicator_rows))
            lines.append("")
        # Optional: show regime name for context, without scores
        if regime:
            lines.append(f"当前市场状态 (Regime): {regime.get('regime_name_cn', 'Unknown')} ({regime.get('regime_name', 'Unknown')})")
            lines.append("")

        # ============= 4. 持仓明细 (Holdings Details) =============
        lines.append("## 4. 持仓明细 (Holdings Details)")
        asset_gains = real_data.get('asset_gains_data', {}) or {}
        holdings_rows = real_data.get('holdings', []) or []
        # Build holding period lookup from lifetime performance (authoritative source used by HTML)
        lifetime_perf = real_data.get('lifetime_performance_data', []) or []
        holding_days_lookup: Dict[str, int] = {}
        lifetime_lookup: Dict[str, Dict[str, Any]] = {}
        for perf in lifetime_perf:
            try:
                nm = str(perf.get('asset_name', '')).strip()
                asset_id = str(perf.get('asset_id', '')).strip()
                holding_days_lookup[nm] = int(perf.get('holding_period_days', 0) or 0)
                # Build comprehensive lookup for ticker, class, P/L and return
                perf_data = {
                    'asset_id': asset_id,
                    'asset_name': nm,
                    'asset_class': perf.get('asset_class'),  # Top-level class (e.g., Equity)
                    'total_pnl': perf.get('total_pnl'),
                    'total_return_pct': perf.get('total_return_pct'),
                    'xirr_pct': perf.get('xirr_pct')
                }
                # Index by both asset_name AND asset_id (to handle Employer_Stock_A vs Employer RSU mismatch)
                lifetime_lookup[nm] = perf_data
                if asset_id:
                    lifetime_lookup[asset_id] = perf_data
                    holding_days_lookup[asset_id] = int(perf.get('holding_period_days', 0) or 0)
            except Exception:
                continue

        def format_holding_period(days: int) -> str:
            try:
                d = int(days)
                if d >= 365:
                    return f"{d // 365}y {(d % 365) // 30}m"
                return f"{d // 30}m {d % 30}d"
            except Exception:
                return "N/A"

        # Build tier lookup map for easy access
        asset_tier_map = {}
        tier_details = real_data.get("tier_analysis", {}).get("tier_details", {})
        for tier_key, assets_list in tier_details.items():
            # Get display name for this tier
            tier_display = tier_key
            for t in real_data.get("tier_analysis", {}).get("tier_table", []):
                if t['tier_key'] == tier_key:
                    tier_display = t['tier_name']
                    break
            
            for asset in assets_list:
                # Map both ID and Name to be safe
                if asset.get('asset_id'):
                    asset_tier_map[str(asset.get('asset_id'))] = tier_display
                if asset.get('asset_name'):
                    asset_tier_map[str(asset.get('asset_name'))] = tier_display

        non_rebalanceable_top_names = {"房地产", "保险", "Real Estate", "Insurance"}
        if holdings_rows:
            # Traverse the flat table and reconstruct hierarchy using subtotal rows
            i = 0
            n = len(holdings_rows)
            def parse_number(s: Any) -> float:
                try:
                    if s is None:
                        return 0.0
                    if isinstance(s, (int, float)):
                        return float(s)
                    return float(str(s).replace(',', '').replace(self.currency_symbol, ''))
                except Exception:
                    return 0.0

            while i < n:
                row = holdings_rows[i]
                if row.get('is_subtotal') and row.get('subtotal_type') == 'top_class':
                    # Top class header
                    top_label = row.get('top_class', '')
                    # Extract display name like "📊 Equity 类别总计" -> "股票/Equity 类别总计" already localized; take first token after icon
                    top_name = top_label.replace('📊', '').replace('类别总计', '').strip()
                    # Skip non-rebalanceable classes from holdings details as requested
                    if top_name in non_rebalanceable_top_names:
                        # Advance i to next top_class subtotal and continue
                        jskip = i + 1
                        while jskip < n and not (holdings_rows[jskip].get('is_subtotal') and holdings_rows[jskip].get('subtotal_type') == 'top_class'):
                            jskip += 1
                        i = jskip
                        continue
                    top_mv = parse_number(row.get('market_value'))
                    top_pct = row.get('portfolio_percentage', '0.0') + '%'

                    # Initialize aggregate profit metrics for this top class
                    top_total_pnl = 0.0
                    top_total_cost = 0.0

                    # Compute weighted avg XIRR for this top class by scanning until next top_class subtotal
                    j = i + 1
                    xirr_weight_sum = 0.0
                    value_sum = 0.0
                    while j < n and not (holdings_rows[j].get('is_subtotal') and holdings_rows[j].get('subtotal_type') == 'top_class'):
                        rj = holdings_rows[j]
                        if not rj.get('is_subtotal'):
                            x = rj.get('xirr')
                            mv = parse_number(rj.get('market_value'))
                            if x is not None:
                                try:
                                    xv = float(x)
                                    xirr_weight_sum += xv * mv
                                    value_sum += mv
                                except Exception:
                                    pass
                        j += 1
                    top_weighted_xirr = f"{(xirr_weight_sum / value_sum):.2f}%" if value_sum > 0 else "N/A"

                    # Emit top class summary (placeholder profit metrics - will be calculated from sub-class aggregation)
                    lines.append(f"#### 大类: {top_name}")
                    lines.append(f"- 市值 (Market Value): {self.format_currency(top_mv)}")
                    lines.append(f"- 占总资产比例 (% of Portfolio): {top_pct}")
                    # Note: top_total_pnl and top_total_cost will be accumulated during sub-class iteration below
                    top_pnl_placeholder_line_idx = len(lines)  # Mark position for later update
                    lines.append(f"- 总盈亏 (Total Profit/Loss): [calculating...]")
                    lines.append(f"- 总收益率 (Total Return %): [calculating...]")
                    lines.append(f"- 加权平均XIRR (Weighted Avg. XIRR): {top_weighted_xirr}")

                    # Now iterate sub-classes within this top class
                    k = i + 1
                    while k < n and not (holdings_rows[k].get('is_subtotal') and holdings_rows[k].get('subtotal_type') == 'top_class'):
                        subrow = holdings_rows[k]
                        if subrow.get('is_subtotal') and subrow.get('subtotal_type') == 'sub_class':
                            sub_label = subrow.get('sub_class', '')
                            sub_name = sub_label.replace('📈', '').replace('小计', '').strip()
                            sub_mv = parse_number(subrow.get('market_value'))
                            sub_pct = subrow.get('portfolio_percentage', '0.0') + '%'

                            # Compute weighted avg XIRR and aggregate profit metrics for this sub-class
                            m = k + 1
                            xw = 0.0
                            sw = 0.0
                            sub_total_pnl = 0.0
                            sub_total_cost = 0.0
                            while m < n and not holdings_rows[m].get('is_subtotal'):
                                hr = holdings_rows[m]
                                x = hr.get('xirr')
                                mv = parse_number(hr.get('market_value'))
                                if x is not None:
                                    try:
                                        xv = float(x)
                                        xw += xv * mv
                                        sw += mv
                                    except Exception:
                                        pass
                                # Aggregate profit metrics
                                asset_name_raw = hr.get('asset_name', '')
                                # Remove leading whitespace first, then bullet characters
                                asset_name_sub = asset_name_raw.strip().lstrip('•●◦').strip()
                                # Use same matching logic as individual holdings
                                life_sub = lifetime_lookup.get(asset_name_sub)
                                if not life_sub:
                                    # Try matching by asset_id
                                    for key, data in lifetime_lookup.items():
                                        if data.get('asset_id') == asset_name_sub or data.get('asset_name') == asset_name_sub:
                                            life_sub = data
                                            break
                                if not life_sub:
                                    life_sub = {}
                                
                                total_pnl_sub = life_sub.get('total_pnl')
                                if isinstance(total_pnl_sub, (int, float)):
                                    sub_total_pnl += total_pnl_sub
                                    sub_total_cost += (mv - total_pnl_sub)
                                m += 1
                            sub_weighted_xirr = f"{(xw / sw):.2f}%" if sw > 0 else "N/A"
                            sub_profit_pct = f"{(sub_total_pnl / sub_total_cost * 100):.2f}%" if sub_total_cost > 0 else "N/A"
                            
                            # Accumulate to top class totals
                            top_total_pnl += sub_total_pnl
                            top_total_cost += sub_total_cost

                            # Emit sub-class summary
                            lines.append(f"  ##### 子类: {sub_name}")
                            lines.append(f"  - 市值: {self.format_currency(sub_mv)}")
                            lines.append(f"  - 占总资产比例: {sub_pct}")
                            lines.append(f"  - 总盈亏 (Total Profit/Loss): {self.format_currency(sub_total_pnl)}")
                            lines.append(f"  - 总收益率 (Total Return %): {sub_profit_pct}")
                            lines.append(f"  - 加权平均XIRR: {sub_weighted_xirr}")

                            # Emit individual holdings under this sub-class
                            h = k + 1
                            while h < n and not holdings_rows[h].get('is_subtotal'):
                                hrow = holdings_rows[h]
                                asset_name_disp = hrow.get('asset_name', '').strip()
                                # Remove bullet prefix if present
                                asset_name = asset_name_disp.lstrip('•').strip()
                                mv = parse_number(hrow.get('market_value'))
                                pct = hrow.get('portfolio_percentage', '0.0') + '%'
                                xirr_val = hrow.get('xirr')
                                xirr_str = self.format_xirr(xirr_val) if xirr_val is not None else "N/A"
                                # Gains and cost basis
                                gains = asset_gains.get(asset_name, {})
                                # Prefer lifetime total P/L and return pct (authoritative, same as Portfolio HTML)
                                # Try matching by asset_name first, then try as potential asset_id
                                life = lifetime_lookup.get(asset_name)
                                if not life:
                                    # Asset name might be an asset_id (e.g., Employer_Stock_A)
                                    # Check if any lifetime entry has matching asset_id
                                    for key, data in lifetime_lookup.items():
                                        if data.get('asset_id') == asset_name or data.get('asset_name') == asset_name:
                                            life = data
                                            break
                                if not life:
                                    life = {}
                                
                                total_pnl = life.get('total_pnl')
                                return_pct = life.get('total_return_pct')
                                # Fallback to unrealized for P/L if lifetime missing
                                if total_pnl is None:
                                    total_pnl = gains.get('total_gains') if isinstance(gains, dict) else None
                                # Derive cost basis from P/L if possible (mv - pnl) as approximate; may be N/A
                                if isinstance(total_pnl, (int, float)):
                                    cost_basis = mv - total_pnl
                                else:
                                    cost_basis = None
                                # Holding period from lifetime performance data
                                hold_days = holding_days_lookup.get(asset_name)
                                if hold_days is None and life:
                                    # Try with asset_id
                                    hold_days = holding_days_lookup.get(life.get('asset_id', ''))
                                hold_str = format_holding_period(hold_days) if hold_days is not None else "N/A"
                                # Ticker/Asset_ID and Asset Class from lifetime data mapping
                                ticker = life.get('asset_id') if life else None
                                asset_class_display = life.get('asset_class') if life else None
                                
                                # Lookup Tier
                                tier_name_display = asset_tier_map.get(asset_name)
                                if not tier_name_display and ticker:
                                    tier_name_display = asset_tier_map.get(str(ticker))
                                if not tier_name_display:
                                    tier_name_display = "Unclassified"

                                # Emit asset block
                                lines.append(f"    - 资产: {asset_name}")
                                lines.append(f"      - 资产代码 (Ticker): {ticker if ticker else 'N/A'}")
                                lines.append(f"      - Asset Tier: {tier_name_display}")
                                lines.append(f"      - Asset Class: {asset_class_display if asset_class_display else top_name}")
                                lines.append(f"      - 当前市值: {self.format_currency(mv)}")
                                lines.append(f"      - 持仓成本 (Cost Basis): {self.format_currency(cost_basis) if cost_basis is not None else 'N/A'}")
                                lines.append(f"      - 总盈亏 (Total Profit/Loss): {self.format_currency(total_pnl) if isinstance(total_pnl, (int, float)) else 'N/A'}")
                                lines.append(f"      - 总收益率 (Return %): {self.format_pct(return_pct, precision=2, already_percent=True) if return_pct is not None else 'N/A'}")
                                lines.append(f"      - 年化收益率 (XIRR): {xirr_str}")
                                lines.append(f"      - 占总资产比例: {pct}")
                                lines.append(f"      - 持有状态: {hrow.get('status', 'Active')}")
                                lines.append(f"      - 持有时间: {hold_str}")
                                h += 1
                            k = h
                            continue
                        k += 1
                    
                    # After processing all sub-classes, update top class profit metrics
                    top_profit_pct = f"{(top_total_pnl / top_total_cost * 100):.2f}%" if top_total_cost > 0 else "N/A"
                    lines[top_pnl_placeholder_line_idx] = f"- 总盈亏 (Total Profit/Loss): {self.format_currency(top_total_pnl)}"
                    lines[top_pnl_placeholder_line_idx + 1] = f"- 总收益率 (Total Return %): {top_profit_pct}"
                    
                    i = k
                    continue
                i += 1
        else:
            lines.append("No holdings data available")
        lines.append("")
        # Sections 4-6 (Risk Analysis, Cash Flow, Recommendations) intentionally omitted per spec

        # Footer
        lines.append("---")
        lines.append("Generated by Personal Investment System v2.0")

        return "\n".join(lines)

    def save_to_file(self, markdown: str, output_path: str) -> None:
        """Persist markdown content to a file.

        Args:
            markdown: The markdown content string
            output_path: Path to write to
        """
        import os

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        logger.info(f"📝 Markdown context generated: {output_path}")
