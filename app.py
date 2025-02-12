import streamlit as st
import pandas as pd
from scanner import rank_best_trades
from backtest import backtest_vcp

st.set_page_config(page_title="🚀 Minervini VCP Scanner", layout="wide")
st.title("🚀 Minervini VCP Scanner (Institutional + Market Confirmation)")

uploaded_file = st.file_uploader("📂 Upload Stock List (CSV)", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    if "Ticker" in df.columns:
        stocks = df["Ticker"].tolist()
    else:
        st.error("❌ CSV file must contain a 'Ticker' column.")
        st.stop()
    
    st.subheader("🔍 Scanning Stocks for VCP Patterns...")
    ranked_trades = rank_best_trades(stocks)
    st.subheader("🏆 Top VCP Stocks (Ranked by Confidence Score)")
    st.dataframe(pd.DataFrame(ranked_trades))
    
    if st.button("📊 Run Backtest on These Stocks"):
        success_rate, backtest_results = backtest_vcp(stocks)
        st.subheader(f"🔥 VCP Historical Success Rate: {success_rate:.2f}%")
        st.dataframe(backtest_results)
    
    if st.button("📤 Export to TradingView (CSV)"):
        output_df = pd.DataFrame(ranked_trades)
        output_df.to_csv("TradingView_Export.csv", index=False)
        st.success("✅ File Ready for Download!")
        st.download_button(label="⬇ Download CSV", data=open("TradingView_Export.csv", "rb"), file_name="TradingView_Export.csv")



