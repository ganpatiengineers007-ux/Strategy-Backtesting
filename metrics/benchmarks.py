def buy_and_hold_return_pct(bars):
    return (bars[-1].close / bars[0].open - 1) * 100.0 if bars else 0.0
