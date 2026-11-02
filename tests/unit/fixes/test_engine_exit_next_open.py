"""Regression: EXIT signal agle bar ke open par bharta hai (same-bar close lookahead nahi)."""
from backtest.engine import run_backtest
from data.models import Bar, Dataset
from strategies.base import Strategy
from strategies.models import Signal


class _Scripted(Strategy):
    strategy_id = "scripted_test"
    required_data = ()

    def __init__(self, script):
        super().__init__({})
        self.script = script
        self.calls = 0

    def on_bar(self, ctx):
        sig = self.script.get(self.calls)
        self.calls += 1
        return sig


def _bars():
    raw = [  # open, high, low, close
        (100, 101, 99, 100),
        (100, 102, 99, 101),
        (101, 103, 100, 102),
        (102, 104, 101, 103),
        (105, 106, 104, 105),
        (106, 107, 105, 106),
    ]
    return [Bar(f"2026-10-12T09:{15 + i:02d}:00", o, h, l, c, 1000.0) for i, (o, h, l, c) in enumerate(raw)]


def test_exit_fills_at_next_bar_open():
    ds = Dataset("t", "TEST", "1", _bars(), quality_status="PASS")
    strat = _Scripted({0: Signal("BUY", stop_loss=90.0), 3: Signal("EXIT")})
    res = run_backtest(ds, strat, {"slippage_bps": 0.0, "fee_pct": 0.0})
    assert res.status == "COMPLETED", res.status
    assert len(res.trades) == 1, res.trades
    t = res.trades[0]
    assert t["exit_price"] == 105.0, t          # bar 4 ka open, bar 3 ka close (103) nahi
    assert t["reason"] == "SIGNAL_EXIT", t
