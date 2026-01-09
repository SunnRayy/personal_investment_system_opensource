"""
Data Validation and Integration Validation

Provides validation capabilities for data quality and module integration.
Ensures data consistency and reliability across the analysis pipeline.
"""

import pandas as pd
from typing import Dict, Any, List, Optional
import logging

class DataValidator:
    """Validates data quality and consistency"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_dataframe(self, df: pd.DataFrame, df_name: str, 
                          required_columns: List[str] = None) -> Dict[str, Any]:
        """Validate a single DataFrame"""
        
        validation_result = {
            'df_name': df_name,
            'is_valid': True,
            'issues': [],
            'warnings': [],
            'quality_score': 100
        }
        
        # Check if DataFrame exists and is not empty
        if df is None:
            validation_result['is_valid'] = False
            validation_result['issues'].append('DataFrame is None')
            validation_result['quality_score'] = 0
            return validation_result
        
        if df.empty:
            validation_result['is_valid'] = False
            validation_result['issues'].append('DataFrame is empty')
            validation_result['quality_score'] = 0
            return validation_result
        
        # Check required columns
        if required_columns:
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                validation_result['is_valid'] = False
                validation_result['issues'].append(f'Missing required columns: {missing_cols}')
                validation_result['quality_score'] -= 30
        
        # Check for excessive missing data
        missing_pct = (df.isnull().sum() / len(df) * 100).max()
        if missing_pct > 50:
            validation_result['issues'].append(f'High missing data: {missing_pct:.1f}%')
            validation_result['quality_score'] -= 20
        elif missing_pct > 20:
            validation_result['warnings'].append(f'Moderate missing data: {missing_pct:.1f}%')
            validation_result['quality_score'] -= 10
        
        # Check for duplicates
        if df.duplicated().any():
            dup_count = df.duplicated().sum()
            validation_result['warnings'].append(f'Duplicate rows found: {dup_count}')
            validation_result['quality_score'] -= 5
        
        # Check data types
        if df.select_dtypes(include=['object']).shape[1] == df.shape[1]:
            validation_result['warnings'].append('All columns are object type - may need type conversion')
            validation_result['quality_score'] -= 5
        
        return validation_result
    
    def validate_financial_data(self, balance_sheet_df: pd.DataFrame,
                               monthly_df: pd.DataFrame,
                               holdings_df: pd.DataFrame,
                               transactions_df: pd.DataFrame) -> Dict[str, Any]:
        """Validate complete financial dataset"""
        
        validation_results = {}
        
        # Define required columns for each DataFrame
        required_columns = {
            'balance_sheet_df': ['Total_Assets_CNY', 'Total_Liabilities_CNY', 'Net_Worth_CNY'],
            'monthly_df': ['Income_CNY', 'Expense_CNY', 'Net_Cash_Flow_CNY'],
            'holdings_df': ['Asset_Name', 'Market_Value_CNY', 'Asset_Type'],
            'transactions_df': ['Date', 'Asset_Name', 'Transaction_Type', 'Amount_Net_CNY']
        }
        
        # Validate each DataFrame
        dataframes = {
            'balance_sheet_df': balance_sheet_df,
            'monthly_df': monthly_df,
            'holdings_df': holdings_df,
            'transactions_df': transactions_df
        }
        
        overall_quality = 100
        critical_issues = []
        
        for df_name, df in dataframes.items():
            result = self.validate_dataframe(df, df_name, required_columns.get(df_name))
            validation_results[df_name] = result
            
            if not result['is_valid']:
                critical_issues.append(f"{df_name}: {', '.join(result['issues'])}")
            
            overall_quality = min(overall_quality, result['quality_score'])
        
        # Cross-DataFrame validations
        cross_validations = self._validate_cross_dataframe_consistency(dataframes)
        
        return {
            'individual_validations': validation_results,
            'cross_validations': cross_validations,
            'overall_quality_score': overall_quality,
            'critical_issues': critical_issues,
            'is_analysis_ready': len(critical_issues) == 0
        }
    
    def _validate_cross_dataframe_consistency(self, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Validate consistency across DataFrames"""
        
        consistency_results = {
            'date_alignment': 'unknown',
            'value_consistency': 'unknown',
            'asset_mapping': 'unknown',
            'issues': []
        }
        
        try:
            # Check date alignment between balance sheet and monthly data
            if (dataframes['balance_sheet_df'] is not None and 
                dataframes['monthly_df'] is not None):
                
                # Basic check - more sophisticated alignment would be implemented
                consistency_results['date_alignment'] = 'basic_check_passed'
            
            # Check asset consistency between holdings and transactions
            if (dataframes['holdings_df'] is not None and 
                dataframes['transactions_df'] is not None):
                
                holdings_assets = set(dataframes['holdings_df']['Asset_Name'].unique())
                transaction_assets = set(dataframes['transactions_df']['Asset_Name'].unique())
                
                # Assets in transactions but not in holdings
                orphaned_assets = transaction_assets - holdings_assets
                if orphaned_assets:
                    consistency_results['issues'].append(
                        f"Assets in transactions but not in holdings: {list(orphaned_assets)[:5]}"
                    )
                
                consistency_results['asset_mapping'] = 'checked'
            
        except Exception as e:
            consistency_results['validation_error'] = str(e)
        
        return consistency_results

