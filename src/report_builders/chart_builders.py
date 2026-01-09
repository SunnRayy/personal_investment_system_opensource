"""
Chart Builders Module - Data generation for report visualizations.

This module contains functions for building chart data from the DataManager.
All functions return JSON strings suitable for Chart.js visualizations.
"""

import json
import logging
import pandas as pd
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.data_manager.manager import DataManager


def build_portfolio_growth_data(data_manager: 'DataManager') -> str:
    """
    Build portfolio growth data from historical balance sheet information.
    Shows absolute portfolio values over time.
    
    Args:
        data_manager: DataManager instance
        
    Returns:
        JSON string containing dates and portfolio values for chart
    """
    try:
        balance_sheet = data_manager.get_balance_sheet()
        
        if balance_sheet is None or balance_sheet.empty:
            # Fallback to mock data if no historical data
            return '{"dates": ["2024-01", "2024-02", "2024-03"], "values": [4500000, 4800000, 5320044]}'
        
        # Get the most recent 36 months or available data
        recent_data = balance_sheet.tail(36).copy()
        
        dates = []
        values = []
        
        for index, row in recent_data.iterrows():
            # Format date as YYYY-MM
            date_str = index.strftime('%Y-%m') if hasattr(index, 'strftime') else str(index)[:7]
            dates.append(date_str)
            
            # Get total assets value
            total_value = row.get('Total_Assets_Calc_CNY', 0)
            if pd.isna(total_value):
                total_value = 0
            values.append(float(total_value))
        
        growth_data = {
            'dates': dates,
            'values': values
        }
        
        return json.dumps(growth_data)
        
    except Exception as e:
        logger.warning(f"Could not build portfolio growth data: {e}")
        # Return fallback data
        return '{"dates": ["2024-01", "2024-02", "2024-03"], "values": [4500000, 4800000, 5320044]}'


def build_portfolio_growth_percentage_data(data_manager: 'DataManager') -> str:
    """
    Build Portfolio Growth PERCENTAGE data for chart visualization.
    
    Portfolio Growth shows cumulative return INCLUDING cash flows (deposits/withdrawals).
    This is different from True Time-Weighted Return which removes cash flow effects.
    
    Args:
        data_manager: DataManager instance
        
    Returns:
        JSON string containing dates and portfolio growth percentage values for chart
    """
    try:
        # Get portfolio values from balance sheet
        balance_sheet = data_manager.get_balance_sheet()
        if balance_sheet is None or balance_sheet.empty:
            return '{"dates": [], "growth_values": [], "message": "No historical data available"}'
        
        # Use total assets to show portfolio growth
        portfolio_series = balance_sheet['Total_Assets_Calc_CNY'].dropna()
        
        # Filter to last 36 months for chart clarity
        if len(portfolio_series) > 36:
            portfolio_series = portfolio_series.tail(36)
            logger.info(f"📊 Portfolio Growth % data filtered to last 36 months (from {len(balance_sheet)} total months)")
        
        if len(portfolio_series) < 2:
            return '{"dates": [], "growth_values": [], "message": "Insufficient data for portfolio growth calculation"}'
        
        # Calculate period-to-period returns
        returns = portfolio_series.pct_change().fillna(0.0)
        
        # Calculate cumulative returns (portfolio growth)
        cumulative_returns = (1 + returns).cumprod() - 1
        
        # Format data for chart
        dates = []
        growth_values = []
        
        for date, value in cumulative_returns.items():
            date_str = date.strftime('%Y-%m') if hasattr(date, 'strftime') else str(date)[:7]
            dates.append(date_str)
            # Convert to percentage
            growth_values.append(float(value * 100))
        
        growth_data = {
            'dates': dates,
            'growth_values': growth_values,
            'message': f'Portfolio growth calculated for {len(dates)} periods'
        }
        
        logger.info(f"✅ Portfolio Growth % data generated for {len(dates)} periods")
        return json.dumps(growth_data)
        
    except Exception as e:
        logger.warning(f"Could not generate portfolio growth % data: {e}")
        
        # Return empty data on error
        return '{"dates": [], "growth_values": [], "message": "Portfolio growth calculation error"}'


