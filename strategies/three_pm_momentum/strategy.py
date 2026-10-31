"""ThreePMMomentumStrategy: 3PM momentum strategy for index futures.
Entry at 3:00 PM if close > previous close, with stop/target. Exit at 3:25 PM."""
from strategies.base import Strategy
from strategies.models import Signal


class ThreePMMomentumStrategy(Strategy):
    strategy_id = "three_pm_momentum"
    required_data = ()

    def __init__(self, params=None):
        super().__init__(params)
        # Default parameters from manifest
        self.params.setdefault("stop_pct", 0.5)
        self.params.setdefault("target_pct", 1.0)
        self.params.setdefault("entry_hour", 15)
        self.params.setdefault("entry_minute", 0)
        self.params.setdefault("exit_hour", 15)
        self.params.setdefault("exit_minute", 25)

    def on_bar(self, ctx):
        p, bar = self.params, ctx.bar
        t = int(bar.ts[11:13]) * 60 + int(bar.ts[14:16])

        if ctx.position is not None:
            if t >= p["exit_hour"] * 60 + p["exit_minute"]:
                return Signal("EXIT", reason="EOD_EXIT")
            return None

        if t == p["entry_hour"] * 60 + p["entry_minute"]:
            prev = ctx.prev(1)
            if prev is not None and bar.close > prev.close:
                return Signal(
                    "BUY",
                    stop_loss=round(bar.close * (1 - p["stop_pct"] / 100), 2),
                    target=round(bar.close * (1 + p["target_pct"] / 100), 2),
                    reason="momentum_3pm"
                )
        return None
