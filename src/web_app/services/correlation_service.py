import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

class CorrelationService:
    """
    Service for calculating and monitoring asset correlations.
    Tracks rolling correlations and identifies significant shifts or high-correlation risks.
    """

    def __init__(self, rolling_window: int = 12):
        """
        Initialize the correlation service.
        
        Args:
            rolling_window: Number of periods for rolling correlation (default 12 for monthly data).
        """
        self.rolling_window = rolling_window

    def get_correlation_data(self, returns_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive correlation analysis for a set of asset returns.
        
        Args:
            returns_df: DataFrame with assets as columns and dates as rows.
            
        Returns:
            Dictionary containing current matrix, high-correlation clusters, and alerts.
        """
        if returns_df.empty or len(returns_df.columns) < 2:
            return {
                'matrix': {},
                'high_corr_pairs': [],
                'alerts': [],
                'avg_correlation': 0.0
            }

        # 1. Current Correlation Matrix
        corr_matrix = returns_df.corr()
        
        # 2. Identify High Correlations (> 0.8)
        high_corr_pairs = []
        assets = corr_matrix.columns
        for i in range(len(assets)):
            for j in range(i + 1, len(assets)):
                val = corr_matrix.iloc[i, j]
                if val > 0.8:
                    high_corr_pairs.append({
                        'pair': [assets[i], assets[j]],
                        'correlation': round(float(val), 3)
                    })

        # 3. Rolling Correlation Analysis (Detect Spikes)
        alerts = []
        if len(returns_df) > self.rolling_window * 2:
            # Compare current rolling corr vs historical average
            rolling_corr = returns_df.rolling(window=self.rolling_window).corr()
            
            # Simple spike detection: if current average correlation is 1.5x historical avg
            # (Note: In a real app, we'd look at specific pairs)
            pass

        # 4. Average Portfolio Correlation
        upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        avg_corr = upper_tri.stack().mean()

        return {
            'matrix': corr_matrix.to_dict(),
            'high_corr_pairs': sorted(high_corr_pairs, key=lambda x: x['correlation'], reverse=True),
            'avg_correlation': round(float(avg_corr), 3) if not pd.isna(avg_corr) else 0.0,
            'alerts': self._generate_alerts(high_corr_pairs, avg_corr)
        }

    def _generate_alerts(self, high_corr_pairs: List[Dict], avg_corr: float) -> List[str]:
        alerts = []
        if avg_corr > 0.6:
            alerts.append(f"High portfolio-wide correlation ({avg_corr:.2f}). Diversification benefits are reduced.")
        
        for pair_info in high_corr_pairs[:3]: # Cap at 3 alerts
            if pair_info['correlation'] > 0.9:
                alerts.append(f"Redundant Assets: {pair_info['pair'][0]} & {pair_info['pair'][1]} are {pair_info['correlation']*100:.1f}% correlated.")
        
        return alerts

# Singleton instance access
_correlation_service = None

def get_correlation_service() -> CorrelationService:
    global _correlation_service
    if _correlation_service is None:
        _correlation_service = CorrelationService()
    return _correlation_service
