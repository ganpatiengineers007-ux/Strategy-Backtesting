"""ThreePMMomentumStrategy: PLACEHOLDER logic (interface demo). Asli niyam aapko replace karne hain.
Rule (demo): entry time par close > pichhla close => BUY; stop/target %; exit time par EXIT."""
from strategies.base import Strategy
from strategies.models import Signal


class ThreePMMomentumStrategy(Strategy):
    strategy_id = "three_pm_momentum"
    required_data = ()

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
                return Signal("BUY", stop_loss=round(bar.close * (1 - p["stop_pct"] / 100), 2),
                              target=round(bar.close * (1 + p["target_pct"] / 100), 2), reason="momentum")
        return None
