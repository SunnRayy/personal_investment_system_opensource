import logging
import os
from datetime import datetime
from typing import Dict, Any

from src.data_manager.manager import DataManager
from src.report_builders.attribution_builder import AttributionBuilder
from src.report_builders.goal_tracking_builder import GoalTrackingBuilder
from src.html_reporter.reporter import HTMLReporter

class WealthInsightsBuilder:
    """
    Orchestrator for the Wealth Insights Report.
    Coordinates data fetching from specialized builders and handles report generation.
    """
    
    def __init__(self, config_path: str = 'config/settings.yaml'):
        self.logger = logging.getLogger(__name__)
        self.data_manager = DataManager(config_path)
        self.attribution_builder = AttributionBuilder(self.data_manager)
        self.goal_builder = GoalTrackingBuilder(self.data_manager)
        self.report_generator = HTMLReporter()
        
    def generate_report(self, output_dir: str = 'output') -> str:
        """
        Generate the Wealth Insights HTML report.
        
        Args:
            output_dir: Directory to save the report
            
        Returns:
            Path to the generated report file
        """
        self.logger.info("Starting Wealth Insights Report generation...")
        
        # 1. Build Data Context
        context = self._build_report_context()
        
        # 2. Render Template
        # We'll use a specific template for this report
        template_name = 'wealth_insights.html'
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'wealth_insights_{timestamp}.html'
        output_path = os.path.join(output_dir, filename)
        
        # Use the report generator's rendering logic
        # Note: We might need to extend ReportGenerator or call jinja env directly
        # if ReportGenerator doesn't support custom templates easily.
        # Assuming ReportGenerator has a render_template method or similar.
        
        try:
            # Render using the generator's environment
            html_content = self.report_generator.env.get_template(template_name).render(**context)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            self.logger.info(f"Report generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to render report: {str(e)}")
            raise

    def _build_report_context(self) -> Dict[str, Any]:
        """
        Gather all data required for the report.
        """
        # 1. Attribution Data
        attribution_data = self.attribution_builder.build_attribution_data(period_months=12)
        
        # 2. Goal Tracking Data
        goal_data = self.goal_builder.build_goal_data()
        
        # 3. Common Context (Dates, User Info, etc.)
        common_context = {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'report_title': 'Wealth Insights & Strategic Analysis',
            'period': 'Last 12 Months'
        }
        
        return {
            **common_context,
            'attribution': attribution_data,
            'goals': goal_data
        }
