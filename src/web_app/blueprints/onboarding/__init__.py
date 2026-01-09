"""
Onboarding Blueprint for first-run experience.

Provides routes for:
- Welcome page with mode selection (Demo/Upload/Skip)
- CSV/Excel file upload
- Column mapping for data import
- Onboarding completion
"""

from flask import Blueprint

bp = Blueprint('onboarding', __name__, url_prefix='/onboarding')

from src.web_app.blueprints.onboarding import routes
