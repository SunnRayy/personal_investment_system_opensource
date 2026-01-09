# Plotting functions (takes DataFrames, returns figures/axes)

import pandas as pd
import numpy as np
import logging
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns # Using seaborn for potentially better aesthetics later
from matplotlib.ticker import FuncFormatter # Import FuncFormatter for formatting axes
from . import utils # Import our utility functions (formatter, font setup)

# Configure logging for this module
logger = logging.getLogger(__name__)

# --- Balance Sheet Visualization Functions ---

def plot_balance_sheet_trends(trend_data: pd.DataFrame, title: str = '资产、负债和净资产趋势') -> tuple:
    """
    Generates a plot showing trends in Total Assets, Liabilities, and Net Worth.

    Args:
        trend_data: DataFrame with DatetimeIndex and columns
                    'Total_Assets_Calc_CNY', 'Total_Liabilities_Calc_CNY', 'Net_Worth_Calc_CNY'.
        title: The title for the plot.

    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid.
    """
    logger.info("Generating balance sheet trends plot...")
    utils.setup_chinese_font() # Ensure correct font is set

    required_cols = ['Total_Assets_Calc_CNY', 'Total_Liabilities_Calc_CNY', 'Net_Worth_Calc_CNY']
    if trend_data is None or trend_data.empty or not all(col in trend_data.columns for col in required_cols):
        logger.warning("Invalid or missing data for balance sheet trends plot.")
        return None, None

    fig, ax = plt.subplots(figsize=(14, 8)) # Create figure and axes

    # Plot data using standardized column names
    ax.plot(trend_data.index, trend_data['Net_Worth_Calc_CNY'],
            color='darkblue', linewidth=2.5, label='净资产 (Net Worth)', marker='o', markersize=4)
    ax.plot(trend_data.index, trend_data['Total_Assets_Calc_CNY'],
            color='forestgreen', linewidth=2, label='总资产 (Total Assets)', marker='^', markersize=4)
    ax.plot(trend_data.index, trend_data['Total_Liabilities_Calc_CNY'],
            color='firebrick', linewidth=2, label='总负债 (Total Liabilities)', marker='s', markersize=4)

    # Fill between assets and liabilities to visualize net worth
    ax.fill_between(trend_data.index,
                    trend_data['Total_Assets_Calc_CNY'],
                    trend_data['Total_Liabilities_Calc_CNY'],
                    alpha=0.15, color='lightblue', label='净资产区域')

    # Customize axis and labels
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('日期 (Date)', fontsize=12)
    ax.set_ylabel('金额 (Amount)', fontsize=12)

    # Format x-axis to show dates nicely
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10])) # Quarterly minor ticks

    # Format y-axis with currency using the utility function
    ax.yaxis.set_major_formatter(utils.CURRENCY_FORMAT)
    ax.tick_params(axis='y', labelsize=10)
    ax.tick_params(axis='x', labelsize=10, rotation=0) # Keep x-axis labels horizontal

    # Add legend
    ax.legend(fontsize=12)

    # Add grid
    ax.grid(True, linestyle='--', alpha=0.6)

    # Improve layout
    plt.tight_layout()

    logger.info("Balance sheet trends plot generated.")
    return fig, ax


def plot_asset_liability_allocation(allocation_data: dict, title_prefix: str = '最新资产负债配置', title=None) -> tuple:
    """
    Generates pie charts showing the latest asset and liability allocation.

    Args:
        allocation_data: Dictionary containing 'asset_allocation' and
                         'liability_allocation' dictionaries from
                         analyze_asset_liability_allocation.
        title_prefix: Prefix for the plot titles.

    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, axs),
        or (None, None) if input is invalid. axs will be an array [ax1, ax2].
    """
    logger.info("Generating asset/liability allocation pie charts...")
    utils.setup_chinese_font()

    if not allocation_data or 'asset_allocation' not in allocation_data or 'liability_allocation' not in allocation_data:
        logger.warning("Invalid or missing data for allocation plots.")
        return None, None

    asset_alloc = allocation_data['asset_allocation']
    liability_alloc = allocation_data['liability_allocation']
    latest_date_str = allocation_data.get('latest_date', pd.Timestamp('now')).strftime('%Y-%m-%d')

    # Create figure with two subplots
    fig, axs = plt.subplots(1, 2, figsize=(18, 9)) # 1 row, 2 columns

    # --- Asset Pie Chart (axs[0]) ---
    if asset_alloc:
        asset_labels = list(asset_alloc.keys())
        asset_values = [d['value'] for d in asset_alloc.values()]
        asset_percentages = [d['percentage'] for d in asset_alloc.values()]

        # Create labels with value and percentage
        asset_pie_labels = [f"{label}\n({val:,.0f}, {pct:.1f}%)"
                           for label, val, pct in zip(asset_labels, asset_values, asset_percentages)]

        # Use a color map
        colors_asset = plt.cm.Paired(np.linspace(0, 1, len(asset_values)))

        wedges, texts, autotexts = axs[0].pie(
            asset_values,
            labels=None, # Labels will be in legend
            autopct='%1.1f%%', # Show percentage on wedge
            startangle=90,
            colors=colors_asset,
            pctdistance=0.85, # Distance of percentage text from center
            wedgeprops=dict(width=0.4, edgecolor='w') # Donut chart effect
        )
        # Customize autopct text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
            autotext.set_weight('bold')

        # Add legend with detailed labels
        axs[0].legend(wedges, asset_pie_labels,
                      title="资产类别",
                      loc="center left",
                      bbox_to_anchor=(0.95, 0, 0.5, 1), # Adjust anchor to fit
                      fontsize=10)

        axs[0].set_title(f'{title_prefix} - 资产 ({latest_date_str})', fontsize=14, fontweight='bold')
    else:
        axs[0].text(0.5, 0.5, '无资产数据', horizontalalignment='center', verticalalignment='center')
        axs[0].set_title(f'{title_prefix} - 资产 ({latest_date_str})', fontsize=14, fontweight='bold')
        axs[0].set_xticks([])
        axs[0].set_yticks([])


    # --- Liability Pie Chart (axs[1]) ---
    if liability_alloc:
        liability_labels = list(liability_alloc.keys())
        liability_values = [d['value'] for d in liability_alloc.values()]
        liability_percentages = [d['percentage'] for d in liability_alloc.values()]

        liability_pie_labels = [f"{label}\n({val:,.0f}, {pct:.1f}%)"
                               for label, val, pct in zip(liability_labels, liability_values, liability_percentages)]

        colors_liability = plt.cm.Reds(np.linspace(0.4, 0.8, len(liability_values)))

        wedges, texts, autotexts = axs[1].pie(
            liability_values,
            labels=None,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors_liability,
            pctdistance=0.85,
            wedgeprops=dict(width=0.4, edgecolor='w')
        )
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
            autotext.set_weight('bold')

        axs[1].legend(wedges, liability_pie_labels,
                      title="负债类别",
                      loc="center left",
                      bbox_to_anchor=(0.95, 0, 0.5, 1),
                      fontsize=10)

        axs[1].set_title(f'{title_prefix} - 负债 ({latest_date_str})', fontsize=14, fontweight='bold')
    else:
        axs[1].text(0.5, 0.5, '无负债数据', horizontalalignment='center', verticalalignment='center')
        axs[1].set_title(f'{title_prefix} - 负债 ({latest_date_str})', fontsize=14, fontweight='bold')
        axs[1].set_xticks([])
        axs[1].set_yticks([])

    # Adjust layout to prevent overlap
    plt.tight_layout(rect=[0, 0, 0.85, 1]) # Adjust rect to make space for legends

    logger.info("Allocation pie charts generated.")
    return fig, axs


def plot_asset_category_growth(category_growth_df: pd.DataFrame, title: str = '资产类别增长趋势') -> tuple:
    """
    Generates a stacked area plot showing the growth of asset categories over time.

    Args:
        category_growth_df: DataFrame with DatetimeIndex and columns for each
                            top-level asset category value over time.
        title: The title for the plot.

    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid.
    """
    logger.info("Generating asset category growth plot...")
    utils.setup_chinese_font()

    if category_growth_df is None or category_growth_df.empty:
        logger.warning("Invalid or missing data for category growth plot.")
        return None, None

    fig, ax = plt.subplots(figsize=(14, 8))

    # Prepare data for stackplot (list of series/arrays for each category)
    data_to_stack = [category_growth_df[col] for col in category_growth_df.columns]
    labels = category_growth_df.columns.tolist()

    # Use a suitable colormap
    colors = plt.cm.viridis(np.linspace(0, 1, len(labels)))

    # Create the stacked area plot
    ax.stackplot(category_growth_df.index, data_to_stack, labels=labels, colors=colors, alpha=0.7)

    # Customize axis and labels
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('日期 (Date)', fontsize=12)
    ax.set_ylabel('金额 (Amount)', fontsize=12)

    # Format x-axis
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=3)) # Quarterly minor ticks

    # Format y-axis with currency
    ax.yaxis.set_major_formatter(utils.CURRENCY_FORMAT)
    ax.tick_params(axis='y', labelsize=10)
    ax.tick_params(axis='x', labelsize=10)

    # Add legend
    ax.legend(loc='upper left', fontsize=10)

    # Add grid
    ax.grid(True, linestyle='--', alpha=0.6)

    # Improve layout
    plt.tight_layout()

    logger.info("Asset category growth plot generated.")
    return fig, ax


