
import pandas as pd
import requests
import time
import functools
from datetime import datetime, timedelta
from config import POLYGON_API_KEY

# ✅ Cache API results to prevent redundant calls
@functools.lru_cache(maxsize=100)
def fetch_stock_data(ticker, days=100):
    """Fetch historical stock data from Polygon.io with rate limit handling."""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}?adjusted=true&sort=asc&apiKey={POLYGON_API_KEY}"
        
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if 'results' in data:
            df = pd.DataFrame(data['results'])
            df['date'] = pd.to_datetime(df['t'], unit='ms')
            df.set_index('date', inplace=True)
            return df
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
    return None
