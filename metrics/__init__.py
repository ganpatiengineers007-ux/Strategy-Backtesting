"""Unified metrics. Yeh sirf ginti karta hai; approval validation pipeline deta hai."""
from . import accuracy, benchmarks, confidence_intervals, expectancy, return_metrics, risk_metrics, trade_metrics


def compute_all(result, dataset=None):
    out = {}
    out.update(return_metrics.compute(result.equity, result.config["initial_capital"]))
    out.update(risk_metrics.compute(result.equity))
    out.update(trade_metrics.compute(result.trades))
    out["win_rate_pct"] = accuracy.win_rate(result.trades)
    out["expectancy"] = expectancy.expectancy(result.trades)
    ci = confidence_intervals.bootstrap_mean_ci([t["pnl"] for t in result.trades])
    out["expectancy_ci95"] = list(ci) if ci else None
    if dataset is not None:
        out["buy_and_hold_return_pct"] = benchmarks.buy_and_hold_return_pct(dataset.bars)
    return out
