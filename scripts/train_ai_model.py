import json

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)
from config.config import (
    PROCESSED_DATA_DIR,
    MODEL_FILE,
    OUTPUT_DIR,
    FEATURE_COLUMNS_FILE,
    AI_CONFIDENCE_THRESHOLD
)
from config.logger import logger


logger.info("Model training started")

DATA_FILE = PROCESSED_DATA_DIR / "nifty_1y_with_market_context.csv"


def build_ai_model():
    df = pd.read_csv(DATA_FILE)

    # Sort data
    df = df.sort_values(by=["Symbol", "Date"])

    # Keep original dataframe for latest prediction
    df_all = df.copy()

    # Training dataframe
    df = df.copy()

    # Calculate next day return
    df["Next_Day_Return_%"] = (
                                      (
                                              df.groupby("Symbol")["Close"].shift(-1) - df["Close"]
                                      ) / df["Close"]
                              ) * 100

    # Target = 1 only if next day's return is at least 1%
    df["Target"] = (df["Next_Day_Return_%"] >= 1.0).astype(int)

    # Remove last row of each stock
    df = df.dropna().reset_index(drop=True)

    print("\n===== Target Distribution =====")
    print(df["Target"].value_counts())
    print(df["Target"].value_counts(normalize=True))

    with open(FEATURE_COLUMNS_FILE, "r") as file:
        feature_columns = json.load(file)

    print("\n===== FEATURES USED FOR TRAINING =====")
    for i, feature in enumerate(feature_columns, start=1):
        print(f"{i}. {feature}")

    print(f"\nTotal Features: {len(feature_columns)}")

    X_train_list = []
    X_test_list = []
    y_train_list = []
    y_test_list = []

    for symbol, group in df.groupby("Symbol"):
        group = group.sort_values("Date")

        split_index = int(len(group) * 0.8)

        train_group = group.iloc[:split_index]
        test_group = group.iloc[split_index:]

        X_train_list.append(train_group[feature_columns])
        X_test_list.append(test_group[feature_columns])

        y_train_list.append(train_group["Target"])
        y_test_list.append(test_group["Target"])

    X_train = pd.concat(X_train_list, ignore_index=True)
    X_test = pd.concat(X_test_list, ignore_index=True)

    y_train = pd.concat(y_train_list, ignore_index=True)
    y_test = pd.concat(y_test_list, ignore_index=True)

    X_train_final, X_valid, y_train_final, y_valid = train_test_split(
        X_train,
        y_train,
        test_size=0.20,
        shuffle=False
    )

    negative = (y_train == 0).sum()
    positive = (y_train == 1).sum()

    scale_pos_weight = (
        negative / positive
        if positive > 0
        else 1
    )

    print(f"Negative Samples : {negative}")
    print(f"Positive Samples : {positive}")
    print(f"Scale Pos Weight : {scale_pos_weight:.2f}")


    # Train Model
    # Hyperparameter Search

    model = XGBClassifier(
        n_estimators=1000,
        max_depth=4,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.9,
        min_child_weight=3,
        gamma=0.1,
        reg_alpha=1,
        reg_lambda=2,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
        scale_pos_weight=scale_pos_weight,
        early_stopping_rounds=30
    )

    model.fit(
        X_train_final,
        y_train_final,
        eval_set=[(X_valid, y_valid)],
        verbose=False
    )

    print("Best iteration:", model.best_iteration)
    print("Best score:", model.best_score)
    logger.info(f"Best iteration : {model.best_iteration}")
    logger.info(f"Best score : {model.best_score}")

    importance = pd.DataFrame({
        "Feature": feature_columns,
        "Importance": model.feature_importances_
    }).sort_values("Importance", ascending=False)

    importance.to_csv(
        OUTPUT_DIR / "feature_importance.csv",
        index=False
    )

    print("\nFeature Importance:")
    print(importance)


    # Save Model
    joblib.dump(model, MODEL_FILE)
    logger.info(f"Model saved to: {MODEL_FILE}")
    print(f"Model saved to: {MODEL_FILE}")

    # Predictions
    y_prob = model.predict_proba(X_test)[:, 1]

    # Use production threshold
    y_pred = (
            y_prob >= AI_CONFIDENCE_THRESHOLD
    ).astype(int)

    print("\n===== TEST SET PROBABILITY DISTRIBUTION =====")
    print(pd.Series(y_prob).describe())

    print("\nProbability Buckets")
    for t in [0.50, 0.55, 0.60, 0.65, 0.70, 0.75]:
        print(f">= {t:.2f} : {(y_prob >= t).sum()}")

    print("\n===== THRESHOLD ANALYSIS =====")

    for threshold in [0.50, 0.55, 0.60, 0.65, 0.70]:
        pred = (y_prob >= threshold).astype(int)

        tp = ((pred == 1) & (y_test == 1)).sum()
        fp = ((pred == 1) & (y_test == 0)).sum()

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0

        print(
            f"Threshold {threshold:.2f} | "
            f"Signals={(pred == 1).sum():5d} | "
            f"Precision={precision:.3f}"
        )

    # Evaluation Metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)

    # Save metrics to JSON
    # Save metrics to JSON
    metrics = {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),

        "best_iteration": int(model.best_iteration),
        "best_score": round(float(model.best_score), 6)
    }

    metrics_file = OUTPUT_DIR / "model_metrics.json"

    with open(metrics_file, "w") as file:
        json.dump(metrics, file, indent=4)

    logger.info(f"Metrics saved to: {metrics_file}")
    print(f"Metrics saved to: {metrics_file}")

    # Console Output
    print(f"\nAccuracy : {accuracy:.2f}")
    print(f"Precision: {precision:.2f}")
    print(f"Recall   : {recall:.2f}")
    print(f"F1 Score : {f1:.2f}")
    print("\nConfusion Matrix:")
    print(cm)

    # Log Output
    logger.info(f"Accuracy : {accuracy:.2f}")
    logger.info(f"Precision: {precision:.2f}")
    logger.info(f"Recall   : {recall:.2f}")
    logger.info(f"F1 Score : {f1:.2f}")
    logger.info(f"\nConfusion Matrix:\n{cm}")

    # Latest data prediction
    latest_data = df_all.groupby("Symbol").tail(1).copy()

    print("\n===== Today's Top 20 Probability Distribution =====")
    print(
        latest_data[["Symbol"]]
        .assign(Probability=model.predict_proba(latest_data[feature_columns])[:, 1])
        .sort_values("Probability", ascending=False)
        .head(20)
    )

    probs = model.predict_proba(latest_data[feature_columns])[:, 1]

    latest_data["Bullish_Probability"] = probs

    # Sort all predictions
    all_predictions = latest_data.sort_values(
        by="Bullish_Probability",
        ascending=False
    )

    logger.info(all_predictions["Bullish_Probability"].describe())

    logger.info(
        all_predictions[["Symbol", "Bullish_Probability"]]
        .sort_values("Bullish_Probability", ascending=False)
        .head(20)
    )

    # Save all predictions
    output_file = OUTPUT_DIR / "all_predictions.csv"
    all_predictions.to_csv(output_file, index=False)

    # Logs
    print("\nTOP PREDICTIONS:\n")
    print(all_predictions[["Symbol", "Bullish_Probability"]].head(10))
    all_predictions.head(20).to_csv(
        OUTPUT_DIR / "top20_predictions.csv",
        index=False
    )

    logger.info("All predictions generated")
    logger.info(f"Saved to: {output_file}")


if __name__ == "__main__":
    build_ai_model()