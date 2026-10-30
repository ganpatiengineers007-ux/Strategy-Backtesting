from backtest.engine import run_backtest
from metrics import expectancy


def run(dataset, factory, config=None, windows=4):
    n, rows = len(dataset.bars), []
    for w in range(windows):
        a, b = n * w // windows, n * (w + 1) // windows
        res = run_backtest(dataset.slice(a, b, f"WF{w}"), factory(), config)
        rows.append({"window": w, "trades": len(res.trades), "expectancy": expectancy.expectancy(res.trades)})
    total = sum(r["trades"] for r in rows)
    if total < 5:
        return {"status": "UNAVAILABLE", "reason": "TOO_FEW_TRADES", "windows": rows}
    active = [r for r in rows if r["trades"]]
    good = sum(1 for r in active if r["expectancy"] > 0)
    ok = len(active) >= windows // 2 and good * 2 >= len(active)
    return {"status": "PASS" if ok else "FAIL", "profitable_windows": good, "active_windows": len(active), "windows": rows}
