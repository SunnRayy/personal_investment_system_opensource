# portfolio_lib/core/mpt.py
"""
Core Modern Portfolio Theory (MPT) model implementation.
Handles calculations for efficient frontier, optimal portfolios based on
various objectives (Sharpe ratio, min volatility), and risk profile portfolios.
Filters out assets with near-zero standard deviation before calculations.
Includes debugging prints for min_volatility optimization.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Dict, Any, Tuple, Optional, List

class AssetAllocationModel:
    """
    Modern Portfolio Theory (MPT) core model class.

    Performs calculations based on provided asset returns data.
    Filters out assets with near-zero standard deviation during initialization.
    Assumes input returns are monthly unless specified otherwise via annualization_factor.
    """

    def __init__(
        self,
        returns_data: pd.DataFrame,
        risk_free_rate: float = 0.02,
        annualization_factor: int = 12,
        std_dev_threshold: float = 1e-8
    ):
        """
        Initializes the MPT model, filtering low-variance assets.

        Args:
            returns_data: DataFrame with asset class returns (rows=time, cols=asset classes).
                          Assumed to be pre-cleaned (no NaNs).
            risk_free_rate: Annual risk-free rate.
            annualization_factor: Factor to annualize returns and volatility.
            std_dev_threshold: Minimum standard deviation required for an asset to be included.
        """
        if not isinstance(returns_data, pd.DataFrame) or returns_data.empty:
            raise ValueError("returns_data must be a non-empty pandas DataFrame.")
        if returns_data.isnull().values.any():
             # This check remains, but ideally NaNs are handled before passing data here.
             print("Warning: Input returns_data contains NaN values. Ensure they were handled appropriately before this step.")

        self.original_assets: List[str] = list(returns_data.columns)
        self.risk_free_rate: float = risk_free_rate
        self.annualization_factor: int = annualization_factor
        self.std_dev_threshold: float = std_dev_threshold

        # --- Filter Assets with Low Standard Deviation ---
        print(f"Filtering assets with standard deviation <= {self.std_dev_threshold:.1e}...")
        period_std_dev = returns_data.std()
        valid_assets_mask = period_std_dev > self.std_dev_threshold
        self.assets: List[str] = period_std_dev[valid_assets_mask].index.tolist()
        self.num_assets: int = len(self.assets)
        removed_assets = list(set(self.original_assets) - set(self.assets))

        if not self.assets:
             raise ValueError("No assets remaining after filtering for near-zero standard deviation.")
        if removed_assets:
            print(f"-> Removed assets: {removed_assets}")

        # Use only the filtered returns data for calculations
        self.returns: pd.DataFrame = returns_data[self.assets].copy() # Use .copy()

        # --- Calculate Statistics on Filtered Data ---
        self.mean_returns: pd.Series = self.returns.mean()
        self.cov_matrix: pd.DataFrame = self.returns.cov()

        self.mean_returns_annualized: pd.Series = self.mean_returns * self.annualization_factor
        self.cov_matrix_annualized: pd.DataFrame = self.cov_matrix * self.annualization_factor

        # Cache for calculated results
        self.efficient_frontier: Optional[pd.DataFrame] = None
        self.risk_profiles: Optional[Dict[str, Dict[str, Any]]] = None
        self._optimization_cache: Dict[str, Any] = {}

        print(f"MPT Model Initialized:")
        print(f"  - Included Assets ({self.num_assets}): {self.assets}")
        print(f"  - Risk-Free Rate: {self.risk_free_rate:.2%}")
        print(f"  - Annualization Factor: {self.annualization_factor}x")
        if self.num_assets < 2:
             print("Warning: Only one asset remains after filtering. MPT optimization may not be meaningful.")

    def calculate_correlation_matrix(self) -> pd.DataFrame:
        """Calculates and returns the asset correlation matrix for included assets."""
        return self.returns.corr()

    def portfolio_performance(self, weights: np.ndarray) -> Tuple[float, float, float]:
        """
        Calculates the annualized expected return, volatility, and Sharpe ratio for given weights.
        Assumes weights correspond to the filtered self.assets list.

        Args:
            weights: Numpy array of asset weights (length must match self.num_assets).

        Returns:
            A tuple: (annualized_return, annualized_volatility, sharpe_ratio).
        """
        if not isinstance(weights, np.ndarray):
            weights = np.array(weights)
        if len(weights) != self.num_assets:
             raise ValueError(f"Length of weights ({len(weights)}) must match number of included assets ({self.num_assets})")

        annualized_return = np.sum(self.mean_returns_annualized * weights)
        # Use the annualized covariance matrix
        variance = np.dot(weights.T, np.dot(self.cov_matrix_annualized, weights))
        annualized_volatility = np.sqrt(max(0, variance)) # Ensure non-negative

        denominator = annualized_volatility
        if denominator < 1e-9:
            sharpe_ratio = 0.0 if annualized_return >= self.risk_free_rate else -np.inf
            # Only warn if variance wasn't exactly zero, to avoid noise
            if variance > 1e-12:
                 # This warning might appear during optimization steps, can be noisy
                 # print(f"Debug Warning: Calculated portfolio volatility is near zero ({annualized_volatility:.2e}). Sharpe ratio may be unreliable.")
                 pass
        else:
            sharpe_ratio = (annualized_return - self.risk_free_rate) / denominator

        return annualized_return, annualized_volatility, sharpe_ratio

    # --- Optimization Helper Functions ---
    def _neg_sharpe(self, weights: np.ndarray) -> float:
        """Objective function for maximizing Sharpe ratio (minimize negative Sharpe)."""
        sharpe = self.portfolio_performance(weights)[2]
        # Return large positive number if Sharpe is -inf to guide optimizer away
        return -sharpe if np.isfinite(sharpe) else 1e9

    def _portfolio_volatility(self, weights: np.ndarray) -> float:
        """Objective function for minimizing volatility."""
        return self.portfolio_performance(weights)[1]

    def _portfolio_return(self, weights: np.ndarray) -> float:
         """Calculates portfolio return (used for constraints)."""
         # Uses annualized mean returns for consistency with target return definition
         return np.sum(self.mean_returns_annualized * weights)

    # --- Core Optimization ---
    def optimize_portfolio(
        self,
        objective: str = 'sharpe',
        target_return: Optional[float] = None,
        constraints: Tuple = (),
        bounds: Optional[Tuple[Tuple[float, float], ...]] = None
    ) -> Dict[str, Any]:
        """
        Optimizes portfolio weights for the included assets based on the specified objective.

        Args:
            objective: Optimization goal ('sharpe' for max Sharpe, 'min_volatility').
            target_return: Required for 'min_volatility' when a specific return is targeted (annualized).
            constraints: Additional constraints for the optimizer (SLSQP format).
            bounds: Bounds for asset weights (default is 0 to 1 for all).

        Returns:
            Dictionary containing optimal weights and portfolio performance metrics.
        """
        cache_key = f"{objective}_{target_return}_{constraints}_{bounds}"
        if cache_key in self._optimization_cache:
            # print(f"Using cached result for {cache_key}") # Optional debug
            return self._optimization_cache[cache_key]

        num_assets = self.num_assets
        if num_assets == 0: raise ValueError("No assets available for optimization.")
        # Handle single asset case directly
        if num_assets == 1:
             print("Warning: Only one asset available. Optimization result will be 100% allocation.")
             weight = np.array([1.0]); ann_ret, ann_vol, sharpe = self.portfolio_performance(weight)
             optimal_portfolio = {'weights': {self.assets[0]: 1.0}, 'returns': ann_ret, 'volatility': ann_vol, 'sharpe': sharpe, 'success': True, 'message': 'Optimization skipped for single asset.'}
             self._optimization_cache[cache_key] = optimal_portfolio
             return optimal_portfolio

        args = ()
        if bounds is None: bounds = tuple((0.0, 1.0) for _ in range(num_assets))
        base_constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})
        all_constraints = list(constraints) + [base_constraints]
        init_guess = np.array([1.0 / num_assets] * num_assets)

        # Select objective function and add target return constraint if needed
        if objective == 'min_volatility':
            opt_func = self._portfolio_volatility
            # --- Add Debug Prints Here ---
            print(f"\n--- Debug: Optimizing for Min Volatility ---")
            print(f"Target Return Constraint: {'Yes' if target_return is not None else 'No'}")
            if target_return is not None:
                print(f"  Target Return Value: {target_return:.4%}")
                return_constraint = ({'type': 'eq', 'fun': lambda w: self._portfolio_return(w) - target_return})
                all_constraints.append(return_constraint)
            print(f"  Included Assets ({num_assets}): {self.assets}")
            print(f"  Initial Guess: {[f'{x:.2f}' for x in init_guess]}")
            # print(f"Bounds: {bounds}") # Can be verbose
            # print(f"Constraints: {all_constraints}") # Can be verbose
            print(f"  Annualized Mean Returns:\n{self.mean_returns_annualized.to_string(float_format='%.4f')}")
            print(f"  Annualized Covariance Matrix:\n{self.cov_matrix_annualized.to_string(float_format='%.6f')}") # More precision for cov
            init_ret, init_vol, init_sharpe = self.portfolio_performance(init_guess)
            print(f"  Initial Guess Performance: Ret={init_ret:.2%}, Vol={init_vol:.2%}, Sharpe={init_sharpe:.2f}")
            print(f"--- End Debug: Optimizing for Min Volatility ---")
            # --- End Debug Prints ---
        elif objective == 'sharpe':
            opt_func = self._neg_sharpe
        else:
            raise ValueError("Objective must be 'sharpe' or 'min_volatility'")

        # Perform optimization
        try:
            result = minimize(
                opt_func, init_guess, method='SLSQP', args=args,
                bounds=bounds, constraints=tuple(all_constraints),
                options={'ftol': 1e-9, 'disp': False} # Set disp=True for detailed optimizer output
            )
        except ValueError as ve:
             # Catch potential issues like inconsistent bounds/constraints
             print(f"Error during optimization call for objective '{objective}': {ve}")
             # Provide more context if possible
             print(f"Optimizer Inputs: func={opt_func.__name__}, init_guess={init_guess}, bounds={bounds}, constraints={all_constraints}")
             # Return a failure dictionary
             return {'weights': {}, 'returns': np.nan, 'volatility': np.nan, 'sharpe': np.nan, 'success': False, 'message': f"Optimization ValueError: {ve}"}
        except Exception as e:
             print(f"Unexpected error during optimization for objective '{objective}': {e}")
             raise # Re-raise unexpected errors

        # Process optimization results
        if not result.success:
            print(f"Warning: Optimization failed for objective '{objective}'. Message: {result.message}")
            # Use the potentially non-optimal weights, but clean and normalize
            optimal_weights = result.x
        else:
            optimal_weights = result.x

        # Clean near-zero weights and re-normalize
        optimal_weights[np.abs(optimal_weights) < 1e-7] = 0.0
        sum_w = np.sum(optimal_weights)
        if abs(sum_w) > 1e-6: # Avoid division by zero if all weights became zero
            optimal_weights = optimal_weights / sum_w
        else:
            # If all weights are zero after cleaning, maybe distribute equally as fallback?
            print("Warning: All weights near zero after cleaning. Resetting to equal weights.")
            optimal_weights = np.array([1.0 / num_assets] * num_assets)


        # Calculate performance of the final weights
        ann_ret, ann_vol, sharpe = self.portfolio_performance(optimal_weights)

        optimal_portfolio = {
            'weights': {self.assets[i]: weight for i, weight in enumerate(optimal_weights)},
            'returns': ann_ret,
            'volatility': ann_vol,
            'sharpe': sharpe,
            'success': result.success,
            'message': result.message
        }
        self._optimization_cache[cache_key] = optimal_portfolio
        return optimal_portfolio

    # --- Efficient Frontier Calculation ---
    def calculate_efficient_frontier(self, points: int = 50) -> Optional[pd.DataFrame]:
        """Calculates points along the efficient frontier for included assets."""
        print(f"Calculating Efficient Frontier ({points} points) for {self.num_assets} included assets...")
        if self.num_assets <= 1:
             print("Cannot calculate frontier with one or zero assets.")
             if self.num_assets == 1:
                  weight = np.array([1.0]); ann_ret, ann_vol, _ = self.portfolio_performance(weight)
                  self.efficient_frontier = pd.DataFrame({'returns': [ann_ret], 'volatility': [ann_vol]})
                  return self.efficient_frontier
             return None
        try:
            # Use optimize_portfolio which includes error handling/warnings
            min_vol_portfolio = self.optimize_portfolio(objective='min_volatility')
            max_sharpe_portfolio = self.optimize_portfolio(objective='sharpe')

            # Proceed only if base optimizations were somewhat successful
            if not min_vol_portfolio or not max_sharpe_portfolio:
                 print("Error: Failed to calculate base min_vol or max_sharpe portfolios.")
                 return None
            # It's okay if success=False, we might still get a range, but warn
            if not min_vol_portfolio['success']: print("Warning: Min Vol optimization may not have fully converged.")
            if not max_sharpe_portfolio['success']: print("Warning: Max Sharpe optimization may not have fully converged.")

            min_ret = min_vol_portfolio['returns']
            max_ret = max_sharpe_portfolio['returns']

            # Check for NaN returns (can happen if optimization failed badly)
            if pd.isna(min_ret) or pd.isna(max_ret):
                 print("Error: NaN return found in min_vol or max_sharpe portfolio. Cannot calculate frontier.")
                 return None

            # Handle edge case: Min return >= Max Sharpe return
            if min_ret >= max_ret - 1e-6: # Use tolerance
                 print("Warning: Min volatility return >= Max Sharpe return. Frontier calculation might be limited.")
                 # Check if points are distinct enough to plot
                 if abs(min_vol_portfolio['volatility'] - max_sharpe_portfolio['volatility']) > 1e-6 or abs(min_ret - max_ret) > 1e-6:
                      frontier_data = {'returns': [min_ret, max_ret], 'volatility': [min_vol_portfolio['volatility'], max_sharpe_portfolio['volatility']]}
                      self.efficient_frontier = pd.DataFrame(frontier_data).sort_values(by='volatility').reset_index(drop=True)
                      print("Returning limited frontier (MinVol, MaxSharpe).")
                      return self.efficient_frontier
                 else:
                      print("Min Volatility and Max Sharpe portfolios are nearly identical. Returning single point.")
                      self.efficient_frontier = pd.DataFrame({'returns': [min_ret], 'volatility': [min_vol_portfolio['volatility']]})
                      return self.efficient_frontier

            # Generate target returns for the frontier calculation
            target_returns = np.linspace(min_ret, max_ret, points) # Go exactly from min to max achieved

            frontier_volatility = []
            frontier_returns = [] # Store actual returns achieved

            for target in target_returns:
                # Find the portfolio with minimum volatility for this target return
                portfolio = self.optimize_portfolio(objective='min_volatility', target_return=target)
                # Include the point even if optimization didn't fully succeed, but check for NaNs
                if portfolio and pd.notna(portfolio['volatility']) and pd.notna(portfolio['returns']):
                    frontier_volatility.append(portfolio['volatility'])
                    frontier_returns.append(portfolio['returns'])
                # else: # Optionally log skipped points
                #    print(f"  Skipping point for target return {target:.2%} due to optimization failure or NaN result.")

            if not frontier_volatility:
                 print("Error: Failed to calculate any valid points for the efficient frontier.")
                 return None

            # Create DataFrame, sort, and remove duplicates
            frontier_df = pd.DataFrame({'returns': frontier_returns, 'volatility': frontier_volatility})
            frontier_df = frontier_df.sort_values(by='volatility').drop_duplicates(subset=['volatility'], keep='first').reset_index(drop=True)

            self.efficient_frontier = frontier_df
            print("Efficient Frontier calculation complete.")
            return self.efficient_frontier

        except Exception as e:
            print(f"Error calculating efficient frontier: {e}")
            import traceback
            print(traceback.format_exc())
            return None

    # --- Risk Profiles Calculation ---
    def calculate_risk_profiles(
        self,
        risk_profile_names: List[str] = ['保守型', '均衡型', '进取型']
        ) -> Optional[Dict[str, Dict[str, Any]]]:
        """Calculates specific portfolios for risk profiles using included assets."""
        print(f"Calculating Risk Profile Portfolios for {self.num_assets} included assets...")
        profiles: Dict[str, Dict[str, Any]] = {}
        # Handle case with only one asset
        if self.num_assets <= 1:
             print("Cannot calculate distinct risk profiles with one or zero assets.")
             if self.num_assets == 1:
                  weight = np.array([1.0]); ann_ret, ann_vol, sharpe = self.portfolio_performance(weight)
                  single_profile = {'weights': {self.assets[0]: 1.0}, 'returns': ann_ret, 'volatility': ann_vol, 'sharpe': sharpe, 'success': True, 'message': 'Single asset portfolio.'}
                  for name in risk_profile_names: profiles[name] = single_profile
                  self.risk_profiles = profiles; return self.risk_profiles
             return None
        try:
            min_vol_portfolio = self.optimize_portfolio(objective='min_volatility')
            max_sharpe_portfolio = self.optimize_portfolio(objective='sharpe')

            # Check if base portfolios are valid before proceeding
            if not min_vol_portfolio or not max_sharpe_portfolio:
                 print("Error: Failed to calculate base portfolios for risk profiles.")
                 return None

            if '保守型' in risk_profile_names:
                profiles['保守型'] = min_vol_portfolio
                print(f"  - 保守型 (Min Vol): Success={min_vol_portfolio.get('success', False)}")

            if '均衡型' in risk_profile_names:
                profiles['均衡型'] = max_sharpe_portfolio
                print(f"  - 均衡型 (Max Sharpe): Success={max_sharpe_portfolio.get('success', False)}")

            if '进取型' in risk_profile_names:
                # Calculate frontier first if needed
                if self.efficient_frontier is None:
                    print("Calculating efficient frontier for Aggressive profile target...")
                    self.calculate_efficient_frontier()

                # Determine max achievable return
                max_frontier_return = -np.inf # Default to negative infinity
                if self.efficient_frontier is not None and not self.efficient_frontier.empty:
                     max_frontier_return = self.efficient_frontier['returns'].max()

                # Use Max Sharpe return as fallback if frontier failed or is invalid
                max_achievable_return = max(max_frontier_return, max_sharpe_portfolio.get('returns', -np.inf))

                # Ensure Max Sharpe return is valid before calculating target
                max_sharpe_return = max_sharpe_portfolio.get('returns')
                if max_sharpe_return is None or pd.isna(max_sharpe_return):
                     print("Error: Max Sharpe return is invalid. Cannot calculate Aggressive profile.")
                     aggressive_portfolio = max_sharpe_portfolio # Fallback
                else:
                     # Target 20% higher return, capped reasonably below max achievable
                     aggressive_target_return = min(max_sharpe_return * 1.2, max_achievable_return * 0.995)

                     if aggressive_target_return > max_sharpe_return + 1e-5: # Only if meaningfully higher
                          aggressive_portfolio = self.optimize_portfolio(
                               objective='min_volatility',
                               target_return=aggressive_target_return
                          )
                          if not aggressive_portfolio or not aggressive_portfolio.get('success'):
                               print(f"  - 进取型: Optimization failed for target {aggressive_target_return:.2%}. Falling back to Max Sharpe.")
                               aggressive_portfolio = max_sharpe_portfolio # Fallback
                          else:
                               print(f"  - 进取型 (Target Ret={aggressive_target_return:.2%}): Success={aggressive_portfolio['success']}")
                     else:
                          print("  - 进取型: Target return not significantly higher than Max Sharpe, using Max Sharpe portfolio.")
                          aggressive_portfolio = max_sharpe_portfolio

                profiles['进取型'] = aggressive_portfolio

            self.risk_profiles = profiles
            print("Risk Profile calculation complete.")
            return self.risk_profiles
        except Exception as e:
            print(f"Error calculating risk profiles: {e}")
            import traceback
            print(traceback.format_exc())
            return None

    # --- Recommendation ---
    def recommend_allocation(self, risk_preference: str = '成长型') -> Optional[Dict[str, Any]]:
        """Recommends an allocation based on a specified risk preference using included assets."""
        if self.risk_profiles is None:
            print("Risk profiles not calculated yet. Calculating...")
            if self.calculate_risk_profiles() is None:
                 print("Error: Failed to calculate risk profiles for recommendation.")
                 return None
        if self.risk_profiles is None: # Check again
             print("Error: Risk profiles are still None after calculation attempt.")
             return None

        if risk_preference not in self.risk_profiles:
            print(f"Error: Risk preference '{risk_preference}' not found in calculated profiles ({list(self.risk_profiles.keys())}).")
            # Fallback logic - prefer Growth profile first, then Balanced
            fallback_profile = '成长型' if '成长型' in self.risk_profiles else ('均衡型' if '均衡型' in self.risk_profiles else (list(self.risk_profiles.keys())[0] if self.risk_profiles else None))
            if fallback_profile:
                 print(f"Falling back to '{fallback_profile}'.")
                 risk_preference = fallback_profile
            else:
                 print("Error: No risk profiles available to recommend.")
                 return None

        recommended_portfolio = self.risk_profiles[risk_preference]

        # Ensure weights dictionary exists and is not empty
        weights_dict = recommended_portfolio.get('weights', {})
        if not weights_dict:
             print(f"Warning: No weights found for risk profile '{risk_preference}'.")

        # Format weights for display string
        formatted_weights = {
            asset: f"{weight:.2%}"
            for asset, weight in weights_dict.items()
            # Optionally filter very small weights for display string
            # if abs(weight) > 1e-4
        }

        # Compile the recommendation dictionary
        recommendation = {
            'risk_profile': risk_preference,
            'allocation_pct_str': formatted_weights, # Formatted string weights
            'allocation_float': weights_dict,       # Raw float weights
            'expected_return': recommended_portfolio.get('returns'),
            'expected_risk': recommended_portfolio.get('volatility'),
            'sharpe_ratio': recommended_portfolio.get('sharpe'),
            'success': recommended_portfolio.get('success', False) # Include success flag
        }
        return recommendation

