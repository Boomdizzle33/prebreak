import pandas as pd
from vcp_detection import is_valid_vcp
from institutional import institutional_score
from market import market_breadth_score
from data_fetch import fetch_stock_data  

# ✅ Rank & Return Top 20 VCP Stocks
def rank_best_trades(stocks):
    trade_data = []

    for stock in stocks:
        df = fetch_stock_data(stock, days=50)
        if df is None:
            continue

        vcp_score = is_valid_vcp(stock)
        if vcp_score == 0:
            continue  

        institutional_strength = institutional_score(stock)
        market_strength = market_breadth_score()

        final_score = (vcp_score * 0.5) + (institutional_strength * 0.2) + (market_strength * 0.3)

        trade_data.append({
            "Stock": stock,
            "VCP Score": vcp_score,
            "Institutional Strength": institutional_strength,
            "Market Strength": market_strength,
            "Final Confidence Score": round(final_score, 2)
        })

    return sorted(trade_data, key=lambda x: x["Final Confidence Score"], reverse=True)[:20]