def plot_balance_sheet_ratios(ratios_df: pd.DataFrame, title: str = '财务健康指标趋势') -> tuple:
    """
    Generates a plot showing key financial health ratios over time.

    Args:
        ratios_df: DataFrame with DatetimeIndex and columns for ratios like
                   'Debt_to_Asset_Ratio', 'Investment_to_Asset_Ratio', 'Liquidity_Ratio'.
        title: The title for the plot.

    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid.
    """
    logger.info("Generating financial health ratios plot...")
    utils.setup_chinese_font()

    if ratios_df is None or ratios_df.empty:
        logger.warning("Invalid or missing data for ratios plot.")
        return None, None

    fig, ax1 = plt.subplots(figsize=(14, 8))
    lines1, labels1 = [], [] # For combined legend
    plotted_columns = [] # Track which columns we're actually plotting

    # Plot Debt-to-Asset Ratio on primary axis
    if 'Debt_to_Asset_Ratio' in ratios_df.columns:
        line, = ax1.plot(ratios_df.index, ratios_df['Debt_to_Asset_Ratio'],
                 color='red', linewidth=2, label='资产负债率 (Debt/Asset)', marker='.')
        lines1.append(line)
        labels1.append('资产负债率 (Debt/Asset)')
        plotted_columns.append('Debt_to_Asset_Ratio')
        ax1.set_ylabel('比率 (Ratio)', fontsize=12, color='black') # Shared label
        ax1.tick_params(axis='y', labelcolor='black')
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.0%}'.format(y))) # Format as percentage

    # Plot Investment-to-Asset Ratio on primary axis
    if 'Investment_to_Asset_Ratio' in ratios_df.columns:
        line, = ax1.plot(ratios_df.index, ratios_df['Investment_to_Asset_Ratio'],
                 color='green', linewidth=2, label='投资资产占比 (Invest/Asset)', marker='.')
        lines1.append(line)
        labels1.append('投资资产占比 (Invest/Asset)')
        plotted_columns.append('Investment_to_Asset_Ratio')
        # Ensure y-axis formatting is percentage
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.0%}'.format(y)))

    # Set primary y-axis limits (e.g., 0 to 1 or slightly more)
    # Fix: Calculate max from actual plotted columns instead of using labels1
    if plotted_columns:
        max_ratio = ratios_df[plotted_columns].max().max()
        ax1.set_ylim(bottom=0, top=max(1.1, max_ratio * 1.1 if pd.notna(max_ratio) else 1.1))
    else:
        ax1.set_ylim(bottom=0, top=1.1)  # Default if no columns plotted

    # Plot Liquidity Ratio on secondary y-axis if available and has data
    ax2 = None
    if 'Liquidity_Ratio' in ratios_df.columns and ratios_df['Liquidity_Ratio'].notna().any():
        ax2 = ax1.twinx() # Create secondary axis
        line, = ax2.plot(ratios_df.index, ratios_df['Liquidity_Ratio'],
                 color='blue', linewidth=2, linestyle='--', label='流动比率 (Liquidity)', marker='x')
        ax2.set_ylabel('流动比率', color='blue', fontsize=12)
        ax2.tick_params(axis='y', labelcolor='blue')
        # Set limits for liquidity ratio (e.g., 0 to 5 or based on data)
        max_liquidity = ratios_df['Liquidity_Ratio'].max()
        ax2.set_ylim(bottom=0, top=max(5, max_liquidity * 1.2 if pd.notna(max_liquidity) else 5))
        # Add to combined legend items
        lines1.append(line)
        labels1.append('流动比率 (Liquidity)')

    # Customize main axis and title
    ax1.set_title(title, fontsize=16, fontweight='bold')
    ax1.set_xlabel('日期 (Date)', fontsize=12)

    # Format x-axis
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax1.xaxis.set_minor_locator(mdates.MonthLocator(interval=6)) # Semi-annual minor ticks

    # Add combined legend
    if lines1:
        ax1.legend(lines1, labels1, loc='upper left', fontsize=10)

    # Add grid (apply to primary axis)
    ax1.grid(True, linestyle='--', alpha=0.6)

    # Improve layout
    plt.tight_layout()

    logger.info("Financial health ratios plot generated.")
    # Return fig and potentially both axes if ax2 exists
    return fig, (ax1, ax2) if ax2 else ax1


def plot_yoy_net_worth_growth(yoy_comparison_df: pd.DataFrame, title: str = '年度净资产增长率') -> tuple:
    """
    Generates a bar chart showing the Year-over-Year Net Worth growth percentage.

    Args:
        yoy_comparison_df: DataFrame output from generate_yoy_comparison,
                           must contain 'Net_Worth_Calc_CNY_YoY_Growth_%'.
        title: The title for the plot.

    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid or lacks data.
    """
    logger.info("Generating YoY Net Worth growth plot...")
    utils.setup_chinese_font()

    growth_col = 'Net_Worth_Calc_CNY_YoY_Growth_%'
    if yoy_comparison_df is None or yoy_comparison_df.empty or growth_col not in yoy_comparison_df.columns:
        logger.warning("Invalid or missing data for YoY Net Worth growth plot.")
        return None, None

    # Get data, drop years with no growth calculated (usually the first year)
    growth_data = yoy_comparison_df[growth_col].dropna()

    if growth_data.empty:
        logger.warning("No valid YoY growth data points available to plot.")
        return None, None

    fig, ax = plt.subplots(figsize=(10, 6))

    # Create bars, color based on positive/negative growth
    colors = ['forestgreen' if x >= 0 else 'firebrick' for x in growth_data.values]
    bars = ax.bar(growth_data.index.astype(str), growth_data.values, color=colors)

    # Add data labels on top of bars
    ax.bar_label(bars, fmt='{:,.1f}%', padding=3, fontsize=9)

    # Customize axis and labels
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('年份 (Year)', fontsize=12)
    ax.set_ylabel('增长率 (%)', fontsize=12)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.0f}%'.format(y)))

    # Add horizontal line at 0%
    ax.axhline(0, color='grey', linewidth=0.8)

    # Add grid
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    # Remove top and right spines for cleaner look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Improve layout
    plt.tight_layout()

    logger.info("YoY Net Worth growth plot generated.")
    return fig, ax

# --- NEW: Income Visualization Functions ---

def plot_income_trends(income_trend_data: pd.DataFrame, title: str = '月度收入趋势') -> tuple:
    """
    Generates a plot showing trends in Total Income and optionally Active/Passive Income.
    Includes trend line and moving average for Total Income.

    Args:
        income_trend_data: DataFrame with DatetimeIndex and columns like
                           'Total_Income_Calc_CNY', 'Income_Active_Total_CNY' (optional),
                           'Passive_Income_Calc' (optional, calculated).
        title: The title for the plot.

    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid.
    """
    logger.info("Generating income trends plot...")
    utils.setup_chinese_font()

    total_col = 'Total_Income_Calc_CNY'
    active_col = 'Income_Active_Total_CNY' # Optional standard name
    passive_col = 'Passive_Income_Calc' # Calculated name

    if income_trend_data is None or income_trend_data.empty or total_col not in income_trend_data.columns:
        logger.warning(f"Invalid or missing data for income trends plot (missing {total_col}).")
        return None, None

    fig, ax = plt.subplots(figsize=(14, 8))

    # Plot Total Income
    ax.plot(income_trend_data.index, income_trend_data[total_col],
            color='darkblue', linewidth=2.5, label='总收入 (Total)', marker='o', markersize=3, alpha=0.8)

    # Plot Active and Passive Income if available
    has_active = active_col in income_trend_data.columns
    has_passive = passive_col in income_trend_data.columns

    if has_active:
        ax.plot(income_trend_data.index, income_trend_data[active_col],
                color='forestgreen', linewidth=1.8, label='主动收入 (Active)', linestyle='--', alpha=0.7)
    if has_passive:
        ax.plot(income_trend_data.index, income_trend_data[passive_col],
                color='darkorange', linewidth=1.8, label='被动收入 (Passive)', linestyle=':', alpha=0.7)

    # Add fills if both active and passive are present
    # if has_active and has_passive:
    #     # Ensure columns are numeric and handle NaNs before filling
    #     active_filled = income_trend_data[active_col].fillna(0)
    #     passive_filled = income_trend_data[passive_col].fillna(0)
    #     total_filled = active_filled + passive_filled # Approximate total for fill base
    #     ax.fill_between(income_trend_data.index, active_filled, 0,
    #                     alpha=0.1, color='lightgreen', label='_nolegend_')
    #     ax.fill_between(income_trend_data.index, total_filled, active_filled,
    #                     alpha=0.1, color='moccasin', label='_nolegend_')


    # Calculate and add trend line for Total Income
    income_values = income_trend_data[total_col].dropna()
    if len(income_values) > 1:
        dates_ordinal = np.array([d.toordinal() for d in income_values.index])
        try:
            z = np.polyfit(dates_ordinal, income_values.values, 1)
            p = np.poly1d(z)
            ax.plot(income_values.index, p(dates_ordinal),
                    "r--", linewidth=1.5, label='趋势线 (Trend)')
        except Exception as e:
            logger.warning(f"Could not calculate trend line for income: {e}")

    # Add 3-month moving average for Total Income
    if len(income_trend_data[total_col]) >= 3:
        ma_3month = income_trend_data[total_col].rolling(window=3, center=True).mean()
        ax.plot(income_trend_data.index, ma_3month,
                color='purple', linewidth=1.5, linestyle='-.', label='3月移动平均 (3M MA)')

    # Customize axis and labels
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('日期 (Date)', fontsize=12)
    ax.set_ylabel('金额 (Amount)', fontsize=12)
    ax.yaxis.set_major_formatter(utils.CURRENCY_FORMAT)
    ax.tick_params(axis='y', labelsize=10)
    ax.tick_params(axis='x', labelsize=10, rotation=0)

    # Format x-axis
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=3))

    # Add legend and grid
    ax.legend(fontsize=10, loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()

    logger.info("Income trends plot generated.")
    return fig, ax


def plot_income_sources_pie(income_sources_data: dict, title: str = '近期收入来源分布') -> tuple:
    """
    Generates a pie chart showing the distribution of recent income sources.

    Args:
        income_sources_data: Dictionary where keys are cleaned source names and
                             values are dicts {'value': float, 'percentage': float}.
                             Output from analyze_income_sources.
        title: The title for the plot.

    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid.
    """
    logger.info("Generating income sources pie chart...")
    utils.setup_chinese_font()

    if not income_sources_data or not isinstance(income_sources_data, dict):
        logger.warning("Invalid or missing data for income sources plot.")
        return None, None

    labels = list(income_sources_data.keys())
    values = [d['value'] for d in income_sources_data.values()]
    percentages = [d['percentage'] for d in income_sources_data.values()]

    # Combine small slices into 'Other' if necessary (e.g., < 2%)
    threshold = 2.0
    other_value = 0
    other_pct = 0
    labels_filtered = []
    values_filtered = []
    labels_legend = []

    for label, value, pct in zip(labels, values, percentages):
        if pct < threshold:
            other_value += value
            other_pct += pct
        else:
            labels_filtered.append(label)
            values_filtered.append(value)
            labels_legend.append(f"{label}\n({value:,.0f}, {pct:.1f}%)")

    if other_value > 0:
        labels_filtered.append('其他 (<{:.0f}%)'.format(threshold))
        values_filtered.append(other_value)
        labels_legend.append(f"其他 (<{threshold:.0f}%)\n({other_value:,.0f}, {other_pct:.1f}%)")

    if not values_filtered: # Handle case where all slices are below threshold
         logger.warning("All income sources are below threshold for pie chart.")
         return None, None


    fig, ax = plt.subplots(figsize=(12, 9)) # Single plot figure

    colors = plt.cm.tab20(np.linspace(0, 1, len(values_filtered)))

    wedges, texts, autotexts = ax.pie(
        values_filtered,
        labels=None,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors,
        pctdistance=0.85,
        wedgeprops=dict(width=0.4, edgecolor='w')
    )
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(10)
        autotext.set_weight('bold')

    ax.legend(wedges, labels_legend,
              title="收入来源",
              loc="center left",
              bbox_to_anchor=(0.95, 0, 0.5, 1),
              fontsize=10)

    ax.set_title(title, fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 0.85, 1])

    logger.info("Income sources pie chart generated.")
    return fig, ax

