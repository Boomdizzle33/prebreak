import pandas as pd
import numpy as np
import ta
from data_fetch import fetch_stock_data

# ✅ Improved VCP Scoring Weights
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
    """Detects a valid VCP pattern with flexible pullback tolerance, volume expansion, and breakout confirmation."""
    df = fetch_stock_data(ticker, days=250)  # Extended timeframe for trend analysis
    if df is None or df.empty:
        return 0

    try:
        df['ATR'] = ta.volatility.AverageTrueRange(df['h'], df['l'], df['c']).average_true_range()
        
        # ✅ Fix: Ensure calculations return Pandas Series, not scalars
        df['ATR_Contraction'] = df['ATR'].diff().rolling(5).sum()
        df['ATR_Contraction'] = pd.Series(df['ATR_Contraction'], index=df.index)  # ✅ Fix scalar issue

        df['Volume_MA'] = df['v'].rolling(20).mean()
        df['Volume_Contraction'] = (df['v'] < df['Volume_MA'] * 0.7).sum()
        df['Volume_Contraction'] = pd.Series(df['Volume_Contraction'], index=df.index)  # ✅ Fix scalar issue
        
        df['Pullback_Size'] = df['c'].diff().rolling(5).sum()

        # ✅ Fix: Ensure Pullback Contraction is a Series, not a scalar
        pullbacks = df['Pullback_Size'].rolling(3).sum().dropna()
        contraction_trend = np.polyfit(range(len(pullbacks[-3:])), pullbacks[-3:], 1)[0]
        pullback_contraction = contraction_trend < 0  
        df['Pullback_Contraction'] = pd.Series(pullback_contraction, index=df.index)  # ✅ Fix scalar issue

        df['Pivot_Level'] = df['c'].rolling(20).max().iloc[-1] * 0.98

        # ✅ Confirm Stock is in an Uptrend using SMA
        df['50_SMA'] = df['c'].rolling(50).mean()
        df['200_SMA'] = df['c'].rolling(200).mean()
        in_trend = df['c'].iloc[-1] > df['50_SMA'].iloc[-1] > df['200_SMA'].iloc[-1]

        # ✅ Ensure Stock is Near 52-Week High Before Confirming Breakout
        df['52_Week_High'] = df['c'].rolling(252).max()
        near_high = df['c'].iloc[-1] >= (df['52_Week_High'].iloc[-1] * 0.90)  # Stock within 10% of the 52-week high

        # ✅ Require Volume Expansion Near Breakout Points
        df['Relative_Volume'] = df['v'].iloc[-1] / df['v'].rolling(5).mean().iloc[-1]
        volume_expansion = df['Relative_Volume'] > 1.3
        df['Volume_Expansion'] = pd.Series(volume_expansion, index=df.index)  # ✅ Fix scalar issue

        # ✅ Ensure Stock Closes in Top 20% of Daily Range Before Breakout
        daily_range = df['h'].iloc[-1] - df['l'].iloc[-1]
        closing_position = (df['c'].iloc[-1] - df['l'].iloc[-1]) / daily_range
        strong_closing_range = closing_position >= 0.8  # Top 20% of the day's range
        df['Closing_Strength'] = pd.Series(strong_closing_range, index=df.index)  # ✅ Fix scalar issue

        vcp_score = (
            (df['ATR_Contraction'].iloc[-1] * VCP_WEIGHTS['ATR_Contraction']) +
            (df['Volume_Contraction'].iloc[-1] * VCP_WEIGHTS['Volume_Contraction']) +
            (df['Pullback_Contraction'].iloc[-1] * VCP_WEIGHTS['Pullback_Contraction']) +
            (df['Pivot_Level'] * VCP_WEIGHTS['Pivot_Level']) +
            (in_trend * VCP_WEIGHTS['SMA_Trend']) +
            (near_high * VCP_WEIGHTS['52_Week_High']) +
            (df['Volume_Expansion'].iloc[-1] * VCP_WEIGHTS['Volume_Expansion']) +
            (df['Closing_Strength'].iloc[-1] * VCP_WEIGHTS['Closing_Strength'])
        )
        return round(vcp_score * 100, 2) if vcp_score > 0.5 else 0
    except Exception as e:
        print(f"VCP calculation error: {e}")
    return 0

