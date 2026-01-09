from flask import render_template, abort, request, jsonify
from flask_login import login_required
from src.web_app.services.report_service import ReportDataService
from src.web_app.services.wealth_service import WealthService
from src.recommendation_engine.recommendation_engine import RecommendationEngine
from src.database.models import MonthlyFinancialSnapshot
from src.database.base import get_session
from sqlalchemy import desc
from . import reports_bp
import logging

logger = logging.getLogger(__name__)

def _sanitize_template_context(data: dict) -> dict:
    """
    Sanitize template context to prevent conflicts with Flask-Babel's translation function.
    
    The Jinja2 template uses `{{ _('String') }}` for i18n translations via Flask-Babel.
    If the data dictionary contains a key named '_' (e.g., from `for _, row in df.iterrows()`
    leaking into the context), it will override the gettext function and cause:
    `TypeError: 'tuple' object is not callable`
    
    This function defensively removes the '_' key if present.
    """
    if '_' in data:
        logger.debug(f"Removing '_' key from template context (type: {type(data['_'])})")
        del data['_']
    return data

# Singleton instance for recommendation engine
_recommendation_engine_instance = None

def get_recommendation_engine():
    """Get or create singleton RecommendationEngine instance."""
    global _recommendation_engine_instance
    if _recommendation_engine_instance is None:
        logger.info("Creating new RecommendationEngine instance")
        _recommendation_engine_instance = RecommendationEngine()
    return _recommendation_engine_instance

# Singleton service instance to ensure cache persists across requests
_report_service_instance = None
_wealth_service_instance = None

def get_report_service():
    """Get or create singleton ReportDataService instance."""
    global _report_service_instance
    if _report_service_instance is None:
        logger.info("Creating new ReportDataService instance")
        _report_service_instance = ReportDataService()
    return _report_service_instance

def get_wealth_service():
    """Get or create singleton WealthService instance."""
    global _wealth_service_instance
    if _wealth_service_instance is None:
        logger.info("Creating new WealthService instance")
        _wealth_service_instance = WealthService(config_dir='config')
    return _wealth_service_instance

@reports_bp.route('/portfolio')
@login_required
def portfolio():
    """Render the Portfolio Analysis report."""
    try:
        force_refresh = request.args.get('refresh') == '1'
        report_service = get_report_service()
        data = report_service.get_portfolio_data(force_refresh=force_refresh)
        _sanitize_template_context(data)
        return render_template('reports/portfolio.html', **data)
    except Exception as e:
        logger.error(f"Error generating portfolio report: {e}", exc_info=True)
        return render_template('errors/500.html', error=e), 500

@reports_bp.route('/compass')
@login_required
def compass():
    """Render the Action Compass report."""
    try:
        report_service = get_report_service()
        # Accept risk_profile override from query params
        active_risk_profile = request.args.get('risk_profile')
        
        data = report_service.get_portfolio_data(
            force_refresh=False, 
            active_risk_profile=active_risk_profile
        )
        
        # PHASE 3: Pass relevant data to recommendation engine for enhanced alerts
        rebalancing_data = data.get('rebalancing_analysis', {})
        # Ensure correlation and stress data are available for the engine
        rebalancing_data['correlation_analysis'] = data.get('correlation_analysis', {})
        rebalancing_data['stress_test_data'] = data.get('stress_test_data', {})
        
        recommendation_engine = get_recommendation_engine()
        recommendations_data = recommendation_engine.generate_all_recommendations(
            rebalancing_data=rebalancing_data,
            holdings_df=data.get('holdings_df'),
            performance_data=data.get('performance_data', {}),
            portfolio_value=data.get('total_portfolio_value', 0),
            market_regime=data.get('market_regime')
        )
        
        # Merge recommendations into data
        data.update(recommendations_data)
        
        _sanitize_template_context(data)
        return render_template('reports/compass.html', **data)
    except Exception as e:
        logger.error(f"Error generating compass report: {e}", exc_info=True)
        return render_template('errors/500.html', error=e), 500

