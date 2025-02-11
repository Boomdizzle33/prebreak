from scanner import is_valid_vcp, fetch_stock_data
import pandas as pd
from datetime import datetime, timedelta

# ✅ Define a Successful Breakout
def is_successful_breakout(df, entry_price, breakout_days=10, target_gain=0.1):
    future_prices = df[df.index > entry_price].head(breakout_days)
    max_future_gain = (future_prices["c"].max() - entry_price) / entry_price
    return max_future_gain >= target_gain  # ✅ Returns True if breakout happened

# ✅ Run Backtest on Past VCP Setups
def backtest_vcp(tickers, start_date="2023-01-01", end_date="2023-12-31"):
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

            results.append({
                "Stock": ticker,
                "VCP Score": vcp_score,
                "Breakout Success": breakout_success
            })

    df_results = pd.DataFrame(results)
    success_rate = df_results["Breakout Success"].mean() * 100

    return success_rate, df_results

# ✅ Run Backtest (Example)
if __name__ == "__main__":
    tickers = ["AAPL", "TSLA", "NVDA", "MSFT"]
    success_rate, results = backtest_vcp(tickers)
    print(f"🔥 VCP Success Rate: {success_rate:.2f}%")
    print(results)
