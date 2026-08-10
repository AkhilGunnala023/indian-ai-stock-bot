import pandas as pd
from config.config import PROCESSED_DATA_DIR


def merge_market_context():

    # Stock data
    stock_df = pd.read_csv(
        PROCESSED_DATA_DIR / "nifty_1y_data.csv"
    )

    # Market data
    market_df = pd.read_csv(
        PROCESSED_DATA_DIR / "nifty_market_data.csv"
    )

    # Convert Date columns
    stock_df["Date"] = pd.to_datetime(stock_df["Date"])
    market_df["Date"] = pd.to_datetime(market_df["Date"])

    market_df = (
        market_df
        .set_index("Date")
        .asfreq("D")
        .ffill()
        .reset_index()
    )

    print("Stock Start :", stock_df["Date"].min())
    print("Stock End   :", stock_df["Date"].max())

    print("Market Start:", market_df["Date"].min())
    print("Market End  :", market_df["Date"].max())

    missing_dates = stock_df.loc[
        ~stock_df["Date"].isin(market_df["Date"]),
        "Date"
    ].drop_duplicates()

    print("\nMissing Dates:")
    print(missing_dates)
    print("Missing Date Count:", len(missing_dates))

    # Merge
    merged_df = stock_df.merge(
        market_df[
            [
                "Date",
                "NIFTY_EMA_20",
                "NIFTY_EMA_50",
                "NIFTY_EMA_Bullish",
                "NIFTY_MACD",
                "NIFTY_Price_EMA20_Distance_%",
                "NIFTY_Daily_Return_%",
                "NIFTY_Return_5D_%",
                "NIFTY_Return_20D_%",
                "NIFTY_RSI_14",
                "NIFTY_RSI_Above_50"
            ]
        ],
        on="Date",
        how="left",
    )

    merged_df["Relative_Strength_5D"] = (
            merged_df["Return_5D_%"] -
            merged_df["NIFTY_Return_5D_%"]
    )

    merged_df["Relative_Strength_20D"] = (
            merged_df["Return_20D_%"] -
            merged_df["NIFTY_Return_20D_%"]
    )

    duplicates = merged_df.duplicated(
        subset=["Date", "Symbol"]
    ).sum()

    print("\n========== MERGE SUMMARY ==========")

    print("Rows        :", len(merged_df))
    print("Columns     :", len(merged_df.columns))
    print("Duplicates  :", duplicates)

    print("\nMissing Values")
    print(merged_df.isnull().sum())

    print("\nMarket Features")

    print(
        merged_df[
            [
                "Date",
                "NIFTY_EMA_20",
                "NIFTY_EMA_50",
                "NIFTY_EMA_Bullish",
                "NIFTY_MACD",
                "NIFTY_Price_EMA20_Distance_%",
                "NIFTY_Daily_Return_%",
                "NIFTY_Return_5D_%",
                "NIFTY_Return_20D_%",
                "NIFTY_RSI_14",
                "NIFTY_RSI_Above_50"
            ]
        ].head()
    )

    print("\n===== Relative Strength =====")
    print(
        merged_df[
            [
                "Symbol",
                "Relative_Strength_5D",
                "Relative_Strength_20D"
            ]
        ].head()
    )

    # Save
    output_file = (
        PROCESSED_DATA_DIR /
        "nifty_1y_with_market_context.csv"
    )

    merged_df.to_csv(output_file, index=False)

    print(f"\nMerged Successfully!")
    print(f"Saved to : {output_file}")


if __name__ == "__main__":
    merge_market_context()