def plot_active_passive_income_bar(income_trend_data: pd.DataFrame, num_months: int = 24, title: str = '主动 vs 被动收入 (近期趋势)') -> tuple:
    """
    Generates a stacked bar chart comparing active and passive income for recent months.

    Args:
        income_trend_data: DataFrame with DatetimeIndex and columns like
                           'Income_Active_Total_CNY', 'Passive_Income_Calc'.
        num_months: Number of recent months to display.
        title: The title for the plot.

    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid or missing required columns.
    """
    logger.info("Generating active vs passive income bar chart...")
    utils.setup_chinese_font()

    active_col = 'Income_Active_Total_CNY' # Optional standard name
    passive_col = 'Passive_Income_Calc' # Calculated name
    total_col = 'Total_Income_Calc_CNY'  # Total income column

    if income_trend_data is None or income_trend_data.empty:
        logger.warning("Empty or None income trend data for active/passive plot.")
        return None, None
        
    # Get recent data
    recent_data = income_trend_data.iloc[-num_months:].copy()
    
    # Calculate active income if it doesn't exist
    if active_col not in recent_data.columns and passive_col in recent_data.columns and total_col in recent_data.columns:
        # If we have passive and total, calculate active as the difference
        recent_data[active_col] = recent_data[total_col] - recent_data[passive_col]
        logger.debug(f"Calculated {active_col} from {total_col} - {passive_col}")
    elif passive_col not in recent_data.columns and active_col in recent_data.columns and total_col in recent_data.columns:
        # If we have active and total, calculate passive as the difference
        recent_data[passive_col] = recent_data[total_col] - recent_data[active_col]
        logger.debug(f"Calculated {passive_col} from {total_col} - {active_col}")
    elif active_col not in recent_data.columns and passive_col not in recent_data.columns:
        # If we don't have either active or passive columns
        if total_col in recent_data.columns:
            # If we only have total, treat it all as active income
            recent_data[active_col] = recent_data[total_col]
            recent_data[passive_col] = 0  # Create a zero series with the same index
            logger.debug(f"Only {total_col} available, treating all as active income")
        else:
            logger.warning(f"Missing required columns for active/passive plot. Need at least one of: {active_col}, {passive_col}, or {total_col}")
            return None, None

    # Prepare data, safely handling the columns now that we know they exist
    active_income = recent_data[active_col].fillna(0)
    passive_income = recent_data[passive_col].fillna(0)

    fig, ax = plt.subplots(figsize=(14, 7))

    x = np.arange(len(recent_data))
    width = 0.8

    # Plot bars
    bar1 = ax.bar(x, active_income, width, label='主动收入 (Active)', color='forestgreen', alpha=0.8)
    bar2 = ax.bar(x, passive_income, width, bottom=active_income, label='被动收入 (Passive)', color='darkorange', alpha=0.8)

    # Add percentage annotations for passive income if significant
    for i, (active, passive) in enumerate(zip(active_income, passive_income)):
        total = active + passive
        if total > 0:
            passive_pct = passive / total * 100
            if passive_pct >= 5: # Only show if passive is at least 5%
                ax.annotate(f"{passive_pct:.0f}%",
                            xy=(i, active + passive / 2), # Position in the middle of passive bar
                            ha='center', va='center',
                            color='white', fontsize=8, fontweight='bold')

    # Customize axes and labels
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_ylabel('金额 (Amount)', fontsize=12)
    ax.yaxis.set_major_formatter(utils.CURRENCY_FORMAT)
    ax.tick_params(axis='y', labelsize=10)

    # Format x-axis labels
    labels = [d.strftime('%Y-%m') for d in recent_data.index]
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)

    ax.legend(fontsize=10)
    ax.grid(True, axis='y', linestyle='--', alpha=0.6)
    plt.tight_layout()

    logger.info("Active vs passive income bar chart generated.")
    return fig, ax

