import pandas as pd
import requests
from config import POLYGON_API_KEY

def fetch_options_activity(ticker):
    """Fetch options flow data for institutional sentiment analysis."""
    try:
        url = f"https://api.polygon.io/v3/reference/options/contracts?underlying_ticker={ticker}&apiKey={POLYGON_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if "results" in data:
            df = pd.DataFrame(data["results"])
            if "open_interest" in df.columns and "volume" in df.columns:
                df["Call/Put Ratio"] = df["open_interest"] / df["volume"]
                return round(df["Call/Put Ratio"].mean(), 2)
    except requests.exceptions.RequestException as e:
        print(f"Options data request failed: {e}")
    return 0  

def institutional_score(ticker):
    """Calculate Institutional Strength Score (Options Flow + Dark Pools)."""
    dark_pool_score = 50  # Placeholder for Dark Pool Data
    options_score = fetch_options_activity(ticker)

    if options_score is None:
        options_score = 0  

    return round((dark_pool_score * 0.3) + (options_score * 0.7), 2)
