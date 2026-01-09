# src/financial_analysis/recommendations.py
import logging
import os
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt # To close figures
import numpy as np
from collections import defaultdict # Import defaultdict for advanced debugging
import re # Import re for regex placeholder finding

# Import visualization functions (assuming they are in the same package)
from . import visualizations
from . import utils # For currency formatting, if needed elsewhere

logger = logging.getLogger(__name__)

class FinancialRecommender:
    def __init__(self, analysis_results: dict, config_dir: str = 'config'):
        """
        Initializes the FinancialRecommender.

        Args:
            analysis_results (dict): The consolidated results from FinancialAnalyzer.run_analysis().
            config_dir (str): Path to the configuration directory (e.g., for templates).
        """
        self.results = analysis_results if analysis_results else {}
        self.config_dir = os.path.abspath(config_dir)
        self.report_data = {
            "report_title": "财务分析与建议报告",
            "generated_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sections": [] # List of section dicts
        }
        # figures_paths will store relative paths for HTML linking, e.g., "images/plot_name.png"
        self.figures_paths = {} 

    def _generate_recommendations_for_section(self, section_name: str, section_results: dict) -> list:
        """
        Generates a list of text recommendations for a given analysis section.
        """
        recommendations = []
        if not section_results or section_results.get("status") == "error" or section_results.get("status") == "skipped":
            status_reason = section_results.get("reason", "未知原因") if section_results else "无分析结果"
            recommendations.append(f"{section_name} 分析数据不足、跳过或存在错误 ({status_reason})，无法生成具体建议。")
            return recommendations

        # --- Balance Sheet Specific Recommendations ---
        if section_name == "资产负债表分析":
            trends = section_results.get('trends', {})
            if trends.get('net_worth_annualized_growth_pct') is not None:
                growth_pct = trends['net_worth_annualized_growth_pct']
                if pd.notna(growth_pct):
                    if growth_pct < 5: # Example threshold
                        recommendations.append(f"提示：净资产年化增长率为 {growth_pct:.2f}%，相对较低。建议审视资产增值策略和负债管理。")
                    elif growth_pct > 15:
                        recommendations.append(f"表现良好：净资产年化增长率为 {growth_pct:.2f}%，保持了较好的增长势头。")

            ratios_data = section_results.get('ratios', {}).get('ratios_df')
            if ratios_data is not None and not ratios_data.empty:
                latest_ratios = ratios_data.iloc[-1]
                debt_to_asset = latest_ratios.get('Debt_to_Asset_Ratio')
                if pd.notna(debt_to_asset):
                    if debt_to_asset > 0.6:
                        recommendations.append(f"注意：最新资产负债率为 {debt_to_asset:.2%}，杠杆水平较高，请关注偿债风险，考虑适当降低负债。")
                    elif debt_to_asset < 0.3:
                        recommendations.append(f"最新资产负债率为 {debt_to_asset:.2%}，杠杆水平较低，财务结构稳健。")
                
                liquidity_ratio = latest_ratios.get('Liquidity_Ratio') # Current Assets / Current Liabilities
                if pd.notna(liquidity_ratio):
                    if liquidity_ratio < 1:
                        recommendations.append(f"警告：流动比率 ({liquidity_ratio:.2f}) 低于1，短期偿债能力可能存在压力，建议增加流动资产或减少短期负债。")
                    elif liquidity_ratio > 2:
                         recommendations.append(f"流动比率 ({liquidity_ratio:.2f}) 较高，短期偿债能力强，但过高也可能意味着流动资产利用效率有提升空间。")

            allocation = section_results.get('allocation', {})
            asset_alloc = allocation.get('asset_allocation', {})
            if asset_alloc:
                # Example: Check for high concentration in a single asset class (excluding '房产')
                for asset_class, details in asset_alloc.items():
                    if asset_class != '房产' and details.get('percentage', 0) > 50: # 50% threshold
                        recommendations.append(f"注意：资产配置中 '{asset_class}' 占比 ({details['percentage']:.1f}%) 较高，可能存在集中风险，建议考虑分散投资。")

        # --- Cash Flow Specific Recommendations ---
        elif section_name == "现金流分析":
            overview = section_results.get('overview', {})
            avg_net_cash_flow = overview.get('average_monthly_net_cash_flow')
            if avg_net_cash_flow is not None and pd.notna(avg_net_cash_flow):
                if avg_net_cash_flow < 0:
                    recommendations.append(f"警告：月均净现金流为负 ({utils.format_currency(avg_net_cash_flow)})，支出长期超出收入，财务状况不可持续，请立即审视并大幅削减非必要支出，或积极拓展收入来源。")
                elif avg_net_cash_flow < 2000: # Example threshold
                    recommendations.append(f"提示：月均净现金流 ({utils.format_currency(avg_net_cash_flow)}) 较低，储蓄能力有限，建议努力提升月度结余，增强财务缓冲。")

            income_analysis = section_results.get('income_analysis', {})
            avg_passive_ratio = income_analysis.get('average_passive_income_ratio')
            if avg_passive_ratio is not None and pd.notna(avg_passive_ratio):
                if avg_passive_ratio < 0.1: # 10% threshold
                    recommendations.append(f"提示：被动收入占比 ({avg_passive_ratio:.2%}) 较低，财务自由度不高。建议积极探索和构建多元化的被动收入来源。")
            
            expense_analysis = section_results.get('expense_analysis', {})
            avg_nonessential_ratio = expense_analysis.get('average_nonessential_ratio')
            if avg_nonessential_ratio is not None and pd.notna(avg_nonessential_ratio):
                if avg_nonessential_ratio > 0.5: # 50% threshold
                    recommendations.append(f"注意：非必要支出占比 ({avg_nonessential_ratio:.2%}) 较高，审视消费习惯，适当控制非必要开支，有助于提高储蓄率。")

        # --- Investment Specific Recommendations ---
        elif section_name == "投资分析":
            asset_perf = section_results.get('asset_performance', {})
            portfolio_xirr = asset_perf.get('portfolio_xirr')
            if portfolio_xirr is not None and pd.notna(portfolio_xirr):
                risk_free_rate = asset_perf.get('risk_free_rate', 0.03) * 100 # Convert to %
                if portfolio_xirr < risk_free_rate:
                    recommendations.append(f"警告：整体投资年化回报率 (XIRR) 为 {portfolio_xirr:.2f}%，低于无风险利率 ({risk_free_rate:.2f}%)，投资组合表现不佳，未能有效增值，急需全面评估投资策略和资产配置。")
                elif portfolio_xirr < 8: # Example target
                    recommendations.append(f"提示：整体投资年化回报率 (XIRR) 为 {portfolio_xirr:.2f}%，表现一般。建议优化资产配置，寻找更高潜在回报的投资标的，同时控制风险。")
            
            rebalance = section_results.get('rebalance_analysis', {})
            if rebalance.get('needs_rebalancing'):
                actions = ", ".join(rebalance.get('rebalance_actions', []))
                recommendations.append(f"建议进行投资组合再平衡，以调整至目标配置。操作建议：{actions}。")
            
            metrics = section_results.get('portfolio_metrics', {})
            if metrics.get('status') == 'success':
                sharpe = metrics.get('sharpe_ratio')
                if pd.notna(sharpe) and sharpe < 0.5: # Example threshold
                     recommendations.append(f"提示：投资组合夏普比率为 {sharpe:.2f}，风险调整后收益表现一般，可考虑优化以提高单位风险的回报。")
                max_drawdown = metrics.get('max_drawdown_pct')
                if pd.notna(max_drawdown) and max_drawdown > 20: # 20% threshold
                     recommendations.append(f"注意：投资组合最大回撤为 {max_drawdown:.2f}%，波动较大，请评估自身风险承受能力，考虑是否需要调整风险暴露。")

        # --- Enhanced Historical Analysis Recommendations ---
        elif section_name == "历史趋势分析":
            portfolio_evolution = section_results.get('portfolio_evolution', {})
            if portfolio_evolution:
                trend_analysis = portfolio_evolution.get('trend_analysis', {})
                avg_monthly_growth = trend_analysis.get('avg_monthly_growth_pct')
                if avg_monthly_growth is not None and pd.notna(avg_monthly_growth):
                    annualized_growth = (1 + avg_monthly_growth/100) ** 12 - 1
                    if annualized_growth < 0.05:  # 5% threshold
                        recommendations.append(f"历史分析：过去投资组合月均增长率为 {avg_monthly_growth:.2f}%（年化 {annualized_growth:.2%}），增长较为缓慢。建议考虑更积极的投资策略或增加资产配置效率。")
                    elif annualized_growth > 0.15:  # 15% threshold
                        recommendations.append(f"历史表现优秀：投资组合月均增长率为 {avg_monthly_growth:.2f}%（年化 {annualized_growth:.2%}），保持了稳健的增长势头。")
                
                volatility = trend_analysis.get('volatility_pct')
                if volatility is not None and pd.notna(volatility):
                    if volatility > 20:  # 20% monthly volatility threshold
                        recommendations.append(f"风险提醒：投资组合历史波动率为 {volatility:.2f}%，波动较大。建议考虑分散投资或增加稳定性资产以降低整体风险。")
                    elif volatility < 5:  # Very low volatility
                        recommendations.append(f"风险偏低：投资组合历史波动率为 {volatility:.2f}%，风险较低但可能限制了收益潜力。如风险承受能力允许，可考虑适当增加收益性资产。")

        # --- Cost Basis & Tax Optimization Recommendations ---
        elif section_name == "成本基础分析":
            cost_basis_analysis = section_results.get('cost_basis_analysis', {})
            unrealized_gains = cost_basis_analysis.get('total_unrealized_gains')
            if unrealized_gains is not None and pd.notna(unrealized_gains):
                if unrealized_gains > 50000:  # Significant unrealized gains
                    recommendations.append(f"税务优化机会：当前投资组合未实现收益为 {utils.format_currency(unrealized_gains)}，建议考虑税务规划策略，如在适当时机实现部分收益进行再投资或税务优化。")
                elif unrealized_gains < -20000:  # Significant unrealized losses
                    recommendations.append(f"税务亏损收获：当前投资组合存在 {utils.format_currency(abs(unrealized_gains))} 未实现亏损，可考虑在年底前实现部分亏损以抵消其他投资收益，实现税务优化。")
            
            high_cost_assets = cost_basis_analysis.get('high_cost_basis_assets', [])
            if high_cost_assets:
                asset_names = [asset.get('asset_id', 'Unknown') for asset in high_cost_assets[:3]]
                recommendations.append(f"成本基础关注：{', '.join(asset_names)} 等资产的成本基础较高，建议密切关注其表现，考虑是否需要调整仓位或止损策略。")

        # --- Performance Attribution Recommendations ---
        elif section_name == "绩效归因分析":
            attribution = section_results.get('performance_attribution', {})
            
            sector_attribution = attribution.get('sector_attribution', {})
            if sector_attribution:
                best_sector = max(sector_attribution.items(), key=lambda x: x[1].get('contribution', 0), default=(None, {}))
                worst_sector = min(sector_attribution.items(), key=lambda x: x[1].get('contribution', 0), default=(None, {}))
                
                if best_sector[0] and best_sector[1].get('contribution', 0) > 5:  # 5% contribution threshold
                    recommendations.append(f"优势行业：{best_sector[0]} 行业对投资组合贡献最大（+{best_sector[1].get('contribution', 0):.2f}%），建议继续关注该行业的投资机会。")
                
                if worst_sector[0] and worst_sector[1].get('contribution', 0) < -3:  # -3% threshold
                    recommendations.append(f"关注行业：{worst_sector[0]} 行业对投资组合造成较大拖累（{worst_sector[1].get('contribution', 0):.2f}%），建议重新评估该行业配置或寻找更优质标的。")
            
            asset_class_attribution = attribution.get('asset_class_attribution', {})
            if asset_class_attribution:
                underweight_classes = [cls for cls, data in asset_class_attribution.items() 
                                     if data.get('allocation_diff', 0) < -5]  # 5% underweight
                if underweight_classes:
                    recommendations.append(f"资产配置机会：{', '.join(underweight_classes)} 等资产类别当前配置偏低，如市场条件合适，可考虑增加配置以优化风险收益特征。")

        # --- Multi-timeframe Analysis Recommendations ---
        elif section_name == "多时间框架分析":
            timeframe_analysis = section_results.get('timeframe_analysis', {})
            
            short_term_trend = timeframe_analysis.get('short_term_trend', {})
            long_term_trend = timeframe_analysis.get('long_term_trend', {})
            
            if short_term_trend.get('direction') == 'declining' and short_term_trend.get('strength', 0) > 0.7:
                recommendations.append(f"短期趋势警告：投资组合近期呈明显下降趋势（强度：{short_term_trend.get('strength', 0):.2f}），建议密切关注市场动态，考虑适当的风险管理措施。")
            
            if long_term_trend.get('direction') == 'growing' and short_term_trend.get('direction') == 'declining':
                recommendations.append("趋势背离：长期趋势向上但短期趋势下降，可能是市场调整期的买入机会。建议根据个人风险承受能力考虑分批建仓。")
            
            consistency_score = timeframe_analysis.get('trend_consistency_score')
            if consistency_score is not None and consistency_score < 0.3:  # Low consistency
                recommendations.append(f"趋势一致性较低（得分：{consistency_score:.2f}），投资组合在不同时间框架表现不一致，建议重新评估投资策略的有效性和一致性。")

        if not recommendations:
            recommendations.append("当前分析结果未触发特定的建议。请结合图表和详细数据综合判断。")
        return recommendations

    def _prepare_and_save_figures(self, output_images_dir: str):
        """
        Generates all plots using visualization functions, saves them as images,
        and stores their relative paths.
        """
        os.makedirs(output_images_dir, exist_ok=True)
        
        # Enhanced robust data extraction functions
        def safe_extract_balance_sheet_trends(r):
            try:
                # Direct extraction from dictionary - follow the path exactly
                if 'balance_sheet' in r:
                    bs_data = r['balance_sheet']
                    if isinstance(bs_data, dict) and 'trends' in bs_data:
                        trend_data = bs_data['trends'].get('trend_data')
                        if trend_data is not None and not (isinstance(trend_data, pd.DataFrame) and trend_data.empty):
                            return trend_data
                logger.warning("Balance sheet trend data is missing or empty")
                return None
            except Exception as e:
                logger.error(f"Error extracting balance sheet trends: {str(e)}")
                return None
                
        def safe_extract_allocation(r):
            try:
                # Get allocation data directly without intermediate .get() calls
                if 'balance_sheet' in r and isinstance(r['balance_sheet'], dict):
                    if 'allocation' in r['balance_sheet']:
                        return r['balance_sheet']['allocation']
                logger.warning("Allocation data is missing or empty")
                return {}
            except Exception as e:
                logger.error(f"Error extracting allocation data: {str(e)}")
                return {}
                
        def safe_extract_category_growth(r):
            try:
                # For category_growth, get it directly from balance_sheet
                if 'balance_sheet' in r and isinstance(r['balance_sheet'], dict):
                    if 'category_growth' in r['balance_sheet']:
                        return r['balance_sheet']['category_growth']
                logger.warning("Category growth data is missing or empty")
                return None
            except Exception as e:
                logger.error(f"Error extracting category growth data: {str(e)}")
                return None
                
        def safe_extract_ratios(r):
            try:
                # Extract ratios directly from balance_sheet
                if 'balance_sheet' in r and isinstance(r['balance_sheet'], dict):
                    if 'ratios' in r['balance_sheet']:
                        return r['balance_sheet']['ratios']
                logger.warning("Ratios data is missing or empty")
                return None
            except Exception as e:
                logger.error(f"Error extracting ratios data: {str(e)}")
                return None
                
        def safe_extract_yoy_comparison(r):
            try:
                # Extract YoY comparison data
                if 'balance_sheet' in r and isinstance(r['balance_sheet'], dict):
                    if 'yoy_comparison' in r['balance_sheet']:
                        return r['balance_sheet']['yoy_comparison']
                logger.warning("YoY comparison data is missing or empty")
                return None
            except Exception as e:
                logger.error(f"Error extracting YoY comparison data: {str(e)}")
                return None
                
        def safe_extract_income_trends(r):
            try:
                # Extract income trends directly
                if 'cash_flow' in r and isinstance(r['cash_flow'], dict):
                    if 'income_trends' in r['cash_flow'] and 'trend_data' in r['cash_flow']['income_trends']:
                        return r['cash_flow']['income_trends']['trend_data']
                logger.warning("Income trends data is missing or empty")
                return None
            except Exception as e:
                logger.error(f"Error extracting income trends data: {str(e)}")
                return None
                
        def safe_extract_income_sources(r):
            try:
                # Extract income sources directly
                if 'cash_flow' in r and isinstance(r['cash_flow'], dict):
                    if 'income_sources' in r['cash_flow']:
                        return r['cash_flow']['income_sources']
                logger.warning("Income sources data is missing or empty")
                return {}
            except Exception as e:
                logger.error(f"Error extracting income sources data: {str(e)}")
                return {}
                
        def safe_extract_monthly_df(r):
            try:
                # Extract monthly data for plots
                if 'cash_flow' in r and isinstance(r['cash_flow'], dict):
                    if 'raw_monthly_df_for_plot' in r['cash_flow']:
                        return r['cash_flow']['raw_monthly_df_for_plot']
                logger.warning("Monthly data for plotting is missing or empty")
                return None
            except Exception as e:
                logger.error(f"Error extracting monthly data: {str(e)}")
                return None
                
        def safe_extract_expense_trends(r):
            try:
                # Extract expense trends directly
                if 'cash_flow' in r and isinstance(r['cash_flow'], dict):
                    if 'expense_trends' in r['cash_flow'] and 'trend_data' in r['cash_flow']['expense_trends']:
                        return r['cash_flow']['expense_trends']['trend_data']
                logger.warning("Expense trends data is missing or empty")
                return None
            except Exception as e:
                logger.error(f"Error extracting expense trends data: {str(e)}")
                return None
                
        def safe_extract_expense_categories(r):
            try:
                # Extract expense categories directly
                if 'cash_flow' in r and isinstance(r['cash_flow'], dict):
                    if 'expense_categories' in r['cash_flow']:
                        return r['cash_flow']['expense_categories']
                logger.warning("Expense categories data is missing or empty")
                return {}
            except Exception as e:
                logger.error(f"Error extracting expense categories data: {str(e)}")
                return {}
                
        def safe_extract_cash_flow_yoy(r):
            try:
                # Extract cash flow YoY comparison data
                if 'cash_flow' in r and isinstance(r['cash_flow'], dict):
                    if 'yoy_comparison' in r['cash_flow']:
                        return r['cash_flow']['yoy_comparison']
                logger.warning("Cash flow YoY data is missing or empty")
                return None
            except Exception as e:
                logger.error(f"Error extracting cash flow YoY data: {str(e)}")
                return None
                
        def safe_extract_expense_income_ratio(r):
            try:
                # Extract cash flow overview and monthly data
                overview = None
                monthly_df = None
                if 'cash_flow' in r and isinstance(r['cash_flow'], dict):
                    if 'cash_flow_overview' in r['cash_flow']:
                        overview = r['cash_flow']['cash_flow_overview']
                    if 'raw_monthly_df_for_plot' in r['cash_flow']:
                        monthly_df = r['cash_flow']['raw_monthly_df_for_plot']
                if overview is None:
                    logger.warning("Cash flow overview data is missing")
                if monthly_df is None:
                    logger.warning("Monthly data for expense/income ratio is missing")
                return (overview or {}, monthly_df)
            except Exception as e:
                logger.error(f"Error extracting expense/income ratio data: {str(e)}")
                return ({}, None)
                
        def safe_extract_investment_allocation(r):
            try:
                # Extract investment allocation data
                if 'investment' in r and isinstance(r['investment'], dict):
                    if 'asset_performance' in r['investment']:
                        perf = r['investment']['asset_performance']
                        asset_class_allocation = perf.get('asset_class_allocation', {})
                        total_value = perf.get('total_portfolio_value', 0)
                        latest_date = None
                        if 'latest_date' in perf:
                            try:
                                latest_date = pd.to_datetime(perf['latest_date'])
                            except:
                                latest_date = pd.Timestamp('now')
                        else:
                            latest_date = pd.Timestamp('now')
                        return (asset_class_allocation, total_value, latest_date)
                logger.warning("Investment allocation data is missing or empty")
                return ({}, 0, pd.Timestamp('now'))
            except Exception as e:
                logger.error(f"Error extracting investment allocation data: {str(e)}")
                return ({}, 0, pd.Timestamp('now'))
                
        def safe_extract_investment_growth(r):
            try:
                # Extract investment growth data
                if 'investment' in r and isinstance(r['investment'], dict):
                    if 'asset_performance' in r['investment']:
                        return r['investment']['asset_performance'].get('historical_allocation', {})
                logger.warning("Investment growth data is missing or empty") 
                return {}
            except Exception as e:
                logger.error(f"Error extracting investment growth data: {str(e)}")
                return {}
                
        def safe_extract_asset_performances(r):
            try:
                # Extract asset performances data
                if 'investment' in r and isinstance(r['investment'], dict):
                    if 'asset_performance' in r['investment']:
                        return r['investment']['asset_performance'].get('asset_performances', {})
                logger.warning("Asset performances data is missing or empty")
                return {}
            except Exception as e:
                logger.error(f"Error extracting asset performances data: {str(e)}")
                return {}
                
        def safe_extract_investment_cashflow(r):
            try:
                # Extract investment cashflow data
                if 'investment' in r and isinstance(r['investment'], dict):
                    if 'cash_flow_analysis' in r['investment']:
                        return r['investment']['cash_flow_analysis'].get('monthly_investment_cashflow_df')
                # Fallback to monthly_df if available
                if 'cash_flow' in r and isinstance(r['cash_flow'], dict):
                    return r['cash_flow'].get('raw_monthly_df_for_plot')
                logger.warning("Investment cashflow data is missing or empty")
                return None
            except Exception as e:
                logger.error(f"Error extracting investment cashflow data: {str(e)}")
                return None
        
        # plot_name: (plot_function, data_extraction_function, title_for_plot (optional))
        plot_functions_map = {
            # Balance Sheet Plots
            'bs_trends': (visualizations.plot_balance_sheet_trends, safe_extract_balance_sheet_trends, "资产负债净值趋势"),
            'bs_allocation': (visualizations.plot_asset_liability_allocation, safe_extract_allocation, "最新资产负债配置"),
            'bs_category_growth': (visualizations.plot_asset_category_growth, safe_extract_category_growth, "资产类别增长趋势"),
            'bs_ratios': (visualizations.plot_balance_sheet_ratios, safe_extract_ratios, "财务健康指标趋势"),
            'bs_yoy_growth': (visualizations.plot_yoy_net_worth_growth, safe_extract_yoy_comparison, "年度净资产增长率"),
            
            # Cash Flow Plots
            'cf_income_trends': (visualizations.plot_income_trends, safe_extract_income_trends, "月度收入趋势"),
            'cf_income_sources': (visualizations.plot_income_sources_pie, safe_extract_income_sources, "近期收入来源"),
            'cf_active_passive_income': (visualizations.plot_active_passive_income_bar, safe_extract_income_trends), 
            'cf_income_seasonality': (visualizations.plot_income_seasonality, safe_extract_monthly_df),
            'cf_income_yoy_comparison': (visualizations.plot_income_yoy_comparison, safe_extract_monthly_df),
            'cf_annual_income_growth': (visualizations.plot_annual_income_growth_bar, safe_extract_cash_flow_yoy),

            'cf_expense_trends': (visualizations.plot_expense_trends, safe_extract_expense_trends, "月度支出趋势"),
            'cf_expense_categories': (visualizations.plot_expense_categories_pie, safe_extract_expense_categories, "近期支出分类"),
            'cf_essential_nonessential_expense': (visualizations.plot_essential_nonessential_bar, safe_extract_expense_trends), 
            'cf_expense_seasonality': (visualizations.plot_expense_seasonality, safe_extract_monthly_df),
            'cf_expense_yoy_comparison': (visualizations.plot_expense_yoy_comparison, safe_extract_monthly_df),
            'cf_annual_expense_growth': (visualizations.plot_annual_expense_growth_bar, safe_extract_cash_flow_yoy),
            
            'cf_income_expense_ratio': (visualizations.plot_expense_income_ratio, safe_extract_expense_income_ratio),

            # Investment Plots
            'inv_allocation_pie': (visualizations.plot_investment_allocation_pie, safe_extract_investment_allocation, "投资组合资产类别配置"),
            'inv_growth_area': (visualizations.plot_investment_growth, safe_extract_investment_growth, "投资组合历史价值与构成"),
            'inv_xirr_comparison': (visualizations.plot_investment_roi_comparison, safe_extract_asset_performances, "投资资产 XIRR 对比"),
            'inv_cashflow_bar': (visualizations.plot_investment_cashflow, safe_extract_investment_cashflow, "月度投资现金流"),
            'inv_bubble_chart': (visualizations.plot_investment_bubble, safe_extract_asset_performances, "投资规模、回报与风险概览"),
        }

        # Rest of the method remains unchanged
        for plot_name, (plot_func, data_extractor, *plot_args) in plot_functions_map.items():
            fig, ax = None, None # Initialize
            try:
                plot_data = data_extractor(self.results)
                
                # Basic validation for plot_data
                if plot_data is None:
                    logger.warning(f"Skipping plot '{plot_name}': Main data is None.")
                    continue
                if isinstance(plot_data, tuple): # For functions expecting multiple args from lambda
                    if any(p is None for p in plot_data if not isinstance(p, dict)): # Allow empty dicts for some plots
                         # Check if all elements are None, or if a non-dict element is None
                        if all(p is None for p in plot_data):
                            logger.warning(f"Skipping plot '{plot_name}': All data components are None.")
                            continue
                        # Check for critical Nones (e.g. a DataFrame that is None)
                        is_critical_none = False
                        for p_item in plot_data:
                            if not isinstance(p_item, (dict, type(None))) and p_item is None : # e.g. DataFrame is None
                                is_critical_none = True
                                break
                        if is_critical_none:
                            logger.warning(f"Skipping plot '{plot_name}': One or more critical data components are None. Data: {plot_data}")
                            continue

                elif isinstance(plot_data, pd.DataFrame) and plot_data.empty:
                    logger.warning(f"Skipping plot '{plot_name}': DataFrame is empty.")
                    continue
                elif isinstance(plot_data, dict) and not plot_data: # Empty dict
                     # Some plots might handle empty dicts gracefully, others might not.
                     # Depending on the plot function, this might be okay or might need skipping.
                     # For now, we'll let the plot function try.
                     logger.debug(f"Plot '{plot_name}': Data is an empty dictionary. Attempting to plot.")
                
                logger.info(f"Generating plot: {plot_name}")
                title_to_pass = plot_args[0] if plot_args else None # Get title if provided

                if isinstance(plot_data, tuple):
                    if title_to_pass: fig, ax = plot_func(*plot_data, title=title_to_pass)
                    else: fig, ax = plot_func(*plot_data)
                else:
                    if title_to_pass: fig, ax = plot_func(plot_data, title=title_to_pass)
                    else: fig, ax = plot_func(plot_data)

                if fig:
                    image_filename = f"{plot_name}.png"
                    image_path_abs = os.path.join(output_images_dir, image_filename)
                    fig.savefig(image_path_abs, bbox_inches='tight') # Use bbox_inches for better layout
                    plt.close(fig) 
                    self.figures_paths[plot_name] = os.path.join("images", image_filename) 
                    logger.info(f"Saved plot {plot_name} to {image_path_abs}")
                else:
                    logger.warning(f"Failed to generate figure for {plot_name}. Plot function returned None.")
            except Exception as e:
                logger.error(f"Error generating plot {plot_name}: {e}", exc_info=True)
                if fig: plt.close(fig) # Ensure figure is closed on error too


    def _get_summary_data(self, section_name: str, section_results: dict) -> dict:
        summary = {}
        if not section_results or section_results.get("status") != "success":
            return {"status_info": section_results.get("reason", "数据不可用或分析失败")}

        if section_name == "资产负债表分析":
            trends = section_results.get('trends', {})
            summary["最新净资产"] = trends.get('end_net_worth')
            summary["最新总资产"] = trends.get('end_assets')
            summary["最新总负债"] = trends.get('end_liabilities')
            summary["净资产年化增长率"] = trends.get('net_worth_annualized_growth_pct')
            ratios_df = section_results.get('ratios', {}).get('ratios_df')
            if ratios_df is not None and not ratios_df.empty:
                summary["最新资产负债率"] = ratios_df['Debt_to_Asset_Ratio'].iloc[-1]
                summary["最新流动比率"] = ratios_df['Liquidity_Ratio'].iloc[-1]
        
        elif section_name == "现金流分析":
            overview = section_results.get('overview', {})
            summary["月均总收入"] = overview.get('average_monthly_income')
            summary["月均总支出"] = overview.get('average_monthly_expense')
            summary["月均净现金流"] = overview.get('average_monthly_net_cash_flow')
            summary["平均储蓄率"] = overview.get('savings_rate') # Assuming this key exists
            income_analysis = section_results.get('income_analysis', {})
            summary["平均被动收入占比"] = income_analysis.get('average_passive_income_ratio')
            expense_analysis = section_results.get('expense_analysis', {})
            summary["平均非必要支出占比"] = expense_analysis.get('average_nonessential_ratio')

        elif section_name == "投资分析":
            asset_perf = section_results.get('asset_performance', {})
            summary["最新总投资市值"] = asset_perf.get('total_portfolio_value')
            summary["整体投资组合XIRR"] = asset_perf.get('portfolio_xirr')
            metrics = section_results.get('portfolio_metrics', {})
            if metrics.get('status') == 'success':
                summary["年化波动率"] = metrics.get('annualized_volatility_pct')
                summary["夏普比率"] = metrics.get('sharpe_ratio')
                summary["最大回撤"] = metrics.get('max_drawdown_pct')
        return summary

    def generate_report_content(self):
        """
        Populates self.report_data with content for each section.
        """
        sections_config = [
            {"name": "资产负债表分析", "key": "balance_sheet", 
             "plots": ['bs_trends', 'bs_allocation', 'bs_category_growth', 'bs_ratios', 'bs_yoy_growth']},
            {"name": "现金流分析", "key": "cash_flow", 
             "plots": ['cf_income_trends', 'cf_income_sources', 'cf_active_passive_income', 'cf_income_seasonality', 'cf_income_yoy_comparison', 'cf_annual_income_growth',
                       'cf_expense_trends', 'cf_expense_categories', 'cf_essential_nonessential_expense', 'cf_expense_seasonality', 'cf_expense_yoy_comparison', 'cf_annual_expense_growth',
                       'cf_income_expense_ratio']},
            {"name": "投资分析", "key": "investment", 
             "plots": ['inv_allocation_pie', 'inv_growth_area', 'inv_xirr_comparison', 'inv_cashflow_bar', 'inv_bubble_chart']},
            # Enhanced DataManager Phase 3 Sections
            {"name": "历史趋势分析", "key": "历史趋势分析", 
             "plots": ['hist_portfolio_evolution', 'hist_asset_count_evolution']},
            {"name": "成本基础分析", "key": "成本基础分析", 
             "plots": ['cost_basis_analysis']},
            {"name": "绩效归因分析", "key": "绩效归因分析", 
             "plots": ['performance_attribution']},
            {"name": "多时间框架分析", "key": "多时间框架分析", 
             "plots": ['multi_timeframe_trends']}
        ]

        for config in sections_config:
            section_results = self.results.get(config["key"], {})
            recommendations = self._generate_recommendations_for_section(config["name"], section_results)
            plots_paths = [self.figures_paths.get(p_name) for p_name in config["plots"] if self.figures_paths.get(p_name)]
            summary_data = self._get_summary_data(config["name"], section_results)

            self.report_data['sections'].append({
                "title": config["name"],
                "summary_data": summary_data,
                "recommendations": recommendations,
                "plots": plots_paths
            })
        logger.info("Report content structure prepared.")


    def _render_html(self) -> str:
        """
        Renders the HTML report using the prepared content.
        Includes enhanced debugging to find the source of unexpected placeholders.
        """
        html_parts = [
            "<html><head><meta charset='UTF-8'><title>{report_title}</title>",
            "<style>",
            "body {{ font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; margin: 0; padding:0; background-color: #f8f9fa; color: #343a40; line-height: 1.6; }}",
            ".header {{ background-color: #343a40; color: white; padding: 20px 40px; text-align: center; }}",
            ".header h1 {{ margin: 0; font-size: 2em; }}",
            ".header .meta {{ font-size: 0.9em; color: #adb5bd; }}",
            ".container {{ max-width: 1200px; margin: 20px auto; padding: 20px; background-color: #fff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}",
            "h2 {{ font-size: 1.75em; color: #007bff; border-bottom: 2px solid #007bff; padding-bottom: 10px; margin-top: 40px; margin-bottom: 20px; }}",
            "h3 {{ font-size: 1.3em; color: #17a2b8; margin-top: 25px; margin-bottom: 15px; }}",
            ".section {{ margin-bottom: 40px; padding: 20px; border: 1px solid #dee2e6; border-radius: 5px; background-color: #fff; }}",
            ".summary-data {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 5px solid #17a2b8; }}",
            ".summary-data p {{ margin: 8px 0; font-size: 0.95em; }}",
            ".summary-data strong {{ color: #495057; }}",
            ".recommendations ul {{ list-style-type: none; padding-left: 0; }}",
            ".recommendations li {{ background-color: #f8f9fa; margin-bottom: 10px; padding: 12px 15px; border-left: 4px solid; border-radius: 4px; }}",
            ".recommendations li.warning {{ border-left-color: #ffc107; background-color: #fff3cd; }}",
            ".recommendations li.good {{ border-left-color: #28a745; background-color: #d4edda; }}",
            ".recommendations li.info {{ border-left-color: #17a2b8; background-color: #d1ecf1; }}",
            ".plots {{ text-align: center; margin-top: 20px; }}",
            ".plots img {{ max-width: 90%; height: auto; border: 1px solid #ced4da; margin-bottom: 20px; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}",
            "footer {{ text-align: center; padding: 20px; font-size: 0.8em; color: #6c757d; margin-top:30px; border-top: 1px solid #dee2e6;}}",
            "</style></head><body>",
            "<div class='header'><h1>{report_title}</h1><div class='meta'>报告生成于: {generated_on}</div></div>",
            "<div class='container'>"
        ]

        for section in self.report_data['sections']:
            html_parts.append(f"<div class='section'><h2>{section['title']}</h2>")

            if section.get("summary_data"):
                html_parts.append("<div class='summary-data'><h3>核心指标概览:</h3>")
                for key, value in section["summary_data"].items():
                    if value is not None and pd.notna(value) : 
                        formatted_value = value
                        try:
                            if isinstance(value, (float, np.floating, int, np.integer)):
                                if "率" in key or "ratio" in key.lower() or "percent" in key.lower() or "占比" in key:
                                    formatted_value = f"{value:.2%}"
                                elif "XIRR" in key or "回报" in key:
                                     formatted_value = f"{value:.2f}%"
                                else: 
                                    formatted_value = f"{value:,.2f}" 
                        except Exception: 
                            pass 
                        html_parts.append(f"<p><strong>{key.replace('_', ' ').title()}:</strong> {formatted_value}</p>")
                html_parts.append("</div>")

            if section['recommendations']:
                html_parts.append("<div class='recommendations'><h3>分析与建议:</h3><ul>")
                for rec in section['recommendations']:
                    rec_class = "info" 
                    if "警告" in rec or "风险" in rec or "较低" in rec and "杠杆水平较低" not in rec : rec_class = "warning"
                    elif "良好" in rec or "健康" in rec or "较高" in rec and "杠杆水平较高" not in rec and "支出占比" not in rec: rec_class = "good"
                    html_parts.append(f"<li class='{rec_class}'>{rec}</li>")
                html_parts.append("</ul></div>")
            
            if section['plots']:
                html_parts.append("<div class='plots'><h3>相关图表:</h3>")
                for plot_path in section['plots']:
                    alt_text = section['title'] + " - " + os.path.basename(plot_path).replace('.png','').replace('_',' ').title()
                    html_parts.append(f"<img src='{plot_path}' alt='{alt_text}'><br>")
                html_parts.append("</div>")
            html_parts.append("</div>")

        html_parts.append("<footer>个人投资管理优化系统 - 财务分析报告</footer>")
        html_parts.append("</div></body></html>")
        
        temp_joined_html = "".join(html_parts)
        
        # --- 更进一步的调试：检查所有未预期的占位符 ---
        all_placeholders_in_html = set(re.findall(r"(\{[^{}]*?\})", temp_joined_html))
        known_placeholders = {"{report_title}", "{generated_on}"}
        unexpected_placeholders = all_placeholders_in_html - known_placeholders

        if unexpected_placeholders:
            logger.error(f"DEBUG: UNEXPECTED placeholders found in pre-formatted HTML: {unexpected_placeholders}")
            for placeholder in unexpected_placeholders:
                try:
                    index = temp_joined_html.find(placeholder)
                    context_start = max(0, index - 100)
                    context_end = min(len(temp_joined_html), index + len(placeholder) + 100)
                    logger.error(f"DEBUG CONTEXT for '{placeholder}': ...{temp_joined_html[context_start:context_end]}...")
                except Exception as e_context:
                    logger.error(f"DEBUG: Could not get context for placeholder '{placeholder}': {e_context}")
            
            # 保存包含未预期占位符的HTML文件
            try:
                project_root_for_debug = os.path.abspath(os.path.join(self.config_dir, os.pardir))
                debug_file_path = os.path.join(project_root_for_debug, "debug_unexpected_placeholders.html")
                with open(debug_file_path, "w", encoding="utf-8") as f_debug:
                    f_debug.write(temp_joined_html)
                logger.error(f"DEBUG: HTML with unexpected placeholders saved to: {debug_file_path}")
            except Exception as e_file:
                logger.error(f"DEBUG: Failed to save HTML with unexpected placeholders: {e_file}")
        else:
            logger.info("DEBUG: No unexpected placeholders found by regex. All found placeholders are known or intentionally escaped.")
        # --- 调试结束 ---

        # 使用自定义字典进行 .format_map() 调用以捕获确切的缺失键
        class DebugFormatDict(dict):
            def __missing__(self, key):
                # 这个方法会在 .format_map 尝试访问一个不存在于字典中的键时被调用
                logger.error(f"DEBUG: format_map is requesting an UNKNOWN key: '{key}' (type: {type(key)}). This key was not provided.")
                # 为了避免因这个缺失键导致format_map失败，我们可以返回一个占位符字符串
                # 或者，更直接地，重新引发KeyError，因为我们的目标是找到原始错误的原因
                raise KeyError(key)

        format_values = DebugFormatDict({
            'report_title': self.report_data['report_title'],
            'generated_on': self.report_data['generated_on']
        })

        final_html = ""
        try:
            final_html = temp_joined_html.format_map(format_values)
        except KeyError as e:
            missing_key = e.args[0]
            logger.error(f"DEBUG: KeyError caught during format_map. Exact missing key: '{missing_key}' (type: {type(missing_key)})")
            
            # 检查这个从错误中得到的 missing_key 是否真的在 temp_joined_html 中形成了占位符
            placeholder_from_error = f"{{{missing_key}}}" # 构建占位符，例如 "{ the_key}"
            
            if placeholder_from_error in temp_joined_html:
                logger.error(f"DEBUG: CONFIRMED - Placeholder '{placeholder_from_error}' (derived from error key) IS in temp_joined_html.")
                try:
                    index = temp_joined_html.find(placeholder_from_error)
                    context_start = max(0, index - 100)
                    context_end = min(len(temp_joined_html), index + len(placeholder_from_error) + 100)
                    logger.error(f"DEBUG CONTEXT for '{placeholder_from_error}': ...{temp_joined_html[context_start:context_end]}...")
                except Exception as e_context:
                    logger.error(f"DEBUG: Could not get context for placeholder '{placeholder_from_error}': {e_context}")
            else:
                logger.error(f"DEBUG: CONTRADICTION - Placeholder '{placeholder_from_error}' (derived from error key) IS NOT in temp_joined_html. This is highly unusual.")
                logger.error(f"DEBUG: This might mean the key '{missing_key}' is being interpreted differently by .format_map, or the string contains complex/nested formatting not handled by simple string search.")
            
            raise # 重新引发原始的KeyError，以便Jupyter Notebook能看到它
        
        return final_html

    def generate_html_report(self, output_dir: str = 'output', filename_prefix: str = 'financial_report'):
        """
        Generates an HTML report with analysis, visualizations, and recommendations.
        """
        logger.info(f"Generating HTML report in {output_dir}...")
        
        os.makedirs(output_dir, exist_ok=True)
        output_images_dir = os.path.join(output_dir, "images")
        os.makedirs(output_images_dir, exist_ok=True)

        self._prepare_and_save_figures(output_images_dir=output_images_dir)
        self.generate_report_content()
        html_content = self._render_html()

        report_filename = f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        report_path_abs = os.path.join(output_dir, report_filename)
        try:
            with open(report_path_abs, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"HTML report saved to {report_path_abs}")
            return report_path_abs
        except IOError as e:
            logger.error(f"Failed to write HTML report to {report_path_abs}: {e}")
            return None