@reports_bp.route('/thermometer')
@login_required
def thermometer():
    """Render the Market Thermometer report."""
    try:
        report_service = get_report_service()
        data = report_service.get_portfolio_data(force_refresh=False)
        _sanitize_template_context(data)
        return render_template('reports/thermometer.html', **data)
    except Exception as e:
        logger.error(f"Error generating thermometer report: {e}", exc_info=True)
        return render_template('errors/500.html', error=e), 500


@reports_bp.route('/attribution')
@login_required
def attribution():
    """Render the Performance Attribution report (Brinson-Fachler)."""
    try:
        report_service = get_report_service()
        # Default to 12 months, or allow query param override
        period = request.args.get('period', default=12, type=int)
        
        # Serialize specific data for charts
        import json
        data = report_service.get_attribution_data(period_months=period)
        
        # Convert chart data/table to JSON for JS if needed, or pass as objects
        # The template expects 'waterfall_chart' as a dict, we can pass it directly 
        # but for Chart.js in template we often need JSON string if we use JSON.parse
        # In this template we wrote `JSON.parse('{{ waterfall_chart_json | safe }}')`
        # So we need to serialize the chart data.
        
        waterfall_json = json.dumps(data.get('waterfall_chart', {}))
        data['waterfall_chart_json'] = waterfall_json
        
        _sanitize_template_context(data)
        return render_template('reports/attribution.html', **data)
    except Exception as e:
        logger.error(f"Error generating attribution report: {e}", exc_info=True)
        return render_template('errors/500.html', error=e), 500


# =========== CASH FLOW REPORT ===========

@reports_bp.route('/cashflow')
@login_required
def cashflow():
    """Render the Cash Flow & Wealth Dashboard."""
    return render_template('reports/cashflow.html')

