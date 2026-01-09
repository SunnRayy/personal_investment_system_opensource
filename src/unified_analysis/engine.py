"""
Main Analysis Engine

The core orchestrator that provides a single entry point for comprehensive 
financial analysis and portfolio optimization.
"""

import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import os

from .pipeline import DataPipeline
from .config_manager import AnalysisConfig, ConfigManager
from .validators import DataValidator, IntegrationValidator
from ..recommendation_engine.comprehensive_engine import ComprehensiveRecommendationEngine

class FinancialAnalysisEngine:
    """
    Main engine that orchestrates complete financial analysis workflow.
    
    Provides a single entry point for:
    - Data loading and validation
    - Financial analysis
    - Portfolio optimization
    - Recommendation generation
    - Report generation
    """
    
    def __init__(self, config_path: str = "config/settings.yaml", 
                 analysis_config: Optional[AnalysisConfig] = None):
        """Initialize the analysis engine"""
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Configuration management
        self.config_manager = ConfigManager()
        self.analysis_config = analysis_config or self.config_manager.load_config()
        
        # Core components
        self.data_pipeline = DataPipeline(config_path)
        self.data_validator = DataValidator()
        self.integration_validator = IntegrationValidator()
        self.recommendation_engine = ComprehensiveRecommendationEngine()
        
        # Results storage
        self.analysis_results = {}
        self.execution_metadata = {}
        
        self.logger.info("FinancialAnalysisEngine initialized")
    
    def run_complete_analysis(self, 
                            generate_reports: bool = True,
                            custom_config: Optional[AnalysisConfig] = None) -> Dict[str, Any]:
        """
        Execute complete financial analysis workflow
        
        Args:
            generate_reports: Whether to generate output reports
            custom_config: Custom analysis configuration
            
        Returns:
            Comprehensive analysis results
        """
        
        start_time = datetime.now()
        
        try:
            # Use custom config if provided
            if custom_config:
                self.analysis_config = custom_config
            
            self.logger.info("Starting complete financial analysis workflow")
            
            # Step 1: Validate configuration
            config_issues = self.config_manager.validate_config(self.analysis_config)
            if config_issues:
                self.logger.warning(f"Configuration issues detected: {config_issues}")
            
            # Step 2: Execute data pipeline
            self.logger.info("Executing data pipeline...")
            pipeline_results = self.data_pipeline.run_complete_pipeline()
            
            if not pipeline_results.get('pipeline_status', {}).get('completed', False):
                raise Exception("Data pipeline execution failed")
            
            # Step 3: Cross-module validation
            self.logger.info("Performing cross-module validation...")
            integration_results = self.integration_validator.validate_integration(
                pipeline_results
            )
            
            # Step 4: Generate recommendations
            self.logger.info("Generating recommendations...")
            recommendations = self._generate_recommendations(pipeline_results)
            
            # Step 5: Compile comprehensive results
            self.analysis_results = {
                'execution_metadata': {
                    'start_time': start_time.isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'execution_time_seconds': (datetime.now() - start_time).total_seconds(),
                    'analysis_config': self._serialize_config(),
                    'config_issues': config_issues
                },
                'data_pipeline_results': pipeline_results,
                'integration_validation': integration_results,
                'financial_analysis': pipeline_results.get('financial_analysis', {}),
                'portfolio_analysis': pipeline_results.get('portfolio_analysis', {}),
                'recommendations': recommendations,
                'comprehensive_insights': self._generate_comprehensive_insights(pipeline_results)
            }
            
            # Step 6: Generate reports if requested
            if generate_reports:
                self.logger.info("Generating output reports...")
                self.analysis_results['report_generation'] = self._generate_reports()
            
            self.logger.info(f"Complete analysis finished successfully in {self.analysis_results['execution_metadata']['execution_time_seconds']:.2f} seconds")
            
            return self.analysis_results
            
        except Exception as e:
            self.logger.error(f"Analysis workflow failed: {e}")
            
            return {
                'execution_metadata': {
                    'start_time': start_time.isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'execution_time_seconds': (datetime.now() - start_time).total_seconds(),
                    'error': str(e),
                    'analysis_config': self._serialize_config()
                },
                'success': False,
                'error': str(e),
                'partial_results': getattr(self, 'analysis_results', {})
            }
    
    def _generate_recommendations(self, pipeline_results: Dict[str, Any]) -> Optional[Any]:
        """Generate recommendations based on analysis results"""
        try:
            # Extract data for recommendation engine
            financial_data = {
                'balance_sheet_df': self.data_pipeline.data_manager.get_balance_sheet(),
                'monthly_df': self.data_pipeline.data_manager.get_monthly_income_expense()
            }
            
            portfolio_data = {
                'holdings_df': self.data_pipeline.data_manager.get_holdings(),
                'transactions_df': self.data_pipeline.data_manager.get_transactions()
            }
            
            analysis_results = {
                'financial_analysis': pipeline_results.get('financial_analysis', {}),
                'portfolio_analysis': pipeline_results.get('portfolio_analysis', {})
            }
            
            # Generate recommendations
            recommendations = self.recommendation_engine.generate_recommendations(
                financial_data=financial_data,
                portfolio_data=portfolio_data,
                analysis_results=analysis_results
            )
            
            self.logger.info(f"Generated {len(recommendations.financial_recommendations)} financial recommendations")
            self.logger.info(f"Generated {len(recommendations.portfolio_recommendations)} portfolio recommendations")
            self.logger.info(f"Generated {len(recommendations.risk_recommendations)} risk recommendations")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Recommendation generation failed: {e}")
            return None
    
    def run_financial_analysis_only(self) -> Dict[str, Any]:
        """Run only financial analysis without portfolio optimization"""
        try:
            # Load data
            if not self.data_pipeline.load_data():
                raise Exception("Data loading failed")
            
            # Run financial analysis
            if not self.data_pipeline.run_financial_analysis():
                raise Exception("Financial analysis failed")
            
            return {
                'success': True,
                'financial_analysis': self.data_pipeline.analysis_results.get('financial_analysis', {}),
                'data_summary': self.data_pipeline._generate_data_summary()
            }
            
        except Exception as e:
            self.logger.error(f"Financial analysis failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_portfolio_analysis_only(self) -> Dict[str, Any]:
        """Run only portfolio optimization without financial analysis"""
        try:
            # Load data
            if not self.data_pipeline.load_data():
                raise Exception("Data loading failed")
            
            # Run portfolio analysis
            if not self.data_pipeline.run_portfolio_analysis():
                raise Exception("Portfolio analysis failed")
            
            return {
                'success': True,
                'portfolio_analysis': self.data_pipeline.analysis_results.get('portfolio_analysis', {}),
                'data_summary': self.data_pipeline._generate_data_summary()
            }
            
        except Exception as e:
            self.logger.error(f"Portfolio analysis failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_quick_summary(self) -> Dict[str, Any]:
        """Generate a quick summary of current portfolio status"""
        try:
            # Load data only
            if not self.data_pipeline.load_data():
                raise Exception("Data loading failed")
            
            # Generate quick summary from raw data
            summary = {
                'data_status': 'loaded',
                'data_summary': self.data_pipeline._generate_data_summary(),
                'data_quality': self.data_pipeline._validate_data_quality(),
                'quick_metrics': self._extract_quick_metrics()
            }
            
            return {'success': True, 'summary': summary}
            
        except Exception as e:
            self.logger.error(f"Quick summary failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_config(self, new_config: AnalysisConfig) -> bool:
        """Update analysis configuration"""
        try:
            # Validate new configuration
            issues = self.config_manager.validate_config(new_config)
            if issues:
                self.logger.warning(f"Configuration issues: {issues}")
            
            self.analysis_config = new_config
            self.config_manager.config = new_config
            
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration update failed: {e}")
            return False
    
    def _serialize_config(self) -> Dict[str, Any]:
        """Convert analysis config to serializable dictionary"""
        config_dict = {}
        for key, value in self.analysis_config.__dict__.items():
            if hasattr(value, 'value'):  # Enum
                config_dict[key] = value.value
            else:
                config_dict[key] = value
        return config_dict
    
    def _extract_quick_metrics(self) -> Dict[str, Any]:
        """Extract quick metrics from loaded data"""
        quick_metrics = {}
        
        try:
            raw_data = self.data_pipeline.raw_data
            
            # Portfolio value
            if 'holdings_df' in raw_data and raw_data['holdings_df'] is not None:
                holdings_df = raw_data['holdings_df']
                if 'Market_Value_CNY' in holdings_df.columns:
                    quick_metrics['total_portfolio_value'] = holdings_df['Market_Value_CNY'].sum()
                    quick_metrics['number_of_holdings'] = len(holdings_df)
            
            # Net worth
            if 'balance_sheet_df' in raw_data and raw_data['balance_sheet_df'] is not None:
                balance_df = raw_data['balance_sheet_df']
                if 'Net_Worth_CNY' in balance_df.columns:
                    quick_metrics['current_net_worth'] = balance_df['Net_Worth_CNY'].iloc[-1]
                    if len(balance_df) > 1:
                        quick_metrics['net_worth_change'] = (
                            balance_df['Net_Worth_CNY'].iloc[-1] - 
                            balance_df['Net_Worth_CNY'].iloc[-2]
                        )
            
            # Recent transactions
            if 'transactions_df' in raw_data and raw_data['transactions_df'] is not None:
                trans_df = raw_data['transactions_df']
                quick_metrics['total_transactions'] = len(trans_df)
                
                # Recent activity (last 30 days)
                if 'Date' in trans_df.columns:
                    recent_cutoff = datetime.now() - pd.Timedelta(days=30)
                    recent_trans = trans_df[trans_df['Date'] >= recent_cutoff]
                    quick_metrics['recent_transactions'] = len(recent_trans)
            
        except Exception as e:
            self.logger.warning(f"Could not extract quick metrics: {e}")
            quick_metrics['extraction_error'] = str(e)
        
        return quick_metrics
    
    def _generate_comprehensive_insights(self, pipeline_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights that integrate financial and portfolio analysis"""
        
        insights = {
            'overall_financial_health': 'unknown',
            'portfolio_optimization_priority': 'unknown',
            'key_recommendations': [],
            'risk_assessment': 'unknown'
        }
        
        try:
            # This would analyze the combined results and generate integrated insights
            # For now, provide basic integration
            
            financial_results = pipeline_results.get('financial_analysis', {})
            portfolio_results = pipeline_results.get('portfolio_analysis', {})
            
            if financial_results and portfolio_results:
                insights['integration_status'] = 'complete'
                insights['analysis_scope'] = 'comprehensive'
            elif financial_results:
                insights['integration_status'] = 'financial_only'
                insights['analysis_scope'] = 'financial'
            elif portfolio_results:
                insights['integration_status'] = 'portfolio_only'
                insights['analysis_scope'] = 'portfolio'
            else:
                insights['integration_status'] = 'none'
                insights['analysis_scope'] = 'none'
            
        except Exception as e:
            insights['generation_error'] = str(e)
        
        return insights
    
    def _generate_reports(self) -> Dict[str, Any]:
        """Generate output reports based on configuration"""
        report_results = {
            'excel_report': None,
            'web_dashboard': None,
            'generated_files': []
        }
        
        try:
            # This would integrate with the output generation modules
            # For now, return placeholder
            
            if self.analysis_config.generate_excel_report:
                report_results['excel_report'] = 'planned'
            
            if self.analysis_config.generate_web_dashboard:
                report_results['web_dashboard'] = 'planned'
                
        except Exception as e:
            report_results['generation_error'] = str(e)
        
        return report_results
