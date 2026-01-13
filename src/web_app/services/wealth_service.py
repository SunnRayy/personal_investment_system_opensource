import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List

# Import FinancialAnalyzer
try:
    from src.financial_analysis.analyzer import FinancialAnalyzer
    from src.data_manager.historical_manager import HistoricalDataManager
except ImportError:
    # Handle potentially different import paths in tests or specific contexts
    import sys
    import os
    sys.path.append(os.getcwd())
    from src.financial_analysis.analyzer import FinancialAnalyzer
    from src.data_manager.historical_manager import HistoricalDataManager

logger = logging.getLogger(__name__)

class WealthService:
    """
    Service layer for the Wealth Dashboard.
    Orchestrates data retrieval from FinancialAnalyzer and serializes it for the API.
    """

    def __init__(self, config_dir: str = 'config'):
        self.config_dir = config_dir
        self.analyzer = FinancialAnalyzer(config_dir=config_dir)
        # We run analysis on init or on demand? On demand is better for freshness, but caching is wise.
        self._analysis_cache = {}
        self._cache_valid = False

    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Retrieves comprehensive dashboard data including Net Worth, Cash Flow, and Expenses.
        """
        logger.info("Fetching dashboard data...")
        
        # In a real app, check cache timestamp. For now, we run every time or simple in-memory cache.
        # analysis_results = self.analyzer.run_analysis()
        # Since run_analysis implies full re-calculation, we might want to be selective if performance is an issue.
        # But for this scale, it's fine.
        
        try:
            results = self.analyzer.run_analysis()
            
            # Serialize for API
            response_data = {
                'summary': self._extract_summary_kpis(results),
                'balance_sheet': self._process_balance_sheet_data(results.get('balance_sheet', {})),
                'cash_flow': self._process_cash_flow_data(results.get('cash_flow', {})),
                'investment': self._process_investment_data(results.get('investment', {})),
                'forecast': self._generate_forecast_data(), # NEW
                'historical': self._process_historical_data(results.get('historical_performance', {}))
            }
            return response_data
        except Exception as e:
            logger.error(f"Error generating dashboard data: {e}", exc_info=True)
            return {'error': str(e)}

    def _extract_summary_kpis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts high-level KPIs for the dashboard header.
        Now focuses on YTD metrics with YoY % comparison.
        """
        # Get adjusted monthly_df for accurate calculations
        raw_monthly_df = self.analyzer.monthly_df
        adjusted_df = self._get_adjusted_monthly_df(raw_monthly_df)
        
        # Calculate YTD metrics using adjusted data
        ytd_metrics = self._calculate_ytd_metrics(adjusted_df)
        
        return ytd_metrics

    def _process_balance_sheet_data(self, bs_results: Dict[str, Any]) -> Dict[str, Any]:
        """Process balance sheet results into chart-ready format."""
        
        # 1. Net Worth Trend
        trends = bs_results.get('trends', {})
        trend_df = trends.get('trend_data')

        if isinstance(trend_df, pd.DataFrame) and not trend_df.empty:
            pass # Systematic fixes in calculators.py should handle this now

        trend_chart = self._serialize_df_to_chart_data(
            trend_df, 
            label_col='index', 
            data_cols=['Total_Assets_Calc_CNY', 'Total_Liabilities_Calc_CNY', 'Net_Worth_Calc_CNY']
        ) if isinstance(trend_df, pd.DataFrame) else {}

        # 2. Allocation
        allocation = bs_results.get('allocation', {})
        asset_alloc = allocation.get('asset_allocation', {})
        liability_alloc = allocation.get('liability_allocation', {})
        
        # Convert dict to simple lists for charts
        asset_labels = list(asset_alloc.keys())
        asset_values = [v['value'] for v in asset_alloc.values()]
        
        # 3. Ratios
        ratios_df = bs_results.get('ratios')
        ratios_chart = self._serialize_df_to_chart_data(
            ratios_df,
            label_col='index',
            data_cols=['Debt_to_Asset_Ratio', 'Liquidity_Ratio']
        ) if isinstance(ratios_df, pd.DataFrame) else {}

        return {
            'trend_chart': trend_chart,
            'asset_allocation': {
                'labels': asset_labels,
                'data': asset_values
            },
            'ratios_chart': ratios_chart,
            'kpis': {
                'total_assets': self._fmt_currency(allocation.get('total_assets', 0)),
                'total_liabilities': self._fmt_currency(allocation.get('total_liabilities', 0)),
                'liability_to_asset': self._fmt_percent(trends.get('end_liabilities', 0) / trends.get('end_assets', 1))
            }
        }

    def _process_cash_flow_data(self, cf_results: Dict[str, Any]) -> Dict[str, Any]:
        """Process cash flow results."""
        
        # 1. Get ADJUSTED monthly_df for all trend analyses
        raw_monthly_df = self.analyzer.monthly_df
        adjusted_df = self._get_adjusted_monthly_df(raw_monthly_df)

        # 2. Income Trends
        income_trends = cf_results.get('income_trends', {})
        income_df = income_trends.get('trend_data')
        income_chart = self._serialize_df_to_chart_data(income_df, label_col='index') if isinstance(income_df, pd.DataFrame) else {}
        
        # Detailed Income Source Trend (Stacked)
        income_source_chart = {}
        if adjusted_df is not None and not adjusted_df.empty:
            income_cols = [
                'Income_Salary_CNY', 'Income_RSU_CNY', 'Income_Bonus_CNY', 
                'Income_Benefit_CNY', 'Income_HousingFund_CNY', 'Income_Other_CNY'
            ]
            available_inc_cols = [c for c in income_cols if c in adjusted_df.columns]
            if available_inc_cols:
                income_source_chart = self._serialize_df_to_chart_data(
                    adjusted_df, label_col='index', data_cols=available_inc_cols
                )
        
        combined_chart = {}
        if adjusted_df is not None and not adjusted_df.empty:
            combined_cols = ['Total_Income_Calc_CNY', 'Total_Expense_Calc_CNY', 'Total_Investment_Calc_CNY']
            available_cols = [c for c in combined_cols if c in adjusted_df.columns]
            if available_cols:
                combined_chart = self._serialize_df_to_chart_data(
                    adjusted_df, label_col='index', data_cols=available_cols
                )
        
        # 3. Expense Trends - Include Essential/NonEssential for stacked chart
        expense_trends = cf_results.get('expense_trends', {})
        expense_df = expense_trends.get('trend_data')
        
        # Detailed Expense Category Trend
        expense_cat_chart = {}
        if adjusted_df is not None and not adjusted_df.empty:
            expense_cols = [col for col in adjusted_df.columns if col.startswith('Expense_') and 'Total' not in col and 'Calc' not in col]
            # Add non-investment outflows
            outflow_cols = [col for col in adjusted_df.columns if col.startswith('Outflow_') and not col.startswith('Outflow_Invest_')]
            available_exp_cols = expense_cols + outflow_cols
            if available_exp_cols:
                expense_cat_chart = self._serialize_df_to_chart_data(
                    adjusted_df, label_col='index', data_cols=available_exp_cols
                )

        # 4. Investment Breakdown Trend (Filter out USD duplicates)
        investment_cat_chart = {}
        if adjusted_df is not None and not adjusted_df.empty:
            invest_cols = [col for col in adjusted_df.columns 
                           if col.startswith('Outflow_Invest_') 
                           and 'Total' not in col 
                           and 'Calc' not in col
                           and not col.endswith('_USD')  # Exclude USD duplicates
                           and '_FromUSD' not in col]   # Exclude converted duplicates
            if invest_cols:
                investment_cat_chart = self._serialize_df_to_chart_data(
                    adjusted_df, label_col='index', data_cols=invest_cols
                )

        expense_chart = self._serialize_df_to_chart_data(expense_df, label_col='index') if isinstance(expense_df, pd.DataFrame) else {}
        
        # Stacked bar chart (Essential vs NonEssential breakdown)
        expense_stacked_chart = {}
        if isinstance(expense_df, pd.DataFrame) and not expense_df.empty:
            stacked_cols = ['Essential_Expense_Calc', 'NonEssential_Expense_Calc']
            available_stacked_cols = [c for c in stacked_cols if c in expense_df.columns]
            if available_stacked_cols:
                expense_stacked_chart = self._serialize_df_to_chart_data(
                    expense_df, label_col='index', data_cols=available_stacked_cols
                )
        
        # 4. Expense Breakdown (pie chart - top categories)
        expense_cats = cf_results.get('expense_categories', {})
        sorted_cats = sorted(expense_cats.items(), key=lambda x: x[1]['value'], reverse=True)
        top_cats = sorted_cats[:6]
        cat_labels = [k for k, v in top_cats]
        cat_values = [v['value'] for k, v in top_cats]
        
        # 5. Cash Flow Overview
        cf_overview = cf_results.get('cash_flow_overview', {})
        net_cf_series = cf_overview.get('net_cash_flow_trend')
        if isinstance(net_cf_series, pd.Series):
            net_cf_df = net_cf_series.to_frame(name='Net_Cash_Flow')
            net_cf_chart = self._serialize_df_to_chart_data(net_cf_df, label_col='index')
        else:
            net_cf_chart = {}

        # 6. Period Comparisons (using adjusted data)
        comparisons = self._calculate_period_comparisons(adjusted_df)
        
        # 7. Income Sources (from cash_flow analysis)
        income_sources = cf_results.get('income_sources', {})
        income_sources_chart = {
            'labels': list(income_sources.keys()),
            'values': [v.get('value', 0) for v in income_sources.values()]
        }
        income_sources_yoy = self._calculate_income_source_yoy(adjusted_df) # NEW YoY comparison for sources

        return {
            'income_chart': income_chart,
            'expense_chart': expense_chart,
            'combined_chart': combined_chart,  # Now uses ADJUSTED data
            'income_source_chart': income_source_chart,
            'expense_cat_chart': expense_cat_chart,
            'investment_cat_chart': investment_cat_chart,
            'expense_stacked_chart': expense_stacked_chart,
            'expense_breakdown': {
                'labels': cat_labels,
                'data': cat_values
            },
            'ytd_expense_breakdown': self._calculate_ytd_expense_breakdown(adjusted_df), # NEW YTD Breakdown with YoY
            'net_cash_flow_chart': net_cf_chart,
            'income_sources': income_sources_chart,  
            'income_sources_yoy': income_sources_yoy, # NEW
            'comparisons': comparisons,  # NEW: MoM, QoQ, YTD, L12M
            'data_adjusted': True,  # Flag to indicate adjustments applied
            'kpis': {
                'monthly_avg_income': self._fmt_currency(income_trends.get('average_income', 0)),
                'monthly_avg_expense': self._fmt_currency(expense_trends.get('average_expense', 0)),
                'savings_rate': self._fmt_percent(cf_overview.get('average_savings_rate', 0))
            }
        }

    def _process_investment_data(self, inv_results: Dict[str, Any]) -> Dict[str, Any]:
        """Process investment analysis results."""
        # This will depend on what analyze_investments returns exactly
        # Assuming typical structure or placeholders
        return {
            'status': inv_results.get('status', 'unknown')
        }
        
    def _process_historical_data(self, hist_results: Dict[str, Any]) -> Dict[str, Any]:
        """Process historical performance data."""
        return {}

    def _get_adjusted_monthly_df(self, monthly_df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply data cleaning rules to monthly_df for trend analysis.
        Excludes: Work Reimbursements + Aug 2020 Property Purchase outliers.
        """
        if monthly_df is None or monthly_df.empty:
            return pd.DataFrame()
        
        df = monthly_df.copy()
        
        # Rule 1: Subtract Income Reimbursements
        if 'Income_Reimbursement_CNY' in df.columns and 'Total_Income_Calc_CNY' in df.columns:
            df['Total_Income_Calc_CNY'] = df['Total_Income_Calc_CNY'] - df['Income_Reimbursement_CNY'].fillna(0)
            logger.debug("Applied adjustment: Subtracted Income_Reimbursement_CNY from Total Income")
        
        # Rule 2: Subtract Reimbursable Expenses
        if 'Expense_Reimbursable_CNY' in df.columns and 'Total_Expense_Calc_CNY' in df.columns:
            df['Total_Expense_Calc_CNY'] = df['Total_Expense_Calc_CNY'] - df['Expense_Reimbursable_CNY'].fillna(0)
            logger.debug("Applied adjustment: Subtracted Expense_Reimbursable_CNY from Total Expense")
        
        # Rule 3 & 4: Aug 2020 Property Purchase Outliers
        anomaly_date = pd.Timestamp('2020-08-31')
        if anomaly_date in df.index:
            # Income: Subtract 880k from Income_Other_CNY contribution
            if 'Income_Other_CNY' in df.columns:
                orig_val = df.loc[anomaly_date, 'Income_Other_CNY']
                if pd.notna(orig_val) and orig_val > 500000:
                    df.loc[anomaly_date, 'Total_Income_Calc_CNY'] -= 880000
                    logger.debug(f"Applied adjustment: Subtracted 880k from Aug 2020 Income")
            
            # Expense: Subtract 928,505 from Expense_FamilyTemp_CNY contribution (corrected value)
            if 'Expense_FamilyTemp_CNY' in df.columns:
                orig_val = df.loc[anomaly_date, 'Expense_FamilyTemp_CNY']
                if pd.notna(orig_val) and orig_val > 500000:
                    df.loc[anomaly_date, 'Total_Expense_Calc_CNY'] -= 928505
                    logger.debug(f"Applied adjustment: Subtracted 928,505 from Aug 2020 Expense")
        
        return df

    def _calculate_period_comparisons(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate period comparison metrics: MoM, QoQ, YTD, L12M.
        Returns dict with percentage changes for income/expense/savings.
        """
        if df is None or df.empty or 'Total_Income_Calc_CNY' not in df.columns:
            return {}
        
        now = pd.Timestamp.now()
        current_month = now.replace(day=1) - pd.DateOffset(months=1)  # Use last complete month
        
        comparisons = {}
        
        # Helper to safely get sum for a period
        def period_sum(start, end, col):
            mask = (df.index >= start) & (df.index <= end)
            return df.loc[mask, col].sum() if mask.any() else 0
        
        # MoM: Current Month vs Previous Month
        prev_month = current_month - pd.DateOffset(months=1)
        cur_m_inc = period_sum(current_month, current_month + pd.DateOffset(months=1) - pd.Timedelta(days=1), 'Total_Income_Calc_CNY')
        prev_m_inc = period_sum(prev_month, prev_month + pd.DateOffset(months=1) - pd.Timedelta(days=1), 'Total_Income_Calc_CNY')
        cur_m_exp = period_sum(current_month, current_month + pd.DateOffset(months=1) - pd.Timedelta(days=1), 'Total_Expense_Calc_CNY')
        prev_m_exp = period_sum(prev_month, prev_month + pd.DateOffset(months=1) - pd.Timedelta(days=1), 'Total_Expense_Calc_CNY')
        
        # MoM
        cur_m_inv = period_sum(current_month, current_month + pd.DateOffset(months=1) - pd.Timedelta(days=1), 'Total_Investment_Calc_CNY')
        prev_m_inv = period_sum(prev_month, prev_month + pd.DateOffset(months=1) - pd.Timedelta(days=1), 'Total_Investment_Calc_CNY')
        comparisons['mom'] = {
            'income_pct': ((cur_m_inc - prev_m_inc) / prev_m_inc * 100) if prev_m_inc else 0,
            'expense_pct': ((cur_m_exp - prev_m_exp) / prev_m_exp * 100) if prev_m_exp else 0,
            'investment_pct': ((cur_m_inv - prev_m_inv) / prev_m_inv * 100) if prev_m_inv else 0,
            'current_income': cur_m_inc,
            'current_expense': cur_m_exp
        }
        
        # QoQ: Current Quarter vs Previous Quarter
        cur_q_start = pd.Timestamp(now.year, ((now.month - 1) // 3) * 3 + 1, 1) - pd.DateOffset(months=3)
        cur_q_end = cur_q_start + pd.DateOffset(months=3) - pd.Timedelta(days=1)
        prev_q_start = cur_q_start - pd.DateOffset(months=3)
        prev_q_end = prev_q_start + pd.DateOffset(months=3) - pd.Timedelta(days=1)
        
        cur_q_inc = period_sum(cur_q_start, cur_q_end, 'Total_Income_Calc_CNY')
        prev_q_inc = period_sum(prev_q_start, prev_q_end, 'Total_Income_Calc_CNY')
        cur_q_exp = period_sum(cur_q_start, cur_q_end, 'Total_Expense_Calc_CNY')
        prev_q_exp = period_sum(prev_q_start, prev_q_end, 'Total_Expense_Calc_CNY')
        cur_q_inv = period_sum(cur_q_start, cur_q_end, 'Total_Investment_Calc_CNY')
        prev_q_inv = period_sum(prev_q_start, prev_q_end, 'Total_Investment_Calc_CNY')
        
        comparisons['qoq'] = {
            'income_pct': ((cur_q_inc - prev_q_inc) / prev_q_inc * 100) if prev_q_inc else 0,
            'expense_pct': ((cur_q_exp - prev_q_exp) / prev_q_exp * 100) if prev_q_exp else 0,
            'investment_pct': ((cur_q_inv - prev_q_inv) / prev_q_inv * 100) if prev_q_inv else 0,
            'quarter': f"Q{((now.month - 1) // 3)}"
        }
        
        # YTD: This Year vs Last Year Same Period
        ytd_start = pd.Timestamp(now.year, 1, 1)
        ytd_end = current_month + pd.DateOffset(months=1) - pd.Timedelta(days=1)
        ly_ytd_start = pd.Timestamp(now.year - 1, 1, 1)
        ly_ytd_end = pd.Timestamp(now.year - 1, current_month.month, 1) + pd.DateOffset(months=1) - pd.Timedelta(days=1)
        
        ytd_inc = period_sum(ytd_start, ytd_end, 'Total_Income_Calc_CNY')
        ly_ytd_inc = period_sum(ly_ytd_start, ly_ytd_end, 'Total_Income_Calc_CNY')
        ytd_exp = period_sum(ytd_start, ytd_end, 'Total_Expense_Calc_CNY')
        ly_ytd_exp = period_sum(ly_ytd_start, ly_ytd_end, 'Total_Expense_Calc_CNY')
        ytd_inv = period_sum(ytd_start, ytd_end, 'Total_Investment_Calc_CNY')
        ly_ytd_inv = period_sum(ly_ytd_start, ly_ytd_end, 'Total_Investment_Calc_CNY')
        
        comparisons['ytd'] = {
            'income_pct': ((ytd_inc - ly_ytd_inc) / ly_ytd_inc * 100) if ly_ytd_inc else 0,
            'expense_pct': ((ytd_exp - ly_ytd_exp) / ly_ytd_exp * 100) if ly_ytd_exp else 0,
            'investment_pct': ((ytd_inv - ly_ytd_inv) / ly_ytd_inv * 100) if ly_ytd_inv else 0,
            'ytd_income': ytd_inc,
            'ytd_expense': ytd_exp
        }
        
        # L12M: Last 12 Months vs Previous 12 Months
        l12m_end = current_month + pd.DateOffset(months=1) - pd.Timedelta(days=1)
        l12m_start = current_month - pd.DateOffset(months=11)
        p12m_end = l12m_start - pd.Timedelta(days=1)
        p12m_start = l12m_start - pd.DateOffset(months=12)
        
        l12m_inc = period_sum(l12m_start, l12m_end, 'Total_Income_Calc_CNY')
        p12m_inc = period_sum(p12m_start, p12m_end, 'Total_Income_Calc_CNY')
        l12m_exp = period_sum(l12m_start, l12m_end, 'Total_Expense_Calc_CNY')
        p12m_exp = period_sum(p12m_start, p12m_end, 'Total_Expense_Calc_CNY')
        l12m_inv = period_sum(l12m_start, l12m_end, 'Total_Investment_Calc_CNY')
        p12m_inv = period_sum(p12m_start, p12m_end, 'Total_Investment_Calc_CNY')
        
        comparisons['l12m'] = {
            'income_pct': ((l12m_inc - p12m_inc) / p12m_inc * 100) if p12m_inc else 0,
            'expense_pct': ((l12m_exp - p12m_exp) / p12m_exp * 100) if p12m_exp else 0,
            'investment_pct': ((l12m_inv - p12m_inv) / p12m_inv * 100) if p12m_inv else 0,
            'total_income': l12m_inc,
            'total_expense': l12m_exp,
            'total_savings': l12m_inc - l12m_exp - l12m_inv
        }
        
        return comparisons

    def _calculate_ytd_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate YTD metrics for KPI cards: Income, Expense, Investment, Net Cash Flow.
        Each includes absolute value and YoY % comparison with previous year.
        Systematically sums specific authoritative columns to avoid double-counting.
        """
        if df is None or df.empty:
            return {
                'ytd_income': '--', 'ytd_income_yoy': '--',
                'ytd_expense': '--', 'ytd_expense_yoy': '--',
                'ytd_investment': '--', 'ytd_investment_yoy': '--',
                'ytd_net_cf': '--', 'ytd_net_cf_yoy': '--'
            }
        
        now = pd.Timestamp.now()
        current_year = now.year
        last_year = current_year - 1
        current_month = now.month
        
        # Explicit allow list
        income_cols = [
            'Income_Salary_CNY', 
            'Income_Bonus_CNY', 
            'Income_RSU_CNY',       # Use CNY version (calculated from vested shares * price * fx)
            'Income_Benefit_CNY',
            'Income_HousingFund_CNY',
            'Income_Other_CNY',
            'Income_Passive_Dividend_CNY',
            'Income_Passive_Interest_CNY'
        ]

        def get_sums(year, month):
            start = pd.Timestamp(year, 1, 1)
            end = pd.Timestamp(year, month, 1) + pd.DateOffset(months=1) - pd.Timedelta(days=1)
            mask = (df.index >= start) & (df.index <= end)
            if not mask.any():
                return 0, 0, 0
            
            # 1. Income (Selective)
            inc = df.loc[mask, [c for c in income_cols if c in df.columns]].sum().sum()
            
            # 2. Expense (Total)
            exp = df.loc[mask, 'Total_Expense_Calc_CNY'].sum() if 'Total_Expense_Calc_CNY' in df.columns else 0
            
            # 3. Investment (Total)
            inv = df.loc[mask, 'Total_Investment_Calc_CNY'].sum() if 'Total_Investment_Calc_CNY' in df.columns else 0
            
            return inc, exp, inv

        ytd_inc, ytd_exp, ytd_inv = get_sums(current_year, current_month)
        ytd_net = ytd_inc - ytd_exp - ytd_inv
        
        prev_inc, prev_exp, prev_inv = get_sums(last_year, current_month)
        prev_net = prev_inc - prev_exp - prev_inv
        
        # Calculate YoY %
        def yoy_pct(current, previous):
            if previous == 0: return 0
            return ((current - previous) / abs(previous)) * 100
        
        # Format helper
        def fmt_yoy(pct):
            sign = '+' if pct >= 0 else ''
            return f"{sign}{pct:.1f}%"
        
        return {
            'ytd_income': self._fmt_currency(ytd_inc),
            'ytd_income_yoy': fmt_yoy(yoy_pct(ytd_inc, prev_inc)),
            'ytd_expense': self._fmt_currency(ytd_exp),
            'ytd_expense_yoy': fmt_yoy(yoy_pct(ytd_exp, prev_exp)),
            'ytd_investment': self._fmt_currency(ytd_inv),
            'ytd_investment_yoy': fmt_yoy(yoy_pct(ytd_inv, prev_inv)),
            'ytd_net_cf': self._fmt_currency(ytd_net),
            'ytd_net_cf_yoy': fmt_yoy(yoy_pct(ytd_net, prev_net))
        }

    def _calculate_ytd_expense_breakdown(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate YTD expense breakdown by category with YoY comparison.
        """
        if df is None or df.empty:
            return {}
            
        now = pd.Timestamp.now()
        current_year = now.year
        last_year = current_year - 1
        current_month = now.month
        
        # Identify expense columns
        exp_cols = [c for c in df.columns if c.startswith('Expense_') and 'Total' not in c and 'Calc' not in c]
        
        # Helper to sum columns for a period
        def get_sums(year, month):
            start = pd.Timestamp(year, 1, 1)
            end = pd.Timestamp(year, month, 1) + pd.DateOffset(months=1) - pd.Timedelta(days=1)
            mask = (df.index >= start) & (df.index <= end)
            if not mask.any():
                return pd.Series(0, index=exp_cols)
            return df.loc[mask, exp_cols].sum()
            
        current_ytd = get_sums(current_year, current_month)
        last_ytd = get_sums(last_year, current_month)
        
        result = {}
        total_curr = current_ytd.sum()
        total_last = last_ytd.sum()
        
        for cat in exp_cols:
            curr_val = current_ytd[cat]
            prev_val = last_ytd[cat]
            
            # Clean category name
            clean_name = cat.replace('Expense_', '').replace('_CNY', '')
            
            # Absolute value YoY %
            yoy = ((curr_val - prev_val) / abs(prev_val) * 100) if prev_val != 0 else 0
            
            # Percentage of total spending
            curr_pct = (curr_val / total_curr * 100) if total_curr > 0 else 0
            last_pct = (prev_val / total_last * 100) if total_last > 0 else 0
            
            # YoY change in percentage points (e.g., was 30%, now 25% = -5pp)
            pct_yoy = curr_pct - last_pct
            
            result[clean_name] = {
                'value': float(curr_val),
                'percentage': float(curr_pct),
                'last_pct': float(last_pct),
                'pct_yoy': float(pct_yoy),  # Percentage point change
                'pct_yoy_str': f"{'+' if pct_yoy >= 0 else ''}{pct_yoy:.1f}pp",
                'yoy': float(yoy),
                'yoy_str': f"{'+' if yoy >= 0 else ''}{yoy:.1f}%" if prev_val != 0 else 'NEW'
            }
            
        return result

    def _generate_forecast_data(self) -> Dict[str, Any]:
        """
        Generate 12-month financial forecast using SARIMA.
        DISABLED for performance. Returns empty structure or placeholder.
        """
        try:
            # from src.financial_analysis.cash_flow_forecaster import CashFlowForecaster
            # forecaster = CashFlowForecaster(self.analyzer.data_manager)
            # forecaster.fetch_and_process_historical_data()
            # forecaster.fit_sarima_models(seasonal_period=12)
            # forecast_df = forecaster.forecast(periods=12, alpha=0.10)
            
            # # Formatting dates for labels
            # dates = [d.strftime('%Y-%m') for d in forecast_df.index]
            
            # return {
            #     'labels': dates,
            #     'income': forecast_df['Income_Forecast'].round(0).tolist(),
            #     'expense': forecast_df['Expenses_Forecast'].round(0).tolist(),
            #     'investment': forecast_df['Investment_Forecast'].round(0).tolist(),
            #     'net_cf': forecast_df['Net_Cash_Flow_Forecast'].round(0).tolist(),
            #     'income_ci': [forecast_df['Income_Lower_CI'].round(0).tolist(), forecast_df['Income_Upper_CI'].round(0).tolist()],
            #     'expense_ci': [forecast_df['Expenses_Lower_CI'].round(0).tolist(), forecast_df['Expenses_Upper_CI'].round(0).tolist()]
            # }
            
            logger.info("Forecast generation skipped for performance.")
            return {} # Return empty dict to indicate no forecast available
        except Exception as e:
            logger.error(f"Error generating forecast: {e}")
            return {'error': str(e)}

    def _calculate_income_source_yoy(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate income source breakdown for L12M with YoY comparison to previous L12M.
        """
        if df is None or df.empty:
            return {}
            
        now = pd.Timestamp.now()
        # L12M = last 12 months from end of data
        end_date = df.index.max()
        l12m_start = end_date - pd.DateOffset(months=11)
        prev_l12m_end = l12m_start - pd.Timedelta(days=1)
        prev_l12m_start = prev_l12m_end - pd.DateOffset(months=11)
        
        inc_cols = [c for c in df.columns if c.startswith('Income_') and 'Total' not in c and 'Calc' not in c]
        
        def get_sums(start, end):
            mask = (df.index >= start) & (df.index <= end)
            if not mask.any():
                return pd.Series(0, index=inc_cols)
            return df.loc[mask, inc_cols].sum()
            
        curr_l12m = get_sums(l12m_start, end_date)
        prev_l12m = get_sums(prev_l12m_start, prev_l12m_end)
        
        result = {}
        total_curr = curr_l12m.sum()
        
        for col in inc_cols:
            curr_val = curr_l12m[col]
            prev_val = prev_l12m[col]
            if curr_val == 0 and prev_val == 0:
                continue
                
            clean_name = col.replace('Income_', '').replace('_CNY', '')
            yoy = ((curr_val - prev_val) / abs(prev_val) * 100) if prev_val != 0 else 0
            
            result[clean_name] = {
                'value': float(curr_val),
                'yoy': float(yoy),
                'yoy_str': f"{'+' if yoy >= 0 else ''}{yoy:.1f}%" if prev_val != 0 else 'NEW'
            }
            
        return result

    def get_stress_test_data(self, income_shock: float = 0.0, expense_shock: float = 0.0) -> Dict[str, Any]:
        """
        Generate stress test data by applying shocks to cash flow forecasts.
        """
        try:
            from src.financial_analysis.cash_flow_forecaster import CashFlowForecaster
            forecaster = CashFlowForecaster(self.analyzer.data_manager)
            forecaster.fetch_and_process_historical_data()
            forecaster.fit_sarima_models(seasonal_period=12)
            
            # Simulate stress scenario (12 months)
            stressed_df = forecaster.simulate_stress_scenario(
                periods=12,
                income_shock=income_shock,
                expense_shock=expense_shock
            )
            
            # Formatting for charts
            dates = [d.strftime('%Y-%m') for d in stressed_df.index]
            
            return {
                'labels': dates,
                'income': stressed_df['Income_Forecast'].round(0).tolist(),
                'expense': stressed_df['Expenses_Forecast'].round(0).tolist(),
                'net_cf': stressed_df['Net_Cash_Flow_Forecast'].round(0).tolist(),
                'warnings': stressed_df['Liquidity_Warning'].tolist(),
                'has_liquidity_issue': stressed_df['Liquidity_Warning'].any()
            }
        except Exception as e:
            logger.error(f"Error generating stress test: {e}")
            return {'error': str(e)}

    # --- Helpers ---

    def _serialize_df_to_chart_data(self, df: pd.DataFrame, label_col: str = 'index', data_cols: List[str] = None) -> Dict[str, Any]:
        """
        Helper to convert DataFrame to Chart.js compatible structure.
        """
        if df is None or df.empty:
            return {'labels': [], 'datasets': []}
            
        if label_col == 'index':
            labels = df.index.strftime('%Y-%m').tolist() if isinstance(df.index, pd.DatetimeIndex) else df.index.tolist()
        else:
            labels = df[label_col].tolist()
            
        datasets = []
        cols = data_cols if data_cols else df.columns.tolist()
        
        for col in cols:
            if col in df.columns:
                datasets.append({
                    'label': col,
                    'data': self._clean_nan(df[col].tolist())
                })
                
        return {
            'labels': labels,
            'datasets': datasets
        }

    def _clean_nan(self, data_list: List) -> List:
        """Replace NaNs with None (which translates to null in JSON)"""
        return [None if pd.isna(x) else x for x in data_list]

    def _fmt_currency(self, value):
        if pd.isna(value): return "¥0"
        return f"¥{value:,.0f}"

    def _fmt_percent(self, value):
        if pd.isna(value): return "0%"
        # If value is 0.5 for 50%, multiply by 100. If 50 for 50%, don't.
        # Assuming standard ratio (0-1) or existing percent.
        # Check logic in analyzer. annualized_growth_pct is *100 already.
        # avg_savings_rate is ratio (0.5).
        # We need to handle scaling.
        # Let's assume input is raw ratio if < 1.0 (heuristic?)
        # Actually analyzer returns inconsistent things (some *100, some not).
        # Savings rate: `savings_rate_monthly` is `div`, so ratio. `avg_savings_rate` is ratio.
        # Growth pct: `annualized_growth_pct` is `* 100`.
        
        # Heuristic: if small, *100. Wait, 100% growth is 1.0. 
        # Better: caller should know.
        # For now, simplistic formatting.
        return f"{value*100:.1f}%" if value <= 1.5 else f"{value:.1f}%" 

