import joblib
import json
import pandas as pd
from sklearn.metrics import accuracy_score

from config.config import (
    PROCESSED_DATA_DIR,
    MODEL_FILE,
    OUTPUT_DIR,
    FEATURE_COLUMNS_FILE
)
from config.logger import logger

def backtest_model():
    model = joblib.load(MODEL_FILE)

    logger.info("Saved model loaded successfully")

    DATA_FILE = PROCESSED_DATA_DIR / "nifty_60d_with_market_context.csv"

    df = pd.read_csv(DATA_FILE)

    logger.info("Historical data loaded")

    with open(FEATURE_COLUMNS_FILE, "r") as file:
        FEATURES = json.load(file)

    df = df.sort_values(by=["Symbol", "Date"])

    df["Target"] = (
            df.groupby("Symbol")["Close"].shift(-1) > df["Close"]
    ).astype(int)

    df["Next_Close"] = df.groupby("Symbol")["Close"].shift(-1)

    df["Return_Percentage"] = (
                                      (df["Next_Close"] - df["Close"]) / df["Close"]
                              ) * 100

    df = df.dropna().reset_index(drop=True)

    X = df[FEATURES]
    y = df["Target"]

    # Prediction probabilities
    df["Probability"] = model.predict_proba(X)[:, 1]

    y_pred = model.predict(X)

    df["Prediction"] = y_pred

    # ===============================
    # Trading Performance
    # ===============================

    # Top 5 predictions every trading day
    bullish_trades = (
        df.groupby("Date", group_keys=False)
        .apply(lambda x: x.nlargest(5, "Probability"), include_groups=False)
        .reset_index(drop=True)
    )

    total_trades = len(bullish_trades)

    total_return = bullish_trades["Return_Percentage"].sum()

    average_return = bullish_trades["Return_Percentage"].mean()

    best_trade = bullish_trades["Return_Percentage"].max()

    worst_trade = bullish_trades["Return_Percentage"].min()

    accuracy = accuracy_score(y, y_pred)

    total_predictions = len(y)
    correct_predictions = (y == y_pred).sum()
    wrong_predictions = total_predictions - correct_predictions

    win_rate = (correct_predictions / total_predictions) * 100
    loss_rate = (wrong_predictions / total_predictions) * 100

    report = {
        "total_predictions": int(total_predictions),
        "correct_predictions": int(correct_predictions),
        "wrong_predictions": int(wrong_predictions),
        "win_rate": float(round(win_rate, 2)),
        "loss_rate": float(round(loss_rate, 2)),
        "total_trades": int(total_trades),
        "total_return": float(round(total_return, 2)),
        "average_return": float(round(average_return, 2)),
        "best_trade": float(round(best_trade, 2)),
        "worst_trade": float(round(worst_trade, 2))
    }

    report_file = OUTPUT_DIR / "backtest_report.json"

    with open(report_file, "w") as file:
        json.dump(report, file, indent=4)

    logger.info(f"Backtest report saved to: {report_file}")
    print(f"\nBacktest report saved to: {report_file}")

    print("\n========== BACKTEST REPORT ==========")
    print(f"Total Predictions   : {total_predictions}")
    print(f"Correct Predictions : {correct_predictions}")
    print(f"Wrong Predictions   : {wrong_predictions}")
    print(f"Win Rate            : {win_rate:.2f}%")
    print(f"Loss Rate           : {loss_rate:.2f}%")
    print("====================================")

    print("\n========== TRADING PERFORMANCE ==========")
    print(f"Total Trades       : {total_trades}")
    print(f"Total Return (%)   : {total_return:.2f}")
    print(f"Average Return (%) : {average_return:.2f}")
    print(f"Best Trade (%)     : {best_trade:.2f}")
    print(f"Worst Trade (%)    : {worst_trade:.2f}")
    print("=========================================")

    logger.info(f"Backtest Accuracy: {accuracy:.2f}")


if __name__ == "__main__":
    backtest_model()