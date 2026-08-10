import pandas as pd
from config.config import OUTPUT_DIR

TRACK_FILE = OUTPUT_DIR / "forward_tracking.csv"


def get_basic_statistics():
    if not TRACK_FILE.exists():
        return None

    df = pd.read_csv(TRACK_FILE)

    df = df[
        (df["Action"] == "BUY") &
        (df["Outcome"] != "NA")
    ]

    if df.empty:
        return None

    return {
        "Predictions": len(df),
        "Wins": len(df[df["Outcome"] == "WIN"]),
        "Losses": len(df[df["Outcome"] == "LOSS"]),
        "WinRate": round(
            len(df[df["Outcome"] == "WIN"]) / len(df) * 100,
            2
        ),
        "AverageReturn": round(
            df["Next_Day_Return_%"].mean(),
            2
        )
    }

if __name__ == "__main__":
    print(get_basic_statistics())