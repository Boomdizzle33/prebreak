import streamlit as st
import pandas as pd
import numpy as np
import requests
import ta
from datetime import datetime, timedelta
from functools import lru_cache

# ✅ Secure API Key Handling
POLYGON_API_KEY = st.secrets.get("POLYGON_API_KEY", "YOUR_POLYGON_API_KEY")

# ✅ Fetch stock data with Debugging
@lru_cache(maxsize=100)
def fetch_stock_data(ticker, days=365):
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}?adjusted=true&sort=asc&apiKey={POLYGON_API_KEY}"

        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if "results" in data and data["results"]:
            df = pd.DataFrame(data["results"])
            df['date'] = pd.to_datetime(df['t'], unit='ms')
            df.set_index('date', inplace=True)
            df.rename(columns={"o": "Open", "h": "High", "l": "Low", "c": "Close", "v": "Volume"}, inplace=True)

            # ✅ Check if all key columns exist
            if df[["Open", "High", "Low", "Close", "Volume"]].isnull().values.any():
                st.warning(f"⚠️ Missing data in {ticker}. Skipping...")
                return pd.DataFrame()
            return df
    except Exception as e:
        st.error(f"❌ Error fetching data for {ticker}: {e}")
        return pd.DataFrame()

# ✅ Debugging: Check Data Retrieval
def check_data_availability(ticker):
    df = fetch_stock_data(ticker, days=365)
    if df.empty:
        st.warning(f"⚠️ No data found for {ticker}. Skipping...")
    return df

# ✅ VCP Detection Algorithm with Debugging
def is_valid_vcp(ticker):
    df = check_data_availability(ticker)
    if df.empty:
        return 0

    try:
        df["ATR"] = ta.volatility.AverageTrueRange(df["High"], df["Low"], df["Close"], window=14).average_true_range()

        # ✅ Ensure ATR is not NaN
        if df["ATR"].isna().all():
            st.warning(f"⚠️ ATR not calculated for {ticker}. Skipping...")
            return 0

        df["ATR_Contraction"] = df["ATR"].rolling(50).mean() / df["ATR"]
        is_tight = df["ATR_Contraction"].iloc[-1] >= 2.5  # ✅ Reduced from 3.0

        df["Volume_MA"] = df["Volume"].rolling(20).mean()
        df["Volume_Contraction"] = (df["Volume"] < df["Volume_MA"] * 0.6).astype(int)  # ✅ Less strict filter

        df["Pivot_Level"] = df["Close"].rolling(20).max()
        is_near_pivot = df["Close"].iloc[-1] >= df["Pivot_Level"].iloc[-1] * 0.95  # ✅ Relaxed from 0.97

        df["50_SMA"] = df["Close"].rolling(50).mean()
        df["200_SMA"] = df["Close"].rolling(200).mean()
        in_trend = df["Close"].iloc[-1] > df["50_SMA"].iloc[-1] > df["200_SMA"].iloc[-1]

        vcp_score = (is_tight * 0.3) + (df["Volume_Contraction"].iloc[-1] * 0.1) + (is_near_pivot * 0.3) + (in_trend * 0.2)

        return round(vcp_score * 100, 2) if vcp_score > 30 else 0  # ✅ Lowered threshold to 30
    except Exception as e:
        st.error(f"❌ Error processing VCP for {ticker}: {e}")
        return 0

# ✅ Backtesting with Debugging
def backtest_vcp(ticker):
    df = check_data_availability(ticker)
    if df.empty:
        return None

    try:
        df["ATR"] = ta.volatility.AverageTrueRange(df["High"], df["Low"], df["Close"], window=14).average_true_range()
        if df["ATR"].isna().all():
            st.warning(f"⚠️ ATR not calculated for {ticker}. Skipping backtest...")
            return None

        entry_price = df["Close"].iloc[-1]
        stop_loss = entry_price - (1.5 * df["ATR"].iloc[-1])
        target_price = entry_price + (3 * (entry_price - stop_loss))  # ✅ 2:1 Risk-Reward

        max_future_price = df["Close"].iloc[-10:].max()
        success = max_future_price >= target_price

        return {
            "Stock": ticker,
            "Entry Price": round(entry_price, 2),
            "Stop Loss": round(stop_loss, 2),
            "Target Price": round(target_price, 2),
            "Max Future Price": round(max_future_price, 2),
            "Success": success
        }
    except Exception as e:
        st.error(f"❌ Error during backtesting for {ticker}: {e}")
        return None

# ✅ Streamlit UI with Progress Bar
st.set_page_config(page_title="🚀 Minervini VCP Scanner", layout="wide")
st.title("🚀 Minervini VCP Scanner (Pre-Market Trade Prep)")

uploaded_file = st.file_uploader("📂 Upload TradingView Watchlist (CSV)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    stocks = df["Ticker"].dropna().tolist() if "Ticker" in df.columns else []
    
    st.subheader("🔍 Scanning TradingView Watchlist for VCP Setups...")
    
    results = []
    backtest_results = []
    progress_bar = st.progress(0)  # ✅ Progress Bar
    
    for i, stock in enumerate(stocks):
        vcp_score = is_valid_vcp(stock)
        progress_bar.progress((i + 1) / len(stocks))  # ✅ Update Progress
        
        if vcp_score >= 30:  # ✅ Lower threshold
            backtest_result = backtest_vcp(stock)
            if backtest_result:
                backtest_result["VCP Score"] = vcp_score
                results.append(backtest_result)
                backtest_results.append(backtest_result)

    progress_bar.empty()  # ✅ Remove Progress Bar When Done
    
    st.subheader("🏆 Confirmed VCP Stocks (2:1 R:R)")
    if results:
        st.dataframe(pd.DataFrame(results))
    else:
        st.warning("⚠️ No valid VCP setups found.")

    st.subheader("📊 Backtest Results")
    if backtest_results:
        st.dataframe(pd.DataFrame(backtest_results))
    else:
        st.warning("⚠️ No valid VCP setups found in backtest.")


