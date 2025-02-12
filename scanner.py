import streamlit as st
import pandas as pd
import numpy as np
import requests
import ta
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from functools import lru_cache

# ✅ Secure API Key Handling
POLYGON_API_KEY = st.secrets["POLYGON_API_KEY"] if "POLYGON_API_KEY" in st.secrets else "YOUR_POLYGON_API_KEY"

# ✅ Define VCP Weights
VCP_WEIGHTS = {
    "ATR_Contraction": 0.2,
    "Volume_Contraction": 0.2,
    "Pullback_Contraction": 0.15,
    "Pivot_Level": 0.1,
    "SMA_Trend": 0.1,
    "52_Week_High": 0.1,
    "Volume_Expansion": 0.1,
    "Closing_Strength": 0.05
}

# ✅ Fetch historical stock data from Polygon.io
@lru_cache(maxsize=100)
def fetch_stock_data(ticker, days=365):
    """Fetch historical stock data using Polygon.io."""
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

            # ✅ Rename columns to match expected format
            df.rename(columns={"o": "Open", "h": "High", "l": "Low", "c": "Close", "v": "Volume"}, inplace=True)

            return df
        else:
            print(f"⚠️ No data found for {ticker}")
            return pd.DataFrame()
    except Exception as e:
        print(f"❌ Error fetching {ticker}: {e}")
        return pd.DataFrame()

# ✅ VCP Detection Algorithm
def is_valid_vcp(ticker):
    df = fetch_stock_data(ticker, days=250)
    if df.empty or not all(col in df.columns for col in ["High", "Low", "Close", "Volume"]):
        return 0

    try:
        df["ATR"] = ta.volatility.AverageTrueRange(df["High"], df["Low"], df["Close"], window=14).average_true_range()
        if df["ATR"].isna().all():
            return 0

        df["ATR_Contraction"] = df["ATR"].diff().rolling(5, min_periods=1).sum()
        df["Volume_MA"] = df["Volume"].rolling(20, min_periods=1).mean()
        df["Volume_Contraction"] = (df["Volume"] < df["Volume_MA"] * 0.7).astype(int)

        df["50_SMA"] = df["Close"].rolling(50, min_periods=1).mean()
        df["200_SMA"] = df["Close"].rolling(200, min_periods=1).mean()
        in_trend = int(df["Close"].iloc[-1] > df["50_SMA"].iloc[-1] > df["200_SMA"].iloc[-1])

        vcp_score = (
            (df["ATR_Contraction"].iloc[-1] * VCP_WEIGHTS["ATR_Contraction"]) +
            (in_trend * VCP_WEIGHTS["SMA_Trend"])
        )

        return round(vcp_score * 100, 2) if vcp_score > 0.5 else 0

    except Exception as e:
        print(f"❌ VCP calculation error for {ticker}: {e}")
        return 0

# ✅ Backtesting with Polygon.io
def backtest_vcp(ticker):
    df = fetch_stock_data(ticker, days=365)
    
    if df.empty or "Close" not in df.columns:
        return None

    df["ATR"] = ta.volatility.AverageTrueRange(df["High"], df["Low"], df["Close"], window=14).average_true_range()
    
    if df["ATR"].isna().all():
        return None

    entry_price = df["Close"].iloc[-1]
    stop_loss = entry_price - (1.5 * df["ATR"].iloc[-1])
    target_price = entry_price + (3 * df["ATR"].iloc[-1])
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

# ✅ Rank and Process Stocks (Fixed Progress Bar)
def rank_best_trades(stocks):
    ranked_trades = []
    progress_placeholder = st.empty()  # ✅ Create a placeholder for progress bar

    def process_stock(stock):
        vcp_score = is_valid_vcp(stock)
        if vcp_score == 0:
            return None

        backtest_result = backtest_vcp(stock)
        if backtest_result is None:
            return None

        success_rate = 1 if backtest_result["Success"] else 0
        final_score = (vcp_score * 0.8) + (success_rate * 0.2)

        return {**backtest_result, "VCP Score": vcp_score, "Final Score": round(final_score, 2)}

    results = []
    with ThreadPoolExecutor() as executor:
        for i, result in enumerate(executor.map(process_stock, stocks)):
            if result:
                results.append(result)
            progress_placeholder.progress((i + 1) / len(stocks))  # ✅ Update progress bar in main thread

    progress_placeholder.empty()  # ✅ Remove progress bar after scanning
    return sorted(results, key=lambda x: x["Final Score"], reverse=True)[:20]

# ✅ Streamlit UI
st.set_page_config(page_title="🚀 Minervini VCP Scanner", layout="wide")
st.title("🚀 Minervini VCP Scanner (Full Automated)")

uploaded_file = st.file_uploader("📂 Upload Stock List (CSV)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    if "Ticker" in df.columns:
        stocks = df["Ticker"].dropna().tolist()
        st.write(f"✅ Loaded {len(stocks)} stocks from CSV")
    else:
        st.error("❌ CSV file must contain a 'Ticker' column.")
        st.stop()

    st.subheader("🔍 Scanning Stocks for VCP Patterns & Running Backtests...")
    ranked_trades = rank_best_trades(stocks)

    if ranked_trades:
        st.subheader("🏆 Top VCP Stocks with Backtesting")
        st.dataframe(pd.DataFrame(ranked_trades))
    else:
        st.warning("⚠️ No valid VCP setups found.")




