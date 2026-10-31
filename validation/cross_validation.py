"""Anchored out-of-sample folds (koi parameter fitting nahi => time-series CV ka test hissa)."""
from backtest.engine import run_backtest
from metrics import expectancy

MIN_TRADES = 5


def decide(folds):
    active = [f for f in folds if f["trades"] > 0]
    if sum(f["trades"] for f in folds) < MIN_TRADES or len(active) < 2:
        return "UNAVAILABLE", "TOO_FEW_TRADES"
    good = sum(1 for f in active if f["expectancy"] > 0)
    return ("PASS" if good / len(active) >= 0.6 else "FAIL"), ""


def run(dataset, factory, config=None, folds=4):
    n = len(dataset.bars)
    size = n // (folds + 1)
    rows = []
    for k in range(1, folds + 1):
        res = run_backtest(dataset.slice(k * size, (k + 1) * size, f"CV{k}"), factory(), config)
        rows.append({"fold": k, "trades": len(res.trades), "expectancy": expectancy.expectancy(res.trades)})
    status, reason = decide(rows)
    return {"status": status, "reason": reason, "folds": rows}
