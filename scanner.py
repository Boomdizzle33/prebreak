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
    df = fetch_stock_data(ticker, days=365)
    if df.empty or len(df) < 200:
        st.warning(f"⚠️ Not enough data for {ticker} (needs 200+ days). Skipping...")
        return 0

    try:
        df = df.sort_index(ascending=True)  # ✅ Ensure correct order

        # ✅ Calculate SMAs
        df["50_SMA"] = df["Close"].rolling(50, min_periods=1).mean()
        df["200_SMA"] = df["Close"].rolling(200, min_periods=1).mean()
        df.dropna(subset=["50_SMA", "200_SMA"], inplace=True)  # ✅ Fix NaN values

        # ✅ Trend Confirmation Fix
        in_trend = df["Close"].iloc[-1] > df["50_SMA"].iloc[-1] and df["Close"].iloc[-1] >= (df["200_SMA"].iloc[-1] * 0.97)

        # ✅ VCP Score Calculation
        df["ATR"] = ta.volatility.AverageTrueRange(df["High"], df["Low"], df["Close"], window=14).average_true_range()
        df["ATR_Contraction"] = df["ATR"].rolling(50).mean() / df["ATR"]
        is_tight = df["ATR_Contraction"].iloc[-1] >= 2.5

        df["Volume_MA"] = df["Volume"].rolling(20).mean()
        df["Volume_Contraction"] = (df["Volume"] < df["Volume_MA"] * 0.6).astype(int)

        df["Pivot_Level"] = df["Close"].rolling(20).max()
        is_near_pivot = df["Close"].iloc[-1] >= df["Pivot_Level"].iloc[-1] * 0.95

        vcp_score = (is_tight * 0.3) + (df["Volume_Contraction"].iloc[-1] * 0.1) + (is_near_pivot * 0.3) + (in_trend * 0.2)

        # ✅ Show Debugging Output in Streamlit
        st.write(f"📊 **VCP Calculation for {ticker}**")
        st.write(f"📌 Latest Close Price: {df['Close'].iloc[-1]:.2f}")
        st.write(f"📌 50-SMA: {df['50_SMA'].iloc[-1]:.2f}")
        st.write(f"📌 200-SMA: {df['200_SMA'].iloc[-1]:.2f}")
        st.write(f"📌 Trend Confirmation (50 & 200 SMA): {in_trend}")
        st.write(f"✅ Final VCP Score: {round(vcp_score * 100, 2)}")

        return round(vcp_score * 100, 2)
    except Exception as e:
        st.error(f"❌ Error processing VCP for {ticker}: {e}")
        return 0

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
    progress_bar = st.progress(0)  # ✅ Progress Bar
    
    for i, stock in enumerate(stocks):
        vcp_score = is_valid_vcp(stock)
        progress_bar.progress((i + 1) / len(stocks))  # ✅ Update Progress

        if vcp_score >= 40:  # ✅ Threshold lowered to 40
            results.append({"Stock": stock, "VCP Score": vcp_score})
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

