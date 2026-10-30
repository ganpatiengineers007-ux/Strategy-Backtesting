from metrics.confidence_intervals import bootstrap_mean_ci

MIN_TRADES = 30


def run(result):
    pnl = [t["pnl"] for t in result.trades]
    if len(pnl) < MIN_TRADES:
        return {"status": "UNAVAILABLE", "reason": f"NEED_{MIN_TRADES}_TRADES", "n_trades": len(pnl)}
    lo, hi = bootstrap_mean_ci(pnl)
    return {"status": "PASS" if lo > 0 else "FAIL", "ci95": [lo, hi], "n_trades": len(pnl)}
