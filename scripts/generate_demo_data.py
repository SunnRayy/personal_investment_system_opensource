#!/usr/bin/env python3
"""
Generate Multi-File Demo Data for Personal Investment System

This script creates a complete set of demo data files in data/demo_source/
matching the system's expected file structure with assets that map correctly
to the asset taxonomy.

Usage:
    python scripts/generate_demo_data.py
    python scripts/generate_demo_data.py --seed 42  # Reproducible data

Generated files:
    - data/demo_source/Financial_Summary_Demo.xlsx (Balance Sheet + Monthly Cash Flow)
    - data/demo_source/funding_transactions.xlsx (CN Fund Holdings + Transactions)
    - data/demo_source/Gold_transactions.xlsx (Gold Holdings + Transactions)
    - data/demo_source/Insurance_Portfolio.xlsx (Insurance Summary + Premiums)
    - data/demo_source/RSU_transactions.xlsx (RSU/Stock Comp Transactions)
    - data/demo_source/Individual-Positions-Demo.csv (US Brokerage Holdings)
    - data/demo_source/Individual_XXXX1234_Transactions_Demo.csv (US Brokerage Transactions)
    - data/historical_snapshots/*.xlsx (Monthly portfolio snapshots for charts)

Key improvements:
    1. Uses assets mapped in config/asset_taxonomy.yaml
    2. Financial Summary has correct 3 header rows for system parsing
    3. Transaction buy/sell balance ensures positive holdings
    4. Generates historical snapshots for time-series charts
    5. Creates a diversified portfolio showing realistic growth
"""

import os
import sys
import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from collections import defaultdict

import pandas as pd
import numpy as np

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# =============================================================================
# Demo Asset Definitions - Assets mapped in asset_taxonomy.yaml
# =============================================================================

# US Brokerage Assets (Schwab) - All mapped to correct categories
US_ASSETS = {
    # Equity (股票 - US Equity)
    'VOO': {'name': 'Vanguard S&P 500 ETF', 'type': 'US Stock ETF', 'base_price': 420, 'volatility': 0.015, 'trend': 0.0003},
    'VTI': {'name': 'Vanguard Total Stock Market ETF', 'type': 'US Stock ETF', 'base_price': 230, 'volatility': 0.015, 'trend': 0.0003},
    'QQQ': {'name': 'Invesco QQQ Trust', 'type': 'US Stock ETF', 'base_price': 380, 'volatility': 0.020, 'trend': 0.0004},
    # International Diversification
    'VEA': {'name': 'Vanguard Developed Markets ETF', 'type': 'International ETF', 'base_price': 50, 'volatility': 0.012, 'trend': 0.0002},
    'IEMG': {'name': 'iShares Emerging Markets ETF', 'type': 'Emerging Markets ETF', 'base_price': 52, 'volatility': 0.018, 'trend': 0.0001},
    # Fixed Income (固定收益 - 美国政府债券)
    'BND': {'name': 'Vanguard Total Bond Market ETF', 'type': 'Bond ETF', 'base_price': 72, 'volatility': 0.004, 'trend': 0.0001},
    'AGG': {'name': 'iShares Core US Aggregate Bond ETF', 'type': 'Bond ETF', 'base_price': 98, 'volatility': 0.004, 'trend': 0.0001},
    # Real Estate (房地产信托)
    'VNQ': {'name': 'Vanguard Real Estate ETF', 'type': 'REIT', 'base_price': 85, 'volatility': 0.015, 'trend': 0.0002},
    # Commodities (商品 - 黄金)
    'GLD': {'name': 'SPDR Gold Shares', 'type': 'Gold ETF', 'base_price': 175, 'volatility': 0.010, 'trend': 0.0002},
    # Alternative (另类投资 - 加密货币)
    'FBTC': {'name': 'Fidelity Wise Origin Bitcoin Fund', 'type': 'Bitcoin ETF', 'base_price': 48, 'volatility': 0.040, 'trend': 0.0006},
}

