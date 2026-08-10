from config.logger import logger

logger.info("Calculating dynamic threshold")
def get_dynamic_threshold(global_regime, nifty_trend, market_breadth):
    # Hard block handled earlier
    if global_regime != "Risk-On":
        return None

    # Strong market
    if "Above" in nifty_trend and "Strong" in market_breadth:
        return 0.55

    # Neutral market
    if "Above" in nifty_trend or "Moderate" in market_breadth:
        return 0.60

    # Weak market
    return 0.65
