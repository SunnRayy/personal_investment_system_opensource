import logging
import time
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
from flask import jsonify, request
from flask_login import login_required

from . import api_bp
from src.data_manager.historical_manager import HistoricalDataManager
from src.unified_analysis.engine import FinancialAnalysisEngine
from src.data_quality.health_checker import DataQualityHealthCheck
from src.web_app.services.report_service import ReportDataService

logger = logging.getLogger(__name__)


@api_bp.route('/assets/list', methods=['GET'])
@login_required
def list_assets():
	"""Return list of unique Asset_ID and Asset_Name pairs for dropdowns."""
	try:
		from src.data_manager.manager import DataManager
		
		# Get assets from holdings
		data_manager = DataManager()
		holdings = data_manager.get_holdings()
		
		# Get unique Asset_ID and Asset_Name pairs from holdings
		if holdings is not None and not holdings.empty and 'Asset_Name' in holdings.columns:
			assets_df = holdings[['Asset_Name']].copy()
			# Use Asset_Name as both ID and display name for consistency
			assets_df['Asset_ID'] = assets_df['Asset_Name']
			assets_df = assets_df[['Asset_ID', 'Asset_Name']].drop_duplicates().sort_values('Asset_Name')
			
			assets_list = assets_df.to_dict('records')
			logger.info(f"Returning {len(assets_list)} unique assets for dropdown")
			return jsonify({'assets': assets_list, 'count': len(assets_list)})
		else:
			logger.warning("No holdings data available for asset list")
			return jsonify({'assets': [], 'count': 0})
			
	except Exception as e:
		logger.error(f"Error fetching asset list: {e}", exc_info=True)
		return jsonify({'error': str(e), 'assets': [], 'count': 0}), 500


@api_bp.route('/health', methods=['GET'])
def health_check():
	"""Simple health check endpoint."""
	return jsonify({
		'status': 'healthy',
		'timestamp': datetime.now().isoformat()
	})


@api_bp.route('/unified_analysis', methods=['GET'])
@login_required
def unified_analysis_api():
	"""Unified analysis endpoint used by dashboards."""
	start_time = time.time()
	logger.info("Starting unified analysis API request")

	try:
		engine = FinancialAnalysisEngine()
		results = engine.run_complete_analysis()

		duration = time.time() - start_time
		logger.info("Unified analysis completed successfully in %.2f seconds", duration)

		def clean_nan_values(obj: Any):
			"""Recursively replace NaN/inf values."""
			if isinstance(obj, dict):
				return {k: clean_nan_values(v) for k, v in obj.items()}
			if isinstance(obj, list):
				return [clean_nan_values(item) for item in obj]
			if isinstance(obj, (float, np.floating)):
				if np.isnan(obj) or np.isinf(obj):
					return None
				return float(obj)
			if isinstance(obj, (np.int64, np.int32)):
				return int(obj)
			return obj

		clean_results = clean_nan_values(results)
		return jsonify(clean_results)

	except Exception as error:  # pragma: no cover - API guard
		logger.error("Error in unified analysis: %s", error)
		return jsonify({'error': str(error)}), 500


