def apply(price, side, bps):
    """BUY ka price upar, SELL ka neeche."""
    k = bps / 10000.0
    return price * (1 + k) if side == "BUY" else price * (1 - k)
