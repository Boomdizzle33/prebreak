import pandas as pd
import numpy as np
import ta
import streamlit as st
from datetime import datetime, timedelta
from data_fetch import fetch_stock_data  # ✅ FIXED CIRCULAR IMPORT

# ✅ Rank & Return Top 20 VCP Stocks
def rank_best_trades(stocks):
    """Ranks stocks by VCP Strength, Institutional Activity, Market Strength, and Historical Breakout Probability."""
    
    from institutional import institutional_score  # 🔄 Moved Inside Function to Fix Circular Import
    from market import market_breadth_score  # 🔄 Moved Inside Function to Fix Circular Import
    from backtest import breakout_probability  # 🔄 Moved Inside Function to Fix Circular Import
    from vcp_detection import is_valid_vcp  # 🔄 Moved Inside Function to Fix Circular Import

    trade_data = []

    for stock in stocks:
        df = fetch_stock_data(stock, days=50)
        if df is None:
            continue

        vcp_score = is_valid_vcp(df)  # ✅ Apply VCP Detection to DataFrame
        if vcp_score == 0:
            continue  

        institutional_strength = institutional_score(stock)
        market_strength = market_breadth_score()
        breakout_prob = breakout_probability(stock)

        # 📊 **Final Confidence Score (Weighted)**
        final_score = (
            (vcp_score * 0.5) +  
            (institutional_strength * 0.2) +  
            (market_strength * 0.15) +  
            (breakout_prob * 0.15)  
        )

        trade_data.append({
            "Stock": stock,
            "VCP Score": vcp_score,
            "Institutional Strength": institutional_strength,
            "Market Strength": market_strength,
            "Historical Breakout Probability": breakout_prob,
            "Final Confidence Score": round(final_score, 2)
        })

    return sorted(trade_data, key=lambda x: x["Final Confidence Score"], reverse=True)[:20]