@reports_bp.route('/cashflow/api/summary')
@login_required
def cashflow_api_summary():
    """API Endpoint for Cash Flow Dashboard Data - Uses ReportDataService for consistency."""
    try:
        import json
        from datetime import datetime
        
        # Get year parameter (default to current year)
        year = request.args.get('year', default=datetime.now().year, type=int)
        
        # Get Portfolio Report data for consistent KPIs and allocation
        report_service = get_report_service()
        portfolio_data = report_service.get_portfolio_data(force_refresh=False)
        
        # Get Cash Flow analysis data
        wealth_service = get_wealth_service()
        cf_data = wealth_service.get_dashboard_data()
        
        # Parse Portfolio allocation data (already JSON strings)
        top_level_alloc = json.loads(portfolio_data.get('top_level_allocation_json', '{}'))
        sub_class_alloc = json.loads(portfolio_data.get('sub_class_allocation_json', '{}'))
        
        # Calculate YTD metrics for the selected year
        monthly_df = wealth_service.analyzer.monthly_df
        ytd_summary = {}
        if monthly_df is not None and not monthly_df.empty:
            # Filter to selected year
            year_mask = monthly_df.index.year == year
            df_year = monthly_df[year_mask]
            
            prev_year_mask = monthly_df.index.year == (year - 1)
            df_prev_year = monthly_df[prev_year_mask]
            
            if not df_year.empty:
                # Calculate YTD totals
                inc_col = 'Total_Income_Calc_CNY'
                exp_col = 'Total_Expense_Calc_CNY'
                inv_col = 'Total_Investment_Calc_CNY'
                
                ytd_income = df_year[inc_col].sum() if inc_col in df_year.columns else 0
                ytd_expense = df_year[exp_col].sum() if exp_col in df_year.columns else 0
                ytd_invest = df_year[inv_col].sum() if inv_col in df_year.columns else 0
                ytd_net = ytd_income - ytd_expense - ytd_invest
                
                # Previous year same period (for YoY)
                prev_income = df_prev_year[inc_col].sum() if inc_col in df_prev_year.columns else 0
                prev_expense = df_prev_year[exp_col].sum() if exp_col in df_prev_year.columns else 0
                prev_invest = df_prev_year[inv_col].sum() if inv_col in df_prev_year.columns else 0
                prev_net = prev_income - prev_expense - prev_invest
                
                # Format values and YoY
                def fmt_val(val):
                    if val >= 1000000:
                        return f"¥{val/1000000:.2f}M"
                    return f"¥{val/1000:.0f}K"
                
                def calc_yoy(curr, prev):
                    if prev == 0:
                        return None
                    pct = ((curr - prev) / abs(prev)) * 100
                    return f"{'+' if pct >= 0 else ''}{pct:.1f}%"
                
                ytd_summary = {
                    'ytd_income': fmt_val(ytd_income),
                    'ytd_income_yoy': calc_yoy(ytd_income, prev_income),
                    'ytd_expense': fmt_val(ytd_expense),
                    'ytd_expense_yoy': calc_yoy(ytd_expense, prev_expense),
                    'ytd_investment': fmt_val(ytd_invest),
                    'ytd_investment_yoy': calc_yoy(ytd_invest, prev_invest),
                    'ytd_net_cf': fmt_val(ytd_net),
                    'ytd_net_cf_yoy': calc_yoy(ytd_net, prev_net),
                }
        
        # Calculate year-filtered expense breakdown
        ytd_expense_breakdown = {}
        if monthly_df is not None and not monthly_df.empty:
            year_mask = monthly_df.index.year == year
            df_year = monthly_df[year_mask]
            
            prev_year_mask = monthly_df.index.year == (year - 1)
            df_prev_year = monthly_df[prev_year_mask]
            
            if not df_year.empty:
                expense_cols = [c for c in df_year.columns if c.startswith('Expense_') and c.endswith('_CNY') and 'Total' not in c and 'Calc' not in c]
                
                # Get totals for percentage calculation
                exp_col = 'Total_Expense_Calc_CNY'
                total_expense_year = df_year[exp_col].sum() if exp_col in df_year.columns else 1
                
                for col in expense_cols:
                    val = df_year[col].sum()
                    if val > 100:  # Only include significant expenses
                        prev_val = df_prev_year[col].sum() if col in df_prev_year.columns else 0
                        
                        # Calculate YoY
                        if prev_val > 0:
                            yoy = ((val - prev_val) / abs(prev_val)) * 100
                            yoy_str = f"{'+' if yoy >= 0 else ''}{yoy:.1f}%"
                        else:
                            yoy = None
                            yoy_str = "NEW"
                        
                        # Calculate percentage of total
                        pct = (val / total_expense_year * 100) if total_expense_year > 0 else 0
                        
                        # Calculate percentage point change YoY
                        total_prev = df_prev_year[exp_col].sum() if exp_col in df_prev_year.columns else 1
                        prev_pct = (prev_val / total_prev * 100) if total_prev > 0 and prev_val > 0 else 0
                        pct_yoy = pct - prev_pct
                        pct_yoy_str = f"{'+' if pct_yoy >= 0 else ''}{pct_yoy:.1f}pp"
                        
                        cat_name = col.replace('Expense_', '').replace('_CNY', '').replace('_', ' ')
                        ytd_expense_breakdown[cat_name] = {
                            'value': val,
                            'yoy': yoy,
                            'yoy_str': yoy_str,
                            'percentage': pct,
                            'pct_yoy': pct_yoy,
                            'pct_yoy_str': pct_yoy_str
                        }
        
        # Build response combining both sources
        summary_base = cf_data.get('summary', {})
        
        # Override with year-specific YTD metrics
        summary_final = summary_base.copy()
        summary_final.update(ytd_summary)
        summary_final.update({
            'net_worth': f"¥{portfolio_data.get('total_net_assets', '0')}",
            'total_liability': f"¥{portfolio_data.get('total_liability', '0')}",
            'total_assets': f"¥{portfolio_data.get('total_portfolio_value', '0')}",
            'liquid_portfolio': f"¥{portfolio_data.get('total_liquid_portfolio', '0')}",
            'selected_year': year,
        })
        
        # Log summary keys to debug missing KPIs
        logger.info(f"Dashboard summary keys: {list(summary_final.keys())}")
        
        # Get base cash flow data and ALWAYS override with year-filtered expense breakdown
        # (base data from WealthService uses current year, but we want selected year)
        cash_flow_data = cf_data.get('cash_flow', {}).copy()  # Copy to avoid mutating cached data
        cash_flow_data['ytd_expense_breakdown'] = ytd_expense_breakdown  # Always override
        
        response = {
            'summary': summary_final,
            'portfolio_allocation': {
                'top_level': top_level_alloc,
                'sub_class': sub_class_alloc
            },
            'balance_sheet': cf_data.get('balance_sheet', {}),
            'cash_flow': cash_flow_data,
            'investment': cf_data.get('investment', {}),
            'forecast': cf_data.get('forecast', {}),
            'historical': cf_data.get('historical', {})
        }
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error fetching cashflow summary: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/cashflow/parity')
@login_required
def cashflow_parity():
    """Data Parity Check - Compare Excel, DB, and API values."""
    return render_template('reports/cashflow_parity.html')