def build_cash_flow_data(data_manager: 'DataManager') -> str:
    """
    Build stacked cash flow data for historical visualization.
    
    Args:
        data_manager: DataManager instance
        
    Returns:
        JSON string containing dates, income, expenses, and investments for stacked chart
    """
    try:
        # Get monthly income/expense data
        monthly_data = data_manager.get_monthly_income_expense()
        
        if monthly_data is None or monthly_data.empty:
            # Fallback to mock data if no historical data
            return '''{"dates": ["2024-01", "2024-02", "2024-03"], 
                       "income": [80000, 85000, 90000], 
                       "expenses": [-60000, -65000, -70000], 
                       "investments": [-15000, -18000, -20000]}'''
        
        # Get the most recent 36 months or available data
        recent_data = monthly_data.tail(36).copy()
        
        dates = []
        income_values = []
        expense_values = []
        investment_values = []
        
        for index, row in recent_data.iterrows():
            # Format date as YYYY-MM
            date_str = index.strftime('%Y-%m') if hasattr(index, 'strftime') else str(index)[:7]
            dates.append(date_str)
            
            # Get income (positive values)
            income = row.get('Total_Income_Calc_CNY', 0)
            if pd.isna(income):
                income = 0
            income_values.append(float(income))
            
            # Get expenses (negative values for visualization)
            expense = row.get('Total_Expense_Calc_CNY', 0)
            if pd.isna(expense):
                expense = 0
            expense_values.append(float(-expense))  # Negative for stacked chart
            
            # Get investments (negative values for visualization)
            investment = row.get('Total_Investment_Calc_CNY', 0)
            if pd.isna(investment):
                investment = 0
            investment_values.append(float(-investment))  # Negative for stacked chart
        
        cash_flow_data = {
            'dates': dates,
            'income': income_values,
            'expenses': expense_values,
            'investments': investment_values
        }
        
        return json.dumps(cash_flow_data)
        
    except Exception as e:
        logger.warning(f"Could not build cash flow data: {e}")
        # Return fallback data
        return '''{"dates": ["2024-01", "2024-02", "2024-03"], 
                   "income": [80000, 85000, 90000], 
                   "expenses": [-60000, -65000, -70000], 
                   "investments": [-15000, -18000, -20000]}'''


def build_forecast_data(data_manager: 'DataManager') -> str:
    """
    Build 12-month forecast data using SARIMA model from CashFlowForecaster.
    Optimized to use only the last 36 months for faster processing while maintaining accuracy.
    
    Args:
        data_manager: DataManager instance for accessing historical data
        
    Returns:
        JSON string containing forecast data for Chart.js
    """
    try:
        from src.financial_analysis.cash_flow_forecaster import CashFlowForecaster
        
        logger.info("🔮 Generating 12-month cash flow forecast...")
        logger.info("⚡ Optimized for performance: using last 36 months of data")
        
        # Initialize forecaster
        forecaster = CashFlowForecaster(data_manager)
        
        # Fetch and process historical data first
        forecaster.fetch_and_process_historical_data()
        
        # Optimization: Limit to last 36 months for faster SARIMA fitting
        if forecaster.monthly_data is not None and len(forecaster.monthly_data) > 36:
            original_length = len(forecaster.monthly_data)
            forecaster.monthly_data = forecaster.monthly_data.tail(36)
            logger.info(f"📊 Data optimized: {original_length} months → {len(forecaster.monthly_data)} months")
        else:
            logger.info(f"📊 Using all available data: {len(forecaster.monthly_data)} months")
        
        # Fit SARIMA models (now faster with limited data)
        fit_results = forecaster.fit_sarima_models()
        logger.info(f"📈 SARIMA models fitted: {list(fit_results.keys())}")
        
        # Generate 12-month forecast
        forecast_df = forecaster.forecast_statsmodels(periods=12)
        
        # Extract forecast data for Chart.js
        dates = []
        income_forecast = []
        expenses_forecast = []
        investments_forecast = []
        
        for index, row in forecast_df.iterrows():
            # Format date as YYYY-MM
            date_str = index.strftime('%Y-%m') if hasattr(index, 'strftime') else str(index)[:7]
            dates.append(date_str)
            
            # Extract forecasted values
            income_forecast.append(float(row.get('Income_Forecast', 0)))
            expenses_forecast.append(float(-row.get('Expenses_Forecast', 0)))  # Negative for visualization
            investments_forecast.append(float(-row.get('Investment_Forecast', 0)))  # Negative for visualization
        
        forecast_data = {
            'dates': dates,
            'income_forecast': income_forecast,
            'expenses_forecast': expenses_forecast,
            'investments_forecast': investments_forecast
        }
        
        logger.info(f"✅ Forecast generated for {len(dates)} months")
        return json.dumps(forecast_data)
        
    except Exception as e:
        logger.warning(f"Could not generate forecast data: {e}")
        logger.info("This may be due to missing packages (pmdarima/statsmodels) or insufficient data")
        
        # Return fallback forecast data
        future_dates = pd.date_range(
            start=pd.Timestamp.now() + pd.DateOffset(months=1),
            periods=12,
            freq='ME'
        )
        
        fallback_data = {
            'dates': [date.strftime('%Y-%m') for date in future_dates],
            'income_forecast': [85000] * 12,  # Conservative income estimate
            'expenses_forecast': [-65000] * 12,  # Conservative expense estimate  
            'investments_forecast': [-18000] * 12  # Conservative investment estimate
        }
        
        return json.dumps(fallback_data)


