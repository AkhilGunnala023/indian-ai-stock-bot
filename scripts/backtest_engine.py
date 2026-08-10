import pandas as pd
import numpy as np
from config.config import PROCESSED_DATA_DIR

DATA_FILE = PROCESSED_DATA_DIR / "nifty_60d_with_indicators.csv"


def backtest():
    df = pd.read_csv(DATA_FILE)

    # ------------------------
    # Prepare data
    # ------------------------
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["Symbol", "Date"])

    # Safety
    df = df.dropna(subset=["Close", "EMA_20", "EMA_50", "RSI_14"])

    # ------------------------
    # Next-day return
    # ------------------------
    df["Next_Close"] = df.groupby("Symbol")["Close"].shift(-1)
    df["Next_Day_Return_%"] = (
        (df["Next_Close"] - df["Close"]) / df["Close"] * 100
    )

    # ------------------------
    # Proxy Risk-On regime (technical regime)
    # ------------------------
    df["Risk_On_Regime"] = (
        (df["EMA_20"] > df["EMA_50"]) &
        (df["RSI_14"] > 45)
    )

    # Only evaluate Risk-On periods
    df = df[df["Risk_On_Regime"]]

    valid = df.dropna(subset=["Next_Day_Return_%"]).copy()

    # ------------------------
    # Bullish signal
    # ------------------------
    valid["Bullish_Signal"] = 1  # since already filtered

    total_signals = len(valid)

    if total_signals == 0:
        print("No Risk-On signals found.")
        return

    valid["Correct"] = np.where(
        valid["Next_Day_Return_%"] > 0,
        1,
        0
    )

    win_rate = valid["Correct"].mean() * 100
    avg_return = valid["Next_Day_Return_%"].mean()

    print("\n📊 BACKTEST RESULTS — TECHNICAL RISK-ON ONLY\n")
    print(f"Total Bullish Signals   : {total_signals}")
    print(f"Win Rate                : {win_rate:.2f}%")
    print(f"Average Next-Day Return : {avg_return:.2f}%")

    valid.to_csv("outputs/backtest_risk_on_results.csv", index=False)
    print("\nSaved: outputs/backtest_risk_on_results.csv")


if __name__ == "__main__":
    backtest()
