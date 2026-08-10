import pandas as pd
import yfinance as yf
from datetime import timedelta

from config.config import OUTPUT_DIR
from config.logger import logger

TRACK_FILE = OUTPUT_DIR / "forward_tracking.csv"

logger.info("Updating prediction outcomes")

def get_next_day_return(symbol, trade_date):
    """
    Fetch next trading day's return using Yahoo Finance
    """
    ticker = f"{symbol}.NS"
    start = trade_date
    end = trade_date + timedelta(days=5)

    try:
        df = yf.download(
            ticker,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            progress=False
        )
        print(f"Checking {symbol}...")
    except Exception:
        return None

    if len(df) < 2:
        return None

    close = df["Close"]

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    entry_close = float(close.iloc[0])
    next_close = float(close.iloc[1])

    return (
        entry_close,
        next_close,
        round(((next_close - entry_close) / entry_close) * 100, 2)
    )


def update_outcomes():
    df = pd.read_csv(TRACK_FILE)
    df["Date"] = pd.to_datetime(df["Date"])

    updated = False

    for i, row in df.iterrows():

        if row["Action"] != "BUY" or row["Outcome"] != "PENDING":
            continue

        result = get_next_day_return(row["Symbol"], row["Date"])

        if result is None:
            continue

        entry_price, exit_price, ret = result

        df.loc[i, "Entry_Price"] = entry_price
        df.loc[i, "Exit_Price"] = exit_price
        df.loc[i, "Next_Day_Return_%"] = ret
        if ret > 0:
            outcome = "WIN"
        elif ret < 0:
            outcome = "LOSS"
        else:
            outcome = "BREAKEVEN"

        df.loc[i, "Outcome"] = outcome
        updated = True

    if updated:
        df.to_csv(TRACK_FILE, index=False)
        logger.info("Outcomes updated successfully.")
    else:
        logger.info("No pending trades to update.")

def get_performance_summary():
    """
    Returns AI performance statistics for Telegram.
    """

    if not TRACK_FILE.exists():
        return {
            "tracked": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "avg_return": 0.0
        }

    df = pd.read_csv(TRACK_FILE)

    # Consider only completed BUY trades
    df = df[
        (df["Action"] == "BUY") &
        (df["Outcome"].isin(["WIN", "LOSS", "BREAKEVEN"]))
        ]

    if df.empty:
        return {
            "tracked": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "avg_return": 0.0
        }

    tracked = len(df)
    wins = len(df[df["Outcome"] == "WIN"])
    losses = len(df[df["Outcome"] == "LOSS"])
    breakeven = len(df[df["Outcome"] == "BREAKEVEN"])

    return {
        "tracked": tracked,
        "wins": wins,
        "losses": losses,
        "breakeven": breakeven,
        "win_rate": round(wins / tracked * 100, 2),
        "avg_return": round(df["Next_Day_Return_%"].mean(), 2)
    }


if __name__ == "__main__":
    update_outcomes()
