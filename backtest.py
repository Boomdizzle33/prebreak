import pandas as pd
from vcp_detection import is_valid_vcp
from market import market_breadth_score
from data_fetch import fetch_stock_data

def fetch_sector_data(ticker):
    """Retrieve sector ETF data to compare against individual stock performance."""
    sector_map = {
        "AAPL": "XLK", "MSFT": "XLK", "NVDA": "XLK",
        "XOM": "XLE", "CVX": "XLE",
        "JPM": "XLF", "GS": "XLF",
        "PFE": "XLV", "JNJ": "XLV"
    }
    sector_ticker = sector_map.get(ticker, "SPY")  
    return fetch_stock_data(sector_ticker, days=200)

def backtest_vcp(tickers, start_date="2023-01-01", end_date="2023-12-31"):
    """Backtests historical VCP setups to evaluate success rates."""
    results = []

    for ticker in tickers:
        df = fetch_stock_data(ticker, days=365)
        if df is None or len(df) < 200:
            continue

        df = df.loc[start_date:end_date]
        vcp_score = is_valid_vcp(ticker)

        if vcp_score > 50:
            breakout_success = vcp_score > 70  

            market_strength = market_breadth_score()
            if market_strength < 60:  
                continue  

            sector_df = fetch_sector_data(ticker)
            if sector_df is not None and "c" in df.columns and "c" in sector_df.columns:
                sector_performance = df["c"].pct_change().sum() > sector_df["c"].pct_change().sum()
                if not sector_performance:
                    continue  

            results.append({
                "Stock": ticker,
                "VCP Score": vcp_score,
                "Breakout Success": breakout_success,
                "Market Strength": market_strength,
                "Outperformed Sector": sector_performance,
            })

    df_results = pd.DataFrame(results)
    success_rate = df_results["Breakout Success"].mean() * 100 if not df_results.empty else 0
    return success_rate, df_results



    

