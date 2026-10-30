"""Risk entry point: order allow/reject + drawdown kill switch."""
from risk.drawdown import DrawdownTracker
from risk.kill_switch import KillSwitch
from risk.limits import RiskLimits


class RiskManager:
    def __init__(self, limits=None):
        self.limits = limits or RiskLimits()
        self.dd, self.kill = DrawdownTracker(), KillSwitch()

    def check_order(self, qty, price, equity):
        if self.kill.tripped:
            return False, "KILL_SWITCH"
        if qty <= 0:
            return False, "ZERO_SIZE"
        if qty * price > equity * self.limits.max_position_pct / 100.0:
            return False, "MAX_POSITION"
        return True, ""

    def after_bar(self, equity):
        dd = self.dd.update(equity)
        if dd >= self.limits.max_drawdown_pct:
            self.kill.trip(f"MAX_DRAWDOWN:{dd:.2f}%")
        return self.kill.tripped
