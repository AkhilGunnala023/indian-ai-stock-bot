import yfinance as yf
from config.config import PROCESSED_DATA_DIR

def fetch_market_context():
    # Download NIFTY Index
    nifty = yf.download(
        "^NSEI",
        period="5y",
        interval="1d",
        auto_adjust=False
    )

    # Flatten MultiIndex columns if present
    if hasattr(nifty.columns, "levels"):
        nifty.columns = nifty.columns.get_level_values(0)

    # Keep only required columns
    nifty = nifty.reset_index()

    # Remove Adj Close
    if "Adj Close" in nifty.columns:
        nifty.drop(columns=["Adj Close"], inplace=True)

    nifty.columns.name = None

    # EMA 20
    nifty["NIFTY_EMA_20"] = nifty["Close"].ewm(span=20, adjust=False).mean()

    # EMA 50
    nifty["NIFTY_EMA_50"] = nifty["Close"].ewm(span=50, adjust=False).mean()

    nifty["NIFTY_EMA_Bullish"] = (
            nifty["NIFTY_EMA_20"] > nifty["NIFTY_EMA_50"]
    ).astype(int)

    # MACD
    nifty["EMA_12"] = nifty["Close"].ewm(span=12, adjust=False).mean()
    nifty["EMA_26"] = nifty["Close"].ewm(span=26, adjust=False).mean()
    nifty["NIFTY_MACD"] = nifty["EMA_12"] - nifty["EMA_26"]

    # Daily Return
    nifty["NIFTY_Daily_Return_%"] = nifty["Close"].pct_change() * 100

    # 5-Day Return
    nifty["NIFTY_Return_5D_%"] = (
                                     (nifty["Close"] / nifty["Close"].shift(5) - 1)
                                 ) * 100

    # 20-Day Return
    nifty["NIFTY_Return_20D_%"] = (
                                      (nifty["Close"] / nifty["Close"].shift(20) - 1)
                                  ) * 100

    # RSI 14
    delta = nifty["Close"].diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss

    nifty["NIFTY_RSI_14"] = 100 - (100 / (1 + rs))

    nifty["NIFTY_RSI_Above_50"] = (
            nifty["NIFTY_RSI_14"] > 50
    ).astype(int)

    nifty["NIFTY_Price_EMA20_Distance_%"] = (
                                                    (nifty["Close"] - nifty["NIFTY_EMA_20"])
                                                    / nifty["NIFTY_EMA_20"]
                                            ) * 100

    nifty = nifty.dropna().reset_index(drop=True)

    duplicates = nifty.duplicated(subset=["Date"]).sum()

    nifty = nifty[
        [
            "Date",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "NIFTY_EMA_20",
            "NIFTY_EMA_50",
            "NIFTY_EMA_Bullish",
            "NIFTY_MACD",
            "NIFTY_Price_EMA20_Distance_%",
            "NIFTY_Daily_Return_%",
            "NIFTY_RSI_14",
            "NIFTY_RSI_Above_50",
            "NIFTY_Return_5D_%",
            "NIFTY_Return_20D_%",
        ]
    ]

    duplicates = nifty.duplicated(subset=["Date"]).sum()

    print("\n========== MARKET CONTEXT ==========")
    print("Rows        :", len(nifty))
    print("Columns     :", len(nifty.columns))
    print("Duplicates  :", duplicates)

    print("\nMissing Values")
    print(nifty.isnull().sum())

    print("Start Date :", nifty["Date"].min())
    print("End Date   :", nifty["Date"].max())

    # Save
    output_file = PROCESSED_DATA_DIR / "nifty_market_data.csv"
    nifty.to_csv(output_file, index=False)
    print(f"\nSaved to: {output_file}")

if __name__ == "__main__":
    fetch_market_context()