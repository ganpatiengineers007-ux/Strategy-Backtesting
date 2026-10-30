from backtest.engine import run_backtest
from metrics import expectancy

MIN_TRADES = 5


def run(dataset, factory, config=None, split=0.7):
    k = int(len(dataset.bars) * split)
    ins = run_backtest(dataset.slice(0, k, "IS"), factory(), config)
    oos = run_backtest(dataset.slice(k, len(dataset.bars), "OOS"), factory(), config)
    out = {"is_trades": len(ins.trades), "oos_trades": len(oos.trades),
           "is_expectancy": expectancy.expectancy(ins.trades), "oos_expectancy": expectancy.expectancy(oos.trades)}
    if len(oos.trades) < MIN_TRADES:
        return {"status": "UNAVAILABLE", "reason": "TOO_FEW_OOS_TRADES", **out}
    return {"status": "PASS" if out["oos_expectancy"] > 0 else "FAIL", **out}
