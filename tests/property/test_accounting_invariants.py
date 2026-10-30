import random

from backtest.engine import run_backtest
from data.models import Bar
from strategies.base import Strategy
from strategies.models import Signal
from tests._helpers import make_dataset

NO_COST = {"slippage_bps": 0.0, "fee_pct": 0.0}


class RandomStrategy(Strategy):
    def __init__(self, params=None):
        super().__init__(params)
        self.rng = random.Random(self.params["seed"])

    def on_bar(self, ctx):
        if ctx.position is None and self.rng.random() < 0.1:
            c = ctx.bar.close
            return Signal("BUY", stop_loss=c * 0.98, target=c * 1.03)
        if ctx.position is not None and self.rng.random() < 0.1:
            return Signal("EXIT")
        return None


def _bars(seed, n=300):
    rng, p, out = random.Random(seed), 100.0, []
    for i in range(n):
        o = p
        c = max(1.0, o * (1 + rng.gauss(0, 0.01)))
        j = i % 75
        out.append(Bar(f"2024-01-{1 + i // 75:02d}T{9 + j // 12:02d}:{(j % 12) * 5:02d}:00", o,
                       max(o, c) * 1.002, min(o, c) * 0.998, c, 100.0))
        p = c
    return out


def test_equity_equals_initial_plus_pnl_when_no_costs():
    for seed in range(25):
        res = run_backtest(make_dataset(_bars(seed)), RandomStrategy({"seed": seed}), NO_COST)
        assert res.status in ("COMPLETED", "HALTED")
        initial = res.config["initial_capital"]
        if res.status == "COMPLETED":
            assert abs(res.equity[-1][1] - (initial + sum(t["pnl"] for t in res.trades))) < 1e-6, seed
        for t in res.trades:
            assert t["qty"] > 0 and t["exit_ts"] >= t["entry_ts"]
