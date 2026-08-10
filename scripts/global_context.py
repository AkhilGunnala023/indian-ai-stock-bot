import yfinance as yf
import pandas as pd
from config.config import PROCESSED_DATA_DIR
from config.logger import logger

logger.info("Calculating global market context")

GLOBAL_SYMBOLS = {
    "SP500": "^GSPC",
    "VIX": "^VIX",
    "DXY": "DX-Y.NYB"
}


def fetch_latest_close(symbol):
    df = yf.download(
        symbol,
        period="5d",
        interval="1d",
        progress=False
    )

    if df.empty:
        return None

    return df["Close"].iloc[-1].item()


def build_global_context():
    context = {}

    for name, symbol in GLOBAL_SYMBOLS.items():
        context[name] = fetch_latest_close(symbol)

    risk_score = 0

    # VIX logic
    if context["VIX"] is not None and context["VIX"] < 20:
        risk_score += 1

    # S&P 500 data available
    if context["SP500"] is not None:
        risk_score += 1

    # Dollar Index logic
    if context["DXY"] is not None and context["DXY"] < 105:
        risk_score += 1

    regime = "Risk-On" if risk_score >= 2 else "Risk-Off"

    df = pd.DataFrame([{
        "SP500": context["SP500"],
        "VIX": context["VIX"],
        "DXY": context["DXY"],
        "Global_Regime": regime
    }])

    df.to_csv(PROCESSED_DATA_DIR / "global_context.csv", index=False)
    logger.info("Global context saved.")


if __name__ == "__main__":
    build_global_context()
