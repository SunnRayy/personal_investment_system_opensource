# portfolio_lib/utils/helpers.py
import pandas as pd # Import pandas for pd.isna check
from matplotlib.ticker import FuncFormatter

# Make 'pos' optional with a default value of None
def currency_formatter(x, pos=None):
    """Formats a number as currency (e.g., 1.2M, 350.5K, 100)."""
    if pd.isna(x): # Handle NaN values
         return ""
    # Ensure x is treated as a number, handle potential strings if necessary
    try:
        numeric_x = float(x)
    except (ValueError, TypeError):
        return str(x) # Return original string if not convertible

    abs_x = abs(numeric_x)
    sign = '-' if numeric_x < 0 else ''
    if abs_x >= 1e6:
        return f'{sign}{abs_x/1e6:.1f}M'
    elif abs_x >= 1e3:
        return f'{sign}{abs_x/1e3:.1f}K'
    else:
        # Use f-string formatting for integers, potentially show decimals for small non-integers
        if abs_x == int(abs_x):
             return f'{sign}{int(abs_x):,d}' # Format integers with commas
        else:
             return f'{sign}{abs_x:,.2f}' # Show decimals for non-integers


# Create a FuncFormatter instance for direct use with matplotlib axes
# This instance will correctly pass both x and pos when used by matplotlib
currency_format = FuncFormatter(currency_formatter)

# Add other general utility functions here if needed in the future
