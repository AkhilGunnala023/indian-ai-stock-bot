import pandas as pd
import os
from datetime import datetime
from config.config import OUTPUT_DIR
from config.logger import logger

TRACK_FILE = OUTPUT_DIR / "forward_tracking.csv"

logger.info("Forward tracking started")

def log_predictions(df, global_regime, threshold):
    today = datetime.now().strftime("%Y-%m-%d")

    rows = []

    if df.empty:
        rows.append({
            "Date": today,
            "Symbol": "ALL",
            "AI_Probability": None,
            "Action": "NO_TRADE",
            "Reason": f"Global={global_regime}, Threshold={threshold}",
            "Next_Day_Return_%": None,
            "Outcome": "NA"
        })
    else:
        for _, row in df.iterrows():
            rows.append({
                "Date": today,
                "Symbol": row["Symbol"],

                "AI_Probability": round(row["Bullish_Probability"], 4),
                "Final_Score": round(row["Final_Score"], 2),
                "Technical_Score": round(row["Technical_Score"], 2),

                "Action": "BUY",

                "Reason": f"Prob>={threshold}",

                "Entry_Price": row["Close"],

                "Exit_Price": None,

                "Next_Day_Return_%": None,

                "Outcome": "PENDING"
            })

    log_df = pd.DataFrame(rows)

    if os.path.exists(TRACK_FILE):

        existing_df = pd.read_csv(TRACK_FILE)

        # Remove today's duplicate predictions
        existing_df = existing_df[
            ~(
                    (existing_df["Date"] == today) &
                    (existing_df["Symbol"].isin(log_df["Symbol"]))
            )
        ]

        final_df = pd.concat(
            [existing_df, log_df],
            ignore_index=True
        )

        final_df.to_csv(TRACK_FILE, index=False)

    else:

        log_df.to_csv(TRACK_FILE, index=False)

    logger.info("Forward tracking updated.")


if __name__ == "__main__":
    logger.info("Run this via send_telegram_alert pipeline.")
