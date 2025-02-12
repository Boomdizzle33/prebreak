import pandas as pd
import numpy as np
import ta
from data_fetch import fetch_stock_data

# Define weights for VCP scoring
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

def is_valid_vcp(ticker):
    """Detects a valid VCP pattern and calculates a score."""
    df = fetch_stock_data(ticker, days=250)
    
    # Ensure data is available
    if df is None or df.empty:
        print(f"⚠️ No data for {ticker}")
        return 0

    try:
        # Compute ATR (Average True Range)
        df['ATR'] = ta.volatility.AverageTrueRange(high=df['h'], low=df['l'], close=df['c']).average_true_range()
        
        # Ensure ATR Contraction is correctly extracted
        df['ATR_Contraction'] = df['ATR'].diff().rolling(5).sum()
        atr_contraction = df['ATR_Contraction'].iloc[-1] if not df['ATR_Contraction'].isna().all() else 0

        # Compute Volume Contraction
        df['Volume_MA'] = df['v'].rolling(20).mean()
        df['Volume_Contraction'] = (df['v'] < df['Volume_MA'] * 0.7).sum()
        volume_contraction = df['Volume_Contraction'].iloc[-1] if not df['Volume_Contraction'].isna().all() else 0

        # Compute Pullback Contraction
        df['Pullback_Size'] = df['c'].diff().rolling(5).sum()
        pullbacks = df['Pullback_Size'].rolling(3).sum().dropna()
        contraction_trend = np.polyfit(range(len(pullbacks[-3:])), pullbacks[-3:], 1)[0] if len(pullbacks) >= 3 else 0
        pullback_contraction = int(contraction_trend < 0)

        # Compute Pivot Level
        pivot_level = df['c'].rolling(20).max().iloc[-1] * 0.98 if not df['c'].rolling(20).max().isna().all() else 0

        # Compute SMA Trend
        df['50_SMA'] = df['c'].rolling(50).mean()
        df['200_SMA'] = df['c'].rolling(200).mean()
        in_trend = int((df['c'].iloc[-1] > df['50_SMA'].iloc[-1]) and (df['50_SMA'].iloc[-1] > df['200_SMA'].iloc[-1]))

        # Compute 52-Week High Position
        df['52_Week_High'] = df['c'].rolling(252).max()
        near_high = int(df['c'].iloc[-1] >= (df['52_Week_High'].iloc[-1] * 0.90)) if not df['52_Week_High'].isna().all() else 0

        # Compute Volume Expansion
        df['Relative_Volume'] = df['v'] / df['v'].rolling(5).mean()
        volume_expansion = int(df['Relative_Volume'].iloc[-1] > 1.3 if not df['Relative_Volume'].isna().all() else 0)

        # Compute Closing Strength
        daily_range = df['h'].iloc[-1] - df['l'].iloc[-1]
        closing_position = (df['c'].iloc[-1] - df['l'].iloc[-1]) / daily_range if daily_range > 0 else 0
        strong_closing_range = int(closing_position >= 0.8)

        # Compute final VCP score
        vcp_score = (
            (atr_contraction * VCP_WEIGHTS['ATR_Contraction']) +
            (volume_contraction * VCP_WEIGHTS['Volume_Contraction']) +
            (pullback_contraction * VCP_WEIGHTS['Pullback_Contraction']) +
            (pivot_level * VCP_WEIGHTS['Pivot_Level']) +
            (in_trend * VCP_WEIGHTS['SMA_Trend']) +
            (near_high * VCP_WEIGHTS['52_Week_High']) +
            (volume_expansion * VCP_WEIGHTS['Volume_Expansion']) +
            (strong_closing_range * VCP_WEIGHTS['Closing_Strength'])
        )

        return round(vcp_score * 100, 2) if vcp_score > 0.5 else 0

    except Exception as e:
        print(f"❌ VCP calculation error for {ticker}: {e}")
    
    return 0