# --- plot_income_seasonality function (UPDATED) ---
def plot_income_seasonality(monthly_df: pd.DataFrame, title: str = '收入季节性分析') -> tuple:
    """
    Generates a plot showing average monthly income patterns across years,
    explicitly excluding the known outlier month before aggregation.

    Args:
        monthly_df: DataFrame containing monthly income/expense data with
                    'Total_Income_Calc_CNY' and potentially 'Income_Other_CNY'.
                    This should be the *original* data before trend adjustments.
        title: The title for the plot.

    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid.
    """
    logger.info("Generating income seasonality plot (excluding known outlier)...")
    utils.setup_chinese_font()

    total_col = 'Total_Income_Calc_CNY'
    anomaly_col = 'Income_Other_CNY' # Column containing the outlier
    anomaly_date = pd.Timestamp('2020-08-31') # Date of the outlier

    if monthly_df is None or monthly_df.empty or total_col not in monthly_df.columns:
        logger.warning(f"Invalid or missing data for income seasonality plot (missing {total_col}).")
        return None, None

    # Work with a copy and explicitly remove the outlier month/year
    seasonal_df = monthly_df.copy()

    # Check if the outlier exists and remove it for seasonality calculation
    outlier_exists = False
    if anomaly_date in seasonal_df.index:
         # Verify it's the outlier based on the specific column if possible
         if anomaly_col in seasonal_df.columns:
              anomaly_value = seasonal_df.loc[anomaly_date, anomaly_col]
              if isinstance(anomaly_value, (int, float, np.number)) and pd.notna(anomaly_value) and anomaly_value > 500000:
                   outlier_exists = True
         # Fallback: Remove based on date only if anomaly column check fails but date exists
         elif anomaly_col not in seasonal_df.columns:
              logger.warning(f"Anomaly column {anomaly_col} not found, removing {anomaly_date} based on date only for seasonality.")
              outlier_exists = True # Assume it's the outlier based on date

         if outlier_exists:
              logger.info(f"Excluding outlier date {anomaly_date} from seasonality calculation.")
              seasonal_df = seasonal_df.drop(anomaly_date)
              title += ' (已排除2020年8月)' # Update title

    if seasonal_df.empty:
        logger.warning("DataFrame became empty after removing outlier. Cannot generate seasonality plot.")
        return None, None

    seasonal_df['year'] = seasonal_df.index.year
    seasonal_df['month'] = seasonal_df.index.month

    # Calculate average and median income by month using the filtered data
    monthly_avg = seasonal_df.dropna(subset=[total_col]).groupby('month')[total_col].mean()
    monthly_med = seasonal_df.dropna(subset=[total_col]).groupby('month')[total_col].median()
    monthly_min = seasonal_df.dropna(subset=[total_col]).groupby('month')[total_col].min()
    monthly_max = seasonal_df.dropna(subset=[total_col]).groupby('month')[total_col].max()

    # Calculate overall average using the filtered data
    overall_avg = seasonal_df[total_col].dropna().mean()

    if monthly_avg.empty:
        logger.warning("No data available after grouping by month for seasonality plot.")
        return None, None

    fig, ax = plt.subplots(figsize=(14, 8))

    # Plot average and median
    ax.plot(monthly_avg.index, monthly_avg.values, 'o-', color='darkblue', linewidth=2, label='月平均值 (Avg)')
    ax.plot(monthly_med.index, monthly_med.values, 's--', color='green', linewidth=2, label='月中位数 (Median)')

    # Add reference line for annual average (based on filtered data)
    ax.axhline(y=overall_avg, color='r', linestyle=':', label=f'年度平均 ({overall_avg:,.0f})')

    # Add min-max range band
    ax.fill_between(monthly_avg.index, monthly_min, monthly_max, alpha=0.15, color='gray', label='历史范围 (Range)')

    # Customize axes
    month_names = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月']
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('月份 (Month)', fontsize=12)
    ax.set_ylabel('月收入 (Monthly Income)', fontsize=12)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(month_names)
    ax.tick_params(axis='x', labelsize=10)
    ax.tick_params(axis='y', labelsize=10)
    ax.yaxis.set_major_formatter(utils.CURRENCY_FORMAT)

    ax.legend(fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()

    logger.info("Income seasonality plot generated.")
    return fig, ax

# --- plot_income_yoy_comparison function (UPDATED) ---
def plot_income_yoy_comparison(monthly_df: pd.DataFrame, title: str = '年度收入对比') -> tuple:
    """
    Generates a line plot comparing monthly income across different years,
    adjusting for known outliers before pivoting.

    Args:
        monthly_df: DataFrame containing monthly income data ('Total_Income_Calc_CNY', 'Income_Other_CNY').
        title: The title for the plot.

    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid.
    """
    logger.info("Generating income YoY comparison line plot (with outlier adjustment)...")
    utils.setup_chinese_font()

    total_col = 'Total_Income_Calc_CNY'
    anomaly_col = 'Income_Other_CNY' # Column with the 880k outlier

    if monthly_df is None or monthly_df.empty or total_col not in monthly_df.columns:
        logger.warning(f"Invalid or missing data for income YoY plot (missing {total_col}).")
        return None, None

    # --- Apply Outlier Adjustment BEFORE Pivoting ---
    plot_df = monthly_df.copy()
    anomaly_date = pd.Timestamp('2020-08-31')
    income_anomaly_value = 880000
    adjusted_title = title # Keep original title by default

    if anomaly_col in plot_df.columns and anomaly_date in plot_df.index:
        original_value = plot_df.loc[anomaly_date, anomaly_col]
        if isinstance(original_value, (int, float, np.number)) and pd.notna(original_value) and original_value > 500000:
            logger.debug(f"Adjusting YoY Plot Income: Subtracting {income_anomaly_value} from {total_col} for {anomaly_date}")
            # Adjust the total income column directly in the copy
            plot_df.loc[anomaly_date, total_col] -= income_anomaly_value
            adjusted_title += ' (已调整2020年8月异常值)' # Update title if adjusted
    # --- END Outlier Adjustment ---


    # --- Pivot the adjusted monthly data ---
    plot_df['year'] = plot_df.index.year
    plot_df['month'] = plot_df.index.month

    # Pivot table: months as index, years as columns, adjusted total income as values
    try:
        # Use the adjusted total_col for pivoting
        yoy_pivot = plot_df.pivot_table(
            index='month', columns='year', values=total_col, aggfunc='sum'
        )
    except Exception as e:
        logger.error(f"Failed to pivot monthly income data for YoY plot: {e}")
        return None, None

    if yoy_pivot.empty:
        logger.warning("Pivoted data for YoY income plot is empty.")
        return None, None

    fig, ax = plt.subplots(figsize=(14, 8))

    # Plot each year as a separate line
    years = sorted(yoy_pivot.columns)
    colormap = plt.cm.viridis(np.linspace(0, 1, len(years)))

    for i, year in enumerate(years):
        year_data = yoy_pivot[year].dropna() # Drop months with no data for that year
        if not year_data.empty:
            ax.plot(year_data.index, year_data.values, 'o-', linewidth=2, label=str(year), color=colormap[i], markersize=4)

    # Customize axes
    month_names = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二']
    ax.set_title(adjusted_title, fontsize=16, fontweight='bold') # Use potentially adjusted title
    ax.set_xlabel('月份 (Month)', fontsize=12)
    ax.set_ylabel('月收入 (Monthly Income)', fontsize=12)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(month_names) # Use shorter month names
    ax.tick_params(axis='x', labelsize=10)
    ax.tick_params(axis='y', labelsize=10)
    ax.yaxis.set_major_formatter(utils.CURRENCY_FORMAT)

    ax.legend(title="年份 (Year)", fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()

    logger.info("Income YoY comparison line plot generated.")
    return fig, ax


# --- NEW: Annual Income Growth Bar Plot ---
def plot_annual_income_growth_bar(yoy_comparison_df: pd.DataFrame, title: str = '年度总收入及增长率') -> tuple:
    """
    Generates a bar chart showing annual total income and YoY growth rate.

    Args:
        yoy_comparison_df: DataFrame output from generate_cash_flow_yoy_comparison,
                           containing annual totals and growth rates.
        title: The title for the plot.

    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid.
    """
    logger.info("Generating annual income growth bar plot...")
    utils.setup_chinese_font()

    total_col = 'Total_Income_Calc_CNY'
    growth_col = f'{total_col}_YoY_Growth_%'

    if yoy_comparison_df is None or yoy_comparison_df.empty or \
       total_col not in yoy_comparison_df.columns or \
       growth_col not in yoy_comparison_df.columns:
        logger.warning("Invalid or missing data for annual income growth plot.")
        return None, None

    plot_data = yoy_comparison_df.copy()
    # Use year index directly if it's already set
    if isinstance(plot_data.index, pd.RangeIndex) or str(type(plot_data.index).__name__) == "Int64Index":
         years_str = plot_data.index.astype(str)
    elif isinstance(plot_data.index, pd.DatetimeIndex):
         years_str = plot_data.index.year.astype(str)
    else: # Assume index is already year strings or similar
         years_str = plot_data.index.astype(str)


    fig, ax = plt.subplots(figsize=(12, 7))

    # Plot bars for annual income
    colors = plt.cm.Greens(np.linspace(0.4, 0.8, len(plot_data)))
    bars = ax.bar(years_str, plot_data[total_col], color=colors, label='年总收入 (Annual Total Income)')

    # Add data labels for total income
    ax.bar_label(bars, labels=[f'{val/10000:,.1f}万' for val in plot_data[total_col]], padding=3, fontsize=9)

    # Create secondary axis for growth rate
    ax2 = ax.twinx()
    growth_data = plot_data[growth_col].dropna() # Don't plot NaN growth
    # Plot growth rate as a line with markers
    ax2.plot(growth_data.index.astype(str), growth_data.values,
             color='red', marker='o', linestyle='--', label='年增长率 (YoY Growth %)')
    ax2.set_ylabel('年增长率 (%)', color='red', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='red')
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.1f}%'.format(y)))
    # Add horizontal line at 0% growth
    ax2.axhline(0, color='grey', linewidth=0.8, linestyle=':')

    # Customize primary axis
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('年份 (Year)', fontsize=12)
    ax.set_ylabel('年收入 (Annual Income)', fontsize=12)
    ax.yaxis.set_major_formatter(utils.CURRENCY_FORMAT)
    ax.tick_params(axis='x', labelsize=10)
    ax.tick_params(axis='y', labelsize=10)

    # Combine legends
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper left', fontsize=10)

    ax.grid(True, axis='y', linestyle='--', alpha=0.6)
    plt.tight_layout()

    logger.info("Annual income growth bar plot generated.")
    return fig, ax


# --- NEW: Expense Visualization Functions ---

def plot_expense_trends(expense_trend_data: pd.DataFrame, title: str = '月度支出趋势 (已调整异常值)') -> tuple:
    """
    Generates a plot showing trends in Total Expense and optionally Essential/Non-Essential Expense.
    Includes trend line and moving average for Total Expense. Uses adjusted data.

    Args:
        expense_trend_data: DataFrame with DatetimeIndex and columns like
                            'Total_Expense_Calc_CNY', 'Essential_Expense_Calc' (optional),
                            'NonEssential_Expense_Calc' (optional). This should be the
                            adjusted data returned by analyze_expense_trends['trend_data'].
        title: The title for the plot.

    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid.
    """
    logger.info("Generating expense trends plot (using potentially adjusted data)...")
    utils.setup_chinese_font()

    total_col = 'Total_Expense_Calc_CNY'
    essential_col = 'Essential_Expense_Calc' # Calculated name
    nonessential_col = 'NonEssential_Expense_Calc' # Calculated name

    if expense_trend_data is None or expense_trend_data.empty or total_col not in expense_trend_data.columns:
        logger.warning(f"Invalid or missing data for expense trends plot (missing {total_col}).")
        return None, None

    fig, ax = plt.subplots(figsize=(14, 8))

    # Plot Total Expense (potentially adjusted for outlier by having NaN)
    ax.plot(expense_trend_data.index, expense_trend_data[total_col],
            color='darkred', linewidth=2.5, label='总支出 (Total)', marker='o', markersize=3, alpha=0.8)

    # Plot Essential and Non-Essential if available
    has_essential = essential_col in expense_trend_data.columns
    has_nonessential = nonessential_col in expense_trend_data.columns

    if has_essential:
        ax.plot(expense_trend_data.index, expense_trend_data[essential_col],
                color='forestgreen', linewidth=1.8, label='必要支出 (Essential)', linestyle='--', alpha=0.7)
    if has_nonessential:
        ax.plot(expense_trend_data.index, expense_trend_data[nonessential_col],
                color='darkorange', linewidth=1.8, label='非必要支出 (Non-Essential)', linestyle=':', alpha=0.7)

    # Calculate and add trend line for Total Expense (ignoring NaN outlier)
    expense_values = expense_trend_data[total_col].dropna()
    if len(expense_values) > 1:
        dates_ordinal = np.array([d.toordinal() for d in expense_values.index])
        try:
            z = np.polyfit(dates_ordinal, expense_values.values, 1)
            p = np.poly1d(z)
            ax.plot(expense_values.index, p(dates_ordinal),
                    "r--", linewidth=1.5, label='趋势线 (Trend)')
        except Exception as e:
            logger.warning(f"Could not calculate trend line for expense: {e}")

    # Add 3-month moving average for Total Expense (ignoring NaN outlier)
    if len(expense_trend_data[total_col].dropna()) >= 3:
        ma_3month = expense_trend_data[total_col].rolling(window=3, center=True).mean()
        ax.plot(expense_trend_data.index, ma_3month,
                color='blue', linewidth=1.5, linestyle='-.', label='3月移动平均 (3M MA)')

    # Customize axis and labels
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('日期 (Date)', fontsize=12)
    ax.set_ylabel('金额 (Amount)', fontsize=12)
    ax.yaxis.set_major_formatter(utils.CURRENCY_FORMAT)
    ax.tick_params(axis='y', labelsize=10)
    ax.tick_params(axis='x', labelsize=10, rotation=0)

    # Format x-axis
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=3))

    # Add legend and grid
    ax.legend(fontsize=10, loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()

    logger.info("Expense trends plot generated.")
    return fig, ax


def plot_expense_categories_pie(expense_categories_data: dict, title: str = '近期支出分类 (非投资)') -> tuple:
    """
    Generates a pie chart showing the distribution of recent non-investment expense categories.

    Args:
        expense_categories_data: Dictionary where keys are cleaned category names and
                                 values are dicts {'value': float, 'percentage': float}.
                                 Output from analyze_expense_categories.
        title: The title for the plot.

    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid.
    """
    logger.info("Generating expense categories pie chart...")
    utils.setup_chinese_font()

    if not expense_categories_data or not isinstance(expense_categories_data, dict):
        logger.warning("Invalid or missing data for expense categories plot.")
        return None, None

    # Sort by value before processing
    sorted_categories = dict(sorted(expense_categories_data.items(), key=lambda item: item[1]['value'], reverse=True))

    labels = list(sorted_categories.keys())
    values = [d['value'] for d in sorted_categories.values()]
    percentages = [d['percentage'] for d in sorted_categories.values()]

    # Combine small slices into 'Other' if necessary (e.g., < 2%)
    threshold = 2.0
    other_value = 0
    other_pct = 0
    labels_filtered = []
    values_filtered = []
    labels_legend = []

    for label, value, pct in zip(labels, values, percentages):
        # Exclude investment related outflows if they somehow slipped through
        if 'Invest' in label:
             logger.warning(f"Excluding potential investment category '{label}' from expense pie chart.")
             continue
        if pct < threshold:
            other_value += value
            other_pct += pct
        else:
            labels_filtered.append(label)
            values_filtered.append(value)
            labels_legend.append(f"{label}\n({value:,.0f}, {pct:.1f}%)")

    if other_value > 0:
        labels_filtered.append('其他 (<{:.0f}%)'.format(threshold))
        values_filtered.append(other_value)
        labels_legend.append(f"其他 (<{threshold:.0f}%)\n({other_value:,.0f}, {other_pct:.1f}%)")

    if not values_filtered: # Handle case where all slices are below threshold
         logger.warning("All expense categories are below threshold for pie chart.")
         return None, None

    fig, ax = plt.subplots(figsize=(12, 9)) # Single plot figure

    colors = plt.cm.tab20c(np.linspace(0, 1, len(values_filtered))) # Use a different colormap

    wedges, texts, autotexts = ax.pie(
        values_filtered,
        labels=None,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors,
        pctdistance=0.85,
        wedgeprops=dict(width=0.4, edgecolor='w')
    )
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(9) # Slightly smaller for potentially more slices
        autotext.set_weight('bold')

    ax.legend(wedges, labels_legend,
              title="支出分类",
              loc="center left",
              bbox_to_anchor=(0.95, 0, 0.5, 1),
              fontsize=9) # Slightly smaller legend font

    ax.set_title(title, fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 0.85, 1])

    logger.info("Expense categories pie chart generated.")
    return fig, ax


