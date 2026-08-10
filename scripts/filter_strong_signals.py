import pandas as pd
import os

from config.logger import logger
from config.config import (
    OUTPUT_DIR,
    AI_CONFIDENCE_THRESHOLD,
    STRONG_BUY_SCORE,
    BUY_SCORE,
    BUY_CANDIDATE_SCORE
)

INPUT_FILE = OUTPUT_DIR / "all_predictions.csv"

logger.info("Filtering strong buy signals")

def filter_strong_signals():
    preds = pd.read_csv(INPUT_FILE)

    # Initialize Technical Score
    preds["Technical_Score"] = 0
    preds["Reason"] = ""


    print("\n===== Probability Buckets =====")

    print(">= 0.60 :", (preds["Bullish_Probability"] >= 0.60).sum())
    print(">= 0.55 :", (preds["Bullish_Probability"] >= 0.55).sum())
    print(">= 0.50 :", (preds["Bullish_Probability"] >= 0.50).sum())
    print(">= 0.45 :", (preds["Bullish_Probability"] >= 0.45).sum())
    print(">= 0.40 :", (preds["Bullish_Probability"] >= 0.40).sum())

    print("\n===== Stocks with Probability >= 0.50 =====")
    print(
        preds.loc[
            preds["Bullish_Probability"] >= 0.50,
            [
                "Symbol",
                "Bullish_Probability",
                "EMA_20",
                "EMA_50",
                "RSI_14",
                "Volume_Spike_%"
            ]
        ]
    )

    # ==============================
    # Technical Score Calculation
    # ==============================

    # EMA Bullish
    mask = preds["EMA_Bullish"] == 1

    preds.loc[mask, "Technical_Score"] += 10
    preds.loc[mask, "Reason"] += "EMA Bullish | "

    # Strong Trend
    mask = preds["Strong_Trend"] == 1

    preds.loc[mask, "Technical_Score"] += 10
    preds.loc[mask, "Reason"] += "Strong Trend | "

    # RSI Above 50
    mask = preds["RSI_Above_50"] == 1

    preds.loc[mask, "Technical_Score"] += 10
    preds.loc[mask, "Reason"] += "RSI Above 50 | "

    # Breakout
    mask = preds["Breakout_20"] == 1

    preds.loc[mask, "Technical_Score"] += 15
    preds.loc[mask, "Reason"] += "20-Day Breakout | "

    # OBV Bullish
    mask = preds["OBV_Bullish"] == 1

    preds.loc[mask, "Technical_Score"] += 10
    preds.loc[mask, "Reason"] += "OBV Bullish | "

    # Relative Strength
    mask = preds["Relative_Strength_20D"] > 0

    preds.loc[mask, "Technical_Score"] += 10
    preds.loc[mask, "Reason"] += "Relative Strength | "

    # Volume Spike
    mask = preds["Volume_Spike_%"] >= 120

    preds.loc[mask, "Technical_Score"] += 10
    preds.loc[mask, "Reason"] += "Volume Spike | "

    # NIFTY EMA Bullish
    mask = preds["NIFTY_EMA_Bullish"] == 1

    preds.loc[mask, "Technical_Score"] += 10
    preds.loc[mask, "Reason"] += "Market EMA Bullish | "

    # NIFTY RSI Above 50
    mask = preds["NIFTY_RSI_Above_50"] == 1

    preds.loc[mask, "Technical_Score"] += 5
    preds.loc[mask, "Reason"] += "Market RSI > 50 | "

    # NIFTY MACD Positive
    mask = preds["NIFTY_MACD"] > 0

    preds.loc[mask, "Technical_Score"] += 10
    preds.loc[mask, "Reason"] += "Market MACD Positive | "

    # ==============================
    # AI Score
    # ==============================

    preds["AI_Score"] = preds["Bullish_Probability"] * 100

    # ==============================
    # Final Score
    # ==============================

    preds["Final_Score"] = (
            preds["AI_Score"] * 0.85 +
            preds["Technical_Score"] * 0.15
    )

    print("\n===== FINAL SCORE =====")

    print(
        preds[
            [
                "Symbol",
                "Bullish_Probability",
                "AI_Score",
                "Technical_Score",
                "Final_Score"
            ]
        ]
        .sort_values(
            "Final_Score",
            ascending=False
        )
        .head(20)
    )

    print("\n===== Technical Score =====")

    print(
        preds[
            [
                "Symbol",
                "Technical_Score"
            ]
        ]
        .sort_values(
            "Technical_Score",
            ascending=False
        )
        .head(20)
    )

    # ✅ DEFINE strong_buys CLEARLY
    print("\n===== FILTER ANALYSIS =====")

    strong_buys = preds.loc[
        (preds["Bullish_Probability"] >= AI_CONFIDENCE_THRESHOLD) &
        (preds["Final_Score"] >= BUY_CANDIDATE_SCORE)
        ].copy()

    strong_buys = strong_buys.sort_values(
        by="Final_Score",
        ascending=False
    )

    # Clean Reason column for Telegram
    strong_buys["Reason"] = (
        strong_buys["Reason"]
        .str.rstrip(" | ")
        .str.replace(" | ", "\n✅ ", regex=False)
    )

    strong_buys["Reason"] = "✅ " + strong_buys["Reason"]

    print(
        strong_buys[
            [
                "Symbol",
                "Bullish_Probability",
                "Final_Score",
                "Reason"
            ]
        ]
    )

    print(f"Final Strong Buys          : {len(strong_buys)}")

    def get_rating(score):
        if score >= STRONG_BUY_SCORE:
            return "⭐⭐⭐⭐⭐ Strong Buy"

        elif score >= BUY_SCORE:
            return "⭐⭐⭐⭐ Buy"

        elif score >= BUY_CANDIDATE_SCORE:
            return "⭐⭐⭐ Buy Candidate"

        else:
            return "Ignore"

    strong_buys["Rating"] = strong_buys["Final_Score"].apply(get_rating)

    output_file = OUTPUT_DIR / "strong_buy_signals.csv"
    strong_buys.to_csv(output_file, index=False)

    logger.info("\n STRONG BUY SIGNALS ")
    if strong_buys.empty:
        logger.info("No high-confidence trades today")
        print("No high-confidence trades today.")
    else:
        logger.info(
            strong_buys[
                ["Symbol", "Bullish_Probability", "RSI_14", "Volume_Spike_%"]
            ]
        )

    logger.info(f"Saved to: {output_file}")


if __name__ == "__main__":
    filter_strong_signals()
