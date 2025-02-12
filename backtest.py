import pandas as pd
import numpy as np
import ta
import yfinance as yf
import streamlit as st
from datetime import datetime, timedelta
from vcp_detection import is_valid_vcp

# ✅ Fetch historical stock data for backtesting
def fetch_stock_data(ticker, days=365):
    """Fetch historical stock data using Yahoo Finance for backtesting."""
    try:
        end_date = datetime.today()
        start_date = end_date - timedelta(days=days)
        df = yf.download(ticker, start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"))
        
        if df.empty:
            print(f"⚠️ No data available for {ticker}")
            return None
        
        # ✅ Rename columns to match expected format
        df = df.rename(columns={"Open": "o", "High": "h", "Low": "l", "Close": "c", "Volume": "v"})
        df.index = pd.to_datetime(df.index)

        # ✅ Ensure ATR Calculation
        df["ATR"] = ta.volatility.AverageTrueRange(high=df["h"], low=df["l"], close=df["c"], window=14).average_true_range()
        if df["ATR"].isna().all():
            print(f"⚠️ ATR calculation failed for {ticker} (All NaN values)")
            return None
        
        return df

    except Exception as e:
        print(f"❌ Error fetching data for {ticker}: {e}")
        return None

# ✅ Backtest function to evaluate past VCP performance
def backtest_vcp(tickers):
    """Backtests VCP setups on historical data and evaluates success rates."""
    backtest_results = []

    for ticker in tickers:
        df = fetch_stock_data(ticker, days=365)
        if df is None or df.empty:
            continue

        vcp_score = is_valid_vcp(ticker)
        if vcp_score < 50:  # ✅ Only consider strong VCP setups
            continue  

        try:
            entry_price = df["c"].iloc[-1]  # Assume entry at last close price
            
            # ✅ Ensure ATR exists and is valid before using it
            if "ATR" not in df.columns or df["ATR"].isna().all():
                print(f"⚠️ Skipping {ticker} - ATR missing or invalid")
                continue

            atr_value = df["ATR"].iloc[-1]
            stop_loss = entry_price - (2 * atr_value)  # 2x ATR Stop Loss
            target_price = entry_price + (4 * atr_value)  # 4x ATR Target
            max_future_price = df["c"].iloc[-10:].max()  # Look at next 10 days

            # ✅ Determine success: Did price reach target before stop-loss?
            success = max_future_price >= target_price

            backtest_results.append({
                "Stock": ticker,
                "VCP Score": vcp_score,
                "Entry Price": round(entry_price, 2),
                "Stop Loss": round(stop_loss, 2),
                "Target Price": round(target_price, 2),
                "Max Future Price": round(max_future_price, 2),
                "Success": success
            })

        except Exception as e:
            print(f"❌ Error processing {ticker} during backtest: {e}")
            continue

    # ✅ Convert results to DataFrame
    df_results = pd.DataFrame(backtest_results)

    # ✅ Calculate win rate
    win_rate = df_results["Success"].mean() * 100 if not df_results.empty else 0

    return win_rate, df_results

# ✅ Streamlit Output for Backtesting Results
def display_backtest_results(tickers):
    """Runs backtest and displays results in Streamlit."""
    st.subheader("📊 Running Backtest on VCP Stocks...")
    win_rate, df_results = backtest_vcp(tickers)

    if not df_results.empty:
        st.subheader(f"🔥 VCP Historical Success Rate: {win_rate:.2f}%")
        st.dataframe(df_results)

        # ✅ Provide CSV export for TradingView
        df_results.to_csv("TradingView_Export.csv", index=False)
        with open("TradingView_Export.csv", "rb") as f:
            st.download_button(label="⬇ Download CSV", data=f, file_name="TradingView_Export.csv")

    else:
        st.warning("❌ No valid VCP setups detected in the backtest period.")

# ✅ If running standalone, test with sample tickers
if __name__ == "__main__":
    test_tickers = ["AAPL", "NVDA", "MSFT", "TSLA", "AMZN"]
    display_backtest_results(test_tickers)

    

