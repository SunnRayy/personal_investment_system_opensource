# HTML Report Generator
# This module provides functionality to generate static HTML reports from financial data

import os
import logging
from typing import Dict, Any, List
from jinja2 import Environment, FileSystemLoader
from src.localization import _

logger = logging.getLogger(__name__)


def format_lifetime_performance_for_template(lifetime_data: List[Dict]) -> List[Dict]:
    """
    Format raw lifetime performance data for template display.
    
    Args:
        lifetime_data: Raw performance data from financial_analyzer
        
    Returns:
        Formatted list of dicts with template-friendly keys and formatted values
    """
    formatted = []
    
    for asset in lifetime_data:
        # Determine holding period string
        holding_days = asset.get('holding_period_days', 0)
        if holding_days >= 365:
            holding_period = f"{holding_days // 365}y {(holding_days % 365) // 30}m"
        else:
            holding_period = f"{holding_days // 30}m {holding_days % 30}d"
        
        # Determine status
        status = _("Active") if asset.get('is_currently_held', False) else _("Closed")
        
        # Get numeric values
        total_invested = asset.get('total_amount_invested', 0) or 0
        current_value = asset.get('current_market_value', 0) or 0
        profit_loss = asset.get('total_pnl', 0) or 0
        return_pct = asset.get('total_return_pct', 0) or 0
        xirr = asset.get('xirr_pct')
        
        # Determine performance status based on XIRR or return
        performance_metric = xirr if xirr is not None else return_pct
        if performance_metric is None:
            performance_status = "N/A"
        elif performance_metric >= 20:
            performance_status = _("Excellent")
        elif performance_metric >= 10:
            performance_status = _("Good")
        elif performance_metric >= 0:
            performance_status = _("Average")
        else:
            performance_status = _("Poor")
        
        formatted.append({
            'asset_name': asset.get('asset_name', 'Unknown'),
            'asset_class': asset.get('asset_class', 'Unknown'),
            'holding_period': holding_period,
            'status': status,
            'total_invested': f"{total_invested:,.0f}",
            'current_value': f"{current_value:,.0f}",
            'profit_loss': f"{profit_loss:,.0f}",
            'profit_loss_float': profit_loss,
            'return_percent': f"{return_pct:.2f}",
            'return_percent_float': return_pct,
            'xirr': f"{xirr:.2f}" if xirr is not None else None,
            'xirr_float': xirr,
            'performance_status': performance_status
        })
    
    return formatted


def format_xirr_diagnostics_for_template(xirr_diagnostics: Dict) -> Dict:
    """
    Transform XIRR diagnostics from {success: [], warning: [], error: []} structure
    to template-friendly format with calculations list and summary stats.
    
    Args:
        xirr_diagnostics: Dict with 'success', 'warning', 'error' keys containing lists
        
    Returns:
        Dict with 'calculations' list and 'summary' dict for template rendering
    """
    if not xirr_diagnostics or not isinstance(xirr_diagnostics, dict):
        return {
            'calculations': [],
            'summary': {
                'successful': 0,
                'warnings': 0,
                'errors': 0,
                'total': 0
            }
        }
    
    # Combine all entries into single calculations list
    calculations = []
    
    # Add success entries
    for entry in xirr_diagnostics.get('success', []):
        calculations.append({
            'asset_name': entry.get('asset_name', 'Unknown'),
            'xirr': entry.get('xirr'),
            'method': entry.get('method', 'unknown'),
            'status': 'success',
            'reason': entry.get('reason', 'Successful calculation'),
            'cash_flows_count': entry.get('cash_flows_count', 0),
            'period_days': entry.get('period_days', 0)
        })
    
    # Add warning entries
    for entry in xirr_diagnostics.get('warning', []):
        calculations.append({
            'asset_name': entry.get('asset_name', 'Unknown'),
            'xirr': entry.get('xirr'),
            'method': entry.get('method', 'approximation'),
            'status': 'warning',
            'reason': entry.get('reason', 'Approximated result'),
            'cash_flows_count': entry.get('cash_flows_count', 0),
            'period_days': entry.get('period_days', 0)
        })
    
    # Add error entries
    for entry in xirr_diagnostics.get('error', []):
        calculations.append({
            'asset_name': entry.get('asset_name', 'Unknown'),
            'xirr': None,
            'method': entry.get('method', 'failed'),
            'status': 'error',
            'reason': entry.get('reason', 'Calculation failed'),
            'cash_flows_count': entry.get('cash_flows_count', 0),
            'period_days': entry.get('period_days', 0)
        })
    
    # Calculate summary stats
    summary = {
        'successful': len(xirr_diagnostics.get('success', [])),
        'warnings': len(xirr_diagnostics.get('warning', [])),
        'errors': len(xirr_diagnostics.get('error', [])),
        'total': len(calculations)
    }
    
    return {
        'calculations': calculations,
        'summary': summary
    }


