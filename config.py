import streamlit as st

# ✅ Store API keys in Streamlit secrets
POLYGON_API_KEY = st.secrets["POLYGON_API_KEY"]
YFINANCE_ENABLED = True  # ✅ Enable YFinance for backtesting

# ✅ Default Scanner Settings
DEFAULT_VCP_SCORE_THRESHOLD = 50  # Ignore weak setups
DEFAULT_MARKET_STRENGTH_THRESHOLD = 50  # Avoid trading in weak markets


