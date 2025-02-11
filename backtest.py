import pandas as pd
import streamlit as st
from vcp_detection import is_valid_vcp  # ✅ Fixed Circular Import
from market import market_breadth_score
from scanner import fetch_stock_data

# ✅ Fetch Sector Performance Data
def fetch_sector_data(ticker):
    """Get sector ETF performance for sector-relative comparison."""
    sector_map = {
        "AAPL": "XLK", "MSFT": "XLK", "NVDA": "XLK",  # Tech
        "XOM": "XLE", "CVX": "XLE",  # Energy
        "JPM": "XLF", "GS": "XLF",  # Financials
        "PFE": "XLV", "JNJ": "XLV"  # Healthcare
    }
    sector_ticker = sector_map.get(ticker, "SPY")  # Default to SPY if unknown

    df = fetch_stock_data(sector_ticker, days=200)
    return df if df is not None else None

# ✅ Define a Successful Breakout
def is_successful_breakout(df, entry_price, breakout_days=10, target_gain=0.1):
    """Check if stock reached 10% gain within X days after VCP setup."""
    future_prices = df[df.index > entry_price].head(breakout_days)
    max_future_gain = (future_prices["c"].max() - entry_price) / entry_price
    return max_future_gain >= target_gain

# ✅ Run Backtest on Past VCP Setups
def backtest_vcp(tickers, start_date="2023-01-01", end_date="2023-12-31"):
    """Backtest historical VCP setups and measure success rates."""
    results = []

    for ticker in tickers:
        df = fetch_stock_data(ticker, days=365)
        if df is None or len(df) < 200:
            continue

        df = df.loc[start_date:end_date]
        vcp_score = is_valid_vcp(ticker)

        if vcp_score > 50:
            entry_price = df["c"].iloc[-1]  # Entry at last closing price
            breakout_success = is_successful_breakout(df, entry_price)

            # ✅ Market Strength Filtering
            market_strength = market_breadth_score()
            if market_strength < 60:  
                continue  # Skip weak markets

            # ✅ Sector Performance Filtering
            sector_df = fetch_sector_data(ticker)
            if sector_df is not None:
                sector_performance = df["c"].pct_change().sum() > sector_df["c"].pct_change().sum()
                if not sector_performance:
                    continue  # Skip stocks underperforming their sector

            # ✅ Calculate Time-to-Breakout
            breakout_dates = df[df["c"] >= entry_price * 1.1].index  
            days_to_breakout = (breakout_dates[0] - df.index[-1]).days if not breakout_dates.empty else None

            results.append({
                "Stock": ticker,
                "VCP Score": vcp_score,
                "Breakout Success": breakout_success,
                "Market Strength": market_strength,
                "Outperformed Sector": sector_performance,
                "Days to Breakout": days_to_breakout
            })

    df_results = pd.DataFrame(results)
    success_rate = df_results["Breakout Success"].mean() * 100

    return success_rate, df_results

