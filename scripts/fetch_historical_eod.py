import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import date
from config.config import PROCESSED_DATA_DIR
from config.logger import logger
from stock_lists.loader import STOCKS

logger.info("Fetching historical market data")


def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def fetch_historical_data():
    all_data = []
    failed_symbols = []

    total = len(STOCKS)

    for i, symbol in enumerate(STOCKS, start=1):

        print(f"[{i}/{total}] Downloading {symbol}")
        try:
            df = yf.Ticker(symbol).history(period="1y")

            if df.empty:
                print(f"No data for {symbol}")
                failed_symbols.append(symbol)
                continue

            df = df.reset_index()
            df["Symbol"] = symbol.replace(".NS", "")

            df = df[["Date", "Symbol", "Open", "High", "Low", "Close", "Volume"]]
            all_data.append(df)


        except Exception as e:

            print(f"Error fetching {symbol}: {e}")

            failed_symbols.append(symbol)

    final_df = pd.concat(all_data, ignore_index=True)

    # Clean date
    final_df["Date"] = pd.to_datetime(final_df["Date"]).dt.date
    final_df = final_df.sort_values(by=["Symbol", "Date"])

    # Indicators
    result = []
    for symbol, group in final_df.groupby("Symbol"):
        group = group.copy()

        group["EMA_20"] = group["Close"].ewm(span=20, adjust=False).mean()
        group["EMA_50"] = group["Close"].ewm(span=50, adjust=False).mean()
        group["EMA_Bullish"] = (
                group["EMA_20"] > group["EMA_50"]
        ).astype(int)
        group["Price_EMA20_Distance_%"] = (
                                                  (group["Close"] - group["EMA_20"]) / group["EMA_20"]
                                          ) * 100
        # MACD
        group["EMA_12"] = group["Close"].ewm(span=12, adjust=False).mean()
        group["EMA_26"] = group["Close"].ewm(span=26, adjust=False).mean()
        group["MACD"] = group["EMA_12"] - group["EMA_26"]
        group["MACD_Signal"] = group["MACD"].ewm(span=9, adjust=False).mean()

        # ATR (Average True Range)

        group["Previous_Close"] = group["Close"].shift(1)

        group["TR"] = (
            pd.concat([
                group["High"] - group["Low"],
                (group["High"] - group["Previous_Close"]).abs(),
                (group["Low"] - group["Previous_Close"]).abs()
            ], axis=1)
            .max(axis=1)
        )

        group["ATR_14"] = group["TR"].rolling(window=14).mean()
        # ---------- ADX ----------

        group["+DM"] = group["High"].diff()
        group["-DM"] = -group["Low"].diff()

        group["+DM"] = group["+DM"].where(
            (group["+DM"] > group["-DM"]) & (group["+DM"] > 0),
            0
        )

        group["-DM"] = group["-DM"].where(
            (group["-DM"] > group["+DM"]) & (group["-DM"] > 0),
            0
        )

        plus_di = 100 * (
                group["+DM"].rolling(14).mean() / group["ATR_14"]
        )

        minus_di = 100 * (
                group["-DM"].rolling(14).mean() / group["ATR_14"]
        )

        dx = (
                     (plus_di - minus_di).abs() /
                     (plus_di + minus_di)
             ) * 100

        group["ADX_14"] = dx.rolling(14).mean()
        group["Strong_Trend"] = (
                group["ADX_14"] > 25
        ).astype(int)
        group["RSI_14"] = calculate_rsi(group["Close"])
        group["RSI_Above_50"] = (
                group["RSI_14"] > 50
        ).astype(int)
        group["Daily_Return_%"] = (
                group["Close"].pct_change(fill_method=None) * 100
        )
        # 5-Day Return
        group["Return_5D_%"] = (
                                   (group["Close"] / group["Close"].shift(5) - 1)
                               ) * 100

        # 20-Day Return
        group["Return_20D_%"] = (
                                    (group["Close"] / group["Close"].shift(20) - 1)
                                ) * 100
        group["Avg_Volume_20"] = group["Volume"].rolling(20).mean()
        group["Volume_Spike_%"] = (group["Volume"] / group["Avg_Volume_20"]) * 100
        # ==========================
        # On Balance Volume (OBV)
        # ==========================

        group["OBV"] = (
            (
                    np.sign(group["Close"].diff())
                    .fillna(0)
                    * group["Volume"]
            )
        ).cumsum()
        # OBV EMA 20
        group["OBV_EMA_20"] = (
            group["OBV"]
            .ewm(span=20, adjust=False)
            .mean()
        )
        group["OBV_Bullish"] = (
                group["OBV"] >
                group["OBV_EMA_20"]
        ).astype(int)

        # Highest High of previous 20 trading days
        group["High_20"] = (
            group["High"]
            .rolling(window=20)
            .max()
            .shift(1)
        )
        # Lowest Low of previous 20 trading days
        group["Low_20"] = (
            group["Low"]
            .rolling(window=20)
            .min()
            .shift(1)
        )
        group["Breakout_20"] = (
                group["Close"] > group["High_20"]
        ).astype(int)
        group["Breakdown_20"] = (
                group["Close"] < group["Low_20"]
        ).astype(int)
        group["Distance_From_High20_%"] = (
                                                  (group["High_20"] - group["Close"])
                                                  / group["High_20"]
                                          ) * 100

        group["Distance_From_Low20_%"] = (
                                                 (group["Close"] - group["Low_20"])
                                                 / group["Low_20"]
                                         ) * 100

        result.append(group)

    final_df = pd.concat(result, ignore_index=True)

    # Drop rows with insufficient history
    final_df = final_df.dropna().reset_index(drop=True)

    duplicates = final_df.duplicated(
        subset=["Date", "Symbol"]
    ).sum()

    print(f"Duplicate Rows : {duplicates}")

    print("\nMissing Values")
    print(final_df.isnull().sum())

    print(
        "Unique Stocks :",
        final_df["Symbol"].nunique()
    )

    print(
        "Start Date:",
        final_df["Date"].min()
    )

    print(
        "End Date:",
        final_df["Date"].max()
    )

    os.makedirs("data/processed", exist_ok=True)
    output_file = PROCESSED_DATA_DIR / "nifty_1y_data.csv"
    print("Dataset Shape:", final_df.shape)
    final_df.to_csv(output_file, index=False)

    print("\n========== DATA SUMMARY ==========")

    print("Rows          :", len(final_df))
    print("Stocks        :", final_df["Symbol"].nunique())
    print("Columns       :", len(final_df.columns))
    print("Duplicates    :", duplicates)
    print("Failed Stocks :", len(failed_symbols))
    print("Start Date    :", final_df["Date"].min())
    print("End Date      :", final_df["Date"].max())

    logger.info("\n===== DAY 3 DATA READY =====")
    logger.info(final_df.tail())
    logger.info(f"Saved to: {output_file}")

    print("\n========== FAILED SYMBOLS ==========")

    if failed_symbols:
        for symbol in failed_symbols:
            print(symbol)
    else:
        print("None")

if __name__ == "__main__":
    fetch_historical_data()
