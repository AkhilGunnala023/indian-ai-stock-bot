import pandas as pd
from config.config import OUTPUT_DIR

def allocate_portfolio(df):
    """
    Allocate capital based on Final Score.
    """

    if df.empty:
        return df

    # Sort by Final Score
    df = df.sort_values(
        "Final_Score",
        ascending=False
    ).reset_index(drop=True)

    # Total score
    total = df["Final_Score"].sum()

    total = df["Final_Score"].sum()

    if total == 0:
        df["Allocation_%"] = 0
        return df

    # Allocation %
    df["Allocation_%"] = (
        df["Final_Score"] / total * 100
    ).round(1)

    return df

if __name__ == "__main__":

    df = pd.read_csv(
        OUTPUT_DIR / "strong_buy_signals.csv"
    )

    df = allocate_portfolio(df)

    print(
        df[
            [
                "Symbol",
                "Final_Score",
                "Allocation_%"
            ]
        ]
    )