# Special Assets - Mapped in asset_taxonomy.yaml (USD values)
SPECIAL_ASSETS = {
    'Property_Residential_A': {'value': 500000, 'type': 'Real Estate', 'sub_class': '住宅地产'},
    'Employer_Stock_A': {'shares': 200, 'price': 185, 'type': 'RSU', 'sub_class': 'US Equity'},
    'Paper_Gold': {'grams': 50, 'price_per_gram': 75, 'type': 'Gold', 'sub_class': '黄金'},  # ~$75/gram in USD
    'Insurance_Policy_A': {'annual_premium': 2000, 'cash_value': 5000, 'type': 'Life Insurance'},
    'Insurance_Policy_B': {'annual_premium': 1200, 'cash_value': 2500, 'type': 'Health Insurance'},
}


# =============================================================================
# Price Generation Utilities
# =============================================================================

def generate_price_history(base_price: float, volatility: float, days: int, trend: float = 0.0002) -> List[float]:
    """Generate realistic price history using geometric Brownian motion with trend."""
    prices = [base_price]
    for _ in range(days - 1):
        daily_return = np.random.normal(trend, volatility)
        new_price = prices[-1] * (1 + daily_return)
        prices.append(max(new_price, base_price * 0.3))  # Floor at 30% of base
    return prices


def build_price_cache(assets: Dict, start_date: datetime, days: int) -> Dict[str, Dict[datetime, float]]:
    """Build price cache for all assets over date range."""
    cache = {}
    for symbol, info in assets.items():
        base = info.get('base_price') or info.get('base_nav', 100)
        vol = info.get('volatility', 0.015)
        trend = info.get('trend', 0.0002)
        prices = generate_price_history(base, vol, days, trend)
        cache[symbol] = {start_date + timedelta(days=i): prices[i] for i in range(days)}
    return cache


def get_price_for_date(cache: Dict, symbol: str, date: datetime, fallback: float) -> float:
    """Get price for a specific date, with nearest date fallback."""
    if symbol in cache:
        if date in cache[symbol]:
            return cache[symbol][date]
        # Find nearest date
        dates = sorted(cache[symbol].keys())
        for d in dates:
            if d >= date:
                return cache[symbol][d]
        if dates:
            return cache[symbol][dates[-1]]
    return fallback


# =============================================================================
# Balance Sheet and Cash Flow Generators
# =============================================================================

