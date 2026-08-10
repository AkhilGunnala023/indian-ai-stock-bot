import yfinance as yf
import pandas as pd
from datetime import date
import os

from config.config import RAW_DATA_DIR
from stock_lists.loader import STOCKS



def fetch_and_save():
    all_data = []
    failed_symbols = []

    for symbol in STOCKS:
        print(f"Fetching {symbol}")
        try:
            df = yf.Ticker(symbol).history(period="2d")

            if df.empty:
                print(f"No data for {symbol}")
                failed_symbols.append(symbol)
                continue

            df = df.reset_index()

            # Keep only completed trading days
            df = df[df["Close"].notna()]

            if df.empty:
                print(f"No completed EOD data for {symbol}")
                continue

            # Latest completed trading day
            df = df.tail(1) # take latest trading day only

            df["Symbol"] = symbol.replace(".NS", "")

            df = df[["Date", "Symbol", "Open", "High", "Low", "Close", "Volume"]]

            all_data.append(df)


        except Exception as e:

            print(f"Error fetching {symbol}: {e}")

            failed_symbols.append(symbol)

    final_df = pd.concat(all_data, ignore_index=True)

    # ✅ DEBUG CHECK
    print("\n===== DATA PREVIEW =====")
    print(final_df.head())

    print("\n===== COLUMNS =====")
    print(final_df.columns)

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    file_name = RAW_DATA_DIR / f"nifty_eod_{date.today()}.csv"

    final_df.to_csv(file_name, index=False)

    print(f"\nSaved EOD data to {file_name}")

    print("\n========== FAILED SYMBOLS ==========")

    if failed_symbols:
        for symbol in failed_symbols:
            print(symbol)
    else:
        print("None")

if __name__ == "__main__":
    fetch_and_save()