def run_recommendation_generation(analysis_results: dict, config_dir: str = 'config', output_dir: str = 'output', filename_prefix: str = 'financial_report'):
    """
    Main function to run the recommendation generation and report creation process.
    """
    if not analysis_results:
        logger.error("Analysis results are empty. Cannot generate recommendations.")
        return None
        
    recommender = FinancialRecommender(analysis_results=analysis_results, config_dir=config_dir)
    report_path = recommender.generate_html_report(output_dir=output_dir, filename_prefix=filename_prefix)
    
    if report_path:
        logger.info(f"Successfully generated financial report: {report_path}")
    else:
        logger.error("Failed to generate financial report.")
    return report_path

if __name__ == '__main__':
    # This is a placeholder for testing.
    # In a real scenario, FinancialAnalyzer would call run_recommendation_generation.
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("Running recommendations.py directly for testing (with dummy data)...")

    # Create dummy analysis_results structure similar to what FinancialAnalyzer would produce
    # This needs to be comprehensive to test all parts.
    # For now, just a very basic structure.
    dummy_results = {
        "balance_sheet": {
            "status": "success",
            "trends": {"trend_data": pd.DataFrame({'Date': pd.to_datetime(['2023-01-01', '2023-12-31']), 'Net_Worth_Calc_CNY': [100000, 120000]}).set_index('Date'),
                       "end_net_worth": 120000, "net_worth_annualized_growth_pct": 20.0},
            "allocation": {"asset_allocation": {"现金及存款": {"value": 50000, "percentage": 41.67}}},
            "ratios": {"ratios_df": pd.DataFrame({'Date': pd.to_datetime(['2023-12-31']), 'Debt_to_Asset_Ratio': [0.25], 'Liquidity_Ratio': [2.5]}).set_index('Date')},
            "category_growth": {"category_growth_df": pd.DataFrame(index=pd.to_datetime(['2023-01-01', '2023-12-31']))}, # Empty for now
            "yoy_comparison": {"yoy_comparison_df": pd.DataFrame(index=[2023])} # Empty for now
        },
        "cash_flow": {
            "status": "success",
            "income_analysis": {
                "trends_data": pd.DataFrame({'Date': pd.to_datetime(['2023-12-31']), 'Total_Income_Calc_CNY': [10000], 'Passive_Income_Calc': [1000]}).set_index('Date'),
                "sources_data": {"工资": {"value": 8000, "percentage": 80.0}},
                "average_passive_income_ratio": 0.1
            },
            "expense_analysis": {
                "trends_data": pd.DataFrame({'Date': pd.to_datetime(['2023-12-31']), 'Total_Expense_Calc_CNY': [5000], 'NonEssential_Expense_Calc': [2000]}).set_index('Date'),
                "categories_data": {"餐饮": {"value": 1500, "percentage": 30.0}},
                "average_nonessential_ratio": 0.4
            },
            "overview": {"average_monthly_net_cash_flow": 5000, "savings_rate": 0.5, "income_expense_ratio_data": pd.DataFrame()},
            "yoy_comparison": {"yoy_comparison_df": pd.DataFrame(index=[2023])},
            "raw_monthly_df_for_plot": pd.DataFrame(index=pd.to_datetime(['2023-01-01'])) # Dummy
        },
        "investment": {
            "status": "success",
            "asset_performance": {
                "total_portfolio_value": 50000,
                "portfolio_xirr": 7.5,
                "asset_class_allocation": {"股票": 60.0, "债券": 40.0},
                "latest_date": "2023-12-31",
                "asset_performances": {}, # Empty for this simple test
                "historical_allocation": {} # Empty
            },
            "portfolio_metrics": {"status": "success", "sharpe_ratio": 0.8, "max_drawdown_pct": 15.0},
            "rebalance_analysis": {"needs_rebalancing": False},
            "cash_flow_analysis": {"monthly_investment_cashflow_df": pd.DataFrame()} # Empty
        }
    }
    # Need to ensure utils.format_currency is available or mock it
    if not hasattr(utils, 'format_currency'):
        def dummy_format_currency(value, currency_symbol='¥', decimals=2):
            if value is None or not pd.notna(value): return ""
            return f"{currency_symbol}{value:,.{decimals}f}"
        utils.format_currency = dummy_format_currency

    report_file = run_recommendation_generation(dummy_results, output_dir='../../output_test') # Save to project root/output_test
    if report_file:
        logger.info(f"Test report generated: {report_file}")
        # Try to open it (platform dependent)
        try:
            if os.name == 'nt': # Windows
                os.startfile(report_file)
            elif os.uname().sysname == 'Darwin': # macOS
                os.system(f'open "{report_file}"')
            else: # Linux
                os.system(f'xdg-open "{report_file}"')
        except Exception as e:
            logger.warning(f"Could not automatically open the report: {e}")