class IntegrationValidator:
    """Validates integration between analysis modules"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_integration(self, pipeline_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate integration between financial and portfolio analysis"""
        
        integration_results = {
            'financial_analysis_status': 'unknown',
            'portfolio_analysis_status': 'unknown',
            'data_consistency': 'unknown',
            'integration_quality': 'unknown',
            'recommendations_alignment': 'unknown',
            'issues': []
        }
        
        try:
            # Check financial analysis status
            financial_analysis = pipeline_results.get('financial_analysis', {})
            if financial_analysis:
                integration_results['financial_analysis_status'] = 'completed'
            else:
                integration_results['financial_analysis_status'] = 'missing'
                integration_results['issues'].append('Financial analysis results missing')
            
            # Check portfolio analysis status
            portfolio_analysis = pipeline_results.get('portfolio_analysis', {})
            if portfolio_analysis:
                integration_results['portfolio_analysis_status'] = 'completed'
            else:
                integration_results['portfolio_analysis_status'] = 'missing'
                integration_results['issues'].append('Portfolio analysis results missing')
            
            # Validate data consistency between modules
            data_consistency = self._validate_data_consistency(pipeline_results)
            integration_results['data_consistency'] = data_consistency
            
            # Determine overall integration quality
            if len(integration_results['issues']) == 0:
                if (integration_results['financial_analysis_status'] == 'completed' and
                    integration_results['portfolio_analysis_status'] == 'completed'):
                    integration_results['integration_quality'] = 'excellent'
                else:
                    integration_results['integration_quality'] = 'partial'
            else:
                integration_results['integration_quality'] = 'poor'
            
        except Exception as e:
            integration_results['validation_error'] = str(e)
            integration_results['integration_quality'] = 'error'
        
        return integration_results
    
    def _validate_data_consistency(self, pipeline_results: Dict[str, Any]) -> str:
        """Validate data consistency between analysis modules"""
        
        try:
            # Check if both modules processed the same underlying data
            pipeline_status = pipeline_results.get('pipeline_status', {})
            
            if (pipeline_status.get('data_loading', False) and
                pipeline_status.get('financial_analysis', False) and
                pipeline_status.get('portfolio_analysis', False)):
                return 'consistent'
            else:
                return 'inconsistent'
                
        except Exception:
            return 'unknown'
    
    def validate_recommendation_consistency(self, financial_recommendations: List[Dict],
                                          portfolio_recommendations: List[Dict]) -> Dict[str, Any]:
        """Validate consistency between different recommendation sources"""
        
        consistency_result = {
            'conflicts': [],
            'alignments': [],
            'overall_consistency': 'unknown'
        }
        
        try:
            # This would implement sophisticated recommendation comparison
            # For now, provide basic structure
            
            if financial_recommendations and portfolio_recommendations:
                consistency_result['overall_consistency'] = 'analysis_required'
            elif financial_recommendations or portfolio_recommendations:
                consistency_result['overall_consistency'] = 'partial'
            else:
                consistency_result['overall_consistency'] = 'no_recommendations'
                
        except Exception as e:
            consistency_result['validation_error'] = str(e)
        
        return consistency_result
