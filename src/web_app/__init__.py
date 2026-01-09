import os
import logging
from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from .stability_manager import WebStabilityManager
from .auth_manager import load_user

def create_app(config_object=None):
    """Application Factory"""
    app = Flask(__name__)
    
    # Configure Logging
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    file_handler = logging.FileHandler('logs/web_app.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    app.logger.addHandler(file_handler)
    logging.getLogger('src').addHandler(file_handler)
    logging.getLogger('src').setLevel(logging.INFO)
    
    # Configure app
    app.config.from_mapping(
        SECRET_KEY='dev-secret-key-change-in-production',
        # Point to the translations directory at project root
        BABEL_TRANSLATION_DIRECTORIES=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'translations')
    )
    
    if config_object:
        app.config.update(config_object)
        
    # Initialize extensions
    CORS(app)
    
    # Initialize Login Manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    login_manager.user_loader(load_user)
    
    # Initialize Stability Manager
    WebStabilityManager(app)
    
    # Initialize Babel for I18n
    from flask_babel import Babel
    from flask import request, session
    
    def get_locale():
        # 1. Check if user has explicitly set a language in session
        if 'lang' in session:
            return session['lang']
        # 2. Check for 'lang' query parameter (useful for testing/overrides)
        if request.args.get('lang'):
            session['lang'] = request.args.get('lang')
            return session['lang']
        # 3. Best match from request headers
        return request.accept_languages.best_match(['en', 'zh']) or 'en'
        
    babel = Babel(app, locale_selector=get_locale)
    
    @app.context_processor
    def inject_locale():
        return dict(get_locale=get_locale)
    
    # Context Processor for Cache Status
    @app.context_processor
    def inject_cache_status():
        from src.web_app.services.report_service import ReportDataService
        
        try:
            service = ReportDataService()
            cache_info = service.get_cache_info()
            return dict(cache_info=cache_info)
        except Exception:
            return dict(cache_info=None)
    
    # Register Blueprints
    from .blueprints.main import main_bp
    app.register_blueprint(main_bp)
    
    from .blueprints.api import api_bp
    app.register_blueprint(api_bp)
    
    from .blueprints.transactions import transactions_bp
    app.register_blueprint(transactions_bp)
    
    from .blueprints.assets import assets_bp
    app.register_blueprint(assets_bp)
    
    from .blueprints.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)

    from .blueprints.reports import reports_bp
    app.register_blueprint(reports_bp, url_prefix='/reports')
    
    from .blueprints.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .blueprints.data_workbench import data_workbench_bp
    app.register_blueprint(data_workbench_bp)
    
    from .blueprints.logic_studio import logic_studio_bp
    app.register_blueprint(logic_studio_bp, url_prefix='/logic-studio')

    from .blueprints.wealth.routes import wealth_bp
    app.register_blueprint(wealth_bp)

    from .blueprints.simulation import simulation_bp
    app.register_blueprint(simulation_bp, url_prefix='/reports/simulation')
    
    return app



