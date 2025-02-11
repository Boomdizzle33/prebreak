import requests
import pandas as pd
import streamlit as st

# ✅ Fetch API key from Streamlit secrets
POLYGON_API_KEY = st.secrets["POLYGON_API_KEY"]

# ✅ Fetch VIX Data (Volatility Index)
def fetch_vix():
    """Get latest VIX value (Volatility Index)."""
    url = f"https://api.polygon.io/v2/aggs/ticker/VIX/range/1/day/2024-01-01/2024-12-31?adjusted=true&sort=asc&apiKey={POLYGON_API_KEY}"
    response = requests.get(url).json()

    if "results" in response:
        df = pd.DataFrame(response["results"])
        return df["c"].iloc[-1]  # Latest Closing Value of VIX
    return None

# ✅ Fetch Advance-Decline Line (ADL)
def fetch_adl():
    """Get latest Advance-Decline Line (ADL) value to measure market breadth."""
    url = f"https://api.polygon.io/v2/aggs/ticker/ADL/range/1/day/2024-01-01/2024-12-31?adjusted=true&sort=asc&apiKey={POLYGON_API_KEY}"
    response = requests.get(url).json()

    if "results" in response:
        df = pd.DataFrame(response["results"])
        return df["c"].iloc[-1]  # Latest ADL Closing Value
    return None

# ✅ Fetch SPY/IWM Trend (Confirm Bull Market)
def fetch_spy_trend():
    """Get latest SPY data & check if market is trending up."""
    url = f"https://api.polygon.io/v2/aggs/ticker/SPY/range/1/day/2024-01-01/2024-12-31?adjusted=true&sort=asc&apiKey={POLYGON_API_KEY}"
    response = requests.get(url).json()

    if "results" in response:
        df = pd.DataFrame(response["results"])
        df["50_SMA"] = df["c"].rolling(50).mean()
        df["200_SMA"] = df["c"].rolling(200).mean()

        # ✅ Market is bullish if SPY is above both 50-day & 200-day SMA
        if df["c"].iloc[-1] > df["50_SMA"].iloc[-1] > df["200_SMA"].iloc[-1]:
            return 100  
        else:
            return 50  # Neutral market condition
    return None

# ✅ Market Breadth Score (Final Calculation)
def market_breadth_score():
    """Calculate overall market strength score using VIX, ADL, and SPY trend."""
    vix = fetch_vix()
    adl = fetch_adl()
    spy_trend = fetch_spy_trend()

    if vix is None or adl is None or spy_trend is None:
        return 0  # Return neutral score if data is missing

    # ✅ VIX Scoring: Low volatility = Bullish
    vix_score = 100 if vix < 20 else 50 if vix < 25 else 0  

    # ✅ ADL Scoring: Positive ADL = Strong Market Breadth
    adl_score = 100 if adl > 0 else 50 if adl > -1000 else 0  

    # ✅ SPY Trend Confirmation
    spy_score = spy_trend  

    # 📊 Final Market Strength Score (Weighted)
    return round((vix_score * 0.4) + (adl_score * 0.3) + (spy_score * 0.3), 2)  
