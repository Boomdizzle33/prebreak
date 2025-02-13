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
            return df
    except Exception as e:
        st.error(f"❌ Error fetching data for {ticker}: {e}")
        return pd.DataFrame()

# ✅ VCP Detection Algorithm with Debugging Output
def is_valid_vcp(ticker):
    df = fetch_stock_data(ticker, days=250)
    if df.empty:
        return 0

    try:
        df["ATR"] = ta.volatility.AverageTrueRange(df["High"], df["Low"], df["Close"], window=14).average_true_range()
        df["ATR_Contraction"] = df["ATR"].rolling(50).mean() / df["ATR"]
        is_tight = df["ATR_Contraction"].iloc[-1] >= 2.5

        df["Volume_MA"] = df["Volume"].rolling(20).mean()
        df["Volume_Contraction"] = (df["Volume"] < df["Volume_MA"] * 0.6).astype(int)

        df["Pivot_Level"] = df["Close"].rolling(20).max()
        is_near_pivot = df["Close"].iloc[-1] >= df["Pivot_Level"].iloc[-1] * 0.95

        df["50_SMA"] = df["Close"].rolling(50).mean()
        df["200_SMA"] = df["Close"].rolling(200).mean()
        in_trend = df["Close"].iloc[-1] > df["50_SMA"].iloc[-1] > df["200_SMA"].iloc[-1]

        vcp_score = (is_tight * 0.3) + (df["Volume_Contraction"].iloc[-1] * 0.1) + (is_near_pivot * 0.3) + (in_trend * 0.2)
        
        # ✅ Show Debugging Output in Streamlit
        st.write(f"📊 **VCP Calculation for {ticker}**")
        st.write(f"📌 ATR Contraction: {df['ATR_Contraction'].iloc[-1]:.2f}")
        st.write(f"📌 Volume Contraction: {df['Volume_Contraction'].iloc[-1]}")
        st.write(f"📌 Near Pivot: {is_near_pivot}")
        st.write(f"📌 Trend Confirmation (50 & 200 SMA): {in_trend}")
        st.write(f"✅ Final VCP Score: {round(vcp_score * 100, 2)}")

        return round(vcp_score * 100, 2)
    except Exception as e:
        st.error(f"❌ Error processing VCP for {ticker}: {e}")
        return 0

# ✅ Backtesting with Score Debugging
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
            "VCP Score": vcp_score,  # ✅ Show Score
            "Entry Price": round(entry_price, 2),
            "Stop Loss": round(stop_loss, 2),
            "Target Price": round(target_price, 2),
            "Max Future Price": round(max_future_price, 2),
            "Success": success
        }
    except Exception as e:
        st.error(f"❌ Error during backtesting for {ticker}: {e}")
        return None

# ✅ Streamlit UI with Progress Bar & Debugging
st.set_page_config(page_title="🚀 Minervini VCP Scanner", layout="wide")
st.title("🚀 Minervini VCP Scanner (Pre-Market Trade Prep)")

uploaded_file = st.file_uploader("📂 Upload TradingView Watchlist (CSV)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    stocks = df["Ticker"].dropna().tolist() if "Ticker" in df.columns else []
    
    st.subheader("🔍 Scanning TradingView Watchlist for VCP Setups...")
    
    results = []
    near_vcp = []  # ✅ Track "Near VCP" setups
    backtest_results = []
    progress_bar = st.progress(0)  # ✅ Progress Bar
    
    for i, stock in enumerate(stocks):
        vcp_score = is_valid_vcp(stock)
        progress_bar.progress((i + 1) / len(stocks))  # ✅ Update Progress

        if vcp_score >= 40:  # ✅ Threshold lowered to 40
            backtest_result = backtest_vcp(stock, vcp_score)
            if backtest_result:
                results.append(backtest_result)
                backtest_results.append(backtest_result)
        elif 30 <= vcp_score < 40:  # ✅ "Near VCP" stocks
            near_vcp.append({"Stock": stock, "VCP Score": vcp_score})

    progress_bar.empty()  # ✅ Remove Progress Bar When Done

    # ✅ Display Top VCP Candidates
    st.subheader("🏆 Confirmed VCP Stocks (Sorted by Score)")
    if results:
        df_results = pd.DataFrame(results).sort_values(by="VCP Score", ascending=False)
        st.dataframe(df_results)
    else:
        st.warning("⚠️ No valid VCP setups found.")

    # ✅ Display "Near VCP" Stocks
    st.subheader("👀 Near-VCP Watchlist (Monitor These)")
    if near_vcp:
        df_near_vcp = pd.DataFrame(near_vcp).sort_values(by="VCP Score", ascending=False)
        st.dataframe(df_near_vcp)
    else:
        st.warning("⚠️ No Near-VCP stocks found.")

    # ✅ Display Backtest Results
    st.subheader("📊 Backtest Results")
    if backtest_results:
        st.dataframe(pd.DataFrame(backtest_results))
    else:
        st.warning("⚠️ No valid VCP setups found in backtest.")

