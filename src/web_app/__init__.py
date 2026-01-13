import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

from flask import Flask, redirect, url_for, request as flask_request
from flask_cors import CORS
from flask_login import LoginManager
from .stability_manager import WebStabilityManager
from .auth_manager import load_user
from .system_state import get_system_state, is_first_run, is_demo_mode, SystemState

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
    # Use SECRET_KEY from environment variable, fallback to dev key
    import secrets
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        if os.environ.get('APP_ENV') == 'production':
            app.logger.warning(
                "SECRET_KEY not set in production! "
                "Sessions will not persist across restarts."
            )
        secret_key = secrets.token_hex(32)

    app.config.from_mapping(
        SECRET_KEY=secret_key,
        # Point to the translations directory at project root
        BABEL_TRANSLATION_DIRECTORIES=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'translations')
    )
    
    if config_object:
        app.config.update(config_object)
        
    # Initialize extensions
    # Configure CORS for React SPA development (localhost:3000 and 3001)
    # In development, allow credentials (cookies) for session-based auth
    default_origins = 'http://localhost:3000,http://localhost:3001'
    cors_origins = os.environ.get('CORS_ORIGINS', default_origins).split(',')
    CORS(app, 
         origins=cors_origins,
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
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
    
    # Context Processor for System State (Docker first-run/demo mode)
    @app.context_processor
    def inject_system_state():
        """Expose system state to all templates."""
        return {
            'system_state': get_system_state().value,
            'is_demo_mode': is_demo_mode(),
            'is_first_run': is_first_run(),
        }
    
    # First-run redirect middleware (Phase 3 onboarding)
    @app.before_request
    def check_first_run():
        """
        Redirect to onboarding if first run.
        
        Checks if this is a fresh installation with no user data
        and redirects to the onboarding flow.
        """
        from flask import session
        
        # Skip for exempt endpoints (health checks, static files, auth, API)
        exempt_prefixes = [
            '/onboarding',
            '/static',
            '/health',
            '/api/',
            '/auth/',
        ]
        
        if any(flask_request.path.startswith(prefix) for prefix in exempt_prefixes):
            return None
        
        # Skip if user explicitly skipped onboarding
        if session.get('onboarding_skipped'):
            return None
        
        # Redirect to onboarding if first run and blueprint exists
        if is_first_run() and 'onboarding' in app.blueprints:
            return redirect(url_for('onboarding.index'))
        
        return None
    
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

    # Onboarding blueprint for first-run experience
    from .blueprints.onboarding import bp as onboarding_bp
    app.register_blueprint(onboarding_bp)

    # Data integrations blueprint for API connections
    from .blueprints.integrations import integrations_bp
    app.register_blueprint(integrations_bp)

    # Root-level health check for Docker (no authentication required)
    @app.route('/health')
    def root_health():
        """
        Root-level health check for Docker/Kubernetes.

        Simple endpoint that returns 200 if the application is running.
        Use /api/health for more detailed health status.
        """
        return {'status': 'healthy', 'app': 'Personal Investment System'}, 200

    # Custom error handlers for better UX
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors with custom page."""
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors with custom page."""
        from flask import render_template
        app.logger.error(f'Server Error: {error}')
        return render_template('errors/500.html'), 500

    return app



