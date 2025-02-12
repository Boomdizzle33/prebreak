import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from vcp_detection import is_valid_vcp
from institutional import institutional_score
from market import market_breadth_score
from data_fetch import fetch_stock_data

# ✅ Fetch Sector Performance
SECTOR_MAP = {
    "AAPL": "XLK", "MSFT": "XLK", "NVDA": "XLK",
    "XOM": "XLE", "CVX": "XLE",
    "JPM": "XLF", "GS": "XLF",
    "PFE": "XLV", "JNJ": "XLV"
}

def fetch_sector_performance(ticker):
    """Fetch sector ETF data for comparison with individual stock performance."""
    sector_ticker = SECTOR_MAP.get(ticker, "SPY")  # Default to SPY if unknown sector
    sector_data = fetch_stock_data(sector_ticker, days=200)
    return sector_data

def rank_best_trades(stocks):
    """Ranks top 20 stocks based on VCP, institutional, and market scores with sector confirmation."""
    trade_data = []
    market_strength = market_breadth_score()

    def process_stock(stock):
        df = fetch_stock_data(stock, days=50)
        if df is None:
            return None

        vcp_score = is_valid_vcp(stock)
        if vcp_score == 0:
            return None

        institutional_strength = institutional_score(stock)
        sector_df = fetch_sector_performance(stock)
        if sector_df is None:
            return None

        stock_performance = df['c'].pct_change().sum()
        sector_performance = sector_df['c'].pct_change().sum()
        outperforms_sector = stock_performance > sector_performance

        final_score = (
            (vcp_score * 0.4) + 
            (institutional_strength * 0.3) + 
            (market_strength * 0.2) +
            (outperforms_sector * 0.1)  # Small weight to sector outperformance
        )

        return {
            "Stock": stock,
            "VCP Score": vcp_score,
            "Institutional Strength": institutional_strength,
            "Market Strength": market_strength,
            "Sector Outperformance": outperforms_sector,
            "Final Confidence Score": round(final_score, 2)
        }

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(process_stock, stocks))

    return sorted([r for r in results if r], key=lambda x: x["Final Confidence Score"], reverse=True)[:20]