def build_twr_data(data_manager: 'DataManager') -> str:
    """
    Build TRUE Time-Weighted Return (TWR) data for chart visualization.
    
    TWR measures investment performance INDEPENDENT of cash flows (deposits/withdrawals).
    It shows how well investments performed regardless of when money was added/removed.
    
    Formula: TWR = ∏(1 + HPR_i) - 1, where HPR is holding period return between cash flows
    
    Args:
        data_manager: DataManager instance
        
    Returns:
        JSON string containing dates and TWR values for chart
    """
    try:
        # Get portfolio values and transactions
        balance_sheet = data_manager.get_balance_sheet()
        transactions = data_manager.get_transactions()
        
        if balance_sheet is None or balance_sheet.empty:
            logger.warning("No balance sheet data for TWR calculation")
            return '{"dates": [], "twr_values": [], "message": "No historical data available"}'
        
        portfolio_series = balance_sheet['Total_Assets_Calc_CNY'].dropna()
        
        # Filter to last 36 months
        if len(portfolio_series) > 36:
            portfolio_series = portfolio_series.tail(36)
            logger.info(f"📊 TWR data filtered to last 36 months (from {len(balance_sheet)} total months)")
        
        if len(portfolio_series) < 2:
            return '{"dates": [], "twr_values": [], "message": "Insufficient data for TWR calculation"}'
        
        # Identify cash flow dates (transactions that affect portfolio value)
        cash_flow_dates = set()
        if transactions is not None and not transactions.empty:
            # Filter for transactions that represent cash flows (Buy/Sell but not dividends reinvested)
            cash_flow_transactions = transactions[
                transactions['Transaction_Type'].isin(['Buy', 'Sell', 'RSU_Vest', 'Premium_Payment'])
            ].copy()
            
            # Get dates and aggregate by month-end
            if not cash_flow_transactions.empty:
                cash_flow_dates = set(pd.to_datetime(cash_flow_transactions.index).to_period('M').to_timestamp('M'))
        
        logger.info(f"Identified {len(cash_flow_dates)} cash flow periods for TWR calculation")
        
        # Calculate sub-period returns
        dates = []
        twr_values = []
        cumulative_twr = 1.0
        
        for i in range(1, len(portfolio_series)):
            curr_date = portfolio_series.index[i]
            prev_value = portfolio_series.iloc[i-1]
            curr_value = portfolio_series.iloc[i]
            
            # Calculate holding period return
            if prev_value > 0:
                # If there was a cash flow in this period, adjust for it
                if curr_date in cash_flow_dates:
                    # Get cash flows for this period
                    period_flows = transactions[
                        (transactions.index.to_period('M') == pd.Period(curr_date, 'M')) &
                        (transactions['Transaction_Type'].isin(['Buy', 'Sell', 'RSU_Vest', 'Premium_Payment']))
                    ]['Amount_Net'].sum() if transactions is not None else 0.0
                    
                    # Adjust return for cash flows: HPR = (End_Value - Cash_Flow) / Start_Value - 1
                    # Negative Amount_Net = outflow (investment), positive = inflow (sale)
                    adjusted_end_value = curr_value + period_flows  # Add back outflows, subtract inflows
                    hpr = (adjusted_end_value / prev_value) - 1
                else:
                    # No cash flow, simple return
                    hpr = (curr_value / prev_value) - 1
                
                # Accumulate TWR
                cumulative_twr *= (1 + hpr)
            
            date_str = curr_date.strftime('%Y-%m') if hasattr(curr_date, 'strftime') else str(curr_date)[:7]
            dates.append(date_str)
            # Convert to percentage
            twr_values.append(float((cumulative_twr - 1) * 100))
        
        twr_data = {
            'dates': dates,
            'twr_values': twr_values,
            'cash_flow_adjusted': True,
            'message': f'True TWR calculated for {len(dates)} periods with {len(cash_flow_dates)} cash flow adjustments'
        }
        
        logger.info(f"✅ True TWR data generated for {len(dates)} periods")
        return json.dumps(twr_data)
        
    except Exception as e:
        logger.warning(f"Could not generate true TWR data: {e}")
        logger.warning("Falling back to portfolio growth approximation")
        
        # Fallback to portfolio growth if TWR calculation fails
        return build_portfolio_growth_data(data_manager)


