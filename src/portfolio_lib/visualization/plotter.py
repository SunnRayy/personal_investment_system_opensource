# portfolio_lib/visualization/plotter.py
"""
Visualization module using Matplotlib and Seaborn.
Generates charts for portfolio analysis, handling non-rebalanceable assets
and preparing plots for reporting.
(Modified to return saved base filenames)
"""

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import matplotlib.font_manager as fm
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Patch # Added for custom legend in sub-category plot
from typing import Dict, Any, Optional, Tuple, List, Set
import os
import re # For sanitizing filenames

# --- Font Setup ---
_DEFAULT_CHINESE_FONTS = ['Heiti TC', 'PingFang TC', 'Songti TC', 'STHeiti', 'SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
_FALLBACK_FONT = 'sans-serif'
def _find_chinese_font(preferred_font: Optional[str] = None) -> str:
    """Finds an available Chinese font or falls back."""
    available_fonts = {f.name for f in fm.fontManager.ttflist}
    if preferred_font and preferred_font in available_fonts:
        print(f"Using specified Chinese font: {preferred_font}")
        return preferred_font
    for font in _DEFAULT_CHINESE_FONTS:
        if font in available_fonts:
            print(f"Using detected Chinese font: {font}")
            return font
    print(f"Warning: No suitable Chinese font found. Using fallback: {_FALLBACK_FONT}")
    return _FALLBACK_FONT

# --- Currency Formatter ---
# Define locally as utils might not be fully implemented/stable yet
def _currency_formatter(x, pos=None):
    """Basic currency formatter."""
    if pd.isna(x): return "N/A"
    try: num_x = float(x); abs_x = abs(num_x); sign = '-' if num_x < 0 else ''
    except (ValueError, TypeError): return str(x)
    if abs_x >= 1e6: return f'{sign}{abs_x/1e6:.1f}M'
    elif abs_x >= 1e3: return f'{sign}{abs_x/1e3:.1f}K'
    else: return f'{sign}{abs_x:,.0f}' # Use comma for thousands
_currency_format = FuncFormatter(_currency_formatter)

# --- Filename Sanitizer ---
def _sanitize_filename(name: str) -> str:
    """Removes potentially problematic characters from filenames."""
    name = name.replace(': ','_').replace(' ','_').replace('(','').replace(')','')
    name = re.sub(r'[^\w\-_\. ]', '_', name) # Keep word chars, hyphen, underscore, period, space
    return name.strip().lower() # Lowercase for consistency

class PortfolioVisualizer:
    """Generates various visualizations for portfolio analysis."""

    def __init__(self, settings: Optional[Dict[str, Any]] = None):
        """Initializes the visualizer and sets plotting styles."""
        vis_settings = settings.get('visualization', {}) if settings else {}
        general_settings = settings.get('general', {}) if settings else {}
        data_paths_settings = settings.get('data_paths', {}) if settings else {}

        self.font_name = _find_chinese_font(vis_settings.get('chinese_font'))
        try: plt.style.use('seaborn-v0_8-whitegrid')
        except OSError: print("Warning: 'seaborn-v0_8-whitegrid' style not found."); plt.style.use('default')
        plt.rcParams['font.family'] = self.font_name
        plt.rcParams['axes.unicode_minus'] = False
        self.default_figsize = tuple(vis_settings.get('figure_size', [12, 8]))
        self.color_palette = vis_settings.get('color_palette', 'tab10')
        self.show_values_on_charts = vis_settings.get('show_values_on_charts', True)
        self.save_charts = vis_settings.get('save_charts', False)
        self.chart_format = vis_settings.get('chart_format', 'png')
        self.chart_dpi = vis_settings.get('chart_dpi', 150)
        self.output_directory = data_paths_settings.get('output_directory', 'output')
        self.debug_mode = general_settings.get('debug_mode', False)
        self.currency_format = _currency_format

        print(f"PortfolioVisualizer Initialized: Font='{self.font_name}', SaveCharts={self.save_charts}, OutputDir='{self.output_directory}'")

    def _save_figure(self, fig: plt.Figure, filename_base: str) -> Optional[str]:
        """
        Saves the figure with a sanitized filename if enabled.

        Args:
            fig: The matplotlib Figure object to save.
            filename_base: The base name for the file (will be sanitized).

        Returns:
            The sanitized base filename (without extension) if saved successfully,
            otherwise None.
        """
        if self.save_charts:
            try:
                output_dir_path = self.output_directory
                # --- Path Calculation Logic (Ensure consistency with Cell 2) ---
                if not os.path.isabs(output_dir_path):
                     # Assumes notebook/script is run from project root ('Asset Allocation')
                     # Or adjust this logic based on your actual project structure and where you run the notebook
                     project_root = os.getcwd()
                     # Example: If notebook is IN personal_portfolio_analyzer, this might be wrong.
                     # Consider passing an absolute path or a path relative to a known root.
                     # For now, keeping original logic, but be aware of potential issues.
                     output_dir_path = os.path.join(project_root, 'personal_portfolio_analyzer', self.output_directory)

                os.makedirs(output_dir_path, exist_ok=True)
                safe_filename_base = _sanitize_filename(filename_base) # Sanitize base
                save_path = os.path.join(output_dir_path, f"{safe_filename_base}.{self.chart_format}")
                fig.savefig(save_path, dpi=self.chart_dpi, bbox_inches='tight')
                print(f"-> Chart saved: {save_path}")
                # --- RETURN THE SANITIZED BASE FILENAME ---
                return safe_filename_base
            except Exception as e:
                print(f"Error saving chart '{filename_base}': {e}")
                return None # Return None on error
        else:
            print(f"-> Chart NOT saved (save_charts=False): {filename_base}")
            return None # Return None if not saving

    def plot_allocation_comparison(
        self,
        current_alloc_pct: Dict[str, float],
        target_alloc: Dict[str, float],
        non_rebalanceable_classes: Optional[Set[str]] = None,
        title_prefix: str = "",
        figsize: Optional[Tuple[float, float]] = None,
        filename_suffix: str = ""
    ) -> Optional[Dict[str, Optional[str]]]:
        """
        Plots allocation comparison WITHIN the REBALANCEABLE portion.

        Args:
            current_alloc_pct: Dictionary of current allocation percentages.
            target_alloc: Dictionary of target allocation percentages.
            non_rebalanceable_classes: Set of asset classes to exclude.
            title_prefix: Prefix for the plot title.
            figsize: Figure size tuple.
            filename_suffix: Suffix to add to the base filenames.

        Returns:
            A dictionary mapping {'pie': base_filename, 'bar': base_filename}
            if charts are saved, otherwise None. Base filenames are sanitized
            and without extension. Values can be None if saving failed for a specific chart.
        """
        print(f"\nPlotting Allocation Comparison ({title_prefix.strip()})...")
        # (Keep filtering and rescaling logic as is - ID: plotter_py_rescale)
        fig_size = figsize or self.default_figsize
        if non_rebalanceable_classes is None: non_rebalanceable_classes = set()
        rebal_current_pct: Dict[str, float] = {}; rebal_target_pct: Dict[str, float] = {}
        total_rebal_pct_current = sum(v for k, v in current_alloc_pct.items() if k not in non_rebalanceable_classes)
        total_rebal_pct_target = sum(v for k, v in target_alloc.items() if k not in non_rebalanceable_classes)
        print(f"  - Total Rebalanceable % (Current): {total_rebal_pct_current:.1%}, (Target): {total_rebal_pct_target:.1%}")
        print(f"  - Excluding: {non_rebalanceable_classes or 'None'}")
        if total_rebal_pct_current > 1e-6:
            for cat, pct in current_alloc_pct.items():
                if cat not in non_rebalanceable_classes: rebal_current_pct[cat] = pct / total_rebal_pct_current
        if total_rebal_pct_target > 1e-6:
             for cat, pct in target_alloc.items():
                 if cat not in non_rebalanceable_classes: rebal_target_pct[cat] = pct / total_rebal_pct_target
        plot_categories = sorted(list(set(rebal_current_pct.keys()) | set(rebal_target_pct.keys())))
        if not plot_categories: print("Warning: No rebalanceable asset classes found to plot."); plt.close(); return None # Close figure and return
        current_pcts_rescaled = [rebal_current_pct.get(cat, 0.0) for cat in plot_categories]; target_pcts_rescaled = [rebal_target_pct.get(cat, 0.0) for cat in plot_categories]
        valid_indices = [i for i, (c, t) in enumerate(zip(current_pcts_rescaled, target_pcts_rescaled)) if c > 1e-6 or t > 1e-6]
        if not valid_indices: print("Warning: No significant rescaled allocations found."); plt.close(); return None # Close figure and return
        categories_to_plot = [plot_categories[i] for i in valid_indices]; current_pcts_to_plot = [current_pcts_rescaled[i] for i in valid_indices]; target_pcts_to_plot = [target_pcts_rescaled[i] for i in valid_indices]

        # --- Dictionary to store saved filenames ---
        saved_filenames: Dict[str, Optional[str]] = {'pie': None, 'bar': None}

        # --- Pie Chart ---
        sort_idx_pie = np.argsort(current_pcts_to_plot)[::-1]; categories_sorted_pie = [categories_to_plot[i] for i in sort_idx_pie]
        current_pcts_sorted_pie = [current_pcts_to_plot[i] for i in sort_idx_pie]; target_pcts_sorted_pie = [rebal_target_pct.get(cat, 0.0) for cat in categories_sorted_pie]
        try: num_colors = len(categories_sorted_pie); cmap = plt.get_cmap(self.color_palette); colors = cmap(np.linspace(0, 1, num_colors)) if num_colors > 0 else []
        except ValueError: print(f"Warning: Colormap '{self.color_palette}' not found. Using 'tab10'."); num_colors = len(categories_sorted_pie); colors = plt.get_cmap('tab10')(np.linspace(0, 1, num_colors)) if num_colors > 0 else []
        pie_figsize = (fig_size[0], fig_size[1] * 0.6) if len(categories_sorted_pie) > 5 else (fig_size[0]*0.8, fig_size[1]*0.5)
        fig_pie, (ax1, ax2) = plt.subplots(1, 2, figsize=pie_figsize, constrained_layout=True)
        fig_pie.suptitle(f'{title_prefix}可调整部分内部配置比较', fontsize=16, fontweight='bold')
        explode = [0.02] * len(categories_sorted_pie)
        wedges1, _, autotexts1 = ax1.pie(current_pcts_sorted_pie, explode=explode, labels=None, colors=colors, autopct='%1.1f%%' if self.show_values_on_charts else None, shadow=True, startangle=90, wedgeprops={'edgecolor': 'white', 'linewidth': 0.8}, pctdistance=0.85)
        ax1.set_title('当前配置 (Current)', fontsize=14)
        wedges2, _, autotexts2 = ax2.pie(target_pcts_sorted_pie, explode=explode, labels=None, colors=colors, autopct='%1.1f%%' if self.show_values_on_charts else None, shadow=True, startangle=90, wedgeprops={'edgecolor': 'white', 'linewidth': 0.8}, pctdistance=0.85)
        ax2.set_title('目标配置 (Target)', fontsize=14)
        if self.show_values_on_charts and autotexts1: plt.setp(autotexts1, size=9, weight="bold", color="white"); plt.setp(autotexts2, size=9, weight="bold", color="white")
        fig_pie.legend(wedges1, categories_sorted_pie, loc='lower center', bbox_to_anchor=(0.5, -0.05 if len(categories_sorted_pie) <= 5 else -0.1), ncol=min(5, len(categories_sorted_pie)), frameon=True, fancybox=True, shadow=True, title="可调整资产类别")
        pie_filename_base = f"alloc_pie{filename_suffix}" # Use suffix
        saved_filenames['pie'] = self._save_figure(fig_pie, pie_filename_base) # Capture result
        plt.show()
        plt.close(fig_pie) # Close figure after showing/saving

        # --- Bar Chart ---
        sort_idx_bar = np.argsort(categories_to_plot); categories_sorted_bar = [categories_to_plot[i] for i in sort_idx_bar]
        current_pcts_sorted_bar = [rebal_current_pct.get(cat, 0.0) for cat in categories_sorted_bar]; target_pcts_sorted_bar = [rebal_target_pct.get(cat, 0.0) for cat in categories_sorted_bar]
        bar_figsize = (fig_size[0], fig_size[1] * 0.7); fig_bar, ax_bar = plt.subplots(figsize=bar_figsize)
        x = np.arange(len(categories_sorted_bar)); width = 0.35; color_current = '#3274A1'; color_target = '#E1812C'
        rects1 = ax_bar.bar(x - width/2, current_pcts_sorted_bar, width, label='当前配置 (Current)', color=color_current, alpha=0.85)
        rects2 = ax_bar.bar(x + width/2, target_pcts_sorted_bar, width, label='目标配置 (Target)', color=color_target, alpha=0.85)
        ax_bar.set_ylabel('可调整部分内部占比 (%)', fontsize=12); ax_bar.set_title(f'{title_prefix}可调整部分内部配置比较', fontsize=16, fontweight='bold')
        ax_bar.set_xticks(x); ax_bar.set_xticklabels(categories_sorted_bar, rotation=30, ha='right'); ax_bar.legend(loc='best', fancybox=True, framealpha=0.9)
        ax_bar.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{y:.0%}'))
        if self.show_values_on_charts:
            def percent_fmt(val): return f'{val:.1%}'
            ax_bar.bar_label(rects1, padding=3, fmt=percent_fmt, fontsize=9); ax_bar.bar_label(rects2, padding=3, fmt=percent_fmt, fontsize=9)
        ax_bar.grid(axis='y', linestyle='--', alpha=0.5); plt.tight_layout()
        bar_filename_base = f"alloc_bar{filename_suffix}" # Use suffix
        saved_filenames['bar'] = self._save_figure(fig_bar, bar_filename_base) # Capture result
        plt.show()
        plt.close(fig_bar) # Close figure after showing/saving

        # Return dict only if at least one chart was saved
        return saved_filenames if any(saved_filenames.values()) else None

    def plot_drift_analysis(
        self,
        drift_analysis_df: pd.DataFrame,
        threshold: float = 0.05,
        non_rebalanceable_classes: Optional[Set[str]] = None,
        title_prefix: str = "",
        figsize: Optional[Tuple[float, float]] = None,
        filename_suffix: str = ""
    ) -> Optional[str]:
        """
        Plots allocation drift for REBALANCEABLE assets.

        Args:
            drift_analysis_df: DataFrame with drift analysis results.
            threshold: Significance threshold for highlighting drift.
            non_rebalanceable_classes: Set of asset classes to exclude.
            title_prefix: Prefix for the plot title.
            figsize: Figure size tuple.
            filename_suffix: Suffix to add to the base filename.

        Returns:
            The sanitized base filename (without extension) if saved successfully,
            otherwise None.
        """
        print(f"\nPlotting Drift Analysis ({title_prefix.strip()})...")
        # (Keep filtering logic as is - ID: plotter_py_drift_filter)
        required_cols = ['当前配置 (%)', '目标配置 (%)', '绝对偏离 (%)'];
        if not isinstance(drift_analysis_df, pd.DataFrame): print("Error: drift_analysis_df must be a pandas DataFrame."); return None
        if not all(col in drift_analysis_df.columns for col in required_cols): print(f"Error: drift_analysis_df missing required columns: {required_cols}"); return None
        if not isinstance(drift_analysis_df.index, pd.Index): print("Error: drift_analysis_df must have asset classes as index."); return None
        if non_rebalanceable_classes is None: non_rebalanceable_classes = set()
        plot_df = drift_analysis_df[~drift_analysis_df.index.isin(non_rebalanceable_classes)].copy()
        if plot_df.empty: print("Warning: No rebalanceable asset classes found for drift plot."); return None
        print(f"  - Plotting drift for rebalanceable classes: {plot_df.index.tolist()}")
        try: plot_df = plot_df[required_cols].astype(float)
        except ValueError as e: print(f"Error converting drift data to float: {e}."); return None
        fig_size = figsize or self.default_figsize; fig, ax = plt.subplots(figsize=fig_size)
        categories = plot_df.index.tolist(); current_alloc = plot_df['当前配置 (%)']; target_alloc = plot_df['目标配置 (%)']; abs_drift = plot_df['绝对偏离 (%)'].abs()
        x = np.arange(len(categories)); width = 0.35; color_current = '#3274A1'; color_target = '#E1812C'
        ax.bar(x - width/2, current_alloc, width, label='当前配置 (% of Total)', color=color_current, alpha=0.8); ax.bar(x + width/2, target_alloc, width, label='目标配置 (% of Total)', color=color_target, alpha=0.8)
        for i, category in enumerate(categories):
            curr_val = current_alloc.loc[category]; targ_val = target_alloc.loc[category]; drift_mag = abs_drift.loc[category]; signed_drift = plot_df.loc[category, '绝对偏离 (%)']
            is_significant = drift_mag > threshold; line_color = 'red' if is_significant else 'grey'; line_style = '-' if is_significant else ':'; line_width = 2 if is_significant else 1; alpha = 0.9 if is_significant else 0.5
            ax.plot([i - width/2, i + width/2], [curr_val, targ_val], color=line_color, linestyle=line_style, linewidth=line_width, alpha=alpha, marker='o', markersize=4)
            if is_significant: drift_text = f"{signed_drift:+.1%}"; ax.annotate(drift_text, xy=((i - width/2 + i + width/2) / 2, (curr_val + targ_val) / 2), xytext=(0, 5 if curr_val > targ_val else -15), textcoords='offset points', ha='center', va='center', fontsize=9, fontweight='bold', color='red', bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="red", alpha=0.7))
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=0.5); ax.grid(True, axis='y', linestyle='--', alpha=0.3); ax.set_xlabel('资产类别 (Asset Class)', fontsize=12); ax.set_ylabel('占总资产比例 (% of Total Portfolio)', fontsize=12)
        plot_title = f'{title_prefix}可调整资产偏离分析 - 阈值: {threshold:.0%}'; ax.set_title(plot_title.strip(), fontsize=16, fontweight='bold')
        ax.set_xticks(x); ax.set_xticklabels(categories, rotation=45, ha='right'); ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{y:.0%}'))
        ax.plot([], [], color='red', linestyle='-', linewidth=2, label=f'偏离 (Drift) > {threshold:.0%}'); ax.legend(loc='best', frameon=True, fancybox=True, shadow=True); plt.tight_layout()
        drift_filename_base = f"drift_analysis{filename_suffix}" # Use suffix
        saved_base_filename = self._save_figure(fig, drift_filename_base) # Capture result
        plt.show()
        plt.close(fig) # Close figure after showing/saving
        return saved_base_filename # Return the base filename string or None

    def plot_sub_category_allocation(
        self,
        holdings_sub_level: Dict[str, float],
        target_sub_level: Dict[str, float],
        taxonomy: Dict[str, Any],
        non_rebalanceable_classes: Optional[Set[str]] = None,
        title_prefix: str = "",
        figsize: Optional[Tuple[float, float]] = None,
        filename_suffix: str = ""
    ) -> Optional[str]:
        """
        Plots current vs target allocation by sub-category using stacked bars.

        Args:
            holdings_sub_level: Dict of current sub-category values.
            target_sub_level: Dict of target sub-category percentages.
            taxonomy: Taxonomy dictionary mapping sub-to-top categories.
            non_rebalanceable_classes: Set of top-level classes to exclude.
            title_prefix: Prefix for the plot title.
            figsize: Figure size tuple.
            filename_suffix: Suffix to add to the base filename.

        Returns:
            The sanitized base filename (without extension) if saved successfully,
            otherwise None.
        """
        print(f"\nPlotting Sub-Category Allocation ({title_prefix.strip()})...")
        fig_size = figsize or self.default_figsize
        if non_rebalanceable_classes is None: non_rebalanceable_classes = set()

        # --- Prepare Data ---
        sub_to_top_map: Dict[str, str] = {}
        for top, subs in taxonomy.get('sub_classes', {}).items():
            for sub in subs: sub_to_top_map[sub] = top

        # Filter out non-rebalanceable sub-categories based on their parent
        plot_subs_current = {k: v for k, v in holdings_sub_level.items() if sub_to_top_map.get(k) not in non_rebalanceable_classes}
        plot_subs_target = {k: v for k, v in target_sub_level.items() if sub_to_top_map.get(k) not in non_rebalanceable_classes}

        if not plot_subs_current and not plot_subs_target:
            print("Warning: No rebalanceable sub-categories found to plot.")
            return None

        # Create DataFrames for plotting
        df_current = pd.Series(plot_subs_current).reset_index()
        df_current.columns = ['SubCategory', 'CurrentValue']
        df_current['TopCategory'] = df_current['SubCategory'].map(sub_to_top_map)

        df_target = pd.Series(plot_subs_target).reset_index()
        df_target.columns = ['SubCategory', 'TargetPct'] # Target is already percentage
        df_target['TopCategory'] = df_target['SubCategory'].map(sub_to_top_map)

        # Calculate current percentages relative to the rebalanceable total value
        total_rebal_value = sum(plot_subs_current.values())
        if total_rebal_value > 1e-6:
            df_current['CurrentPct'] = df_current['CurrentValue'] / total_rebal_value
        else:
            df_current['CurrentPct'] = 0.0

        # Pivot data for stacked bar plot
        pivot_current = df_current.pivot(index='TopCategory', columns='SubCategory', values='CurrentPct').fillna(0)
        # Target percentages need to be rescaled relative to rebalanceable total target %
        total_target_rebal_pct = sum(plot_subs_target.values())
        if total_target_rebal_pct > 1e-6:
             df_target['TargetPctRescaled'] = df_target['TargetPct'] / total_target_rebal_pct
        else:
             df_target['TargetPctRescaled'] = 0.0
        pivot_target = df_target.pivot(index='TopCategory', columns='SubCategory', values='TargetPctRescaled').fillna(0)

        # Ensure both pivots have the same columns (all sub-categories) and index (all top-categories)
        all_subs = sorted(list(set(df_current['SubCategory']) | set(df_target['SubCategory'])))
        all_tops = sorted(list(set(df_current['TopCategory']) | set(df_target['TopCategory'])))
        pivot_current = pivot_current.reindex(index=all_tops, columns=all_subs, fill_value=0)
        pivot_target = pivot_target.reindex(index=all_tops, columns=all_subs, fill_value=0)

        # --- Plotting ---
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=fig_size, sharey=True)
        fig.suptitle(f'{title_prefix}子类别配置比较 (内部占比)', fontsize=16, fontweight='bold')

        # Use a distinct colormap
        try:
            num_sub_colors = len(all_subs)
            sub_cmap = plt.get_cmap(self.color_palette) # Use same palette or a different one
            sub_colors = sub_cmap(np.linspace(0, 1, num_sub_colors)) if num_sub_colors > 0 else []
        except ValueError:
            print(f"Warning: Colormap '{self.color_palette}' not found. Using 'tab20'.")
            sub_colors = plt.get_cmap('tab20')(np.linspace(0, 1, len(all_subs))) if len(all_subs) > 0 else []

        # Create mapping from SubCategory name to color
        color_map = {label: color for label, color in zip(all_subs, sub_colors)}

        pivot_current.plot(kind='bar', stacked=True, ax=ax1, color=[color_map.get(c, 'grey') for c in pivot_current.columns], legend=False, width=0.8)
        ax1.set_title('当前配置 (Current)')
        ax1.set_ylabel('可调整部分内部占比 (%)')
        ax1.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{y:.0%}'))
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(axis='y', linestyle='--', alpha=0.5)

        pivot_target.plot(kind='bar', stacked=True, ax=ax2, color=[color_map.get(c, 'grey') for c in pivot_target.columns], legend=False, width=0.8)
        ax2.set_title('目标配置 (Target)')
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(axis='y', linestyle='--', alpha=0.5)

        # Add a single legend for sub-categories
        # Create custom legend handles (patches)
        legend_handles = [Patch(color=color_map[label], label=label) for label in all_subs if label in color_map and (label in pivot_current.columns or label in pivot_target.columns)] # Only create handles for plotted subs

        fig.legend(handles=legend_handles, title='子类别 (Sub-Category)', loc='lower center',
                   bbox_to_anchor=(0.5, -0.15 if len(all_tops)>4 else -0.1), ncol=min(4, len(legend_handles)))

        plt.tight_layout(rect=[0, 0.1, 1, 0.95]) # Adjust layout to make room for legend
        sub_cat_filename_base = f"sub_category_allocation{filename_suffix}"
        saved_base_filename = self._save_figure(fig, sub_cat_filename_base) # Capture result
        plt.show()
        plt.close(fig) # Close figure after showing/saving
        return saved_base_filename # Return the base filename string or None


    def plot_efficient_frontier(self, model, risk_preference: str = '均衡型', figsize: Optional[Tuple[float, float]] = None) -> Optional[str]:
        """
        Plots the efficient frontier, individual assets, risk profiles, and CML.

        Args:
            model: An instance of AssetAllocationModel containing calculated results.
            risk_preference: The specific risk profile to highlight.
            figsize: Figure size tuple.

        Returns:
            The sanitized base filename ("efficient_frontier") if saved successfully,
            otherwise None.
        """
        print("\nPlotting Efficient Frontier...")
        fig_size = figsize or self.default_figsize
        if not hasattr(model, 'efficient_frontier') or not hasattr(model, 'risk_profiles'):
            print("Error: Provided 'model' object does not appear to be a valid AssetAllocationModel instance.")
            return None
        if model.efficient_frontier is None:
            print("Efficient frontier data not found, calculating...")
            model.calculate_efficient_frontier()
        if model.risk_profiles is None:
            print("Risk profiles not found, calculating...")
            model.calculate_risk_profiles()
        if model.efficient_frontier is None or model.efficient_frontier.empty or model.risk_profiles is None:
            print("Error: Cannot plot efficient frontier. Missing required data.")
            return None

        fig, ax = plt.subplots(figsize=fig_size)
        # Plot efficient frontier line
        ax.plot(model.efficient_frontier['volatility'], model.efficient_frontier['returns'],
                color='#007ACC', linewidth=2.5, label='有效前沿 (Efficient Frontier)', zorder=2)

        # Plot individual assets
        if hasattr(model, 'cov_matrix_annualized') and hasattr(model, 'mean_returns_annualized'):
            try:
                asset_vol = np.sqrt(np.diag(model.cov_matrix_annualized))
                asset_ret = model.mean_returns_annualized
                ax.scatter(asset_vol, asset_ret, s=100, marker='o', c='#D62728',
                           label='单个资产 (Individual Assets)', alpha=0.7, edgecolors='w', zorder=3)
                for i, asset in enumerate(model.assets):
                    ax.text(asset_vol[i]*1.01, asset_ret[i]*1.01, asset, fontsize=9, verticalalignment='bottom')
            except Exception as e:
                print(f"Warning: Could not plot individual assets. Error: {e}")
        else:
            print("Warning: Annualized mean/covariance not found. Skipping individual assets plot.")

        # Plot risk profiles
        profile_colors = {'保守型': '#2CA02C', '均衡型': '#FF7F0E', '进取型': '#9467BD'}
        profile_markers = {'保守型': 'D', '均衡型': '*', '进取型': 'X'}
        for name, portfolio in model.risk_profiles.items():
             if not portfolio or not portfolio.get('success'):
                 print(f"Warning: Skipping invalid profile '{name}'.")
                 continue
             vol = portfolio.get('volatility')
             ret = portfolio.get('returns')
             if vol is None or ret is None:
                 print(f"Warning: Missing data for profile '{name}'.")
                 continue
             is_highlighted = (name == risk_preference)
             ax.scatter(vol, ret, s=250 if is_highlighted else 150, marker=profile_markers.get(name, 'o'),
                        c=profile_colors.get(name, 'grey'), label=f'{name} 组合 (Portfolio)',
                        alpha=1.0 if is_highlighted else 0.8, edgecolors='k' if is_highlighted else 'w',
                        linewidth=1.5 if is_highlighted else 1.0, zorder=4)
             if is_highlighted:
                 ax.annotate(f"{name}\nReturn: {ret:.2%}\nRisk: {vol:.2%}", (vol, ret),
                             textcoords="offset points", xytext=(0, -40), ha='center', fontsize=10,
                             bbox=dict(boxstyle="round,pad=0.5", fc=profile_colors.get(name, 'grey'), alpha=0.2))

        # Plot Capital Market Line (CML) if possible
        max_sharpe_portfolio = model.risk_profiles.get('成长型') # Use Growth profile as default for max Sharpe
        if max_sharpe_portfolio and max_sharpe_portfolio.get('success') and max_sharpe_portfolio.get('volatility', 0) > 1e-6:
             m_vol = max_sharpe_portfolio['volatility']
             m_ret = max_sharpe_portfolio['returns']
             rf_rate = model.risk_free_rate
             # Extend CML slightly beyond the last point on the frontier or the max sharpe point
             max_vol_on_plot = max(model.efficient_frontier['volatility'].max() * 1.1, m_vol * 1.2)
             cml_x = np.linspace(0, max_vol_on_plot, 100)
             cml_slope = (m_ret - rf_rate) / m_vol
             cml_y = rf_rate + cml_slope * cml_x
             ax.plot(cml_x, cml_y, color='#1f77b4', linestyle='--', linewidth=1.5,
                     label='资本市场线 (CML)', zorder=1)
             ax.scatter(0, rf_rate, s=100, marker='s', c='#1f77b4',
                        label='无风险利率 (Risk-Free Rate)', zorder=3, edgecolors='w')
             ax.text(max_vol_on_plot * 0.01, rf_rate, f' {rf_rate:.1%}', fontsize=9, verticalalignment='center')

        # Formatting
        ax.set_title('投资组合有效前沿分析 (Portfolio Efficient Frontier Analysis)', fontsize=16, fontweight='bold')
        ax.set_xlabel('预期年化波动率 (Expected Annual Volatility)', fontsize=12)
        ax.set_ylabel('预期年化收益率 (Expected Annual Return)', fontsize=12)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{y:.1%}'))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.1%}'))
        ax.legend(loc='upper left', bbox_to_anchor=(0.01, 0.99), fontsize=10, frameon=True, fancybox=True, framealpha=0.8)
        ax.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()

        frontier_filename_base = "efficient_frontier"
        saved_base_filename = self._save_figure(fig, frontier_filename_base) # Capture result
        plt.show()
        plt.close(fig) # Close figure after showing/saving
        return saved_base_filename # Return the base filename string or None

    def plot_correlation_heatmap(self, returns_data: pd.DataFrame, title: str = "资产类别相关性矩阵 (Asset Class Correlation Matrix)", figsize: Optional[Tuple[float, float]] = None) -> Optional[str]:
        """
        Plots a heatmap of the correlation matrix for asset returns.

        Args:
            returns_data: DataFrame of asset returns (columns are assets, index is time).
            title: Title for the heatmap.
            figsize: Figure size tuple.

        Returns:
            The sanitized base filename ("correlation_heatmap") if saved successfully,
            otherwise None.
        """
        print("\nPlotting Correlation Heatmap...")
        if not isinstance(returns_data, pd.DataFrame) or returns_data.shape[1] < 2:
            print("Warning: Need DataFrame with >= 2 assets for correlation heatmap.")
            return None
        try:
            corr_matrix = returns_data.corr()
        except Exception as e:
            print(f"Error calculating correlation matrix: {e}")
            return None

        n_assets = corr_matrix.shape[1]
        # Adjust figsize dynamically based on number of assets
        base_size = 6
        size_factor = 0.8
        fig_w = max(base_size, n_assets * size_factor)
        fig_h = max(base_size * 0.8, n_assets * size_factor * 0.8)
        fig_size = figsize or (fig_w, fig_h)
        fig, ax = plt.subplots(figsize=fig_size)

        mask = np.triu(np.ones_like(corr_matrix, dtype=bool)) # Mask for upper triangle
        cmap = sns.diverging_palette(230, 20, as_cmap=True, center='light') # Blue-Red diverging palette

        sns.heatmap(corr_matrix, mask=mask, cmap=cmap, vmax=1, vmin=-1, center=0,
                    square=True, linewidths=.5, annot=True, fmt=".2f",
                    annot_kws={"size": 9 if n_assets < 10 else 8},
                    cbar_kws={"shrink": .7, "label": "相关系数 (Correlation Coefficient)"}, ax=ax)

        ax.set_title(title, fontsize=16, fontweight='bold')
        plt.xticks(rotation=45, ha='right', fontsize=10)
        plt.yticks(rotation=0, fontsize=10)
        plt.tight_layout(pad=1.5) # Add padding

        heatmap_filename_base = "correlation_heatmap"
        saved_base_filename = self._save_figure(fig, heatmap_filename_base) # Capture result
        plt.show()
        plt.close(fig) # Close figure after showing/saving
        return saved_base_filename # Return the base filename string or None