def generate_financial_summary(start_date: datetime, end_date: datetime, num_periods: int = 24) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate Financial Summary Excel content with 3 header rows:
    - Balance Sheet (monthly snapshots)
    - Monthly Cash Flow (income/expenses)

    The data format matches what the system expects (header on row 3).
    """
    dates = pd.date_range(start=start_date, end=end_date, periods=num_periods)

    # ===== Balance Sheet =====
    balance_data = []

    # Starting values with realistic growth trajectory (USD)
    base_values = {
        'Asset_Cash': 5000,
        'Asset_Checking': 8000,
        'Asset_Savings': 25000,
        'Asset_Brokerage': 120000,  # Will show investment growth
        'Asset_Retirement': 180000,  # Will show steady growth
        'Asset_Real_Estate': 500000,
        'Liability_Credit_Card': 2500,
        'Liability_Mortgage': 350000,
    }

    values = base_values.copy()

    for i, date in enumerate(dates):
        # Simulate realistic monthly changes with upward trend
        month_factor = i / num_periods  # 0 to ~1 over the period

        # Cash fluctuates
        values['Asset_Cash'] = base_values['Asset_Cash'] * (1 + 0.3 * month_factor + random.uniform(-0.1, 0.15))
        values['Asset_Checking'] = base_values['Asset_Checking'] * (1 + random.uniform(-0.05, 0.1))

        # Savings grows steadily
        values['Asset_Savings'] = base_values['Asset_Savings'] * (1 + 0.08 * month_factor + random.uniform(-0.01, 0.02))

        # Brokerage shows investment growth (~15% annual)
        monthly_return = random.uniform(-0.03, 0.05)  # Monthly variance
        if i > 0:
            values['Asset_Brokerage'] *= (1 + monthly_return + 0.01)  # Base 1% monthly growth + variance

        # Retirement grows steadily (~8% annual with contributions)
        values['Asset_Retirement'] = base_values['Asset_Retirement'] * (1 + 0.12 * month_factor + random.uniform(-0.02, 0.03))

        # Real estate appreciates slowly
        values['Asset_Real_Estate'] = base_values['Asset_Real_Estate'] * (1 + 0.04 * month_factor)

        # Credit card varies
        values['Liability_Credit_Card'] = max(0, 2000 + random.uniform(-500, 1500))

        # Mortgage decreases with payments
        values['Liability_Mortgage'] = max(0, base_values['Liability_Mortgage'] - (1500 * i))  # ~$1500/month principal

        balance_data.append({
            'Date': date.strftime('%Y-%m-%d'),
            'Asset_Cash': round(values['Asset_Cash'], 2),
            'Asset_Checking': round(values['Asset_Checking'], 2),
            'Asset_Savings': round(values['Asset_Savings'], 2),
            'Asset_Brokerage': round(values['Asset_Brokerage'], 2),
            'Asset_Retirement': round(values['Asset_Retirement'], 2),
            'Asset_Real_Estate': round(values['Asset_Real_Estate'], 2),
            'Liability_Credit_Card': round(values['Liability_Credit_Card'], 2),
            'Liability_Mortgage': round(values['Liability_Mortgage'], 2),
        })

    balance_df = pd.DataFrame(balance_data)

    # ===== Monthly Cash Flow =====
    cashflow_data = []
    base_salary = 8000  # Monthly salary in USD

    for i, date in enumerate(dates):
        # Salary with occasional raises
        salary = base_salary * (1 + 0.03 * (i // 6))  # 3% raise every 6 months
        salary *= (1 + random.uniform(-0.02, 0.02))  # Small variance

        # Quarterly bonus (10% of base salary)
        bonus = salary * 0.3 if (i + 1) % 3 == 0 else 0

        # Investment income grows with portfolio
        dividends = 150 + (i * 15) + random.uniform(-30, 60)  # Growing dividends
        interest = 80 + (i * 8) + random.uniform(-15, 30)

        # Expenses with seasonal variation (USD)
        housing = 2500 + random.uniform(-100, 100)
        utilities = 200 + random.uniform(-50, 80) + (50 if i % 12 in [0, 1, 6, 7] else 0)  # Higher in winter/summer
        groceries = 600 + random.uniform(-80, 120)
        transportation = 350 + random.uniform(-50, 100)
        healthcare = 150 + random.uniform(0, 250)  # Occasional higher expenses
        entertainment = 300 + random.uniform(-80, 200)
        invest_brokerage = 1000 + random.uniform(-200, 500)  # Monthly investment contribution

        cashflow_data.append({
            'Date': date.strftime('%Y-%m-%d'),
            'Income_Salary': round(salary, 2),
            'Income_Bonus': round(bonus, 2),
            'Income_Dividends': round(dividends, 2),
            'Income_Interest': round(interest, 2),
            'Expense_Housing': round(housing, 2),
            'Expense_Utilities': round(utilities, 2),
            'Expense_Groceries': round(groceries, 2),
            'Expense_Transportation': round(transportation, 2),
            'Expense_Healthcare': round(healthcare, 2),
            'Expense_Entertainment': round(entertainment, 2),
            'Outflow_Invest_Brokerage': round(invest_brokerage, 2),
        })

    cashflow_df = pd.DataFrame(cashflow_data)

    return balance_df, cashflow_df


def write_financial_summary_excel(output_path: str, balance_df: pd.DataFrame, cashflow_df: pd.DataFrame):
    """
    Write Financial Summary Excel with proper 3 header rows.
    The system expects header on row 3 (0-indexed), so we add title rows.
    """
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Balance Sheet - add 3 header rows
        balance_with_headers = pd.DataFrame([
            {'Date': 'Personal Investment System - Balance Sheet'},
            {'Date': f'Generated: {datetime.now().strftime("%Y-%m-%d")}'},
            {'Date': ''},  # Empty row before header
        ])
        balance_with_headers.to_excel(writer, sheet_name='Balance Sheet', index=False, header=False)
        balance_df.to_excel(writer, sheet_name='Balance Sheet', index=False, startrow=3)

        # Monthly Cash Flow - add 3 header rows
        cashflow_with_headers = pd.DataFrame([
            {'Date': 'Personal Investment System - Monthly Cash Flow'},
            {'Date': f'Generated: {datetime.now().strftime("%Y-%m-%d")}'},
            {'Date': ''},
        ])
        cashflow_with_headers.to_excel(writer, sheet_name='Monthly Cash Flow', index=False, header=False)
        cashflow_df.to_excel(writer, sheet_name='Monthly Cash Flow', index=False, startrow=3)


# =============================================================================
# Gold Data Generator
# =============================================================================

def generate_gold_data(start_date: datetime, end_date: datetime) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Generate Gold data with balanced buy/sell transactions (USD values)."""
    gold_price_base = 75  # USD per gram (~2400/oz)

    # Track gold holdings
    gold_grams = 0
    transactions_data = []
    date_range = (end_date - start_date).days

    # Generate gold prices over time (trending up)
    gold_prices = generate_price_history(gold_price_base * 0.85, 0.008, date_range + 1, 0.0002)
    price_by_day = {start_date + timedelta(days=i): gold_prices[i] for i in range(len(gold_prices))}

    # Generate transactions (mostly buys)
    for _ in range(15):
        txn_date = start_date + timedelta(days=random.randint(0, date_range))

        # 75% buy, 25% sell
        if random.random() < 0.75 or gold_grams < 10:
            txn_type = 'Buy'
            grams = round(random.uniform(3, 10), 2)
            gold_grams += grams
        else:
            txn_type = 'Sell'
            grams = round(min(gold_grams * 0.3, random.uniform(2, 5)), 2)
            gold_grams -= grams

        # Get price for date
        price = price_by_day.get(txn_date, gold_price_base)

        transactions_data.append({
            'Transaction_Date': txn_date.strftime('%Y-%m-%d'),
            'Asset_Name': 'Paper_Gold',
            'Transaction_Type_Raw': txn_type,
            'Quantity': grams,
            'Price_Unit': round(price, 2),
            'Amount_Gross': round(grams * price, 2),
            'Commission_Fee': round(grams * price * 0.001, 2),
            'Account': 'Bank_A',
            'Currency': 'USD'
        })

    transactions_df = pd.DataFrame(transactions_data)
    transactions_df = transactions_df.sort_values('Transaction_Date').reset_index(drop=True)

    # Current holdings
    current_price = gold_prices[-1]
    avg_cost = gold_price_base * 0.92  # Assume bought at slightly lower average

    holdings_data = [{
        'Asset_Name': 'Paper_Gold',
        'Quantity': max(gold_grams, 50),  # Minimum 50g for display
        'Unit': 'Gram',
        'Cost_Price_Unit': round(avg_cost, 2),
        'Market_Price_Unit': round(current_price, 2),
        'Market_Value_Raw': round(max(gold_grams, 50) * current_price, 2),
        'Account': 'Bank_A',
        'Currency': 'USD'
    }]

    holdings_df = pd.DataFrame(holdings_data)

    return holdings_df, transactions_df


