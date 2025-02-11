import pandas as pd
import requests
from config import POLYGON_API_KEY

# ✅ Fetch Options Activity Data
def fetch_options_activity(ticker):
    """Fetch options flow data for institutional sentiment analysis."""
    url = f"https://api.polygon.io/v3/reference/options/contracts?underlying_ticker={ticker}&apiKey={POLYGON_API_KEY}"
    
    response = requests.get(url).json()
    if "results" in response:
        df = pd.DataFrame(response["results"])
        
        if "open_interest" in df.columns and "volume" in df.columns:
            df["Call/Put Ratio"] = df["open_interest"] / df["volume"]
            return df["Call/Put Ratio"].mean()
        
    return None  

# ✅ Institutional Accumulation Score
def institutional_score(ticker):
    """Calculate Institutional Strength Score (Dark Pools + Options Activity)."""
    
    dark_pool_score = 50  # Placeholder for Dark Pool Data
    options_score = fetch_options_activity(ticker)

    if options_score is None:
        options_score = 0  

    return round((dark_pool_score * 0.3) + (options_score * 0.7), 2)

