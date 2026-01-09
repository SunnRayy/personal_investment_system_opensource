"""
Performance Attribution Visualizations

This module provides visualization functions for performance attribution analysis,
including cumulative attribution charts and waterfall charts for breaking down
attribution components.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any, Optional, Union
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set style for matplotlib
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")


def plot_cumulative_attribution(data: Union[Dict[str, Any], pd.DataFrame], 
                               title: str = "Cumulative Performance Attribution",
                               use_plotly: bool = True,
                               save_path: Optional[str] = None) -> None:
    """
    Generate a line chart showing the cumulative impact of selection and allocation 
    effects on the portfolio's excess return over time.
    
    Args:
        data: Attribution data - either a dictionary with results or DataFrame
        title: Chart title
        use_plotly: If True, use Plotly for interactive charts; if False, use matplotlib
        save_path: Optional path to save the chart
    """
    logger.info("Generating cumulative attribution visualization")
    
    # Extract data from different input formats
    if isinstance(data, dict):
        # Handle MultiPeriodAttributionResult format
        if 'monthly_results' in data:
            df = _extract_monthly_results(data['monthly_results'])
        elif 'cumulative_results' in data:
            df = _extract_cumulative_results(data['cumulative_results'])
        else:
            # Handle direct dictionary format
            df = pd.DataFrame(data)
    elif isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        raise ValueError("Data must be a dictionary or DataFrame")
    
    # Ensure we have the required columns
    required_cols = ['allocation_effect', 'selection_effect']
    if not all(col in df.columns for col in required_cols):
        logger.warning(f"Missing required columns. Available: {list(df.columns)}")
        # Try to find similar columns
        for col in required_cols:
            if col not in df.columns:
                # Look for similar column names
                similar_cols = [c for c in df.columns if col.split('_')[0] in c.lower()]
                if similar_cols:
                    logger.info(f"Using {similar_cols[0]} for {col}")
                    df[col] = df[similar_cols[0]]
    
    # Calculate cumulative effects
    df['cumulative_allocation'] = df['allocation_effect'].cumsum()
    df['cumulative_selection'] = df['selection_effect'].cumsum()
    df['cumulative_total'] = df['cumulative_allocation'] + df['cumulative_selection']
    
    # Ensure we have a proper date index
    if not isinstance(df.index, pd.DatetimeIndex):
        if 'date' in df.columns:
            df.set_index('date', inplace=True)
        elif 'period' in df.columns:
            df.set_index('period', inplace=True)
        else:
            # Create a simple date range
            df.index = pd.date_range(start='2023-01-01', periods=len(df), freq='M')
    
    if use_plotly:
        _plot_cumulative_plotly(df, title, save_path)
    else:
        _plot_cumulative_matplotlib(df, title, save_path)
    
    logger.info("Cumulative attribution chart generated successfully")


def plot_waterfall_attribution(data: Union[Dict[str, Any], pd.Series],
                              period_label: str = "Latest Period",
                              title: str = "Attribution Waterfall Analysis",
                              use_plotly: bool = True,
                              save_path: Optional[str] = None) -> None:
    """
    Generate a waterfall chart that breaks down the total excess return for a single 
    period into its core attribution components.
    
    Args:
        data: Attribution data for a single period
        period_label: Label for the period being analyzed
        title: Chart title
        use_plotly: If True, use Plotly for interactive charts; if False, use matplotlib
        save_path: Optional path to save the chart
    """
    logger.info(f"Generating waterfall attribution chart for {period_label}")
    
    # Extract components from data
    if isinstance(data, dict):
        components = _extract_waterfall_components(data)
    elif isinstance(data, pd.Series):
        components = data.to_dict()
    elif isinstance(data, pd.DataFrame):
        # Take the last row if DataFrame
        components = data.iloc[-1].to_dict()
    else:
        raise ValueError("Data must be a dictionary, Series, or DataFrame")
    
    # Standardize component names
    component_mapping = {
        'allocation_effect': 'Asset Allocation',
        'selection_effect': 'Security Selection',
        'interaction_effect': 'Interaction',
        'total_attribution': 'Total Attribution',
        'excess_return': 'Total Excess Return',
        'portfolio_return': 'Portfolio Return',
        'benchmark_return': 'Benchmark Return'
    }
    
    # Build waterfall data
    waterfall_data = []
    cumulative = 0
    
    # Core attribution components
    core_components = ['allocation_effect', 'selection_effect', 'interaction_effect']
    
    for key in core_components:
        if key in components and components[key] is not None:
            value = float(components[key])
            waterfall_data.append({
                'component': component_mapping.get(key, key.replace('_', ' ').title()),
                'value': value,
                'cumulative': cumulative + value,
                'type': 'component'
            })
            cumulative += value
    
    # Add total
    total_key = 'total_attribution' if 'total_attribution' in components else 'excess_return'
    if total_key in components:
        total_value = float(components[total_key])
        waterfall_data.append({
            'component': 'Total',
            'value': total_value,
            'cumulative': total_value,
            'type': 'total'
        })
    
    if use_plotly:
        _plot_waterfall_plotly(waterfall_data, title, period_label, save_path)
    else:
        _plot_waterfall_matplotlib(waterfall_data, title, period_label, save_path)
    
    logger.info("Waterfall attribution chart generated successfully")


def _extract_monthly_results(monthly_results: List[Dict]) -> pd.DataFrame:
    """Extract monthly results into a DataFrame"""
    data = []
    for result in monthly_results:
        if hasattr(result, '__dict__'):
            # Handle object format
            row = {
                'allocation_effect': getattr(result, 'allocation_effect', 0),
                'selection_effect': getattr(result, 'selection_effect', 0),
                'interaction_effect': getattr(result, 'interaction_effect', 0),
                'total_attribution': getattr(result, 'total_attribution', 0),
                'excess_return': getattr(result, 'excess_return', 0)
            }
            if hasattr(result, 'end_date'):
                row['date'] = result.end_date
        else:
            # Handle dictionary format
            row = dict(result)
        data.append(row)
    
    df = pd.DataFrame(data)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
    
    return df


def _extract_cumulative_results(cumulative_results: Dict) -> pd.DataFrame:
    """Extract cumulative results into a DataFrame"""
    # This should be a single row, but we'll create a time series for visualization
    if isinstance(cumulative_results, dict):
        # Create a simple time series with the cumulative values
        dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='M')
        
        # For cumulative view, we'll assume equal monthly contributions
        total_allocation = cumulative_results.get('allocation_effect', 0)
        total_selection = cumulative_results.get('selection_effect', 0)
        
        monthly_allocation = total_allocation / len(dates)
        monthly_selection = total_selection / len(dates)
        
        data = {
            'allocation_effect': [monthly_allocation] * len(dates),
            'selection_effect': [monthly_selection] * len(dates)
        }
        
        df = pd.DataFrame(data, index=dates)
        return df
    
    return pd.DataFrame()


def _extract_waterfall_components(data: Dict) -> Dict:
    """Extract waterfall components from various data formats"""
    components = {}
    
    # Try different possible keys
    key_mappings = {
        'allocation_effect': ['allocation_effect', 'allocation', 'asset_allocation'],
        'selection_effect': ['selection_effect', 'selection', 'security_selection'],
        'interaction_effect': ['interaction_effect', 'interaction'],
        'total_attribution': ['total_attribution', 'total', 'total_effect'],
        'excess_return': ['excess_return', 'excess', 'active_return']
    }
    
    for standard_key, possible_keys in key_mappings.items():
        for key in possible_keys:
            if key in data:
                components[standard_key] = data[key]
                break
    
    return components


def _plot_cumulative_plotly(df: pd.DataFrame, title: str, save_path: Optional[str]) -> None:
    """Generate cumulative attribution chart using Plotly"""
    fig = go.Figure()
    
    # Add traces for each component
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['cumulative_allocation'],
        mode='lines+markers',
        name='Asset Allocation',
        line=dict(color='#1f77b4', width=3),
        hovertemplate='<b>Asset Allocation</b><br>Date: %{x}<br>Cumulative Effect: %{y:.2%}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['cumulative_selection'],
        mode='lines+markers',
        name='Security Selection',
        line=dict(color='#ff7f0e', width=3),
        hovertemplate='<b>Security Selection</b><br>Date: %{x}<br>Cumulative Effect: %{y:.2%}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['cumulative_total'],
        mode='lines+markers',
        name='Total Attribution',
        line=dict(color='#2ca02c', width=3, dash='dash'),
        hovertemplate='<b>Total Attribution</b><br>Date: %{x}<br>Cumulative Effect: %{y:.2%}<extra></extra>'
    ))
    
    # Add horizontal line at zero
    fig.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.7)
    
    # Update layout
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16}
        },
        xaxis_title="Date",
        yaxis_title="Cumulative Attribution (%)",
        yaxis=dict(tickformat='.1%'),
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        template='plotly_white',
        width=900,
        height=500
    )
    
    # Show the plot
    fig.show()
    
    # Save if path provided
    if save_path:
        fig.write_html(save_path)


def _plot_cumulative_matplotlib(df: pd.DataFrame, title: str, save_path: Optional[str]) -> None:
    """Generate cumulative attribution chart using Matplotlib"""
    plt.figure(figsize=(12, 6))
    
    # Plot lines
    plt.plot(df.index, df['cumulative_allocation'], 
             label='Asset Allocation', linewidth=2.5, marker='o', markersize=4)
    plt.plot(df.index, df['cumulative_selection'], 
             label='Security Selection', linewidth=2.5, marker='s', markersize=4)
    plt.plot(df.index, df['cumulative_total'], 
             label='Total Attribution', linewidth=2.5, linestyle='--', marker='^', markersize=4)
    
    # Add horizontal line at zero
    plt.axhline(y=0, color='gray', linestyle=':', alpha=0.7)
    
    # Formatting
    plt.title(title, fontsize=14, fontweight='bold', pad=20)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Cumulative Attribution (%)', fontsize=12)
    plt.legend(loc='best')
    plt.grid(True, alpha=0.3)
    
    # Format y-axis as percentage
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.1%}'.format(y)))
    
    plt.tight_layout()
    
    # Save if path provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    plt.show()


def _plot_waterfall_plotly(waterfall_data: List[Dict], title: str, 
                          period_label: str, save_path: Optional[str]) -> None:
    """Generate waterfall chart using Plotly"""
    components = [item['component'] for item in waterfall_data]
    values = [item['value'] for item in waterfall_data]
    
    # Create waterfall chart
    fig = go.Figure(go.Waterfall(
        name="Attribution",
        orientation="v",
        measure=["relative"] * (len(components) - 1) + ["total"],
        x=components,
        textposition="outside",
        text=[f"{val:.2%}" for val in values],
        y=values,
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": "#2ca02c"}},
        decreasing={"marker": {"color": "#d62728"}},
        totals={"marker": {"color": "#1f77b4"}}
    ))
    
    fig.update_layout(
        title={
            'text': f"{title}<br><sub>{period_label}</sub>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16}
        },
        xaxis_title="Attribution Components",
        yaxis_title="Contribution to Excess Return (%)",
        yaxis=dict(tickformat='.2%'),
        template='plotly_white',
        width=800,
        height=500,
        showlegend=False
    )
    
    # Show the plot
    fig.show()
    
    # Save if path provided
    if save_path:
        fig.write_html(save_path)


def _plot_waterfall_matplotlib(waterfall_data: List[Dict], title: str, 
                              period_label: str, save_path: Optional[str]) -> None:
    """Generate waterfall chart using Matplotlib"""
    components = [item['component'] for item in waterfall_data]
    values = [item['value'] for item in waterfall_data]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Calculate positions for waterfall
    cumulative = 0
    positions = []
    colors = []
    
    for i, (comp, val) in enumerate(zip(components, values)):
        if comp == 'Total':
            # Total bar starts from zero
            positions.append(0)
            colors.append('#1f77b4')
        else:
            # Component bars start from cumulative
            positions.append(cumulative)
            colors.append('#2ca02c' if val >= 0 else '#d62728')
            cumulative += val
    
    # Create bars
    bars = ax.bar(components, values, bottom=positions, color=colors, alpha=0.8, edgecolor='black')
    
    # Add value labels on bars
    for i, (bar, val) in enumerate(zip(bars, values)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., 
                positions[i] + height/2,
                f'{val:.2%}', 
                ha='center', va='center', fontweight='bold', fontsize=10)
    
    # Add connecting lines (simplified)
    for i in range(len(components) - 2):
        if components[i+1] != 'Total':
            x1 = i + 0.4
            x2 = i + 1 - 0.4
            y = cumulative - values[i+1] if i < len(values) - 1 else cumulative
            ax.plot([x1, x2], [y, y], 'k--', alpha=0.5, linewidth=1)
    
    # Add horizontal line at zero
    ax.axhline(y=0, color='gray', linestyle=':', alpha=0.7)
    
    # Formatting
    ax.set_title(f"{title}\n{period_label}", fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('Attribution Components', fontsize=12)
    ax.set_ylabel('Contribution to Excess Return (%)', fontsize=12)
    ax.grid(True, alpha=0.3)
    
    # Format y-axis as percentage
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.2%}'.format(y)))
    
    # Rotate x-axis labels if needed
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Save if path provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    plt.show()


def create_attribution_dashboard(multi_period_results: Dict[str, Any],
                               latest_period_data: Union[Dict, pd.Series],
                               save_path: Optional[str] = None) -> None:
    """
    Create a comprehensive attribution dashboard with both cumulative and waterfall charts.
    
    Args:
        multi_period_results: Multi-period attribution results
        latest_period_data: Data for the latest period for waterfall chart
        save_path: Optional path to save the dashboard
    """
    logger.info("Creating comprehensive attribution dashboard")
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Cumulative Performance Attribution", "Latest Period Attribution Breakdown"),
        vertical_spacing=0.15,
        specs=[[{"secondary_y": False}], [{"type": "waterfall"}]]
    )
    
    # Extract monthly data for cumulative chart
    if 'monthly_results' in multi_period_results:
        df = _extract_monthly_results(multi_period_results['monthly_results'])
    else:
        df = pd.DataFrame(multi_period_results)
    
    # Add cumulative attribution traces
    if not df.empty:
        df['cumulative_allocation'] = df['allocation_effect'].cumsum()
        df['cumulative_selection'] = df['selection_effect'].cumsum()
        df['cumulative_total'] = df['cumulative_allocation'] + df['cumulative_selection']
        
        fig.add_trace(
            go.Scatter(x=df.index, y=df['cumulative_allocation'], 
                      name='Asset Allocation', line=dict(color='#1f77b4')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['cumulative_selection'], 
                      name='Security Selection', line=dict(color='#ff7f0e')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['cumulative_total'], 
                      name='Total', line=dict(color='#2ca02c', dash='dash')),
            row=1, col=1
        )
    
    # Extract waterfall data
    waterfall_components = _extract_waterfall_components(latest_period_data)
    components = ['Asset Allocation', 'Security Selection', 'Interaction', 'Total']
    values = [
        waterfall_components.get('allocation_effect', 0),
        waterfall_components.get('selection_effect', 0),
        waterfall_components.get('interaction_effect', 0),
        waterfall_components.get('total_attribution', 0)
    ]
    
    # Add waterfall chart
    fig.add_trace(
        go.Waterfall(
            x=components[:3],
            measure=["relative", "relative", "relative"],
            y=values[:3],
            name="Components"
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        title_text="Performance Attribution Analysis Dashboard",
        height=800,
        showlegend=True,
        template='plotly_white'
    )
    
    # Update y-axes to show percentages
    fig.update_yaxes(tickformat='.2%', title_text="Cumulative Attribution", row=1, col=1)
    fig.update_yaxes(tickformat='.2%', title_text="Attribution Components", row=2, col=1)
    
    # Show the dashboard
    fig.show()
    
    # Save if path provided
    if save_path:
        fig.write_html(save_path)
    
    logger.info("Attribution dashboard created successfully")
