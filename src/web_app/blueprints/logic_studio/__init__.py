from flask import Blueprint

logic_studio_bp = Blueprint('logic_studio', __name__)

from . import routes