@api_bp.route('/portfolio_overview', methods=['GET'])
@login_required
def portfolio_overview_api():
	"""Summarize holdings and history for dashboard cards."""
	try:
		data_manager = HistoricalDataManager(config_path='config/settings.yaml')
		current_holdings = data_manager.get_holdings(latest_only=True)
		historical_holdings = data_manager.get_historical_holdings()
		balance_sheet = data_manager.get_balance_sheet()

		total_value = 0
		holdings_count = 0
		historical_records = 0
		allocation_data = {}
		trend_data = {'dates': [], 'values': []}

		if current_holdings is not None and not current_holdings.empty:
			holdings_count = len(current_holdings)
			logger.info(f"Current holdings count: {holdings_count}")
			if 'Market_Value_CNY' in current_holdings.columns:
				total_value = float(current_holdings['Market_Value_CNY'].sum())

				group_col = 'Asset_Class' if 'Asset_Class' in current_holdings.columns else 'Asset_Type'
				if group_col in current_holdings.columns:
					allocation = current_holdings.groupby(group_col)['Market_Value_CNY'].sum()
					allocation_data = {k: float(v) for k, v in allocation.items()}
			elif 'Market_Value' in current_holdings.columns:
				total_value = float(current_holdings['Market_Value'].sum())

		# Get transaction count for "History Points" metric (user expects transaction count, not snapshot count)
		try:
			# HistoricalDataManager inherits from DataManager, so it has get_transactions()
			transactions = data_manager.get_transactions()
			historical_records = len(transactions) if transactions is not None and not transactions.empty else 0
			logger.info(f"✅ Transaction count (History Points): {historical_records}")
		except Exception as e:
			# Fallback: use historical holdings count if transactions unavailable
			logger.warning(f"Could not get transactions: {e}")
			if historical_holdings is not None and not historical_holdings.empty:
				historical_records = len(historical_holdings)
				logger.warning(f"⚠️ Using historical holdings count ({historical_records}) as fallback for History Points")
			else:
				historical_records = 0

		# Prepare trend data - Prefer Balance Sheet for consistency with Portfolio Report
		if balance_sheet is not None and not balance_sheet.empty and 'Total_Assets_Calc_CNY' in balance_sheet.columns:
			try:
				# Ensure Date is available
				df_trend = balance_sheet.copy()
				if 'Date' not in df_trend.columns:
					df_trend = df_trend.reset_index()
				
				if 'Date' in df_trend.columns:
					# Sort by date
					df_trend['Date'] = pd.to_datetime(df_trend['Date'])
					df_trend = df_trend.sort_values('Date')
					
					# Filter last 12 months by default
					last_12_months = df_trend[df_trend['Date'] >= (datetime.now() - timedelta(days=365))]
					if last_12_months.empty:
						last_12_months = df_trend.tail(12) # Fallback to last 12 records
					
					trend_data = {
						'dates': last_12_months['Date'].dt.strftime('%Y-%m-%d').tolist(),
						'values': last_12_months['Total_Assets_Calc_CNY'].fillna(0).tolist()
					}
					logger.info(f"✅ Generated trend data from Balance Sheet ({len(trend_data['dates'])} points)")
			except Exception as e:
				logger.error(f"❌ Error generating trend from Balance Sheet: {e}")
				# Fallback will happen below if trend_data is still empty
		
		# Fallback to historical holdings if Balance Sheet failed or was empty
		if (not trend_data['dates']) and historical_holdings is not None and not historical_holdings.empty:
			logger.warning("⚠️ Using historical holdings for trend data (Balance Sheet unavailable)")
			# Handle Date column availability (Snapshot_Date in index vs Date column)
			df_for_trend = historical_holdings.copy()
			date_col = None
			
			if 'Date' in df_for_trend.columns:
				date_col = 'Date'
			elif 'Snapshot_Date' in df_for_trend.columns:
				date_col = 'Snapshot_Date'
			elif isinstance(df_for_trend.index, pd.MultiIndex) and 'Snapshot_Date' in df_for_trend.index.names:
				df_for_trend = df_for_trend.reset_index()
				date_col = 'Snapshot_Date'
			
			if date_col:
				# Group by date and sum market value
				daily_values = df_for_trend.groupby(date_col)['Market_Value_CNY'].sum().reset_index()
				daily_values[date_col] = pd.to_datetime(daily_values[date_col])
				daily_values = daily_values.sort_values(date_col)
				
				# Filter last 12 months
				last_12_months = daily_values[daily_values[date_col] >= (datetime.now() - timedelta(days=365))]
				if last_12_months.empty:
					last_12_months = daily_values.tail(12)
				
				trend_data = {
					'dates': last_12_months[date_col].dt.strftime('%Y-%m-%d').tolist(),
					'values': last_12_months['Market_Value_CNY'].fillna(0).tolist()
				}

		response_data = {
			'status': 'success',
			'data': {
				'total_portfolio_value': total_value,
				'current_holdings_count': holdings_count,
				'historical_records': historical_records,
				'allocation': allocation_data,
				'trend': trend_data,
				'holdings_available': current_holdings is not None,
				'balance_sheet_available': balance_sheet is not None,
				'currency': 'CNY',
				'generated_at': datetime.now().isoformat()
			}
		}

		return jsonify(response_data)

	except Exception as error:  # pragma: no cover - API guard
		logger.error("Error in portfolio overview: %s", error)
		return jsonify({
			'status': 'error',
			'message': str(error),
			'component': 'portfolio_overview'
		}), 500


@api_bp.route('/data_quality', methods=['GET'])
@login_required
def data_quality_api():
	"""Expose data quality health check results."""
	checker = DataQualityHealthCheck()
	results = checker.run_all_checks()
	return jsonify({
		'status': 'success',
		'data': results,
		'generated_at': datetime.now().isoformat()
	})


@api_bp.route('/cache/refresh', methods=['POST'])
@login_required
def refresh_cache():
	"""Force refresh of the report data cache."""
	try:
		report_service = ReportDataService()
		report_service.get_portfolio_data(force_refresh=True)
		return jsonify({'status': 'success', 'message': 'Cache refreshed successfully'})
	except Exception as e:
		logger.error(f"Error refreshing cache: {e}")
		return jsonify({'error': str(e)}), 500