# =============================================================================
# Insurance Data Generator
# =============================================================================

def generate_insurance_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Generate Insurance portfolio with realistic policies (USD values)."""
    summary_data = [
        {
            'Asset_Name': 'Insurance_Policy_A',
            'Insurance_Company': 'Insurance_Co_A',
            'Asset_Type_Raw': 'Life Insurance',
            'Policy_Start_Date': '2020-01-15',
            'Coverage_Term_Raw': '30 Years',
            'Payment_Term_Raw': '20 Years',
            'Annual_Premium': 2000,
            'Sum_Insured': 500000,
            'Coverage_Scope': 'Life + Critical Illness',
            'Policy_Status': 'Active',
            'Currency': 'USD'
        },
        {
            'Asset_Name': 'Insurance_Policy_B',
            'Insurance_Company': 'Insurance_Co_B',
            'Asset_Type_Raw': 'Health Insurance',
            'Policy_Start_Date': '2021-06-01',
            'Coverage_Term_Raw': 'Annual Renewal',
            'Payment_Term_Raw': 'Annual',
            'Annual_Premium': 1200,
            'Sum_Insured': 100000,
            'Coverage_Scope': 'Medical + Dental',
            'Policy_Status': 'Active',
            'Currency': 'USD'
        }
    ]
    summary_df = pd.DataFrame(summary_data)

    # Generate premium payments for past 4 years
    premiums_data = []
    for year in range(2022, 2027):
        for policy_name, premium in [('Insurance_Policy_A', 2000), ('Insurance_Policy_B', 1200)]:
            premiums_data.append({
                'Date': f'{year}-01-15',
                'Policy': policy_name,
                'Amount': premium,
                'Currency': 'USD',
                'Status': 'Paid' if year < 2026 else 'Due'
            })

    premiums_df = pd.DataFrame(premiums_data)

    return summary_df, premiums_df


# =============================================================================
# RSU Data Generator
# =============================================================================

def generate_rsu_data(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Generate RSU transactions with quarterly vesting schedule."""
    transactions_data = []

    vest_dates = pd.date_range(start=start_date, end=end_date, freq='QE')
    base_price = 175
    total_vested = 0
    total_sold = 0

    # Generate stock price history
    price_history = generate_price_history(base_price, 0.020, (end_date - start_date).days + 1, 0.0003)

    for i, vest_date in enumerate(vest_dates):
        # Vest event - increasing grants over time
        shares_vested = random.randint(25, 45) + (i * 2)
        day_idx = (vest_date.to_pydatetime() - start_date).days
        price = price_history[min(day_idx, len(price_history) - 1)]

        total_vested += shares_vested

        transactions_data.append({
            'Transaction_Date': vest_date.strftime('%Y-%m-%d'),
            'Asset_Name': 'Employer_Stock_A',
            'Transaction_Type_Raw': 'RSU Vest',
            'Quantity': shares_vested,
            'Unit': 'Shares',
            'Price_Unit': round(price, 2),
            'Amount_Gross': round(shares_vested * price, 2),
            'Commission_Fee': 0,
            'Currency': 'USD',
            'Memo': 'Quarterly vest'
        })

        # Occasional tax sell (30% of vest, only if enough shares)
        if random.random() < 0.4 and total_vested - total_sold > 30:
            sell_date = vest_date + timedelta(days=random.randint(5, 20))
            if sell_date <= end_date:
                sell_shares = min(shares_vested // 3, total_vested - total_sold - 20)
                if sell_shares > 0:
                    day_idx = (sell_date - start_date).days
                    sell_price = price_history[min(day_idx, len(price_history) - 1)]
                    total_sold += sell_shares

                    transactions_data.append({
                        'Transaction_Date': sell_date.strftime('%Y-%m-%d'),
                        'Asset_Name': 'Employer_Stock_A',
                        'Transaction_Type_Raw': 'Sell',
                        'Quantity': sell_shares,
                        'Unit': 'Shares',
                        'Price_Unit': round(sell_price, 2),
                        'Amount_Gross': round(sell_shares * sell_price, 2),
                        'Commission_Fee': round(sell_shares * sell_price * 0.001, 2),
                        'Currency': 'USD',
                        'Memo': 'Tax sell'
                    })

    transactions_df = pd.DataFrame(transactions_data)
    transactions_df = transactions_df.sort_values('Transaction_Date').reset_index(drop=True)

    return transactions_df


# =============================================================================
# Schwab Data Generator
# =============================================================================

def generate_schwab_data(start_date: datetime, end_date: datetime, price_cache: Dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Generate Schwab brokerage data with balanced transactions."""

    # Track holdings per symbol
    holdings_tracker = defaultdict(float)

    # Generate transactions first
    transactions_data = []
    date_range = (end_date - start_date).days

    # Initial purchases at the start
    for symbol, info in US_ASSETS.items():
        initial_date = start_date + timedelta(days=random.randint(0, 30))
        price = get_price_for_date(price_cache, symbol, initial_date, info['base_price'])
        quantity = round(random.uniform(15, 40))
        holdings_tracker[symbol] = quantity

        transactions_data.append({
            'Date': initial_date.strftime('%m/%d/%Y'),
            'Action': 'Buy',
            'Symbol': symbol,
            'Description': info['name'],
            'Quantity': quantity,
            'Price': f"${price:.2f}",
            'Fees & Comm': f"${price * quantity * 0.0005:.2f}",
            'Amount': f"-${price * quantity:.2f}"
        })

    # Generate ongoing transactions (more buys than sells)
    for _ in range(80):
        txn_date = start_date + timedelta(days=random.randint(30, date_range))
        symbol = random.choice(list(US_ASSETS.keys()))
        info = US_ASSETS[symbol]

        action = random.choices(
            ['Buy', 'Sell', 'Reinvest Dividend', 'Qualified Dividend'],
            weights=[0.45, 0.15, 0.25, 0.15]
        )[0]

        price = get_price_for_date(price_cache, symbol, txn_date, info['base_price'])

        if action == 'Sell':
            # Only sell if we have sufficient holdings
            if holdings_tracker[symbol] > 10:
                quantity = round(min(holdings_tracker[symbol] * 0.2, random.uniform(3, 10)))
                holdings_tracker[symbol] -= quantity
            else:
                action = 'Buy'
                quantity = round(random.uniform(5, 15))
                holdings_tracker[symbol] += quantity
        elif action in ['Buy', 'Reinvest Dividend']:
            quantity = round(random.uniform(2, 12), 4) if 'Dividend' in action else round(random.uniform(5, 15))
            holdings_tracker[symbol] += quantity
        else:  # Qualified Dividend (cash)
            quantity = round(random.uniform(0.5, 3), 4)

        amount = round(price * quantity, 2)
        fees = round(amount * 0.0005, 2) if action in ['Buy', 'Sell'] else 0

        amount_str = f"-${amount:.2f}" if action == 'Buy' else f"${amount:.2f}"

        transactions_data.append({
            'Date': txn_date.strftime('%m/%d/%Y'),
            'Action': action,
            'Symbol': symbol,
            'Description': info['name'],
            'Quantity': quantity,
            'Price': f"${price:.2f}",
            'Fees & Comm': f"${fees:.2f}" if fees else "",
            'Amount': amount_str
        })

    transactions_df = pd.DataFrame(transactions_data)
    transactions_df['_sort_date'] = pd.to_datetime(transactions_df['Date'], format='%m/%d/%Y')
    transactions_df = transactions_df.sort_values('_sort_date').drop('_sort_date', axis=1).reset_index(drop=True)

    # Generate Holdings based on tracked holdings
    holdings_data = []
    for symbol, info in US_ASSETS.items():
        price = get_price_for_date(price_cache, symbol, end_date, info['base_price'])
        quantity = max(holdings_tracker[symbol], random.uniform(15, 35))  # Ensure positive holdings
        value = round(price * quantity, 2)
        cost = round(value * random.uniform(0.75, 0.95), 2)  # Cost basis lower (showing gains)

        holdings_data.append({
            'Symbol': symbol,
            'Description': info['name'],
            'Quantity': round(quantity),
            'Price': f"${price:.2f}",
            'Market Value': f"${value:,.2f}",
            'Cost Basis': f"${cost:,.2f}",
            'Day Change $': f"${random.uniform(-30, 50):.2f}",
            'Day Change %': f"{random.uniform(-1.5, 2):.2f}%"
        })

    holdings_df = pd.DataFrame(holdings_data)

    return holdings_df, transactions_df


# =============================================================================
# Historical Snapshots Generator
# =============================================================================

def generate_historical_snapshots(output_dir: str, start_date: datetime, end_date: datetime,
                                   us_cache: Dict) -> int:
    """Generate monthly historical snapshots for time-series charts (USD only)."""

    snapshots_dir = os.path.join(output_dir, '..', 'historical_snapshots')
    os.makedirs(snapshots_dir, exist_ok=True)

    # Generate monthly snapshots
    snapshot_dates = pd.date_range(start=start_date, end=end_date, freq='ME')

    for snap_date in snapshot_dates:
        snapshot_data = []
        snap_dt = snap_date.to_pydatetime()

        # US Assets (including international ETFs)
        for symbol, info in US_ASSETS.items():
            price = get_price_for_date(us_cache, symbol, snap_dt, info['base_price'])
            quantity = round(random.uniform(20, 50) * (1 + (snap_date - snapshot_dates[0]).days / 365 * 0.3))

            snapshot_data.append({
                'Snapshot_Date': snap_date.strftime('%Y-%m-%d'),
                'Asset_ID': symbol,
                'Asset_Name': info['name'],
                'Asset_Class': info['type'],
                'Quantity': round(quantity, 2),
                'Price': round(price, 2),
                'Market_Value': round(quantity * price, 2),
                'Currency': 'USD'
            })

        # Gold (USD)
        gold_price = 75 * (1 + (snap_date - snapshot_dates[0]).days / 365 * 0.08)  # USD per gram
        gold_qty = 30 + (snap_date - snapshot_dates[0]).days / 30 * 2
        snapshot_data.append({
            'Snapshot_Date': snap_date.strftime('%Y-%m-%d'),
            'Asset_ID': 'Paper_Gold',
            'Asset_Name': 'Paper Gold',
            'Asset_Class': 'Gold',
            'Quantity': round(gold_qty, 2),
            'Price': round(gold_price, 2),
            'Market_Value': round(gold_qty * gold_price, 2),
            'Currency': 'USD'
        })

        snapshot_df = pd.DataFrame(snapshot_data)
        snapshot_path = os.path.join(snapshots_dir, f"snapshot_{snap_date.strftime('%Y%m')}.xlsx")
        snapshot_df.to_excel(snapshot_path, index=False)

    return len(snapshot_dates)


# =============================================================================
# Main Generator
# =============================================================================

def generate_all_demo_data(output_dir: str = None, seed: int = None) -> str:
    """
    Generate complete demo dataset with multiple files.

    Args:
        output_dir: Output directory. Defaults to data/demo_source/
        seed: Random seed for reproducibility

    Returns:
        Path to output directory
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    if output_dir is None:
        output_dir = os.path.join(PROJECT_ROOT, 'data', 'demo_source')

    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("  GENERATING DEMO DATA FOR PERSONAL INVESTMENT SYSTEM")
    print("=" * 70)
    print(f"Output directory: {output_dir}")
    print()

    # Date range: 2 years of history
    end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=730)
    days = (end_date - start_date).days + 1

    # Build price cache for US assets with realistic trends
    print("Building price history...")
    us_price_cache = build_price_cache(US_ASSETS, start_date, days)

    # 1. Financial Summary (with correct 3 header rows and calculator-compatible columns)
    print("Generating Financial_Summary_Demo.xlsx (with Asset_/Liability_/Income_/Expense_ columns)...")
    balance_df, cashflow_df = generate_financial_summary(start_date, end_date)
    write_financial_summary_excel(
        os.path.join(output_dir, 'Financial_Summary_Demo.xlsx'),
        balance_df, cashflow_df
    )
    print(f"   Balance Sheet: {len(balance_df)} rows")
    print(f"   Monthly Cash Flow: {len(cashflow_df)} rows")

    # 2. Gold Data (USD)
    print("Generating Gold_transactions.xlsx...")
    gold_holdings_df, gold_txn_df = generate_gold_data(start_date, end_date)
    with pd.ExcelWriter(os.path.join(output_dir, 'Gold_transactions.xlsx'), engine='openpyxl') as writer:
        gold_holdings_df.to_excel(writer, sheet_name='Holdings', index=False)
        gold_txn_df.to_excel(writer, sheet_name='Transactions', index=False)
    print(f"   Gold Holdings: {len(gold_holdings_df)} positions")
    print(f"   Gold Transactions: {len(gold_txn_df)} records")

    # 3. Insurance Data (USD)
    print("Generating Insurance_Portfolio.xlsx...")
    ins_summary_df, ins_premiums_df = generate_insurance_data()
    with pd.ExcelWriter(os.path.join(output_dir, 'Insurance_Portfolio.xlsx'), engine='openpyxl') as writer:
        ins_summary_df.to_excel(writer, sheet_name='Summary', index=False)
        ins_premiums_df.to_excel(writer, sheet_name='Premiums', index=False)
    print(f"   Insurance Summary: {len(ins_summary_df)} policies")
    print(f"   Premiums: {len(ins_premiums_df)} payments")

    # 4. RSU Data
    print("Generating RSU_transactions.xlsx...")
    rsu_df = generate_rsu_data(start_date, end_date)
    with pd.ExcelWriter(os.path.join(output_dir, 'RSU_transactions.xlsx'), engine='openpyxl') as writer:
        rsu_df.to_excel(writer, sheet_name='Transactions', index=False)
    print(f"   RSU Transactions: {len(rsu_df)} records")

    # 5. Schwab Data (US ETFs including international diversification)
    print("Generating Schwab CSV files...")
    schwab_holdings_df, schwab_txn_df = generate_schwab_data(start_date, end_date, us_price_cache)

    # Schwab Holdings with account header
    schwab_holdings_path = os.path.join(output_dir, 'Individual-Positions-Demo.csv')
    with open(schwab_holdings_path, 'w') as f:
        f.write(f'"Positions for account Demo Account XXXX-1234 as of {end_date.strftime("%m/%d/%Y")}"\n')
        f.write('""\n')
    schwab_holdings_df.to_csv(schwab_holdings_path, mode='a', index=False)

    # Schwab Transactions
    schwab_txn_path = os.path.join(output_dir, 'Individual_XXXX1234_Transactions_Demo.csv')
    schwab_txn_df.to_csv(schwab_txn_path, index=False)

    print(f"   Schwab Holdings: {len(schwab_holdings_df)} positions")
    print(f"   Schwab Transactions: {len(schwab_txn_df)} records")

    # 6. Historical Snapshots (USD only)
    print("Generating historical snapshots...")
    num_snapshots = generate_historical_snapshots(output_dir, start_date, end_date, us_price_cache)
    print(f"   Historical Snapshots: {num_snapshots} monthly snapshots")

    # Summary
    print()
    print("=" * 70)
    print("  DEMO DATA GENERATION COMPLETE")
    print("=" * 70)
    print(f"Output directory: {output_dir}")
    print()
    print("Generated files:")
    for f in sorted(os.listdir(output_dir)):
        if not f.startswith('.'):
            size = os.path.getsize(os.path.join(output_dir, f))
            print(f"   {f} ({size:,} bytes)")
    print()
    print("Portfolio characteristics:")
    print("   - 10 US ETFs (VOO, VTI, QQQ, VEA, IEMG, BND, AGG, VNQ, GLD, FBTC)")
    print("   - Gold holdings (Paper Gold)")
    print("   - Insurance policies (2)")
    print("   - RSU/Stock compensation")
    print("   - Real estate (simulated in balance sheet)")
    print()
    print("Run 'python main.py run-all' to generate reports with this demo data.")
    print("=" * 70)

    return output_dir


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate multi-file demo data for testing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Generate with random data
    python scripts/generate_demo_data.py

    # Generate with specific seed for reproducibility
    python scripts/generate_demo_data.py --seed 42

    # Generate to custom location
    python scripts/generate_demo_data.py --output data/my_demo/
"""
    )

    parser.add_argument(
        '--output', '-o',
        help='Output directory (default: data/demo_source/)'
    )

    parser.add_argument(
        '--seed', '-s',
        type=int,
        help='Random seed for reproducibility'
    )

    args = parser.parse_args()

    generate_all_demo_data(output_dir=args.output, seed=args.seed)


if __name__ == '__main__':
    main()
