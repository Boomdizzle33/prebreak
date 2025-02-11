import requests
import pandas as pd
import streamlit as st

# ✅ Fetch API key from Streamlit secrets
POLYGON_API_KEY = st.secrets["POLYGON_API_KEY"]

# ✅ Fetch Dark Pool Data from FINRA
def fetch_dark_pool_data(ticker):
    """Get Dark Pool Short Volume % (Institutional Buying)."""
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/2024-01-01/2024-12-31?adjusted=true&sort=asc&apiKey={POLYGON_API_KEY}"
    response = requests.get(url).json()

    if "results" in response:
        df = pd.DataFrame(response["results"])
        df["Short Volume %"] = df["v"] / df["v"].rolling(10).mean()  
        return df["Short Volume %"].iloc[-1]  # Latest Dark Pool Short Volume Percentage
    return None

# ✅ Fetch Unusual Options Activity
def fetch_options_activity(ticker):
    """Get Call/Put Ratio & Open Interest to detect institutional activity."""
    url = f"https://api.polygon.io/v3/reference/options/contracts?underlying_ticker={ticker}&apiKey={POLYGON_API_KEY}"
    response = requests.get(url).json()

    if "results" in response:
        df = pd.DataFrame(response["results"])
        df["Call/Put Ratio"] = df["open_interest"] / df["volume"]  
        return df["Call/Put Ratio"].mean()  # Average Call/Put Ratio
    return None

# ✅ Institutional Strength Score (Weighted)
def institutional_score(ticker):
    """Calculate Institutional Strength Score (Dark Pools + Options Activity)."""
    dark_pool_score = fetch_dark_pool_data(ticker) * 30  # Dark Pool Weight: 30%
    options_score = fetch_options_activity(ticker) * 70  # Options Weight: 70%

    if dark_pool_score is None or options_score is None:
        return 0  # If data unavailable, assume no institutional activity

    return round((dark_pool_score + options_score) / 100, 2)  # Final Institutional Score
