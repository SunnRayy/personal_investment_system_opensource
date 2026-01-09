import logging
from typing import Any, Dict, List, Optional

import pandas as pd
from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from . import transactions_bp
from src.database.connector import DatabaseConnector

logger = logging.getLogger(__name__)
db_connector = DatabaseConnector()


def _load_transactions() -> List[Dict[str, Any]]:
	"""Return transactions as a list of dictionaries for the template."""
	try:
		df = db_connector.get_transactions()
		if df is None or df.empty:
			return []

		df_reset = df.reset_index()
		df_reset['Date'] = pd.to_datetime(df_reset['Date'])
		return df_reset.to_dict('records')
	except Exception as error:  # pragma: no cover - flash only
		logger.error("Error loading transactions: %s", error)
		return []


def _parse_float(value: str) -> Optional[float]:
	"""Convert optional form values to float."""
	try:
		if value is None or value == '':
			return None
		return float(value)
	except (TypeError, ValueError):
		return None


@transactions_bp.route('/')
@login_required
def list_transactions():
	"""Render transaction list."""
	transactions = _load_transactions()
	return render_template('transactions/list.html', transactions=transactions)


@transactions_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
	"""Add a new transaction."""
	if request.method == 'POST':
		form = request.form
		data = {
			'date': form.get('date'),
			'asset_id': form.get('asset_id'),
			'asset_name': form.get('asset_name'),
			'transaction_type': form.get('transaction_type'),
			'amount': _parse_float(form.get('amount')),
			'currency': form.get('currency', 'CNY'),
			'shares': _parse_float(form.get('shares')),
			'price': _parse_float(form.get('price')),
			'exchange_rate': _parse_float(form.get('exchange_rate')),
			'source': 'Manual_Web'
		}
		
		asset_type = form.get('asset_type')

		missing_required = [key for key in ('date', 'asset_id', 'asset_name', 'transaction_type') if not data[key]]
		if missing_required or data['amount'] is None:
			flash("All required fields must be filled, including a numeric amount.", "error")
			return render_template('transactions/add.html', form=form)

		try:
			# Check if asset exists, if not create it
			existing_asset = db_connector.get_asset(data['asset_id'])
			if not existing_asset:
				if not asset_type:
					flash("Asset Type is required for new assets.", "error")
					return render_template('transactions/add.html', form=form)
					
				logger.info(f"Creating new asset: {data['asset_id']} ({asset_type})")
				db_connector.add_asset({
					'asset_id': data['asset_id'],
					'asset_name': data['asset_name'],
					'asset_type': asset_type,
					'asset_class': 'Unknown', # Default, can be updated later
					'risk_level': 'Medium'
				})

			db_connector.add_transaction(data)
			flash("Transaction added successfully", "success")
			return redirect(url_for('transactions.list_transactions'))
		except Exception as error:  # pragma: no cover - flash only
			logger.error("Error adding transaction: %s", error)
			flash(f"Error adding transaction: {error}", "error")

	return render_template('transactions/add.html')


@transactions_bp.route('/edit/<int:txn_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(txn_id: int):
	"""Edit an existing transaction."""
	if request.method == 'POST':
		form = request.form
		data = {
			'date': form.get('date'),
			'asset_id': form.get('asset_id'),
			'asset_name': form.get('asset_name'),
			'transaction_type': form.get('transaction_type'),
			'amount': _parse_float(form.get('amount')),
			'currency': form.get('currency', 'CNY'),
			'shares': _parse_float(form.get('shares')),
			'price': _parse_float(form.get('price')),
			'exchange_rate': _parse_float(form.get('exchange_rate')),
		}

		try:
			db_connector.update_transaction(txn_id, data)
			flash("Transaction updated successfully", "success")
			return redirect(url_for('transactions.list_transactions'))
		except Exception as error:  # pragma: no cover - flash only
			logger.error("Error updating transaction %s: %s", txn_id, error)
			flash(f"Error updating transaction: {error}", "error")

	try:
		txn = db_connector.get_transaction_by_id(txn_id)
		if not txn:
			flash("Transaction not found", "error")
			return redirect(url_for('transactions.list_transactions'))
		return render_template('transactions/edit.html', transaction=txn)
	except Exception as error:  # pragma: no cover - flash only
		logger.error("Error fetching transaction %s: %s", txn_id, error)
		flash(f"Error loading transaction: {error}", "error")
		return redirect(url_for('transactions.list_transactions'))


@transactions_bp.route('/delete/<int:txn_id>', methods=['POST'])
@login_required
def delete_transaction(txn_id: int):
	"""Delete a transaction."""
	try:
		db_connector.delete_transaction(txn_id)
		flash("Transaction deleted successfully", "success")
	except Exception as error:  # pragma: no cover - flash only
		logger.error("Error deleting transaction %s: %s", txn_id, error)
		flash(f"Error deleting transaction: {error}", "error")

	return redirect(url_for('transactions.list_transactions'))

