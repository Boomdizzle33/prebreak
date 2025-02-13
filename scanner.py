import streamlit as st
import pandas as pd
import numpy as np
import requests
import ta
from datetime import datetime, timedelta
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

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
            return df
    except Exception as e:
        st.error(f"❌ Error fetching data for {ticker}: {e}")
        return pd.DataFrame()

# ✅ Market Breadth Filter (SPX % above 50-SMA)
def fetch_market_breadth():
    sp500 = fetch_stock_data("SPY", days=365)
    sp500["Above_50SMA"] = sp500["Close"] > sp500["Close"].rolling(50).mean()
    return sp500["Above_50SMA"].mean()

# ✅ Check Relative Strength vs SPY
def fetch_relative_strength(ticker, benchmark="SPY"):
    df_stock = fetch_stock_data(ticker, days=365)
    df_benchmark = fetch_stock_data(benchmark, days=365)

    if df_stock.empty or df_benchmark.empty:
        return None

    df_stock["RS"] = df_stock["Close"] / df_benchmark["Close"]
    df_stock["RS_Trend"] = df_stock["RS"].rolling(20).mean().diff()
    return df_stock["RS_Trend"].iloc[-1] > 0

# ✅ VCP Detection with Debugging
def is_valid_vcp(ticker):
    df = fetch_stock_data(ticker, days=365)
    if df.empty or len(df) < 200:
        return 0

    try:
        df = df.sort_index(ascending=True)

        # ✅ Calculate SMAs
        df["50_SMA"] = df["Close"].rolling(50, min_periods=1).mean()
        df["200_SMA"] = df["Close"].rolling(200, min_periods=1).mean()
        df.dropna(subset=["50_SMA", "200_SMA"], inplace=True)

        in_trend = df["Close"].iloc[-1] > df["50_SMA"].iloc[-1] and df["Close"].iloc[-1] >= (df["200_SMA"].iloc[-1] * 0.95)

        # ✅ ATR Calculation (Less Strict)
        df["ATR"] = ta.volatility.AverageTrueRange(df["High"], df["Low"], df["Close"], window=14).average_true_range()
        df["ATR_Contraction"] = df["ATR"].rolling(50).mean() / df["ATR"]
        is_tight = df["ATR_Contraction"].iloc[-1] >= 2.0

        # ✅ Volume Contraction (Less Strict)
        df["Volume_MA"] = df["Volume"].rolling(20, min_periods=1).mean()
        df["Volume_Contraction"] = (df["Volume"] < df["Volume_MA"] * 0.7).astype(int)

        df["Pivot_Level"] = df["Close"].rolling(20).max()
        is_near_pivot = df["Close"].iloc[-1] >= df["Pivot_Level"].iloc[-1] * 0.95

        relative_strength = fetch_relative_strength(ticker)

        # ✅ Final VCP Score
        vcp_score = (is_tight * 0.3) + (df["Volume_Contraction"].iloc[-1] * 0.1) + (is_near_pivot * 0.3) + (in_trend * 0.2) + (relative_strength * 0.1)

        return round(vcp_score * 100, 2)
    except Exception as e:
        st.error(f"❌ Error processing VCP for {ticker}: {e}")
        return 0

# ✅ Backtesting Function (2:1 Risk-Reward)
def backtest_vcp(ticker, vcp_score):
    df = fetch_stock_data(ticker, days=365)
    if df.empty:
        return None

    try:
        df["ATR"] = ta.volatility.AverageTrueRange(df["High"], df["Low"], df["Close"], window=14).average_true_range()
        entry_price = df["Close"].iloc[-1]
        stop_loss = entry_price - (1.5 * df["ATR"].iloc[-1])
        target_price = entry_price + (3 * (entry_price - stop_loss))  # ✅ 2:1 Risk-Reward

        max_future_price = df["Close"].iloc[-10:].max()
        success = max_future_price >= target_price

        return {
            "Stock": ticker,
            "VCP Score": vcp_score,
            "Entry Price": round(entry_price, 2),
            "Stop Loss": round(stop_loss, 2),
            "Target Price": round(target_price, 2),
            "Max Future Price": round(max_future_price, 2),
            "Success": success
        }
    except Exception as e:
        st.error(f"❌ Error during backtesting for {ticker}: {e}")
        return None

# ✅ Streamlit UI
st.set_page_config(page_title="🚀 Minervini VCP Scanner", layout="wide")
st.title("🚀 Minervini VCP Scanner (Pre-Market Trade Prep)")

uploaded_file = st.file_uploader("📂 Upload TradingView Watchlist (CSV)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    stocks = df["Ticker"].dropna().tolist() if "Ticker" in df.columns else []

    st.subheader("🔍 Scanning TradingView Watchlist for VCP Setups...")
    progress_bar = st.progress(0)

    results = []
    backtest_results = []
    
    for i, stock in enumerate(stocks):
        vcp_score = is_valid_vcp(stock)
        progress_bar.progress((i + 1) / len(stocks))

        if vcp_score >= 40:
            backtest_result = backtest_vcp(stock, vcp_score)
            if backtest_result:
                results.append(backtest_result)
                backtest_results.append(backtest_result)

    progress_bar.empty()
    
    st.subheader("📊 Backtest Results")
    if backtest_results:
        st.dataframe(pd.DataFrame(backtest_results))
    else:
        st.warning("⚠️ No valid VCP setups found in backtest.")



