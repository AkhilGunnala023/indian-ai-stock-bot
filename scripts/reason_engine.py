from config.logger import logger

logger.info("Generating prediction reasons")

def generate_reasons(row, global_regime, news_summary):

    reasons = []

    # EMA
    if row["EMA_Bullish"] == 1:
        reasons.append("EMA Bullish")

    # Trend
    if row["Strong_Trend"] == 1:
        reasons.append("Strong Trend (ADX > 25)")

    # RSI
    rsi = row["RSI_14"]

    if rsi < 30:
        reasons.append(f"RSI Oversold ({rsi:.1f})")

    elif rsi < 50:
        reasons.append(f"RSI Neutral ({rsi:.1f})")

    elif rsi <= 70:
        reasons.append(f"RSI Healthy ({rsi:.1f})")

    else:
        reasons.append(f"RSI Strong / Overbought ({rsi:.1f})")

    # Breakout
    if row["Breakout_20"] == 1:
        reasons.append("20-Day Breakout")

    # OBV
    if row["OBV_Bullish"] == 1:
        reasons.append("OBV Bullish")

    # Relative Strength
    if row["Relative_Strength_20D"] > 0:
        reasons.append("Outperforming NIFTY")

    # Volume
    if row["Volume_Spike_%"] >= 120:
        reasons.append(
            f"Volume Spike ({row['Volume_Spike_%']:.0f}%)"
        )

    # Market
    if row["NIFTY_EMA_Bullish"] == 1:
        reasons.append("Market Trend Bullish")

    if row["NIFTY_RSI_Above_50"] == 1:
        reasons.append("Market Momentum Positive")

    return reasons[:6]


def generate_no_trade_reasons(global_regime, news_summary):
    reasons = []

    # Macro reason
    if global_regime != "Risk-On":
        reasons.append("Global risk-off environment")

    # Momentum reason
    reasons.append("Weak momentum across sectors")

    # Volume reason
    reasons.append("Volume confirmation missing")

    return reasons
