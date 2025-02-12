import pandas as pd
import numpy as np
import ta
from data_fetch import fetch_stock_data

# ✅ VCP Scoring Weights
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
    """Detects a valid VCP pattern with pullback contraction, volume expansion, and breakout confirmation."""
    df = fetch_stock_data(ticker, days=250)  # Extended timeframe for trend analysis
    if df is None or df.empty:
        return 0

    try:
        df['ATR'] = ta.volatility.AverageTrueRange(df['h'], df['l'], df['c']).average_true_range()
        df['ATR_Contraction'] = df['ATR'].diff().rolling(5).sum()

        df['Volume_MA'] = df['v'].rolling(20).mean()
        df['Volume_Contraction'] = (df['v'] < df['Volume_MA'] * 0.7).sum()

        df['Pullback_Size'] = df['c'].diff().rolling(5).sum()
        
        # ✅ Fix: Ensure Pullback Contraction is a Single Value
        pullbacks = df['Pullback_Size'].rolling(3).sum().dropna()
        contraction_trend = np.polyfit(range(len(pullbacks[-3:])), pullbacks[-3:], 1)[0]
        pullback_contraction = contraction_trend < 0  
        df['Pullback_Contraction'] = pullback_contraction  # ✅ Single Boolean Value

        df['Pivot_Level'] = df['c'].rolling(20).max().iloc[-1] * 0.98

        # ✅ Fix: Ensure SMA Trend is a Single Value
        df['50_SMA'] = df['c'].rolling(50).mean()
        df['200_SMA'] = df['c'].rolling(200).mean()
        in_trend = (df['c'].iloc[-1] > df['50_SMA'].iloc[-1]) and (df['50_SMA'].iloc[-1] > df['200_SMA'].iloc[-1])

        # ✅ Fix: Ensure 52-Week High is Evaluated Correctly
        df['52_Week_High'] = df['c'].rolling(252).max()
        near_high = df['c'].iloc[-1] >= (df['52_Week_High'].iloc[-1] * 0.90)

        # ✅ Fix: Ensure Volume Expansion is a Single Value
        df['Relative_Volume'] = df['v'].iloc[-1] / df['v'].rolling(5).mean().iloc[-1]
        volume_expansion = df['Relative_Volume'].iloc[-1] > 1.3

        # ✅ Fix: Ensure Closing Strength is a Single Value
        daily_range = df['h'].iloc[-1] - df['l'].iloc[-1]
        closing_position = (df['c'].iloc[-1] - df['l'].iloc[-1]) / daily_range
        strong_closing_range = closing_position >= 0.8  # Top 20% of the day's range

        vcp_score = (
            (df['ATR_Contraction'].iloc[-1] * VCP_WEIGHTS['ATR_Contraction']) +
            (df['Volume_Contraction'] * VCP_WEIGHTS['Volume_Contraction']) +
            (pullback_contraction * VCP_WEIGHTS['Pullback_Contraction']) +
            (df['Pivot_Level'] * VCP_WEIGHTS['Pivot_Level']) +
            (in_trend * VCP_WEIGHTS['SMA_Trend']) +
            (near_high * VCP_WEIGHTS['52_Week_High']) +
            (volume_expansion * VCP_WEIGHTS['Volume_Expansion']) +
            (strong_closing_range * VCP_WEIGHTS['Closing_Strength'])
        )

        return round(vcp_score * 100, 2) if vcp_score > 0.5 else 0
    
    except Exception as e:
        print(f"VCP calculation error for {ticker}: {e}")
    
    return 0


