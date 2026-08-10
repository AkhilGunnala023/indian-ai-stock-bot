from config.config import STOCK_UNIVERSE

if STOCK_UNIVERSE == "NIFTY50":
    from stock_lists.nifty50 import NIFTY50 as STOCKS

elif STOCK_UNIVERSE == "TOP500":
    from stock_lists.top500 import TOP500 as STOCKS

else:
    raise ValueError(f"Unsupported stock universe: {STOCK_UNIVERSE}")