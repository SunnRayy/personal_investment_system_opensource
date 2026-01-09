import logging
import time
import json
from pathlib import Path
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional

from src.data_manager.manager import DataManager
from src.portfolio_lib.data_integration import PortfolioAnalysisManager
from src.portfolio_lib.taxonomy_manager import TaxonomyManager
from src.financial_analysis.analyzer import FinancialAnalyzer
from src.report_generators.real_report import build_real_data_dict
from src.report_builders.attribution_builder import AttributionBuilder
from src.portfolio_lib.holdings_calculator import HoldingsCalculator
from src.portfolio_lib.price_service import PriceService
from src.investment_optimization.time_series_analyzer import TimeSeriesAnalyzer
from src.web_app.services.correlation_service import get_correlation_service

logger = logging.getLogger(__name__)

class NumpyEncoder(json.JSONEncoder):
    """Custom encoder for NumPy data types"""
    def default(self, obj):
        import pandas as pd
        from datetime import datetime
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32,
                              np.float64)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

class ReportDataService:
    """
    Service to prepare data for interactive reports.
    Decouples data preparation from HTML generation.
    """
    
    CACHE_FILE = Path('data/cache/report_data_cache.json')
    CACHE_DURATION = 300  # 5 minutes - balances freshness with performance

    def __init__(self, config_path: str = 'config/settings.yaml', holdings_source: str = 'auto'):
        """
        Initialize ReportDataService.
        
        Args:
            config_path: Path to settings.yaml
            holdings_source: 'excel', 'database', or 'auto' (auto-detect from config)
        """
        self.config_path = config_path
        self.data_manager = DataManager(config_path=config_path)
        self.portfolio_manager = PortfolioAnalysisManager()
        self.taxonomy_manager = TaxonomyManager()
        self.financial_analyzer = FinancialAnalyzer(config_dir='config') # Assuming config dir is 'config'
        
        # Phase 6.3: Holdings calculation source
        self.holdings_source = holdings_source
        if holdings_source == 'auto':
            # Auto-detect from config
            self.holdings_source = self._detect_holdings_source()
        
        # Initialize HoldingsCalculator if using database mode
        self.holdings_calculator = None
        self.price_service = None
        if self.holdings_source == 'database':
            self.price_service = PriceService(data_manager=self.data_manager)
            self.holdings_calculator = HoldingsCalculator(price_service=self.price_service)
            logger.info("✅ ReportService: Using HoldingsCalculator (database mode)")
        else:
            logger.info("✅ ReportService: Using Excel holdings (legacy mode)")
        
        # Caching mechanism
        self._cache = self._load_cache()

    def _detect_holdings_source(self) -> str:
        """
        Auto-detect holdings source from config.
        
        Returns:
            'database' if database mode is enabled, otherwise 'excel'
        """
        try:
            import yaml
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            db_mode = config.get('database', {}).get('mode', 'excel')
            if db_mode == 'database':
                return 'database'
        except Exception as e:
            logger.warning(f"Could not detect holdings source from config: {e}")
        
        return 'excel'
    
    def _load_cache(self) -> Optional[Dict[str, Any]]:
        """Load cache from disk if valid."""
        try:
            if self.CACHE_FILE.exists():
                with open(self.CACHE_FILE, 'r') as f:
                    cache_data = json.load(f)
                    
                timestamp = cache_data.get('timestamp', 0)
                age = time.time() - timestamp
                
                if age < self.CACHE_DURATION:
                    logger.info(f"📂 Loaded persistent cache from {self.CACHE_FILE} (Age: {age:.1f}s)")
                    return cache_data.get('data')
                else:
                    logger.info(f"⚠️ Cache expired (Age: {age:.1f}s)")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load cache: {e}")
        return None

    def _save_cache(self, data: Dict[str, Any]):
        """Save data to persistent cache."""
        try:
            self.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.CACHE_FILE, 'w') as f:
                json.dump({
                    'timestamp': time.time(),
                    'data': data
                }, f, cls=NumpyEncoder)
            logger.info(f"💾 Saved persistent cache to {self.CACHE_FILE}")
        except Exception as e:
            logger.error(f"❌ Failed to save cache: {e}")

    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache status information."""
        try:
            if self.CACHE_FILE.exists():
                mtime = self.CACHE_FILE.stat().st_mtime
                age = time.time() - mtime
                
                return {
                    'exists': True,
                    'timestamp': mtime,
                    'age_seconds': age,
                    'is_valid': age < self.CACHE_DURATION,
                    'formatted_time': datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
                }
            else:
                return {'exists': False, 'is_valid': False}
        except Exception as e:
            logger.error(f"Error checking cache info: {e}")
            return {'exists': False, 'is_valid': False}

    def clear_cache(self):
        """Force clears the in-memory cache."""
        self._cache = None
        # Optionally clear file cache too, but usually in-memory is what hits first
        if self.CACHE_FILE.exists():
            try:
                os.remove(self.CACHE_FILE)
            except OSError:
                pass
        logger.info("ReportDataService cache cleared manually.")

    def get_portfolio_data(self, force_refresh: bool = False, active_risk_profile: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates the complete data dictionary required for the Portfolio Analysis report.
        Uses a 5-minute cache to balance freshness with performance.
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh data
            active_risk_profile: Optional override for risk profile (e.g. '成长型', '稳健型')
        """
        # Check cache first (unless force_refresh or risk profile override)
        if not force_refresh and active_risk_profile is None and self._cache is not None:
            logger.debug("ReportDataService: Returning cached portfolio data")
            return self._cache
        
        start_time = time.perf_counter()
        logger.debug(f"ReportDataService: Loading portfolio data... (Profile: {active_risk_profile or 'Default'})")
        
        # Phase 6.3: Use HoldingsCalculator if in database mode
        # NOTE (2025-12-16): HoldingsCalculator has bugs (missing SGOV, wrong FX for USD deposits).
        # Always use DataManager.get_holdings() for now, which is the authoritative source (same as Parity Dashboard).
        # TODO: Debug HoldingsCalculator and re-enable once parity is confirmed.
        # if self.holdings_source == 'database' and self.holdings_calculator:
        #     logger.info("📊 Using HoldingsCalculator for holdings data...")
        #     ... (disabled)
        
        # Excel mode (legacy) - ALWAYS use this for now for consistency with Parity
        current_holdings = self.data_manager.get_holdings(latest_only=True)
        
        balance_sheet = self.data_manager.get_balance_sheet()
        
        # 2. Calculate Total Portfolio Value
        total_portfolio_value = 0
        if current_holdings is not None and not current_holdings.empty:
            if 'Market_Value_CNY' in current_holdings.columns:
                total_portfolio_value = current_holdings['Market_Value_CNY'].sum()
            elif 'Market_Value' in current_holdings.columns:
                total_portfolio_value = current_holdings['Market_Value'].sum()
        
        if total_portfolio_value == 0 and balance_sheet is not None and not balance_sheet.empty:
            # Fallback to balance sheet
            latest_balance = balance_sheet.iloc[-1]
            total_portfolio_value = latest_balance.get('Total_Assets_Calc_CNY', 0) or latest_balance.get('Net_Worth_Calc_CNY', 0)
            
        # 3. Calculate Last Month Change
        last_month_change = 0.0
        if balance_sheet is not None and not balance_sheet.empty and len(balance_sheet) >= 2:
            try:
                latest_val = balance_sheet.iloc[-1].get('Total_Assets_Calc_CNY', 0)
                prev_val = balance_sheet.iloc[-2].get('Total_Assets_Calc_CNY', 0)
                if prev_val > 0:
                    last_month_change = ((latest_val - prev_val) / prev_val) * 100
            except Exception as e:
                logger.warning(f"Could not calculate last month change: {e}")

        # 4. Get Real-time Rates (Optional/Best Effort)
        usd_cny_rate = None
        employer_stock_price_usd = None
        try:
            from src.data_manager.connectors.google_finance_connector import get_google_finance_connector
            connector = get_google_finance_connector()
            usd_cny_rate = connector.get_exchange_rate('USD', 'CNY')
            employer_stock_price_usd = connector.get_stock_price('AMZN')
        except Exception as e:
            logger.warning(f"Could not fetch real-time rates: {e}")
            # Fallback to Excel data
            if balance_sheet is not None and not balance_sheet.empty:
                latest_row = balance_sheet.iloc[-1]
                usd_cny_rate = latest_row.get('Ref_USD_FX_Rate')
                employer_stock_price_usd = latest_row.get('Ref_Employer_Stock_Price_USD')

        # 5. Build Data Dictionary using existing logic
        # We reuse build_real_data_dict to ensure 100% parity with static reports
        real_data = build_real_data_dict(
            self.data_manager,
            self.portfolio_manager,
            self.taxonomy_manager,
            self.financial_analyzer,
            current_holdings,
            total_portfolio_value,
            last_month_change,
            usd_cny_rate,
            employer_stock_price_usd,
            active_risk_profile=active_risk_profile
        )
        
        # 6. Add Correlation Analysis (Sub-class and Asset levels)
        try:
            historical_holdings = self.data_manager.get_holdings(latest_only=False)
            if historical_holdings is not None and not historical_holdings.empty:
                ts_analyzer = TimeSeriesAnalyzer(historical_holdings, balance_sheet)
                asset_returns = ts_analyzer.calculate_asset_returns()
                
                # Filter to market assets only (exclude deposits, cash, pensions, property)
                exclude_patterns = ['Cash_', 'Pension_', 'Property_', 'Insurance_', 'BankWealth_', 'Ins_']
                
                def is_market_asset(name: str) -> bool:
                    """Check if asset is suitable for correlation analysis."""
                    if any(name.startswith(p) for p in exclude_patterns):
                        return False
                    if 'Deposit' in name:
                        return False
                    return True

                market_assets = [col for col in asset_returns.columns if is_market_asset(col)]
                
                if market_assets:
                    filtered_returns = asset_returns[market_assets]
                    filtered_returns = filtered_returns.loc[:, filtered_returns.std() > 0.001]
                    
                    if len(filtered_returns.columns) >= 2:
                        correlation_service = get_correlation_service()
                        
                        # --- Build asset name mapping for display ---
                        asset_names = {}
                        for asset_id in filtered_returns.columns:
                            # Try to get friendly name from holdings
                            try:
                                if hasattr(historical_holdings, 'xs'):
                                    asset_data = historical_holdings.xs(asset_id, level=1, drop_level=False)
                                    if 'Asset_Name' in asset_data.columns and not asset_data.empty:
                                        asset_names[asset_id] = asset_data['Asset_Name'].iloc[-1]
                                    else:
                                        asset_names[asset_id] = asset_id
                                else:
                                    asset_names[asset_id] = asset_id
                            except:
                                asset_names[asset_id] = asset_id
                        
                        # --- Calculate sub-class level correlations ---
                        subclass_returns = {}
                        asset_to_subclass = {}
                        
                        for asset_id in filtered_returns.columns:
                            try:
                                subclass, _ = self.taxonomy_manager.get_asset_classification(asset_id)
                                if not subclass or subclass in ('其他_子类', 'Other', None):
                                    subclass = 'Other'
                            except:
                                subclass = 'Other'
                            
                            asset_to_subclass[asset_id] = subclass
                            
                            if subclass not in subclass_returns:
                                subclass_returns[subclass] = []
                            subclass_returns[subclass].append(filtered_returns[asset_id])
                        
                        # Aggregate returns by sub-class (simple average)
                        import pandas as pd
                        subclass_agg = pd.DataFrame()
                        for subclass, returns_list in subclass_returns.items():
                            if len(returns_list) == 1:
                                subclass_agg[subclass] = returns_list[0]
                            else:
                                subclass_agg[subclass] = pd.concat(returns_list, axis=1).mean(axis=1)
                        
                        # Filter sub-classes with enough variance
                        subclass_agg = subclass_agg.loc[:, subclass_agg.std() > 0.0001]
                        
                        # Calculate sub-class level correlation
                        if len(subclass_agg.columns) >= 2:
                            subclass_corr_data = correlation_service.get_correlation_data(subclass_agg)
                        else:
                            subclass_corr_data = {'matrix': {}, 'high_corr_pairs': [], 'alerts': [], 'avg_correlation': 0.0}
                        
                        # Calculate asset-level correlation (original)
                        asset_corr_data = correlation_service.get_correlation_data(filtered_returns)
                        
                        # Combine into enhanced structure
                        real_data['correlation_analysis'] = {
                            'subclass_matrix': subclass_corr_data.get('matrix', {}),
                            'subclass_assets': sorted(subclass_agg.columns.tolist()) if not subclass_agg.empty else [],
                            'asset_matrix': asset_corr_data.get('matrix', {}),
                            'asset_names': asset_names,
                            'high_corr_pairs': subclass_corr_data.get('high_corr_pairs', []),
                            'avg_correlation': subclass_corr_data.get('avg_correlation', 0.0),
                            'alerts': subclass_corr_data.get('alerts', [])
                        }
                        logger.info(f"✅ Correlation analysis: {len(subclass_agg.columns)} sub-classes, {len(filtered_returns.columns)} assets")
                    else:
                        real_data['correlation_analysis'] = {'subclass_matrix': {}, 'asset_matrix': {}, 'asset_names': {}, 'high_corr_pairs': [], 'alerts': [], 'avg_correlation': 0.0}
                else:
                    real_data['correlation_analysis'] = {'subclass_matrix': {}, 'asset_matrix': {}, 'asset_names': {}, 'high_corr_pairs': [], 'alerts': [], 'avg_correlation': 0.0}
            else:
                real_data['correlation_analysis'] = {'subclass_matrix': {}, 'asset_matrix': {}, 'asset_names': {}, 'high_corr_pairs': [], 'alerts': [], 'avg_correlation': 0.0}
        except Exception as e:
            logger.warning(f"Could not add correlation analysis: {e}")
            import traceback
            traceback.print_exc()
            real_data['correlation_analysis'] = {'subclass_matrix': {}, 'asset_matrix': {}, 'asset_names': {}, 'high_corr_pairs': [], 'alerts': [], 'avg_correlation': 0.0}


        # Update cache
        self._cache = real_data
        self._save_cache(real_data)
        
        logger.info(f"✅ ReportDataService: Data prepared in {time.perf_counter() - start_time:.2f}s")
        return real_data

    def get_attribution_data(self, period_months: int = 12) -> Dict[str, Any]:
        """
        Get attribution analysis data.
        Uses a separate cache key as this is a distinct heavy calculation.
        """
        cache_key = f"attribution_data_{period_months}m"
        # Try to load specific cache (ignoring the main report cache structure for now)
        # For simplicity, we won't implement persistent caching for this specific report yet
        # unless it proves slow. But we can add a simple in-memory check if needed.
        
        logger.info(f"ReportDataService: Fetching attribution data for {period_months} months...")
        try:
            builder = AttributionBuilder(self.data_manager)
            # Pass managers if needed, but Builder initializes them itself currently.
            # Ideally we should inject them to share instances/cache:
            # builder.portfolio_manager = self.portfolio_manager 
            # But AttributionBuilder.__init__ currently creates its own. 
            # We'll leave it as is for Phase 1 to minimize coupling changes.
            
            return builder.build_attribution_data(period_months=period_months)
        except Exception as e:
            logger.error(f"Error in get_attribution_data: {e}")
            return {
                'error': str(e),
                'summary': {'portfolio_return': 0},
                'waterfall_chart': {'labels': [], 'values': []},
                'asset_class_table': []
            }
