import streamlit as st
import pandas as pd
import time
from scanner import rank_best_trades  # ✅ Scanner function to find best trades
from backtest import breakout_probability  # ✅ Fixed Import
from data_fetch import fetch_stock_data  # ✅ Directly fetch stock data

# ✅ Streamlit UI Setup
st.title("📈 VCP Scanner - Find the Best Pre-Breakout Stocks")

# ✅ Upload CSV
uploaded_file = st.file_uploader("📂 Upload Stock List CSV", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    stocks = df["Ticker"].tolist() if "Ticker" in df.columns else df["Symbol"].tolist()
else:
    st.warning("⚠️ Please upload a valid CSV with a 'Ticker' or 'Symbol' column.")
    st.stop()

# ✅ Run Scanner
st.subheader("🔍 Running Scanner...")
progress_bar = st.progress(0)
status_text = st.empty()

start_time = time.time()
ranked_trades = rank_best_trades(stocks)
progress_bar.progress(1.0)
status_text.text("✅ Scan Complete! Showing Best Pre-Breakout Setups.")

# ✅ Display Results
st.subheader("🏆 Top 20 Pre-Breakout Stocks")
st.dataframe(pd.DataFrame(ranked_trades))


