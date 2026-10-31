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


from datetime import date, timedelta
import random as _random


def make_days(days=20, per_day=20, seed=1, drift=0.0004):
    """Multi-day random-walk bars (valid dates), per_day bars/din."""
    rng, p, d, out = _random.Random(seed), 100.0, date(2024, 1, 1), []
    while len(out) < days * per_day:
        if d.weekday() < 5:
            for i in range(per_day):
                o = p
                c = max(1.0, o * (1 + rng.gauss(drift, 0.004)))
                out.append(Bar(f"{d.isoformat()}T{9 + i // 12:02d}:{(i % 12) * 5:02d}:00", o,
                               max(o, c) * 1.001, min(o, c) * 0.999, c, 100.0))
                p = c
        d += timedelta(days=1)
    return out


class BuyEvery(Strategy):
    """Har n bars par BUY, n//2 par EXIT. params: n (int), stop_pct/target_pct (float)."""
    strategy_id = "buy_every"

    def on_bar(self, ctx):
        n = self.params.get("n", 6)
        if ctx.position is None and ctx.index % n == 0:
            c = ctx.bar.close
            return Signal("BUY", stop_loss=c * (1 - self.params.get("stop_pct", 1.0) / 100),
                          target=c * (1 + self.params.get("target_pct", 2.0) / 100))
        if ctx.position is not None and ctx.index % n == n // 2:
            return Signal("EXIT")
        return None