class HTMLReporter:
    """HTML Report Generator for modular multi-page reports."""
    
    def __init__(self, templates_dir: str = None):
        """
        Initialize the HTML Reporter.
        
        Args:
            templates_dir: Path to templates directory. If None, uses default.
        """
        if templates_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            templates_dir = os.path.join(current_dir, 'templates')
        
        self.templates_dir = templates_dir
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            extensions=['jinja2.ext.i18n']
        )
        self.env.install_gettext_callables(gettext=_, ngettext=lambda s, p, n: _(p) if n > 1 else _(s), newstyle=True)
        
        # Add custom Jinja2 filters
        self.env.filters['format_number'] = self._format_number
        self.env.filters['abs'] = abs  # Add built-in abs function as filter
        
        logger.info(f"HTMLReporter initialized with templates_dir: {templates_dir}")
    
    def _format_number(self, value):
        """Custom Jinja2 filter to format numbers with thousands separator."""
        try:
            if value is None or value == '':
                return '0'
            # Convert to float if string
            if isinstance(value, str):
                value = float(value.replace(',', ''))
            return f"{value:,.0f}"
        except (ValueError, TypeError):
            return str(value)
    
    def consolidate_priority_actions(
        self,
        strategic_directive: Dict[str, Any],
        recommendations: List[Dict[str, Any]],
        alt_assets_recommendations: List[Dict[str, Any]],
        rebalancing_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Merge all action sources into single prioritized list for Action Compass.
        
        This function consolidates actions from three sources:
        1. Strategic actions from strategic_directive (market regime-based, priority 80-100)
        2. Tactical recommendations (operational, priority 70+)
        3. Alternative assets with strong signals (|score| >= 4.0)
        
        Args:
            strategic_directive: Strategic directive with action_steps and allocation_gaps
            recommendations: List of tactical recommendations from RecommendationEngine
            alt_assets_recommendations: List of alternative assets (Gold/BTC/ETH) recommendations
            rebalancing_data: Rebalancing data for portfolio context
            
        Returns:
            List of top 7 priority actions sorted by priority descending
            Each action dict contains: {category, icon, priority, action, amount, rationale, details}
        """
        consolidated_actions = []
        
        # Source 1: Strategic actions from strategic_directive
        # These are high-level market regime-based actions with priority 80-100
        if strategic_directive and 'action_steps' in strategic_directive:
            for step in strategic_directive.get('action_steps', []):
                consolidated_actions.append({
                    'category': 'STRATEGIC',
                    'icon': '🎯',
                    'priority': step.get('priority', 85),
                    'action': step.get('action', ''),
                    'amount': step.get('amount', 0),
                    'rationale': step.get('rationale', ''),
                    'details': {
                        'source': 'Strategic Directive',
                        'regime': strategic_directive.get('regime', {}).get('name_cn', 'Unknown'),
                        'allocation_changes': step.get('allocation_changes', [])
                    }
                })
        
        # Source 2: High-priority tactical recommendations (priority >= 70)
        # EXCLUDE duplicates with type='STRATEGIC_REGIME' to avoid double-display
        if recommendations:
            for rec in recommendations:
                # Skip strategic regime recommendations (already in strategic_directive)
                if rec.get('type') == 'STRATEGIC_REGIME':
                    logger.debug(f"Skipping duplicate strategic recommendation: {rec.get('action', '')[:50]}")
                    continue
                
                # Only include high-priority tactical recommendations
                priority = rec.get('priority', 0)
                if priority >= 70:
                    # Map recommendation type to category and icon
                    rec_type = rec.get('type', 'OTHER')
                    category_map = {
                        'CAPITAL_ALLOCATION': ('ALLOCATION', '💰'),
                        'PROFIT_REBALANCING': ('REBALANCING', '⚖️'),
                        'RISK_CONCENTRATION': ('RISK', '⚠️'),
                        'MARKET_TIMING': ('TIMING', '📊'),
                        'TAX_OPTIMIZATION': ('TAX', '🧾'),
                        'CASH_FLOW': ('CASH', '💵')
                    }
                    category, icon = category_map.get(rec_type, ('TACTICAL', '📋'))
                    
                    consolidated_actions.append({
                        'category': category,
                        'icon': icon,
                        'priority': priority,
                        'action': rec.get('action', ''),
                        'amount': rec.get('financial_impact', 0),
                        'rationale': rec.get('rationale', ''),
                        'details': {
                            'source': 'Tactical Recommendations',
                            'type': rec_type,
                            'action_items': rec.get('action_items', [])
                        }
                    })
        
        # Source 3: Alternative assets with strong signals (|score| >= 4.0)
        # These are Gold/BTC/ETH recommendations based on weighted scoring
        if alt_assets_recommendations:
            for alt_rec in alt_assets_recommendations:
                # Check if using Phase 3 weighted scoring data
                weighted_data = alt_rec.get('weighted_data', {})
                if weighted_data:
                    score = weighted_data.get('weighted_score', 0)
                    recommendation = weighted_data.get('recommendation', 'HOLD')
                else:
                    # Fallback to legacy recommendation structure
                    rec_data = alt_rec.get('recommendation', {})
                    recommendation = rec_data.get('recommendation', 'HOLD')
                    # Estimate score from recommendation text
                    score_map = {'STRONG_BUY': 5, 'BUY': 3, 'HOLD': 0, 'SELL': -3, 'STRONG_SELL': -5}
                    score = score_map.get(recommendation, 0)
                
                # Only include strong signals: |score| >= 4.0
                if abs(score) >= 4.0:
                    # Determine action text and icon
                    asset_name = alt_rec.get('asset_name', 'Unknown')
                    asset_icon = alt_rec.get('asset_icon', '💎')
                    
                    if recommendation in ['STRONG_BUY', 'BUY']:
                        action_verb = _('Increase') if recommendation == 'STRONG_BUY' else _('Increase Moderately')
                        priority = 75 if recommendation == 'STRONG_BUY' else 72
                    else:  # STRONG_SELL or SELL
                        action_verb = _('Decrease') if recommendation == 'STRONG_SELL' else _('Decrease Moderately')
                        priority = 75 if recommendation == 'STRONG_SELL' else 72
                    
                    action_text = f"{action_verb}{asset_name}"
                    
                    # Extract rationale from weighted indicators
                    rationale_parts = []
                    if weighted_data:
                        for indicator in weighted_data.get('indicators', []):
                            if indicator.get('weight', 0) > 0:
                                rationale_parts.append(
                                    f"{indicator.get('name', '')}: {indicator.get('signal', '')} "
                                    f"(score: {indicator.get('score', 0):.1f})"
                                )
                    rationale = ' | '.join(rationale_parts) if rationale_parts else f"{recommendation} signal"
                    
                    consolidated_actions.append({
                        'category': 'ALT_ASSETS',
                        'icon': asset_icon,
                        'priority': priority,
                        'action': action_text,
                        'amount': 0,  # No specific amount for alt assets
                        'rationale': rationale,
                        'details': {
                            'source': 'Alternative Assets Advisor',
                            'asset': asset_name,
                            'recommendation': recommendation,
                            'score': score,
                            'weighted_data': weighted_data
                        }
                    })
        
        # Sort by priority descending and return top 7
        consolidated_actions.sort(key=lambda x: x.get('priority', 0), reverse=True)
        top_actions = consolidated_actions[:7]
        
        logger.info(f"Consolidated {len(consolidated_actions)} actions from all sources, returning top {len(top_actions)}")
        logger.debug(f"Top actions priorities: {[a.get('priority') for a in top_actions]}")
        
        return top_actions
    
    
    def _prepare_alt_assets_recommendations(self, unified_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Prepare alternative assets (Gold, BTC, ETH) recommendations for Action Compass.
        
        Extracts recommendation data from gold_analysis and crypto_analysis and formats
        it for display in the Action Compass template. Includes Phase 3 weighted scoring data.
        
        Args:
            unified_context: Complete analysis results from UnifiedAnalysisEngine
            
        Returns:
            List of alt-assets recommendation dicts with asset_name, recommendation, and weighted_data
        """
        # Check if alt_assets_recommendations already exists in context (Phase 3)
        if 'alt_assets_recommendations' in unified_context:
            alt_assets_recs = unified_context.get('alt_assets_recommendations', [])
            logger.info(f"Using existing alt_assets_recommendations with {len(alt_assets_recs)} items (Phase 3 weighted scoring)")
            return alt_assets_recs
        
        # Fallback: Build alt_assets_recommendations from gold_analysis and crypto_analysis (legacy)
        alt_assets_recs = []
        
        # Extract Gold recommendation
        gold_analysis = unified_context.get('gold_analysis', {})
        if gold_analysis.get('status') == 'success':
            gold_rec = gold_analysis.get('recommendation', {})
            if gold_rec:
                alt_assets_recs.append({
                    'asset_name': 'Gold',
                    'asset_icon': '🏅',
                    'recommendation': gold_rec
                })
        
        # Extract BTC recommendation
        crypto_analysis = unified_context.get('crypto_analysis', {})
        if crypto_analysis.get('status') == 'success':
            btc_rec = crypto_analysis.get('btc_recommendation', {})
            if btc_rec:
                alt_assets_recs.append({
                    'asset_name': 'Bitcoin (BTC)',
                    'asset_icon': '₿',
                    'recommendation': btc_rec
                })
            
            # Extract ETH recommendation
            eth_rec = crypto_analysis.get('eth_recommendation', {})
            if eth_rec:
                alt_assets_recs.append({
                    'asset_name': 'Ethereum (ETH)',
                    'asset_icon': 'Ξ',
                    'recommendation': eth_rec
                })
        
        logger.info(f"Prepared {len(alt_assets_recs)} alternative assets recommendations (legacy mode)")
        return alt_assets_recs
    
    def _split_context(self, unified_context: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Split unified analysis context into 4 separate report contexts.
        
        Args:
            unified_context: Complete analysis results from UnifiedAnalysisEngine
            
        Returns:
            Dict with keys: 'index', 'portfolio', 'thermometer', 'compass'
        """
        logger.info("Splitting unified context into 4 report contexts")
        
        # Index context: High-level summary only
        # Ensure numeric values are properly typed
        def safe_float(value, default=0.0):
            try:
                return float(value) if value not in (None, '', 'N/A') else default
            except (ValueError, TypeError):
                return default
        
        def safe_int(value, default=0):
            try:
                return int(value) if value not in (None, '', 'N/A') else default
            except (ValueError, TypeError):
                return default
        
        # 1. Index Page Context
        index_context = {
            'total_value': safe_float(unified_context.get('total_portfolio_value_numeric', 0)),
            'overall_xirr': safe_float(unified_context.get('overall_xirr', 0)),
            'last_month_change': safe_float(unified_context.get('last_month_change', 0)),
            'num_holdings': len(unified_context.get('holdings', [])),
            'top_level_allocation_json': unified_context.get('top_level_allocation_json', '{}'),
            'generation_time': unified_context.get('generation_time', ''),
            'validation_report': unified_context.get('validation_report', {}),  # Add validation report
            'checksums': unified_context.get('checksums', {}),  # Add checksums
            'usd_cny_rate': unified_context.get('usd_cny_rate'),  # Add USD/CNY rate for System Status
            'employer_stock_price_usd': unified_context.get('employer_stock_price_usd'),  # Add employer stock price for System Status
            'active_page': 'index'
        }
        
        # Portfolio context: All dashboard data (preserve all existing keys)
        portfolio_context = dict(unified_context)
        portfolio_context['active_page'] = 'portfolio'
        
        # Ensure required keys have defaults to prevent template errors
        portfolio_defaults = {
            'xirr_metadata': {'show_warning': False, 'reason': ''},
            'gains_analysis_data': {
                'realized_gains': 0,
                'unrealized_gains': 0,
                'total_gains': 0,
                'subclass_breakdown': []
            },
            'holdings_table': [],
            'lifetime_performance_table': [],
            'xirr_diagnostics': {
                'success_count': 0,
                'approximation_count': 0,
                'failure_count': 0,
                'details': []
            },
            'top_level_allocation_json': '{}',
            'sub_class_allocation_json': '{}',
            'portfolio_growth_json': '{}',
            'cash_flow_json': '{}',
            'twr_json': '{}',
            'drawdown_json': '{}',
            'forecast_json': '{}',
            'top_level_performance': [],
            'subclass_performance': []
        }
        for key, default_value in portfolio_defaults.items():
            portfolio_context.setdefault(key, default_value)
        
        # Template compatibility: Map and format data keys for template variable names
        raw_lifetime_data = portfolio_context.get('lifetime_performance_data', [])
        portfolio_context['lifetime_performance'] = format_lifetime_performance_for_template(raw_lifetime_data)
        
        # Transform XIRR diagnostics to template format
        raw_xirr_diagnostics = portfolio_context.get('xirr_diagnostics', {})
        portfolio_context['xirr_diagnostics'] = format_xirr_diagnostics_for_template(raw_xirr_diagnostics)
        
        # Thermometer context: Market indicators only
        thermometer_context = {
            'generation_time': unified_context.get('generation_time', ''),
            'market_regime': unified_context.get('market_regime', {}),  # Phase 2a: Market Regime moved here
            'market_thermometer': unified_context.get('market_thermometer', {}),
            'gold_analysis': unified_context.get('gold_analysis', {}),  # Phase 1.2: Gold indicators
            'crypto_analysis': unified_context.get('crypto_analysis', {}),  # Phase 2.4: Crypto indicators (BTC & ETH)
            'active_page': 'thermometer'
        }
        
        # Compass context: Recommendations and actions
        compass_context = {
            'generation_time': unified_context.get('generation_time', ''),
            'market_regime': unified_context.get('market_regime', {}),
            'strategic_directive': unified_context.get('strategic_directive'),  # Phase 1: Strategic Directive
            'recommendations': unified_context.get('recommendations', []),
            'recommendation_stats': unified_context.get('recommendation_stats', {}),
            'rebalancing_data': unified_context.get('rebalancing_data', {}),
            'capital_allocation_suggestion': unified_context.get('capital_allocation_suggestion', {}),
            'proportional_allocation': unified_context.get('proportional_allocation', {}),
            'sub_class_breakdowns': unified_context.get('sub_class_breakdowns', []),
            'rsu_alerts': unified_context.get('rsu_alerts', []),
            'total_portfolio_value_numeric': unified_context.get('total_portfolio_value_numeric', 0),
            'insurance_value': unified_context.get('insurance_value', 0),
            'alt_assets_recommendations': self._prepare_alt_assets_recommendations(unified_context),  # Phase 1: Alt-assets
            'active_page': 'compass'
        }
        
        # Phase 2a: Add consolidated priority actions (top 7 from all sources)
        compass_context['consolidated_actions'] = self.consolidate_priority_actions(
            strategic_directive=compass_context['strategic_directive'] or {},
            recommendations=compass_context['recommendations'],
            alt_assets_recommendations=compass_context['alt_assets_recommendations'],
            rebalancing_data=compass_context['rebalancing_data']
        )
        
        logger.info(f"Context split completed: index={len(index_context)} keys, "
                   f"portfolio={len(portfolio_context)} keys, "
                   f"thermometer={len(thermometer_context)} keys, "
                   f"compass={len(compass_context)} keys")
        
        return {
            'index': index_context,
            'portfolio': portfolio_context,
            'thermometer': thermometer_context,
            'compass': compass_context
        }
    
    def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a template with the given context.
        
        Args:
            template_name: Name of the template file
            context: Context data for rendering
            
        Returns:
            Rendered HTML string
        """
        logger.debug(f"Rendering template: {template_name}")
        template = self.env.get_template(template_name)
        return template.render(**context)
    
    def generate_reports(self, unified_context: Dict[str, Any], output_dir: str) -> Dict[str, str]:
        """
        Generate all 4 HTML reports from unified context.
        
        Args:
            unified_context: Complete analysis context from UnifiedAnalysisEngine
            output_dir: Directory where HTML files should be written
            
        Returns:
            Dict mapping filename to output filepath
        """
        logger.info("Starting modular report generation")
        
        # Split context
        contexts = self._split_context(unified_context)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Define reports to generate
        reports_config = [
            ('index.html', 'index', 'Landing Page'),
            ('portfolio_report.html', 'portfolio', 'Portfolio Report'),
            ('market_thermometer.html', 'thermometer', 'Market Thermometer'),
            ('action_compass.html', 'compass', 'Action Compass')
        ]
        
        # Generate each report
        output_files = {}
        for template_name, context_key, display_name in reports_config:
            try:
                # Render template
                html_content = self._render_template(template_name, contexts[context_key])
                
                # Write to file
                output_path = os.path.join(output_dir, template_name)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                output_files[template_name] = output_path
                logger.info(f"✅ Generated: {display_name} -> {output_path}")
                
            except Exception as e:
                logger.error(f"❌ Failed to generate {display_name}: {str(e)}")
                raise
        
        logger.info(f"✅ All {len(output_files)} reports generated successfully")
        return output_files


# Legacy function for backward compatibility
def generate_report(data: Dict[str, Any], output_path: str) -> None:
    """
    Generate a static HTML report from financial data (LEGACY - single page).
    
    This function is maintained for backward compatibility.
    For new code, use HTMLReporter.generate_reports() instead.
    
    Args:
        data: Dictionary containing financial data to inject into the template
        output_path: File path where the generated HTML report should be saved
    """
    logger.warning("Using legacy generate_report() function. Consider migrating to HTMLReporter.generate_reports()")
    
    # Get the directory where this script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(current_dir, 'templates')
    
    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader(templates_dir))
    env.filters['abs'] = abs  # Add abs filter for templates
    
    # Load the template
    template = env.get_template('report_template.html')
    
    # Render the template with data
    rendered_html = template.render(**data)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Write the rendered HTML to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(rendered_html)
    
    print(f"HTML report generated successfully at: {output_path}")