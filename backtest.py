import pandas as pd
import numpy as np
import ta
import yfinance as yf
from datetime import datetime, timedelta

# ✅ Fetch historical stock data
def fetch_stock_data(ticker, days=365):
    """Fetch stock data using Yahoo Finance for backtesting"""
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days)
    df = yf.download(ticker, start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"))
    
    if df.empty:
        return None
    
    df = df.rename(columns={"Open": "o", "High": "h", "Low": "l", "Close": "c", "Volume": "v"})
    df.index = pd.to_datetime(df.index)
    return df

# ✅ Fetch VIX for market volatility analysis
def fetch_vix():
    """Fetch latest VIX value to adjust breakout criteria based on market volatility"""
    vix_df = yf.download("^VIX", period="1y", interval="1d")
    return vix_df["Close"].iloc[-1] if not vix_df.empty else None

# ✅ Fetch sector ETF performance
def fetch_sector_performance(ticker):
    """Compares stock performance to its sector ETF"""
    sector_map = {
        "AAPL": "XLK", "MSFT": "XLK", "NVDA": "XLK",
        "XOM": "XLE", "CVX": "XLE",
        "JPM": "XLF", "GS": "XLF",
        "PFE": "XLV", "JNJ": "XLV"
    }
    sector_ticker = sector_map.get(ticker, "SPY")  # Default to SPY if unknown
    sector_data = fetch_stock_data(sector_ticker, days=200)
    
    return sector_data["c"].pct_change().sum() if sector_data is not None else None

# ✅ Detects VCP Patterns with market & volatility adjustments
def is_valid_vcp(ticker):
    """Detects a valid VCP pattern with market trend, volatility, and breakout refinements."""
    df = fetch_stock_data(ticker, days=250)
    if df is None or df.empty:
        return 0

    try:
        df["ATR"] = ta.volatility.AverageTrueRange(df["h"], df["l"], df["c"]).average_true_range()
        df["ATR_Contraction"] = df["ATR"].diff().rolling(5).sum()
        df["Volume_MA"] = df["v"].rolling(20).mean()
        df["Volume_Contraction"] = (df["v"] < df["Volume_MA"] * 0.7).sum()
        df["Pullback_Size"] = df["c"].diff().rolling(5).sum()

        # ✅ Market Condition Adjustments (Bull vs. Bear Market)
        vix = fetch_vix()
        if vix and vix > 25:
            atr_threshold = -0.02  # Require tighter ATR contraction in high-volatility markets
        else:
            atr_threshold = -0.04  # More relaxed in low-volatility markets

        # ✅ Pullback Contraction Check
        pullbacks = df["Pullback_Size"].rolling(3).sum().dropna()
        contraction_trend = np.polyfit(range(len(pullbacks[-3:])), pullbacks[-3:], 1)[0]
        pullback_contraction = contraction_trend < atr_threshold

        df["Pullback_Contraction"] = pullback_contraction
        df["Pivot_Level"] = df["c"].rolling(20).max().iloc[-1] * 0.98

        # ✅ Trend Confirmation (50-SMA & 200-SMA)
        df["50_SMA"] = df["c"].rolling(50).mean()
        df["200_SMA"] = df["c"].rolling(200).mean()
        in_trend = df["c"].iloc[-1] > df["50_SMA"].iloc[-1] > df["200_SMA"].iloc[-1]

        # ✅ Sector Strength Check
        sector_performance = fetch_sector_performance(ticker)
        stock_performance = df["c"].pct_change().sum()
        sector_strong = stock_performance > sector_performance if sector_performance is not None else False

        # ✅ Volume Expansion Confirmation
        df["Relative_Volume"] = df["v"].iloc[-1] / df["v"].rolling(5).mean().iloc[-1]
        volume_expansion = df["Relative_Volume"] > 1.3

        # ✅ Breakout Confirmation (Closing above pivot level)
        breakout_signal = df["c"].iloc[-1] > df["Pivot_Level"]

        vcp_score = (
            (df["ATR_Contraction"].iloc[-1] * 0.2) +
            (df["Volume_Contraction"] * 0.2) +
            (df["Pullback_Contraction"] * 0.15) +
            (df["Pivot_Level"] * 0.1) +
            (in_trend * 0.1) +
            (sector_strong * 0.1) +
            (volume_expansion * 0.1) +
            (breakout_signal * 0.05)
        )
        return round(vcp_score * 100, 2) if vcp_score > 0.5 else 0
    except Exception as e:
        print(f"VCP calculation error: {e}")
    return 0

# ✅ Backtest on past stocks
test_tickers = ["AAPL", "NVDA", "MSFT", "TSLA", "AMZN"]
start_date = datetime(2023, 1, 1)
end_date = datetime(2023, 12, 31)
backtest_results = []

for ticker in test_tickers:
    df = fetch_stock_data(ticker, days=365)
    if df is None or df.empty:
        continue

    df = df[(df.index >= start_date) & (df.index <= end_date)]
    vcp_score = is_valid_vcp(ticker)

    if vcp_score > 50:
        entry_price = df["c"].iloc[-1]
        stop_loss = entry_price - (2 * df["ATR"].iloc[-1])
        target_price = entry_price + (4 * df["ATR"].iloc[-1])
        max_future_price = df["c"].iloc[-10:].max()

        success = max_future_price >= target_price

        backtest_results.append({
            "Stock": ticker,
            "VCP Score": vcp_score,
            "Entry Price": round(entry_price, 2),
            "Stop Loss": round(stop_loss, 2),
            "Target Price": round(target_price, 2),
            "Max Future Price": round(max_future_price, 2),
            "Success": success
        })

# ✅ Convert results to DataFrame
df_results = pd.DataFrame(backtest_results)
win_rate = df_results["Success"].mean() * 100 if not df_results.empty else 0

# ✅ Display results
import ace_tools as tools
tools.display_dataframe_to_user(name="VCP Backtest Results", dataframe=df_results)

print(f"Win Rate: {win_rate:.2f}%")




    