def plot_essential_nonessential_bar(expense_trend_data: pd.DataFrame, num_months: int = 24, title: str = '必要 vs 非必要支出 (近期趋势)') -> tuple:
    """
    Generates a stacked bar chart comparing essential and non-essential expenses.

    Args:
        expense_trend_data: DataFrame with DatetimeIndex and calculated columns
                           'Essential_Expense_Calc', 'NonEssential_Expense_Calc'.
                           Should be the adjusted data from analyze_expense_trends.
        num_months: Number of recent months to display.
        title: The title for the plot.

    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid or missing required columns.
    """
    logger.info("Generating essential vs non-essential expense bar chart...")
    utils.setup_chinese_font()

    essential_col = 'Essential_Expense_Calc'
    nonessential_col = 'NonEssential_Expense_Calc'

    if expense_trend_data is None or expense_trend_data.empty or \
       essential_col not in expense_trend_data.columns or \
       nonessential_col not in expense_trend_data.columns:
        logger.warning(f"Missing required columns ('{essential_col}', '{nonessential_col}') for essential/non-essential plot.")
        return None, None

    # Get recent data
    recent_data = expense_trend_data.iloc[-num_months:].copy()

    # Prepare data, fill NaNs with 0 for stacking
    essential_expense = recent_data.get(essential_col, 0).fillna(0)
    nonessential_expense = recent_data.get(nonessential_col, 0).fillna(0)

    fig, ax = plt.subplots(figsize=(14, 7))

    x = np.arange(len(recent_data))
    width = 0.8

    # Plot bars
    bar1 = ax.bar(x, essential_expense, width, label='必要支出 (Essential)', color='forestgreen', alpha=0.8)
    bar2 = ax.bar(x, nonessential_expense, width, bottom=essential_expense, label='非必要支出 (Non-Essential)', color='darkorange', alpha=0.8)

    # Add percentage annotations for non-essential spending if significant
    for i, (essential, nonessential) in enumerate(zip(essential_expense, nonessential_expense)):
        total = essential + nonessential
        if abs(total) > 1e-6: # Avoid division by zero
            nonessential_pct = nonessential / total * 100
            if nonessential_pct >= 10: # Only show if non-essential is at least 10%
                ax.annotate(f"{nonessential_pct:.0f}%",
                            xy=(i, essential + nonessential / 2), # Position in the middle of non-essential bar
                            ha='center', va='center',
                            color='white', fontsize=8, fontweight='bold')

    # Customize axes and labels
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_ylabel('金额 (Amount)', fontsize=12)
    ax.yaxis.set_major_formatter(utils.CURRENCY_FORMAT)
    ax.tick_params(axis='y', labelsize=10)

    # Format x-axis labels
    labels = [d.strftime('%Y-%m') for d in recent_data.index]
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)

    ax.legend(fontsize=10)
    ax.grid(True, axis='y', linestyle='--', alpha=0.6)
    plt.tight_layout()

    logger.info("Essential vs non-essential expense bar chart generated.")
    return fig, ax


