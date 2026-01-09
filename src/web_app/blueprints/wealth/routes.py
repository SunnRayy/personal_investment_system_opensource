from flask import Blueprint, render_template, jsonify, current_app
from src.web_app.services.wealth_service import WealthService
from src.database.models import MonthlyFinancialSnapshot
from src.database.base import get_session
from sqlalchemy import desc
import logging
import pandas as pd

# Define the blueprint
wealth_bp = Blueprint('wealth', __name__, 
                      template_folder='templates',
                      url_prefix='/wealth')

logger = logging.getLogger(__name__)

def get_service():
    return WealthService(config_dir='config')

@wealth_bp.route('/')
def dashboard():
    """Render the main Wealth Dashboard."""
    return render_template('wealth/dashboard.html')

@wealth_bp.route('/api/summary')
def get_summary():
    """API Endpoint for Dashboard Summary Data (All Tabs)."""
    try:
        service = get_service()
        data = service.get_dashboard_data()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching summary: {e}")
        return jsonify({'error': str(e)}), 500

@wealth_bp.route('/api/balance-sheet')
def get_balance_sheet():
    return jsonify({'status': 'included_in_summary'})

@wealth_bp.route('/api/cash-flow')
def get_cash_flow():
    return jsonify({'status': 'included_in_summary'})

@wealth_bp.route('/parity')
def parity_check():
    """Data Parity Check - Compare Excel, DB, and API values."""
    return render_template('wealth/parity.html')

@wealth_bp.route('/api/parity')
def get_parity_data():
    """API Endpoint for Parity Check Data."""
    try:
        # 1. Get Excel data (latest month from FinancialAnalyzer)
        service = get_service()
        analyzer = service.analyzer
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
        
        # 2. Get DB data (latest from MonthlyFinancialSnapshot)
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
        
        # 3. Calculate deltas
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

