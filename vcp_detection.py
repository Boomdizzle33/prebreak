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
        df['ATR_Contraction'] = df['ATR'].diff().rolling(5).sum()
        df['Volume_MA'] = df['v'].rolling(20).mean()
        df['Volume_Contraction'] = (df['v'] < df['Volume_MA'] * 0.7).sum()
        df['Pullback_Size'] = df['c'].diff().rolling(5).sum()

        # ✅ More Flexible Pullback Contraction
        pullbacks = df['Pullback_Size'].rolling(3).sum().dropna()
        contraction_trend = np.polyfit(range(len(pullbacks[-3:])), pullbacks[-3:], 1)[0]
        pullback_contraction = contraction_trend < 0  

        df['Pullback_Contraction'] = pullback_contraction

        df['Pivot_Level'] = df['c'].rolling(20).max().iloc[-1] * 0.98

        # ✅ Trend Confirmation (50-SMA & 200-SMA)
        df['50_SMA'] = df['c'].rolling(50).mean()
        df['200_SMA'] = df['c'].rolling(200).mean()
        in_trend = df['c'].iloc[-1] > df['50_SMA'].iloc[-1] > df['200_SMA'].iloc[-1]

        # ✅ More Flexible 52-Week High Check
        df['52_Week_High'] = df['c'].rolling(252).max()
        near_high = df['c'].iloc[-1] >= (df['52_Week_High'].iloc[-1] * 0.90)  

        # ✅ Volume Expansion
        df['Relative_Volume'] = df['v'].iloc[-1] / df['v'].rolling(5).mean().iloc[-1]
        volume_expansion = df['Relative_Volume'] > 1.3  

        # ✅ Closing Strength & Bollinger Band Breakout
        df['Upper_BB'] = ta.volatility.BollingerBands(df['c']).bollinger_hband()
        breakout_signal = df['c'].iloc[-1] > df['Upper_BB'].iloc[-1]

        # ✅ Volatility Squeeze Before Breakout
        df['BB_Width'] = ta.volatility.BollingerBands(df['c']).bollinger_wband()
        volatility_squeeze = df['BB_Width'].rolling(5).mean().iloc[-1] < df['BB_Width'].rolling(50).mean().iloc[-1] * 0.8

        vcp_score = (
            (df['ATR_Contraction'].iloc[-1] * VCP_WEIGHTS['ATR_Contraction']) +
            (df['Volume_Contraction'] * VCP_WEIGHTS['Volume_Contraction']) +
            (df['Pullback_Contraction'] * VCP_WEIGHTS['Pullback_Contraction']) +
            (df['Pivot_Level'] * VCP_WEIGHTS['Pivot_Level']) +
            (in_trend * VCP_WEIGHTS['SMA_Trend']) +
            (near_high * VCP_WEIGHTS['52_Week_High']) +
            (volume_expansion * VCP_WEIGHTS['Volume_Expansion']) +
            (breakout_signal * VCP_WEIGHTS['Closing_Strength'])
        )
        return round(vcp_score * 100, 2) if vcp_score > 0.5 else 0
    except Exception as e:
        print(f"VCP calculation error: {e}")
    return 0