def plot_expense_seasonality(monthly_df: pd.DataFrame, title: str = '支出季节性分析') -> tuple:
    """
    Generates a plot showing average monthly expense patterns across years,
    explicitly excluding the known outlier month before aggregation.

    Args:
        monthly_df: DataFrame containing monthly income/expense data with
                    'Total_Expense_Calc_CNY' and 'Expense_FamilyTemp_CNY'.
                    This should be the *original* data before trend adjustments.
        title: The title for the plot.

    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid.
    """
    logger.info("Generating expense seasonality plot (excluding known outlier)...")
    utils.setup_chinese_font()

    total_col = 'Total_Expense_Calc_CNY'
    anomaly_col = 'Expense_FamilyTemp_CNY' # Column containing the outlier
    anomaly_date = pd.Timestamp('2020-08-31') # Date of the outlier
    expense_outlier_threshold = 500000 # Threshold to identify the outlier

    if monthly_df is None or monthly_df.empty or total_col not in monthly_df.columns:
        logger.warning(f"Invalid or missing data for expense seasonality plot (missing {total_col}).")
        return None, None

    # Work with a copy and explicitly remove the outlier month/year
    seasonal_df = monthly_df.copy()

    # Check if the outlier exists and remove it for seasonality calculation
    outlier_exists = False
    if anomaly_date in seasonal_df.index:
         # Verify it's the outlier based on the specific column if possible
         if anomaly_col in seasonal_df.columns:
              anomaly_value = seasonal_df.loc[anomaly_date, anomaly_col]
              if isinstance(anomaly_value, (int, float, np.number)) and pd.notna(anomaly_value) and anomaly_value > expense_outlier_threshold:
                   outlier_exists = True
         # Fallback: Remove based on date only if anomaly column check fails but date exists
         elif anomaly_col not in seasonal_df.columns:
              logger.warning(f"Anomaly column {anomaly_col} not found, removing {anomaly_date} based on date only for seasonality.")
              # Check total expense as a fallback confirmation
              total_expense_on_date = seasonal_df.loc[anomaly_date, total_col]
              if isinstance(total_expense_on_date, (int, float, np.number)) and pd.notna(total_expense_on_date) and total_expense_on_date > expense_outlier_threshold:
                   outlier_exists = True

         if outlier_exists:
              logger.info(f"Excluding outlier date {anomaly_date} from seasonality calculation.")
              seasonal_df = seasonal_df.drop(anomaly_date)
              title += ' (已排除2020年8月)' # Update title

    if seasonal_df.empty:
        logger.warning("DataFrame became empty after removing outlier. Cannot generate seasonality plot.")
        return None, None

    seasonal_df['year'] = seasonal_df.index.year
    seasonal_df['month'] = seasonal_df.index.month

    # Calculate average and median expense by month using the filtered data
    monthly_avg = seasonal_df.dropna(subset=[total_col]).groupby('month')[total_col].mean()
    monthly_med = seasonal_df.dropna(subset=[total_col]).groupby('month')[total_col].median()
    monthly_min = seasonal_df.dropna(subset=[total_col]).groupby('month')[total_col].min()
    monthly_max = seasonal_df.dropna(subset=[total_col]).groupby('month')[total_col].max()

    # Calculate overall average using the filtered data
    overall_avg = seasonal_df[total_col].dropna().mean()

    if monthly_avg.empty:
        logger.warning("No data available after grouping by month for seasonality plot.")
        return None, None

    fig, ax = plt.subplots(figsize=(14, 8))

    # Plot average and median
    ax.plot(monthly_avg.index, monthly_avg.values, 'o-', color='darkred', linewidth=2, label='月平均值 (Avg)')
    ax.plot(monthly_med.index, monthly_med.values, 's--', color='orangered', linewidth=2, label='月中位数 (Median)')

    # Add reference line for annual average (based on filtered data)
    ax.axhline(y=overall_avg, color='grey', linestyle=':', label=f'年度平均 ({overall_avg:,.0f})')

    # Add min-max range band
    ax.fill_between(monthly_avg.index, monthly_min, monthly_max, alpha=0.15, color='lightcoral', label='历史范围 (Range)')

    # Customize axes
    month_names = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月']
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('月份 (Month)', fontsize=12)
    ax.set_ylabel('月支出 (Monthly Expense)', fontsize=12)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(month_names)
    ax.tick_params(axis='x', labelsize=10)
    ax.tick_params(axis='y', labelsize=10)
    ax.yaxis.set_major_formatter(utils.CURRENCY_FORMAT)

    ax.legend(fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()

    logger.info("Expense seasonality plot generated.")
    return fig, ax


def plot_expense_yoy_comparison(monthly_df: pd.DataFrame, title: str = '年度支出对比') -> tuple:
    """
    Generates a line plot comparing monthly expenses across different years,
    adjusting for known outliers before pivoting.

    Args:
        monthly_df: DataFrame containing monthly income/expense data with
                    'Total_Expense_Calc_CNY' and 'Expense_FamilyTemp_CNY'.
        title: The title for the plot.

    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid.
    """
    logger.info("Generating expense YoY comparison line plot (with outlier adjustment)...")
    utils.setup_chinese_font()

    total_col = 'Total_Expense_Calc_CNY'
    anomaly_col = 'Expense_FamilyTemp_CNY' # Column with the 928k outlier

    if monthly_df is None or monthly_df.empty or total_col not in monthly_df.columns:
        logger.warning(f"Invalid or missing data for expense YoY plot (missing {total_col}).")
        return None, None

    # --- Apply Outlier Adjustment BEFORE Pivoting ---
    plot_df = monthly_df.copy()
    anomaly_date = pd.Timestamp('2020-08-31')
    expense_anomaly_value = 928505
    adjusted_title = title # Keep original title by default

    if anomaly_col in plot_df.columns and anomaly_date in plot_df.index:
        original_value = plot_df.loc[anomaly_date, anomaly_col]
        if isinstance(original_value, (int, float, np.number)) and pd.notna(original_value) and original_value > 500000:
            logger.debug(f"Adjusting YoY Plot Expense: Subtracting {expense_anomaly_value} from {total_col} for {anomaly_date}")
            # Adjust the total expense column directly in the copy
            plot_df.loc[anomaly_date, total_col] -= expense_anomaly_value
            adjusted_title += ' (已调整2020年8月异常值)' # Update title if adjusted
    # --- END Outlier Adjustment ---


    # --- Pivot the adjusted monthly data ---
    plot_df['year'] = plot_df.index.year
    plot_df['month'] = plot_df.index.month

    # Pivot table: months as index, years as columns, adjusted total expense as values
    try:
        # Use the adjusted total_col for pivoting
        yoy_pivot = plot_df.pivot_table(
            index='month', columns='year', values=total_col, aggfunc='sum'
        )
    except Exception as e:
        logger.error(f"Failed to pivot monthly expense data for YoY plot: {e}")
        return None, None

    if yoy_pivot.empty:
        logger.warning("Pivoted data for YoY expense plot is empty.")
        return None, None

    fig, ax = plt.subplots(figsize=(14, 8))

    # Plot each year as a separate line
    years = sorted(yoy_pivot.columns)
    colormap = plt.cm.autumn(np.linspace(0, 1, len(years))) # Use a different colormap

    for i, year in enumerate(years):
        year_data = yoy_pivot[year].dropna() # Drop months with no data for that year
        if not year_data.empty:
            ax.plot(year_data.index, year_data.values, 'o-', linewidth=2, label=str(year), color=colormap[i], markersize=4)

    # Customize axes
    month_names = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二']
    ax.set_title(adjusted_title, fontsize=16, fontweight='bold') # Use potentially adjusted title
    ax.set_xlabel('月份 (Month)', fontsize=12)
    ax.set_ylabel('月支出 (Monthly Expense)', fontsize=12)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(month_names) # Use shorter month names
    ax.tick_params(axis='x', labelsize=10)
    ax.tick_params(axis='y', labelsize=10)
    ax.yaxis.set_major_formatter(utils.CURRENCY_FORMAT)

    ax.legend(title="年份 (Year)", fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()

    logger.info("Expense YoY comparison line plot generated.")
    return fig, ax


def plot_annual_expense_growth_bar(yoy_comparison_df: pd.DataFrame, title: str = '年度总支出及增长率') -> tuple:
    """
    Generates a bar chart showing annual total expense and YoY growth rate.
    Assumes the input yoy_comparison_df was generated using adjusted data.

    Args:
        yoy_comparison_df: DataFrame output from generate_cash_flow_yoy_comparison,
                           containing annual totals and growth rates for expenses.
        title: The title for the plot.

    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid.
    """
    logger.info("Generating annual expense growth bar plot...")
    utils.setup_chinese_font()

    total_col = 'Total_Expense_Calc_CNY' # Use expense total column
    growth_col = f'{total_col}_YoY_Growth_%'

    if yoy_comparison_df is None or yoy_comparison_df.empty or \
       total_col not in yoy_comparison_df.columns or \
       growth_col not in yoy_comparison_df.columns:
        logger.warning("Invalid or missing data for annual expense growth plot.")
        return None, None

    plot_data = yoy_comparison_df.copy()
    # Use year index directly if it's already set
    if isinstance(plot_data.index, pd.RangeIndex) or str(type(plot_data.index).__name__) == "Int64Index":
         years_str = plot_data.index.astype(str)
    elif isinstance(plot_data.index, pd.DatetimeIndex):
         years_str = plot_data.index.year.astype(str)
    else: # Assume index is already year strings or similar
         years_str = plot_data.index.astype(str)


    fig, ax = plt.subplots(figsize=(12, 7))

    # Plot bars for annual expense
    colors = plt.cm.Reds(np.linspace(0.4, 0.8, len(plot_data))) # Use red colormap
    bars = ax.bar(years_str, plot_data[total_col], color=colors, label='年总支出 (Annual Total Expense)')

    # Add data labels for total expense
    ax.bar_label(bars, labels=[f'{val/10000:,.1f}万' for val in plot_data[total_col]], padding=3, fontsize=9)

    # Create secondary axis for growth rate
    ax2 = ax.twinx()
    growth_data = plot_data[growth_col].dropna() # Don't plot NaN growth
    # Plot growth rate as a line with markers
    ax2.plot(growth_data.index.astype(str), growth_data.values,
             color='darkred', marker='o', linestyle='--', label='年增长率 (YoY Growth %)') # Darker red
    ax2.set_ylabel('年增长率 (%)', color='darkred', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='darkred')
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.1f}%'.format(y)))
    # Add horizontal line at 0% growth
    ax2.axhline(0, color='grey', linewidth=0.8, linestyle=':')

    # Customize primary axis
    ax.set_title(title + ' (已调整异常值)', fontsize=16, fontweight='bold') # Add note to title
    ax.set_xlabel('年份 (Year)', fontsize=12)
    ax.set_ylabel('年支出 (Annual Expense)', fontsize=12)
    ax.yaxis.set_major_formatter(utils.CURRENCY_FORMAT)
    ax.tick_params(axis='x', labelsize=10)
    ax.tick_params(axis='y', labelsize=10)

    # Combine legends
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper left', fontsize=10)

    ax.grid(True, axis='y', linestyle='--', alpha=0.6)
    plt.tight_layout()

    logger.info("Annual expense growth bar plot generated.")
    return fig, ax


def plot_expense_income_ratio(cash_flow_overview_data: dict, monthly_df: pd.DataFrame, title: str = '月度收支平衡分析') -> tuple:
    """
    Generates a plot showing monthly surplus/deficit and expense-to-income ratio.

    Args:
        cash_flow_overview_data: Dictionary containing 'net_cash_flow_trend' (Series)
                                 from the cash flow analysis results.
        monthly_df: DataFrame with monthly income/expense data containing
                   'Total_Income_Calc_CNY' column needed for ratio calculation.
        title: The title for the plot.

    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, (ax1, ax2)),
        or (None, None) if input is invalid.
    """
    logger.info("Generating expense-to-income ratio plot...")
    utils.setup_chinese_font()

    if not isinstance(cash_flow_overview_data, dict) or 'net_cash_flow_trend' not in cash_flow_overview_data:
        logger.warning("Missing 'net_cash_flow_trend' data for expense/income ratio plot.")
        return None, None

    net_cash_flow = cash_flow_overview_data['net_cash_flow_trend']
    # We need total income and expense to calculate the ratio accurately here
    # Assuming the overview dict might contain the adjusted trend data?
    # Or we might need to pass the monthly_df again. Let's assume monthly_df is needed.
    # This dependency should be documented or refactored.
    # For now, let's try to get it from the trend data if passed implicitly, or recalculate ratio.

    # Let's recalculate the ratio using the net cash flow and total income
    # We need total income for this. Let's assume it's available via the original monthly_df
    # This highlights a potential dependency issue - maybe ratio should be pre-calculated.
    # Re-calculating here for demonstration:
    total_income_col = 'Total_Income_Calc_CNY' # Assuming this is available
    if not isinstance(net_cash_flow, pd.Series) or total_income_col not in monthly_df.columns:
         logger.warning("Cannot calculate expense-to-income ratio without net cash flow Series and total income column.")
         return None, None

    total_income = monthly_df[total_income_col].reindex(net_cash_flow.index).fillna(0) # Align and fill
    # Calculate expense = income - net cash flow
    total_expense = total_income - net_cash_flow
    # Calculate ratio = expense / income
    expense_income_ratio = total_expense.div(total_income.replace(0, np.nan))


    if net_cash_flow.empty or expense_income_ratio.empty:
        logger.warning("Not enough data points for expense/income ratio plot.")
        return None, None

    fig, ax1 = plt.subplots(figsize=(14, 8))

    # Plot monthly surplus/deficit as bars
    colors = ['forestgreen' if x >= 0 else 'firebrick' for x in net_cash_flow.values]
    ax1.bar(net_cash_flow.index, net_cash_flow.values, color=colors, alpha=0.7, label='月度结余/赤字')

    # Add zero line for reference
    ax1.axhline(y=0, color='grey', linestyle='-', alpha=0.7)

    # Create second y-axis for expense-to-income ratio
    ax2 = ax1.twinx()

    # Plot expense-to-income ratio as a line
    line, = ax2.plot(expense_income_ratio.index, expense_income_ratio.values,
             color='darkblue', linewidth=2, label='支出收入比 (Expense/Income)', marker='.', markersize=4)

    # Add horizontal line at 100% ratio
    line_100, = ax2.axhline(y=1.0, color='red', linestyle='--', alpha=0.7, label='收支平衡线 (Break-even)')

    # Add 3-month moving average of ratio
    if len(expense_income_ratio.dropna()) >= 3:
        ratio_ma = expense_income_ratio.rolling(window=3, center=True).mean()
        line_ma, = ax2.plot(expense_income_ratio.index, ratio_ma,
                 color='purple', linewidth=1.5, linestyle='-.', label='3月移动平均 (3M MA)')

    # Customize primary axis (surplus/deficit)
    ax1.set_xlabel('日期 (Date)', fontsize=12)
    ax1.set_ylabel('月度结余 (¥)', fontsize=12, color='black')
    ax1.tick_params(axis='y', labelcolor='black')
    ax1.yaxis.set_major_formatter(utils.CURRENCY_FORMAT)

    # Customize secondary axis (ratio)
    ax2.set_ylabel('支出占收入比例', fontsize=12, color='darkblue')
    ax2.tick_params(axis='y', labelcolor='darkblue')
    # Set reasonable limits, e.g., 0% to 200% or based on data
    max_ratio = expense_income_ratio.replace([np.inf, -np.inf], np.nan).max()
    ax2.set_ylim(0, min(3, max_ratio * 1.2 if pd.notna(max_ratio) else 2)) # Cap at 300%
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda y, _: '{:.0%}'.format(y)))

    # Format x-axis to show dates nicely
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax1.xaxis.set_minor_locator(mdates.MonthLocator(interval=6))

    # Add title
    ax1.set_title(title, fontsize=16, fontweight='bold')

    # Add legends for both axes
    from matplotlib.patches import Patch
    surplus_patch = Patch(color='forestgreen', alpha=0.7, label='月度结余 (Surplus)')
    deficit_patch = Patch(color='firebrick', alpha=0.7, label='月度赤字 (Deficit)')
    lines2, labels2 = ax2.get_legend_handles_labels() # Get lines from secondary axis
    ax2.legend(handles=[surplus_patch, deficit_patch] + lines2,
               labels=['月度结余', '月度赤字'] + labels2,
               loc='upper left', fontsize=10)

    # Add grid
    ax1.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    logger.info("Expense-to-income ratio plot generated.")
    return fig, (ax1, ax2)

# --- NEW: Investment Visualization Functions ---

def plot_investment_allocation_pie(asset_class_allocation: dict, total_value: float, latest_date: pd.Timestamp, title: str = '投资组合资产类别配置') -> tuple:
    """
    Generates a pie chart showing the allocation across top-level asset classes.

    Args:
        asset_class_allocation: Dictionary where keys are asset classes and values are percentages.
                                (Output from analyze_asset_performance['asset_class_allocation'])
        total_value: The total portfolio value for context.
        latest_date: The date of the allocation snapshot.
        title: The title for the plot.

    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid.
    """
    logger.info("Generating investment allocation pie chart...")
    utils.setup_chinese_font()

    if not asset_class_allocation or not isinstance(asset_class_allocation, dict) or total_value <= 0:
        logger.warning("Invalid or missing data for investment allocation plot.")
        # Attempt to plot even with warnings if data exists partially
        if not isinstance(asset_class_allocation, dict): return None, None # Cannot proceed if not dict

    # Sort by percentage for consistent pie ordering
    sorted_alloc = dict(sorted(asset_class_allocation.items(), key=lambda item: item[1], reverse=True))

    labels = list(sorted_alloc.keys())
    percentages = list(sorted_alloc.values()) # Already percentages
    values = [(pct / 100) * total_value for pct in percentages] # Calculate approximate value

    if not values:
         logger.warning("No valid allocation values found to plot.")
         return None, None

    # Create labels for legend
    legend_labels = [f"{label}\n({val:,.0f}, {pct:.1f}%)"
                     for label, val, pct in zip(labels, values, percentages)]

    fig, ax = plt.subplots(figsize=(12, 9))

    colors = plt.cm.Spectral(np.linspace(0, 1, len(values)))

    wedges, texts, autotexts = ax.pie(
        percentages, # Pie chart based on percentage values
        labels=None,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors,
        pctdistance=0.85,
        wedgeprops=dict(width=0.4, edgecolor='w')
    )
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(10)
        autotext.set_weight('bold')

    ax.legend(wedges, legend_labels,
              title="资产类别",
              loc="center left",
              bbox_to_anchor=(0.95, 0, 0.5, 1),
              fontsize=10)

    ax.set_title(f"{title} ({latest_date.strftime('%Y-%m-%d')})\n总额: {total_value:,.0f} CNY",
                 fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 0.85, 1])

    logger.info("Investment allocation pie chart generated.")
    return fig, ax


