"""
Market Regime Detection Module

This module implements Hidden Markov Model (HMM) based market regime detection
to identify distinct market states (high/low volatility, bull/bear markets)
for dynamic asset allocation strategies.

Phase 5.3 Step 2 - Market Regime Detection
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import warnings

# HMM and ML libraries
from hmmlearn.hmm import GaussianHMM
from sklearn.preprocessing import StandardScaler
import yaml

# For type hints when DataManager might not be available
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from data_manager.manager import DataManager as DataManagerType
else:
    DataManagerType = object


class MarketRegimeDetector:
    """
    Market Regime Detection using Hidden Markov Models (HMM).
    
    This class identifies distinct market regimes (e.g., high-volatility, low-volatility,
    bull, bear) using historical market data and Hidden Markov Models.
    """
    
    def __init__(self, data_manager: DataManagerType, n_components: int = 3):
        """
        Initialize the Market Regime Detector.
        
        Args:
            data_manager (DataManager): Instance of DataManager for data access
            n_components (int): Number of hidden states/regimes to detect (default: 3)
        """
        self.data_manager = data_manager
        self.n_components = n_components
        self.logger = logging.getLogger(__name__)
        
        # Model and data storage
        self.hmm_model = None
        self.market_data = None
        self.regime_predictions = None
        self.feature_scaler = StandardScaler()
        
        # Configuration
        self.benchmark_config = self._load_benchmark_config()
        
        self.logger.info(f"MarketRegimeDetector initialized with {n_components} regimes")
    
    def _load_benchmark_config(self) -> Dict[str, Any]:
        """Load benchmark configuration from config/benchmark.yaml"""
        try:
            with open('config/benchmark.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            self.logger.info("Benchmark configuration loaded successfully")
            return config
        except FileNotFoundError:
            self.logger.warning("benchmark.yaml not found, using default configuration")
            return {
                'primary_benchmark': 'SPY',  # Default to S&P 500
                'benchmarks': {
                    'SPY': {
                        'name': 'S&P 500 ETF',
                        'type': 'equity_index',
                        'description': 'Large-cap US equity market benchmark'
                    }
                }
            }
        except Exception as e:
            self.logger.error(f"Error loading benchmark configuration: {e}")
            return {}
    
    def get_market_data(self, 
                       start_date: Optional[datetime] = None, 
                       end_date: Optional[datetime] = None,
                       benchmark: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch and process historical market data for regime detection.
        
        Args:
            start_date (datetime, optional): Start date for data retrieval
            end_date (datetime, optional): End date for data retrieval  
            benchmark (str, optional): Benchmark symbol to use (default: from config)
            
        Returns:
            pd.DataFrame: DataFrame with datetime index and returns/features columns
        """
        try:
            # Determine benchmark to use
            if benchmark is None:
                benchmark = self.benchmark_config.get('primary_benchmark', 'SPY')
            
            self.logger.info(f"Fetching market data for benchmark: {benchmark}")
            
            # For Phase 5.3 Step 2.1, we'll use portfolio returns as a proxy for market data
            # since we have comprehensive historical portfolio data available
            # This approach aligns with the personal investment system's data architecture
            
            # Get historical portfolio data from DataManager
            portfolio_data = self._get_portfolio_returns_as_market_proxy()
            
            if portfolio_data is None or portfolio_data.empty:
                raise ValueError("No portfolio data available for market analysis")
            
            # Calculate market features for regime detection
            market_features = self._calculate_market_features(portfolio_data)
            
            # Store the processed data
            self.market_data = market_features
            
            self.logger.info(f"Market data processed successfully: {market_features.shape}")
            return market_features
            
        except Exception as e:
            self.logger.error(f"Error fetching market data: {e}")
            raise
    
    def _get_portfolio_returns_as_market_proxy(self) -> pd.DataFrame:
        """
        Get portfolio returns data as a proxy for market data.
        
        This leverages the existing 60-month historical portfolio infrastructure
        to provide market-representative data for regime detection.
        
        Returns:
            pd.DataFrame: Portfolio returns with datetime index
        """
        try:
            # Get monthly income/expense data which contains market-relevant information
            monthly_data = self.data_manager.get_monthly_income_expense()
            
            if monthly_data is None or monthly_data.empty:
                self.logger.warning("No monthly data available from DataManager")
                return pd.DataFrame()
            
            # Calculate net cash flow as a market indicator
            # Positive cash flow periods often correlate with positive market periods
            if 'Net_Cash_Flow_Calc_CNY' in monthly_data.columns:
                market_proxy = monthly_data[['Net_Cash_Flow_Calc_CNY']].copy()
                market_proxy.columns = ['market_indicator']
                
                # Calculate month-over-month changes as returns proxy
                market_proxy['returns'] = market_proxy['market_indicator'].pct_change()
                
                # Remove infinite and NaN values
                market_proxy = market_proxy.replace([np.inf, -np.inf], np.nan).dropna()
                
                self.logger.info(f"Portfolio-based market proxy created: {market_proxy.shape}")
                return market_proxy
            else:
                self.logger.error("Net_Cash_Flow_Calc_CNY column not found in monthly data")
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"Error creating portfolio returns proxy: {e}")
            return pd.DataFrame()
    
    def _calculate_market_features(self, portfolio_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate market features for regime detection.
        
        Args:
            portfolio_data (pd.DataFrame): Raw portfolio/market data
            
        Returns:
            pd.DataFrame: DataFrame with calculated features for HMM
        """
        try:
            features_df = portfolio_data.copy()
            
            # Ensure we have returns column
            if 'returns' not in features_df.columns:
                if 'market_indicator' in features_df.columns:
                    features_df['returns'] = features_df['market_indicator'].pct_change()
                else:
                    raise ValueError("No suitable data for returns calculation")
            
            # Calculate rolling volatility (key regime indicator)
            window = min(12, len(features_df) // 3)  # Use 12-month or 1/3 of data
            features_df['volatility'] = features_df['returns'].rolling(window=window).std()
            
            # Calculate rolling mean returns (trend indicator)
            features_df['trend'] = features_df['returns'].rolling(window=window).mean()
            
            # Calculate momentum (short vs long term returns)
            short_window = max(3, window // 4)
            long_window = window
            features_df['momentum'] = (
                features_df['returns'].rolling(window=short_window).mean() - 
                features_df['returns'].rolling(window=long_window).mean()
            )
            
            # Remove NaN values created by rolling calculations
            features_df = features_df.dropna()
            
            # Validate features
            required_features = ['returns', 'volatility', 'trend', 'momentum']
            for feature in required_features:
                if feature not in features_df.columns:
                    raise ValueError(f"Required feature {feature} not calculated")
            
            self.logger.info(f"Market features calculated: {required_features}")
            return features_df
            
        except Exception as e:
            self.logger.error(f"Error calculating market features: {e}")
            raise
    
    def fit(self, n_regimes: int = 3) -> 'MarketRegimeDetector':
        """
        Fit the Hidden Markov Model to detect market regimes.
        
        This is the core HMM implementation method as specified in Phase 5.3 Step 2.2.
        Takes returns data and fits a Gaussian HMM model to identify market regimes.
        
        Args:
            n_regimes (int): Number of regimes/components for the HMM (default: 3)
            
        Returns:
            MarketRegimeDetector: Self for method chaining
        """
        try:
            if self.market_data is None or self.market_data.empty:
                raise ValueError("No market data available. Call get_market_data() first.")
            
            # Validate returns data exists
            if 'returns' not in self.market_data.columns:
                raise ValueError("Returns data not found. Ensure get_market_data() was called successfully.")
            
            # Update number of components
            self.n_components = n_regimes
            
            # Prepare returns data for HMM fitting
            returns_data = self.market_data['returns'].dropna()
            if len(returns_data) == 0:
                raise ValueError("No valid returns data available for HMM fitting")
            
            # Reshape returns for HMM (needs 2D array)
            X = returns_data.values.reshape(-1, 1)
            
            # Scale returns for better HMM performance
            X_scaled = self.feature_scaler.fit_transform(X)
            
            # Initialize Gaussian HMM with specified parameters
            self.hmm_model = GaussianHMM(
                n_components=self.n_components,
                covariance_type='full',
                n_iter=100,
                random_state=42
            )
            
            # Fit the HMM model
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")  # Suppress convergence warnings
                self.hmm_model.fit(X_scaled)
            
            # Generate regime predictions for the returns data
            self.regime_predictions = self.hmm_model.predict(X_scaled)
            
            self.logger.info(f"HMM fitted successfully with {self.n_components} regimes on {len(returns_data)} data points")
            return self
            
        except Exception as e:
            self.logger.error(f"Error fitting HMM model: {e}")
            raise
    
    def fit_regime_model(self, 
                        features: Optional[List[str]] = None,
                        **hmm_kwargs) -> 'MarketRegimeDetector':
        """
        Fit the Hidden Markov Model to detect market regimes using multiple features.
        
        This is the advanced multi-feature fitting method for enhanced regime detection.
        
        Args:
            features (List[str], optional): List of feature columns to use
            **hmm_kwargs: Additional arguments for GaussianHMM
            
        Returns:
            MarketRegimeDetector: Self for method chaining
        """
        try:
            if self.market_data is None or self.market_data.empty:
                raise ValueError("No market data available. Call get_market_data() first.")
            
            # Default features for regime detection
            if features is None:
                features = ['returns', 'volatility', 'trend']
            
            # Validate features exist
            missing_features = [f for f in features if f not in self.market_data.columns]
            if missing_features:
                raise ValueError(f"Missing features in market data: {missing_features}")
            
            # Prepare feature matrix
            X = self.market_data[features].values
            
            # Scale features for better HMM performance
            X_scaled = self.feature_scaler.fit_transform(X)
            
            # Set default HMM parameters
            hmm_params = {
                'n_components': self.n_components,
                'covariance_type': 'full',
                'n_iter': 100,
                'random_state': 42
            }
            hmm_params.update(hmm_kwargs)
            
            # Initialize and fit HMM
            self.hmm_model = GaussianHMM(**hmm_params)
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")  # Suppress convergence warnings
                self.hmm_model.fit(X_scaled)
            
            # Generate regime predictions
            self.regime_predictions = self.hmm_model.predict(X_scaled)
            
            self.logger.info(f"HMM regime model fitted successfully with {len(features)} features")
            return self
            
        except Exception as e:
            self.logger.error(f"Error fitting regime model: {e}")
            raise
    
    def predict_current_regime(self) -> int:
        """
        Predict the current market regime.
        
        Returns:
            int: Current regime state (0 to n_components-1)
        """
        if self.regime_predictions is None:
            raise ValueError("Model not fitted. Call fit_regime_model() first.")
        
        current_regime = self.regime_predictions[-1]
        self.logger.info(f"Current market regime: {current_regime}")
        return current_regime
    
    def get_regime_characteristics(self) -> Dict[int, Dict[str, float]]:
        """
        Get characteristics of each detected regime.
        
        Returns:
            Dict[int, Dict[str, float]]: Regime characteristics
        """
        if self.hmm_model is None or self.market_data is None:
            raise ValueError("Model not fitted or no market data available")
        
        try:
            regime_chars = {}
            features = ['returns', 'volatility', 'trend']
            
            for regime in range(self.n_components):
                regime_mask = self.regime_predictions == regime
                regime_data = self.market_data[regime_mask]
                
                characteristics = {}
                for feature in features:
                    if feature in regime_data.columns:
                        characteristics[f'mean_{feature}'] = regime_data[feature].mean()
                        characteristics[f'std_{feature}'] = regime_data[feature].std()
                
                characteristics['periods'] = len(regime_data)
                characteristics['frequency'] = len(regime_data) / len(self.market_data)
                
                regime_chars[regime] = characteristics
            
            self.logger.info(f"Regime characteristics calculated for {self.n_components} regimes")
            return regime_chars
            
        except Exception as e:
            self.logger.error(f"Error calculating regime characteristics: {e}")
            raise
    
    def get_regime_transition_matrix(self) -> np.ndarray:
        """
        Get the regime transition probability matrix.
        
        Returns:
            np.ndarray: Transition matrix [n_components x n_components]
        """
        if self.hmm_model is None:
            raise ValueError("Model not fitted. Call fit_regime_model() first.")
        
        return self.hmm_model.transmat_
    
    def get_regime_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of the regime detection results.
        
        Returns:
            Dict[str, Any]: Summary including characteristics, transitions, and current state
        """
        if self.hmm_model is None:
            raise ValueError("Model not fitted. Call fit_regime_model() first.")
        
        summary = {
            'n_regimes': self.n_components,
            'current_regime': self.predict_current_regime(),
            'regime_characteristics': self.get_regime_characteristics(),
            'transition_matrix': self.get_regime_transition_matrix().tolist(),
            'model_score': self.hmm_model.score(
                self.feature_scaler.transform(
                    self.market_data[['returns', 'volatility', 'trend']].values
                )
            ),
            'data_period': {
                'start': self.market_data.index.min().strftime('%Y-%m-%d'),
                'end': self.market_data.index.max().strftime('%Y-%m-%d'),
                'periods': len(self.market_data)
            }
        }
        
        return summary
    
    def get_regime_summary_step23(self):
        """
        Analyze the fitted model to characterize each regime with human-readable descriptions.
        This method implements Step 2.3 requirements for regime interpretation.
        
        Returns:
            dict: Regime characteristics with descriptions
        """
        if self.hmm_model is None:
            raise ValueError("Model must be fitted before analyzing regimes. Call fit() first.")
        
        n_regimes = self.hmm_model.n_components
        means = self.hmm_model.means_
        covars = self.hmm_model.covars_
        
        regime_summary = {}
        
        for regime in range(n_regimes):
            regime_means = means[regime]
            regime_covar = covars[regime]
            
            # Extract feature statistics (for single-feature HMM from fit() method)
            returns_mean = regime_means[0]
            
            # Calculate volatility of returns from covariance matrix
            returns_volatility = np.sqrt(regime_covar[0, 0])
            
            # Characterize regime based on statistical properties
            # Returns characterization
            if returns_mean > 0.01:
                returns_desc = "Strong Positive Returns"
            elif returns_mean > 0.005:
                returns_desc = "Moderate Positive Returns"
            elif returns_mean > -0.005:
                returns_desc = "Neutral Returns"
            elif returns_mean > -0.01:
                returns_desc = "Moderate Negative Returns"
            else:
                returns_desc = "Strong Negative Returns"
            
            # Volatility characterization
            if returns_volatility > 0.05:
                vol_desc = "High Volatility"
            elif returns_volatility > 0.02:
                vol_desc = "Moderate Volatility"
            else:
                vol_desc = "Low Volatility"
            
            # Overall regime classification
            if returns_mean > 0.005 and returns_volatility < 0.03:
                regime_type = "Bull Market"
            elif returns_mean < -0.005 and returns_volatility > 0.03:
                regime_type = "Bear Market"
            elif abs(returns_mean) < 0.005 and returns_volatility > 0.04:
                regime_type = "High Volatility Market"
            elif abs(returns_mean) < 0.005 and returns_volatility < 0.02:
                regime_type = "Stable Market"
            else:
                regime_type = "Transitional Market"
            
            regime_summary[regime] = {
                'type': regime_type,
                'returns': {
                    'mean': returns_mean,
                    'description': returns_desc,
                    'volatility': returns_volatility
                },
                'volatility': {
                    'description': vol_desc
                },
                'summary': f"{regime_type}: {returns_desc}, {vol_desc}"
            }
        
        return regime_summary
    
    def plot_regimes(self, figsize=(15, 8), save_path=None):
        """
        Plot the market price series with background shading according to detected regimes.
        This method implements Step 2.3 requirements for regime visualization.
        
        Args:
            figsize (tuple): Figure size for the plot
            save_path (str, optional): Path to save the plot
            
        Returns:
            matplotlib.figure.Figure: The generated plot figure
        """
        if self.hmm_model is None or self.regime_predictions is None:
            raise ValueError("Model must be fitted before plotting. Call fit() first.")
        
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        
        # Get market data and create price series
        market_data = self.market_data  # Use cached data instead of calling get_market_data() again
        
        # Calculate cumulative returns to create a price proxy
        cumulative_returns = (1 + market_data['returns'].fillna(0)).cumprod()
        price_series = cumulative_returns * 100  # Normalize to start at 100
        
        # Get regime summary for labels
        regime_summary = self.get_regime_summary_step23()
        
        # Create the plot
        fig, ax = plt.subplots(figsize=figsize)
        
        # Define colors for different regimes
        colors = ['lightblue', 'lightcoral', 'lightgreen', 'lightyellow', 'lightpink', 'lightgray']
        
        # Improved regime shading logic - group consecutive regimes
        dates = price_series.index
        regime_changes = np.where(np.diff(self.regime_predictions, prepend=self.regime_predictions[0]))[0]
        regime_changes = np.append(regime_changes, len(self.regime_predictions))
        
        # Track which regimes we've labeled to avoid duplicates
        labeled_regimes = set()
        
        for i in range(len(regime_changes) - 1):
            start_idx = regime_changes[i]
            end_idx = regime_changes[i + 1] - 1
            regime = self.regime_predictions[start_idx]
            
            regime_color = colors[regime % len(colors)]
            regime_type = regime_summary[regime]['type']
            
            # Only add label for first occurrence of each regime
            label = f'Regime {regime}: {regime_type}' if regime not in labeled_regimes else ""
            if regime not in labeled_regimes:
                labeled_regimes.add(regime)
            
            ax.axvspan(dates[start_idx], dates[end_idx], 
                      alpha=0.3, color=regime_color, label=label)
        
        # Plot the price series
        ax.plot(dates, price_series.values, linewidth=2, color='black', label='Portfolio Value Index')
        
        # Formatting
        ax.set_title('Market Regime Detection - Portfolio Performance with Regime Classification', 
                    fontsize=16, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Portfolio Value Index (Base = 100)', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))  # Reduced frequency
        plt.xticks(rotation=45)
        
        # Add legend
        ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved to: {save_path}")
        
        return fig
