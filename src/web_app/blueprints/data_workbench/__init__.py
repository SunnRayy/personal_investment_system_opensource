from flask import Blueprint

data_workbench_bp = Blueprint('data_workbench', __name__, url_prefix='/workbench')

from . import routes
