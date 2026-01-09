# portfolio_lib/analysis/engine.py
"""
Portfolio Analysis Engine module.

Provides the PortfolioAnalysisEngine class to analyze current portfolio
holdings (both top-level and sub-level) against target allocations,
calculating drift and concentration risk.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

class PortfolioAnalysisEngine:
    """
    Analyzes a portfolio's current allocation against a target allocation
    at both top-level and sub-level asset classes.

    Calculates allocation drift for both levels and concentration risk (HHI)
    based on the top-level allocation.
    """

    def __init__(
        self,
        holdings_top_level: Dict[str, float],
        holdings_sub_level: Dict[str, float]
        ):
        """
        Initializes the analysis engine with categorized holdings.

        Args:
            holdings_top_level: Dict {top_class: value_float}.
            holdings_sub_level: Dict {sub_class: value_float}.
        """
        # --- Input Validation ---
        if not isinstance(holdings_top_level, dict) or not isinstance(holdings_sub_level, dict):
            raise TypeError("Holdings must be provided as dictionaries.")
        if not all(isinstance(v, (int, float)) for v in holdings_top_level.values()):
             raise ValueError("Values in holdings_top_level must be numeric.")
        if not all(isinstance(v, (int, float)) for v in holdings_sub_level.values()):
             raise ValueError("Values in holdings_sub_level must be numeric.")

        # --- Top Level Data ---
        self.holdings_top_level_values: Dict[str, float] = holdings_top_level
        self.total_value_top: float = sum(self.holdings_top_level_values.values())
        self.current_alloc_top_pct: Dict[str, float] = {
            asset: (value / self.total_value_top) if self.total_value_top > 0 else 0.0
            for asset, value in self.holdings_top_level_values.items()
        }
        self.target_alloc_top: Optional[Dict[str, float]] = None

        # --- Sub Level Data ---
        self.holdings_sub_level_values: Dict[str, float] = holdings_sub_level
        # Use the same total value for calculating sub-level percentages
        self.total_value_sub: float = sum(self.holdings_sub_level_values.values())
        # Sanity check totals
        if not np.isclose(self.total_value_top, self.total_value_sub, atol=1e-2): # Allow small tolerance for float sums
             print(f"Warning: Top-level total ({self.total_value_top:,.0f}) and Sub-level total ({self.total_value_sub:,.0f}) differ slightly.")
             # Use top-level total as the definitive one for percentage calculations
             self.total_value = self.total_value_top
        else:
             self.total_value = self.total_value_top

        self.current_alloc_sub_pct: Dict[str, float] = {
            asset: (value / self.total_value) if self.total_value > 0 else 0.0
            for asset, value in self.holdings_sub_level_values.items()
        }
        self.target_alloc_sub: Optional[Dict[str, float]] = None

        print("PortfolioAnalysisEngine Initialized.")
        print(f"  - Total Portfolio Value: {self.total_value:,.0f}")
        # print(f"  - Current Top-Level Allocation (%): { {k: f'{v:.1%}' for k, v in self.current_alloc_top_pct.items()} }")
        # print(f"  - Current Sub-Level Allocation (%): { {k: f'{v:.1%}' for k, v in self.current_alloc_sub_pct.items()} }")


    def set_target_allocation(
        self,
        target_allocation_top: Dict[str, float],
        target_allocation_sub: Dict[str, float]
        ):
        """
        Sets the target asset allocations for comparison (both levels).

        Args:
            target_allocation_top: Dict {top_class: pct_float}.
            target_allocation_sub: Dict {sub_class: pct_float}.
        """
        # --- Validate and Set Top Level Target ---
        if not isinstance(target_allocation_top, dict): raise TypeError("target_allocation_top must be a dictionary.")
        if not all(isinstance(v, float) for v in target_allocation_top.values()): raise ValueError("Values in target_allocation_top must be floats.")
        total_target_top = sum(target_allocation_top.values())
        if not np.isclose(total_target_top, 1.0, atol=0.01):
            print(f"Warning: Top-level target allocations sum to {total_target_top:.2%}. Normalizing...")
            if abs(total_target_top) > 1e-6: self.target_alloc_top = {k: v / total_target_top for k, v in target_allocation_top.items()}
            else: print("Warning: Cannot normalize top-level target with zero sum."); self.target_alloc_top = target_allocation_top
        else: self.target_alloc_top = target_allocation_top
        print("Top-Level target allocation set.")
        # print(f"  - Target Top-Level (%): { {k: f'{v:.1%}' for k, v in self.target_alloc_top.items()} }")

        # --- Validate and Set Sub Level Target ---
        if not isinstance(target_allocation_sub, dict): raise TypeError("target_allocation_sub must be a dictionary.")
        if not all(isinstance(v, float) for v in target_allocation_sub.values()): raise ValueError("Values in target_allocation_sub must be floats.")
        total_target_sub = sum(target_allocation_sub.values())
        # Sub-level sum should also ideally match the top-level sum (which should be 1.0)
        if not np.isclose(total_target_sub, 1.0, atol=0.01):
            print(f"Warning: Sub-level target allocations sum to {total_target_sub:.2%}. Check calculation/configuration.")
            # We generally don't normalize sub-level independently, as it should derive from top-level
            self.target_alloc_sub = target_allocation_sub # Store as is, but warn
        else:
            self.target_alloc_sub = target_allocation_sub
        print("Sub-Level target allocation set.")
        # print(f"  - Target Sub-Level (%): { {k: f'{v:.1%}' for k, v in self.target_alloc_sub.items()} }")


    def analyze_drift_top_level(self) -> Optional[pd.DataFrame]:
        """
        Analyzes the drift for top-level asset classes.

        Returns:
            DataFrame with drift analysis or None if target not set.
            Columns contain floats representing percentages (0.0 to 1.0).
        """
        if self.target_alloc_top is None:
            print("Error: Top-level target allocation not set.")
            return None

        print("\nAnalyzing Top-Level Allocation Drift...")
        drift_data = {}
        all_categories = set(self.current_alloc_top_pct.keys()) | set(self.target_alloc_top.keys())

        for category in sorted(list(all_categories)):
            current_pct = self.current_alloc_top_pct.get(category, 0.0)
            target_pct = self.target_alloc_top.get(category, 0.0)
            absolute_drift = current_pct - target_pct
            if abs(target_pct) > 1e-9: relative_drift = absolute_drift / target_pct
            elif abs(absolute_drift) > 1e-9: relative_drift = np.inf * np.sign(absolute_drift)
            else: relative_drift = 0.0

            drift_data[category] = {
                '当前配置 (%)': current_pct,
                '目标配置 (%)': target_pct,
                '绝对偏离 (%)': absolute_drift,
                '相对偏离 (%)': relative_drift
            }

        drift_df = pd.DataFrame.from_dict(drift_data, orient='index')
        print("Top-Level drift analysis complete.")
        return drift_df

    # --- NEW METHOD: analyze_drift_sub_level ---
    def analyze_drift_sub_level(self) -> Optional[pd.DataFrame]:
        """
        Analyzes the drift for sub-level asset classes.

        Returns:
            DataFrame with drift analysis or None if target not set.
            Columns contain floats representing percentages (0.0 to 1.0).
        """
        if self.target_alloc_sub is None:
            print("Error: Sub-level target allocation not set.")
            return None

        print("\nAnalyzing Sub-Level Allocation Drift...")
        drift_data = {}
        # Combine keys from current sub-level holdings and sub-level target
        all_sub_categories = set(self.current_alloc_sub_pct.keys()) | set(self.target_alloc_sub.keys())

        for sub_category in sorted(list(all_sub_categories)):
            current_pct = self.current_alloc_sub_pct.get(sub_category, 0.0)
            target_pct = self.target_alloc_sub.get(sub_category, 0.0)
            absolute_drift = current_pct - target_pct

            # Calculate relative drift, handle division by zero
            if abs(target_pct) > 1e-9:
                relative_drift = absolute_drift / target_pct
            elif abs(absolute_drift) > 1e-9: # Target is 0 but current is not
                 relative_drift = np.inf * np.sign(absolute_drift)
            else: # Both target and current are near zero
                 relative_drift = 0.0

            drift_data[sub_category] = {
                '当前配置 (%)': current_pct,
                '目标配置 (%)': target_pct,
                '绝对偏离 (%)': absolute_drift,
                '相对偏离 (%)': relative_drift
            }

        drift_df = pd.DataFrame.from_dict(drift_data, orient='index')
        print("Sub-Level drift analysis complete.")
        return drift_df


    def analyze_concentration_risk(self) -> Dict[str, Any]:
        """
        Analyzes portfolio concentration risk using HHI based on TOP-LEVEL allocation.

        Returns:
            A dictionary containing concentration risk metrics.
        """
        print("\nAnalyzing Concentration Risk (based on Top-Level)...")
        # Concentration risk is typically assessed at the top level
        current_alloc = self.current_alloc_top_pct

        hhi = sum(pct**2 for pct in current_alloc.values() if pd.notna(pct))

        if current_alloc:
             sorted_alloc = sorted(current_alloc.items(), key=lambda item: item[1], reverse=True)
             max_category_name = sorted_alloc[0][0]
             max_category_pct = sorted_alloc[0][1]
             top3_pct = sum(item[1] for item in sorted_alloc[:3])
        else:
             max_category_name = "N/A"; max_category_pct = 0.0; top3_pct = 0.0

        # Determine risk level based on HHI thresholds
        if hhi > 0.35: risk_level = "高风险 (High Risk)"; suggestion = "建议显著增加资产多元化 (Recommend significant diversification)"
        elif hhi > 0.25: risk_level = "中等风险 (Medium Risk)"; suggestion = "建议增加资产多样性 (Recommend increasing diversity)"
        elif hhi > 0.18: risk_level = "适中风险 (Moderate Risk)"; suggestion = "集中度在合理范围 (Concentration reasonable)"
        else: risk_level = "低风险 (Low Risk)"; suggestion = "资产配置较为分散 (Portfolio well-diversified)"

        concentration_analysis = {
            'HHI指数': hhi,
            '集中度风险级别': risk_level,
            '最大持仓类别': max_category_name,
            '最大持仓比例': max_category_pct, # Float
            '前3大类别占比': top3_pct,       # Float
            '建议': suggestion
        }
        print("Concentration risk analysis complete.")
        return concentration_analysis

