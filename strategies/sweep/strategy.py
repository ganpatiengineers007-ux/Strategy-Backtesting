"""SweepStrategy registry wrapper (STR14).
Adapts scripts/sweep_strategy.py logic to the Strategy interface without
opening any broker connection, live order, or API key."""
from strategies.base import Strategy
from strategies.models import Signal


class SweepStrategy(Strategy):
    strategy_id = "sweep"
    required_data = ()

    def __init__(self, params=None):
        super().__init__(params)
        self.params.setdefault("stop_pct", 0.25)
        self.params.setdefault("target_pct", 1.0)

    def on_bar(self, ctx):
        """Return Signal on sweep-reclaim; no broker, no keys, no live orders."""
        bar = ctx.bar
        close = float(bar.close)
        prev = ctx.prev(1)
        if prev is None:
            return None
        prev_close = float(prev.close)

        # Simple sweep-reclaim proxy: close back above prev close after a dip
        if close > prev_close and bar.low < prev_close:
            return Signal(
                "BUY",
                stop_loss=round(close * (1 - self.params["stop_pct"] / 100), 2),
                target=round(close * (1 + self.params["target_pct"] / 100), 2),
                reason="sweep_reclaim_proxy",
            )
        return None
