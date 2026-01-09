import logging
import yaml
from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from . import assets_bp
from src.portfolio_lib.taxonomy_manager import TaxonomyManager

logger = logging.getLogger(__name__)


def _load_manager() -> TaxonomyManager:
	"""Helper to load the taxonomy manager."""
	return TaxonomyManager()


@assets_bp.route('/')
@login_required
def list_assets():
	"""List all asset mappings for review."""
	try:
		tm = _load_manager()
		config = tm.config

		asset_mapping = config.get('asset_mapping', {})
		pattern_mapping = config.get('pattern_mapping', {})

		mappings = [
			{
				'name': asset_name,
				'category': category,
				'type': 'exact'
			}
			for asset_name, category in asset_mapping.items()
		]

		pattern_entries = [
			{
				'name': pattern,
				'category': category,
				'type': 'pattern'
			}
			for pattern, category in pattern_mapping.items()
		]

		mappings.extend(pattern_entries)
		mappings.sort(key=lambda item: (item['category'], item['name']))

		categories = sorted({item['category'] for item in mappings})

		return render_template('assets/list.html', mappings=mappings, categories=categories)
	except Exception as error:  # pragma: no cover - flash only
		logger.error("Error listing assets: %s", error)
		flash(f"Error loading asset taxonomy: {error}", "error")
		return render_template('assets/list.html', mappings=[], categories=[])


@assets_bp.route('/add', methods=['POST'])
@login_required
def add_mapping():
	"""Add a new asset mapping entry."""
	asset_name = request.form.get('asset_name', '').strip()
	category = request.form.get('category', '').strip()
	mapping_type = request.form.get('mapping_type', 'exact')

	if not asset_name or not category:
		flash("Asset name and category are required", "error")
		return redirect(url_for('assets.list_assets'))

	try:
		tm = _load_manager()
		config = tm.config

		if mapping_type == 'pattern':
			pattern_mapping = config.setdefault('pattern_mapping', {})
			pattern_mapping[asset_name] = category
		else:
			asset_mapping = config.setdefault('asset_mapping', {})
			asset_mapping[asset_name] = category

		with open(tm.config_path, 'w', encoding='utf-8') as config_file:
			yaml.dump(config, config_file, allow_unicode=True, default_flow_style=False, sort_keys=False)

		flash(f"Added mapping for {asset_name}", "success")
	except Exception as error:  # pragma: no cover - flash only
		logger.error("Error adding mapping: %s", error)
		flash(f"Error adding mapping: {error}", "error")

	return redirect(url_for('assets.list_assets'))


@assets_bp.route('/delete', methods=['POST'])
@login_required
def delete_mapping():
	"""Delete an asset mapping entry."""
	asset_name = request.form.get('asset_name', '').strip()
	category = request.form.get('category', '').strip()
	mapping_type = request.form.get('mapping_type', 'exact')

	try:
		tm = _load_manager()
		config = tm.config

		target_mapping = config.get('pattern_mapping' if mapping_type == 'pattern' else 'asset_mapping', {})

		if asset_name in target_mapping and target_mapping[asset_name] == category:
			target_mapping.pop(asset_name, None)
			with open(tm.config_path, 'w', encoding='utf-8') as config_file:
				yaml.dump(config, config_file, allow_unicode=True, default_flow_style=False, sort_keys=False)
			flash(f"Removed mapping for {asset_name}", "success")
		else:
			flash("Mapping not found", "warning")
	except Exception as error:  # pragma: no cover - flash only
		logger.error("Error deleting mapping: %s", error)
		flash(f"Error deleting mapping: {error}", "error")

	return redirect(url_for('assets.list_assets'))

