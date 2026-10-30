from data.models import Bar, Dataset
from strategies.base import Strategy
from strategies.models import Signal


def make_bars(n=20, start=100.0, step=1.0):
    bars, p = [], start
    for i in range(n):
        o = p + 0.3
        c = o + (step if i % 2 == 0 else -step / 2)
        bars.append(Bar(f"2024-01-01T{9 + i // 12:02d}:{(i % 12) * 5:02d}:00", o, max(o, c) + 0.1, min(o, c) - 0.1, c, 100.0))
        p = c
    return bars


def make_dataset(bars, fields=None):
    return Dataset("t", "T", "5m", bars, fields=fields or {"open", "high", "low", "close", "volume"}, quality_status="PASS")


class BuyAtIndex(Strategy):
    strategy_id = "buy_at_index"

    def on_bar(self, ctx):
        if ctx.index == self.params.get("at", 1) and ctx.position is None:
            return Signal("BUY", reason="test")
        return None