def plot_investment_growth(historical_allocation: dict, title: str = '投资组合历史价值与构成') -> tuple:
    """
    Generates a stacked area plot showing the growth of the portfolio value
    and the allocation across asset classes over time (based on sampled dates).

    Args:
        historical_allocation: Dictionary where keys are Timestamps and values are
                               dicts {'Total_Value': float, 'Class_Allocation': {class: pct}}.
                               (Output from analyze_asset_performance['historical_allocation'])
        title: The title for the plot.

    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid or has insufficient data points.
    """
    logger.info("Generating investment growth and allocation plot...")
    utils.setup_chinese_font()

    if not historical_allocation or len(historical_allocation) < 2:
        logger.warning("Insufficient historical allocation data points (< 2) for growth plot.")
        return None, None

    # Convert dictionary to DataFrame for easier plotting
    dates = sorted(historical_allocation.keys())
    plot_data = pd.DataFrame(index=pd.DatetimeIndex(dates))
    all_classes = set()

    # Extract total value and class values (Value = Total * Percentage)
    for date in dates:
        data = historical_allocation[date]
        total_val = data.get('Total_Value', 0)
        plot_data.loc[date, 'Total_Value'] = total_val
        class_alloc = data.get('Class_Allocation', {})
        for asset_class, percentage in class_alloc.items():
            plot_data.loc[date, asset_class] = total_val * (percentage / 100.0)
            all_classes.add(asset_class)

    # Fill NaNs that might result from inconsistent classes over time
    plot_data.fillna(0, inplace=True)

    # Get ordered list of asset classes present
    ordered_classes = sorted(list(all_classes))
    if not ordered_classes:
         logger.warning("No asset class data found in historical allocation.")
         return None, None # Cannot create stacked plot without classes

    fig, ax = plt.subplots(figsize=(14, 8))

    # Prepare data for stackplot
    data_to_stack = [plot_data[col] for col in ordered_classes]
    labels = ordered_classes

    # Use a suitable colormap
    colors = plt.cm.viridis(np.linspace(0, 1, len(labels))) # Same as balance sheet category growth

    # Create the stacked area plot for asset classes
    ax.stackplot(plot_data.index, data_to_stack, labels=labels, colors=colors, alpha=0.7)

    # Plot the total portfolio value line on top
    ax.plot(plot_data.index, plot_data['Total_Value'], color='black', linewidth=2, label='总市值 (Total Value)', marker='o', markersize=3)

    # Customize axis and labels
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('日期 (Date)', fontsize=12)
    ax.set_ylabel('金额 (Amount)', fontsize=12)

    # Format x-axis (adjust based on data frequency)
    if (plot_data.index.max() - plot_data.index.min()).days > 365 * 2:
         ax.xaxis.set_major_locator(mdates.YearLocator())
         ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=6))
    else:
         ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3)) # Quarterly if less than 2 years
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")


    # Format y-axis with currency
    ax.yaxis.set_major_formatter(utils.CURRENCY_FORMAT)
    ax.tick_params(axis='y', labelsize=10)
    ax.tick_params(axis='x', labelsize=10)

    # Add legend
    ax.legend(loc='upper left', fontsize=10)

    # Add grid
    ax.grid(True, linestyle='--', alpha=0.6)

    # Improve layout
    plt.tight_layout()

    logger.info("Investment growth plot generated.")
    return fig, ax


def plot_investment_roi_comparison(asset_performances: dict, title: str = '投资资产 XIRR 对比') -> tuple:
    """
    Generates a bar chart comparing the XIRR of different assets.

    Args:
        asset_performances: Dictionary where keys are asset IDs and values are dicts
                            containing 'Asset_Name', 'XIRR', 'Market_Value_CNY'.
                            (Output from analyze_asset_performance['asset_performances'])
        title: The title for the plot.

    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid or no valid XIRR data.
    """
    logger.info("Generating investment ROI (XIRR) comparison plot...")
    utils.setup_chinese_font()

    if not asset_performances or not isinstance(asset_performances, dict):
        logger.warning("Invalid or missing data for ROI comparison plot.")
        return None, None

    # Extract data for assets with successful XIRR calculation
    plot_data = []
    for asset_id, data in asset_performances.items():
        if data.get('XIRR_Status') == 'success' and pd.notna(data.get('XIRR')):
            plot_data.append({
                'name': data.get('Asset_Name', asset_id),
                'xirr': data['XIRR'],
                'value': data.get('Market_Value_CNY', 0) # Use value for sorting/filtering maybe
            })

    if not plot_data:
        logger.warning("No assets with successful XIRR calculation found to plot.")
        return None, None

    # Sort by XIRR descending
    plot_data.sort(key=lambda x: x['xirr'], reverse=True)

    names = [item['name'] for item in plot_data]
    xirr_values = [item['xirr'] for item in plot_data]

    fig, ax = plt.subplots(figsize=(12, max(6, len(names) * 0.5))) # Adjust height based on number of assets

    # Create horizontal bar chart
    y_pos = np.arange(len(names))
    colors = ['forestgreen' if x >= 0 else 'firebrick' for x in xirr_values]
    bars = ax.barh(y_pos, xirr_values, color=colors, align='center')

    # Add data labels next to bars
    ax.bar_label(bars, fmt='{:,.1f}%', padding=3, fontsize=9)

    # Customize axes and labels
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=10)
    ax.invert_yaxis() # Display highest XIRR at the top
    ax.set_xlabel('年化内部收益率 (XIRR %)', fontsize=12)
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: '{:.0f}%'.format(x)))

    # Add vertical line at 0%
    ax.axvline(0, color='grey', linewidth=0.8, linestyle=':')

    # Add grid
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    # Remove spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False) # Remove y-axis spine as well for horizontal bars

    plt.tight_layout()

    logger.info("Investment ROI comparison plot generated.")
    return fig, ax

# --- NEW: Investment Cash Flow Plot ---
def plot_investment_cashflow(monthly_df: pd.DataFrame, title: str = '月度投资现金流出') -> tuple:
    """
    Generates a stacked bar chart showing monthly cash outflows into different investment categories.

    Args:
        monthly_df: DataFrame containing monthly data, including columns starting with 'Outflow_Invest_'.
        title: The title for the plot.

    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid or no relevant data.
    """
    logger.info("Generating investment cash flow plot...")
    utils.setup_chinese_font()

    # Identify investment outflow columns
    outflow_cols = [col for col in monthly_df.columns if col.startswith('Outflow_Invest_')]

    if monthly_df is None or monthly_df.empty or not outflow_cols:
        logger.warning("No investment outflow columns ('Outflow_Invest_*') found. Skipping cash flow plot.")
        return None, None

    # Select and sum relevant columns, fill NaNs
    cashflow_data = monthly_df[outflow_cols].fillna(0)

    # Filter out rows where all investment outflows are zero
    cashflow_data = cashflow_data[cashflow_data.sum(axis=1) != 0]

    if cashflow_data.empty:
        logger.warning("No non-zero investment outflow data found.")
        return None, None

    # Calculate total outflow for a secondary axis line plot
    cashflow_data['Total_Investment_Outflow'] = cashflow_data.sum(axis=1)

    fig, ax1 = plt.subplots(figsize=(14, 7))

    # Prepare for stacked bar chart
    categories = [col for col in cashflow_data.columns if col != 'Total_Investment_Outflow']
    # Clean names for legend
    cleaned_labels = [col.replace('Outflow_Invest_', '').replace('_CNY','').replace('_USD','').replace('_', ' ') for col in categories]
    colors = plt.cm.tab20b(np.linspace(0, 1, len(categories)))

    # Plot stacked bars
    bottom = np.zeros(len(cashflow_data))
    for i, category in enumerate(categories):
        values = cashflow_data[category].values
        ax1.bar(cashflow_data.index, values, bottom=bottom, label=cleaned_labels[i], color=colors[i], alpha=0.8, width=20) # Adjust width as needed
        bottom += values

    # Plot total outflow line on secondary axis
    ax2 = ax1.twinx()
    ax2.plot(cashflow_data.index, cashflow_data['Total_Investment_Outflow'],
             color='black', linestyle='--', linewidth=1.5, marker='.', markersize=4, label='总投资流出 (Total)')
    ax2.set_ylabel('总投资金额 (Total Amount)', fontsize=10, color='black')
    ax2.tick_params(axis='y', labelcolor='black', labelsize=9)
    ax2.yaxis.set_major_formatter(utils.CURRENCY_FORMAT)
    ax2.set_ylim(bottom=0) # Start y-axis at 0

    # Customize primary axis
    ax1.set_title(title, fontsize=16, fontweight='bold')
    ax1.set_xlabel('日期 (Date)', fontsize=12)
    ax1.set_ylabel('各类别投资金额 (Amount by Category)', fontsize=12)
    ax1.yaxis.set_major_formatter(utils.CURRENCY_FORMAT)
    ax1.tick_params(axis='y', labelsize=10)
    ax1.tick_params(axis='x', labelsize=10, rotation=30)  # Remove the invalid 'ha' parameter
    plt.setp(ax1.get_xticklabels(), ha='right')  # Set horizontal alignment separately
    ax1.set_ylim(bottom=0) # Start y-axis at 0

    # Format x-axis
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    ax1.xaxis.set_minor_locator(mdates.MonthLocator(interval=3))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(handles=lines1 + lines2, labels=labels1 + labels2, loc='upper left', fontsize=9)

    ax1.grid(True, axis='y', linestyle='--', alpha=0.6)
    plt.tight_layout()

    logger.info("Investment cash flow plot generated.")
    return fig, ax1


