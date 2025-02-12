import streamlit as st
import pandas as pd
from scanner import rank_best_trades
from backtest import display_backtest_results  # ✅ Import backtest display function

# ✅ Streamlit Page Configuration
st.set_page_config(page_title="🚀 Minervini VCP Scanner", layout="wide")
st.title("🚀 Minervini VCP Scanner (Institutional + Market Confirmation)")

# ✅ CSV Upload Section
uploaded_file = st.file_uploader("📂 Upload Stock List (CSV)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # ✅ Check for "Ticker" or "Tickers" column dynamically
    column_name = None
    for col in df.columns:
        if col.lower() in ["ticker", "tickers"]:  
            column_name = col
            break

    if column_name:
        stocks = df[column_name].tolist()  # ✅ Extract tickers dynamically
        st.write(f"✅ Loaded {len(stocks)} stocks from CSV: {stocks}")  # ✅ Show stocks loaded
    else:
        st.error("❌ CSV file must contain a column named 'Ticker' or 'Tickers'.")
        st.stop()

    # ✅ Run Scanner
    st.subheader("🔍 Scanning Stocks for VCP Patterns...")
    ranked_trades = rank_best_trades(stocks)

    # ✅ Display Ranked VCP Stocks
    if ranked_trades:
        st.subheader("🏆 Top VCP Stocks (Ranked by Confidence Score)")
        st.dataframe(pd.DataFrame(ranked_trades))
    else:
        st.warning("⚠️ No valid VCP setups found in the uploaded stock list.")

    # ✅ Run Full Backtest After Scanning
    if st.button("📊 Run Full Backtest on These Stocks"):
        display_backtest_results(stocks)

    # ✅ Export Ranked Stocks to TradingView
    if ranked_trades:
        output_df = pd.DataFrame(ranked_trades)
        output_df.to_csv("TradingView_Export.csv", index=False)
        st.success("✅ File Ready for Download!")
        st.download_button(label="⬇ Download CSV", data=open("TradingView_Export.csv", "rb"), file_name="TradingView_Export.csv")


