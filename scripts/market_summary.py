import yfinance as yf
import pandas as pd

from config.config import PROCESSED_DATA_DIR
from config.logger import logger

logger.info("Generating market summary")

def build_market_summary():
    nifty = yf.download("^NSEI", period="30d", interval="1d", progress=False)

    if nifty.empty:
        logger.info("NIFTY data not available")
        return

    nifty["EMA_20"] = nifty["Close"].ewm(span=20).mean()

    latest_close = nifty["Close"].iloc[-1].item()
    latest_ema20 = nifty["EMA_20"].iloc[-1].item()

    if latest_close > latest_ema20:
        nifty_trend = "Above 20 EMA (Bullish)"
    else:
        nifty_trend = "Below 20 EMA (Weak)"

    # Simple breadth proxy (lightweight & safe)
    market_breadth = "Weak breadth"
    try:
        etf = yf.download("NIFTYBEES.NS", period="5d", interval="1d", progress=False)
        if not etf.empty:
            market_breadth = "Moderate breadth"
    except:
        pass

    df = pd.DataFrame([{
        "NIFTY_Trend": nifty_trend,
        "Market_Breadth": market_breadth
    }])

    df.to_csv(PROCESSED_DATA_DIR / "market_summary.csv", index=False)
    logger.info("Market summary saved.")


if __name__ == "__main__":
    build_market_summary()