@reports_bp.route('/cashflow/api/parity')
@login_required
def cashflow_api_parity():
    """API Endpoint for Parity Check Data."""
    try:
        wealth_service = get_wealth_service()
        analyzer = wealth_service.analyzer
        monthly_df = analyzer.monthly_df
        
        excel_latest = {}
        if monthly_df is not None and not monthly_df.empty:
            latest_row = monthly_df.iloc[-1]
            excel_latest = {
                'date': str(monthly_df.index[-1].date()),
                'total_income': float(latest_row.get('Total_Income_Calc_CNY', 0)),
                'total_expense': float(latest_row.get('Total_Expense_Calc_CNY', 0)),
                'net_savings': float(latest_row.get('Total_Income_Calc_CNY', 0)) - float(latest_row.get('Total_Expense_Calc_CNY', 0))
            }
        
        session = get_session()
        db_latest_row = session.query(MonthlyFinancialSnapshot).order_by(desc(MonthlyFinancialSnapshot.snapshot_date)).first()
        
        db_latest = {}
        if db_latest_row:
            db_latest = {
                'date': str(db_latest_row.snapshot_date),
                'total_income': float(db_latest_row.total_income or 0),
                'total_expense': float(db_latest_row.total_expense or 0),
                'net_savings': float(db_latest_row.net_savings or 0)
            }
        session.close()
        
        def calc_delta(excel_val, db_val):
            if excel_val == 0:
                return 0 if db_val == 0 else float('inf')
            return ((db_val - excel_val) / abs(excel_val)) * 100
        
        deltas = {}
        if excel_latest and db_latest:
            deltas = {
                'total_income_delta_pct': calc_delta(excel_latest['total_income'], db_latest['total_income']),
                'total_expense_delta_pct': calc_delta(excel_latest['total_expense'], db_latest['total_expense']),
                'net_savings_delta_pct': calc_delta(excel_latest['net_savings'], db_latest['net_savings']),
            }
        
        return jsonify({
            'excel': excel_latest,
            'database': db_latest,
            'deltas': deltas,
            'status': 'ok'
        })
    except Exception as e:
        logger.error(f"Error in parity check: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# =========== ANNUAL REPORT ===========

@reports_bp.route('/annual')
@login_required
def annual():
    """Render the Annual Financial Report page."""
    return render_template('reports/annual.html')

@reports_bp.route('/api/annual/stress')
@login_required
def annual_api_stress():
    """API Endpoint for Annual Report Stress Test Data."""
    try:
        income_shock = request.args.get('income_shock', default=0.0, type=float)
        expense_shock = request.args.get('expense_shock', default=0.0, type=float)
        
        wealth_service = get_wealth_service()
        data = wealth_service.get_stress_test_data(
            income_shock=income_shock,
            expense_shock=expense_shock
        )
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error in annual_api_stress: {e}")
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/api/annual/sankey')
@login_required
def annual_api_sankey():
    """
    API Endpoint for Annual Report Sankey Data.
    Returns 4-layered flow: Sources -> Total Income -> Inflow Hub -> Buckets -> Categories.
    """
    try:
        import pandas as pd
        import numpy as np
        
        year = request.args.get('year', default=2025, type=int)
        wealth_service = get_wealth_service()
        monthly_df = wealth_service.analyzer.monthly_df
        
        if monthly_df is None or monthly_df.empty:
            return jsonify({'error': 'No data available'}), 404

        # --- Helper: Calculate Totals and Breakdown for a Year ---
        def get_year_data(target_year):
            mask = monthly_df.index.year == target_year
            df_year = monthly_df[mask]
            
            if df_year.empty:
                return {}
                
            data = {'income': {}, 'expense': {}, 'investment': {}}
            
            # 1. Income
            income_cols = [c for c in df_year.columns if c.startswith('Income_') and c.endswith('_CNY') and 'Total' not in c and 'Calc' not in c]
            for col in income_cols:
                val = df_year[col].sum()
                if val > 100:
                    name = col.replace('Income_', '').replace('_CNY', '').replace('_', ' ')
                    data['income'][name] = val
            
            # 2. Expense
            expense_cols = [c for c in df_year.columns if c.startswith('Expense_') and c.endswith('_CNY') and 'Total' not in c and 'Calc' not in c]
            for col in expense_cols:
                val = df_year[col].sum()
                if val > 100:
                    name = col.replace('Expense_', '').replace('_CNY', '').replace('_', ' ')
                    data['expense'][name] = val
            
            # 3. Investment
            invest_cols = [c for c in df_year.columns if c.startswith('Outflow_Invest_') and c.endswith('_CNY')]
            for col in invest_cols:
                val = df_year[col].sum()
                if val > 100:
                    name = col.replace('Outflow_Invest_', '').replace('_CNY', '').replace('_', ' ')
                    data['investment'][name] = val
            
            return data

        # Get Current and Previous Year Data for YoY
        data_curr = get_year_data(year)
        data_prev = get_year_data(year - 1)
        
        if not data_curr:
             return jsonify({'error': f'No data for {year}'}), 404

        # Calculate Totals
        total_inc_curr = sum(data_curr.get('income', {}).values())
        total_exp_curr = sum(data_curr.get('expense', {}).values())
        total_inv_curr = sum(data_curr.get('investment', {}).values())
        savings_curr = total_inc_curr - total_exp_curr - total_inv_curr
        
        total_inc_prev = sum(data_prev.get('income', {}).values())
        total_exp_prev = sum(data_prev.get('expense', {}).values())
        total_inv_prev = sum(data_prev.get('investment', {}).values())
        savings_prev = total_inc_prev - total_exp_prev - total_inv_prev

        # YoY Helpers
        def calc_yoy(curr, prev):
            if not prev or prev == 0: return 0.0
            return (curr - prev) / abs(prev)
            
        def fmt_val(val):
            if val >= 1000000: return f"¥{val/1000000:.2f}M"
            return f"¥{val/1000:.1f}k"

        # --- Build Links for 4-Layer Sankey ---
        links = []
        
        # NODE NAMES
        total_income_node = "Total Income"
        inflow_hub_node = "Disposable Inflow"
        expense_bucket = "Total Expenses"
        invest_bucket = "Total Investments"
        savings_bucket = "Cash Savings"

        # LAYER 1: Income Sources -> Total Income
        for name, val in data_curr['income'].items():
            prev_val = data_prev.get('income', {}).get(name, 0)
            yoy = calc_yoy(val, prev_val)
            tooltip = f"{name}: {fmt_val(val)} ({yoy:+.1%})"
            links.append([name, total_income_node, float(val), tooltip])

        # LAYER 2: Total Income -> Inflow Hub (Consolidation)
        yoy_total_inc = calc_yoy(total_inc_curr, total_inc_prev)
        tooltip_total = f"Total Income: {fmt_val(total_inc_curr)} ({yoy_total_inc:+.1%})"
        links.append([total_income_node, inflow_hub_node, float(total_inc_curr), tooltip_total])

        # LAYER 3: Inflow Hub -> Buckets
        # Expenses
        yoy_exp = calc_yoy(total_exp_curr, total_exp_prev)
        links.append([inflow_hub_node, expense_bucket, float(total_exp_curr), f"Expenses: {fmt_val(total_exp_curr)} ({yoy_exp:+.1%})"])
        
        # Investments
        yoy_inv = calc_yoy(total_inv_curr, total_inv_prev)
        links.append([inflow_hub_node, invest_bucket, float(total_inv_curr), f"Investments: {fmt_val(total_inv_curr)} ({yoy_inv:+.1%})"])
        
        # Savings
        if savings_curr > 0:
            yoy_sav = calc_yoy(savings_curr, savings_prev)
            links.append([inflow_hub_node, savings_bucket, float(savings_curr), f"Savings: {fmt_val(savings_curr)} ({yoy_sav:+.1%})"])

        # LAYER 4: Buckets -> Detailed Categories
        # Expenses -> Categories
        for name, val in data_curr['expense'].items():
            prev_val = data_prev.get('expense', {}).get(name, 0)
            yoy = calc_yoy(val, prev_val)
            tooltip = f"{name}: {fmt_val(val)} ({yoy:+.1%})"
            links.append([expense_bucket, name, float(val), tooltip])

        # Investments -> Categories
        for name, val in data_curr['investment'].items():
            prev_val = data_prev.get('investment', {}).get(name, 0)
            yoy = calc_yoy(val, prev_val)
            node_name = f"Invest: {name}"
            tooltip = f"{node_name}: {fmt_val(val)} ({yoy:+.1%})"
            links.append([invest_bucket, node_name, float(val), tooltip])

        # Response Totals (Absolute values and YoY for summary)
        summary = {
            'income': {'value': total_inc_curr, 'yoy_pct': yoy_total_inc},
            'expense': {'value': total_exp_curr, 'yoy_pct': yoy_exp},
            'investment': {'value': total_inv_curr, 'yoy_pct': yoy_inv},
            'savings': {'value': savings_curr, 'yoy_pct': calc_yoy(savings_curr, savings_prev)}
        }
        
        # --- EXTENDED METRICS ---
        # 1. Savings Rate % = (Income - Expense) / Income
        savings_rate = ((total_inc_curr - total_exp_curr) / total_inc_curr * 100) if total_inc_curr > 0 else 0
        savings_rate_prev = ((total_inc_prev - total_exp_prev) / total_inc_prev * 100) if total_inc_prev > 0 else 0
        
        # 2. Investment Rate % = Investment / Income (gross, including reinvestments)
        invest_rate = (total_inv_curr / total_inc_curr * 100) if total_inc_curr > 0 else 0
        invest_rate_prev = (total_inv_prev / total_inc_prev * 100) if total_inc_prev > 0 else 0
        
        # 3. Passive Income % (RSU, FundRedemption, Other, Dividends, Interest)
        passive_sources = ['RSU', 'RSU USD', 'RSU FromUSD', 'Passive FundRedemption', 'Other', 'Dividend', 'Interest']
        passive_curr = sum(data_curr.get('income', {}).get(k, 0) for k in passive_sources)
        passive_prev = sum(data_prev.get('income', {}).get(k, 0) for k in passive_sources)
        passive_pct = (passive_curr / total_inc_curr * 100) if total_inc_curr > 0 else 0
        passive_pct_prev = (passive_prev / total_inc_prev * 100) if total_inc_prev > 0 else 0
        
        # 4. Net New Investment = Total Investment - Fund Redemptions
        redemption_sources = ['Passive FundRedemption']
        redemption_curr = sum(data_curr.get('income', {}).get(k, 0) for k in redemption_sources)
        redemption_prev = sum(data_prev.get('income', {}).get(k, 0) for k in redemption_sources)
        net_new_invest_curr = total_inv_curr - redemption_curr
        net_new_invest_prev = total_inv_prev - redemption_prev
        net_new_invest_rate = (net_new_invest_curr / total_inc_curr * 100) if total_inc_curr > 0 else 0
        net_new_invest_rate_prev = (net_new_invest_prev / total_inc_prev * 100) if total_inc_prev > 0 else 0
        
        # 5. Net Worth Growth % (from balance sheet)
        balance_sheet_df = wealth_service.analyzer.balance_sheet_df
        nw_growth = None
        liquid_nw_growth = None
        nw_end = None
        nw_start = None
        if balance_sheet_df is not None and not balance_sheet_df.empty:
            try:
                # Get year-end and year-start net worth
                year_mask_curr = balance_sheet_df.index.year == year
                year_mask_prev = balance_sheet_df.index.year == (year - 1)
                
                if year_mask_curr.any() and year_mask_prev.any():
                    nw_col = 'Net_Worth_Calc_CNY'
                    nw_end = balance_sheet_df.loc[year_mask_curr, nw_col].iloc[-1] if nw_col in balance_sheet_df.columns else None
                    nw_start = balance_sheet_df.loc[year_mask_prev, nw_col].iloc[-1] if nw_col in balance_sheet_df.columns else None
                    
                    if nw_end and nw_start and nw_start != 0:
                        nw_growth = ((nw_end - nw_start) / abs(nw_start)) * 100
                    
                    # Liquid NW (exclude Property and Insurance)
                    prop_col = 'Holding_Property_CNY'
                    ins_col = 'Holding_Insurance_CNY' 
                    
                    prop_end = balance_sheet_df.loc[year_mask_curr, prop_col].iloc[-1] if prop_col in balance_sheet_df.columns else 0
                    prop_start = balance_sheet_df.loc[year_mask_prev, prop_col].iloc[-1] if prop_col in balance_sheet_df.columns else 0
                    ins_end = balance_sheet_df.loc[year_mask_curr, ins_col].iloc[-1] if ins_col in balance_sheet_df.columns else 0
                    ins_start = balance_sheet_df.loc[year_mask_prev, ins_col].iloc[-1] if ins_col in balance_sheet_df.columns else 0
                    
                    liquid_nw_end = (nw_end or 0) - (prop_end or 0) - (ins_end or 0)
                    liquid_nw_start = (nw_start or 0) - (prop_start or 0) - (ins_start or 0)
                    
                    if liquid_nw_start != 0:
                        liquid_nw_growth = ((liquid_nw_end - liquid_nw_start) / abs(liquid_nw_start)) * 100
            except Exception as e:
                logger.warning(f"Could not calculate NW growth: {e}")
        
        # 6. Market Gain = NW Change - Net New Investment (external capital inflow)
        # External income = Salary + RSU + Dividends (non-redemption income)
        # Market Gain = NW_End - NW_Start - Net_New_Investment
        invest_gain = None
        if nw_end is not None and nw_start is not None:
            nw_change = nw_end - nw_start
            # Market Gain = NW change minus net new capital deployed into investments
            invest_gain = nw_change - net_new_invest_curr
        
        # Add extended metrics to response
        summary['savings_rate_pct'] = savings_rate
        summary['savings_rate_pct_yoy'] = savings_rate - savings_rate_prev
        summary['invest_rate_pct'] = invest_rate
        summary['invest_rate_pct_yoy'] = invest_rate - invest_rate_prev
        summary['passive_income_pct'] = passive_pct
        summary['passive_income_pct_yoy'] = passive_pct - passive_pct_prev
        summary['passive_income_value'] = passive_curr
        summary['net_new_invest'] = net_new_invest_curr
        summary['net_new_invest_rate'] = net_new_invest_rate
        summary['net_new_invest_rate_yoy'] = net_new_invest_rate - net_new_invest_rate_prev
        summary['nw_growth_pct'] = nw_growth
        summary['liquid_nw_growth_pct'] = liquid_nw_growth
        summary['invest_gain'] = invest_gain
        
        return jsonify({
            'year': year,
            'links': links,
            'totals': summary
        })

    except Exception as e:
        logger.error(f"Error generating Annual Sankey data: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

