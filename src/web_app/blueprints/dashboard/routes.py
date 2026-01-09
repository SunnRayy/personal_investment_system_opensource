from flask import render_template
from flask_login import login_required
import logging

from . import dashboard_bp

logger = logging.getLogger(__name__)


@dashboard_bp.route('/')
@login_required
def index():
	"""Render main dashboard view."""
	return render_template('dashboard/index.html')


@dashboard_bp.route('/health-check')
@login_required
def data_quality_health_check():
	"""Render the data quality health dashboard."""
	return render_template('dashboard/health.html')


@dashboard_bp.route('/parity')
@login_required
def parity():
	"""Render the data parity dashboard comparing Excel vs DB vs HoldingsCalculator."""
	try:
		from src.data_manager.manager import DataManager
		from src.portfolio_lib.holdings_calculator import HoldingsCalculator
		from src.portfolio_lib.price_service import PriceService
		import pandas as pd
		
		# 1. Get Baseline (Excel Mode) - "Truth" from files
		dm_excel = DataManager(force_mode='excel')
		excel_holdings = dm_excel.get_holdings(latest_only=True)
		
		excel_total = 0
		excel_map = {}
		
		if excel_holdings is not None and not excel_holdings.empty:
			if isinstance(excel_holdings.index, pd.MultiIndex):
				excel_holdings = excel_holdings.reset_index()
			if 'Market_Value_CNY' in excel_holdings.columns:
				excel_total = excel_holdings['Market_Value_CNY'].sum()
			elif 'Market_Value' in excel_holdings.columns:
				excel_total = excel_holdings['Market_Value'].sum()
			for _, row in excel_holdings.iterrows():
				aid = row.get('Asset_ID')
				if not aid:
					continue
				val = row.get('Market_Value_CNY') or row.get('Market_Value') or 0
				excel_map[str(aid)] = float(val)

		# 2. Get DB Snapshots (Database Mode)
		dm_db = DataManager(force_mode='database')
		db_holdings = dm_db.get_holdings(latest_only=True)
		
		db_total = 0
		db_map = {}
		
		if db_holdings is not None and not db_holdings.empty:
			if isinstance(db_holdings.index, pd.MultiIndex):
				db_holdings = db_holdings.reset_index()
			if 'Market_Value_CNY' in db_holdings.columns:
				db_total = db_holdings['Market_Value_CNY'].sum()
			elif 'Market_Value' in db_holdings.columns:
				db_total = db_holdings['Market_Value'].sum()
			for _, row in db_holdings.iterrows():
				aid = row.get('Asset_ID')
				if not aid:
					continue
				val = row.get('Market_Value_CNY') or row.get('Market_Value') or 0
				db_map[str(aid)] = float(val)

		# 3. Get HoldingsCalculator (Transaction-derived)
		hc_total = 0
		hc_map = {}
		hc_error = None
		
		try:
			ps = PriceService(data_manager=dm_excel)
			hc = HoldingsCalculator(price_service=ps)
			hc_holdings = hc.calculate_current_holdings()
			
			if hc_holdings is not None and not hc_holdings.empty:
				if 'Market_Value' in hc_holdings.columns:
					hc_total = hc_holdings['Market_Value'].sum()
				for _, row in hc_holdings.iterrows():
					aid = row.get('Asset_ID')
					if not aid:
						continue
					val = row.get('Market_Value') or 0
					hc_map[str(aid)] = float(val)
		except Exception as e:
			logger.error(f"HoldingsCalculator failed: {e}", exc_info=True)
			hc_error = str(e)

		# 4. Build Excel vs DB Comparison (existing)
		all_assets = set(excel_map.keys()) | set(db_map.keys())
		comparison = []
		
		for aid in all_assets:
			excel_val = excel_map.get(aid, 0.0)
			db_val = db_map.get(aid, 0.0)
			delta = db_val - excel_val
			
			if abs(delta) > 1.0 or (excel_val > 0 and db_val == 0) or (db_val > 0 and excel_val == 0):
				comparison.append({
					'asset_id': aid,
					'excel_value': excel_val,
					'db_value': db_val,
					'delta': delta,
					'delta_abs': abs(delta),
					'status': 'Match' if abs(delta) < 1.0 else ('Missing in DB' if db_val == 0 else ('Missing in Excel' if excel_val == 0 else 'Mismatch'))
				})
		
		comparison.sort(key=lambda x: x['delta_abs'], reverse=True)
		
		# 5. Build Excel vs HoldingsCalculator Comparison (NEW)
		all_hc_assets = set(excel_map.keys()) | set(hc_map.keys())
		hc_comparison = []
		
		for aid in all_hc_assets:
			excel_val = excel_map.get(aid, 0.0)
			hc_val = hc_map.get(aid, 0.0)
			delta = excel_val - hc_val  # Excel - HoldingsCalc (positive = HC is missing)
			
			if abs(delta) > 100.0 or (excel_val > 0 and hc_val == 0) or (hc_val > 0 and excel_val == 0):
				hc_comparison.append({
					'asset_id': aid,
					'excel_value': excel_val,
					'hc_value': hc_val,
					'delta': delta,
					'delta_abs': abs(delta),
					'status': 'Match' if abs(delta) < 100.0 else ('Missing in HC' if hc_val == 0 else ('Extra in HC' if excel_val == 0 else 'Mismatch'))
				})
		
		hc_comparison.sort(key=lambda x: x['delta_abs'], reverse=True)
		
		# 6. Calculate Deltas
		delta_total = db_total - excel_total
		delta_pct = (delta_total / excel_total * 100) if excel_total > 0 else 0
		
		hc_delta_total = excel_total - hc_total  # Excel - HC (positive = HC is low)
		hc_delta_pct = (hc_delta_total / excel_total * 100) if excel_total > 0 else 0
		
		return render_template('dashboard/parity.html',
			excel_total=excel_total,
			db_total=db_total,
			delta=delta_total,
			delta_pct=delta_pct,
			comparison_data=comparison,
			# HoldingsCalculator additions
			hc_total=hc_total,
			hc_delta=hc_delta_total,
			hc_delta_pct=hc_delta_pct,
			hc_comparison=hc_comparison,
			hc_error=hc_error
		)
	except Exception as e:
		logger.error(f"Error generating parity dashboard: {e}", exc_info=True)
		return render_template('errors/500.html', error=str(e)), 500