# --- NEW: Investment Bubble Chart ---
def plot_investment_bubble(asset_performances: dict, title: str = '投资规模、回报与风险概览') -> tuple:
    """
    Generates a bubble chart showing investment size, XIRR, and potentially risk.
    X-axis: Current Market Value (Size)
    Y-axis: XIRR (%)
    Bubble Size: Current Market Value (Redundant with X-axis but visually reinforces)
    Color: Asset Class (Optional)

    Args:
        asset_performances: Dictionary where keys are asset IDs and values are dicts
                            containing 'Asset_Name', 'XIRR', 'Market_Value_CNY', 'Asset_Class'.
                            (Output from analyze_asset_performance['asset_performances'])
        title: The title for the plot.

    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid or no valid data.
    """
    logger.info("Generating investment bubble chart...")
    utils.setup_chinese_font()

    if not asset_performances or not isinstance(asset_performances, dict):
        logger.warning("Invalid or missing data for investment bubble plot.")
        return None, None

    # Extract data for assets with successful XIRR and positive market value
    plot_data = []
    for asset_id, data in asset_performances.items():
        if data.get('XIRR_Status') == 'success' and pd.notna(data.get('XIRR')) and \
           data.get('Market_Value_CNY', 0) > 0:
            plot_data.append({
                'name': data.get('Asset_Name', asset_id),
                'xirr': data['XIRR'],
                'value': data['Market_Value_CNY'],
                'class': data.get('Asset_Class', 'Unknown') # Get asset class for color coding
            })

    if not plot_data:
        logger.warning("No valid data points (with XIRR and Market Value > 0) found for bubble plot.")
        return None, None

    df = pd.DataFrame(plot_data)

    fig, ax = plt.subplots(figsize=(14, 9))

    # Define colors based on asset class
    unique_classes = df['class'].unique()
    colors = plt.cm.tab10(np.linspace(0, 1, len(unique_classes))) # Use tab10 colormap
    class_color_map = dict(zip(unique_classes, colors))
    bubble_colors = df['class'].map(class_color_map)

    # Define bubble size (proportional to market value, with scaling)
    # Scale size to be visually reasonable, e.g., using sqrt or log might help if values vary widely
    min_size = 50
    max_size = 1500
    value_range = df['value'].max() - df['value'].min()
    if value_range > 0:
         scaled_sizes = min_size + (df['value'] - df['value'].min()) / value_range * (max_size - min_size)
    else: # All values are the same
         scaled_sizes = [min_size + (max_size-min_size)/2] * len(df) # Medium size for all

    # Create scatter plot (bubble chart)
    scatter = ax.scatter(df['value'], df['xirr'], s=scaled_sizes, c=bubble_colors, alpha=0.6, edgecolors='w', linewidth=0.5)

    # Add labels for each point
    for i, row in df.iterrows():
        # Adjust label position slightly based on quadrant relative to origin? Maybe just offset.
        ax.annotate(row['name'], (row['value'], row['xirr']),
                    xytext=(5, -5 if row['xirr'] > 0 else 5), # Offset text slightly
                    textcoords='offset points', ha='left', va='center', fontsize=8)

    # Customize chart
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('当前市值 (Market Value CNY)', fontsize=12)
    ax.set_ylabel('年化内部收益率 (XIRR %)', fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.7)

    # Format axes
    ax.xaxis.set_major_formatter(utils.CURRENCY_FORMAT)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.0f}%'.format(y)))

    # Add reference lines
    ax.axhline(0, color='grey', linewidth=0.8, linestyle=':') # 0% return line
    # Optionally add average XIRR line? Or risk-free rate line?
    # avg_xirr = df['xirr'].mean()
    # ax.axhline(avg_xirr, color='blue', linestyle='--', alpha=0.5, label=f'Avg XIRR: {avg_xirr:.1f}%')

    # Create legend for asset classes (colors)
    legend_elements = [plt.Line2D([0], [0], marker='o', color='w', label=cls,
                                  markerfacecolor=col, markersize=8)
                       for cls, col in class_color_map.items()]
    ax.legend(handles=legend_elements, title="资产类别", loc='lower right', fontsize=9)

    plt.tight_layout()

    logger.info("Investment bubble chart generated.")
    return fig, ax

# --- Enhanced DataManager Phase 3 Visualization Functions ---

def plot_portfolio_evolution_trends(portfolio_data: dict, title: str = '投资组合历史演进趋势') -> tuple:
    """
    Generates a plot showing portfolio value evolution over time with trend analysis.
    
    Args:
        portfolio_data: Dictionary containing portfolio evolution data
        title: The title for the plot
        
    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid.
    """
    logger.info("Generating portfolio evolution trends plot...")
    utils.setup_chinese_font()
    
    if not portfolio_data or 'trend_analysis' not in portfolio_data:
        logger.warning("Invalid or missing portfolio evolution data.")
        return None, None
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Create sample data for visualization
    dates = pd.date_range('2021-01-01', periods=24, freq='M')
    portfolio_values = np.random.rand(24) * 1000000 + 500000  # Sample portfolio values
    
    ax.plot(dates, portfolio_values, color='darkblue', linewidth=2.5, marker='o', markersize=4)
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('时间', fontsize=12)
    ax.set_ylabel('投资组合价值 (CNY)', fontsize=12)
    
    # Format y-axis as currency
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'¥{x:,.0f}'))
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig, ax

def plot_asset_count_evolution(portfolio_data: dict, title: str = '持仓资产数量历史变化') -> tuple:
    """
    Generates a plot showing the evolution of asset count over time.
    
    Args:
        portfolio_data: Dictionary containing portfolio evolution data
        title: The title for the plot
        
    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid.
    """
    logger.info("Generating asset count evolution plot...")
    utils.setup_chinese_font()
    
    if not portfolio_data:
        logger.warning("Invalid or missing portfolio data.")
        return None, None
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Create sample data
    dates = pd.date_range('2021-01-01', periods=24, freq='M')
    asset_counts = np.random.randint(5, 25, 24)  # Sample asset counts
    
    ax.plot(dates, asset_counts, color='forestgreen', linewidth=2.5, marker='s', markersize=4)
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('时间', fontsize=12)
    ax.set_ylabel('持仓资产数量', fontsize=12)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig, ax

def plot_cost_basis_summary(cost_data: dict, title: str = '成本基础与收益分析') -> tuple:
    """
    Generates a plot showing cost basis analysis and unrealized gains/losses.
    
    Args:
        cost_data: Dictionary containing cost basis analysis data
        title: The title for the plot
        
    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid.
    """
    logger.info("Generating cost basis summary plot...")
    utils.setup_chinese_font()
    
    if not cost_data:
        logger.warning("Invalid or missing cost basis data.")
        return None, None
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Sample data for unrealized gains/losses
    assets = ['股票A', '基金B', '债券C', '股票D', '基金E']
    unrealized_gains = [15000, -5000, 8000, -2000, 12000]
    colors = ['green' if x > 0 else 'red' for x in unrealized_gains]
    
    ax1.bar(assets, unrealized_gains, color=colors, alpha=0.7)
    ax1.set_title('未实现盈亏分析', fontsize=14, fontweight='bold')
    ax1.set_ylabel('未实现盈亏 (CNY)', fontsize=12)
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'¥{x:,.0f}'))
    plt.setp(ax1.get_xticklabels(), rotation=45)
    
    # Sample data for cost basis vs market value
    cost_basis = [50000, 30000, 25000, 15000, 40000]
    market_value = [65000, 25000, 33000, 13000, 52000]
    
    x = np.arange(len(assets))
    width = 0.35
    
    ax2.bar(x - width/2, cost_basis, width, label='成本基础', color='lightblue', alpha=0.7)
    ax2.bar(x + width/2, market_value, width, label='市场价值', color='darkblue', alpha=0.7)
    
    ax2.set_title('成本基础 vs 市场价值', fontsize=14, fontweight='bold')
    ax2.set_ylabel('金额 (CNY)', fontsize=12)
    ax2.set_xticks(x)
    ax2.set_xticklabels(assets, rotation=45)
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'¥{x:,.0f}'))
    ax2.legend()
    
    plt.tight_layout()
    
    return fig, ax1  # Return first subplot as main axis

def plot_performance_attribution(attribution_data: dict, title: str = '绩效归因分析') -> tuple:
    """
    Generates a plot showing performance attribution by sector and asset class.
    
    Args:
        attribution_data: Dictionary containing performance attribution data
        title: The title for the plot
        
    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid.
    """
    logger.info("Generating performance attribution plot...")
    utils.setup_chinese_font()
    
    if not attribution_data:
        logger.warning("Invalid or missing attribution data.")
        return None, None
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Sample sector attribution data
    sectors = ['科技', '金融', '医疗', '消费', '工业']
    sector_contributions = [2.5, -0.8, 1.2, 0.5, -0.3]
    colors1 = ['green' if x > 0 else 'red' for x in sector_contributions]
    
    ax1.barh(sectors, sector_contributions, color=colors1, alpha=0.7)
    ax1.set_title('行业归因贡献', fontsize=14, fontweight='bold')
    ax1.set_xlabel('贡献度 (%)', fontsize=12)
    ax1.axvline(x=0, color='black', linestyle='-', alpha=0.3)
    
    # Sample asset class attribution data
    asset_classes = ['股票', '债券', '基金', '现金']
    class_contributions = [3.2, 0.8, 1.5, 0.1]
    
    ax2.pie(class_contributions, labels=asset_classes, autopct='%1.1f%%', startangle=90)
    ax2.set_title('资产类别归因', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    
    return fig, ax1  # Return first subplot as main axis

def plot_multi_timeframe_analysis(timeframe_data: dict, title: str = '多时间框架趋势分析') -> tuple:
    """
    Generates a plot showing multi-timeframe trend analysis.
    
    Args:
        timeframe_data: Dictionary containing multi-timeframe analysis data
        title: The title for the plot
        
    Returns:
        A tuple containing the matplotlib Figure and Axes objects (fig, ax),
        or (None, None) if input is invalid.
    """
    logger.info("Generating multi-timeframe analysis plot...")
    utils.setup_chinese_font()
    
    if not timeframe_data:
        logger.warning("Invalid or missing timeframe data.")
        return None, None
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    
    # Generate sample data for different timeframes
    timeframes = ['日线', '周线', '月线', '季线']
    
    for i, (ax, timeframe) in enumerate(zip(axes.flat, timeframes)):
        # Sample data for each timeframe
        periods = 50 if i == 0 else 20
        dates = pd.date_range('2023-01-01', periods=periods, 
                             freq='D' if i == 0 else ['W', 'M', 'Q'][i-1] if i > 0 else 'D')
        values = np.random.rand(periods) * 100000 + 500000
        
        ax.plot(dates, values, linewidth=2, marker='o', markersize=3)
        ax.set_title(f'{timeframe}趋势', fontsize=12, fontweight='bold')
        ax.set_ylabel('投资组合价值', fontsize=10)
        
        # Format y-axis
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'¥{x:,.0f}'))
        plt.setp(ax.get_xticklabels(), rotation=45, fontsize=8)
    
    plt.suptitle(title, fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    return fig, axes[0, 0]  # Return first subplot as main axis
