def size(equity, price, stop=None, risk_pct=1.0, max_pct=100.0):
    cap = int(equity * max_pct / 100.0 / price)
    if stop is not None and stop < price:
        return max(0, min(int(equity * risk_pct / 100.0 / (price - stop)), cap))
    return max(0, min(int(equity * 0.10 / price), cap))  # stop nahi: equity ka 10%
