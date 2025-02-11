import pandas as pd
import ta
from data_fetch import fetch_stock_data  # ✅ Centralized Data Fetching

# ✅ Identify a True VCP Pattern
def is_valid_vcp(ticker):
    """Detects whether a stock forms a valid Volatility Contraction Pattern (VCP)."""
    df = fetch_stock_data(ticker, days=50)
    if df is None:
        return 0

    # 📉 **Step 1: Detect Progressive Volatility Contraction**
    df["Bollinger_Band_Width"] = ta.volatility.BollingerBands(df["c"]).bollinger_wband()
    df["ATR"] = ta.volatility.AverageTrueRange(df["h"], df["l"], df["c"]).average_true_range()
    
    df["ATR_Contraction"] = df["ATR"].diff().rolling(5).sum()
    df["BB_Contraction"] = df["Bollinger_Band_Width"].diff().rolling(5).sum()

    is_contracting = (df["ATR_Contraction"].iloc[-1] < 0) and (df["BB_Contraction"].iloc[-1] < 0)

    # 📉 **Step 2: Ensure Volume Contracts in Sync With Price**
    df["Volume_MA"] = df["v"].rolling(20).mean()
    volume_contractions = (df["v"] < df["Volume_MA"] * 0.7).sum()  

    # 📈 **Step 3: Confirm Higher Lows**
    df["Pullback_Size"] = df["c"].diff().rolling(5).sum()
    higher_lows = (df["Pullback_Size"].iloc[-3] < df["Pullback_Size"].iloc[-2] < df["Pullback_Size"].iloc[-1])

    # 📍 **Step 4: Pivot Point Entry (Before Breakout)**
    pivot_level = df["c"].rolling(20).max().iloc[-1] * 0.98  

    # ✅ Final VCP Score Calculation
    vcp_score = (
        (is_contracting * 30) +  
        (volume_contractions * 20) +  
        (higher_lows * 20) +  
        (pivot_level * 10)  
    )

    return round(vcp_score, 2) if vcp_score > 50 else 0  # **Only return if valid VCP**

