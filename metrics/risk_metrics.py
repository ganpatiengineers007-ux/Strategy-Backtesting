import math
import statistics


def max_drawdown_pct(equity):
    peak, worst = None, 0.0
    for _, e in equity:
        peak = e if peak is None else max(peak, e)
        worst = max(worst, (peak - e) / peak * 100.0 if peak else 0.0)
    return worst


def sharpe_daily(equity):
    daily = {}
    for ts, e in equity:
        daily[ts[:10]] = e
    v = list(daily.values())
    rets = [v[i] / v[i - 1] - 1 for i in range(1, len(v)) if v[i - 1]]
    if len(rets) < 2:
        return None
    sd = statistics.pstdev(rets)
    return None if sd == 0 else statistics.mean(rets) / sd * math.sqrt(252)


def compute(equity):
    return {"max_drawdown_pct": max_drawdown_pct(equity), "sharpe_daily": sharpe_daily(equity)}
