import json
import pandas as pd
import numpy as np
from xgboost import XGBClassifier

from config.config import (
    PROCESSED_DATA_DIR,
    FEATURE_COLUMNS_FILE,
    OUTPUT_DIR
)
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier

from config.config import PROBABILITY_THRESHOLD


DATA_FILE = PROCESSED_DATA_DIR / "nifty_1y_with_market_context.csv"


def walk_forward_backtest():

    df = pd.read_csv(DATA_FILE)

    df = df.sort_values(["Date", "Symbol"])

    df["Target"] = (
        df.groupby("Symbol")["Close"].shift(-1) > df["Close"]
    ).astype(int)


    df["Tomorrow_Return_%"] = (
        df.groupby("Symbol")["Daily_Return_%"].shift(-1)
    )

    with open(FEATURE_COLUMNS_FILE) as file:
        features = json.load(file)

    with open(FEATURE_COLUMNS_FILE) as file:
        features = json.load(file)

    required_columns = features + ["Target", "Tomorrow_Return_%"]

    df = df.dropna(subset=required_columns).reset_index(drop=True)

    with open(FEATURE_COLUMNS_FILE) as file:
        features = json.load(file)

    predictions = []

    feature_importance_sum = np.zeros(len(features))
    feature_importance_count = 0

    unique_dates = sorted(df["Date"].unique())

    # Use first 20 days for initial training
    for i in range(20, len(unique_dates)):
        train_dates = unique_dates[:i]

        test_date = unique_dates[i]

        train_df = df[df["Date"].isin(train_dates)]

        test_df = df[df["Date"] == test_date]

        X_train = train_df[features]
        y_train = train_df["Target"]

        X_test = test_df[features]
        y_test = test_df["Target"]

        model = XGBClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric="logloss"
        )

        model.fit(X_train, y_train)

        feature_importance_sum += model.feature_importances_
        feature_importance_count += 1

        probabilities_today = model.predict_proba(X_test)[:, 1]

        predictions_today = (
                probabilities_today >= PROBABILITY_THRESHOLD
        ).astype(int)

        for idx in range(len(test_df)):
            predictions.append({
                "Date": test_df.iloc[idx]["Date"],
                "Symbol": test_df.iloc[idx]["Symbol"],
                "Probability": probabilities_today[idx],
                "Prediction": predictions_today[idx],
                "Actual": y_test.iloc[idx],
                "Return_%": test_df.iloc[idx]["Tomorrow_Return_%"]
            })


    predictions_df = pd.DataFrame(predictions)

    predictions_df.to_csv(
        OUTPUT_DIR / "walk_forward_predictions.csv",
        index=False
    )

    print("✅ Saved: walk_forward_predictions.csv")

    buy_predictions = predictions_df[predictions_df["Prediction"] == 1]

    top5_predictions = (
        buy_predictions
        .sort_values(["Date", "Probability"], ascending=[True, False])
        .groupby("Date")
        .head(5)
        .reset_index(drop=True)
    )

    print("\nBUY Predictions :", len(buy_predictions))
    print("Top 5 Trades    :", len(top5_predictions))

    capital = 100000.0

    portfolio_history = []

    for trade_date, day_df in top5_predictions.groupby("Date"):

        allocation = capital / len(day_df)

        day_end_value = 0

        for _, row in day_df.iterrows():
            trade_value = allocation * (1 + row["Return_%"] / 100)

            day_end_value += trade_value

        capital = day_end_value

        portfolio_history.append({
            "Date": trade_date,
            "Capital": round(capital, 2)
        })
    portfolio_df = pd.DataFrame(portfolio_history)

    portfolio_df["Peak"] = portfolio_df["Capital"].cummax()

    portfolio_df["Drawdown"] = (
                                       (portfolio_df["Capital"] - portfolio_df["Peak"])
                                       / portfolio_df["Peak"]
                               ) * 100

    max_drawdown = portfolio_df["Drawdown"].min()

    portfolio_df.to_csv(
        OUTPUT_DIR / "portfolio_history.csv",
        index=False
    )

    print("✅ Saved: portfolio_history.csv")

    # Average feature importance
    avg_importance = feature_importance_sum / feature_importance_count

    feature_importance_df = pd.DataFrame({
        "Feature": features,
        "Importance": avg_importance
    })

    feature_importance_df = feature_importance_df.sort_values(
        "Importance",
        ascending=False
    )

    feature_importance_df.to_csv(
        OUTPUT_DIR / "feature_importance.csv",
        index=False
    )

    print("✅ Saved: feature_importance.csv")

    roi = ((capital - 100000) / 100000) * 100

    summary = {
        "Model": "XGBoost",
        "Probability Threshold": PROBABILITY_THRESHOLD,
        "Initial Capital": 100000,
        "Final Capital": round(capital, 2),
        "ROI (%)": round(roi, 2),
        "Maximum Drawdown (%)": round(max_drawdown, 2),
        "BUY Signals": len(buy_predictions),
        "Trades Executed": len(top5_predictions),
        "Total Predictions": len(predictions_df)
    }

    with open(
            OUTPUT_DIR / "walk_forward_summary.json",
            "w"
    ) as file:
        json.dump(summary, file, indent=4)

    print("✅ Saved: walk_forward_summary.json")

    print("\n========== Walk Forward Backtest ==========")
    print(f"Initial Capital : ₹100,000.00")
    print(f"Final Capital   : ₹{capital:,.2f}")
    print(f"ROI             : {roi:.2f}%")
    print(f"Maximum Drawdown: {max_drawdown:.2f}%")
    print(f"BUY Signals     : {len(buy_predictions)}")
    print(f"Trades Executed : {len(top5_predictions)}")
    print(f"Threshold       : {PROBABILITY_THRESHOLD:.2f}")
    print("===========================================")



if __name__ == "__main__":
    walk_forward_backtest()