def build_drawdown_data(data_manager: 'DataManager') -> str:
    """
    Build Portfolio Drawdown History data for area chart visualization.
    
    Drawdown measures the decline from a historical peak in portfolio value,
    showing periods of loss and recovery over time.
    
    Args:
        data_manager: DataManager instance
        
    Returns:
        JSON string containing dates and drawdown values for chart
    """
    try:
        from src.financial_analysis.metrics import FinancialMetrics
        
        # Get portfolio values from balance sheet
        balance_sheet = data_manager.get_balance_sheet()
        if balance_sheet is None or balance_sheet.empty:
            return '{"dates": [], "drawdown_values": [], "message": "No historical data available"}'
        
        # Use portfolio series for drawdown calculation
        portfolio_series = balance_sheet['Total_Assets_Calc_CNY'].dropna()
        
        # Filter to last 36 months to match TWR chart timeframe
        if len(portfolio_series) > 36:
            portfolio_series = portfolio_series.tail(36)
            logger.info(f"📊 Drawdown data filtered to last 36 months (from {len(balance_sheet)} total months)")
        
        if len(portfolio_series) < 2:
            return '{"dates": [], "drawdown_values": [], "message": "Insufficient data for drawdown calculation"}'
        
        # Calculate drawdown using FinancialMetrics
        metrics = FinancialMetrics()
        drawdown_analysis = metrics.calculate_max_drawdown(portfolio_series)
        
        if 'drawdown_series' not in drawdown_analysis:
            return '{"dates": [], "drawdown_values": [], "message": "Drawdown calculation failed"}'
        
        drawdown_series = drawdown_analysis['drawdown_series']
        
        # Format data for chart
        dates = []
        drawdown_values = []
        
        for date, value in drawdown_series.items():
            date_str = date.strftime('%Y-%m') if hasattr(date, 'strftime') else str(date)[:7]
            dates.append(date_str)
            # Convert to percentage (drawdown is negative, so we show it as positive decline)
            drawdown_values.append(float(abs(value) * 100))
        
        # Get max drawdown statistics for context
        max_drawdown = drawdown_analysis.get('max_drawdown', 0)
        current_drawdown = drawdown_analysis.get('current_drawdown', 0)
        
        drawdown_data = {
            'dates': dates,
            'drawdown_values': drawdown_values,
            'max_drawdown_pct': float(abs(max_drawdown) * 100),
            'current_drawdown_pct': float(abs(current_drawdown) * 100),
            'message': f'Drawdown history calculated for {len(dates)} periods'
        }
        
        logger.info(f"✅ Drawdown data generated for {len(dates)} periods")
        return json.dumps(drawdown_data)
        
    except Exception as e:
        logger.warning(f"Could not generate drawdown data: {e}")
        
        # Return empty data on error
        return '{"dates": [], "drawdown_values": [], "message": "Drawdown calculation error"}'


def build_allocation_from_holdings(holdings_df) -> tuple:
    """Build allocation data directly from holdings DataFrame."""
    
    # Initialize taxonomy manager for classification
    from src.portfolio_lib.taxonomy_manager import TaxonomyManager
    from src.report_generators.real_report import classify_asset_using_taxonomy
    
    taxonomy_manager = TaxonomyManager()
    
    # Phase 6.4 Fix: Reset index if MultiIndex (from database mode)
    if isinstance(holdings_df.index, pd.MultiIndex):
        holdings_df = holdings_df.reset_index()
    
    # Group by asset type if available
    top_level_agg = {}
    sub_class_agg = {}
    
    for _, holding in holdings_df.iterrows():
        asset_name = holding.get('Asset_Name', 'Unknown')
        # Phase 6.4 Fix: Fallback to Asset_Type if Asset_Type_Raw is missing (for HoldingsCalculator output)
        asset_type = holding.get('Asset_Type_Raw', holding.get('Asset_Type', 'Unknown'))
        market_value = holding.get('Market_Value_CNY', 0) or 0
        
        # Use proper taxonomy classification instead of hardcoded logic
        level_1, level_2 = classify_asset_using_taxonomy(asset_name, asset_type, taxonomy_manager)
        
        # Aggregate top-level
        top_level_agg[level_1] = top_level_agg.get(level_1, 0) + market_value
        sub_class_agg[level_2] = sub_class_agg.get(level_2, 0) + market_value
    
    # Convert to chart format
    top_level_allocation = {
        "labels": list(top_level_agg.keys()),
        "values": list(top_level_agg.values())
    }
    
    sub_class_allocation = {
        "labels": list(sub_class_agg.keys()),
        "values": list(sub_class_agg.values())
    }
    
    return top_level_allocation, sub_class_allocation
