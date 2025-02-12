import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from vcp_detection import is_valid_vcp
from institutional import institutional_score
from market import market_breadth_score
from data_fetch import fetch_stock_data
from backtest import backtest_vcp  # ✅ Import the backtest function

def rank_best_trades(stocks):
    """Ranks top stocks based on VCP, institutional, and market scores, and backtest success rate."""
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
        
        # ✅ Fetch historical backtest success rate from YFinance
        success_rate, _ = backtest_vcp([stock])  

        final_score = (
            (vcp_score * 0.4) + 
            (institutional_strength * 0.3) + 
            (market_strength * 0.2) +
            (success_rate * 0.1)  # ✅ Give weight to historical success rate
        )

        return {
            "Stock": stock,
            "VCP Score": vcp_score,
            "Institutional Strength": institutional_strength,
            "Market Strength": market_strength,
            "Historical Success Rate": success_rate,
            "Final Confidence Score": round(final_score, 2)
        }

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(process_stock, stocks))

    return sorted([r for r in results if r], key=lambda x: x["Final Confidence Score"], reverse=True)[:20]







